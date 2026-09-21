"""Reading everything a file offers, and proving nothing was dropped.

Two of the toolkit's readers for formats this product's users actually work in **read no results at
all** unless each array is switched on by name, and neither says so:

* `vtkExodusIIReader` - 27 array categories, every status 0 (E-136);
* `vtkCGNSReader` - three `vtkDataArraySelection` objects, every array off (E-137).

Two formats with two unrelated APIs and the same defect is a pattern rather than a quirk, so the answer
lives here rather than being written a third time for the third format. What a reader must supply is
small: how to list what the file offers, and how to switch it all on. What this module supplies is the
part that matters - **the check that what was offered arrived**.

The distinction is the whole point. Switching everything on is an *attempt*: it can fall behind a
toolkit release, misspell a category, or miss an API that did not exist when it was written. Comparing
what came back against what the file said it held cannot. A result that is missing stops the read,
because it is not an absent value - XC-001 governs a value the file does not have, and this is a value
the file does have and the reader did not fetch.

**A file shorter than its own header says** is the same defect from the other side (E-212, XC-284):
`vtkExodusIIReader` given an Exodus file cut at 90 per cent returns every point, every cell and every
field name of the complete file, with the values replaced by zeros, and says nothing. The check here
reads the NetCDF classic header - which declares where every variable's bytes lie - and refuses a
file that does not reach that far, before the reader is asked for anything.

Specification: ingest/REQ-015, AC-022, AC-032, XC-237, XC-284. Evidence: E-136 (T1), E-137 (T1),
E-212 (T1).
"""

from __future__ import annotations

import struct
from pathlib import Path

from vtkmodules.vtkCommonDataModel import vtkCompositeDataSet, vtkDataSet


class ResultsLost(Exception):
    """Raised when a file offered a result that did not arrive. Never silently dropped."""


class FileIncomplete(Exception):
    """Raised when a file is shorter than its own header declares. What is there is never read as
    a result: the reader would fill the missing part with zeros and say nothing (E-212)."""


#: NetCDF classic containers start "CDF" and a version byte: 1 (32-bit offsets), 2 (64-bit offsets),
#: 5 (64-bit data). Exodus II files are one of these, or HDF5 - and HDF5 refuses its own truncation.
_NETCDF_VERSIONS = (1, 2, 5)
_STREAMING = 0xFFFFFFFF
_NC_DIMENSION, _NC_VARIABLE, _NC_ATTRIBUTE = 0x0A, 0x0B, 0x0C
_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 4, 6: 8, 7: 1, 8: 2, 9: 4, 10: 8, 11: 8}
#: How much of the front of a file is read for its header. An Exodus header of many blocks and names
#: is kilobytes; one past this is not checked, and `netcdf_declared_length` says so by answering None.
HEADER_BYTES = 4 << 20


def netcdf_declared_length(head: bytes) -> int | None:
    """How long a NetCDF classic file must be, from its own header - or None where it does not say.

    The header lists every variable with the offset its data begins at and the size of one record of
    it, so the end of the last one is the least the file can be. None where the bytes are not a
    NetCDF classic header (HDF5 among others), where the record count is the streaming marker, or
    where the header runs past what was read; none of those is a statement that the file is whole.
    """
    if len(head) < 8 or head[:3] != b"CDF" or head[3] not in _NETCDF_VERSIONS:
        return None
    version = head[3]
    wide = version == 5
    position = 4

    def take(fmt: str) -> int:
        nonlocal position
        size = struct.calcsize(fmt)
        (value,) = struct.unpack(fmt, head[position:position + size])
        position += size
        return int(value)

    def count() -> int:
        return take(">q") if wide else take(">i")

    def skip(length: int) -> None:
        nonlocal position
        position += (length + 3) // 4 * 4

    def attributes() -> None:
        tag = take(">i")
        number = count()
        if tag != _NC_ATTRIBUTE:
            return
        for _ in range(number):
            skip(count())
            kind = take(">i")
            skip(count() * _TYPE_SIZES[kind])

    try:
        records = take(">q") if wide else take(">I")
        tag = take(">i")
        number = count()
        dimensions: list[int] = []
        if tag == _NC_DIMENSION:
            for _ in range(number):
                skip(count())
                dimensions.append(count())
        attributes()
        tag = take(">i")
        number = count()
        fixed_end = 0
        record_variables: list[tuple[int, int]] = []
        if tag == _NC_VARIABLE:
            for _ in range(number):
                skip(count())
                dimension_ids = [take(">i") for _ in range(count())]
                attributes()
                take(">i")  # the type; the header's vsize already accounts for it
                vsize = count()
                begin = take(">q") if version >= 2 else take(">I")
                if dimension_ids and dimensions[dimension_ids[0]] == 0:
                    record_variables.append((begin, vsize))
                else:
                    fixed_end = max(fixed_end, begin + vsize)
    except (struct.error, IndexError):
        return None
    if records == _STREAMING:
        return None
    end = fixed_end
    if record_variables and records > 0:
        # Records are interleaved: record r of a variable lies recsize bytes after record r - 1,
        # where recsize is every record variable's slab together (one variable alone is unpadded).
        recsize = sum(vsize for _, vsize in record_variables) if len(record_variables) > 1 else record_variables[0][1]
        for begin, vsize in record_variables:
            end = max(end, begin + (records - 1) * recsize + vsize)
    return end


