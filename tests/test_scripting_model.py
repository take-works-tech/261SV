"""What a script can reach, and what opening a workspace must never start.

AC-035 asks that a script build the same declarative document the editor builds, openable and editable
by hand afterwards. The test for that is equality, not resemblance: two documents that merely look alike
diverge on the first rule one of them enforces and the other does not.

AC-036 is the security half of the same decision (XC-102). Opening a workspace runs nothing, and running
a stored pipeline executes no Python - a workspace arrives by email, and a document that can start an
interpreter is a document that can do anything the person who opened it can do.

XC-103's lookup rule is here too, and it is where the two reference products disagree with each other and
with this one: one appends a numeric suffix so `Cube` becomes `Cube.002` (E-064), the other returns every
match so the documented idiom is to take the first and hope (E-067). Refusing is the only one of the
three that never quietly points a reference at the wrong object.

Verifies: pipeline/AC-035, AC-036, XC-102, XC-103, XC-061, pipeline/TASK-035, TASK-036.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import pytest

from service.command.surface import Command, Effect, Handler, Origin, Status, Surface
from service.pipeline.document import (
    DefinitionRef,
    Kind,
    PipelineError,
    Source,
    add,
    add_cases_unit,
    artefact_unit,
    variable_unit,
)
from service.scripting.model import Collection, Named, ScriptError, Session

VIEW_REF = DefinitionRef(Source.WORKSPACE_ITEM, "view:001", 1)
CASES = ["case:001", "case:002", "case:003"]


def at(hour: int):
    return lambda: datetime(2026, 8, 25, hour, tzinfo=timezone(timedelta(hours=9)))


def a_session() -> Session:
    surface = Surface(clock=at(9))
    store: dict[str, str] = {}

    def rename(parameters: Mapping[str, Any], targets: tuple[str, ...]) -> Effect:
        identifier = str(parameters["viewId"])
        before = store.get(identifier)

        def undo() -> None:
            if before is None:
                store.pop(identifier, None)
            else:
                store[identifier] = before

        store[identifier] = str(parameters["newName"])
        # The result CT-003 states for a rename: the item and its new revision.
        return Effect(
            "名前を変更しました",
            changed=(identifier,),
            value={"id": identifier, "revision": len(store) + 1},
            undo=undo,
        )

    surface.register(
        Handler(
            "view.rename",
            rename,
        )
    )
    surface.register(
        Handler(
            "history.list",
            lambda p, t: Effect("読みました", value={"entries": []}),
        )
    )
    session = Session(surface, group_id="script:001")
    session.views.add(Named("view:001", "Pressure top"))
    session.cases.add(Named("case:001", "Run 12"))
    return session


class TestAScriptBuildsTheSameDocument:
    def test_it_equals_one_built_by_hand(self) -> None:
        """AC-035, asserted by comparison. Resemblance is not the property: two documents that look
        alike diverge on the first rule one of them enforces and the other does not."""
        by_hand: dict[str, Any] = {"id": "pipeline:001", "name": "毎回の確認", "units": []}
        add(by_hand, add_cases_unit("unit:cases", CASES))
        add(by_hand, artefact_unit("unit:view", Kind.VIEW, VIEW_REF))
        add(by_hand, variable_unit("unit:v", "inlet", value=3.0, unit_symbol="m"))

        script = a_session().pipeline("pipeline:001", "毎回の確認")
        script.add_cases("unit:cases", CASES).view("unit:view", VIEW_REF)
        script.variable("unit:v", "inlet", value=3.0, unit_symbol="m")

        assert script.document == by_hand

    def test_it_is_refused_by_the_same_rules(self) -> None:
        """A builder that assembled the dictionary itself would be a second implementation of the
        edit-time rules, and the copy would be the one that stopped refusing."""
        script = a_session().pipeline("pipeline:001", "毎回の確認")
        script.add_cases("unit:cases", CASES)

        with pytest.raises(PipelineError):
            script.add_cases("unit:cases", CASES)

    def test_an_unbound_name_in_a_formula_is_refused_here_too(self) -> None:
        script = a_session().pipeline("pipeline:001", "毎回の確認")

        with pytest.raises(PipelineError):
            script.formula("unit:f", "x", "nowhere * 2")

    def test_a_formula_may_name_what_the_workspace_supplies(self) -> None:
        """A formula reads recorded quantities of a case, which no unit above it binds. Refusing those
        would refuse every expression the pipeline exists to evaluate."""
        script = a_session().pipeline("pipeline:001", "毎回の確認")

        script.formula("unit:f", "margin", "peak * 2", outside=["peak"])

        assert script.document["units"][0]["id"] == "unit:f"

    def test_a_reference_is_pinned_to_the_revision_the_item_has_now(self) -> None:
        """A reference that quietly becomes the newest revision is a pipeline whose output changed
        because somebody else edited a definition."""
        session = a_session()

        reference = session.reference(session.views["Pressure top"])

        assert reference == DefinitionRef(Source.WORKSPACE_ITEM, "view:001", 1)


class TestLookupResolvesToOneObjectOrRaises:
    def test_a_name_that_is_not_there_raises_and_lists_what_is(self) -> None:
        session = a_session()

        with pytest.raises(ScriptError) as refusal:
            session.views["Pressure bottom"]
        assert "Pressure top" in str(refusal.value)

    def test_a_duplicate_name_raises_rather_than_returning_either(self) -> None:
        """The other reference product returns every match and its own documentation says the lookup is
        robust only where names happen to be unique."""
        crowded = Collection("ビュー", [Named("a", "同じ名前"), Named("b", "同じ名前")])

        with pytest.raises(ScriptError) as refusal:
            crowded["同じ名前"]
        assert "XC-103" in str(refusal.value)

    def test_creating_a_name_in_use_is_refused_naming_what_holds_it(self) -> None:
        """Not a numeric suffix. `Cube` becoming `Cube.002` hands a script something other than what it
        asked for, without saying so."""
        session = a_session()

        with pytest.raises(ScriptError) as refusal:
            session.views.add(Named("view:002", "Pressure top"))
        assert "view:001" in str(refusal.value)

    def test_lookup_never_returns_a_list(self) -> None:
        session = a_session()

        assert isinstance(session.views["Pressure top"], Named)

    def test_an_identifier_is_what_a_stored_reference_uses(self) -> None:
        """Renaming rewires nothing, because nothing stored ever pointed at the name."""
        session = a_session()

        assert session.views.by_id("view:001").name == "Pressure top"


class TestAScriptIssuesCommandsAndDoesNotReachPastThem:
    def test_every_call_goes_through_the_surface(self) -> None:
        session = a_session()

        session.ops.call("view.rename", {"viewId": "view:001", "newName": "新しい名前"})

        assert [entry.operation for entry in session.surface.history()] == ["view.rename"]

    def test_the_log_says_it_was_a_script(self) -> None:
        session = a_session()
        session.ops.call("history.list", {"workspaceId": "w"})

        assert session.surface.history()[-1].origin is Origin.SCRIPT

    def test_a_refused_command_is_refused_the_same_way(self) -> None:
        """There is no privileged form. A script's commands are ordinary commands."""
        session = a_session()

        result = session.ops.call("view.rename", {"viewId": "view:001", "force": True})

        assert result.status is Status.REFUSED

    def test_an_operation_outside_the_catalogue_stops_at_the_call(self) -> None:
        session = a_session()

        with pytest.raises(ScriptError):
            session.ops.call("view.explode", {})

    def test_one_script_is_one_undo_step(self) -> None:
        """XC-061 and XC-102, deliberately unlike the reference application where operators called from
        Python skip the undo stack by default."""
        session = a_session()
        operations = session.ops
        operations.call("view.rename", {"viewId": "view:001", "newName": "一"})
        operations.call("view.rename", {"viewId": "view:002", "newName": "二"})

        assert session.surface.undoable() == ("script:001",)

        undone = operations.undo_all()

        assert undone.status is Status.APPLIED
        assert session.surface.undoable() == ()

    def test_reading_produces_no_undo_step(self) -> None:
        """`sv.data` is readable and `sv.ops` is writable, and the split is not cosmetic: a script that
        only reads produces no log entries and no undo steps."""
        session = a_session()
        session.ops.call("history.list", {"workspaceId": "w"})

        assert session.surface.undoable() == ()

    def test_a_caller_can_ask_whether_a_sequence_writes(self) -> None:
        session = a_session()

        assert session.reads_only(["history.list", "view.render"]) is True
        assert session.reads_only(["history.list", "view.rename"]) is False


