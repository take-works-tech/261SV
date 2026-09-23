"""EnSight Gold and VTKHDF, read through the product's reader (ingest/AC-052, XC-308; #426).

The toolkit's EnSight reader, measured on files its own writer produced, takes the process down on a
geometry file cut in half, loops forever on a case file cut in half, and reads a geometry cut at
99 per cent, a cut variable file and a cut ASCII geometry as whole (E-227). So every file a case
names is walked by its own counts before the reader sees any of it, and these tests hold that: whole
files read with the values their writer put in, in either byte order, and every cut is a refusal
that names the case and the file, within seconds, with the process still here to say so. VTKHDF is
held to the same: random bytes, an empty file and a file cut short are refused by name before the
read, and a whole one reads with its values.
"""

from __future__ import annotations

import random
import struct
import time
from pathlib import Path

import numpy as np
import pytest
from conftest import requires_vtk

requires_vtk()

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet  # noqa: E402
from vtkmodules.vtkIOEnSight import vtkGenericEnSightReader  # noqa: E402

from engine import ensight, reader  # noqa: E402
from engine.completeness import FileIncomplete, ResultsLost, hdf5_signature_present  # noqa: E402
from demo_case import write_ensight, write_ensight_ascii, write_ensight_transient, write_vtkhdf  # noqa: E402
from regression_catalogue import cut_companion, truncated  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from test_handlers import loaded, opened  # noqa: E402

REFUSALS = (reader.UnreadableFileError, FileIncomplete, ResultsLost)
#: A refusal has to come back, and soon: the toolkit's reader, given two of these files, did not come
#: back at all (E-227). Generous, because a shared runner is not this machine.
PROMPT_SECONDS = 5.0


def values(case: object, part_name: str, field: str) -> list[float]:
    part = next(one for one in case.present if one.name == part_name)  # type: ignore[attr-defined]
    return part.dataset.fields[field].values.ravel().tolist()


def refused(path: Path) -> str:
    started = time.perf_counter()
    with pytest.raises(REFUSALS) as refusal:
        reader.read_case(path)
    elapsed = time.perf_counter() - started
    assert elapsed < PROMPT_SECONDS, f"{path.name}: refused, but after {elapsed:.1f} s"
    return str(refusal.value)


def write_binary_gold(path: Path, order: str) -> None:
    """The one-part sheet as binary Gold in the byte order given, written by hand: node and element
    ids given, one tria3 block, a node scalar and an element scalar - the layout the format
    specifies, independent of what the toolkit's writer happens to produce."""

    def line(text: str) -> bytes:
        return text.encode("ascii").ljust(80, b"\0")

    def ints(*numbers: int) -> bytes:
        return struct.pack(f"{order}{len(numbers)}i", *numbers)

    def floats(*numbers: float) -> bytes:
        return struct.pack(f"{order}{len(numbers)}f", *numbers)

    stem = path.stem
    geometry = (
        line("C Binary") + line("written by hand") + line("sheet") + line("node id given") + line("element id given")
        + line("part") + ints(1) + line("sheet") + line("coordinates") + ints(4) + ints(1, 2, 3, 4)
        + floats(0.0, 1.0, 1.0, 0.0) + floats(0.0, 0.0, 1.0, 1.0) + floats(0.0, 0.0, 0.0, 0.0)
        + line("tria3") + ints(2) + ints(1, 2) + ints(1, 2, 3, 1, 3, 4)
    )
    (path.parent / f"{stem}.geo").write_bytes(geometry)
    (path.parent / f"{stem}.temperature").write_bytes(
        line("temperature") + line("part") + ints(1) + line("coordinates") + floats(300.0, 310.0, 320.0, 330.0)
    )
    (path.parent / f"{stem}.load").write_bytes(line("load") + line("part") + ints(1) + line("tria3") + floats(1.5, 2.5))
    path.write_text(
        f"FORMAT\ntype: ensight gold\nGEOMETRY\nmodel: {stem}.geo\nVARIABLE\n"
        f"scalar per node: temperature {stem}.temperature\nscalar per element: load {stem}.load\n",
        encoding="ascii",
    )


