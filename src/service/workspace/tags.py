"""Filtering the case tree by tag, and never hiding what the user is looking at.

Two rules, and the second is the one a filter usually gets wrong.

**A filter says how many it hid** (workspace/AC-014). A tree that quietly shrinks looks like a tree that
lost cases, and the user's next question is whether something was deleted.

**The selected case stays visible, marked as outside the filter** (AC-015). Hiding what someone has open
is how a filter loses their place: they came back to a case, applied a filter to find its siblings, and
the thing they were reading vanished. It is shown, and it says it does not match, which is a different
statement from being included.

An ancestor of a match is kept too - not as a match, but because a tree with the middle removed is not a
tree. Those are marked the same way as the selection: present, and not what you asked for.

Specification: workspace/AC-014, AC-015, CT-001.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any

from service.workspace.hierarchy import walk

Case = dict[str, Any]


@dataclass(frozen=True, slots=True)
class FilterResult:
    """Which cases a filter shows, which of those actually match, and how many it left out."""

    #: Ids in tree order: matches, their ancestors, and the selection if it was kept.
    shown: tuple[str, ...]
    matched: frozenset[str] = dataclass_field(default_factory=frozenset)
    hidden_count: int = 0
    #: Shown without matching - an ancestor holding a match, or the selection.
    shown_outside_filter: frozenset[str] = dataclass_field(default_factory=frozenset)

    def describe(self) -> str:
        if not self.hidden_count and not self.shown_outside_filter:
            return f"{len(self.matched)} 件が一致しました"
        parts = [f"{len(self.matched)} 件が一致し、{self.hidden_count} 件を隠しています"]
        if self.shown_outside_filter:
            parts.append(f"うち {len(self.shown_outside_filter)} 件は絞り込みの対象外ですが表示しています")
        return "。".join(parts)


def tags_of(case: Case) -> frozenset[str]:
    return frozenset(str(tag) for tag in case.get("tags", []))


def all_tags(cases: list[Case]) -> tuple[str, ...]:
    """Every tag in the tree, sorted. What a filter offers is what is there, never a fixed list."""
    found: set[str] = set()
    for case, _ in walk(cases):
        found |= tags_of(case)
    return tuple(sorted(found))


def filter_by_tags(
    cases: list[Case],
    wanted: frozenset[str] | set[str] | tuple[str, ...],
    *,
    selected: str | None = None,
    match_all: bool = False,
) -> FilterResult:
    """Which cases to show for a tag filter.

    `match_all` chooses between a case needing every wanted tag and needing any of them. It is a
    parameter rather than a default because the two give different answers on the same tree and neither
    is the obvious one; the caller is the only place that knows which the user asked for.
    """
    wanted = frozenset(wanted)
    if not wanted:
        everything = tuple(str(case.get("id", "")) for case, _ in walk(cases))
        return FilterResult(shown=everything, matched=frozenset(everything))

    matched: set[str] = set()
    ancestors_of: dict[str, tuple[str, ...]] = {}
    order: list[str] = []
    for case, ancestors in walk(cases):
        case_id = str(case.get("id", ""))
        order.append(case_id)
        ancestors_of[case_id] = ancestors
        tags = tags_of(case)
        if (wanted <= tags) if match_all else bool(wanted & tags):
            matched.add(case_id)

    # An ancestor of a match is kept because a tree with its middle removed is not a tree - but it is
    # not a match, and it says so.
    kept: set[str] = set(matched)
    for case_id in matched:
        kept.update(ancestors_of[case_id])

    outside: set[str] = kept - matched
    if selected is not None and selected in order and selected not in kept:
        # AC-015. Hiding what someone has open is how a filter loses their place.
        kept.add(selected)
        kept.update(ancestors_of[selected])
        outside |= {selected} | (set(ancestors_of[selected]) - matched)

    return FilterResult(
        shown=tuple(case_id for case_id in order if case_id in kept),
        matched=frozenset(matched),
        hidden_count=len(order) - len(kept),
        shown_outside_filter=frozenset(outside),
    )
