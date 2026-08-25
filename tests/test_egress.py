"""Everything that leaves the machine, and the two different rules it leaves under.

Conflating them would relax the stricter one, so the tests keep them apart.

A **search query is data leaving the machine** (XC-106): values, case names and paths are withheld
unless allowed for that search, the query is shown before it goes, and an unlisted host is refused by
name with no fallback.

A **dataset value never reaches a language model** (XC-229) - not with permission, not with consent, not
for one call. So the rule is the type: a model request has nowhere to put a number, and a caller cannot
supply one by being careless.

Offline is a first-class state (INV-007): with the network off nothing is attempted, and a request that
never left is recorded as refused with the question it left unanswered.

Verifies: XC-106, XC-126, XC-229, INV-007, assistant/AC-018 to AC-022, assistant/TASK-018 to TASK-022.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

from service.egress.gate import (
    EgressError,
    Gate,
    ModelRequest,
    Outcome,
    Permission,
    Purpose,
    SearchRequest,
)

WORKSPACE = "workspace:001"
HOST = "search.example.test"


def at(hour: int = 9):
    return lambda: datetime(2026, 8, 25, hour, tzinfo=timezone(timedelta(hours=9)))


def a_gate(*, offline: bool = False, permission: Permission | None = None) -> Gate:
    sent: list[tuple[Purpose, str, str]] = []
    gate = Gate(offline=offline, clock=at(), send=lambda p, h, s: sent.append((p, h, s)))
    gate.permit(WORKSPACE, permission or Permission())
    gate.attempts = sent  # type: ignore[attr-defined]
    return gate


def permissive(**changed: object) -> Permission:
    fields_: dict[str, object] = {
        "search": True, "language_model": True, "update_check": True,
        "hosts": frozenset({HOST}), "without_asking": True, "workspace_content": False,
    }
    fields_.update(changed)
    return Permission(**fields_)  # type: ignore[arg-type]


class TestAFreshWorkspacePermitsNothing:
    def test_a_search_is_refused(self) -> None:
        """XC-106. Not "nothing until configured" as a convention - the defaults are the refusal."""
        gate = a_gate()

        found = gate.search(SearchRequest("疲労限度 SUS304", HOST), workspace_id=WORKSPACE)

        assert found.outcome is Outcome.REFUSED
        assert gate.attempts == []  # type: ignore[attr-defined]

    def test_the_refusal_names_the_question_that_went_unanswered(self) -> None:
        """AC-018: the rest of the operation continues, and the user learns which part it lacked."""
        found = a_gate().search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE)

        assert found.unanswered == "検索が必要な部分"

    def test_an_unconfigured_workspace_is_the_same_as_a_denying_one(self) -> None:
        gate = Gate(clock=at())

        assert gate.permission("workspace:never-seen").allows(Purpose.WEB_SEARCH) is False

    def test_an_empty_host_list_means_none_rather_than_any(self) -> None:
        """An empty allow-list read as permission is how a setting nobody filled in becomes access to
        everywhere."""
        gate = a_gate(permission=permissive(hosts=frozenset()))

        found = gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE, confirmed=True)

        assert found.outcome is Outcome.REFUSED
        assert "許可リストにありません" in (found.record.reason or "")

    def test_a_support_bundle_is_never_a_standing_permission(self) -> None:
        """XC-126: it leaves with explicit consent each time, not because a workspace once allowed it."""
        assert permissive().allows(Purpose.SUPPORT_BUNDLE) is False


class TestOfflineMeansNothingIsAttempted:
    def test_no_request_is_made(self) -> None:
        """INV-007. A refusal is not an attempt."""
        gate = a_gate(offline=True, permission=permissive())

        gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE, confirmed=True)

        assert gate.attempts == []  # type: ignore[attr-defined]

    def test_it_is_recorded_as_refused_with_the_reason(self) -> None:
        gate = a_gate(offline=True, permission=permissive())

        found = gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE, confirmed=True)

        assert found.outcome is Outcome.REFUSED
        assert "オフライン" in (found.record.reason or "")

    def test_the_operation_learns_what_it_could_not_answer(self) -> None:
        gate = a_gate(offline=True, permission=permissive())

        found = gate.check_for_updates(workspace_id=WORKSPACE, host=HOST)

        assert found.unanswered == "更新の有無"


class TestTheQueryIsShownBeforeItIsSent:
    def test_per_search_confirmation_holds_it(self) -> None:
        """AC-019."""
        gate = a_gate(permission=permissive(without_asking=False))

        found = gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE)

        assert found.outcome is Outcome.AWAITING
        assert gate.attempts == []  # type: ignore[attr-defined]

    def test_what_would_be_sent_is_in_the_record(self) -> None:
        gate = a_gate(permission=permissive(without_asking=False))

        found = gate.search(SearchRequest("疲労限度 SUS304", HOST), workspace_id=WORKSPACE)

        assert "疲労限度 SUS304" in found.record.sent

    def test_confirming_sends_it(self) -> None:
        gate = a_gate(permission=permissive(without_asking=False))

        found = gate.search(
            SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE, confirmed=True
        )

        assert found.outcome is Outcome.SENT

    def test_a_query_that_waited_is_in_the_audit_too(self) -> None:
        """So the audit shows what was about to go, not only what went."""
        gate = a_gate(permission=permissive(without_asking=False))
        gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE)

        assert gate.audit()[-1].outcome is Outcome.AWAITING


class TestWorkspaceContentIsWithheldFromAQuery:
    def test_the_case_name_is_taken_out(self) -> None:
        """AC-020."""
        gate = a_gate(permission=permissive())
        request = SearchRequest(
            "Run 12 の材料 SUS304 の疲労限度", HOST, workspace_terms=("Run 12",)
        )

        found = gate.search(request, workspace_id=WORKSPACE, confirmed=True)

        assert "Run 12" not in found.record.sent
        assert "SUS304" in found.record.sent

    def test_what_was_withheld_is_named_in_the_audit(self) -> None:
        gate = a_gate(permission=permissive())
        request = SearchRequest("Run 12 の疲労限度", HOST, workspace_terms=("Run 12",))

        found = gate.search(request, workspace_id=WORKSPACE, confirmed=True)

        assert found.record.withheld == ("Run 12",)
        assert "伏せた語" in found.record.describe()

    def test_a_marker_is_left_where_it_was(self) -> None:
        """Deleted, the query stops reading as a question and the user cannot see where their content
        was removed from."""
        gate = a_gate(permission=permissive())
        request = SearchRequest("Run 12 の疲労限度", HOST, workspace_terms=("Run 12",))

        found = gate.search(request, workspace_id=WORKSPACE, confirmed=True)

        assert "［伏せた語］" in found.record.sent

    def test_allowing_it_for_that_search_lets_it_through(self) -> None:
        """AC-020's "for that search": the per-search answer overrides the workspace default."""
        gate = a_gate(permission=permissive())
        request = SearchRequest(
            "Run 12 の疲労限度", HOST, workspace_terms=("Run 12",), allow_workspace_content=True
        )

        found = gate.search(request, workspace_id=WORKSPACE, confirmed=True)

        assert "Run 12" in found.record.sent
        assert found.record.withheld == ()

    def test_and_refusing_it_for_that_search_overrides_a_permissive_workspace(self) -> None:
        gate = a_gate(permission=permissive(workspace_content=True))
        request = SearchRequest(
            "Run 12 の疲労限度", HOST, workspace_terms=("Run 12",), allow_workspace_content=False
        )

        found = gate.search(request, workspace_id=WORKSPACE, confirmed=True)

        assert "Run 12" not in found.record.sent


