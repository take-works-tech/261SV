"""The one entry point that turns a file into a @Dataset.

Nothing above this module knows which reader ran. What it returns is always in the canonical frame -
right-handed, Z up, metres - with fields that remember their association and units that are declared
or absent.

Three of the toolkit's defaults are overridden here, and each override is the reason this module
exists rather than a call site using the toolkit directly:

* a field arrives with the association the file gave it, and is not promoted to points (INV-003)
* a value that could not be read is missing, never zero (INV-011)
* no unit is inferred from a field name, a magnitude or a format (XC-003)

Specification: ingest/REQ-010, REQ-011, REQ-013, ingest/TASK-001, TASK-002.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from xml.etree import ElementTree
from typing import Callable
from pathlib import Path

import numpy as np
from engine.code_page import UTF8_CODE_PAGE, active_code_page
from domain_core.os_paths import for_os
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkStringArray
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataObject,
    vtkDataSet,
    vtkMultiBlockDataSet,
    vtkPartitionedDataSet,
    vtkPartitionedDataSetCollection,
    vtkPolyData,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkIOCGNSReader import vtkCGNSReader
from vtkmodules.vtkIOExodus import vtkExodusIIReader
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkIOXML import (
    vtkXMLPolyDataReader,
    vtkXMLPUnstructuredGridReader,
    vtkXMLUnstructuredGridReader,
)

from domain_core.case_contents import CaseContents, ResultAxis
from domain_core.dataset import Association, Dataset, Field, SourceFrame
from domain_core.frame import (
    CANONICAL_SCALE,
    FORMATS_CARRYING_UNIT_INFORMATION,
    FrameDeclaration,
    resolve_frame,
)
from domain_core.conversion import ConversionRecord
from domain_core.identifiers import SourceIdentifiers
from domain_core.mesh import Cells
from domain_core.object_compatibility import Disposition, handling
from domain_core.partitions import Partitioning
from domain_core.parts import LoadedCase, Part
from engine.conversion import to_unstructured
from engine import cgns, exodus
from engine.result_axis import axis_of, delivered_position
from engine.survey import _pieces as survey_pieces
from engine.completeness import check_stl_before_read
from engine.exodus import BLOCK_ID_ARRAY

class UnsupportedFormatError(Exception):
    """Raised for a file this build has no reader for. Names the format rather than failing vaguely."""


class UnreadableFileError(Exception):
    """Raised when a supported format cannot be read: truncated, damaged, or empty of geometry."""


class FileChanged(UnreadableFileError):
    """A file that changed while it was being read, or since the dataset was loaded from it. What
    was read may be from two versions of the file, so it is not a dataset (ingest/AC-045)."""


#: What identifies a file's contents without reading them: its size and its modification time to the
#: nanosecond, per file involved - a `.pvtu` involves its pieces. Two snapshots that differ mean the
#: bytes read may be from two versions of the file, and no dataset is made of them (XC-284).
Fingerprint = dict[str, tuple[int, int]]


def _files_of(location: Path) -> list[Path]:
    if location.suffix.lower() == ".pvtu":
        # A manifest cut short is not XML: refused here by name rather than raised through the
        # fingerprint as a parser's own exception, which is what a half-written one did until measured.
        try:
            present, _, _ = survey_pieces(location)
        except ElementTree.ParseError as error:
            raise UnreadableFileError(
                f"{location.name} は XML として読めません（{error}）。書き込み途中か、切り詰められたマニフェストです"
            ) from error
        return [location, *(location.parent / piece for piece in present)]
    return [location]


def snapshot(path: str | Path) -> Fingerprint:
    """The fingerprint of a file and of every file it names, taken now. Raises `UnreadableFileError`
    where the file is not there or the operating system will not say what it is."""
    location = for_os(path)
    if not location.exists():
        raise UnreadableFileError(f"{location} does not exist")
    found: Fingerprint = {}
    for one in _files_of(location):
        try:
            stat = one.stat()
        except OSError as error:
            raise UnreadableFileError(f"{one.name} の状態を読めません（{error.strerror or error}）") from error
        found[one.name] = (stat.st_size, stat.st_mtime_ns)
    return found


def _readable(location: Path) -> None:
    """Refuse, naming the operating system's reason, a file that cannot be opened or read at all.

    A file another process holds without sharing - a solver writing on Windows - or one this user may
    not read reaches the toolkit's reader as an empty result, which it reports as "no part is there"
    (E-213). Asking the operating system first gives the reason that is true.
    """
    try:
        with location.open("rb") as handle:
            handle.read(4096)
    except OSError as error:
        raise UnreadableFileError(
            f"{location.name} を開けません、または読めません（{error.strerror or error}）。"
            "別のプロセスが書き込み中に握っているか、読む権限がないファイルです"
        ) from error


def _vanished(location: Path, before: Fingerprint, *, during: bool) -> FileChanged:
    was = before.get(location.name)
    size = f"{was[0]} バイト、更新時刻 {_when(was[1])}" if was else "記録なし"
    if during:
        return FileChanged(
            f"{location.name} は読んでいる間に消えました（読み込み前は {size}）。"
            "読めた分を結果として返す代わりに拒みます（ingest/AC-046）"
        )
    return FileChanged(
        f"{location.name} は読み込んだあとに消えました（読み込み時は {size}）。今ある数は読み込んだ時点のファイルのもので、"
        "無くなったファイルからは読みません（ingest/AC-046）"
    )


def _when(mtime_ns: int) -> str:
    return datetime.fromtimestamp(mtime_ns / 1e9, tz=timezone.utc).isoformat(timespec="microseconds")


def _changed(location: Path, before: Fingerprint, after: Fingerprint, *, during: bool) -> FileChanged:
    """The refusal for a file that did not hold still, naming what moved (ingest/AC-045)."""
    moved = []
    for name in sorted(set(before) | set(after)):
        if before.get(name) != after.get(name):
            was, now = before.get(name), after.get(name)
            moved.append(
                f"{name}：{was[0] if was else '無し'}→{now[0] if now else '無し'} バイト、"
                f"更新時刻 {_when(was[1]) if was else '無し'}→{_when(now[1]) if now else '無し'}"
            )
    detail = "；".join(moved)
    if during:
        message = (
            f"{location.name} は読んでいる間に変わりました（{detail}）。ソルバが書いている最中のファイルかもしれません。"
            "読めた分を結果として返す代わりに拒みます。書き終わってから読み直してください（ingest/AC-045）"
        )
    else:
        message = (
            f"{location.name} は読み込んだあとに変わりました（{detail}）。今ある数は読み込んだ時点のファイルのもので、"
            "変わったファイルからは読みません。読み込み直してください（ingest/AC-045）"
        )
    return FileChanged(message)


def _held_still(location: Path, before: Fingerprint) -> None:
    if not location.exists():
        raise _vanished(location, before, during=True)
    after = snapshot(location)
    if after != before:
        raise _changed(location, before, after, during=True)


def _declared_frame(path: Path, data: vtkDataObject | None) -> FrameDeclaration:
    """What this file declares about its frame.

    Every format this build reads declares **nothing**: the VTK XML formats carry no frame or unit
    field, and STL carries geometry alone (E-130). So this returns an empty declaration today, and the
    assumption that the file is already canonical is what gets recorded (AC-028). It exists as a step
    rather than as a comment so that a format which does declare - CGNS, with its `LengthUnits`
    enumeration - is read here and validated by the same rule, instead of at whatever call site adds it.
    """
    return FrameDeclaration()


@dataclass(frozen=True, slots=True)
class ReaderChoice:
    """Which reader will run, and what this product promises about it (XC-049)."""

    suffix: str
    factory: type
    support_level: str  # "Verified" | "Offered"
    known_gaps: str = ""
    # What unit information the file may carry that this reader does not read. Empty means the format
    # carries none - which is the measured case for every format in this build (E-130) - not that the
    # question was skipped.
    unread_unit_information: str = ""
    # New fields go at the end. The four above are passed positionally at every call site, and a field
    # inserted among them silently reassigns them - which is how a reader's stated gap became its
    # preparation step for one commit, caught by a test rather than by review.
    #
    # What must be switched on between `SetFileName` and `Update`. None for a reader whose defaults
    # read the file; a function for one whose defaults do not, which is not a thing to leave implicit
    # (E-136).
    prepare: "Callable[[object], None] | None" = None
    # Run after `Update` to refuse a read that lost something. Separate from `prepare` because the
    # switching is an attempt and the checking is the guarantee.
    verify: "Callable[[object, object], None] | None" = None
    # The library behind this reader takes the path as a narrow string on Windows, and given a
    # character outside the process's code page it does not fail: it takes the process down
    # (E-216). Such a path is refused here, by name, before the library sees it (XC-293).
    narrow_path: bool = False

    def __post_init__(self) -> None:
        carried = FORMATS_CARRYING_UNIT_INFORMATION.get(self.suffix)
        if carried and not self.unread_unit_information:
            raise ValueError(
                f"{self.suffix} files carry {carried}; a reader for them must either read it or say "
                f"that it does not (ingest/AC-034)"
            )


# Exodus reads **no results at all** unless every array is switched on by name, across 27 categories
# that all start off (E-136). The gap is named here because a user is entitled to know that this
# format needed handling the others did not.
_EXODUS = ReaderChoice(
    ".ex2", vtkExodusIIReader, "Verified",
    known_gaps=(
        "the toolkit's reader returns no results unless each array is enabled by name; this product "
        "enables every category and refuses the read if a result the file offered did not arrive"
    ),
    prepare=exodus.enable_everything,
    verify=exodus.verify,
    narrow_path=True,
)

# CGNS is the one format this build reads that **declares** its units, and the one whose reader
# exposes no way to read them (E-130, E-137). Saying so is required rather than optional: constructing
# this without `unread_unit_information` is refused by `ReaderChoice` itself (ingest/AC-034).
_CGNS = ReaderChoice(
    ".cgns", vtkCGNSReader, "Verified",
    known_gaps=cgns.KNOWN_GAPS,
    unread_unit_information=cgns.UNREAD_UNIT_INFORMATION,
    prepare=cgns.enable_everything,
    verify=cgns.verify,
)

_READERS: dict[str, ReaderChoice] = {
    ".vtu": ReaderChoice(".vtu", vtkXMLUnstructuredGridReader, "Verified"),
    ".pvtu": ReaderChoice(".pvtu", vtkXMLPUnstructuredGridReader, "Verified",
                          "pieces are concatenated; points on partition boundaries appear more than once"),
    ".vtp": ReaderChoice(".vtp", vtkXMLPolyDataReader, "Verified"),
    ".stl": ReaderChoice(
        ".stl", vtkSTLReader, "Verified", "carries geometry only; no fields",
        prepare=check_stl_before_read,
    ),
    ".cgns": _CGNS,
    ".e": _EXODUS,
    ".ex2": _EXODUS,
    ".exo": _EXODUS,
}


def supported_suffixes() -> list[str]:
    return sorted(_READERS)


__all__ = ["UTF8_CODE_PAGE", "active_code_page"]  # re-exported for the readers' callers and tests


def path_the_reader_cannot_take(location: Path, choice: ReaderChoice) -> str | None:
    """Why this reader must not be handed this path, or None where it may be (XC-293, E-216).

    Only the readers whose library takes a narrow path are concerned, and only on Windows, and only
    when the path carries a character outside ASCII and the process is not running in the UTF-8 code
    page. The measured alternative is the engine process ending with no answer at all, which is
    worse than any refusal: a refusal names the file, the library and the two ways out.
    """
    if not choice.narrow_path or sys.platform != "win32":
        return None
    text = str(location)
    if text.isascii() or active_code_page() == UTF8_CODE_PAGE:
        return None
    offending = "".join(dict.fromkeys(ch for ch in text if ord(ch) > 127))[:8]
    return (
        f"{location.name} はこの経路からは読めません：この形式（{choice.suffix}）のライブラリ（netCDF）は Windows で"
        f"経路を狭い文字列として受け取り、ASCII 以外の文字（ここでは '{offending}'）を含む経路では読めずにエンジンごと"
        "止まります（E-216）。ASCII だけの名前の場所に置いて読み込むか、UTF-8 コードページで動く版でお使いください（XC-293）"
    )


def load_refusal(path: str | Path) -> str | None:
    """Why a load of this file would be refused before anything is read, or None: what
    `dataset.inspect` answers so that a drop is refused before any load (XC-291, XC-293)."""
    location = Path(path)
    choice = _READERS.get(location.suffix.lower())
    return path_the_reader_cannot_take(location, choice) if choice is not None else None


def _canonical_cells(data: vtkDataSet) -> Cells:
    """The connectivity the file declared, in the toolkit's own layout and with nothing tessellated.

    An unstructured grid hands over its three arrays directly. Anything else - an image, a rectilinear
    or structured grid - has implicit connectivity rather than stored connectivity, and this build has
    no reader for one, so the case is refused by name instead of being approximated by its surface.
    """
    if isinstance(data, vtkUnstructuredGrid):
        cells = data.GetCells()
        return Cells(
            offsets=vtk_to_numpy(cells.GetOffsetsArray()).astype(np.int64, copy=True),
            connectivity=vtk_to_numpy(cells.GetConnectivityArray()).astype(np.int64, copy=True),
            types=vtk_to_numpy(data.GetCellTypesArray()).astype(np.uint8, copy=True),
        )
    if isinstance(data, vtkPolyData):
        # A surface file is already the thing it draws. Its four cell arrays are read in the order VTK
        # stores them so that a cell index means the same here as it does in the file.
        offsets = [np.zeros(1, np.int64)]
        connectivity: list[np.ndarray] = []
        types: list[np.ndarray] = []
        base = 0
        for array, cell_type in (
            (data.GetVerts(), 1), (data.GetLines(), 4), (data.GetPolys(), 7), (data.GetStrips(), 6),
        ):
            if array.GetNumberOfCells() == 0:
                continue
            piece = vtk_to_numpy(array.GetOffsetsArray()).astype(np.int64, copy=True)
            offsets.append(piece[1:] + base)
            entries = vtk_to_numpy(array.GetConnectivityArray()).astype(np.int64, copy=True)
            connectivity.append(entries)
            types.append(np.full(array.GetNumberOfCells(), cell_type, np.uint8))
            base += entries.size
        return Cells(
            offsets=np.concatenate(offsets),
            connectivity=np.concatenate(connectivity) if connectivity else np.zeros(0, np.int64),
            types=np.concatenate(types) if types else np.zeros(0, np.uint8),
        )
    raise UnreadableFileError(
        f"{type(data).__name__} stores no explicit connectivity; this build reads only the two types "
        "that do, and approximating the rest by its surface would put display geometry where the "
        "canonical geometry belongs (INV-001)"
    )


def _identifier_names(container) -> set[str]:
    """The names of the arrays this container has marked as identifiers rather than as data.

    Read from the attribute roles the file declared - `<PointData GlobalIds="GlobalNodeId">` - and not
    from the array's name, because a writer may call an identifier anything and a data array may be
    called `GlobalNodeId` by somebody who meant it (E-135).
    """
    names: set[str] = set()
    for array in (container.GetGlobalIds(), container.GetPedigreeIds()):
        if array is not None and array.GetName():
            names.add(array.GetName())
    return names


def _identifiers(container) -> SourceIdentifiers | None:
    """What the file called each entry, or None where it called them nothing."""
    global_array = container.GetGlobalIds()
    pedigree_array = container.GetPedigreeIds()
    if global_array is None and pedigree_array is None:
        return None

    global_ids = None
    if global_array is not None:
        # int64 and not the float the fields use: an identifier's exactness is the whole of its value,
        # and float64 stops being exact above 2^53.
        global_ids = vtk_to_numpy(global_array).astype(np.int64, copy=True).reshape(-1)

    pedigree_ids = None
    if pedigree_array is not None:
        if isinstance(pedigree_array, vtkStringArray):
            pedigree_ids = tuple(
                pedigree_array.GetValue(i) for i in range(pedigree_array.GetNumberOfValues())
            )
        else:
            pedigree_ids = tuple(str(v) for v in vtk_to_numpy(pedigree_array).reshape(-1).tolist())

    return SourceIdentifiers(
        global_ids=global_ids,
        pedigree_ids=pedigree_ids,
        global_name=global_array.GetName() if global_array is not None else None,
        pedigree_name=pedigree_array.GetName() if pedigree_array is not None else None,
    )


def _fields(data: vtkDataSet) -> dict[str, Field]:
    """Every array that is data, with the association the file gave it and no declared unit.

    Identifier arrays are **not** fields and are left out here: an identifier is not a physical
    quantity, and offering `GlobalNodeId` in the list a user picks a @Variable from invites a plot of
    node numbers against node numbers (GL-034, INV-023).
    """
    found: dict[str, Field] = {}
    for association, container in (
        (Association.POINT, data.GetPointData()),
        (Association.CELL, data.GetCellData()),
    ):
        identifiers = _identifier_names(container)
        for index in range(container.GetNumberOfArrays()):
            array = container.GetArray(index)
            if array is None or array.GetName() in identifiers:
                continue
            if array.GetName() == BLOCK_ID_ARRAY:
                # The element-block number Exodus writes onto every cell. An identity, carried on the
                # part rather than offered as a quantity to plot (XC-236, E-136).
                continue
            # Stored at the precision the file gave it: a float32 result stays float32 (XC-246), so
            # that `Field.significant_digits` says six and not fifteen (INV-014). The copy is what
            # detaches the array from VTK's memory; the dtype is not touched. Promoting here was the
            # defect XC-257 names first - it doubled the case against LIM-001 and, worse, made every
            # float32 field claim double precision on the one path that reaches a document.
            values = np.array(vtk_to_numpy(array), copy=True)
            name = array.GetName() or f"{association.value}_array_{index}"
            found[name] = Field(name=name, association=association, values=values, unit=None)
    return found


# CT-012's dispositions, as the reader applies them. A composite is taken apart into the parts of one
# @Case; a dataset is read; anything else names itself and stops.
_PARTITION_CONTAINERS = (vtkPartitionedDataSet,)


def _block_name(parent: vtkCompositeDataSet, index: int, fallback: str) -> str:
    """The name the file gave a block, or a generated one that says it was generated."""
    metadata = parent.GetMetaData(index)
    if metadata is not None and metadata.Has(vtkMultiBlockDataSet.NAME()):
        name = metadata.Get(vtkMultiBlockDataSet.NAME())
        if name:
            return str(name)
    return fallback


#: The reader's reason for a part it returned without geometry (XC-272, E-210).
NO_CELLS = "要素なし"


def _walk(node: vtkDataObject, path: tuple[str, ...], parts: list[Part], partitions: list[int],
          source: SourceFrame | None = None) -> None:
    """Collect the leaves of a composite as parts - present, or absent with the reason.

    One list for both, because an absence is a part the file named (INV-019): where it sits in the
    hierarchy is as much a fact about it as the name, and a second list of strings lost it.

    An empty leaf is a named `None` (E-133's measurement companion): the file said there was a part
    there and there is not, which is exactly what AC-027 asks be reported rather than skipped.
    """
    if isinstance(node, _PARTITION_CONTAINERS):
        # Partitions of one part: they recombine, so this is one part with a piece count (XC-234).
        pieces = [node.GetPartition(i) for i in range(node.GetNumberOfPartitions())]
        present = [piece for piece in pieces if piece is not None]
        partitions.append(max(len(present), 1))
        if not present:
            parts.append(Part(name=path[-1], path=path, dataset=None))
            return
        parts.append(Part(name=path[-1], path=path, dataset=_combine(present, source)))
        return

    if isinstance(node, vtkCompositeDataSet):
        count = (
            node.GetNumberOfPartitionedDataSets()
            if isinstance(node, vtkPartitionedDataSetCollection)
            else node.GetNumberOfBlocks()
        )
        for index in range(count):
            child = (
                node.GetPartitionedDataSet(index)
                if isinstance(node, vtkPartitionedDataSetCollection)
                else node.GetBlock(index)
            )
            name = _block_name(node, index, f"block {index}")
            if child is None:
                parts.append(Part(name=name, path=path + (name,), dataset=None))
                continue
            _walk(child, path + (name,), parts, partitions, source)
        return

    # From here on the disposition is CT-012's, read from the contract rather than restated.
    where = " / ".join(path) or "the root object"
    row = handling(node.GetClassName())

    if row.disposition is Disposition.READ and isinstance(node, vtkDataSet):
        if node.GetNumberOfCells() == 0:
            # The file named a part here and the reader returned no geometry for it - which is what a
            # zone it could not read looks like from outside: points allocated from the declared
            # size, no cells, and an error on the toolkit's log that reaches nobody (E-210). An
            # absence, said as one, never a part of nothing counted as present (AC-027, XC-272).
            parts.append(Part(name=path[-1], path=path, dataset=None, reason=NO_CELLS))
            return
        parts.append(Part(name=path[-1], path=path, dataset=_as_dataset(node, source=source)))
        return

    if row.disposition is Disposition.CONVERT:
        converted, record = to_unstructured(node)
        if converted.GetNumberOfCells() == 0:
            parts.append(Part(name=path[-1], path=path, dataset=None, reason=NO_CELLS))
            return
        parts.append(Part(
            name=path[-1], path=path, dataset=_as_dataset(converted, source=source, conversion=record),
        ))
        return

    raise UnsupportedFormatError(
        f"{where} is a {node.GetClassName()}, which this product does not read. {row.reason or ''} "
        "(CT-012). Naming it is the point: a generic read failure sends a user looking for a corrupt "
        "file that does not exist"
    )


def read(path: str | Path) -> Dataset:
    """Read a result file into a @Dataset in the canonical frame.

    Raises UnsupportedFormatError for a format with no reader here, and UnreadableFileError when a
    supported file yields no geometry - never a partial dataset, and never an empty one presented as
    a result (ingest/AC-021, AC-022).
    """
    location = for_os(path)
    choice = _READERS.get(location.suffix.lower())
    if choice is None:
        raise UnsupportedFormatError(
            f"'{location.suffix}' is not a format this build reads; it reads {supported_suffixes()}"
        )
    if not location.exists():
        raise UnreadableFileError(f"{location} does not exist")
    refused = path_the_reader_cannot_take(location, choice)
    if refused:
        raise UnreadableFileError(refused)
    before = snapshot(location)
    _readable(location)

    reader = choice.factory()
    reader.SetFileName(str(location))
    if choice.prepare is not None:
        choice.prepare(reader)
    reader.Update()
    data = reader.GetOutput()
    if choice.verify is not None:
        choice.verify(reader, data)
    _held_still(location, before)

    if data is not None and handling(data.GetClassName()).disposition is Disposition.DECOMPOSE:
        # Asked from the contract rather than by testing the class, so that what this refuses and what
        # CT-012 says are one answer - and so the compatibility gate can tell a guard from a read.
        raise UnsupportedFormatError(
            f"{location.name} holds more than one part; use read_case, which returns them all rather "
            "than one of them (XC-234)"
        )
    if data is None or data.GetNumberOfPoints() == 0:
        raise UnreadableFileError(f"{location.name} was read by {choice.factory.__name__} but contains no points")

    return _as_dataset(data, source=SourceFrame(
        *resolve_frame(_declared_frame(location, data)), reader=choice.factory.__name__
    ))


def _as_dataset(
    data: vtkDataSet, *, source: SourceFrame | None = None,
    conversion: ConversionRecord | None = None,
) -> Dataset:
    """One `vtkDataSet` as a @Dataset in the canonical frame, with nothing drawn.

    Shared by the single-file path and the composite walk so that a part of an assembly and a file on
    its own go through the same conversion - a second path here is a second set of rounding.
    """
    if data.GetNumberOfPoints() == 0:
        raise UnreadableFileError(f"a {type(data).__name__} was read and contains no points")
    scale = source.scale_to_metres if source is not None else CANONICAL_SCALE
    points = vtk_to_numpy(data.GetPoints().GetData()).astype(np.float64, copy=True)
    # One multiplication, at one point, and only when it changes the value. XC-230: a conversion happens
    # once at a stated place, and `* 1.0` on every coordinate of every dataset is an operation that can
    # only lose precision and never adds any.
    return Dataset(
        points_m=points if scale == CANONICAL_SCALE else points * scale,
        cells=_canonical_cells(data),
        fields=_fields(data),
        identifiers={
            association: found
            for association, container in (
                (Association.POINT, data.GetPointData()),
                (Association.CELL, data.GetCellData()),
            )
            if (found := _identifiers(container)) is not None
        },
        source=source,
        conversion=conversion,
    )


def _combine(pieces: list[vtkDataSet], source: SourceFrame | None = None) -> Dataset:
    """The partitions of one part, as the one mesh they were cut from.

    They are concatenated and **not merged**: the reader performs no point merging (E-039), so the
    interface points arrive twice and stay twice. Which is right - INV-010 governs them from there, and
    welding them here would need a tolerance (XC-232).
    """
    if len(pieces) == 1:
        return _as_dataset(pieces[0], source=source)
    datasets = [_as_dataset(piece, source=source) for piece in pieces]
    offset = 0
    points, offsets, connectivity, types = [], [np.zeros(1, np.int64)], [], []
    base = 0
    for dataset in datasets:
        points.append(dataset.points_m)
        offsets.append(dataset.cells.offsets[1:] + base)
        connectivity.append(dataset.cells.connectivity + offset)
        types.append(dataset.cells.types)
        base += dataset.cells.connectivity.size
        offset += dataset.point_count
    fields: dict[str, Field] = {}
    shared = set.intersection(*(set(dataset.fields) for dataset in datasets)) if datasets else set()
    for name in sorted(shared):
        first = datasets[0].fields[name]
        fields[name] = Field(
            name=name,
            association=first.association,
            values=np.concatenate([dataset.fields[name].values for dataset in datasets]),
            unit=first.unit,
        )
    return Dataset(
        points_m=np.concatenate(points),
        cells=Cells(np.concatenate(offsets), np.concatenate(connectivity), np.concatenate(types)),
        fields=fields,
        partitioning=Partitioning(partitions=len(pieces)),
        source=source,
    )


def read_case(path: str | Path, *, step: int = 0, expected: Fingerprint | None = None) -> LoadedCase:
    """Read a file as one @Case, however many parts it turns out to hold (ingest/AC-026, AC-027).

    A composite is taken apart into named parts; a single dataset is one part named after its file.
    Either way what comes back states how many parts were found, how many pieces they were cut into,
    and which named parts were not there.

    The file has to hold still: its fingerprint - size and modification time, of every file involved
    - is taken before the read and again after it, and a difference is a refusal rather than a
    dataset, because the bytes read may be from two versions of the file (ingest/AC-045, XC-284).
    `expected` is the fingerprint the file had when the dataset was loaded; a read of another step
    from a file that has changed since is refused the same way, naming the change.

    `step` is the ordinal along the sequence the file declared, from 0 (XC-283). The values at that
    step are what comes back; the axis is the whole sequence either way. A step the file does not
    have raises `PositionError` before anything is read, and nothing nearer is read instead
    (view/AC-033): the toolkit, asked for a value between two declared ones, delivers the next one
    and says so only on a pipeline key (E-211), so the value asked for is always a declared one and
    the one delivered is checked against it.
    """
    location = for_os(path)
    choice = _READERS.get(location.suffix.lower())
    if choice is None:
        raise UnsupportedFormatError(
            f"'{location.suffix}' is not a format this build reads; it reads {supported_suffixes()}"
        )
    if not location.exists():
        if expected is not None:
            raise _vanished(location, expected, during=False)
        raise UnreadableFileError(f"{location} does not exist")
    refused = path_the_reader_cannot_take(location, choice)
    if refused:
        raise UnreadableFileError(refused)
    before = snapshot(location)
    if expected is not None and before != expected:
        raise _changed(location, expected, before, during=False)
    _readable(location)

    reader = choice.factory()
    reader.SetFileName(str(location))
    if choice.prepare is not None:
        choice.prepare(reader)
    # The sequence the file declared is on the pipeline after the metadata pass alone (E-211), so the
    # step is checked against it before the data is read: a step that is not there costs no read.
    reader.UpdateInformation()
    axis = axis_of(reader)
    position = axis.at(step)
    if position.value is None:
        reader.Update()
    else:
        reader.UpdateTimeStep(position.value)
    data = reader.GetOutputDataObject(0)
    if choice.verify is not None:
        choice.verify(reader, data)
    if data is None:
        raise UnreadableFileError(f"{location.name} was read by {choice.factory.__name__} and is empty")
    if position.value is not None:
        delivered = delivered_position(data)
        if delivered != position.value:
            raise UnreadableFileError(
                f"{location.name}: step {step} at position {position.value!r} was asked for and the reader "
                f"delivered {delivered!r}. A value from another step is not reported as this one (view/AC-033)"
            )

    parts: list[Part] = []
    partitions: list[int] = []
    # The frame is resolved once for the file and carried onto every part, exactly as `read` carries
    # it onto its one dataset: a part that arrived through a composite is no less converted, and a
    # coordinate whose conversion cannot be explained is a coordinate that is merely trusted
    # (ingest/AC-028). Until 2026-09-18 the parts of a case had no source at all.
    source = SourceFrame(
        *resolve_frame(_declared_frame(location, data)), reader=choice.factory.__name__
    )
    _walk(data, (location.stem,), parts, partitions, source)

    if not any(part.is_present for part in parts):
        raise UnreadableFileError(
            f"{location.name} named {len(parts)} part(s) and none of them is there"
            if parts
            else f"{location.name} holds no part this build can read"
        )
    _held_still(location, before)
    # The sequence the file declared, read from the pipeline rather than from any one reader's method,
    # and its **kind left undeclared**: no reader in this build surfaces a statement of what the values
    # mean, and one of them will guess if asked (E-138, XC-240).
    return assemble(parts, axis=axis, partitions=partitions)


def assemble(parts: Sequence[Part], *, axis: ResultAxis, partitions: Sequence[int]) -> LoadedCase:
    """The case from its parts, present and absent (AC-027).

    The counts are of what is here; the absences are listed by name with the reader's reason. One
    place, so that a composite walked in memory and a file read from disk say the same about
    themselves.
    """
    return LoadedCase(
        parts=tuple(parts),
        contents=CaseContents(
            steps=len(axis.positions) if axis.positions else 1,
            parts=sum(1 for part in parts if part.is_present),
            axis=axis,
            missing_parts=tuple(part.absence for part in parts if not part.is_present),
            partitions=max(list(partitions) or [1]),
        ),
    )


def support_level(path: str | Path) -> tuple[str, str]:
    """The level this product promises for a file's format, and the reader's known gaps (AC-032).

    An unread unit declaration is one of those gaps (AC-034): the unit stays undeclared either way, and
    the difference between "this file said nothing" and "this file said something we did not read" is
    the user's to know, because only one of the two can be fixed by asking the solver.
    """
    choice = _READERS.get(Path(path).suffix.lower())
    if choice is None:
        return "Absent", "no reader for this format in this build"
    gaps = [gap for gap in (choice.known_gaps, choice.unread_unit_information) if gap]
    return choice.support_level, "; ".join(gaps)


def is_unstructured(data: vtkDataSet) -> bool:
    return isinstance(data, vtkUnstructuredGrid)
