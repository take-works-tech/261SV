---
status: draft
updated: 2026-08-20
---

# Tasks: diff

### TASK-001 - Same-mesh difference
- satisfies: AC-001
- depends_on: ingest/TASK-001
- done_when: the difference keeps the association of its sources and matches a hand-computed value
- done: 2026-08-24, `src/engine/analysis/difference.py` - MOD-004's first code. The association of
  the sources is kept, and two different associations are refused: subtracting a cell value from a point
  value subtracts two different places (INV-003).
### TASK-002 - Identifier matching
- satisfies: AC-002
- depends_on: TASK-001
- done_when: locations match by source identifier where present, not by array position
- done: 2026-08-24. Where both cases carry identifiers, locations match by them and the result
  keeps the **left** case's order, because the diff is a field on the left case's geometry.
  A test shows what position-matching would have given on the same data: the two answers differ, which
  is the defect that looks right for as long as nobody remeshes. Array position is the same location
  only if both files were written the same way, and two runs of the same solver on the same mesh do not
  guarantee that.
### TASK-003 - Unit compatibility
- satisfies: AC-003
- depends_on: TASK-001
- done_when: differing declared units are refused with both named
- done: 2026-08-24. Both units are named and **nothing is converted** - a conversion here is one
  nobody asked for, inside an operation whose entire output is a difference.
  One distinction the task did not name: two **undeclared** units are not a mismatch. They are two
  fields nobody has declared, and their difference is as undeclared as they are.
### TASK-004 - Missing propagates
- satisfies: AC-004
- depends_on: TASK-001
- done_when: a missing value on either side yields missing, never zero
- done: 2026-08-24. Missing on either side is missing in the result, and a location present in one
  case and not the other is missing rather than zero - zero is a value an engineer reads as "these
  agree" (INV-011). The count of unmatched locations travels with the result, so it can be shown rather
  than inferred from a colour map full of gaps.
### TASK-005 - Diff as a field
- satisfies: AC-009
- depends_on: TASK-001
- done_when: the result is a field with unit and provenance naming both cases and the method
- done: 2026-08-24. The result is a @Field with the source unit and a provenance line naming both
  cases and the method - and the method is carried because it changes what the number means (GL-011).
### TASK-006 - Relative difference
- satisfies: AC-010
- depends_on: TASK-005
- done_when: the reference must be named, and a zero reference reports undefined rather than infinite
- done: 2026-08-24. The reference must be one of the two cases and is never chosen here: a relative
  difference against an unnamed denominator is a percentage nobody can reproduce.
  A zero reference reports **undefined**, not infinite. An infinity in a field propagates into a colour
  scale and takes the whole picture with it, and the count of undefined locations is reported beside the
  result.
### TASK-007 - Cross-mesh direction is explicit
- satisfies: AC-005
- depends_on: TASK-005
- done_when: no direction is chosen without the user naming the target dataset

### TASK-008 - Cross-mesh disclosure
- satisfies: AC-006
- depends_on: TASK-007
- done_when: direction, outside-point count and round-trip error travel with the result

### TASK-009 - Outside points are missing
- satisfies: AC-007
- depends_on: TASK-007
- done_when: a point outside the source is missing, never extrapolated

### TASK-010 - The report says what is in the number
- satisfies: AC-008
- depends_on: TASK-008, report/TASK-024
- done_when: a cross-mesh diff in a report states that physical difference and interpolation are both
  present in the value
