---
status: draft
updated: 2026-08-20
---

# Specifications

Index. The always-loaded layer points here and nowhere else; every body below is opened on demand.

| File | Holds | Category |
|---|---|---|
| [00_glossary.md](00_glossary.md) | terms, units, coordinate frames | 1 |
| [01_boundaries.md](01_boundaries.md) | modules and dependency direction | 7 |
| [02_invariants.md](02_invariants.md) | what must always be true | 4 |
| [03_failure_policy.md](03_failure_policy.md) | default failure semantics | 5 |
| [04_principles.md](04_principles.md) | product trade-off ordering | 2b |
| [05_limits.md](05_limits.md) | capacity limits | 8 |
| [06_external.md](06_external.md) | external systems and failure modes | 9 |
| [07_cross_cutting.md](07_cross_cutting.md) | errors, i18n, a11y, audit, update, licence, security | 10 |
| [08_decisions.md](08_decisions.md) | project-level decisions and what they ruled out | - |
| [09_technology.md](09_technology.md) | stack, dependencies with licence and support horizon, dev environment | - |
| [10_delivery.md](10_delivery.md) | installer, update and rollback, environments, monitoring, backup | - |
| [11_ui.md](11_ui.md) | screens, transitions, shared components, conventions | - |
| [12_business_model.md](12_business_model.md) | what is sold, to whom, at what price, and why they pay | - |
| [13_scripting.md](13_scripting.md) | the Python surface, the naming rule, and the expression language | - |
| [14_reporting_standards.md](14_reporting_standards.md) | what a generated report may say, and in what language | - |
| [15_derived_quantities.md](15_derived_quantities.md) | derived quantities, component frames, result axes, identifiers | - |
| [contracts/](contracts/) | data contracts, one file each | 3 |
| [verification/plan.md](verification/plan.md) | how each acceptance criterion is verified | 6 |
| [features/](features/) | one directory per feature | 2, 6 |
| [../evidence/sources.md](../evidence/sources.md) | sources and tiers behind every Fixed value | - |
| [../evidence/](../evidence/) | the other evidence files: pipeline and scripting, reporting standards, CAE conventions, result kinds | - |

## Gates

Seven run in the build, and each says what it could **not** check rather than letting silence read as
coverage:

| Gate | Checks |
|---|---|
| `validate/check_specs.py` | the twenty-two checks of the specification model, plus `--report` for release readiness |
| `validate/check_boundaries.py` | module ownership, layer direction and declared dependencies (01_boundaries.md) |
| `validate/check_commands.py` | the operation catalogue against its schema, prose references, and shared-component uniqueness (XC-127) |
| `validate/check_constant_duplication.py` | the same constant defined in two files: contradictions, and copies that will become contradictions |
| `validate/check_context_budget.py` | the instruction layer paid on every turn - CLAUDE.md and what it imports, AGENTS.md, rules, output styles - and the path-scoped layer, both charged |
| `validate/check_dependency_pins.py` | declared dependency versions against the manifests that pin them, in both directions - check 7 compares `SYMBOL = literal` in source files, and a pin inside a TOML array matches nothing it looks at (XC-185) |
| `validate/check_gates_wired.py` | every validator here is invoked by something that runs it |

## Format

Every file starts with a metadata block:

```
---
status: draft | active | superseded
updated: 2026-08-19
---
```

Every item is a heading plus attribute lines. The linter reads this shape, so it is not decoration:

```
### REQ-001 - Operator starts a run
- priority: MUST            # MUST | SHOULD | COULD  (does the product fail without it)
- phase: r1                 # r1 | later             (is it in the first release)
- decidedness: Fixed        # Fixed | Bounded | Delegated | Open
- basis: E-001 (T1)         # required when Fixed; tier T3 may never justify a Fixed value
- acceptance:
  - AC-001: When the operator presses Start, the system shall begin the run within 1 s
  - AC-002: If the device is disconnected, then the system shall abort and report the reason
```

Rules the linter enforces: every requirement has at least one acceptance criterion, a priority and a
phase; every feature has at least one `If ... then ...` criterion; every Fixed item cites evidence of
tier T1 or T2; every Open item names a tracking ID; glossary references written `@Term` resolve; links
and IDs resolve; a Fixed value with a `source_of_truth` matches the code and exists in one place only.

**`TBD` marks every slot that still needs an answer.** The linter counts them, so a freshly installed
skeleton reports the whole work list rather than looking nearly finished. Replace the token, not just
the prose around it.

Run it: `python validate/check_specs.py`
