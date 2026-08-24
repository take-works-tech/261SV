"""CT-012's table, exercised rather than read (ingest/TASK-029, TASK-030).

The point of a total table is that it decides every case, so these tests **walk the contract** instead
of listing types beside it. A list written here would be a third copy of the same facts and the one
nobody updates.

The table itself needs no VTK; the conversions do, and they say so.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.conversion import ConversionRecord, ConversionTooLarge
from domain_core.object_compatibility import HANDLING, Disposition, handling


class TestTheTableIsTotalAndUsable:
    def test_every_row_says_enough_to_act_on(self) -> None:
        for name, row in HANDLING.items():
            if row.disposition is Disposition.CONVERT:
                assert row.via and row.costs, f"{name} converts and does not say by what or at what cost"
            if row.disposition is Disposition.REFUSE:
                assert row.reason, f"{name} is refused with no reason"
            if row.disposition is Disposition.DECOMPOSE:
                assert row.into, f"{name} decomposes into nothing stated"

    def test_a_type_outside_the_table_is_a_defect_and_says_so(self) -> None:
        """Not a refusal. A type the table does not mention is a hole in the contract, and answering
        'unsupported' would let the hole pass for a decision."""
        with pytest.raises(KeyError) as refusal:
            handling("vtkSomethingNobodyWroteDown")
        assert "defect in the contract" in str(refusal.value)

    def test_refusal_and_acceptance_are_the_only_two_outcomes(self) -> None:
        for name, row in HANDLING.items():
            assert row.is_accepted is (row.disposition is not Disposition.REFUSE), name

    def test_the_toolkit_s_own_base_classes_are_refused(self) -> None:
        """A reader returning a `vtkDataObject` has told us nothing about what it read, which is a
        reason to stop rather than to guess."""
        for name in ("vtkDataObject", "vtkDataSet", "vtkCompositeDataSet"):
            assert HANDLING[name].disposition is Disposition.REFUSE


class TestARefusalNamesItself:
    """TASK-030. A generic read failure tells a user their file is broken, and sends them looking for
    a corrupt file that does not exist."""

    def test_every_refused_type_carries_a_reason_a_person_can_act_on(self) -> None:
        refused = [name for name, row in HANDLING.items() if row.disposition is Disposition.REFUSE]

        assert len(refused) > 30
        for name in refused:
            reason = HANDLING[name].reason or ""
            assert len(reason) > 20, f"{name}'s reason is too short to tell anyone anything: {reason!r}"

    def test_the_overlapping_amr_refusal_says_what_would_be_wrong(self) -> None:
        """The one refusal that is about arithmetic rather than about domain: its levels overlap by
        construction, so a sum over the leaves counts a refined region once per level."""
        reason = HANDLING["vtkOverlappingAMR"].reason or ""

        assert "level" in reason
        assert "INV-010" in reason


class TestAConversionRecordsWhatItCost:
    def test_a_record_without_a_cost_is_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            ConversionRecord("vtkImageData", "vtkUnstructuredGrid", via="", costs="", cells=1)
        assert "indistinguishable from data that arrived that way" in str(refusal.value)

    def test_the_line_states_the_source_the_filter_and_the_count(self) -> None:
        line = ConversionRecord(
            "vtkImageData", "vtkUnstructuredGrid", via="vtkImageDataToPointSet", costs="…",
            cells=1000, preserved={"spacing": (0.5, 0.5, 2.0)},
        ).describe()

        assert "vtkImageData" in line
        assert "1,000" in line
        assert "spacing" in line


class TestTheConversionsThemselves:
    """These run the filters, so they need VTK."""

    @pytest.fixture(autouse=True)
    def _vtk(self) -> None:
        pytest.importorskip("vtkmodules.vtkFiltersGeneral")

    def image(self, side: int = 11):
        from vtkmodules.vtkCommonDataModel import vtkImageData

        grid = vtkImageData()
        grid.SetDimensions(side, side, side)
        grid.SetSpacing(0.5, 0.5, 2.0)
        grid.SetOrigin(1.0, 2.0, 3.0)
        return grid

    def test_the_cost_is_known_before_the_conversion_runs(self) -> None:
        """AC-032 as written. The count comes from the source, so refusing costs nothing."""
        from engine.conversion import cost_in_cells

        assert cost_in_cells(self.image()) == 1000

    def test_a_conversion_over_budget_is_refused_before_it_runs(self) -> None:
        from engine.conversion import to_unstructured

        with pytest.raises(ConversionTooLarge) as refusal:
            to_unstructured(self.image(), budget=100)
        assert "1,000" in str(refusal.value)
        assert "100" in str(refusal.value)

    def test_an_accepted_cost_runs(self) -> None:
        from engine.conversion import to_unstructured

        grid, _ = to_unstructured(self.image(), budget=100, accepted=True)

        assert grid.GetNumberOfCells() == 1000

    def test_the_spacing_survives_the_conversion_that_destroys_it(self) -> None:
        """The one number in a voxel result that carries a length. After the points are explicit
        nothing in the dataset remembers it, so it is captured or it is lost."""
        from engine.conversion import to_unstructured

        _, record = to_unstructured(self.image())

        assert record.preserved["spacing"] == (0.5, 0.5, 2.0)
        assert record.preserved["origin"] == (1.0, 2.0, 3.0)

    def test_the_filter_is_the_one_the_contract_names(self) -> None:
        """Not a chain that happens to work: what the specification says and what the code does cannot
        be two answers."""
        from engine.conversion import to_unstructured

        _, record = to_unstructured(self.image())

        assert record.via == HANDLING["vtkImageData"].via

    def test_converting_something_the_contract_does_not_convert_is_refused(self) -> None:
        from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid

        from engine.conversion import to_unstructured

        with pytest.raises(ValueError) as refusal:
            to_unstructured(vtkUnstructuredGrid())
        assert "not a conversion" in str(refusal.value)

    def test_a_converted_dataset_carries_the_record(self) -> None:
        from engine.conversion import to_unstructured
        from engine.reader import _as_dataset

        grid, record = to_unstructured(self.image(side=3))
        dataset = _as_dataset(grid, conversion=record)

        assert dataset.conversion is not None
        assert dataset.conversion.source_type == "vtkImageData"
        assert dataset.cell_count == 8
        assert np.array_equal(dataset.cells.types, np.full(8, 12, np.uint8))