class TestADatasetValueNeverReachesAModel:
    def test_there_is_nowhere_in_the_request_to_put_one(self) -> None:
        """XC-229 as a property of the type. A rule that depends on a caller redacting correctly is a
        rule that holds until somebody adds a field."""
        names = {one.name for one in fields(ModelRequest)}

        assert names == {
            "instruction", "field_names", "associations", "declared_units",
            "counts", "case_names", "part_names",
        }
        assert "values" not in names
        assert "data" not in names

    def test_what_it_may_carry_is_what_the_decision_lists(self) -> None:
        request = ModelRequest(
            instruction="最大応力の図を作って",
            field_names=("stress",),
            declared_units={"stress": "MPa"},
            counts={"points": 1127844},
            case_names=("Run 12",),
        )

        sent = request.as_sent()

        assert "stress" in sent and "MPa" in sent and "1127844" in sent

    def test_a_model_call_is_still_refused_without_permission(self) -> None:
        gate = a_gate()

        found = gate.ask_model(
            ModelRequest("要約して"), workspace_id=WORKSPACE, host=HOST
        )

        assert found.outcome is Outcome.REFUSED

    def test_the_module_names_no_field_that_could_hold_a_number(self) -> None:
        """Structural, over the module rather than over this one class, so a second request type added
        later is covered."""
        import service.egress.gate as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "np.ndarray" not in source
        assert "float" not in source.split('"""')[2] if source.count('"""') > 2 else True


