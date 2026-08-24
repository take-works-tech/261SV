"""What a run is holding, and the refusal that keeps the operating system out of the decision.

REQ-006's title is the argument: memory is managed by the pipeline, not by luck. A forty-case study
loads forty datasets, and the failure mode without a ledger is not a slow run - it is the process being
killed, which loses the run record along with everything else and tells the user nothing about why.

So a case is **held** before it is acted on and **released** when a clear unit empties the target set.
A hold that would exceed the budget is refused with what was needed and what was available (AC-019), the
case stops there, and the rest of the study continues - the same shape as any other per-case failure
(XC-095).

Two things this deliberately does not do.

**It does not measure.** The size of a case is supplied by whoever can answer it; MOD-002 knows what a
file costs to load and this module knows the rule. A ledger that estimated would be a second opinion
about a number MOD-002 already has.

**It does not free anything.** Releasing a hold says the pipeline is no longer counting that case
against the budget; what the runtime does with the memory afterwards is the runtime's business. A
module that claimed to free memory it does not own would be reporting an outcome it cannot observe.

Specification: LIM-001, XC-086, pipeline/AC-018, AC-019, REQ-006.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field

from domain_core.locale_format import bytes_as_text


class MemoryRefusal(Exception):
    """Raised when holding a case would take the run past its budget.

    Carries both numbers, because "out of memory" tells a user nothing they can act on and "this case
    needs 9.0 GiB and 4.0 GiB is free" tells them whether to close the other window or split the study.
    """

    def __init__(self, case_id: str, needed: int, available: int, budget: int) -> None:
        super().__init__(
            f"{case_id} の読み込みには {bytes_as_text(needed)} が必要ですが、"
            f"空きは {bytes_as_text(available)} です"
            f"（1 ケースあたりの上限 {bytes_as_text(budget)}、LIM-001）。"
            "このケースだけを止めます — 残りのケースは続行し、"
            "OS に落とされるのではなく製品が断ります"
        )
        self.case_id = case_id
        self.needed = needed
        self.available = available
        self.budget = budget


@dataclass(slots=True)
class Ledger:
    """What a run is currently holding, against a stated budget.

    `budget_bytes` is not defaulted. LIM-001 differs by machine class (XC-086), and a default here would
    be the workstation's budget handed to a laptop - twice what that class allows, in the direction that
    ends with the process being killed. `engine.limits.dataset_budget_bytes` answers it once the class
    is known.
    """

    budget_bytes: int
    held: dict[str, int] = dataclass_field(default_factory=dict)
    #: Every hold and release in order, so "what was this run holding when it failed" is answerable
    #: afterwards rather than reconstructed.
    log: list[str] = dataclass_field(default_factory=list)

    @property
    def held_bytes(self) -> int:
        return sum(self.held.values())

    @property
    def available_bytes(self) -> int:
        return max(0, self.budget_bytes - self.held_bytes)

    def holds(self, case_id: str) -> bool:
        return case_id in self.held

    def hold(self, case_id: str, needed: int) -> None:
        """Count a case against the budget, or refuse naming both numbers (AC-019).

        Holding a case already held is not an error and not a second charge: a case is loaded once and
        every unit below acts on the same loaded data.
        """
        if case_id in self.held:
            return
        if needed > self.available_bytes:
            raise MemoryRefusal(case_id, needed, self.available_bytes, self.budget_bytes)
        self.held[case_id] = needed
        self.log.append(f"{case_id}：{bytes_as_text(needed)} を確保（保持 {self.summary()}）")

    def release(self, case_id: str) -> int:
        """Stop counting one case. Returns what it was holding, or 0 where it held nothing."""
        freed = self.held.pop(case_id, 0)
        if freed:
            self.log.append(f"{case_id}：{bytes_as_text(freed)} を解放（保持 {self.summary()}）")
        return freed

    def release_all(self, unit_id: str) -> int:
        """What a clear unit does to the ledger (AC-018): every case it held, released.

        No source file is touched, here or anywhere in this module - it holds integers and case
        identifiers and has no path to a file to touch.
        """
        freed = self.held_bytes
        self.held.clear()
        self.log.append(
            f"{unit_id}：読み込み済みデータ {bytes_as_text(freed)} を解放しました"
            "（元ファイルには触れていません）"
        )
        return freed

    def summary(self) -> str:
        return f"{bytes_as_text(self.held_bytes)} / {bytes_as_text(self.budget_bytes)}"

    def describe(self) -> str:
        return (
            f"読み込み済み {len(self.held)} 件、{self.summary()}、"
            f"空き {bytes_as_text(self.available_bytes)}"
        )