class TestEnSightGoldReadsWhole:
    def test_a_binary_case_by_the_toolkits_writer(self, tmp_path: Path) -> None:
        path = tmp_path / "sheet.case"
        write_ensight(path)

        case = reader.read_case(path)

        assert [part.name for part in case.present] == ["VTK Part"], "the part is named by the geometry's description"
        assert (case.contents.steps, case.contents.parts) == (1, 1)
        temperature = case.present[0].dataset.fields["temperature_n"]
        assert temperature.values.dtype == np.float32, "stored as the file gave it"
        assert temperature.values.tolist() == [300.0, 310.0, 320.0, 330.0]
        assert values(case, "VTK Part", "load_c") == [1.5, 2.5]
        assert reader.support_level(path)[0] == "Verified"
        # The fingerprint covers every file the case names - and not the BlockId file the writer
        # wrote beside them and the case does not list.
        assert set(reader.snapshot(path)) == {"sheet.case", "sheet.0.00000.geo", "sheet.0.00000_n.temperature", "sheet.0.00000_c.load"}

    def test_an_ascii_case_written_by_hand(self, tmp_path: Path) -> None:
        path = tmp_path / "sheet.case"
        write_ensight_ascii(path)

        case = reader.read_case(path)

        assert [part.name for part in case.present] == ["sheet"]
        assert values(case, "sheet", "temperature") == [300.0, 310.0, 320.0, 330.0]
        assert values(case, "sheet", "load") == [1.5, 2.5]

    @pytest.mark.parametrize("order", ["<", ">"], ids=["little-endian", "big-endian"])
    def test_a_binary_case_in_either_byte_order(self, tmp_path: Path, order: str) -> None:
        path = tmp_path / "sheet.case"
        write_binary_gold(path, order)

        case = reader.read_case(path)

        assert [part.name for part in case.present] == ["sheet"]
        assert values(case, "sheet", "temperature") == [300.0, 310.0, 320.0, 330.0]
        assert values(case, "sheet", "load") == [1.5, 2.5]
        assert case.present[0].dataset.cell_count == 2

    def test_two_parts_and_two_steps(self, tmp_path: Path) -> None:
        path = tmp_path / "sweep.case"
        write_ensight_transient(path)

        first = reader.read_case(path)
        second = reader.read_case(path, step=1)

        assert [part.name for part in first.present] == ["part 1", "part 2"]
        assert first.contents.steps == 2 and first.contents.axis.positions == (0.0, 1.0)
        assert values(first, "part 1", "temperature_n") == [300.0, 310.0, 320.0, 330.0]
        assert values(first, "part 2", "temperature_n") == [310.0, 320.0, 340.0, 350.0], "part 2 is the sheet's other four nodes"
        assert values(second, "part 2", "temperature_n") == [320.0, 330.0, 350.0, 360.0], "the second step's file"
        assert values(second, "part 1", "load_c") == [3.5, 4.5] and values(second, "part 2", "load_c") == [5.5, 6.5]
        assert len(reader.snapshot(path)) == 6, "the case, the geometry and two files per variable"

    def test_a_variable_the_reader_dropped_is_a_result_lost(self, tmp_path: Path) -> None:
        """The reader, measured on a cut variable file, returned the part with the variable silently
        missing (E-227); the check after the read is what turns that into a refusal."""
        path = tmp_path / "sheet.case"
        write_ensight(path)
        source = vtkGenericEnSightReader()
        source.SetCaseFileName(str(path))

        with pytest.raises(ResultsLost) as refusal:
            ensight.verify(source, vtkMultiBlockDataSet())

        assert "temperature_n" in str(refusal.value) and "load_c" in str(refusal.value) and "sheet.case" in str(refusal.value)

    def test_it_loads_through_the_handlers_and_the_record_holds_the_case_file(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_ensight, name="sheet.case")

        inspected = surface.submit(Command("dataset.inspect", {"path": str(tmp_path / "sheet.case")}))

        assert inspected.status is Status.ANSWERED
        assert inspected.value["supportLevel"] == "Verified" and any("E-227" in gap for gap in inspected.value["gaps"])
        assert "refusal" not in inspected.value
        assert sorted(session.datasets[dataset_id].case.present[0].dataset.fields) == ["load_c", "temperature_n"]
        assert [one["pathRelative"] for one in session.workspace.cases[0]["sources"]] == ["sheet.case"], "the record holds the case file; the files it names are found through it"


