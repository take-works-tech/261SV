"""Spec linter — the machine-checkable definition of "complete".

Implements the twenty checks of spec-model section 6. Ships with the generated project and runs in its
CI: generation-time checking misses the decay that happens months later during hand edits.

Usage:
    python validate/check_specs.py [--root .] [--specs specs] [--code .] [--json]

Exit code 0 when no findings, 1 when any finding is reported, 2 on usage error.
Standard library only, so it runs anywhere the project already runs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ID_TYPES = ("REQ", "AC", "TASK", "CT", "INV", "GL", "MOD", "LIM", "EXT", "XC", "OPEN", "E")
ID_RE = re.compile(r"\b(" + "|".join(ID_TYPES) + r")-(\d{3})\b")
# A feature-scoped id may be qualified from outside its feature: "checkout/REQ-004" (model 6.1)
QUALIFIED_ID_RE = re.compile(r"([a-z][a-z0-9_-]*)/(" + "|".join(ID_TYPES) + r")-(\d{3})")
ITEM_HEAD_RE = re.compile(r"^###\s+((?:" + "|".join(ID_TYPES) + r")-\d{3})\s+[-—]\s+(.+?)\s*$")
ATTR_RE = re.compile(r"^\s*-\s+([a-z_]+):\s*(.*)$")
ACCEPTANCE_RE = re.compile(r"^\s+-\s+(AC-\d{3}):\s*(.+?)\s*$")
# A glossary term may be several words ("reference material"), so the marker captures a run of words
# and the longest defined term wins. Inline code is exempt: `@Term` in an instruction is an example.
TERM_REF_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_-]*(?:\s+[a-z][A-Za-z0-9_-]*){0,3})")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)")
BASIS_RE = re.compile(r"^(E-\d{3})\s*\((T[123])\)$")
UNWANTED_RE = re.compile(r"^If\s+.+,\s*then the\s+.+\s+shall\s+.+", re.IGNORECASE)
META_KEYS = ("status", "updated")
PLACEHOLDERS = ("TBD", "YYYY-MM-DD")
FENCE_RE = re.compile(r"^\s*```")
VALID_STATUS = ("draft", "active", "superseded")
ITEM_STATUS = ("active", "retired", "superseded")
FEATURE_SCOPED = ("REQ", "AC", "TASK")
PROJECT_SCOPE = "*"
INACTIVE_STATUS = ("retired", "superseded")
AUTOMATED_METHODS = ("unit", "integration", "end-to-end")
# Words that describe a feeling about the result rather than the result. An observer cannot agree or
# disagree with "gracefully", so a criterion built on one cannot be passed or failed.
WEAK_WORDS = (
    "gracefully", "appropriately", "properly", "correctly", "efficiently", "robustly", "seamlessly",
    "quickly", "fast", "slow", "user-friendly", "intuitive", "reasonable", "reasonably", "as needed",
    "if necessary", "where appropriate", "acceptable", "smoothly", "nicely", "easily", "sufficient",
)
WEAK_WORD_RE = re.compile(r"\b(" + "|".join(word.replace(" ", r"\s+") for word in WEAK_WORDS) + r")\b", re.IGNORECASE)
BARE_NUMBER_RE = re.compile(r"(?<![\w.-])\d{2,}(?![\w.-])")
DEFAULT_EVIDENCE_AGE_DAYS = 365
# The three questions that decide whether a dependency is safe to take on. Left blank they are not
# omissions of paperwork - they are the questions nobody asked before depending on it.
DEPENDENCY_COLUMNS = ("licence", "license", "adoption", "support")
TEST_REF_RE = re.compile(r"[\w./-]+\.(?:py|tsx|ts|jsx|js|rs|go|java|kt|cs)(?!\w)(?:::[\w:.\[\]-]+)?")
VALID_DECIDEDNESS = ("Fixed", "Bounded", "Delegated", "Open")
VALID_PRIORITY = ("MUST", "SHOULD", "COULD")
CODE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".kt", ".cs")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".mypy_cache"}


@dataclass
class Finding:
    check: int
    file: str
    line: int
    message: str

    def render(self) -> str:
        return f"[check {self.check}] {self.file}:{self.line}: {self.message}"


@dataclass
class Item:
    id: str
    title: str
    file: Path
    line: int
    attrs: dict[str, str] = field(default_factory=dict)
    acceptance: list[tuple[str, str, int]] = field(default_factory=list)

    @property
    def kind(self) -> str:
        return self.id.split("-")[0]

    @property
    def scope(self) -> str:
        parts = self.file.parts
        if "features" in parts:
            index = parts.index("features")
            if index + 1 < len(parts):
                return parts[index + 1]
        return PROJECT_SCOPE

    @property
    def key(self) -> tuple[str, str]:
        return (self.scope if self.kind in FEATURE_SCOPED else PROJECT_SCOPE, self.id)

    @property
    def active(self) -> bool:
        """A retired item keeps its ID so references survive, but it no longer states a requirement."""
        return self.attrs.get("status", "active") not in INACTIVE_STATUS


@dataclass
class SpecFile:
    path: Path
    meta: dict[str, str]
    items: list[Item]
    text: str
    meta_line: int
    fenced: set[int] = field(default_factory=set)


def _iter_spec_files(specs_root: Path) -> list[Path]:
    return sorted(p for p in specs_root.rglob("*.md") if not any(d in p.parts for d in SKIP_DIRS))


def parse_spec_file(path: Path) -> SpecFile:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    meta: dict[str, str] = {}
    meta_line = 0
    start = 0
    if lines and lines[0].strip() == "---":
        for index, raw in enumerate(lines[1:], start=2):
            if raw.strip() == "---":
                start = index
                break
            if ":" in raw:
                key, _, value = raw.partition(":")
                meta[key.strip()] = value.strip()
        meta_line = 1

    items: list[Item] = []
    current: Item | None = None
    in_acceptance = False
    fenced: set[int] = set()
    in_fence = False
    for index, raw in enumerate(lines[start:], start=start + 1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            fenced.add(index)
            continue
        if in_fence:
            fenced.add(index)
            continue
        head = ITEM_HEAD_RE.match(raw)
        if head:
            current = Item(id=head.group(1), title=head.group(2), file=path, line=index)
            items.append(current)
            in_acceptance = False
            continue
        if current is None:
            continue
        accept = ACCEPTANCE_RE.match(raw)
        if accept and in_acceptance:
            current.acceptance.append((accept.group(1), accept.group(2), index))
            continue
        attr = ATTR_RE.match(raw)
        if attr:
            key, value = attr.group(1), re.sub(r"\s{2,}#.*$", "", attr.group(2)).strip()
            in_acceptance = key == "acceptance" and value == ""
            if not in_acceptance:
                current.attrs[key] = value
            continue
        if raw.startswith("#"):
            current = None
            in_acceptance = False
    return SpecFile(path=path, meta=meta, items=items, text=text, meta_line=meta_line, fenced=fenced)


class Linter:
    def __init__(
        self,
        root: Path,
        specs_root: Path,
        code_root: Path,
        evidence_root: Path | None = None,
        max_evidence_age_days: int = DEFAULT_EVIDENCE_AGE_DAYS,
        today: date | None = None,
    ) -> None:
        self.max_evidence_age_days = max_evidence_age_days
        self.today = today or date.today()
        self.root = root
        self.specs_root = specs_root
        self.code_root = code_root
        self.findings: list[Finding] = []
        sources = _iter_spec_files(specs_root)
        if evidence_root is not None and evidence_root.is_dir():
            sources += _iter_spec_files(evidence_root)
        self.files = [parse_spec_file(p) for p in sources]
        self.items: dict[str, Item] = {}
        self.scoped: dict[tuple[str, str], Item] = {}
        self.duplicates: list[tuple[Item, Item]] = []
        for spec in self.files:
            for item in spec.items:
                first = self.scoped.setdefault(item.key, item)
                if first is not item:
                    self.duplicates.append((item, first))
                self.items.setdefault(item.id, item)
        # (scope, id) pairs that exist, including acceptance ids declared inside a requirement
        self.defined_scoped: set[tuple[str, str]] = set(self.scoped)
        for spec in self.files:
            scope = spec.path.parts[spec.path.parts.index("features") + 1] if "features" in spec.path.parts else PROJECT_SCOPE
            for item in spec.items:
                for ac_id, _, _ in item.acceptance:
                    self.defined_scoped.add((scope, ac_id))
        self.defined_ids: set[str] = {identifier for _, identifier in self.defined_scoped}
        self.terms = {item.title.lower() for item in self.items.values() if item.kind == "GL"}
        self.referenced_evidence: set[str] = set()

    def report(self, check: int, file: Path, line: int, message: str) -> None:
        try:
            shown = file.relative_to(self.root).as_posix()
        except ValueError:
            shown = file.as_posix()
        self.findings.append(Finding(check, shown, line, message))

    # check 1 + 5 + 6 -------------------------------------------------------
    def check_requirements(self) -> None:
        for spec in self.files:
            is_feature = "features" in spec.path.parts
            unwanted_seen = False
            requirements = [i for i in spec.items if i.kind == "REQ" and i.active]
            for item in requirements:
                if not item.acceptance:
                    self.report(1, spec.path, item.line, f"{item.id} has no acceptance criterion")
                priority = item.attrs.get("priority")
                if priority is None:
                    self.report(6, spec.path, item.line, f"{item.id} has no priority")
                elif priority not in VALID_PRIORITY:
                    self.report(6, spec.path, item.line, f"{item.id} priority '{priority}' is not one of {VALID_PRIORITY}")
                if "phase" not in item.attrs:
                    self.report(6, spec.path, item.line, f"{item.id} has no release phase")
                for _, text, _ in item.acceptance:
                    if UNWANTED_RE.match(text):
                        unwanted_seen = True
            if is_feature and requirements and not unwanted_seen:
                self.report(
                    5,
                    spec.path,
                    requirements[0].line,
                    "no 'If <trigger>, then the <system> shall <response>' criterion: failure semantics never stated",
                )

    # check 2 ---------------------------------------------------------------
    def _resolves(self, phrase: str) -> str | None:
        """Longest defined term that the phrase after @ starts with, or None."""
        words = phrase.split()
        for length in range(len(words), 0, -1):
            candidate = " ".join(words[:length]).lower().rstrip(".,;:)")
            if candidate in self.terms:
                return candidate
        return None

    def check_glossary_terms(self) -> None:
        for spec in self.files:
            for index, raw in enumerate(spec.text.splitlines(), start=1):
                if raw.startswith("### GL-") or index in spec.fenced:
                    continue
                line = INLINE_CODE_RE.sub(" ", raw)
                for match in TERM_REF_RE.finditer(line):
                    phrase = match.group(1)
                    if self._resolves(phrase) is None:
                        first = phrase.split()[0]
                        self.report(2, spec.path, index, f"term @{first} is used but not defined in the glossary")

    # check 3 ---------------------------------------------------------------
    def check_references(self) -> None:
        for spec in self.files:
            for index, raw in enumerate(spec.text.splitlines(), start=1):
                if raw.lstrip().startswith("### ") or index in spec.fenced:
                    continue
                for match in LINK_RE.finditer(raw):
                    target = match.group(1).strip()
                    if target.startswith(("http://", "https://", "mailto:")):
                        continue
                    if not (spec.path.parent / target).exists():
                        self.report(3, spec.path, index, f"link target '{target}' does not exist")
                scope = (
                    spec.path.parts[spec.path.parts.index("features") + 1]
                    if "features" in spec.path.parts
                    else PROJECT_SCOPE
                )
                # Only feature-scoped kinds can be qualified. "schema/CT-001.json" is a path, and
                # reading it as a qualified id invents a feature called schema.
                qualified = {
                    (match.group(1), f"{match.group(2)}-{match.group(3)}"): match.start()
                    for match in QUALIFIED_ID_RE.finditer(raw)
                    if match.group(2) in FEATURE_SCOPED
                }
                for owner, ref in qualified:
                    if (owner, ref) not in self.defined_scoped:
                        self.report(3, spec.path, index, f"{owner}/{ref} is referenced but never defined")
                qualified_ids = {ref for _, ref in qualified}
                for match in ID_RE.finditer(raw):
                    kind = match.group(1)
                    ref = f"{kind}-{match.group(2)}"
                    if ref in qualified_ids:
                        continue
                    if ref.startswith("E-"):
                        self.referenced_evidence.add(ref)
                        continue
                    if kind not in FEATURE_SCOPED:
                        if (PROJECT_SCOPE, ref) not in self.defined_scoped:
                            self.report(3, spec.path, index, f"{ref} is referenced but never defined")
                        continue
                    owners = sorted({owner for owner, identifier in self.defined_scoped if identifier == ref})
                    if not owners:
                        self.report(3, spec.path, index, f"{ref} is referenced but never defined")
                    elif scope in owners:
                        continue
                    elif len(owners) > 1:
                        self.report(3, spec.path, index, f"{ref} is ambiguous: defined in {', '.join(owners)}. Qualify it as <feature>/{ref}")

    # check 4 + 9 -----------------------------------------------------------
    def check_decidedness(self) -> None:
        needs_label = {"REQ", "LIM", "CT", "EXT", "XC", "INV"}
        for spec in self.files:
            for item in spec.items:
                if item.kind not in needs_label or not item.active:
                    continue
                label = item.attrs.get("decidedness")
                if label is None:
                    self.report(4, spec.path, item.line, f"{item.id} has no decidedness label")
                    continue
                if label not in VALID_DECIDEDNESS:
                    self.report(4, spec.path, item.line, f"{item.id} decidedness '{label}' is not one of {VALID_DECIDEDNESS}")
                    continue
                if label == "Open":
                    tracking = item.attrs.get("open")
                    if not tracking:
                        self.report(4, spec.path, item.line, f"{item.id} is Open with no tracking ID")
                    elif tracking not in self.items:
                        self.report(4, spec.path, item.line, f"{item.id} tracks {tracking}, which is not defined")
                if label == "Fixed":
                    basis = item.attrs.get("basis")
                    if not basis:
                        self.report(9, spec.path, item.line, f"{item.id} is Fixed with no basis")
                        continue
                    # A decision may rest on more than one source: "E-001 (T1), E-004 (T2)"
                    parts = [part.strip() for part in basis.split(",") if part.strip()]
                    matches = [BASIS_RE.match(part) for part in parts]
                    if not parts or any(match is None for match in matches):
                        self.report(9, spec.path, item.line, f"{item.id} basis '{basis}' is not '<E-NNN> (T1|T2|T3)', or a comma-separated list of them")
                        continue
                    for matched in matches:
                        evidence_id, tier = matched.group(1), matched.group(2)
                        self.referenced_evidence.add(evidence_id)
                        if tier == "T3":
                            self.report(9, spec.path, item.line, f"{item.id} is Fixed on tier T3 evidence ({evidence_id}), which may never justify a Fixed value")
                        if evidence_id not in self.items:
                            self.report(3, spec.path, item.line, f"{item.id} cites {evidence_id}, which is not in the evidence record")

    # check 6 (file metadata) ----------------------------------------------
    def check_metadata(self) -> None:
        for spec in self.files:
            for key in META_KEYS:
                if key not in spec.meta:
                    self.report(6, spec.path, 1, f"file has no '{key}' metadata")
            status = spec.meta.get("status")
            if status is not None and status not in VALID_STATUS:
                self.report(6, spec.path, 1, f"status '{status}' is not one of {VALID_STATUS}")
            tracked = self._tracked_open_ranges(spec)
            for index, raw in enumerate(spec.text.splitlines(), start=1):
                if index in spec.fenced:
                    continue
                # Inline code is exempt: a line explaining the `TBD` convention is documentation.
                line = INLINE_CODE_RE.sub(" ", raw)
                for token in PLACEHOLDERS:
                    if token in line and not any(start <= index <= end for start, end in tracked):
                        self.report(6, spec.path, index, f"unfilled placeholder '{token}'")

    @staticmethod
    def _tracked_open_ranges(spec: SpecFile) -> list[tuple[int, int]]:
        """Line ranges of items that are declared Open *and* carry a tracking ID.

        A placeholder is normally a defect - somebody meant to come back and did not. Inside a tracked
        Open item it is the honest state: the model says a value may be undecided, and the tracking ID
        is what stops it being silent. Without this exemption the linter pushes an author to invent a
        number to make it pass, which is the failure it exists to prevent, wearing a green tick.
        """
        ranges: list[tuple[int, int]] = []
        boundaries = [item.line for item in spec.items] + [len(spec.text.splitlines()) + 1]
        for position, item in enumerate(spec.items):
            if item.attrs.get("decidedness") != "Open" or not item.attrs.get("open"):
                continue
            ranges.append((item.line, boundaries[position + 1] - 1))
        return ranges

    # check 7 ---------------------------------------------------------------
    def check_code_parity(self) -> None:
        code_files = {
            p: p.read_text(encoding="utf-8", errors="ignore")
            for p in self.code_root.rglob("*")
            if p.suffix in CODE_SUFFIXES and not any(d in p.parts for d in SKIP_DIRS)
        }
        for spec in self.files:
            for item in spec.items:
                target = item.attrs.get("source_of_truth")
                if not target:
                    if item.attrs.get("decidedness") == "Fixed" and item.attrs.get("value") and item.active:
                        self.report(15, spec.path, item.line, f"{item.id} fixes a value but does not say where it lives: a value with no one place has as many as it has readers")
                    continue
                # Before the code exists a value still has a planned home (D-3). "planned:" states it
                # and is exempt; removing the word is when the path must resolve.
                if target.startswith("planned:"):
                    continue
                if ":" not in target:
                    self.report(7, spec.path, item.line, f"{item.id} source_of_truth '{target}' is not '<path>:<SYMBOL>'")
                    continue
                rel, _, symbol = target.rpartition(":")
                path = self.root / rel
                if not path.exists():
                    self.report(7, spec.path, item.line, f"{item.id} source_of_truth file '{rel}' does not exist")
                    continue
                assign = re.compile(r"^\s*(?:export\s+)?(?:const\s+|let\s+|var\s+)?" + re.escape(symbol) + r"\s*(?::[^=]+)?=\s*(.+?)\s*;?\s*$", re.MULTILINE)
                source = code_files.get(path, path.read_text(encoding="utf-8", errors="ignore"))
                found = assign.search(source)
                if not found:
                    self.report(7, spec.path, item.line, f"{item.id} symbol '{symbol}' is not assigned in {rel}")
                    continue
                declared = item.attrs.get("value")
                if declared is not None and found.group(1).strip().rstrip(",") != declared:
                    self.report(
                        7,
                        spec.path,
                        item.line,
                        f"{item.id} says {declared} but {rel} assigns {found.group(1).strip()}",
                    )
                elsewhere = [
                    other
                    for other, body in code_files.items()
                    if other.resolve() != path.resolve() and assign.search(body)
                ]
                for duplicate in elsewhere:
                    self.report(
                        7,
                        spec.path,
                        item.line,
                        f"{item.id} symbol '{symbol}' is also assigned in {duplicate.relative_to(self.root).as_posix()}: one value, one place",
                    )

    # check 8 ---------------------------------------------------------------
    def check_contract_schemas(self) -> None:
        for spec in self.files:
            for item in spec.items:
                if item.kind != "CT":
                    continue
                schema_ref = item.attrs.get("schema")
                if not schema_ref:
                    self.report(8, spec.path, item.line, f"{item.id} has no machine-readable schema")
                    continue
                schema_path = spec.path.parent / schema_ref
                if not schema_path.exists():
                    self.report(8, spec.path, item.line, f"{item.id} schema '{schema_ref}' does not exist")
                    continue
                try:
                    schema = json.loads(schema_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as error:
                    self.report(8, spec.path, item.line, f"{item.id} schema is not valid JSON: {error.msg}")
                    continue
                declared = item.attrs.get("version")
                actual = str(schema.get("version", ""))
                if declared and actual != declared:
                    self.report(8, spec.path, item.line, f"{item.id} says version {declared} but the schema says {actual or 'nothing'}")

    # check 9 (unreferenced evidence) --------------------------------------
    def check_evidence_usage(self) -> None:
        for item in self.items.values():
            if item.kind == "E" and item.id not in self.referenced_evidence:
                self.report(9, item.file, item.line, f"{item.id} is recorded but nothing references it")

    # check 10 --------------------------------------------------------------
    def check_duplicate_ids(self) -> None:
        for duplicate, first in self.duplicates:
            try:
                where = first.file.relative_to(self.root).as_posix()
            except ValueError:
                where = first.file.as_posix()
            self.report(
                10,
                duplicate.file,
                duplicate.line,
                f"{duplicate.id} is already defined at {where}:{first.line} in the same scope: IDs are never reused",
            )

    # check 11 --------------------------------------------------------------
    def check_verification_coverage(self) -> None:
        plans = [spec for spec in self.files if spec.path.parent.name == "verification"]
        if not plans:
            for spec in self.files:
                for item in spec.items:
                    if item.acceptance:
                        self.report(11, spec.path, item.line, "no verification plan exists: specs/verification/plan.md is missing")
                        return
            return
        planned = planned_acceptance(plans)
        for spec in self.files:
            scope = (
                spec.path.parts[spec.path.parts.index("features") + 1]
                if "features" in spec.path.parts
                else PROJECT_SCOPE
            )
            for item in spec.items:
                if not item.active:
                    continue
                for ac_id, _, line in item.acceptance:
                    if (scope, ac_id) in planned or (PROJECT_SCOPE, ac_id) in planned:
                        continue
                    self.report(11, spec.path, line, f"{scope}/{ac_id} has no entry in the verification plan: how it is checked is undefined")

    # check 12 --------------------------------------------------------------
    def check_item_lifecycle(self) -> None:
        for spec in self.files:
            for item in spec.items:
                status = item.attrs.get("status")
                if status is None:
                    continue
                if status not in ITEM_STATUS:
                    self.report(12, spec.path, item.line, f"{item.id} status '{status}' is not one of {ITEM_STATUS}")
                    continue
                if status in INACTIVE_STATUS:
                    replacement = item.attrs.get("superseded_by")
                    if not replacement:
                        self.report(12, spec.path, item.line, f"{item.id} is {status} but does not name what replaced it")
                    elif replacement not in self.defined_ids and replacement.lower() not in ("none", "nothing"):
                        self.report(12, spec.path, item.line, f"{item.id} is {status} by {replacement}, which is not defined")

    # check 13 --------------------------------------------------------------
    def check_contradictions(self) -> None:
        owners: dict[str, Item] = {}
        terms: dict[str, Item] = {}
        for spec in self.files:
            for item in spec.items:
                if not item.active:
                    continue
                target = item.attrs.get("source_of_truth")
                if target and not target.startswith("TBD"):
                    first = owners.setdefault(target, item)
                    if first is not item:
                        self.report(13, spec.path, item.line, f"{item.id} and {first.id} both claim {target}: a value has one owner")
                if item.kind == "GL":
                    first_term = terms.setdefault(item.title.lower(), item)
                    if first_term is not item:
                        self.report(13, spec.path, item.line, f"{item.id} defines '{item.title}' again, already defined by {first_term.id}")

    # check 14 --------------------------------------------------------------
    def check_test_references(self) -> None:
        for spec in self.files:
            if spec.path.parent.name != "verification":
                continue
            for index, raw in enumerate(spec.text.splitlines(), start=1):
                if not raw.lstrip().startswith("|"):
                    continue
                cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
                if len(cells) < 2 or not ID_RE.search(cells[0]):
                    continue
                method = cells[1].lower()
                if not any(method.startswith(automated) for automated in AUTOMATED_METHODS):
                    continue
                # A spec is written before the code exists (D-3). A row marked planned states the
                # intent now and starts demanding a real test the moment it claims to be implemented.
                if "planned" in method:
                    continue
                reference = TEST_REF_RE.search(raw)
                if not reference:
                    self.report(14, spec.path, index, f"{cells[0]} is verified automatically but names no test")
                    continue
                test_file = reference.group(0).split("::")[0]
                if not (self.root / test_file).exists():
                    self.report(14, spec.path, index, f"{cells[0]} names test file '{test_file}', which does not exist")

    # check 15 --------------------------------------------------------------
    def check_bounded_has_principles(self) -> None:
        bounded = [
            (spec, item)
            for spec in self.files
            for item in spec.items
            if item.attrs.get("decidedness") == "Bounded" and item.active
        ]
        if not bounded:
            return
        principles = [
            item
            for spec in self.files
            if "principles" in spec.path.stem
            for item in spec.items
            if item.active and not any(value.startswith("TBD") for value in item.attrs.values())
        ]
        if principles:
            return
        spec, item = bounded[0]
        self.report(
            15,
            spec.path,
            item.line,
            f"{item.id} is Bounded but no product principle is defined: with nothing to judge by, Bounded is Delegated",
        )

    # check 16 --------------------------------------------------------------
    def check_weak_acceptance(self) -> None:
        for spec in self.files:
            for item in spec.items:
                if not item.active:
                    continue
                for ac_id, body, line in item.acceptance:
                    found = WEAK_WORD_RE.search(body)
                    if found:
                        self.report(16, spec.path, line, f"{ac_id} is judged by '{found.group(0)}': name what an observer would see instead")

    # check 17 --------------------------------------------------------------
    def check_out_of_scope(self) -> None:
        for spec in self.files:
            if spec.path.name != "spec.md" or "features" not in spec.path.parts:
                continue
            lines = spec.text.splitlines()
            heading = next((index for index, raw in enumerate(lines) if raw.strip().lower().startswith("## out of scope")), None)
            if heading is None:
                self.report(17, spec.path, 1, "no 'Out of scope' section: the only mechanism that stops an agent expanding the feature")
                continue
            entries = 0
            for raw in lines[heading + 1:]:
                if raw.startswith("#"):
                    break
                stripped = raw.strip()
                if stripped.startswith("- ") and len(stripped) > 2 and not stripped.startswith("- TBD"):
                    entries += 1
            if entries == 0:
                self.report(17, spec.path, heading + 1, "'Out of scope' is empty: an empty list means nobody decided, not that nothing is excluded")

    # check 18 --------------------------------------------------------------
    def check_evidence_freshness(self) -> None:
        for spec in self.files:
            for item in spec.items:
                if item.kind != "E":
                    continue
                stamp = item.attrs.get("verified")
                if not stamp or stamp.startswith("TBD") or stamp.startswith("YYYY"):
                    continue
                try:
                    verified = date.fromisoformat(stamp.split()[0])
                except ValueError:
                    self.report(18, spec.path, item.line, f"{item.id} verified date '{stamp}' is not a date (YYYY-MM-DD)")
                    continue
                age = (self.today - verified).days
                if age > self.max_evidence_age_days:
                    self.report(18, spec.path, item.line, f"{item.id} was last verified {age} days ago: re-check it or record that it still holds")

    # check 19 --------------------------------------------------------------
    def check_inline_numbers(self) -> None:
        for spec in self.files:
            for item in spec.items:
                if not item.active:
                    continue
                for ac_id, body, line in item.acceptance:
                    if ID_RE.search(body):
                        continue
                    number = BARE_NUMBER_RE.search(body)
                    if number:
                        self.report(19, spec.path, line, f"{ac_id} hard-codes {number.group(0)} instead of citing a limit: two places, two values, one day apart")

    # check 20 --------------------------------------------------------------
    def check_dependency_table(self) -> None:
        for spec in self.files:
            header: list[str] | None = None
            required: dict[str, int] = {}
            for index, raw in enumerate(spec.text.splitlines(), start=1):
                if index in spec.fenced:
                    continue
                stripped = raw.strip()
                if not stripped.startswith("|"):
                    header = None
                    required = {}
                    continue
                cells = [cell.strip() for cell in stripped.strip("|").split("|")]
                if header is None:
                    lowered = [cell.lower() for cell in cells]
                    if not lowered or "dependency" not in lowered[0]:
                        continue
                    header = lowered
                    required = {
                        name: position
                        for position, name in enumerate(lowered)
                        if any(name.startswith(column) for column in DEPENDENCY_COLUMNS)
                    }
                    continue
                if set(stripped) <= set("|- :"):
                    continue
                if not cells or not cells[0] or cells[0].startswith("TBD"):
                    continue
                for name, position in required.items():
                    if position >= len(cells) or not cells[position] or cells[position] in ("-", "?"):
                        self.report(20, spec.path, index, f"dependency '{cells[0]}' has no {name}: that is the question nobody asked before depending on it")

    def check_named_references(self) -> None:
        """An ID written next to a name that belongs to a *different* item.

        `MOD-008 pipeline` when MOD-008 is the assistant module: the id exists, the name exists, and
        every check that verifies references pass. Only a reader who knows both catches it - which is
        to say, nobody, six months later. Prose after an id is normal (`MOD-002 knows which reader
        ran`), so the rule is deliberately narrow: flag only when the following word is *another
        item's own name*.
        """
        by_name: dict[tuple[str, str], str] = {}
        for spec in self.files:
            for item in spec.items:
                name = item.title.strip().lower()
                if name and " " not in name:
                    by_name[(item.kind, name)] = item.id
        if not by_name:
            return
        pattern = re.compile(r"\b([A-Z]{2,4})-(\d{3})\s+([A-Za-z][A-Za-z0-9_-]*)")
        for spec in self.files:
            for index, raw in enumerate(spec.text.splitlines(), start=1):
                if index in spec.fenced:
                    continue
                for match in pattern.finditer(raw):
                    kind, number, word = match.group(1), match.group(2), match.group(3).lower()
                    owner = by_name.get((kind, word))
                    if owner is None:
                        continue
                    written = f"{kind}-{number}"
                    if owner != written:
                        self.report(
                            21,
                            spec.path,
                            index,
                            f"{written} is written next to the name of {owner}: one of the two is wrong",
                        )

    def check_decision_reaches_its_contracts(self) -> None:
        """A decision dated after the contract it says it affects.

        This is how a specification rots while every other check stays green: somebody decides
        something, writes it down as a decision, lists the contracts it changes - and does not change
        them. The IDs all resolve, the schemas all validate, and the contract quietly says the opposite
        of the decision. Comparing the decision's date against the `updated:` of each file it claims to
        affect catches exactly that, and costs one line per decision to keep true.
        """
        contract_files: dict[str, tuple[SpecFile, str]] = {}
        for spec in self.files:
            updated = spec.meta.get("updated", "")
            for item in spec.items:
                if item.kind in ("CT", "MOD", "INV", "GL", "LIM"):
                    contract_files[item.id] = (spec, updated)

        for spec in self.files:
            for item in spec.items:
                decided = item.attrs.get("decided", "").split(",")[0].strip()
                affects = item.attrs.get("affects", "")
                if not decided or not affects or not item.active:
                    continue
                for target in (name.strip() for name in affects.split(",")):
                    entry = contract_files.get(target)
                    if entry is None:
                        continue
                    target_spec, updated = entry
                    if target_spec.path == spec.path or not updated:
                        continue
                    if updated < decided:
                        self.report(
                            22,
                            spec.path,
                            item.line,
                            f"{item.id} was decided {decided} and affects {target}, whose file "
                            f"{target_spec.path.name} was last updated {updated}: the decision may not have reached it",
                        )

    def run(self) -> list[Finding]:
        self.check_metadata()
        self.check_requirements()
        self.check_glossary_terms()
        self.check_decidedness()
        self.check_references()
        self.check_code_parity()
        self.check_contract_schemas()
        self.check_evidence_usage()
        self.check_duplicate_ids()
        self.check_verification_coverage()
        self.check_item_lifecycle()
        self.check_contradictions()
        self.check_test_references()
        self.check_bounded_has_principles()
        self.check_weak_acceptance()
        self.check_out_of_scope()
        self.check_evidence_freshness()
        self.check_inline_numbers()
        self.check_dependency_table()
        self.check_named_references()
        self.check_decision_reaches_its_contracts()
        self.findings.sort(key=lambda f: (f.file, f.line, f.check))
        return self.findings


def planned_acceptance(files: list[SpecFile]) -> set[tuple[str, str]]:
    """(feature, acceptance id) pairs listed in a verification plan **table row**.

    Prose is not a plan: a sentence explaining why a criterion is hard to check would otherwise count as
    checking it. And the pair matters, not the number: two features each numbering from AC-001 means a
    bare id would mark one feature's criterion covered by the other's row.
    """
    planned: set[tuple[str, str]] = set()
    for spec in files:
        if spec.path.parent.name != "verification":
            continue
        for raw in spec.text.splitlines():
            if not raw.lstrip().startswith("|"):
                continue
            qualified = {
                (match.group(1), f"{match.group(2)}-{match.group(3)}")
                for match in QUALIFIED_ID_RE.finditer(raw)
                if match.group(2) == "AC"
            }
            planned |= qualified
            covered = {identifier for _, identifier in qualified}
            for match in ID_RE.finditer(raw):
                if match.group(1) != "AC":
                    continue
                identifier = f"AC-{match.group(2)}"
                if identifier not in covered:
                    planned.add((PROJECT_SCOPE, identifier))
    return planned


def build_report(linter: "Linter") -> dict:
    """Summarise readiness. Counts, not judgement: the numbers say what is left, not whether to ship."""
    requirements = [item for spec in linter.files for item in spec.items if item.kind == "REQ" and item.active]
    acceptance = [(item, ac_id) for item in requirements for ac_id, _, _ in item.acceptance]

    planned = {identifier for _, identifier in planned_acceptance(linter.files)}

    by_phase: dict[str, dict[str, int]] = {}
    for item in requirements:
        phase = item.attrs.get("phase", "unset")
        priority = item.attrs.get("priority", "unset")
        by_phase.setdefault(phase, {}).setdefault(priority, 0)
        by_phase[phase][priority] += 1

    fixed = [item for spec in linter.files for item in spec.items if item.attrs.get("decidedness") == "Fixed"]
    tiers: dict[str, int] = {}
    for item in fixed:
        # A basis may cite several sources; the weakest tier is the one that matters.
        parts = [BASIS_RE.match(part.strip()) for part in item.attrs.get("basis", "").split(",") if part.strip()]
        found = [match.group(2) for match in parts if match]
        label = max(found) if found else "none"
        tiers[label] = tiers.get(label, 0) + 1

    # A superseded question is not an open one: counting it keeps a resolved decision on the worry list.
    opens = sorted(
        item.id
        for spec in linter.files
        for item in spec.items
        if item.active and (item.attrs.get("decidedness") == "Open" or item.kind == "OPEN")
    )

    unverified = sorted({ac_id for _, ac_id in acceptance if ac_id not in planned})
    blocking = [
        item.id
        for item in requirements
        if item.attrs.get("phase") == "r1"
        and item.attrs.get("priority") == "MUST"
        and any(ac_id not in planned for ac_id, _, _ in item.acceptance)
    ]

    return {
        "requirements": len(requirements),
        "by_phase": by_phase,
        "acceptance_criteria": len(acceptance),
        "verified_in_plan": len(acceptance) - len(unverified),
        "unverified": unverified,
        "fixed_values": len(fixed),
        "fixed_by_tier": tiers,
        "with_source_of_truth": sum(1 for item in fixed if item.attrs.get("source_of_truth")),
        "open_questions": opens,
        "release_blocking": sorted(set(blocking)),
        "retired": sorted(
            item.id for spec in linter.files for item in spec.items if not item.active
        ),
        "context_cost": context_cost(linter),
    }


def context_cost(linter: "Linter") -> dict:
    """Bytes an agent must load. The project-wide layer is paid on every feature, so it is the one to watch."""
    core = 0
    features: dict[str, int] = {}
    for spec in linter.files:
        size = len(spec.text.encode("utf-8"))
        parts = spec.path.parts
        if "features" in parts:
            features[parts[parts.index("features") + 1]] = features.get(parts[parts.index("features") + 1], 0) + size
        else:
            core += size
    worst = max(features.items(), key=lambda pair: pair[1], default=("-", 0))
    return {
        "core_bytes": core,
        "features": features,
        "largest_feature": worst[0],
        "largest_feature_bytes": worst[1],
        "worst_case_bytes": core + worst[1],
    }


def render_report(report: dict) -> str:
    lines = ["Release readiness", "=" * 17, ""]
    lines.append(f"requirements            {report['requirements']}")
    for phase in sorted(report["by_phase"]):
        counts = ", ".join(f"{priority} {count}" for priority, count in sorted(report["by_phase"][phase].items()))
        lines.append(f"  phase {phase:<15} {counts}")
    lines.append("")
    lines.append(f"acceptance criteria     {report['acceptance_criteria']}")
    lines.append(f"  with a verification    {report['verified_in_plan']}")
    if report["unverified"]:
        lines.append(f"  without one            {', '.join(report['unverified'])}")
    lines.append("")
    lines.append(f"Fixed values            {report['fixed_values']}")
    tiers = ", ".join(f"{tier} {count}" for tier, count in sorted(report["fixed_by_tier"].items())) or "-"
    lines.append(f"  by evidence tier       {tiers}")
    lines.append(f"  with source_of_truth   {report['with_source_of_truth']}")
    lines.append("")
    lines.append(f"open questions          {', '.join(report['open_questions']) or 'none'}")
    lines.append(f"retired items           {', '.join(report['retired']) or 'none'}")
    lines.append("")
    cost = report["context_cost"]
    lines.append(f"context cost            core {cost['core_bytes'] // 1024} KiB, "
                 f"largest feature {cost['largest_feature']} {cost['largest_feature_bytes'] // 1024} KiB, "
                 f"worst case {cost['worst_case_bytes'] // 1024} KiB per session")
    lines.append("")
    if report["release_blocking"]:
        lines.append("First-release MUST requirements with an unverifiable criterion:")
        lines.append("  " + ", ".join(report["release_blocking"]))
        lines.append("A MUST nobody can check is a MUST nobody can sign off.")
    else:
        lines.append("Every first-release MUST requirement has a verification for each of its criteria.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a spec set for completeness and for parity with the code.")
    parser.add_argument("--root", default=".", help="project root (default: current directory)")
    parser.add_argument("--specs", default="specs", help="spec directory, relative to root")
    parser.add_argument("--code", default=".", help="code root for parity checks, relative to root")
    parser.add_argument("--evidence", default="evidence", help="evidence directory, relative to root")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    parser.add_argument("--report", action="store_true", help="print a release-readiness summary as well")
    parser.add_argument("--max-evidence-age-days", type=int, default=DEFAULT_EVIDENCE_AGE_DAYS, help="how old a verified source may be before it must be re-checked")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    specs_root = root / args.specs
    if not specs_root.is_dir():
        print(f"spec directory not found: {specs_root}", file=sys.stderr)
        return 2

    linter = Linter(
        root=root,
        specs_root=specs_root,
        code_root=root / args.code,
        evidence_root=root / args.evidence,
        max_evidence_age_days=args.max_evidence_age_days,
    )
    findings = linter.run()
    report = build_report(linter) if args.report else None

    if args.json:
        payload: dict = {"findings": [f.__dict__ for f in findings]}
        if report is not None:
            payload["report"] = report
        print(json.dumps(payload, indent=2))
    else:
        if report is not None:
            print(render_report(report))
            print()
        for finding in findings:
            print(finding.render())
        print(f"\n{len(findings)} finding(s)." if findings else "\nSpecs complete: 0 findings.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