class TestNothingStoredExecutesItself:
    def test_no_module_that_opens_or_runs_reaches_a_python_interpreter(self) -> None:
        """AC-036, XC-102. Structural rather than behavioural: a workspace arrives by email, and the
        claim is about what the code can do, not about the payloads somebody thought to try.

        The three packages checked are the ones a stored document reaches - the workspace it is read
        into, the pipeline that runs, and the surface every change goes through.
        """
        import service.command.surface as command_surface
        import service.pipeline.run as pipeline_run
        import service.scripting.model as scripting_model

        doors = re.compile(r"(?<![.\w])(eval|exec|compile|__import__|importlib)\s*[(.]")
        for module in (command_surface, pipeline_run, scripting_model):
            source = Path(module.__file__).read_text(encoding="utf-8")
            assert doors.findall(source) == [], module.__name__

    def test_the_whole_service_and_domain_tree_is_clear(self) -> None:
        """The narrow check above names three modules; this one is the sweep, so a fourth added later
        is covered without anybody remembering to list it."""
        # `service` is a namespace package and has no `__file__`, so the tree is reached through a
        # module inside it rather than through the package itself.
        import service.scripting.model as anchor

        root = Path(anchor.__file__).resolve().parents[2]
        doors = re.compile(r"(?<![.\w])(eval|exec|__import__|importlib)\s*[(.]")
        offenders = [
            path.name
            for path in sorted(root.rglob("*.py"))
            if "__pycache__" not in path.parts
            and doors.findall(path.read_text(encoding="utf-8"))
        ]

        assert offenders == []

    def test_a_pipeline_carrying_something_that_looks_like_code_is_just_data(self) -> None:
        """A stored pipeline is a document. A field holding Python is a string that never runs, and the
        unit kind it names is refused because the catalogue of kinds is closed."""
        from service.pipeline.run import run

        document: dict[str, Any] = {
            "id": "pipeline:001",
            "units": [{"id": "unit:evil", "kind": "python", "code": "__import__('os').system('x')"}],
        }

        with pytest.raises(PipelineError) as refusal:
            run(document, cases=CASES)

        assert "CT-009" in str(refusal.value)

    def test_an_expression_is_evaluated_by_this_products_own_evaluator(self) -> None:
        """The other half of XC-102: the language a stored document *may* contain has no interpreter
        behind it, so reading a formula is not running one."""
        from engine.analysis.expression import ExpressionError, evaluate

        with pytest.raises(ExpressionError):
            evaluate("__import__('os')")


class TestTheSurfaceIsTheOnlyWayThroughForAScript:
    def test_the_model_holds_no_dispatch_of_its_own(self) -> None:
        """It builds documents and issues commands, and holds no behaviour of its own (MOD-013)."""
        import service.scripting.model as model

        source = Path(model.__file__).read_text(encoding="utf-8")
        assert "def _execute" not in source
        assert source.count("Surface") >= 1

    def test_a_command_from_a_script_carries_the_group_it_belongs_to(self) -> None:
        session = a_session()
        session.ops.call("view.rename", {"viewId": "view:001", "newName": "一"})

        assert session.surface.history()[-1].group_id == "script:001"

    def test_a_direct_command_and_a_scripted_one_take_the_same_path(self) -> None:
        """INV-006: none of the four callers has a private path."""
        session = a_session()

        session.ops.call("view.rename", {"viewId": "view:001", "newName": "一"})
        session.surface.submit(
            Command("view.rename", {"viewId": "view:001", "newName": "二"}, Origin.INTERFACE)
        )

        origins = [entry.origin for entry in session.surface.history()]
        assert origins == [Origin.SCRIPT, Origin.INTERFACE]
        assert all(entry.status is Status.APPLIED for entry in session.surface.history())
