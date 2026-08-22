# Contributing

Read `AGENTS.md` first — it is short, and it is what both Claude Code and Codex are given every
session. This file adds only what a human needs that an agent already has.

## Getting the environment

```bash
python -m venv .venv                       # Python 3.12 or later; pyproject.toml requires it
.venv/Scripts/activate                     # Windows;  source .venv/bin/activate elsewhere
python -m pip install -e ".[dev]"          # engine dependencies, pinned
python -m pytest tests                     # 105 tests
python validate/check_specs.py             # the work list, in its own order
```

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
