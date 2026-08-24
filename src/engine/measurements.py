"""Importing measured values against a @Case, from a table whose columns are declared.

A measurement file is not a result file: it comes from a rig or a spreadsheet, and it has no format
standard behind it. So this reads a small **declared** shape rather than trying to recognise one, and
refuses anything it cannot read exactly. The alternative - guessing which column is the value and which
the uncertainty - is the kind of convenience that is right most of the time and silently wrong the rest.

Every refusal here names the row and the reason, because a rejected measurement file is something the
user can fix in thirty seconds if told what is wrong and cannot fix at all if told "invalid".

Specification: GL-035, XC-125, ingest/AC-037, AC-038, AC-039. Evidence: E-070 (T1).
"""

from __future__ import annotations

import csv
from pathlib import Path

from domain_core.measurement import MeasuredValue, Uncertainty, UncertaintyKind

#: The columns this reads. `name`, `value` and `source` are required; the rest may be empty, and an
#: empty cell means **absent**, never zero and never a default.
REQUIRED_COLUMNS = ("name", "value", "source")
OPTIONAL_COLUMNS = ("unit", "uncertainty", "uncertainty_kind", "coverage_factor", "confidence", "at")


class MeasurementFileError(Exception):
    """Raised when a measurement file cannot be read exactly. Names the row and what is wrong."""


def _number(text: str, column: str, row: int) -> float:
    try:
        return float(text)
    except ValueError:
        raise MeasurementFileError(
            f"{row} 行目の {column} が数値ではありません：{text!r}"
        ) from None


def _uncertainty(record: dict[str, str], row: int) -> Uncertainty | None:
    raw = (record.get("uncertainty") or "").strip()
    if not raw:
        return None
    kind_text = (record.get("uncertainty_kind") or "").strip().lower()
    if not kind_text:
        raise MeasurementFileError(
            f"{row} 行目に不確かさがありますが、その種類が書かれていません。"
            "'standard'（合成標準）か 'expanded'（拡張）かを指定してください。"
            "この二つは同じ数値で二倍異なる区間を表します（E-070）"
        )
    try:
        kind = UncertaintyKind(kind_text)
    except ValueError:
        raise MeasurementFileError(
            f"{row} 行目の uncertainty_kind が {kind_text!r} です。"
            f"使えるのは {[k.value for k in UncertaintyKind]} です"
        ) from None

    coverage_text = (record.get("coverage_factor") or "").strip()
    confidence_text = (record.get("confidence") or "").strip()
    try:
        return Uncertainty(
            value=_number(raw, "uncertainty", row),
            kind=kind,
            coverage_factor=_number(coverage_text, "coverage_factor", row) if coverage_text else None,
            confidence=_number(confidence_text, "confidence", row) if confidence_text else None,
        )
    except ValueError as error:
        # The type's own refusals - an expanded uncertainty with no k, a standard one carrying one -
        # reported against the row they came from rather than as a bare exception.
        raise MeasurementFileError(f"{row} 行目：{error}") from None


def read_measurements(path: str | Path) -> tuple[MeasuredValue, ...]:
    """Every measured value in a table, or a refusal naming the row that could not be read."""
    location = Path(path)
    if not location.exists():
        raise MeasurementFileError(f"{location} がありません")

    with location.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing:
            raise MeasurementFileError(
                f"必須の列がありません：{', '.join(missing)}。"
                f"読める列は {list(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)} です"
            )
        unknown = sorted(columns - set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS))
        if unknown:
            # Not ignored. A column nobody reads is data the user believes was imported.
            raise MeasurementFileError(
                f"読み方の決まっていない列があります：{', '.join(unknown)}。"
                "無視すると、取り込まれたと思われたまま失われます"
            )

        found: list[MeasuredValue] = []
        for row, record in enumerate(reader, start=2):  # row 1 is the header
            name = (record.get("name") or "").strip()
            if not name and not any((value or "").strip() for value in record.values()):
                continue  # a blank line, which a spreadsheet leaves behind
            unit = (record.get("unit") or "").strip() or None
            at = (record.get("at") or "").strip() or None
            try:
                found.append(
                    MeasuredValue(
                        name=name,
                        value=_number((record.get("value") or "").strip(), "value", row),
                        unit=unit,
                        uncertainty=_uncertainty(record, row),
                        at=at,
                        source=(record.get("source") or "").strip(),
                    )
                )
            except ValueError as error:
                raise MeasurementFileError(f"{row} 行目：{error}") from None

    if not found:
        raise MeasurementFileError(f"{location.name} に測定値が 1 件もありません")
    return tuple(found)