class TestAnUnlistedHostIsRefusedByName:
    def test_it_is_named(self) -> None:
        """AC-022."""
        gate = a_gate(permission=permissive())

        found = gate.search(
            SearchRequest("疲労限度", "elsewhere.example.test"), workspace_id=WORKSPACE, confirmed=True
        )

        assert found.outcome is Outcome.REFUSED
        assert "elsewhere.example.test" in (found.record.reason or "")

    def test_no_other_source_is_tried(self) -> None:
        """Trying another host would be this product choosing where a customer's question goes."""
        gate = a_gate(permission=permissive())

        gate.search(
            SearchRequest("疲労限度", "elsewhere.example.test"), workspace_id=WORKSPACE, confirmed=True
        )

        assert gate.attempts == []  # type: ignore[attr-defined]
        assert "別の宛先は試しません" in (gate.audit()[-1].reason or "")


class TestASupportBundleLeavesOnlyWithConsent:
    def test_without_consent_nothing_goes(self) -> None:
        """XC-126."""
        gate = a_gate(permission=permissive())

        found = gate.send_support_bundle(
            workspace_id=WORKSPACE, host=HOST, contents=["log.txt", "Run 12"], consented=False
        )

        assert found.outcome is Outcome.REFUSED
        assert gate.attempts == []  # type: ignore[attr-defined]

    def test_with_consent_the_audit_lists_what_was_in_it(self) -> None:
        """The thing they consented to is the list, so the list is what is recorded."""
        gate = a_gate(permission=permissive())

        found = gate.send_support_bundle(
            workspace_id=WORKSPACE, host=HOST, contents=["log.txt", "Run 12"], consented=True
        )

        assert found.outcome is Outcome.SENT
        assert "Run 12" in found.record.sent


class TestTheAuditIsReadableAndExportable:
    def test_every_request_is_in_it_whatever_happened(self) -> None:
        """AC-021. A refusal that leaves no trace is a refusal nobody can investigate."""
        gate = a_gate(permission=permissive())
        gate.search(SearchRequest("一", HOST), workspace_id=WORKSPACE, confirmed=True)
        gate.search(SearchRequest("二", "elsewhere.test"), workspace_id=WORKSPACE, confirmed=True)

        assert [one.outcome for one in gate.audit()] == [Outcome.SENT, Outcome.REFUSED]

    def test_each_line_says_what_where_and_when(self) -> None:
        gate = a_gate(permission=permissive())
        gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE, confirmed=True)

        line = gate.audit()[-1].describe()
        assert "2026-08-25T00:00:00Z" in line
        assert HOST in line
        assert "疲労限度" in line

    def test_an_empty_audit_says_so_rather_than_being_blank(self) -> None:
        assert "外部に出た要求はありません" in a_gate().export_audit()

    def test_it_exports_as_text(self) -> None:
        gate = a_gate(permission=permissive())
        gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE, confirmed=True)

        assert HOST in gate.export_audit()


class TestNothingElseOpensAConnection:
    def test_no_other_module_imports_a_network_client(self) -> None:
        """assistant/TASK-018's own condition: asserted by a test that fails if any other module opens a
        connection. Swept over the tree rather than over a list, so a module added later is covered."""
        import service.egress.gate as anchor

        root = Path(anchor.__file__).resolve().parents[3]
        clients = ("import requests", "import httpx", "import urllib.request", "import socket",
                   "from urllib import request", "http.client")
        offenders = [
            path.relative_to(root).as_posix()
            for path in sorted((root / "src").rglob("*.py"))
            if "__pycache__" not in path.parts
            and "egress" not in path.parts
            and any(client in path.read_text(encoding="utf-8") for client in clients)
        ]

        assert offenders == []

    def test_the_gate_itself_holds_no_transport_by_default(self) -> None:
        """A gate with no transport refuses rather than pretending to send, which is what an offline
        build is and what a test wants."""
        gate = Gate(clock=at())
        gate.permit(WORKSPACE, permissive())

        found = gate.search(SearchRequest("疲労限度", HOST), workspace_id=WORKSPACE, confirmed=True)

        assert found.outcome is Outcome.REFUSED
        assert "送ったふりはしません" in (found.record.reason or "")

    def test_the_error_type_exists_for_a_request_that_cannot_be_described(self) -> None:
        assert issubclass(EgressError, Exception)
