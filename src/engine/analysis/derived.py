"""The derived-quantity catalogue, computed here and nowhere else (15_derived_quantities.md).

A result file carries components; an engineer asks about von Mises stress, a displacement's magnitude
or the first principal value. Between the two sits arithmetic that is easy to get subtly wrong and
impossible to notice afterwards, because every wrong answer is the right shape and a plausible size.
So every entry here carries the formula it used and the conventions it depended on, and the caller
records both beside the value (INV-020, XC-121, XC-282).

The conventions are the field's, not this product's (E-073): a six-component symmetric tensor is
**XX, YY, ZZ, XY, YZ, XZ**, a two-dimensional one **XX, YY, XY**, a vector **X, Y, Z**, and principal
values are ordered largest to smallest. A nine-component tensor has no standard naming and is refused
for everything but its components.

What this build derives: component, magnitude, von Mises, the three principal values, maximum shear
and trace - the scalar-valued entries whose unit is the source's. What it does not: principal
directions and the deviatoric part (tensor-valued), the invariants I2 and I3 (units the product cannot
name), and the complex-result entries (no reader here returns a complex field). Each is refused by
name rather than approximated.

Specification: 15_derived_quantities.md, INV-020, INV-021, INV-031, XC-121, XC-282, E-073.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from domain_core.dataset import Field

#: The one frame this build reports components in. Named on every component, never assumed silently
#: (15_derived_quantities.md "Component frames", INV-021).
GLOBAL_CARTESIAN = "global Cartesian"

VECTOR = ("X", "Y", "Z")
TENSOR_3D = ("XX", "YY", "ZZ", "XY", "YZ", "XZ")
TENSOR_2D = ("XX", "YY", "XY")

ORDER_CONVENTION = "成分順は XX, YY, ZZ, XY, YZ, XZ（二次元は XX, YY, XY）（E-073）"
PRINCIPAL_CONVENTION = "主値は大きい順 σ1 ≥ σ2 ≥ σ3（E-073）"
PLANE_CONVENTION = "三成分の対称テンソルは ZZ, YZ, XZ を 0 として読む（二次元・面内）"
PRECISION_CONVENTION = "float64 で計算し、元の場の精度で保持する（INV-031, INV-014）"


class DerivedError(Exception):
    """Raised where a quantity cannot be derived honestly from what the field is."""


class Quantity(str, Enum):
    """The catalogue entries this build computes. The strings are what `field.derive` takes."""

    COMPONENT = "component"
    MAGNITUDE = "magnitude"
    VON_MISES = "vonMises"
    PRINCIPAL = "principal"
    MAXIMUM_SHEAR = "maximumShear"
    TRACE = "trace"


#: Catalogue entries this build does not derive, each with why, so a request names its own answer.
NOT_BUILT: dict[str, str] = {
    "principalDirections": "テンソル値（方向ベクトル）を返す量はこの版では扱いません",
    "deviatoric": "テンソル値を返す量はこの版では扱いません",
    "invariants": "I2, I3 は元の単位の二乗・三乗で、この製品の単位系にありません",
    "amplitude": "複素数の場を返す読み手がこの版にありません",
    "valueAtPhase": "複素数の場を返す読み手がこの版にありません",
    "phaseAngle": "複素数の場を返す読み手がこの版にありません",
}


@dataclass(frozen=True, slots=True)
class Derived:
    """One derived scalar field: its values in float64, and what a reader needs to check them."""

    name: str
    values: np.ndarray
    formula: str
    conventions: tuple[str, ...]


def components_of(field: Field) -> int:
    return 1 if field.values.ndim == 1 else int(field.values.shape[1])


def component_names(field: Field) -> tuple[str, ...]:
    """The names the field's components carry by convention, or a refusal where there is none."""
    count = components_of(field)
    if count == 3:
        # Three components are a vector; a two-dimensional symmetric tensor also has three, and the
        # file does not say which. Vector is the reading; a caller wanting XX, YY, XY says `tensor`.
        return VECTOR
    if count == 6:
        return TENSOR_3D
    if count == 1:
        return ("",)
    raise DerivedError(
        f"'{field.name}' は {count} 成分で、この製品はその並びの意味を知りません"
        "（ベクトルは 3、対称テンソルは 6、二次元対称テンソルは 3）。九成分のテンソルには標準の名前がありません（E-073）"
    )


def _values64(field: Field) -> np.ndarray:
    # Computed in double whatever the field is stored in (INV-031); the result goes back to the
    # source's precision at the caller, because the source supports no more digits (INV-014).
    return np.asarray(field.values, dtype=np.float64)


def _as_tensor(field: Field, *, as_tensor: bool) -> tuple[np.ndarray, tuple[str, ...]]:
    """The six symmetric components in catalogue order, from a six- or three-component field."""
    count = components_of(field)
    values = _values64(field)
    if count == 6:
        return values, (ORDER_CONVENTION,)
    if count == 3 and as_tensor:
        rows = values.shape[0]
        full = np.zeros((rows, 6), dtype=np.float64)
        full[:, 0] = values[:, 0]  # XX
        full[:, 1] = values[:, 1]  # YY
        full[:, 3] = values[:, 2]  # XY
        return full, (ORDER_CONVENTION, PLANE_CONVENTION)
    raise DerivedError(
        f"'{field.name}' は {count} 成分で、対称テンソルではありません"
        "（六成分 XX, YY, ZZ, XY, YZ, XZ、または三成分 XX, YY, XY を tensor と指定）"
    )


