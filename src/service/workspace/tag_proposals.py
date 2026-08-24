"""Tags proposed from what can be read, and applied only when a person says so.

XC-120: nothing is applied until accepted, in one action for a whole import, and **a rejected proposal
is not offered again in the session**. That last clause is the one that makes the feature bearable - a
suggestion that returns every time you decline it is a suggestion you learn to click past, and a user
who clicks past suggestions accepts a wrong one eventually.

Every proposal **says what it was read from**. "steel" with no reason is a tag a user must either trust
or check by hand; "steel — from the solver's material block" is one they can accept in a second. Where a
proposal comes from a language model reading a name, it is marked **inferred** (AC-042), because a name
is what somebody typed and a solver record is what the run contained, and the two do not deserve equal
confidence.

Nothing here reads a @Dataset. Signals are handed in by whoever loaded the file, so this module can be
exercised without one and so that no language model ever sees field values (XC-229).

Specification: XC-120, XC-081, workspace/AC-041, AC-042, AC-043.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import Any, Iterable


class Signal(str, Enum):
    """What a proposal was read from. Deterministic ones first; the inferred one is last and marked."""

    SOLVER = "solver"                # the writer the file names
    MESH_SIZE = "mesh-size"          # a band, not a count - "large" survives a remesh, "1,043,221" does not
    DIFFERING_VARIABLE = "variable"  # what distinguishes this case from its siblings
    FILE_DATE = "file-date"
    INFERRED_FROM_NAME = "inferred"  # a language model reading the case's own naming (AC-042)


_SIGNAL_WORD = {
    Signal.SOLVER: "ソルバ名から",
    Signal.MESH_SIZE: "メッシュ規模から",
    Signal.DIFFERING_VARIABLE: "兄弟ケースと異なる変数から",
    Signal.FILE_DATE: "ファイルの日付から",
    Signal.INFERRED_FROM_NAME: "名前からの推測",
}

#: Mesh size is proposed as a band rather than a count. "1,043,221 points" is not a tag anybody filters
#: by, and it stops matching the moment the mesh is refined; "large" survives that and is what a person
#: would have written.
MESH_BANDS: tuple[tuple[int, str], ...] = (
    (1_000_000, "large-mesh"),
    (100_000, "medium-mesh"),
    (0, "small-mesh"),
)


@dataclass(frozen=True, slots=True)
class Proposal:
    """One tag somebody might want, and where it came from."""

    tag: str
    signal: Signal

    @property
    def is_inferred(self) -> bool:
        """AC-042. A name is what somebody typed; a solver record is what the run contained."""
        return self.signal is Signal.INFERRED_FROM_NAME

    def describe(self) -> str:
        return f"{self.tag}（{_SIGNAL_WORD[self.signal]}）"


@dataclass
class Session:
    """What has been declined so far, so it is not offered again (AC-043).

    Session-scoped on purpose: a rejection is "not now", not "never". Persisting it would mean a tag
    declined once in March is unavailable in June, with nothing on screen saying why.
    """

    rejected: set[tuple[str, str]] = dataclass_field(default_factory=set)

    def reject(self, proposal: Proposal) -> None:
        self.rejected.add((proposal.tag, proposal.signal.value))

    def was_rejected(self, proposal: Proposal) -> bool:
        return (proposal.tag, proposal.signal.value) in self.rejected


def propose(
    *,
    solver: str | None = None,
    point_count: int | None = None,
    differing_variables: Iterable[str] = (),
    inferred_from_name: Iterable[str] = (),
    already_tagged: Iterable[str] = (),
    session: Session | None = None,
) -> tuple[Proposal, ...]:
    """What could be proposed for one @Case, in a fixed order and with nothing applied.

    Signals are handed in rather than read here: this layer does not open files, and no language model
    ever sees a field value (XC-229). `inferred_from_name` is whatever a configured model returned from
    the case's own naming, and it is marked as inferred rather than mixed in.
    """
    have = {str(tag) for tag in already_tagged}
    found: list[Proposal] = []

    if solver:
        found.append(Proposal(_slug(solver), Signal.SOLVER))
    if point_count is not None:
        for threshold, band in MESH_BANDS:
            if point_count >= threshold:
                found.append(Proposal(band, Signal.MESH_SIZE))
                break
    for name in sorted({str(v) for v in differing_variables}):
        found.append(Proposal(_slug(name), Signal.DIFFERING_VARIABLE))
    for name in sorted({str(v) for v in inferred_from_name}):
        found.append(Proposal(_slug(name), Signal.INFERRED_FROM_NAME))

    seen: set[str] = set()
    kept: list[Proposal] = []
    for proposal in found:
        if proposal.tag in have or proposal.tag in seen:
            # A tag the case already carries is not a proposal, and the same tag from two signals is
            # one tag - offered under the first signal that produced it, which is the deterministic one.
            continue
        if session is not None and session.was_rejected(proposal):
            continue
        seen.add(proposal.tag)
        kept.append(proposal)
    return tuple(kept)


def accept(case: dict[str, Any], proposals: Iterable[Proposal]) -> tuple[str, ...]:
    """Apply proposals to a case, in one action for the whole set (XC-120).

    One action rather than one per tag: a user reviewing eleven proposals and clicking eleven times is
    a user who stops reviewing at the fourth.
    """
    tags = list(case.setdefault("tags", []))
    added: list[str] = []
    for proposal in proposals:
        if proposal.tag not in tags:
            tags.append(proposal.tag)
            added.append(proposal.tag)
    case["tags"] = tags
    return tuple(added)


def _slug(value: str) -> str:
    """A tag as it is stored. Lowercased and hyphenated only for ASCII: Japanese has no case and no
    word separator, and rewriting it would turn a tag somebody typed into one they cannot search for."""
    text = value.strip()
    if text.isascii():
        return "-".join(text.lower().split())
    return text
