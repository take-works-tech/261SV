# Contributing

Read `AGENTS.md` first — it is short, and it is what both Claude Code and Codex are given every
session. This file adds only what a human needs that an agent already has.

## Getting the environment

```bash
python -m venv .venv                       # Python 3.12 or later; pyproject.toml requires it
.venv/Scripts/activate                     # Windows;  source .venv/bin/activate elsewhere
python -m pip install -e ".[dev]"          # engine dependencies, pinned
git config core.hooksPath .githooks        # once per clone - see below
python -m pytest tests                     # the suite, including the repository gates
python validate/check_specs.py             # the work list, in its own order
```

**`core.hooksPath` is not optional here.** The hook is versioned so it travels with the repository,
but git ignores it until each clone is pointed at it, and this is the only guard that runs in a plain
terminal: it refuses a push that rewrites published history and a push whose gates are red. GitHub
refuses neither, because branch protection is unavailable on this plan (OPEN-020). A test fails if you
skip this line.

Without VTK the reader tests skip and say why. That is a reasonable answer on a laptop and not one in
CI, which sets `SIM_VIEWER_REQUIRE_VTK=1` and turns the skip into a failure. A suite allowed to skip
where it matters reports success for tests that never ran.

The mockup catalogue is a separate toolchain:

```bash
cd mockups/ui && npm ci && npm run typecheck && npm run dev
```

It is **design states only, and never evidence of implemented behaviour**. A screen existing there says
what the product should look like, not that anything behind it works.

## The one rule that surprises people

**A specification change and the code it describes ship in the same pull request.** Not before it in a
separate commit, and not after. `validate/check_specs.py` compares a Fixed value against the code, so a
spec-only change leaves the project red until the code lands, and a code-only change leaves it red
until the spec catches up. Red is correct in both cases — the two disagree, and something is
unfinished. Putting them together is what keeps the red state brief rather than normal, and a linter
that is normally red is one everyone learns to ignore.

## What the gates check, and what they cannot

Seven run in CI. Each prints what it could **not** check, because silence from a gate reads as coverage:

| Gate | Checks |
|---|---|
| `check_specs.py` | the twenty-two checks of the specification model; `--report` for release readiness and context cost |
| `check_boundaries.py` | module ownership, layer direction, declared dependencies |
| `check_commands.py` | the operation catalogue against its schema and its prose references |
| `check_constant_duplication.py` | the same constant defined in two files |
| `check_context_budget.py` | the instruction layer charged on every turn, and the path-scoped layer |
| `check_dependency_pins.py` | declared versions against the manifests that pin them, both directions |
| `check_gates_wired.py` | that every validator here is invoked by something that runs it |

What none of them can see is a **semantic contradiction between two prose statements**. Two specs that
disagree in words remain a job for a reader. Saying so is better than implying the gate set is
complete.

## What decides whether a pull request can merge

The three CI jobs — `repository gates`, `tests`, `mockup catalogue typecheck` — and nothing else.
The automated Claude review does not run on a pull request (XC-188): with no token it failed on every
one, and a check that is red for a reason unrelated to the change teaches everyone to read red as
normal. It still runs by hand:

```bash
gh workflow run claude-code-review.yml -f pull_request_number=<n>
```

**Nothing enforces this.** Branch protection is unavailable on this plan (OPEN-020), so a red pull
request can still be merged by anyone who chooses to. The checks tell you; they do not stop you.

## Evidence

A number without a source is not a finding. Every Fixed value cites an entry in `evidence/sources.md`
with its tier and the date it was verified, and tier T3 — vendor marketing, unattributed figures, blog
summaries — may never justify a Fixed value. The linter enforces the tier rule; it cannot enforce
honesty about which of *measured*, *estimated* and *assumed* a number is. All three are legitimate.
Presenting one as another is not.

If available sources cannot settle a question, that is a result to report, not a gap to fill with a
plausible number. Open it as a tracked question instead.

## When a measurement contradicts a decision

Correct the decision **and keep the record of the correction**. A decision fixed for a reason that
turned out false gets reversed later for the wrong cause. `specs/08_decisions.md` marks a superseded
decision rather than deleting it, and several entries carry an explicit `correction:` line saying what
was believed before and why it was wrong. Those lines are part of the deliverable.

This is also why history here is append-only: force-push, hard reset and rebase are refused by
`.claude/hooks/local_only_guard.py`.

**That refusal is client-side only, and you should know it.** Branch protection is not available for a
private repository on a free personal account — measured 2026-08-22, both the rulesets API and the
classic branch-protection API answer HTTP 403 with "Upgrade to GitHub Pro or make this repository
public". So CI runs on every push and pull request and reports honestly, and it cannot block a merge;
the hook runs only inside an agent session on this machine and is silent in a plain terminal. Rebase
merges are disabled at the repository level, which the free plan does allow. The gap is tracked as
OPEN-020, with the ruleset already written and rejected only by the plan.

## Publishing

This repository publishes to `take-works-tech/202604-sim-analysis-visualization`, private, and nowhere
else (XC-186). The guard enforces the remote by name, and `tests/test_environment_gates.py` proves the
guard can still fail — a guard nobody has watched fail is a guard nobody should trust.

### If a push is rejected only when it touches `.github/workflows/`

```
! [remote rejected] main -> main (refusing to allow a Personal Access Token to create or
  update workflow .github/workflows/... without `workflow` scope)
```

The cause is not the repository. **A `GITHUB_TOKEN` in the environment overrides whatever `gh auth
login` stored**, and a personal access token issued with only `repo` scope cannot write a workflow
file. Everything else keeps working, so the mismatch stays invisible until the day a workflow changes
— which is why it reads as a sudden permissions failure rather than as a setting somebody chose.

Check which credential is actually in use, and what it can do:

```bash
gh auth status          # the account marked "Active account: true" is the one git will use
```

If the active row says `(GITHUB_TOKEN)` and its scopes lack `workflow`, the fix is to stop injecting
it, not to weaken the push. `gh auth refresh` cannot help: it will not modify a token supplied through
the environment. On Windows the variable is usually at User scope:

```powershell
[Environment]::SetEnvironmentVariable('GITHUB_TOKEN', $null, 'User')   # then open a new terminal
```

`gh` then falls back to the credential it stored itself, which `gh auth login` gives the `workflow`
and `read:org` scopes this repository needs. For a single command without changing anything:
`env -u GITHUB_TOKEN git push`.
