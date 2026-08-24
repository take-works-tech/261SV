"""One @Case as it was loaded: its parts, named, with the ones that were not there still named.

A @Case is not a file and it is not one mesh either (GL-002). The formats this product exists for say
so: 19 of the 40 CAE readers in the pinned build return a `vtkMultiBlockDataSet` and 6 a
`vtkPartitionedDataSetCollection`, against 4 that return a single unstructured grid (E-133). An assembly
arrives as an assembly.

**Nothing here sums across parts** (XC-234). A part is a distinct thing in the model - an element block,
a side set, a material - and adding a flange's values to a gasket's produces a number that is
arithmetically fine and means nothing. What is offered case-wide is the extremum, which is the number an
engineer reports and the one aggregate that is the same whether it is taken part by part or all at once.

Specification: GL-002, XC-234, CT-012, ingest/AC-026, AC-027. Evidence: E-133 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass

from domain_core.case_contents import CaseContents
from domain_core.dataset import Dataset
from domain_core.reported_value import Caveat, Provenance, ReportedValue


@dataclass(frozen=True, slots=True)
class Part:
    """One named component of a @Case, or the record that the file named one and it was not there."""

    name: str
    # Where it sits in the block hierarchy, root first. A leaf named `gasket` inside `assembly` is
    # ("assembly", "gasket"), because two parts in different assemblies may share a name and the
    # hierarchy is the only thing that tells them apart.
    path: tuple[str, ...]
    dataset: Dataset | None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a part is named; an unnamed one cannot be referred to or reported on")
        if not self.path or self.path[-1] != self.name:
            raise ValueError("a part's path ends with its own name")

    @property
    def is_present(self) -> bool:
        return self.dataset is not None

    @property
    def label(self) -> str:
        """The path as one string, for a message a person reads."""
        return " / ".join(self.path)


@dataclass(slots=True)
class LoadedCase:
    """A @Case that has been read: every part the file named, present or not, and the counts."""

    parts: tuple[Part, ...]
    contents: CaseContents

    def __post_init__(self) -> None:
        present = sum(1 for part in self.parts if part.is_present)
        if present != self.contents.parts:
            raise ValueError(
                f"{present} parts were loaded and the contents say {self.contents.parts}; a count that "
                "disagrees with what is here is a count somebody will report"
            )

    @property
    def present(self) -> tuple[Part, ...]:
        return tuple(part for part in self.parts if part.is_present)

    @property
    def is_partial(self) -> bool:
        return self.contents.is_partial

    def part(self, label: str) -> Part:
        """One part by name or by its full path."""
        for part in self.parts:
            if label in (part.name, part.label):
                return part
        raise KeyError(f"no part called '{label}'; this case has {[p.label for p in self.parts]}")

    def maximum(self, field: str) -> ReportedValue:
        """The largest value of a field across every part that carries it.

        The one case-wide aggregate offered, because it is the only one that is the same taken part by
        part as taken all at once - and because it is the number an engineer reports. A sum or a mean
        across parts is refused rather than computed: adding a flange's values to a gasket's is
        arithmetically fine and means nothing (XC-234).
        """
        found = [
            part.dataset.maximum(field)
            for part in self.present
            if part.dataset is not None and field in part.dataset.fields
        ]
        usable = [value for value in found if not value.is_missing]
        if not usable:
            reason = (
                f"'{field}' を持つパートがありません"
                if not found
                else "この量を報告できるパートがありません：" + "；".join(
                    value.missing_because or "理由不明" for value in found
                )
            )
            return ReportedValue.unavailable(
                reason, unit=None, digits=1, provenance=Provenance.COMPUTED,
                formula=f"extremum({field}) over parts",
            )

        largest = max(usable, key=lambda value: value.value or float("-inf"))
        caveats = frozenset().union(*(value.caveats for value in usable))
        if self.is_partial:
            caveats = caveats | {Caveat.PARTIAL_DATASET}
        return ReportedValue(
            value=largest.value,
            unit=largest.unit,
            digits=min(value.digits for value in usable),
            provenance=Provenance.COMPUTED,
            caveats=caveats,
            formula=f"extremum({field}) over {len(usable)} parts",
        )

    def describe(self) -> str:
        """One line stating what was found, including what was not."""
        return self.contents.describe()