def _principal(tensor: np.ndarray) -> np.ndarray:
    """The three eigenvalues per entry, largest first (E-073). A row with a missing component is
    missing in every principal value rather than a value computed around the hole (INV-011)."""
    rows = tensor.shape[0]
    out = np.full((rows, 3), np.nan, dtype=np.float64)
    finite = np.isfinite(tensor).all(axis=1)
    if finite.any():
        xx, yy, zz, xy, yz, xz = (tensor[finite, index] for index in range(6))
        matrices = np.empty((int(finite.sum()), 3, 3), dtype=np.float64)
        matrices[:, 0, 0], matrices[:, 1, 1], matrices[:, 2, 2] = xx, yy, zz
        matrices[:, 0, 1] = matrices[:, 1, 0] = xy
        matrices[:, 1, 2] = matrices[:, 2, 1] = yz
        matrices[:, 0, 2] = matrices[:, 2, 0] = xz
        out[finite] = np.linalg.eigvalsh(matrices)[:, ::-1]
    return out


def derive(
    field: Field,
    quantity: Quantity,
    *,
    component: str | None = None,
    as_tensor: bool = False,
    frame: str = GLOBAL_CARTESIAN,
) -> tuple[Derived, ...]:
    """The catalogue entry `quantity` of `field`, as one or more scalar fields with their formulas.

    `frame` is the frame components are reported in; only global Cartesian exists in this build, and a
    request for another is refused here by name rather than resolved silently (INV-021).
    """
    if frame != GLOBAL_CARTESIAN:
        raise DerivedError(
            f"フレーム '{frame}' は定義されていません。この版が報告できるのは {GLOBAL_CARTESIAN} だけです（INV-021, XC-122）"
        )
    frame_convention = f"フレーム：{frame}（INV-021）"
    count = components_of(field)
    if count == 1:
        raise DerivedError(f"'{field.name}' は一成分の場で、導出するものがありません")

    if quantity is Quantity.COMPONENT:
        names = TENSOR_2D if (as_tensor and count == 3) else component_names(field)
        if component is None or component not in names:
            raise DerivedError(
                f"'{field.name}' の成分は {list(names)} です（成分名 component を指定してください）"
            )
        index = names.index(component)
        return (Derived(
            f"{field.name}.{component}", _values64(field)[:, index],
            formula=f"{field.name}[{component}]",
            conventions=(ORDER_CONVENTION if len(names) != 3 or as_tensor else "成分順は X, Y, Z", frame_convention),
        ),)

    if quantity is Quantity.MAGNITUDE:
        if count != 3 or as_tensor:
            raise DerivedError(f"大きさはベクトル（三成分）の量です。'{field.name}' は {count} 成分です")
        values = _values64(field)
        return (Derived(
            f"{field.name}.magnitude", np.sqrt(np.sum(values * values, axis=1)),
            formula="sqrt(X^2 + Y^2 + Z^2)", conventions=("成分順は X, Y, Z", frame_convention, PRECISION_CONVENTION),
        ),)

    tensor, conventions = _as_tensor(field, as_tensor=as_tensor)
    xx, yy, zz, xy, yz, xz = (tensor[:, index] for index in range(6))
    if quantity is Quantity.VON_MISES:
        values = np.sqrt(((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2 + 6.0 * (xy**2 + yz**2 + xz**2)) / 2.0)
        return (Derived(
            f"{field.name}.vonMises", values,
            formula="sqrt( ((XX-YY)^2 + (YY-ZZ)^2 + (ZZ-XX)^2 + 6*(XY^2 + YZ^2 + XZ^2)) / 2 )",
            conventions=(*conventions, frame_convention, PRECISION_CONVENTION),
        ),)
    if quantity is Quantity.TRACE:
        return (Derived(
            f"{field.name}.trace", xx + yy + zz, formula="XX + YY + ZZ",
            conventions=(*conventions, frame_convention, PRECISION_CONVENTION),
        ),)
    principal = _principal(tensor)
    if quantity is Quantity.PRINCIPAL:
        return tuple(
            Derived(
                f"{field.name}.principal{rank + 1}", principal[:, rank],
                formula=f"eigenvalue {rank + 1} of the symmetric tensor, ordered largest to smallest",
                conventions=(*conventions, PRINCIPAL_CONVENTION, frame_convention, PRECISION_CONVENTION),
            )
            for rank in range(3)
        )
    if quantity is Quantity.MAXIMUM_SHEAR:
        return (Derived(
            f"{field.name}.maximumShear", (principal[:, 0] - principal[:, 2]) / 2.0,
            formula="(σ1 - σ3) / 2",
            conventions=(*conventions, PRINCIPAL_CONVENTION, frame_convention, PRECISION_CONVENTION),
        ),)
    raise DerivedError(f"'{quantity}' はこの版が導出する量ではありません")  # pragma: no cover - every member is handled
