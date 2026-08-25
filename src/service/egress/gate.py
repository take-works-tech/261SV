"""Everything that leaves this machine, and the two different rules it leaves under.

MOD-014 owns every outbound request - language-model calls, web search, update checks, a support bundle
- with the permission each requires, the audit of what was sent, and the offline state. Nothing else in
the product opens a connection, and that is asserted rather than asked for.

**Offline is a first-class state, not a failure** (INV-007, XC-106). With the network off, everything
not marked network-dependent completes and **no call is attempted**. A refusal here is not an attempt: a
request that never left is recorded as refused, and the audit says which question went unanswered.

The two rules are genuinely different and conflating them would relax the stricter one.

**A search query is data leaving the machine** (XC-106, AC-020). Values, case names and file paths are
withheld unless the user allowed them **for that search**, the query is shown before it goes, and an
unlisted host is refused by name with no fallback source.

**A dataset value never reaches a language model. Ever** (XC-229). Not with permission, not with
consent, not for one call. So a model request is not free text: it carries names, associations, units,
counts and the instruction, and there is nowhere in it to put a number. The rule is the type, because a
rule that depends on a caller redacting correctly is a rule that holds until somebody adds a field.

Specification: XC-106, XC-126, XC-229, INV-007, assistant/AC-018 to AC-022, operations/AC-009.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from enum import Enum
from typing import Callable, Iterable, Mapping, Sequence

from domain_core.recorded_time import RecordedTime, record as record_time


class Purpose(str, Enum):
    """Why something would leave. MOD-014's four, and a fifth is a decision rather than a string."""

    LANGUAGE_MODEL = "languageModel"
    WEB_SEARCH = "webSearch"
    UPDATE_CHECK = "updateCheck"
    SUPPORT_BUNDLE = "supportBundle"


class Outcome(str, Enum):
    """What happened to a request. `AWAITING` never became a request at all."""

    SENT = "sent"
    REFUSED = "refused"
    AWAITING = "awaitingConfirmation"


class EgressError(Exception):
    """Raised where a request cannot be described honestly enough to decide about."""


@dataclass(frozen=True, slots=True)
class Permission:
    """What one @Workspace allows to leave (XC-106).

    A fresh workspace permits **nothing**. Not "nothing until configured" as a convention - the default
    values here are the refusal, so a workspace nobody has configured cannot reach anything.
    """

    search: bool = False
    language_model: bool = False
    update_check: bool = False
    #: Hosts that may be reached. Empty means **none**, not "any": an empty allow-list read as
    #: permission is how a setting nobody filled in becomes access to everywhere.
    hosts: frozenset[str] = frozenset()
    #: Whether each search may go without asking. Off means the query waits for a confirmation.
    without_asking: bool = False
    #: Whether workspace content - values, case names, paths - may travel in a search query. Per
    #: workspace, and overridable per search, which is what AC-020's "for that search" means.
    workspace_content: bool = False

    def allows(self, purpose: Purpose) -> bool:
        return {
            Purpose.WEB_SEARCH: self.search,
            Purpose.LANGUAGE_MODEL: self.language_model,
            Purpose.UPDATE_CHECK: self.update_check,
            Purpose.SUPPORT_BUNDLE: False,  # always explicit, never a standing permission (XC-126)
        }[purpose]


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """What may go to a language model, as a shape with nowhere to put a number (XC-229).

    Field names, whether each is at points or cells, declared units, counts, case and part names, and
    the instruction. The numbers those names refer to are not a field here and cannot be added by a
    caller being careless - which is the difference between this rule and a redaction step.
    """

    instruction: str
    field_names: tuple[str, ...] = dataclass_field(default_factory=tuple)
    associations: Mapping[str, str] = dataclass_field(default_factory=dict)
    declared_units: Mapping[str, str] = dataclass_field(default_factory=dict)
    counts: Mapping[str, int] = dataclass_field(default_factory=dict)
    case_names: tuple[str, ...] = dataclass_field(default_factory=tuple)
    part_names: tuple[str, ...] = dataclass_field(default_factory=tuple)

    def as_sent(self) -> str:
        """What is recorded in the audit: exactly what left, not a summary of it."""
        parts = [f"指示：{self.instruction}"]
        if self.field_names:
            parts.append(f"フィールド名：{'、'.join(self.field_names)}")
        if self.declared_units:
            parts.append(
                "宣言単位：" + "、".join(f"{k}={v}" for k, v in sorted(self.declared_units.items()))
            )
        if self.counts:
            parts.append("件数：" + "、".join(f"{k}={v}" for k, v in sorted(self.counts.items())))
        if self.case_names:
            parts.append(f"ケース名：{'、'.join(self.case_names)}")
        return "｜".join(parts)


