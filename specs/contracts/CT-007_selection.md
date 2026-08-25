---
status: draft
updated: 2026-08-25
---

# Contract: case selection

### CT-007 - Selection
- purpose: which @Case a graph draws, a report covers, or a template is applied to. Written
  declaratively by default, and readable by a person who did not write it
- schema: schema/CT-007.json
- version: 1.0.0
- strictness: unknown fields are **rejected** - a selection carrying a condition the engine does not
  understand would silently select the wrong cases, which is worse than refusing
- compatibility: an operator added to the language has a defined meaning from the version it appears in;
  older engines refuse rather than approximate
- migration: a stored selection is upgraded on open, like the document that holds it (CT-001)
- decidedness: Fixed
- basis: E-001 (T1)

## The declarative form

A selection is a tree of conditions over things the product already knows: tags, names, variables,
declared units, time steps, the hierarchy, and the support level of the source format. It has
comparison, membership, and the three connectives - and, or, not. **It has no arithmetic and no
function calls**, because a selection that can compute is an evaluator, and the reason this is
declarative is that it must not be one (XC-080).

```
{ "all": [ { "tag": "converged" },
           { "variable": "inlet_velocity", "unit": "m/s", "greaterThan": 10 },
           { "not": { "name": { "startsWith": "draft_" } } } ] }
```

Every condition names its unit where it compares a quantity. A comparison against a variable whose unit
is undeclared is refused, not silently compared as a bare number (XC-003). The unit may be composed -
`m/s` above is a product of two known symbols (XC-244) - and the two sides are converted before they are
compared, so `12 m/s` satisfies `greaterThan 10000` in `mm/s`.

## The code form, when a user opts in

A user may write Python instead (XC-089). It receives **metadata only** - case identifiers, names,
tags, variable values with their units and provenance, time-step counts - and returns identifiers. It
does not receive datasets, cannot open files, has no network, and runs with a time and memory limit in
a separate process.

- **A model never writes this code.** The assistant may propose a declarative selection; it may not
  propose or edit code (XC-080)
- **The code cannot produce a displayed number.** It chooses which cases appear; the values shown come
  from the analysis module in every case
- **A failure is a refusal, not an empty result.** Code that raises, times out, or returns identifiers
  that do not exist selects nothing and says why - an empty graph with no explanation would read as
  "no data" when it means "your code broke"

## Why both forms exist

The declarative form covers what can be said about tags, names and variables, which is most of what a
parameter study needs, and it is readable by the next person and by the assistant. The code form
exists because real studies have selection rules that are genuinely conditional, and refusing them
would push the user back to the manual work this product is meant to remove.

The line between them is not convenience but consequence: **the choice of what to show may be
arbitrary; the values shown may not be.**

## Selecting by state

A selection may name @Case state - unresolved, unloaded, loading, loaded, partial, failed (GL-039). A
state is what the product observed; a tag is what a person decided, and the two are kept apart so that
"every case that failed" is answerable without anyone having tagged them.
