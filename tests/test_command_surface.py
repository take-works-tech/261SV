"""One surface, four callers, and the refusals that keep it one.

INV-006 says the interface, the assistant, a script and a pipeline all act through the same set of
operations and none of them has a private path. That is what makes undo, the run record, the dry run and
the log each need building once - so the tests here are mostly about what the surface refuses, because
each refusal is what keeps the claim true.

CT-002 is explicit about why an unknown parameter is rejected here while CT-001 preserves unknown fields
in a document: a document outlives the program that wrote it and dropping a field destroys somebody's
work, while a command executes immediately and an unrecognised parameter means the caller believes
something is happening that is not.

Verifies: CT-002, CT-003, INV-006, XC-061, XC-102, operations/REQ-004.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

import pytest

from service.command.catalogue import OPERATIONS, READS, WRITES, writes
from service.command.surface import (
    Command,
    Effect,
    Handler,
    Origin,
    Permission,
    Result,
    Status,
    Surface,
    only_reads,
)


def at(hour: int):
    return lambda: datetime(2026, 8, 25, hour, tzinfo=timezone(timedelta(hours=9)))


class Store:
    """Somewhere for a handler to change, so undo has something to put back."""

    def __init__(self) -> None:
        self.names: dict[str, str] = {}

    def rename(self, parameters: Mapping[str, Any], targets: tuple[str, ...]) -> Effect:
        identifier = str(parameters["viewId"])
        before = self.names.get(identifier)
        self.names[identifier] = str(parameters["newName"])

        def undo() -> None:
            if before is None:
                self.names.pop(identifier, None)
            else:
                self.names[identifier] = before

        return Effect(f"{identifier} の名前を変更しました", changed=(identifier,), undo=undo)

    def read(self, parameters: Mapping[str, Any], targets: tuple[str, ...]) -> Effect:
        return Effect("名前を読みました", value=dict(self.names))


def a_surface(store: Store | None = None) -> tuple[Surface, Store]:
    held = store or Store()
    surface = Surface(clock=at(9))
    surface.register(
        Handler(
            "view.rename",
            held.rename,
        )
    )
    surface.register(Handler("history.list", held.read))
    return surface, held


class TestTheCatalogueIsTheSet:
    def test_it_holds_every_operation_the_contract_lists(self) -> None:
        assert len(OPERATIONS) == 61
        assert "view.rename" in OPERATIONS

    def test_reads_and_writes_partition_it(self) -> None:
        assert READS | WRITES == set(OPERATIONS)
        assert not READS & WRITES

    def test_which_one_comes_from_the_contract_rather_than_the_name(self) -> None:
        """`view.render` reads and `view.rename` writes, and nothing about the two names says so."""
        assert writes("view.rename") is True
        assert writes("view.render") is False

    def test_an_unknown_operation_raises_rather_than_defaulting(self) -> None:
        """Defaulting to read lets a write escape the undo history; defaulting to write puts a question
        in front of an answer somebody just asked for."""
        with pytest.raises(KeyError):
            writes("view.explode")


class TestRegistrationIsAgainstTheCatalogue:
    def test_an_operation_the_contract_does_not_list_is_refused(self) -> None:
        surface = Surface()

        with pytest.raises(KeyError) as refusal:
            surface.register(Handler("view.explode", lambda p, t: Effect("")))
        assert "CT-003" in str(refusal.value)

    def test_a_second_implementation_of_one_operation_is_refused(self) -> None:
        surface, store = a_surface()

        with pytest.raises(KeyError):
            surface.register(Handler("view.rename", store.rename))

    def test_a_handler_cannot_say_what_its_operation_accepts(self) -> None:
        """OPEN-028's answer, and the reason it mattered. A handler that declared its own parameters
        would be a second answer to what an operation takes, and the enforcement would then hold against
        the copy rather than against CT-003.

        The first version of this module let a handler declare them, so `view.rename` accepted whatever
        that handler happened to list - which is not what CT-002 promises when it says an unknown
        parameter is rejected.
        """
        import dataclasses

        names = {one.name for one in dataclasses.fields(Handler)}

        assert names == {"operation", "perform", "needs"}

    def test_they_come_from_the_contract(self) -> None:
        from service.command.catalogue import PARAMETERS

        surface, store = a_surface()
        handler = Handler("view.rename", store.rename)

        assert handler.parameters == PARAMETERS["view.rename"][0]
        assert "newName" in handler.required

    def test_every_operation_in_the_catalogue_has_its_parameters_stated(self) -> None:
        """134 parameters over 61 operations, so a handler for any of them is checkable."""
        from service.command.catalogue import OPERATIONS, PARAMETERS

        assert set(PARAMETERS) == set(OPERATIONS)
        assert sum(len(accepted) for accepted, _ in PARAMETERS.values()) == 134

    def test_what_is_not_implemented_is_reportable(self) -> None:
        """A build that answers "unimplemented" for most of the catalogue should be able to say which,
        rather than leaving a caller to discover it one operation at a time."""
        surface, _ = a_surface()

        assert set(surface.registered()) == {"view.rename", "history.list"}
        assert len(surface.unimplemented()) == len(OPERATIONS) - 2


class TestRefusalBeatsAssumption:
    def test_an_unknown_operation_is_refused_and_changes_nothing(self) -> None:
        surface, store = a_surface()

        result = surface.submit(Command("view.explode", {"viewId": "v"}))

        assert result.status is Status.REFUSED
        assert result.changed == ()
        assert store.names == {}

    def test_a_catalogue_operation_with_no_handler_says_so_differently(self) -> None:
        """Two different facts: "there is no such operation" and "this build does not do it yet". A
        caller can act on the second and cannot act on the first."""
        surface, _ = a_surface()

        result = surface.submit(Command("view.duplicate", {"viewId": "v"}))

        assert result.status is Status.REFUSED
        assert "実装がありません" in (result.reason or "")

    def test_an_unknown_parameter_is_rejected(self) -> None:
        """CT-002's strictness, and its reason: an unrecognised parameter means the caller believes
        something is happening that is not."""
        surface, store = a_surface()

        result = surface.submit(
            Command("view.rename", {"viewId": "v", "newName": "n", "force": True})
        )

        assert result.status is Status.REFUSED
        assert "force" in (result.reason or "")
        assert store.names == {}

    def test_a_missing_required_parameter_is_refused(self) -> None:
        surface, _ = a_surface()

        assert surface.submit(Command("view.rename", {"viewId": "v"})).status is Status.REFUSED

    def test_a_refusal_always_carries_a_reason(self) -> None:
        """CT-003 requires it, and a refusal without one is indistinguishable from a silence."""
        with pytest.raises(ValueError):
            Result(Status.REFUSED)

    def test_a_refusal_that_changed_something_is_not_a_refusal(self) -> None:
        with pytest.raises(ValueError):
            Result(Status.REFUSED, changed=("v",), reason="なにか")

    def test_a_handler_that_raises_is_a_failure_rather_than_a_crash(self) -> None:
        surface = Surface(clock=at(9))

        def explode(parameters: Mapping[str, Any], targets: tuple[str, ...]) -> Effect:
            raise RuntimeError("ディスクがいっぱいです")

        surface.register(Handler("view.delete", explode))
        result = surface.submit(Command("view.delete", {"viewId": "v"}))

        assert result.status is Status.FAILED
        assert "ディスク" in (result.reason or "")


class TestAuthorisationIsNeverAssumed:
    def test_an_operation_needing_permission_is_refused_without_it(self) -> None:
        surface = Surface(clock=at(9))
        surface.register(
            Handler(
                "report.export",
                lambda p, t: Effect("書き出しました", undo=lambda: None),
                needs=frozenset({Permission.OVERWRITE}),
            )
        )

        result = surface.submit(Command("report.export", {"reportId": "r", "path": "out"}))

        assert result.status is Status.REFUSED
        assert "allowOverwrite" in (result.reason or "")

    def test_granting_it_lets_the_operation_run(self) -> None:
        surface = Surface(clock=at(9))
        surface.register(
            Handler(
                "report.export",
                lambda p, t: Effect("書き出しました", undo=lambda: None),
                needs=frozenset({Permission.OVERWRITE}),
            )
        )

        result = surface.submit(
            Command(
                "report.export",
                {"reportId": "r", "path": "out"},
                allowed=frozenset({Permission.OVERWRITE}),
            )
        )

        assert result.status is Status.APPLIED


class TestAReadIsNotAWrite:
    def test_a_read_answers_rather_than_applies(self) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("history.list", {"workspaceId": "w"}))

        assert result.status is Status.ANSWERED
        assert result.undo_id is None

    def test_a_read_leaves_nothing_to_undo(self) -> None:
        surface, _ = a_surface()
        surface.submit(Command("history.list", {"workspaceId": "w"}))

        assert surface.undoable() == ()

    def test_a_write_that_cannot_be_undone_is_not_applied(self) -> None:
        """Putting an irreversible change into the history is worse than not making it: the history
        would say it can be taken back."""
        surface = Surface(clock=at(9))
        surface.register(Handler("case.delete", lambda p, t: Effect("消しました")))

        result = surface.submit(Command("case.delete", {"caseId": "c"}))

        assert result.status is Status.FAILED
        assert "元に戻す方法" in (result.reason or "")

    def test_a_caller_can_ask_whether_a_sequence_changes_anything(self) -> None:
        assert only_reads([Command("history.list"), Command("view.render")]) is True
        assert only_reads([Command("history.list"), Command("view.rename")]) is False


class TestADryRunIsTheSameCommand:
    def test_it_reports_the_effect(self) -> None:
        surface, store = a_surface()

        result = surface.submit(
            Command("view.rename", {"viewId": "v", "newName": "新しい名前"}, dry_run=True)
        )

        assert result.status is Status.ANSWERED
        assert "名前を変更" in (result.effect_summary or "")

    def test_it_leaves_nothing_to_undo(self) -> None:
        surface, _ = a_surface()

        surface.submit(Command("view.rename", {"viewId": "v", "newName": "n"}, dry_run=True))

        assert surface.undoable() == ()

    def test_it_is_marked_as_a_dry_run_in_the_log(self) -> None:
        surface, _ = a_surface()
        surface.submit(Command("view.rename", {"viewId": "v", "newName": "n"}, dry_run=True))

        assert surface.history()[-1].dry_run is True
        assert "試算" in surface.history()[-1].describe()

    def test_it_is_refused_by_the_same_rules(self) -> None:
        """A dry run that accepted a command the real one would refuse would be describing an execution
        that cannot happen."""
        surface, _ = a_surface()

        result = surface.submit(
            Command("view.rename", {"viewId": "v", "force": True}, dry_run=True)
        )

        assert result.status is Status.REFUSED


class TestOneInstructionOneUndo:
    def test_a_write_can_be_taken_back(self) -> None:
        surface, store = a_surface()
        applied = surface.submit(Command("view.rename", {"viewId": "v", "newName": "後"}))

        assert store.names == {"v": "後"}
        assert applied.undo_id is not None

        surface.undo(applied.undo_id)

        assert store.names == {}

    def test_a_group_undoes_together(self) -> None:
        """XC-102: one script is one undo step, deliberately unlike the reference application where
        operators called from Python skip the undo stack by default."""
        surface, store = a_surface()

        surface.submit_group(
            [
                Command("view.rename", {"viewId": "a", "newName": "一"}, Origin.SCRIPT),
                Command("view.rename", {"viewId": "b", "newName": "二"}, Origin.SCRIPT),
            ],
            group_id="script:001",
        )
        assert store.names == {"a": "一", "b": "二"}

        surface.undo("script:001")

        assert store.names == {}

    def test_it_undoes_in_reverse(self) -> None:
        """Forwards would put an earlier state back underneath a later one."""
        surface, store = a_surface()
        surface.submit_group(
            [
                Command("view.rename", {"viewId": "v", "newName": "一"}),
                Command("view.rename", {"viewId": "v", "newName": "二"}),
            ],
            group_id="group:001",
        )

        surface.undo("group:001")

        assert store.names == {}

    def test_a_group_with_one_refusal_still_undoes_what_happened(self) -> None:
        """The caller asked for several things, and undoing what did happen is what the group is for."""
        surface, store = a_surface()

        results = surface.submit_group(
            [
                Command("view.rename", {"viewId": "a", "newName": "一"}),
                Command("view.rename", {"viewId": "b"}),
            ],
            group_id="group:002",
        )

        assert [r.status for r in results] == [Status.APPLIED, Status.REFUSED]
        surface.undo("group:002")
        assert store.names == {}

    def test_an_unknown_undo_id_is_refused_rather_than_ignored(self) -> None:
        surface, _ = a_surface()

        assert surface.undo("undo:9999").status is Status.REFUSED

    def test_undoing_twice_is_refused_rather_than_repeated(self) -> None:
        surface, store = a_surface()
        applied = surface.submit(Command("view.rename", {"viewId": "v", "newName": "後"}))
        assert applied.undo_id is not None
        surface.undo(applied.undo_id)

        assert surface.undo(applied.undo_id).status is Status.REFUSED


class TestTheLogIsWhatHistoryReadsBack:
    def test_every_command_is_recorded_including_the_refused_ones(self) -> None:
        """A refusal that leaves no trace is a refusal nobody can investigate."""
        surface, _ = a_surface()
        surface.submit(Command("view.rename", {"viewId": "v", "newName": "n"}))
        surface.submit(Command("view.explode", {}))

        assert [entry.status for entry in surface.history()] == [Status.APPLIED, Status.REFUSED]

    def test_each_line_carries_who_issued_it(self) -> None:
        """"Who changed this" is unanswerable afterwards from a log that treats every caller alike."""
        surface, _ = a_surface()
        surface.submit(Command("view.rename", {"viewId": "v", "newName": "n"}, Origin.ASSISTANT))

        assert surface.history()[-1].origin is Origin.ASSISTANT
        assert "assistant" in surface.history()[-1].describe()

    def test_each_line_carries_when(self) -> None:
        surface, _ = a_surface()
        surface.submit(Command("history.list", {}))

        assert surface.history()[-1].at.utc == "2026-08-25T00:00:00Z"

    def test_the_four_callers_are_the_four_the_contract_names(self) -> None:
        assert {origin.value for origin in Origin} == {
            "interface", "assistant", "script", "pipeline"
        }
