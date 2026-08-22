"""Refuse the operations this project has decided it does not do.

Three rules, all stated in AGENTS.md, all easy to break by habit rather than by intent:

1. **Edits stay inside this directory.** Another project on this machine is not this project's
   business, and a verifier that wandered into a neighbouring repository already produced one wrong
   conclusion here.
2. **One remote, named.** XC-181 authorised publication to exactly one repository. A second remote -
   a fork, a mistyped owner, a personal scratch repo - is how a product plan and its market analysis
   reach an audience nobody chose.
3. **History is append-only.** Force-push, hard reset, rebase and filter-branch destroy the record of
   a correction, and this project's whole working agreement is that a correction is part of the
   deliverable.

Advisory rules in a document are followed until someone is in a hurry. These are cheap to enforce and
expensive to get wrong, which is the whole test for whether a rule belongs in a hook.

**Path resolution is anchored to the hook file, never to the shell's working directory.** An earlier
version was invoked as `python .claude/hooks/local_only_guard.py`; one command run from a subdirectory
left the shell there, the path stopped resolving, and Python's exit code 2 for a missing file is the
same code that means *block this tool call* - so the guard denied every edit and every command in the
session, including the one that would repair it. The settings file now passes an absolute path built
from `$CLAUDE_PROJECT_DIR`, and this module refuses to guess a root it cannot derive from its own
location.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# The one repository this project publishes to (XC-181). Written here rather than read from
# `git remote` so that a wrong remote is refused instead of being adopted as the definition.
AUTHORISED_REMOTE = "take-works-tech/261SV"

FORBIDDEN_COMMANDS = (
    (
        re.compile(r"\bgit\s+push\b.*(?:--force\b|--force-with-lease\b|(?<!\w)-f(?!\w))"),
        "history is append-only here; a force-push destroys the record of a correction",
    ),
    (
        re.compile(r"\bgit\s+(?:filter-branch|filter-repo)\b"),
        "rewriting history erases the corrections this project deliberately keeps",
    ),
    (
        re.compile(r"\bgit\s+reset\s+--hard\b"),
        "a hard reset discards work that nothing else recorded",
    ),
    (
        re.compile(r"\bgh\s+(?:repo|release)\s+delete\b"),
        "deleting a published repository or release is not an operation this project performs",
    ),
)


def blocked_path(raw: str) -> str | None:
    if not raw:
        return None
    try:
        target = Path(raw).resolve()
    except (OSError, ValueError):
        return None
    try:
        target.relative_to(ROOT)
    except ValueError:
        return f"{target} is outside this project; edits stay inside {ROOT.name}"
    return None


# A GitHub repository, in the three forms a remote is ever written in. The host is consumed by the
# prefix rather than matched as an owner: a naive `owner/repo` pattern reads `github.com/take-works-tech`
# out of a correct URL and refuses the one remote that is allowed.
_GITHUB_URL = re.compile(
    r"(?:https?://(?:www\.)?github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"(?P<repo>[\w.-]+/[\w.-]+?)(?:\.git)?(?=[\s'\"]|$)"
)
# `gh repo create owner/name`, where the repository is a bare argument rather than a URL.
_GH_REPO_ARG = re.compile(r"\bgh\s+repo\s+create\s+(?:-\S+\s+|--\S+(?:[= ]\S+)?\s+)*(?P<repo>[\w.-]+/[\w.-]+)")

_REMOTE_COMMAND = re.compile(r"\bgit\s+(?:push|remote\s+(?:add|set-url))\b|\bgh\s+repo\s+create\b")


def blocked_remote(command: str) -> str | None:
    """A push or remote-configuring command naming a repository other than the authorised one.

    Matched on the whole command text rather than on a parsed argument list: the point is to catch a
    mistyped owner or a second repository slipped into a compound command, and both appear as text
    wherever they appear at all.

    A bare `git push`, `git push origin` or `git push -u origin main` names no repository, so the
    configured remote decides - and that remote was itself checked here when it was added.
    """
    if not _REMOTE_COMMAND.search(command):
        return None
    named = {match.group("repo") for match in _GITHUB_URL.finditer(command)}
    named |= {match.group("repo") for match in _GH_REPO_ARG.finditer(command)}
    foreign = sorted(name for name in named if name != AUTHORISED_REMOTE)
    if foreign:
        return (
            f"names {', '.join(foreign)}; this project publishes to {AUTHORISED_REMOTE} "
            "and nowhere else (XC-181)"
        )
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if tool in ("Write", "Edit", "NotebookEdit"):
        reason = blocked_path(str(tool_input.get("file_path", "")))
        if reason:
            print(reason, file=sys.stderr)
            return 2

    if tool in ("Bash", "PowerShell"):
        command = str(tool_input.get("command", ""))
        for pattern, reason in FORBIDDEN_COMMANDS:
            if pattern.search(command):
                print(f"refused: {reason}", file=sys.stderr)
                return 2
        reason = blocked_remote(command)
        if reason:
            print(f"refused: {reason}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
