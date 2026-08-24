"""Whether a unit with an offset can survive multiplication, measured rather than reasoned about.

The expression language of `specs/13_scripting.md` carries units through arithmetic: a length divided
by a time is a velocity. The question this settles is what happens at the one unit family that is not a
pure scale factor - temperature, where degC and degF carry an offset (INV-028, `domain_core.units`).

Run with `PYTHONPATH=src python spike/measure_expression_units.py`. Needs no toolkit and no network;
it measures this product's own converter. Writes `expression_units.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

from domain_core.units import convert


def doubling_disagreement(value: float, symbol: str) -> dict[str, float]:
    """`2 x` computed before conversion, and after it.

    For a unit that is a pure scale factor the two are the same number, because doubling and scaling
    commute. For a unit with an offset they are not, and the gap is the offset itself - so "double this
    temperature" has no single answer, and any answer the product picked would be one it invented.
    """
    before = convert(2.0 * value, symbol, "K" if symbol.startswith("deg") or symbol == "K" else "m")
    after = 2.0 * convert(value, symbol, "K" if symbol.startswith("deg") or symbol == "K" else "m")
    return {"doubled_then_converted": before, "converted_then_doubled": after, "gap": after - before}


def main() -> None:
    measured = {
        "degC at 20": doubling_disagreement(20.0, "degC"),
        "degF at 68": doubling_disagreement(68.0, "degF"),
        "K at 293.15": doubling_disagreement(293.15, "K"),
        "mm at 20": doubling_disagreement(20.0, "mm"),
    }
    out = Path(__file__).with_name("expression_units.json")
    out.write_text(json.dumps(measured, indent=2), encoding="utf-8")
    for name, result in measured.items():
        print(f"{name}: gap {result['gap']:g}")


if __name__ == "__main__":
    main()
