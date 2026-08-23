"""The complete-product design must stay connected to the product that exists.

`specs/16_application_model.md` describes the shell the shipped screens are a subset of. A design
document nothing checks drifts from the code in one direction and from the specification in the other,
and the drift is invisible because prose always parses. These checks read the design's own tables and
compare them with the design catalogue and with the region vocabulary the same file fixes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "specs" / "16_application_model.md"
SCENARIOS = ROOT / "specs" / "17_user_scenarios.md"
CATALOG = ROOT / "mockups" / "ui" / "lib" / "screen-catalog.json"

# Section 3 of the design fixes the vocabulary. It is read from the file rather than restated here for
# the reason XC-189 gives: two copies of one list agree with each other and with nothing else.
REGION_TABLE_HEADING = "## 3. Region vocabulary"
AREA_TABLE_HEADING = "## 4. Area catalogue"


def _table_rows(text: str, heading: str) -> list[list[str]]:
    section = text.split(heading, 1)[1]
    section = section.split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if set(stripped) <= set("|- :") or cells[0] in {"Region", "Area"}:
            continue
        rows.append(cells)
    return rows


def region_vocabulary() -> set[str]:
    rows = _table_rows(MODEL.read_text(encoding="utf-8"), REGION_TABLE_HEADING)
    names = {row[0].strip("`") for row in rows}
    assert len(names) == 8, f"the region vocabulary changed shape: {sorted(names)}"
    return names


def area_rows() -> list[list[str]]:
    rows = _table_rows(MODEL.read_text(encoding="utf-8"), AREA_TABLE_HEADING)
    # The catalogue is the first table under the heading; the prose below it carries no pipe rows.
    return [row for row in rows if len(row) == 5]


def test_every_area_declares_regions_from_the_one_vocabulary() -> None:
    vocabulary = region_vocabulary()
    for area, _edits, regions, _r1, _screen in area_rows():
        declared = {part.strip() for part in regions.split(",")}
        unknown = declared - vocabulary
        assert not unknown, f"{area} declares {sorted(unknown)}, which section 3 does not define"
        assert "main" in declared, f"{area} declares no main region; an Area always has one"


def test_the_area_catalogue_and_the_design_catalogue_agree_in_both_directions() -> None:
    """A screen the mockup carries with no Area is a surface the model cannot place; an Area claiming a
    screen the mockup does not carry is a claim about shipped work that is not there."""
    rows = area_rows()
    claimed = {row[4].strip("`") for row in rows if row[4] != "-"}
    shipped = {str(item["screen"]) for item in json.loads(CATALOG.read_text(encoding="utf-8"))["scenarios"]}
    assert claimed == shipped, f"only in the model: {sorted(claimed - shipped)}; only in the catalogue: {sorted(shipped - claimed)}"


def test_an_area_that_claims_a_screen_is_marked_as_shipped() -> None:
    for area, _edits, _regions, r1, screen in area_rows():
        if screen == "-":
            continue
        assert r1.startswith("yes"), f"{area} claims screen {screen} while its r1 column says '{r1}'"


def test_an_area_with_no_screen_says_what_it_is_instead_of_claiming_r1() -> None:
    for area, _edits, _regions, r1, screen in area_rows():
        if screen != "-":
            continue
        assert r1 != "yes", f"{area} says it ships in r1 but names no screen in the design catalogue"


def test_every_area_named_in_a_scenario_exists_in_the_catalogue() -> None:
    known = {row[0].strip("`") for row in area_rows()}
    text = SCENARIOS.read_text(encoding="utf-8")
    # Scenario tables name an Area in backticks in their "Where" column.
    referenced = set(re.findall(r"^\| \d+ \| `([a-z]+)`", text, flags=re.M))
    unknown = referenced - known
    assert not unknown, f"scenarios name areas the catalogue does not define: {sorted(unknown)}"
    assert len(referenced) >= 8, "the scenarios stopped naming where they happen"


def test_the_gap_list_names_only_things_r1_does_not_have() -> None:
    """Section 14 is the difference between the design and the product. A row that names something the
    product already has turns the list into decoration."""
    text = MODEL.read_text(encoding="utf-8")
    section = text.split("## 14. What r1 would have to gain", 1)[1]
    rows = [line for line in section.splitlines() if line.strip().startswith("|")]
    additions = [row.split("|")[1].strip() for row in rows if not set(row.strip()) <= set("|- :")]
    additions = [item for item in additions if item and item != "Addition"]
    assert len(additions) >= 8, "the gap list shrank without the product growing"
    shipped_areas = {row[0].strip("`") for row in area_rows() if row[4] != "-"}
    for addition in additions:
        named = set(re.findall(r"`([a-z]+)`", addition))
        overlap = named & shipped_areas
        assert not overlap, f"the gap list names {sorted(overlap)}, which r1 already ships"
