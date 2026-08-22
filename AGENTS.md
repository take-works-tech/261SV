# SOLVIA CAE Visualization

A desktop product that reads CAE result files and produces a self-contained, presentable deliverable -
geometry, the numbers with their units, graphs, commentary and a verdict in one file a recipient opens
with nothing installed. Desktop first and offline by default; a hosted service reaches the same core
over a different transport.

**The product's claim is trustworthy numbers.** A wrong value shown confidently is worse here than a
missing feature, and most of the rules below exist for that reason.

Specifications live in specs/. Read specs/README.md before changing behaviour: it indexes the
glossary, limits, contracts, invariants and the per-feature specs.

## Where things are

| Path | What it holds |
|---|---|
| `specs/` | the specification set - the source of truth for what this product does |
| `evidence/sources.md` | every source behind a Fixed value, with its tier and the date it was verified |
| `spike/` | measurements taken to settle open questions; `results.json` is the record |
| `src/` | the current walking-skeleton engine |
| `tests/` | executable product checks and repository-gate tests |
| `mockups/ui/` | the executable UI catalogue; design states only, never evidence of implemented behaviour |
| `validate/check_specs.py` | the spec linter; it defines what "complete" means |
| `.agents/skills/spec-authoring/` | the authoring procedure and the question bank |
| `archive/` | Git-ignored legacy and private local material; never a source of truth |

The walking-skeleton engine lives under `src/`. Earlier root-level implementations and tool settings
are preserved under `archive/legacy-root-2026-08-21/`; they are reference material, not a second
product source tree.

## Commands

```bash
python validate/check_specs.py            # the work list, in its own order
python validate/check_specs.py --report   # release readiness and context cost
python -m pytest tests                     # implementation and repository-gate tests
python spike/measure_export.py             # re-run the export measurement in a prepared spike env
```

`pytest` needs the engine environment (`python -m pip install -e ".[dev]"`, Python 3.12 or later).
Without VTK the reader tests skip and say so; CI sets `SIM_VIEWER_REQUIRE_VTK=1`, which turns that
skip into a failure - a suite allowed to skip where it matters reports success for tests that never
ran. Every gate in `validate/` runs in `.github/workflows/ci.yml`, and
`validate/check_gates_wired.py` fails if one of them is invoked by nothing.

## Rules that are not obvious from the files

- **A number and a picture come from different code paths.** Reported values are computed on the full
  dataset in the canonical frame; display geometry is decimated, tessellated and scaled, and measuring
  it produces a number that is wrong in a way that looks right (INV-001, INV-009).
- **Units never come from the file.** CAE formats do not carry them reliably, so a unit is declared by
  the user or the value is shown as undeclared. Nothing in this product infers one (XC-003).
- **Failing loudly beats a plausible default.** Missing values stay missing and say so; no substituted
  zero, no previous value, no interpolated neighbour (XC-001).
- **Offline is a feature, not a fallback.** With the network blocked, everything not explicitly marked
  network-dependent completes, and nothing is attempted (INV-007).
- **A spec change and the code it describes ship together.** The linter compares Fixed values against
  the code, so either order alone leaves the project red (spec model 6.5).

## How a change is made here

- **Fix the cause, not the symptom.** When something breaks, find the structure that allowed it and
  change that. A patch at the point of failure leaves the same defect available everywhere else, and
  the next occurrence looks unrelated. Recent examples, all fixed at the cause: a hook path relative to
  the shell's cwd locked a whole session out (anchored, not retried); `--muted` named two roles so
  `bg-muted` rendered dark (the name was split, not the one visible site patched); a version pinned in
  a manifest was invisible to every gate (a gate was added, not the one file corrected).
- **Plan the whole shape before writing any of it.** A feature's `plan.md` and `tasks.md` exist for
  this: decide the structure, then implement it. Discovering the structure while typing produces one
  that fits the order things were written in.
- **Aim at the best available answer, not the first workable one** — and when two are defensible,
  `specs/04_principles.md` is the tie-breaker rather than preference. Where a Bounded item has no
  principle to judge it by, it is Delegated wearing a different word.
- Structure and duplication are not advice here, they are gates. The vertical (capability) and
  horizontal (layer) split, and the blast radius of a change, are in
  [specs/01_boundaries.md](specs/01_boundaries.md) and checked by `check_boundaries.py`. One
  definition per value - constants, and CSS tokens with their two layers (XC-187) - is checked by
  `check_constant_duplication.py`; one implementation per shared component by `check_commands.py`.

## Working agreements

- **One remote, named** (XC-186): `take-works-tech/261SV`, private. Pushing
  there is authorised; any other repository is not. Force-push, hard reset, rebase and history rewriting
  are refused - the record of a correction is part of what this project ships.
- Edits stay inside this directory.
- Evidence is first-hand or it is not evidence. Vendor marketing is tier T3 and cannot justify a Fixed
  value; the linter enforces it.
- When a measurement contradicts a recorded conclusion, correct the conclusion **and keep the record of
  the correction** - a decision fixed for a reason that turned out false gets reversed later for the
  wrong cause.