@dataclass(frozen=True, slots=True)
class SearchRequest:
    """A query, and what of the workspace it would carry (AC-019, AC-020)."""

    query: str
    host: str
    #: What in the query came from the workspace, named so it can be withheld or allowed knowingly.
    workspace_terms: tuple[str, ...] = dataclass_field(default_factory=tuple)
    #: Allowed for **this** search, overriding the workspace default either way.
    allow_workspace_content: bool | None = None

    def withheld(self) -> tuple[str, ...]:
        return self.workspace_terms

    def redacted(self) -> str:
        """The query with the workspace's own words taken out.

        Replaced with a marker rather than deleted, so what is sent still reads as a question and the
        user can see where their content was removed from.
        """
        text = self.query
        for term in sorted(self.workspace_terms, key=len, reverse=True):
            text = re.sub(re.escape(term), "［伏せた語］", text)
        return text


@dataclass(frozen=True, slots=True)
class Record:
    """One line of the outbound audit: what was sent, to which host, and when (AC-021)."""

    at: RecordedTime
    purpose: Purpose
    host: str
    outcome: Outcome
    sent: str = ""
    reason: str | None = None
    withheld: tuple[str, ...] = dataclass_field(default_factory=tuple)

    def describe(self) -> str:
        line = f"{self.at.utc} {self.purpose.value} → {self.host}：{self.outcome.value}"
        if self.reason:
            line += f"（{self.reason}）"
        if self.withheld:
            line += f"・伏せた語 {len(self.withheld)} 件：{'、'.join(self.withheld)}"
        if self.sent:
            line += f"\n  送信内容：{self.sent}"
        return line


@dataclass(frozen=True, slots=True)
class Result:
    """What happened, and what the caller may do next."""

    outcome: Outcome
    record: Record
    unanswered: str | None = None

    @property
    def left_the_machine(self) -> bool:
        return self.outcome is Outcome.SENT


