"""Instruction-context budget gate for sim-viewer.

The harness loads project memory into every turn. The generator measured this once, at the moment it
wrote the environment; **this gate measures it forever after**, which is the only version that helps.
An environment is small on the day it is generated and large two hundred days later, and nothing in
between charges it for the difference.

Two layers, two ceilings:

  ALWAYS      paid on every turn of every session
                - CLAUDE.md, **and whatever it pulls in with `@path` imports**
                - AGENTS.md, loaded once per session by the other agent runtime
                - .claude/rules/*.md WITHOUT `paths:` frontmatter
                - .claude/output-styles/*.md   (appended to the system prompt)
  CONDITIONAL paid only when a matching file is touched
                - .claude/rules/*.md WITH `paths:` frontmatter

A one-line `CLAUDE.md` reading `@AGENTS.md` is a common and sensible shape, and it is exactly where a
naive gate reads two tokens and reports a tiny always-layer while several thousand tokens load every
turn. Following the import is not a refinement; without it the number is wrong in the direction that
matters.

**Both are charged.** Charging only the first would make `paths:` a way to hide growth rather than a
trade: move a rule out of ALWAYS and the number falls, while the corpus the agent must eventually read
keeps growing. Path-scoping is a real decision with a real cost - a scoped rule does not reach a
subagent, and does not survive a compaction - so it is bounded rather than free.

Reported but not charged, because they are machine-local and absent on CI:
  CLAUDE.local.md, and any per-project auto-memory index.

Token estimate: tokens ~= ascii_chars / 4 + non_ascii_chars. Deliberately crude and deliberately
pessimistic for non-ASCII text; a gate that under-counts is a gate that passes the day it should not.

Exit code: 0 within budget, 1 over budget. Stdlib only.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

ALWAYS_CEILING_TOKENS = 6000
CONDITIONAL_CEILING_TOKENS = 2000

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_PATHS_KEY = re.compile(r"^paths:\s*$", re.MULTILINE)

# Reported for context, never charged: written on one machine, absent on another, so charging them
# would fail somebody else's unrelated change.
UNCHARGED = ("CLAUDE.local.md",)


def estimate_tokens(text: str) -> int:
    """Rough token count. One token per non-ASCII character, one per four ASCII characters."""
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    return ascii_chars // 4 + (len(text) - ascii_chars)


def is_path_scoped(text: str) -> bool:
    """True when the file carries `paths:` frontmatter, so the harness loads it conditionally."""
    match = _FRONTMATTER.match(text)
    return bool(match and _PATHS_KEY.search(match.group(1)))


def collect() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    always: dict[str, str] = {}
    conditional: dict[str, str] = {}
    uncharged: dict[str, str] = {}

    seen: set[str] = set()

    def charge(name: str) -> None:
        """Add a file once, following any `@path` import it declares."""
        if name in seen:
            return
        candidate = ROOT / name
        if not candidate.is_file():
            return
        seen.add(name)
        text = candidate.read_text(encoding="utf-8")
        always[name] = text
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("@") and not stripped.startswith("@@"):
                charge(stripped[1:].strip())

    charge("CLAUDE.md")
    charge("AGENTS.md")

    for rule in sorted((ROOT / ".claude" / "rules").glob("*.md")):
        text = rule.read_text(encoding="utf-8")
        target = conditional if is_path_scoped(text) else always
        target[f".claude/rules/{rule.name}"] = text

    for style in sorted((ROOT / ".claude" / "output-styles").glob("*.md")):
        always[f".claude/output-styles/{style.name}"] = style.read_text(encoding="utf-8")

    for name in UNCHARGED:
        candidate = ROOT / name
        if candidate.is_file():
            uncharged[name] = candidate.read_text(encoding="utf-8")

    return always, conditional, uncharged


def report(label: str, files: dict[str, str], ceiling: int | None) -> int:
    total = 0
    print(f"{label}:")
    for name, text in sorted(files.items(), key=lambda item: -estimate_tokens(item[1])):
        tokens = estimate_tokens(text)
        total += tokens
        print(f"  {tokens:6d}  {name}")
    if ceiling is None:
        print(f"  {total:6d}  TOTAL (reported, not charged)")
    else:
        verdict = "OVER" if total > ceiling else "ok"
        print(f"  {total:6d}  TOTAL of {ceiling}  [{verdict}]")
    print()
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--always-ceiling", type=int, default=ALWAYS_CEILING_TOKENS)
    parser.add_argument("--conditional-ceiling", type=int, default=CONDITIONAL_CEILING_TOKENS)
    args = parser.parse_args()

    always, conditional, uncharged = collect()
    always_total = report("ALWAYS (every turn)", always, args.always_ceiling)
    conditional_total = report("CONDITIONAL (when a matching file is touched)", conditional, args.conditional_ceiling)
    if uncharged:
        report("Machine-local, reported only", uncharged, None)

    failures = []
    if always_total > args.always_ceiling:
        failures.append(f"always-injected {always_total} tokens exceeds {args.always_ceiling}")
    if conditional_total > args.conditional_ceiling:
        failures.append(f"path-scoped {conditional_total} tokens exceeds {args.conditional_ceiling}")

    if failures:
        for line in failures:
            print(f"OVER BUDGET: {line}", file=sys.stderr)
        print(
            "Move the body of a rule into an on-demand skill and leave a pointer, or delete it. "
            "Path-scoping moves cost between the two layers; it does not remove it.",
            file=sys.stderr,
        )
        return 1

    print("Instruction context within budget.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
