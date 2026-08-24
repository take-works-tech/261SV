"""The same @Field compared between two @Case, on a mesh they share.

GL-011 says what a @Diff is and, in its `not`, what the dangerous version looks like: **a number that
stands alone**. A cross-mesh diff without its disclosure is physical difference, discretisation and
interpolation added together and presented as one figure. This module handles the shared-mesh case,
where none of that applies - and it is written so that the cross-mesh one cannot borrow it by accident.

Four refusals, each of which is an invariant this product already holds, arriving at the one place two
cases meet.

**Locations match by identifier where both cases have them** (AC-002, INV-023). Array position is the
same location only if both files were written the same way, and two runs of the same solver on the same
mesh do not guarantee that. Matching by position when identifiers are present is the defect that looks
right for as long as nobody remeshes.

**Different declared units are refused with both named** (AC-003). Not converted: a conversion here
would be one nobody asked for, inside an operation whose whole output is a difference.

**A location missing on either side is missing in the result** (AC-004, INV-011), never zero. Zero is a
value an engineer reads as "these agree".

**A relative difference names its reference** (AC-010), and reports a zero reference as **undefined**
rather than infinite. Infinity in a field is a number that propagates into a colour scale and takes the
whole picture with it.

Specification: GL-011, INV-003, INV-011, INV-023, diff/AC-001 to AC-004, AC-009, AC-010.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from domain_core.association import Association, AssociationError
from domain_core.dataset import Dataset, Field
from domain_core.identifiers import SourceIdentifiers
from domain_core.reported_value import DIMENSIONLESS


class Method(str, Enum):
    """How two cases were compared. Carried with the result, because it changes what the number means."""

    SHARED_MESH = "shared-mesh"                # position by position, same mesh
    SHARED_MESH_BY_IDENTIFIER = "by-identifier"  # matched by the identifiers both files wrote
    RESAMPLED = "resampled"                    # one dataset interpolated onto another (cross-mesh)


class DiffError(Exception):
    """Raised when a difference would mean something other than what it appears to."""


@dataclass(frozen=True, slots=True)
class Difference:
    """A diff as a @Field, with everything needed to say what it is (AC-009)."""

    field: Field
    left_case: str
    right_case: str
    method: Method
    #: Locations present in one case and not the other. Missing in the result, and counted so the
    #: number of them can be shown rather than inferred from a colour map full of gaps.
    unmatched: int = 0
    reference_case: str | None = None
    undefined_reference: int = 0

    @property
    def provenance(self) -> str:
        """Both cases and the method, in one line a report can carry (AC-009)."""
        line = f"{self.left_case} − {self.right_case}（{_METHOD_WORD[self.method]}）"
        if self.reference_case:
            line = f"({line}) / {self.reference_case}"
        return line

    def describe(self) -> str:
        parts = [self.provenance]
        if self.unmatched:
            parts.append(f"一方にしかない位置 {self.unmatched} 件は欠測です")
        if self.undefined_reference:
            parts.append(
                f"基準が 0 の位置 {self.undefined_reference} 件は未定義です"
                "（無限大ではありません — 無限大は色スケールに入り、絵全体を持って行きます）"
            )
        return "。".join(parts)


_METHOD_WORD = {
    Method.SHARED_MESH: "同一メッシュ・配列位置で対応",
    Method.SHARED_MESH_BY_IDENTIFIER: "同一メッシュ・識別子で対応",
    Method.RESAMPLED: "再サンプリング",
}


def _identifiers(dataset: Dataset, association: Association) -> SourceIdentifiers | None:
    found = dataset.identifiers.get(association)
    return found if found is not None and found.global_ids is not None else None


def difference(
    left: Dataset,
    right: Dataset,
    name: str,
    *,
    left_case: str,
    right_case: str,
) -> Difference:
    """The same field in two cases on one mesh, subtracted where both have a value."""
    a, b = left.field(name), right.field(name)

    if a.association is not b.association:
        raise AssociationError(
            f"'{name}' は一方が {a.association.value}、他方が {b.association.value} です。"
            "association の違う二つを引き算すると、別の場所どうしを引くことになります（INV-003）"
        )
    if a.unit != b.unit:
        # Named, not converted. A conversion here is one nobody asked for, inside an operation whose
        # entire output is a difference.
        raise DiffError(
            f"'{name}' の単位が異なります（{_unit_word(a.unit)} と {_unit_word(b.unit)}）。"
            "差を取る前に単位を揃えてください — ここでは換算しません（INV-002, XC-003）"
        )

    left_ids = _identifiers(left, a.association)
    right_ids = _identifiers(right, b.association)

    if left_ids is not None and right_ids is not None:
        values, unmatched = _by_identifier(a.values, b.values, left_ids, right_ids)
        method = Method.SHARED_MESH_BY_IDENTIFIER
    else:
        if a.values.shape != b.values.shape:
            raise DiffError(
                f"'{name}' の要素数が違います（{a.values.shape[0]} と {b.values.shape[0]}）。"
                "識別子がないため位置で対応させるほかなく、長さが違えば対応がつきません"
            )
        values = a.values - b.values
        unmatched = 0
        method = Method.SHARED_MESH

    return Difference(
        field=Field(f"Δ{name}", a.association, values, unit=a.unit),
        left_case=left_case,
        right_case=right_case,
        method=method,
        unmatched=unmatched,
    )


def _by_identifier(
    left_values: np.ndarray,
    right_values: np.ndarray,
    left_ids: SourceIdentifiers,
    right_ids: SourceIdentifiers,
) -> tuple[np.ndarray, int]:
    """Subtract by matching the identifiers both files wrote (AC-002).

    Array position is the same location only if both files were written the same way, and two runs of
    the same solver on the same mesh do not guarantee that. The result keeps the **left** case's order,
    because the diff is a field on the left case's geometry.
    """
    assert left_ids.global_ids is not None and right_ids.global_ids is not None
    lookup = {int(identifier): index for index, identifier in enumerate(right_ids.global_ids)}
    values = np.full(left_values.shape, np.nan, dtype=np.float64)
    unmatched = 0
    for index, identifier in enumerate(left_ids.global_ids):
        found = lookup.get(int(identifier))
        if found is None:
            # Present on the left and not on the right. Missing, never zero: zero is a value an
            # engineer reads as "these agree" (INV-011).
            unmatched += 1
            continue
        values[index] = left_values[index] - right_values[found]
    return values, unmatched


def relative_difference(
    left: Dataset,
    right: Dataset,
    name: str,
    *,
    left_case: str,
    right_case: str,
    reference: str,
) -> Difference:
    """A difference divided by a named reference (AC-010).

    `reference` is required and must be one of the two cases. Nothing here picks one: a relative
    difference against an unnamed denominator is a percentage nobody can reproduce.
    """
    if reference not in (left_case, right_case):
        raise DiffError(
            f"基準 '{reference}' は比較している二つのケース（{left_case}、{right_case}）の"
            "どちらでもありません。基準の名前がない相対差は、誰にも再現できない百分率です"
        )
    absolute = difference(left, right, name, left_case=left_case, right_case=right_case)
    denominator = (left if reference == left_case else right).field(name).values

    values = np.full(absolute.field.values.shape, np.nan, dtype=np.float64)
    undefined = 0
    for index, base in enumerate(denominator[: values.size]):
        if base == 0 or base != base:
            # Undefined, not infinite. An infinity in a field propagates into a colour scale and takes
            # the whole picture with it.
            undefined += 1
            continue
        values[index] = absolute.field.values[index] / base

    return Difference(
        field=Field(f"Δ{name}/{reference}", absolute.field.association, values, unit=DIMENSIONLESS),
        left_case=left_case,
        right_case=right_case,
        method=absolute.method,
        unmatched=absolute.unmatched,
        reference_case=reference,
        undefined_reference=undefined,
    )


def _unit_word(unit: str | None) -> str:
    return unit if unit else "未宣言"