def check_file_is_whole(path: Path) -> None:
    """Refuse a NetCDF classic file shorter than its own header declares (E-212, ingest/AC-022).

    Before the read, because the reader fills what is missing with zeros and reports nothing: a
    result file a solver is still writing, or one that was cut, would arrive as a complete-looking
    dataset of wrong numbers. A file whose header says nothing usable is not refused here - that is
    not a statement that it is whole, and the reader's own checks follow.
    """
    location = Path(path)
    size = location.stat().st_size
    with location.open("rb") as handle:
        head = handle.read(min(size, HEADER_BYTES))
    declared = netcdf_declared_length(head)
    if declared is not None and size < declared:
        raise FileIncomplete(
            f"{location.name} は {size} バイトで、ファイル自身のヘッダが宣言する {declared} バイトより短い。"
            "書き込み途中か、切り詰められたファイルです。このリーダーは足りない部分を 0 で埋めて何も言わないので、"
            "読めた分を結果として返す代わりに拒みます（E-212）"
        )


def enable_selections(*selections: object) -> None:
    """Switch on every array of each `vtkDataArraySelection` given."""
    for selection in selections:
        selection.EnableAllArrays()


def names_in_selections(*selections: object) -> set[str]:
    """Every array name the given selections offer."""
    found: set[str] = set()
    for selection in selections:
        found.update(
            selection.GetArrayName(index) for index in range(selection.GetNumberOfArrays())
        )
    return {name for name in found if name}


def arrays_present(node: object, found: set[str] | None = None) -> set[str]:
    """Every array name anywhere in a data object, walking composites to their leaves."""
    found = set() if found is None else found
    if isinstance(node, vtkCompositeDataSet):
        iterator = node.NewIterator()
        iterator.InitTraversal()
        while not iterator.IsDoneWithTraversal():
            arrays_present(iterator.GetCurrentDataObject(), found)
            iterator.GoToNextItem()
        return found
    if isinstance(node, vtkDataSet):
        for container in (node.GetPointData(), node.GetCellData(), node.GetFieldData()):
            for index in range(container.GetNumberOfArrays()):
                name = container.GetArrayName(index)
                if name:
                    found.add(name)
    return found


def check_nothing_was_dropped(offered: set[str], output: object, *, evidence: str) -> None:
    """Refuse the read if a result the file offered is not in what came back.

    `evidence` names the measurement behind the refusal, because a user meeting this message is being
    told something surprising about their file's reader and is entitled to know it was measured.
    """
    missing = sorted(offered - arrays_present(output))
    if missing:
        raise ResultsLost(
            "このファイルが持つ結果のうち、読み込まれなかったものがあります："
            f"{', '.join(missing)}。"
            "このリーダーは既定では結果を読まないため、これは黙って失われる種類の欠落です"
            f"（{evidence}）。値のない結果を返すより、読み込みを中止します"
        )
