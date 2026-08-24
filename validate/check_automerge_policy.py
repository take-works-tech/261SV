"""The automatic-merge workflow still says what the decision says it says.

XC-218 lets a workflow merge to `main` with nobody reading the change, until the first working
prototype. On this plan there is no branch protection and no merge queue to hold the line (E-129,
OPEN-020), so the conditions written into `.github/workflows/auto-merge.yml` **are** the line. A
condition quietly dropped from that file fails nothing on its own: the workflow keeps merging, just on
less. Nothing else in the repository would notice.

So this gate reads the workflow and checks that every condition the decision names is still there, that
each one leaves without merging rather than guessing, that the switch is still a repository variable
rather than a file, and that the agent still has no merge authority of its own. It also checks the two
ends of the time box against each other: the workflow present while the decision is superseded, or
absent while it is active, are both the period ending in one place and not the other.

The direction matters: this reads the *implementation* against the *record*, so removing a guard means
editing two files, one of which is the decision that says why the guard is there.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "auto-merge.yml"
DECISIONS = ROOT / "specs" / "08_decisions.md"
SETTINGS = ROOT / ".claude" / "settings.json"
WORKFLOW_DIR = ROOT / ".github" / "workflows"

# What the decision promises, and the text in the workflow that keeps the promise.
REQUIRED_CONDITIONS: list[tuple[str, str]] = [
    ("a switch that is a repository variable, not a file", "vars.AUTO_MERGE_ENABLED == 'true'"),
    ("the triggering run concluded success", "github.event.workflow_run.conclusion == 'success'"),
    ("the run was for a pull request", '"$TRIGGERING_EVENT" = "pull_request"'),
    ("the head is not on a fork", '"$HEAD_REPO" = "$REPO"'),
    ("exactly one open pull request for this commit", '"$pr_count" = "1"'),
    ("the pull request is open", 'jq -r .state)" = "OPEN"'),
    ("the pull request is not a draft", ".isDraft"),
    ("the base branch is main", ".baseRefName"),
    ("the head is still the commit that was checked", '.headRefOid)" = "$SHA"'),
    ("a per-pull-request brake", "grep -qx 'no-auto-merge'"),
    ("git-level state is not dirty, blocked or undecided", "DIRTY|BLOCKED|UNKNOWN"),
    ("every check run on the commit, not only the triggering workflow", "commits/$SHA/check-runs"),
    ("this job's own check is excluded from that query", 'own="$OWN_CHECK_NAME"'),
    ("a commit with no other checks is refused", "nothing verified it"),
    ("a check still running stops the merge", '$2 != "completed"'),
    ("only success, skipped and neutral count as green", '$3 != "success" && $3 != "skipped" && $3 != "neutral"'),
    ("the whole file list is visible before anything is decided from it", '"$file_count" -lt 100'),
    # No longer a refusal (XC-238): every path merges, including this file and this check. What is
    # still required is that a change to the merging machinery is **written to the log**, because
    # nobody sees it beforehand and the log is the only place it can be found afterwards.
    ("a change to the merge machinery is recorded in the log", "merging unread"),
    ("the merge is a squash", "--squash"),
]

FAIL_CLOSED = 'stop() { echo "auto-merge stopped: $1"; exit 0; }'
# Every workflow that can put a check on a pull request has to be waited for, or the merge happens
# while one of them is still running.
OWN_WORKFLOW = "auto-merge"


def workflow_names() -> list[str]:
    names = []
    for path in sorted(WORKFLOW_DIR.glob("*.yml")):
        match = re.search(r"^name:\s*(.+?)\s*$", path.read_text(encoding="utf-8"), re.M)
        if match:
            names.append(match.group(1).strip("'\""))
    return names


def main() -> int:
    findings: list[str] = []
    decisions = DECISIONS.read_text(encoding="utf-8")
    match = re.search(r"^### XC-218 .*?^- status: (\w+)", decisions, re.S | re.M)
    status = match.group(1) if match else None

    if status is None:
        findings.append("XC-218 is not in specs/08_decisions.md, so nothing states why this workflow may merge")

    if not WORKFLOW.exists():
        if status == "active":
            findings.append(f"{WORKFLOW.relative_to(ROOT)} is missing while XC-218 is active")
        elif status is None:
            pass
        else:
            print("auto-merge is not configured and XC-218 is not active: the two ends agree.")
            return 0
    else:
        if status not in (None, "active"):
            findings.append(
                f"XC-218 is '{status}' but {WORKFLOW.relative_to(ROOT)} is still here - the period "
                "ended in the record and not in the repository"
            )
        workflow = WORKFLOW.read_text(encoding="utf-8")

        if FAIL_CLOSED not in workflow:
            findings.append("the fail-closed `stop` helper is not the recorded one")
        for promise, needle in REQUIRED_CONDITIONS:
            if needle not in workflow:
                findings.append(f"the workflow no longer checks {promise} (looked for {needle!r})")

        # Every workflow but this one must be waited on.
        expected = [name for name in workflow_names() if name != OWN_WORKFLOW]
        listed = re.search(r"workflows:\s*\[(.*?)\]", workflow)
        actual = [item.strip().strip("'\"") for item in listed.group(1).split(",")] if listed else []
        for name in expected:
            if name not in actual:
                findings.append(f"workflow '{name}' can check a pull request and is not waited for")
        for name in actual:
            if name not in expected:
                findings.append(f"'{name}' is waited for and is not a workflow in this repository")

        # The agent opens pull requests; it does not land them.
        permissions = json.loads(SETTINGS.read_text(encoding="utf-8")).get("permissions", {})
        if not any(rule.startswith("Bash(gh pr merge") for rule in permissions.get("deny", [])):
            findings.append(
                "`gh pr merge` is not denied in .claude/settings.json - with no branch protection, an "
                "agent that can merge is the whole gate removed"
            )

        # The hole is accepted, so it is written down where the next reader will meet it.
        if "merges with **nobody reading it**" not in workflow:
            findings.append("the workflow header no longer states what merges without being read")
        if "TIME-LIMITED" not in workflow:
            findings.append("the workflow header no longer says the measure is time-limited")

    if findings:
        for finding in findings:
            print(f"[auto-merge policy] {finding}")
        print(f"\n{len(findings)} finding(s).")
        return 1
    print(f"auto-merge policy holds: {len(REQUIRED_CONDITIONS)} conditions, fail-closed, variable switch, agent denied merge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