class Gate:
    """The one door out. Holds the permissions, the audit and the offline state."""

    def __init__(
        self,
        *,
        offline: bool = False,
        clock: Callable[[], datetime] | None = None,
        send: Callable[[Purpose, str, str], None] | None = None,
    ) -> None:
        self.offline = offline
        self._permissions: dict[str, Permission] = {}
        self._audit: list[Record] = []
        self._clock = clock or (lambda: datetime.now().astimezone())
        #: What actually performs a request. Injected, and absent by default: a gate with no transport
        #: refuses to send rather than pretending to, which is what a test wants and what an offline
        #: build is.
        self._send = send

    def permit(self, workspace_id: str, permission: Permission) -> None:
        self._permissions[workspace_id] = permission

    def permission(self, workspace_id: str) -> Permission:
        """What this workspace allows. An unconfigured one allows nothing (XC-106)."""
        return self._permissions.get(workspace_id, Permission())

    def audit(self) -> tuple[Record, ...]:
        return tuple(self._audit)

    def export_audit(self) -> str:
        """The audit as text the user can read and keep (AC-021)."""
        if not self._audit:
            return "このワークスペースから外部に出た要求はありません"
        return "\n".join(one.describe() for one in self._audit)

    # -- the two doors --------------------------------------------------------------------

    def ask_model(
        self, request: ModelRequest, *, workspace_id: str, host: str
    ) -> Result:
        """Send an instruction and structure to a language model (XC-229).

        There is no parameter here for dataset values, and that is the enforcement. A caller cannot
        supply them by mistake and a future field cannot be added without this docstring being read.
        """
        return self._decide(
            Purpose.LANGUAGE_MODEL, host, workspace_id, request.as_sent(), (),
            unanswered_if_refused="モデルに問い合わせる部分",
        )

    def search(self, request: SearchRequest, *, workspace_id: str, confirmed: bool = False) -> Result:
        """Send a search query, or refuse it, or hold it for confirmation (AC-018 to AC-022)."""
        permission = self.permission(workspace_id)
        allowed_content = (
            permission.workspace_content
            if request.allow_workspace_content is None
            else request.allow_workspace_content
        )
        withheld = () if allowed_content else request.withheld()
        text = request.query if allowed_content else request.redacted()

        # The refusals come **first**. Asking somebody to confirm a query the workspace forbids is
        # asking them to authorise something that will then be refused - and the first version of this
        # did exactly that, holding an unpermitted search for confirmation.
        refusal = self._refusal(
            Purpose.WEB_SEARCH, request.host, workspace_id, withheld,
            unanswered="検索が必要な部分",
        )
        if refusal is not None:
            return refusal
        if not permission.without_asking and not confirmed:
            # AC-019: shown, and not sent until confirmed. Recorded so the audit shows a query that
            # waited as well as one that went.
            return self._record(
                Purpose.WEB_SEARCH, request.host, Outcome.AWAITING, text,
                "1 件ごとの確認が設定されています。送信前の内容は上記のとおりです", withheld,
            )
        return self._decide(
            Purpose.WEB_SEARCH, request.host, workspace_id, text, withheld,
            unanswered_if_refused="検索が必要な部分",
        )

    def check_for_updates(self, *, workspace_id: str, host: str) -> Result:
        return self._decide(
            Purpose.UPDATE_CHECK, host, workspace_id, "更新の確認", (),
            unanswered_if_refused="更新の有無",
        )

    def send_support_bundle(
        self, *, workspace_id: str, host: str, contents: Sequence[str], consented: bool
    ) -> Result:
        """A bundle leaves only with explicit consent, and the audit lists what was in it (XC-126).

        `contents` is the manifest the user was shown. Recorded rather than summarised, because the
        thing they consented to is the list.
        """
        if not consented:
            return self._record(
                Purpose.SUPPORT_BUNDLE, host, Outcome.REFUSED, "",
                "同意がありません。診断情報は同意なしには出ません（XC-126）", (),
            )
        return self._decide(
            Purpose.SUPPORT_BUNDLE, host, workspace_id,
            "同封物：" + "、".join(contents), (),
            unanswered_if_refused="サポートへの送信",
            already_consented=True,
        )

    # -- the one decision -----------------------------------------------------------------

    def _refusal(
        self,
        purpose: Purpose,
        host: str,
        workspace_id: str,
        withheld: Iterable[str],
        *,
        unanswered: str,
        already_consented: bool = False,
    ) -> Result | None:
        """Why this request may not go, or None. Every reason a request is stopped, in one place.

        Separate from sending so the order is visible: offline, then permission, then the host list,
        then the transport - and confirmation after all of them, because confirming a request that will
        be refused is a question nobody should be asked.
        """
        withheld = tuple(withheld)
        if self.offline:
            # INV-007: nothing is attempted. A refusal is not an attempt, and the rest of the operation
            # continues without it.
            return self._record(
                purpose, host, Outcome.REFUSED, "", "オフラインです。要求は送っていません", withheld,
                unanswered=unanswered,
            )
        permission = self.permission(workspace_id)
        if not already_consented and not permission.allows(purpose):
            return self._record(
                purpose, host, Outcome.REFUSED, "",
                f"このワークスペースでは {purpose.value} が許可されていません。"
                "新しいワークスペースは何も許可しません（XC-106）",
                withheld, unanswered=unanswered,
            )
        if host not in permission.hosts:
            # AC-022: refused by name, and no fallback source. Trying another host would be this
            # product choosing where a customer's question goes.
            return self._record(
                purpose, host, Outcome.REFUSED, "",
                f"'{host}' はこのワークスペースの許可リストにありません"
                f"（{sorted(permission.hosts) or '空です'}）。別の宛先は試しません",
                withheld, unanswered=unanswered,
            )
        if self._send is None:
            return self._record(
                purpose, host, Outcome.REFUSED, "",
                "送信経路が構成されていません。送ったふりはしません", withheld,
                unanswered=unanswered,
            )
        return None

    def _decide(
        self,
        purpose: Purpose,
        host: str,
        workspace_id: str,
        sent: str,
        withheld: Iterable[str],
        *,
        unanswered_if_refused: str,
        already_consented: bool = False,
    ) -> Result:
        refusal = self._refusal(
            purpose, host, workspace_id, withheld,
            unanswered=unanswered_if_refused, already_consented=already_consented,
        )
        if refusal is not None:
            return refusal
        assert self._send is not None  # `_refusal` returns for a gate with no transport
        self._send(purpose, host, sent)
        return self._record(purpose, host, Outcome.SENT, sent, None, tuple(withheld))

    def _record(
        self,
        purpose: Purpose,
        host: str,
        outcome: Outcome,
        sent: str,
        reason: str | None,
        withheld: Iterable[str],
        *,
        unanswered: str | None = None,
    ) -> Result:
        record = Record(
            record_time(self._clock()), purpose, host, outcome, sent, reason, tuple(withheld)
        )
        self._audit.append(record)
        return Result(outcome, record, unanswered if outcome is not Outcome.SENT else None)