class TestACutEnSightFileIsRefusedBeforeTheRead:
    """Each of these, handed to the toolkit's reader as it stands, crashed the process, hung it, or
    read as whole (E-227). Here each is a refusal that names the case and the file, and comes back."""

    @pytest.mark.parametrize(
        ("label", "write", "named"),
        [
            ("the case file cut in half", truncated(write_ensight, 0.5), ("sheet.case",)),
            ("the case file cut at 90 per cent", truncated(write_ensight, 0.9), ("sheet.case",)),
            ("the geometry cut in half", cut_companion(write_ensight, ".geo", 0.5), ("sheet.case", "sheet.0.00000.geo", "E-227")),
            ("the geometry cut at 99 per cent", cut_companion(write_ensight, ".geo", 0.99), ("sheet.case", "sheet.0.00000.geo", "E-227")),
            ("a variable file cut in half", cut_companion(write_ensight, "_n.temperature", 0.5), ("sheet.case", "temperature_n", "sheet.0.00000_n.temperature")),
            ("an ASCII geometry cut in half", cut_companion(write_ensight_ascii, ".geo", 0.5), ("sheet.case", "sheet.geo")),
            ("an ASCII variable file cut in half", cut_companion(write_ensight_ascii, ".temperature", 0.5), ("sheet.case", "sheet.temperature")),
        ],
        ids=lambda one: one if isinstance(one, str) else "",
    )
    def test_each_cut_is_refused_by_name(self, tmp_path: Path, label: str, write: object, named: tuple[str, ...]) -> None:
        path = tmp_path / "sheet.case"
        write(path)  # type: ignore[operator]

        message = refused(path)

        for expected in named:
            assert expected in message, f"{label}: {expected!r} is not named in: {message}"

    def test_a_case_naming_a_file_that_is_not_there_is_refused_with_both_names(self, tmp_path: Path) -> None:
        path = tmp_path / "sheet.case"
        write_ensight(path)
        (tmp_path / "sheet.0.00000.geo").unlink()

        message = refused(path)

        assert "sheet.case" in message and "sheet.0.00000.geo" in message and "がありません" in message

    def test_random_bytes_and_an_empty_file_are_refused_as_not_a_case(self, tmp_path: Path) -> None:
        junk = tmp_path / "junk.case"
        junk.write_bytes(random.Random(426).randbytes(4096))
        empty = tmp_path / "empty.case"
        empty.write_bytes(b"")

        assert "junk.case" in refused(junk) and "case ファイルではないか" in refused(junk)
        assert "empty.case" in refused(empty) and "空です" in refused(empty)
        assert "テキストではない" in refused(junk), "random bytes are not quoted back"

    def test_what_this_build_does_not_read_is_refused_by_name_before_the_reader(self, tmp_path: Path) -> None:
        """A changing geometry, a constant, several time sets, a structured part, an extents line and
        a partial variable are what the toolkit's reader reads and nothing here can check; each is
        named rather than handed over (E-227)."""
        path = tmp_path / "sheet.case"
        write_ensight_ascii(path)
        text = path.read_text(encoding="ascii")
        geometry = tmp_path / "sheet.geo"
        geometry_text = geometry.read_text(encoding="ascii")

        path.write_text(text.replace("model: sheet.geo", "model: 1 sheet.geo change_coords_only"), encoding="ascii")
        assert "形状が時刻で変わる" in refused(path)
        path.write_text(text + "constant per case: gravity 9.81\n", encoding="ascii")
        assert "constant" in refused(path) and "この版では読みません" in refused(path)
        path.write_text(text + "TIME\ntime set: 1\nnumber of steps: 1\nfilename start number: 0\nfilename increment: 1\ntime values: 0.0\ntime set: 2\nnumber of steps: 1\nfilename start number: 0\nfilename increment: 1\ntime values: 0.0\n", encoding="ascii")
        assert "時刻集合が二つ以上" in refused(path)
        path.write_text(text, encoding="ascii")

        geometry.write_text(geometry_text.replace("coordinates", "block"), encoding="ascii")
        assert "coordinates" in refused(path) and "sheet.geo" in refused(path)
        geometry.write_text(geometry_text.replace("part\n", "extents\n 0.0 1.0\n 0.0 1.0\n 0.0 0.0\npart\n", 1), encoding="ascii")
        assert "extents" in refused(path)
        geometry.write_text(geometry_text, encoding="ascii")

        temperature = tmp_path / "sheet.temperature"
        temperature.write_text(temperature_text := temperature.read_text(encoding="ascii").replace("coordinates", "coordinates partial"), encoding="ascii")
        assert temperature_text and "partial" in refused(path)


