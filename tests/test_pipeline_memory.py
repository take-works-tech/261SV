"""Memory managed by the pipeline rather than by luck, and a clear unit that releases without deleting.

REQ-006's title is the argument. A forty-case study loads forty datasets, and the failure without a
ledger is not a slow run - it is the process being killed, which loses the run record along with
everything else and tells the user nothing about why.

AC-019 asks for the two numbers: what was needed and what was available. "Out of memory" tells a user
nothing they can act on; "this case needs 2.0 KiB and 900 B is free" tells them whether to close the
other window or split the study.

LIM-001 differs by machine class (XC-086), and the direction of the mistake matters: the workstation's
budget handed to a laptop is twice what that class allows, which is the direction that ends with the
operating system making the decision.

Verifies: pipeline/AC-018, AC-019, pipeline/TASK-032, TASK-033, LIM-001, XC-086.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from domain_core.locale_format import bytes_as_text
from engine.limits import (
    MAX_DATASET_BYTES,
    MAX_DATASET_BYTES_BY_CLASS,
    MachineClass,
    dataset_budget_bytes,
)
from service.pipeline.document import (
    DefinitionRef,
    Kind,
    Source,
    add,
    add_cases_unit,
    artefact_unit,
)
from service.pipeline.memory import Ledger, MemoryRefusal
from service.pipeline.run import Authorisation, Outcome, RunError, run

VIEW_REF = DefinitionRef(Source.WORKSPACE_ITEM, "view:001", 1)
CASES = ["case:001", "case:002", "case:003"]


def a_pipeline(*, with_clear: bool = False) -> dict[str, Any]:
    document: dict[str, Any] = {"id": "pipeline:001", "units": []}
    add(document, add_cases_unit("unit:cases", CASES))
    add(document, artefact_unit("unit:view", Kind.VIEW, VIEW_REF))
    if with_clear:
        add(document, {"id": "unit:clear", "kind": Kind.CLEAR.value})
    return document


class TestTheBudgetSaysWhichMachineItIsFor:
    def test_the_two_classes_are_the_two_XC_086_names(self) -> None:
        assert set(MAX_DATASET_BYTES_BY_CLASS) == {
            MachineClass.WORKSTATION, MachineClass.INTEGRATED
        }

    def test_the_constant_is_the_workstation_figure(self) -> None:
        """LIM-001's rationale is a 32 GB workstation. The module docstring used to say every constant
        in the file was the integrated-graphics class, which is right for LIM-002 and wrong here - so a
        build reading the constant on a laptop would have allowed twice what the limit permits."""
        assert dataset_budget_bytes(MachineClass.WORKSTATION) == MAX_DATASET_BYTES

    def test_the_laptop_gets_half_of_it(self) -> None:
        assert dataset_budget_bytes(MachineClass.INTEGRATED) == MAX_DATASET_BYTES // 2

    def test_the_halving_is_derived_rather_than_written_twice(self) -> None:
        """Two literals a factor of two apart are two numbers to keep in step, and the day they part
        company is the day one of them is wrong and nothing says so."""
        assert (
            MAX_DATASET_BYTES_BY_CLASS[MachineClass.INTEGRATED] * 2
            == MAX_DATASET_BYTES_BY_CLASS[MachineClass.WORKSTATION]
        )

    def test_a_run_with_a_budget_and_no_way_to_size_a_case_is_refused(self) -> None:
        """A budget with nothing to measure against measures nothing, and the pipeline would report a
        ledger it never consulted."""
        with pytest.raises(RunError):
            run(a_pipeline(), cases=CASES, budget_bytes=1000)

    def test_and_the_other_way_round(self) -> None:
        with pytest.raises(RunError):
            run(a_pipeline(), cases=CASES, size_of=lambda case: 1)


class TestTheLedgerHoldsAndReleases:
    def test_holding_counts_against_the_budget(self) -> None:
        ledger = Ledger(1000)
        ledger.hold("case:001", 400)

        assert ledger.held_bytes == 400
        assert ledger.available_bytes == 600

    def test_holding_the_same_case_twice_is_not_a_second_charge(self) -> None:
        """A case is loaded once and every unit below acts on the same loaded data."""
        ledger = Ledger(1000)
        ledger.hold("case:001", 400)
        ledger.hold("case:001", 400)

        assert ledger.held_bytes == 400

    def test_a_hold_past_the_budget_is_refused_with_both_numbers(self) -> None:
        """AC-019."""
        ledger = Ledger(1000)
        ledger.hold("case:001", 900)

        with pytest.raises(MemoryRefusal) as refusal:
            ledger.hold("case:002", 500)

        assert refusal.value.needed == 500
        assert refusal.value.available == 100
        assert "500 B" in str(refusal.value) and "100 B" in str(refusal.value)
        assert "LIM-001" in str(refusal.value)

    def test_releasing_frees_the_room_for_the_next_case(self) -> None:
        ledger = Ledger(1000)
        ledger.hold("case:001", 900)
        ledger.release("case:001")

        ledger.hold("case:002", 900)

        assert ledger.held_bytes == 900

    def test_the_log_answers_what_was_held_when(self) -> None:
        ledger = Ledger(1000)
        ledger.hold("case:001", 400)
        ledger.release("case:001")

        assert len(ledger.log) == 2
        assert "確保" in ledger.log[0] and "解放" in ledger.log[1]


class TestOneCaseTooLargeStopsThatCase:
    def test_the_others_complete(self) -> None:
        """AC-019 and XC-095 are the same shape: the refusal travels the path a per-case failure already
        travels, so the study continues."""
        record = run(
            a_pipeline(), cases=CASES, budget_bytes=1000,
            size_of=lambda case: 2000 if case == "case:002" else 100,
        )

        done = {r.case_id for r in record.results if r.outcome is Outcome.DONE and r.case_id}
        assert done == {"case:001", "case:003"}
        assert record.failed_cases == ("case:002",)

    def test_the_record_states_what_was_needed_and_what_was_available(self) -> None:
        record = run(
            a_pipeline(), cases=CASES, budget_bytes=1000,
            size_of=lambda case: 2000 if case == "case:002" else 100,
        )

        detail = next(r.detail or "" for r in record.results if r.outcome is Outcome.FAILED)
        assert "2.0 KiB" in detail
        assert "900 B" in detail

    def test_the_process_survives_rather_than_being_terminated(self) -> None:
        """The whole point of AC-019: the product refuses instead of the operating system deciding.
        Asserted by the run returning a record at all."""
        record = run(
            a_pipeline(), cases=CASES, budget_bytes=1, size_of=lambda case: 1_000_000
        )

        assert len(record.failed_cases) == len(CASES)
        assert record.describe()

    def test_a_run_with_no_budget_holds_nothing(self) -> None:
        """None means the caller has not said which machine class this is, not that memory is
        unlimited - so nothing here invents a budget to check against."""
        record = run(a_pipeline(), cases=CASES)

        assert record.failed_cases == ()


class TestAClearUnitReleasesWithoutDeleting:
    def test_it_empties_the_target_set(self) -> None:
        """AC-018. Authorised, because an unauthorised clear does not clear - and asserting "empty or
        done" would have passed either way, which is not a test."""
        document = a_pipeline(with_clear=True)
        add(document, artefact_unit("unit:after", Kind.REPORT, VIEW_REF))

        record = run(document, cases=CASES, authorisations=[Authorisation("unit:clear", 3)])

        after = next(r for r in record.results if r.unit_id == "unit:after")
        assert after.outcome is Outcome.SKIPPED_EMPTY

    def test_an_unauthorised_clear_leaves_the_set_alone(self) -> None:
        """The other half of the same behaviour, and the reason the assertion above has to be exact."""
        document = a_pipeline(with_clear=True)
        add(document, artefact_unit("unit:after", Kind.REPORT, VIEW_REF))

        record = run(document, cases=CASES, authorisations=[])

        assert {r.case_id for r in record.results if r.unit_id == "unit:after"} == set(CASES)

    def test_it_releases_what_the_run_was_holding(self) -> None:
        ledger = Ledger(1000)
        ledger.hold("case:001", 300)
        ledger.hold("case:002", 300)

        freed = ledger.release_all("unit:clear")

        assert freed == 600
        assert ledger.held_bytes == 0

    def test_the_release_is_recorded_on_the_unit(self) -> None:
        document = a_pipeline(with_clear=True)
        record = run(
            document, cases=CASES, budget_bytes=10_000, size_of=lambda case: 100,
            authorisations=[Authorisation("unit:clear", 3)],
        )

        detail = next(r.detail or "" for r in record.results if r.unit_id == "unit:clear")
        assert "解放" in detail
        assert "元ファイルには触れていません" in detail

    def test_no_source_file_is_touched(self, tmp_path: Path) -> None:
        """AC-018's second half. What this proves is narrow and worth stating: the pipeline layer holds
        integers and case identifiers and has no path to a file, so the check is that it stays that way
        rather than a demonstration that some deletion was averted."""
        sources = []
        for name in ("a.vtu", "b.vtu"):
            path = tmp_path / name
            path.write_bytes(b"points and cells")
            sources.append(path)
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}

        run(
            a_pipeline(with_clear=True), cases=CASES, budget_bytes=10_000,
            size_of=lambda case: 100, authorisations=[Authorisation("unit:clear", 3)],
        )

        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        assert after == before

    def test_the_ledger_module_names_no_path_type_at_all(self) -> None:
        """Structural, and the reason the test above can be narrow: a module that cannot express a file
        cannot touch one."""
        import service.pipeline.memory as memory

        source = Path(memory.__file__).read_text(encoding="utf-8")
        for door in ("Path", "open(", "os.", "shutil", "unlink", "remove("):
            assert door not in source, door


class TestByteCountsAreWrittenOneWay:
    def test_the_steps_are_binary_and_so_are_the_names(self) -> None:
        """1 << 30 bytes is a gibibyte. Two call sites each carried their own copy of this, identical
        and both labelled GB, which is the arrangement where one gets fixed and the other keeps
        printing the old answer."""
        assert bytes_as_text(1 << 30) == "1.0 GiB"
        assert bytes_as_text(1 << 20) == "1.0 MiB"
        assert bytes_as_text(1 << 10) == "1.0 KiB"
        assert bytes_as_text(512) == "512 B"

    def test_it_agrees_with_what_the_limit_states_about_itself(self) -> None:
        """LIM-001's human_value says 8 GiB."""
        assert bytes_as_text(MAX_DATASET_BYTES) == "8.0 GiB"
