---
status: draft
updated: 2026-08-19
---

# Failure policy

The project-wide default for what happens when something goes wrong. A feature may override it and
must say so explicitly. In a product whose value is trustworthy numbers, silence here is the
expensive kind: an agent optimising for "code that runs" substitutes a plausible value, and a wrong
number reaches a customer looking like a measurement.

### XC-001 - Default failure semantics
- statement: a computation that cannot produce a correct value returns a missing-value marker that is
  distinguishable from a real result at every layer, and the interface shows it as missing - not as
  zero, not as the previous value, not as an interpolated neighbour
- never: substitute a value that cannot be told apart from a measurement; swallow the error; clamp a
  result into range to keep a picture looking right
- user_visible: the affected element is drawn in the missing-data style, and the reason is available
  on the element itself rather than only in a log
- decidedness: Fixed
- basis: E-001 (T1)

### XC-002 - Partial results
- statement: a partially loaded @Dataset may be used, and every derived number states the coverage it
  was computed over; a @Report built on partial data carries that statement in the document
- never: report a maximum, mean or integral over a subset while presenting it as the whole
- decidedness: Fixed
- basis: E-001 (T1)

### XC-003 - Undeclared units
- statement: a @Field with no declared unit is displayed and exported as a bare number with an explicit
  "unit not declared" marker; it is never labelled with a guessed unit
- never: infer units from magnitude, field name, or the solver that wrote the file
- decidedness: Fixed
- basis: E-001 (T1)

### XC-004 - Renderer unavailable
- statement: when the selected renderer backend cannot run on this machine, the product says which one
  failed and why, and offers a backend that can; it does not silently substitute one
- rationale: a substituted backend can change shading, tessellation and colour interpolation, which
  changes what the user believes they measured
- decidedness: Fixed
- basis: E-001 (T1)

### XC-005 - Assistant failure
- statement: when the assistant cannot complete an instruction, it reports what it did not do and
  leaves the @Workspace unchanged; a partially applied instruction is rolled back
- never: guess the missing half of an instruction, or apply the part it understood and stay quiet
  about the rest
- decidedness: Fixed
- basis: E-001 (T1)

### XC-006 - Retry and timeout
- statement: which operations retry, how often, with what backoff, and what the user sees after the
  last attempt
- decidedness: Bounded

### XC-007 - Workspace file damage
- statement: a @Workspace file that fails to load is never overwritten; the product opens what it can,
  reports what it could not, and keeps the original untouched
- decidedness: Fixed
- basis: E-001 (T1)

### XC-008 - Material dependency or compilation failure
- statement: if a required CT-011 input, result field/component/association/position/unit, resource,
  graph node or renderer feature cannot resolve, the affected Material Binding remains editable but
  enters `failed`; its entire target is drawn with reserved diagnostic magenta, its ordinary legend is
  suppressed and CT-010 names every cause. Missing entries inside an otherwise resolved result mark
  only those entries through the validity attribute
- never: retain previous successful pixels, substitute zero or another field, use an undeclared
  Material Asset or renderer fallback, or present diagnostic magenta as a successful export
- user_visible: the viewport, Outliner and Materials properties mark the failed target and provide the
  exact requirement and expected type; presentable export refuses until it is repaired (XC-175)
- decidedness: Fixed
- basis: E-001 (T1)

A save path that destroys the only copy of a week of work is the failure users never forgive, and the
one that costs nothing to prevent.
