"""Numbers a person reads follow the interface language; numbers a machine reads never do.

INV-018 states the hazard exactly, and it is worth restating because it is the kind that leaves no
trace: in several European locales a comma is the decimal separator and a period groups thousands, so
`1.234` is **one thousand two hundred and thirty-four**. A file written under one locale and read under
another is off by a factor of a thousand, and every value in it still looks entirely plausible.

So this module has two functions and they are not variants of each other. `for_display` takes a locale.
`for_machine` **takes no locale and has no parameter that could carry one**, which is the only way to
make AC-034 hold at every call site rather than at the ones somebody remembered.

The third rule is for the files that are read by both. A CSV a person opens in a spreadsheet and a
script parses is the case where either choice is wrong for somebody, so it **states the convention it
used** in the file (AC-035). A stated convention is checkable; a guessed one is a factor of a thousand.

Specification: INV-018, workspace/AC-033, AC-034, AC-035, GL-024.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain_core.precision import format_value


@dataclass(frozen=True, slots=True)
class NumberConvention:
    """How one interface language writes a number for a person to read."""

    language: str
    decimal: str
    grouping: str
    #: How many digits a group holds. Three almost everywhere; the field exists so that a language which
    #: groups differently is a row in a table rather than a special case in the formatter.
    group_size: int = 3

    def describe(self) -> str:
        grouping = f"桁区切り '{self.grouping}'" if self.grouping else "桁区切りなし"
        return f"小数点 '{self.decimal}'、{grouping}"


#: The conventions this build knows. A language absent from here is formatted the machine way and said
#: to be, rather than guessed at from a similar one - a near-miss on a decimal separator is the whole
#: of the hazard.
#: U+202F, the narrow no-break space French typography groups with. Named because a literal space in
#: source is indistinguishable from an ASCII one by eye, and a test asserting it by literal is a test
#: nobody can read - which is how the two disagreed here the first time.
NARROW_NO_BREAK_SPACE = " "

CONVENTIONS: dict[str, NumberConvention] = {
    "ja": NumberConvention("ja", ".", ","),
    "en": NumberConvention("en", ".", ","),
    "de": NumberConvention("de", ",", "."),
    "fr": NumberConvention("fr", ",", " "),  # narrow no-break space, as French typography sets it
}

#: What every machine-readable output uses, whatever the interface language is (INV-018).
MACHINE = NumberConvention("machine", ".", "")

#: The line a dual-purpose file carries so that a reader does not have to infer the convention from the
#: values - which is exactly the inference that fails silently.
CONVENTION_NOTE = "numeric-convention: decimal-point='{decimal}' digit-grouping='{grouping}'"


def for_machine(value: float, digits: int, *, missing: str = "") -> str:
    """A number for a file another program will read.

    **No locale parameter**, deliberately. A function that could be told to use a comma is a function
    that will be, at the one call site nobody checked, and the resulting file is wrong by a factor of a
    thousand while looking correct.
    """
    if value is None or value != value:  # None and NaN
        return missing
    return format_value(value, digits, missing=missing)


def for_display(value: float | None, digits: int, language: str, *, missing: str = "—") -> str:
    """A number for a person, in the interface language.

    An unknown language falls back to the machine convention rather than to a similar-looking one. A
    near miss on a decimal separator is the whole of the hazard, so guessing is worse than plain.
    """
    if value is None or value != value:
        return missing
    convention = CONVENTIONS.get(language, MACHINE)
    plain = format_value(value, digits)
    return _apply(plain, convention)


def _apply(plain: str, convention: NumberConvention) -> str:
    """Rewrite a period-decimal, ungrouped number into one convention."""
    if "e" in plain or "E" in plain:
        # An exponent form has no grouping to add and its separator is the mantissa's. Rewriting the
        # mantissa alone keeps `1.5e-9` readable without inventing a grouped exponent nobody writes.
        mantissa, _, exponent = plain.partition("e" if "e" in plain else "E")
        return _apply(mantissa, convention) + "e" + exponent

    sign = "-" if plain.startswith("-") else ""
    body = plain.lstrip("-")
    whole, _, fraction = body.partition(".")

    if convention.grouping and len(whole) > convention.group_size:
        # Grouped from the right, at four digits and above, consistently.
        #
        # **A year must not come through here.** 2026 formatted as a quantity is "2,026", and no rule
        # about digit counts can tell a year from a number that happens to be 2026 - the formatter is
        # not told which it has. A year is not a measured quantity and is written by whatever formats
        # dates; trying to detect one here would be an inference with nothing behind it.
        digits = []
        for index, digit in enumerate(reversed(whole)):
            if index and index % convention.group_size == 0:
                digits.append(convention.grouping)
            digits.append(digit)
        whole = "".join(reversed(digits))

    return sign + whole + (convention.decimal + fraction if fraction else "")


def convention_note(convention: NumberConvention = MACHINE) -> str:
    """The line a dual-purpose file carries, stating what it did rather than leaving it to be inferred."""
    return CONVENTION_NOTE.format(
        decimal=convention.decimal, grouping=convention.grouping or "none"
    )


#: The steps a byte count is reported in, largest first. **Binary** steps with **binary names**: 1 << 30
#: bytes is a gibibyte, and calling it a gigabyte overstates nothing and misnames it by 7 per cent -
#: which is the kind of small, confident wrongness this product exists not to produce. The limits say
#: GiB in their own `human_value` (LIM-001, LIM-012), so this is also the spelling that agrees with them.
BYTE_STEPS = (("GiB", 1 << 30), ("MiB", 1 << 20), ("KiB", 1 << 10))


def bytes_as_text(size: int) -> str:
    """A byte count for a person to read.

    One implementation, in one place. There were two - `service/workspace/output.py` and
    `service/workspace/pack.py` each carried their own copy, identical and both mislabelled - which is
    the arrangement where one gets fixed and the other keeps printing the old answer.
    """
    for name, step in BYTE_STEPS:
        if size >= step:
            return f"{size / step:.1f} {name}"
    return f"{size} B"
