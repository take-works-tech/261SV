"""The regression set is a gate (XC-307; #203): every reader this build has is held to a whole
fixture and a broken one, every required kind is present, every fixture writes and reads as its kind
says - a whole file with points, a partial case that says so, a broken file refused by name, a
million-cell grid read whole - and the Verified formats this build does not read yet are named here,
so that the table in XC-049 cannot imply a regression test that does not exist."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from conftest import requires_h5py, requires_vtk

requires_vtk()

from engine import reader  # noqa: E402
from engine.completeness import FileIncomplete, ResultsLost  # noqa: E402
from regression_catalogue import FIXTURES, REQUIRED_KINDS, VERIFIED_WITHOUT_READER, Fixture, by_format  # noqa: E402

REFUSALS = (reader.UnsupportedFormatError, reader.UnreadableFileError, FileIncomplete, ResultsLost)


class TestTheSetIsComplete:
    def test_every_reader_this_build_has_is_held_to_a_whole_fixture_and_a_broken_one(self) -> None:
        readers = sorted(reader._READERS)  # noqa: SLF001 - the table is the fact under test
        assert readers, "no readers"
        lacking = {
            suffix: [kind for kind in ("normal", "broken") if not any(one.kind == kind for one in by_format(suffix))]
            for suffix in readers
        }
        # Exodus answers to three suffixes through one reader; one fixture family covers them.
        exodus = {".e", ".ex2", ".exo"}
        for suffix in exodus & set(readers):
            if any(one.format in exodus for one in FIXTURES):
                lacking[suffix] = []
        assert not {suffix: kinds for suffix, kinds in lacking.items() if kinds}, lacking

    def test_every_required_kind_is_present_and_every_id_is_one_fixture(self) -> None:
        present = {one.kind for one in FIXTURES}
        assert set(REQUIRED_KINDS) <= present, sorted(set(REQUIRED_KINDS) - present)
        ids = [one.id for one in FIXTURES]
        assert len(ids) == len(set(ids)), "a fixture id names one fixture"
        assert all(one.proves for one in FIXTURES), "every fixture says what it proves"

    def test_the_verified_tier_names_formats_this_build_does_not_read_yet(self) -> None:
        """XC-049 lists EnSight Gold and VTKHDF as Verified; no reader here takes their files. Held so
        that wiring one is the moment this list shrinks and the table becomes true (#426)."""
        assert VERIFIED_WITHOUT_READER == ("EnSight Gold", "VTKHDF")
        assert not {".case", ".vtkhdf", ".hdf"} & set(reader._READERS)  # noqa: SLF001


@pytest.mark.parametrize("fixture", FIXTURES, ids=[one.id for one in FIXTURES])
def test_each_fixture_writes_and_reads_as_its_kind_says(tmp_path: Path, fixture: Fixture) -> None:
    if fixture.needs == "h5py":
        requires_h5py()
    path = tmp_path / f"{fixture.id.replace('/', '-')}{fixture.format}"

    fixture.write(path)

    assert path.exists(), f"{fixture.id}: nothing written"
    if fixture.kind == "broken":
        with pytest.raises(REFUSALS) as refusal:
            reader.read_case(path)
        assert path.name in str(refusal.value) or fixture.format in str(refusal.value), f"{fixture.id}: the refusal names neither the file nor its format: {refusal.value}"
        return
    started = time.perf_counter()
    case = reader.read_case(path)
    elapsed = time.perf_counter() - started
    points = sum(part.dataset.point_count for part in case.present if part.dataset is not None)
    assert points > 0, f"{fixture.id}: read with no points"
    if fixture.kind == "partial":
        assert case.is_partial, f"{fixture.id}: expected a partial case"
        assert case.contents.missing_parts, f"{fixture.id}: a partial case names what is missing"
    else:
        assert not case.is_partial, f"{fixture.id}: read as partial: {case.describe()}"
    if fixture.kind == "large":
        cells = sum(part.dataset.cell_count for part in case.present if part.dataset is not None)
        assert cells == 1_000_000 and points == 1_030_301
        print(f"large: {points} points, {cells} cells, {path.stat().st_size / 1e6:.1f} MB, read in {elapsed:.2f} s (this machine)")