class TestVTKHDF:
    def test_a_grid_by_the_toolkits_writer_reads_whole(self, tmp_path: Path) -> None:
        path = tmp_path / "grid.vtkhdf"
        write_vtkhdf(path)

        case = reader.read_case(path)

        assert sorted(case.present[0].dataset.fields) == ["load", "temperature"]
        assert case.present[0].dataset.fields["temperature"].values.dtype == np.float32
        assert values(case, "grid", "temperature") == [300.0, 310.0, 320.0, 330.0]
        assert values(case, "grid", "load") == [1.5, 2.5]
        assert reader.support_level(path)[0] == "Verified"
        assert set(reader.snapshot(path)) == {"grid.vtkhdf"}

    def test_random_bytes_an_empty_file_and_a_cut_file_are_refused_before_the_read(self, tmp_path: Path) -> None:
        junk = tmp_path / "junk.vtkhdf"
        junk.write_bytes(random.Random(426).randbytes(4096))
        empty = tmp_path / "empty.vtkhdf"
        empty.write_bytes(b"")
        cut = tmp_path / "cut.vtkhdf"
        truncated(write_vtkhdf, 0.5)(cut)

        assert "junk.vtkhdf" in refused(junk) and "HDF5 の署名がありません" in refused(junk)
        assert "empty.vtkhdf" in refused(empty) and "HDF5 の署名がありません" in refused(empty)
        assert "cut.vtkhdf" in refused(cut) and "開けません" in refused(cut) and "E-227" in refused(cut)

    def test_the_signature_is_found_where_the_format_allows_it(self, tmp_path: Path) -> None:
        """HDF5 allows a user block of 512, 1024, ... bytes before the superblock; the signature is
        then at that offset, and the file is still HDF5 to the library."""
        plain = tmp_path / "plain.vtkhdf"
        write_vtkhdf(plain)
        body = plain.read_bytes()
        with_user_block = tmp_path / "user-block.vtkhdf"
        with_user_block.write_bytes(b"\x00" * 512 + body)
        junk = tmp_path / "junk.vtkhdf"
        junk.write_bytes(b"\x00" * 512 + b"not hdf5")

        assert hdf5_signature_present(plain) and hdf5_signature_present(with_user_block)
        assert not hdf5_signature_present(junk)
        assert values(reader.read_case(with_user_block), "user-block", "load") == [1.5, 2.5], "the library reads past a user block"


class TestTheTableOfXC049IsTrueOfThisBuild:
    def test_both_formats_are_verified_with_their_gaps_named(self, tmp_path: Path) -> None:
        for suffix in (".case", ".vtkhdf"):
            level, gaps = reader.support_level(tmp_path / f"a{suffix}")
            assert level == "Verified", suffix
            assert "unexercised" in gaps or "E-227" in gaps, f"{suffix}: the measured edge of the promise is named"
        assert {".case", ".vtkhdf"} <= set(reader.supported_suffixes())

    def test_the_reader_is_given_the_case_through_its_own_setter(self, tmp_path: Path) -> None:
        """`SetCaseFileName`, not `SetFileName`; and the name it keeps is the name alone, so the
        path is put back together from the directory it keeps beside it (measured)."""
        path = tmp_path / "sheet.case"
        write_ensight(path)
        source = vtkGenericEnSightReader()

        ensight.feed_path(source, str(path))

        assert Path(source.GetCaseFileName()).name == "sheet.case"
        assert ensight.case_path_of(source) == path
        surface, session, workspace = opened(tmp_path)
        assert surface.submit(Command("dataset.inspect", {"path": str(path)})).value["format"] == "case"
