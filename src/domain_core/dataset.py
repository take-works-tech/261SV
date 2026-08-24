"""The dataset as this product holds it: geometry in the canonical frame, fields that know what they
are attached to, and units that are declared or absent.

Two properties here exist because the toolkit underneath does not provide them. A field remembers
whether it came from points or from cells and refuses to be read as the other (INV-003). And a value
that could not be computed is missing rather than zero, everywhere, including after a transfer between
meshes (INV-011).

A field also knows how precise it is. The number of digits it may be shown to follows from the type
it was stored as, not from the width of the column it is displayed in (INV-014).

Specification: GL-005, GL-006, GL-007, GL-021, GL-023, INV-001, INV-003, INV-011, INV-014.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
import numpy as np

from domain_core.association import Association, AssociationError
from domain_core.case_contents import CaseContents
from domain_core.conversion import ConversionRecord
from domain_core.identifiers import SourceIdentifiers, location_of
from domain_core.mesh import Cells, DisplayGeometry
from domain_core.partitions import Aggregate, Partitioning, counted
from domain_core.reported_value import DIMENSIONLESS, Caveat, Provenance, ReportedValue

from domain_core.precision import format_value, significant_digits

#: XC-123, in the words a user sees. The extrapolation is not merely unimplemented: it depends on the
#: element formulation, and the file does not carry it - so there is no correct version of it to write.
_NO_EXTRAPOLATION = (
    "'{name}' は積分点の値です。節点への外挿は要素定式化に依存し、その情報はファイルにありません。"
    "この製品は積分点の値を書かれたまま読み、外挿しません（XC-123）"
)

#: The aggregates that need quadrature weights when taken over integration-point values. A count does
#: not - it counts entries, which is a fact about the array rather than about the physics.
_NEEDS_WEIGHTS = frozenset({Aggregate.TOTAL, Aggregate.MEAN})
_AGGREGATE_WORD = {
    Aggregate.TOTAL: "合計",
    Aggregate.MEAN: "平均",
    Aggregate.EXTREMUM: "極値",
    Aggregate.COUNT: "件数",
}

__all__ = [
    "Association", "AssociationError", "Cells", "Dataset", "DisplayGeometry", "Field",
    "SourceFrame",
]


@dataclass(frozen=True, slots=True)
class Field:
    """One physical quantity on a dataset, with its association and its declared unit.

    `unit` is None until a person declares one. Nothing in this product fills it in (XC-003).
    """

    name: str
    association: Association
    values: np.ndarray
    unit: str | None = None
    #: How many quadrature points each cell holds. Required for an integration-point field and refused
    #: for any other: it is what makes the array's length mean something, and it cannot be inferred
    #: from the length alone because a mesh of n cells with 8 points each and one of 8n cells with one
    #: each are the same number of values.
    points_per_cell: int | None = None

    def __post_init__(self) -> None:
        at_integration_points = self.association is Association.INTEGRATION_POINT
        if at_integration_points and not self.points_per_cell:
            raise AssociationError(
                f"'{self.name}' is at integration points and does not say how many per cell; without "
                "that the array's length says nothing about which cell a value belongs to"
            )
        if not at_integration_points and self.points_per_cell is not None:
            raise AssociationError(
                f"'{self.name}' is {self.association.value} data and cannot have points per cell"
            )
        if self.points_per_cell is not None and self.points_per_cell < 1:
            raise AssociationError("a cell holds at least one integration point")

    def as_point_data(self) -> np.ndarray:
        if self.association is Association.INTEGRATION_POINT:
            raise AssociationError(_NO_EXTRAPOLATION.format(name=self.name))
        if self.association is not Association.POINT:
            raise AssociationError(
                f"'{self.name}' is cell data; converting it to point data changes its values and must be asked for"
            )
        return self.values

    def as_cell_data(self) -> np.ndarray:
        if self.association is Association.INTEGRATION_POINT:
            raise AssociationError(_NO_EXTRAPOLATION.format(name=self.name))
        if self.association is not Association.CELL:
            raise AssociationError(
                f"'{self.name}' is point data; converting it to cell data changes its values and must be asked for"
            )
        return self.values

    def at_integration_points(self, points_per_cell: int) -> "Field":
        """Declare that this field's values sit at quadrature points, as a person states a unit.

        Declared and never inferred. Solvers name these arrays by convention - `sigma_xx_1` through
        `_8` - and reading a convention as a fact is how eight independent results become one quantity
        nobody asked to combine.
        """
        return Field(self.name, Association.INTEGRATION_POINT, self.values, self.unit, points_per_cell)

    @property
    def missing_count(self) -> int:
        """How many entries are missing. Missing is NaN, never zero (INV-011)."""
        return int(np.count_nonzero(np.isnan(self.values)))

    @property
    def significant_digits(self) -> int:
        """Digits this field may be displayed to, from the type it was stored as (INV-014)."""
        return significant_digits(self.values.dtype)

    def formatted(self, index: int, *, missing: str = "-") -> str:
        """One entry, written to the precision the storage supports and no further."""
        return format_value(float(self.values[index]), self.significant_digits, missing=missing)

    def declared(self, symbol: str) -> "Field":
        """Return the same field with a unit the user declared."""
        return Field(self.name, self.association, self.values, symbol)


@dataclass(frozen=True, slots=True)
class SourceFrame:
    """What the reader found, and what was done to it to reach the canonical frame.

    Kept so that a converted coordinate can be explained rather than merely trusted (ingest/AC-028).
    """

    up_axis: str
    scale_to_metres: float
    reader: str


@dataclass(slots=True)
class Dataset:
    """Geometry and fields in the canonical frame: right-handed, Z up, metres (GL-021)."""

    points_m: np.ndarray
    cells: Cells
    fields: dict[str, Field] = dataclass_field(default_factory=dict)
    # Display geometry, by the triangle budget it was built for. A cache and not a field: producing it
    # is MOD-003's work, it costs 22 seconds for a million-point surface, and it is derived entirely from
    # the geometry above - so it belongs to the object it is derived from and dies with it (XC-230,
    # ingest/TASK-017). Keyed by budget because two views of one @Case may have different ones.
    display_by_budget: dict[int, DisplayGeometry] = dataclass_field(default_factory=dict)
    # The ghost arrays, held apart from `fields` for two reasons: `vtkGhostType` is not a physical
    # quantity and does not belong in the list a user picks a @Variable from, and the point one and the
    # cell one share a name, so a dictionary keyed by name could only ever hold one of them.
    ghosts: dict[Association, np.ndarray] = dataclass_field(default_factory=dict)
    # What the file called each point and each cell (GL-034). Apart from `fields` for the same reason
    # the ghost arrays are: an identifier is not a physical quantity, its exactness is integer, and a
    # pedigree identifier may be text - none of which a float64 field can hold or should offer.
    identifiers: dict[Association, SourceIdentifiers] = dataclass_field(default_factory=dict)
    partitioning: Partitioning = dataclass_field(default_factory=Partitioning)
    source: SourceFrame | None = None
    # What CT-012 conversion produced this, where one did. Held rather than logged because three of
    # the conversions lose something no later step can recover - an image grid's spacing above all.
    conversion: ConversionRecord | None = None
    # What the survey found: how many steps and parts, and whether a part the manifest named was
    # absent. Held on the dataset so that a value read from it can carry the mark without the call
    # site having to remember to ask (ingest/AC-027).
    contents: "CaseContents | None" = None
    # An incompleteness of a kind the survey does not describe - recorded by whoever found it.
    partial: bool = False
    partial_reason: str | None = None

    @property
    def is_partial(self) -> bool:
        """Whether this dataset is incomplete, from either source.

        Two things can say so and they are not the same: the survey found a part the manifest named and
        could not open (`contents.missing_parts`), or a caller recorded an incompleteness of another
        kind (`mark_partial`). One property answers the question so that no reader has to check both and
        no path can be incomplete in a way the other source does not see.
        """
        return self.partial or (self.contents is not None and self.contents.is_partial)

    @property
    def incompleteness(self) -> str | None:
        """Why it is incomplete, in a line, or None."""
        if self.partial_reason:
            return self.partial_reason
        if self.contents is not None and self.contents.missing_parts:
            missing = ", ".join(self.contents.missing_parts)
            return f"マニフェストが名指したパートが見つかりません：{missing}"
        return None

    def caveats(self) -> frozenset[Caveat]:
        """The caveats every value read from this dataset carries.

        Read from the dataset rather than attached by a caller: a caveat that has to be remembered is a
        caveat that gets forgotten on the one path nobody tested.
        """
        return frozenset({Caveat.PARTIAL_DATASET}) if self.is_partial else frozenset()

    def value(self, name: str, index: int) -> ReportedValue:
        """One value of one field, carrying this dataset's caveats and the field's declared unit."""
        field = self.fields[name]
        raw = field.values[index]
        missing = bool(np.isnan(raw)) if np.issubdtype(field.values.dtype, np.floating) else False
        caveats = self.caveats()
        if field.unit is None:
            caveats = caveats | {Caveat.UNDECLARED_UNIT}
        return ReportedValue(
            value=None if missing else float(raw),
            unit=field.unit,
            digits=field.significant_digits,
            provenance=Provenance.DATASET,
            caveats=caveats,
        )

    def __post_init__(self) -> None:
        if self.points_m.ndim != 2 or self.points_m.shape[1] != 3:
            raise ValueError("points must be an (n, 3) array of metres in the canonical frame")
        # A field is indexed by the points or the cells it is attached to. Checking it here is what
        # turns a whole class of silent wrongness into a refusal at construction: a field that is a
        # point longer than the geometry is not off by one entry, it is a different point set, and
        # every index into it after that names the wrong place (E-132).
        for field in self.fields.values():
            if field.association is Association.INTEGRATION_POINT:
                expected = self.cell_count * (field.points_per_cell or 0)
            elif field.association is Association.POINT:
                expected = self.point_count
            else:
                expected = self.cell_count
            if field.values.shape[0] != expected:
                raise ValueError(
                    f"'{field.name}' has {field.values.shape[0]} {field.association.value} values for "
                    f"{expected} {field.association.value}s. A field of the wrong length is not a field "
                    "with a gap - it belongs to a different geometry, and reading it against this one "
                    "returns real values from the wrong places (INV-001)"
                )
        if self.contents is not None:
            # The survey counted the pieces; a caller restating them could restate them wrongly, and a
            # partitioning that disagrees with the manifest decides which numbers get refused. It is the
            # **partition** count that belongs here: a part's points are nobody's duplicates (XC-234).
            self.partitioning = Partitioning(self.contents.partitions, self.contents.ghost_level)
        for association, ghosts in self.ghosts.items():
            expected = self.point_count if association is Association.POINT else self.cell_count
            if ghosts.shape != (expected,):
                raise ValueError(
                    f"the {association.value} ghost array has {ghosts.shape} entries for {expected} "
                    f"{association.value}s; a mask that does not line up excludes the wrong ones"
                )

    def counted(self, association: Association) -> np.ndarray | None:
        """The mask of entries a number is computed over, or None when nothing was marked."""
        ghosts = self.ghosts.get(association)
        return None if ghosts is None else counted(ghosts, association)

    def _aggregate(self, name: str, aggregate: Aggregate) -> ReportedValue:
        """One number over a field, over the entries that count, or a refusal saying why not."""
        field = self.field(name)
        # A count is dimensionless whatever the field is in; every other aggregate here is in the
        # field's own unit, so it inherits the field's undeclared-unit caveat.
        unit = DIMENSIONLESS if aggregate is Aggregate.COUNT else field.unit
        caveats = self.caveats()
        if unit is None:
            caveats = caveats | {Caveat.UNDECLARED_UNIT}
        formula = f"{aggregate.value}({name})"

        def refuse(reason: str) -> ReportedValue:
            return ReportedValue.unavailable(
                reason, unit=unit, digits=field.significant_digits,
                provenance=Provenance.COMPUTED, caveats=caveats, formula=formula,
            )

        if field.association is Association.INTEGRATION_POINT and aggregate in _NEEDS_WEIGHTS:
            # An unweighted mean of quadrature-point values is not the cell's average, and their sum is
            # not its integral: both need the weights of the rule the solver used, and the file does not
            # carry it. The extremum is exactly the peak value the solver evaluated, and is reported.
            return refuse(
                f"'{name}' は積分点の値です。{_AGGREGATE_WORD[aggregate]}には求積則の重みが必要で、"
                "その情報はファイルにありません。重みなしで計算した値はセルの値ではありません（XC-123）"
            )

        mask = self.counted(field.association)
        reason = self.partitioning.refusal(aggregate, field.association, marked=mask is not None)
        if reason is not None:
            return refuse(reason)

        values = field.values if mask is None else field.values[mask]
        if values.size == 0:
            return refuse("計算対象の要素が 1 件もありません")
        missing = int(np.count_nonzero(np.isnan(values)))
        if missing and aggregate is not Aggregate.COUNT:
            return refuse(
                f"{values.size} 件のうち {missing} 件が欠損しています。"
                "残りだけで計算した値は、全体の値として読まれます（INV-011, XC-001）。"
            )

        # Where the extremum is, in the source's own words. Taken against the **unmasked** field so
        # that the index is the dataset's own, not a position within the filtered view.
        location: str | None = None
        if aggregate is Aggregate.EXTREMUM:
            position = int(np.argmax(field.values if mask is None else np.where(mask, field.values, -np.inf)))
            location = location_of(self.identifiers.get(field.association), position)

        result = {
            Aggregate.EXTREMUM: lambda: float(np.max(values)),
            Aggregate.TOTAL: lambda: float(np.sum(values)),
            Aggregate.MEAN: lambda: float(np.mean(values)),
            Aggregate.COUNT: lambda: float(values.size),
        }[aggregate]()
        return ReportedValue(
            value=result, unit=unit, digits=field.significant_digits,
            provenance=Provenance.COMPUTED, caveats=caveats, formula=formula, location=location,
        )

    def counted_entries(self, name: str) -> ReportedValue:
        """How many entries of a field a reported number is computed over."""
        return self._aggregate(name, Aggregate.COUNT)

    def maximum(self, name: str) -> ReportedValue:
        """The largest value of a field. Unharmed by partitioning: a repeat is the same number."""
        return self._aggregate(name, Aggregate.EXTREMUM)

    def total(self, name: str) -> ReportedValue:
        """The sum of a field over the entries that count.

        This is the sum the ghost mask governs, not yet a volume-weighted integral - weighting needs
        cell measures, which arrive with the geometry tasks. The double-counting INV-010 is about is
        the same in both.
        """
        return self._aggregate(name, Aggregate.TOTAL)

    def mean(self, name: str) -> ReportedValue:
        """The mean of a field over the entries that count."""
        return self._aggregate(name, Aggregate.MEAN)

    @property
    def point_count(self) -> int:
        return int(self.points_m.shape[0])

    @property
    def cell_count(self) -> int:
        return self.cells.count

    def field(self, name: str) -> Field:
        try:
            return self.fields[name]
        except KeyError:
            raise KeyError(f"no field named '{name}'; this dataset has {sorted(self.fields)}") from None

    def mark_partial(self, reason: str) -> None:
        """Record an incompleteness the survey did not describe, so every derived number says so.

        The "every derived number" half is `value()` and `ReportedValue.derive`, which carry
        `Caveat.PARTIAL_DATASET` through every computation (ingest/AC-027). Until those existed this
        method set a flag nobody read.
        """
        self.partial = True
        self.partial_reason = reason
