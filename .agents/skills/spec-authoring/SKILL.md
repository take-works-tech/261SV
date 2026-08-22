---
name: spec-authoring
description: Author or complete this project's specification set - interview, research, propose, confirm - until the spec linter reports zero findings. Use when starting a new project or feature, when a spec is missing information, when check_specs.py reports findings, or when asked what still has to be decided.
---

# Spec authoring

Fill `specs/` until `python validate/check_specs.py` reports zero findings. The linter defines
"complete"; your own sense that it looks finished does not.

Read `specs/README.md` (from the project root) for the file layout and the item format before writing anything.

## The loop

1. **Detect** - run the linter. Its findings are the work list, in its order.
2. **Classify** - for each finding ask: does this value appear in two or more places? is it externally
   observable? does getting it wrong deliver a wrong result to the user? Any yes means **Fixed**.
   Otherwise it is **Bounded** (a constraint with a criterion) or **Delegated** (free).
3. **Fixed** - research it, then come back with options, a recommendation, the basis and its tier, and
   **what would have to be true for a different option to win**. Confirm with the human before writing.
4. **Bounded or Delegated** - do not ask. Decide it, judging by `specs/04_principles.md`, and record one
   line of rationale.
5. Repeat until the linter is green.

## Rules

- **Searching is unattended; adopting is not.** Reading sources needs no permission. Promoting a
  finding to a Fixed value does.
- **Stop and ask regardless of tier** when the value is safety-, regulatory- or certification-relevant,
  when researching it would disclose confidential information to a third party, or when the source
  costs money. A correct-looking value is worse than an open question in those three cases.
- **A proposal is not an answer.** An Open becomes Fixed only after a human confirms it.
- **Batch proposals per stage**, about seven at a time, decisions that constrain other decisions first.
  Never mix stages in one batch.
- **Never invent a number.** If sources cannot settle it, say so and record it as Open with a tracking ID.
- An estimate is a labelled calculation, not evidence: record the method, the inputs and the assumptions.

## Stages

Work in this order; each stage answers what the next one depends on.

| Stage | What it settles | Skip when |
|---|---|---|
| S0 Framing | capacity, market, domain leverage, definition of success, review batch size | never |
| S1 Viability | is this worth building, and which variant | not a new product or business |
| S2 Product spec | glossary, users and scope, contracts, invariants, failure semantics, acceptance | never |
| S3 Technical | architecture, canonical basis, technology, licensing, delivery, dev environment, UI | never |
| S4 Gate | linter green, every Fixed value traceable | never |

The questions for each stage are in `question-bank.md`, next to this file. **Ask all of them.** An
unasked question becomes an assumption, and an assumption is how a wrong value enters a spec with
nobody deciding it. Every question offers "undecided" and "you decide", which is what keeps the
interview answerable - not asking fewer questions.

Treat the two escapes differently: **undecided** means research it and come back to confirm;
**you decide** means decide it and do not come back.
