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
- done: 2026-08-24, `src/engine/analysis/resample.py` and `cross_mesh_difference`. The basis must
  name one of the two cases and is never chosen here: the two directions give different numbers, and a
  product that picks one has made an engineering decision on the user's behalf (AC-005).
  Cell data is refused rather than resampled as points - treating a cell value as a point value asserts
  it was at the centroid, which nothing said.
### TASK-008 - Cross-mesh disclosure
- satisfies: AC-006
- depends_on: TASK-007
- done_when: direction, outside-point count and round-trip error travel with the result
- done: 2026-08-24. All four of XC-038's disclosures travel with the result: direction, outside
  count **and proportion**, round-trip error in the field's own unit, and the statement that three
  contributions are in the number.
  The round-trip error is **measured, not estimated** - the field is carried onto the target and back,
  and compared with what was there before. A point that fell outside on either hop is excluded rather
  than counted as zero error, which would make a barely-overlapping pair of meshes look like a perfect
  one.
### TASK-009 - Outside points are missing
- satisfies: AC-007
- depends_on: TASK-007
- done_when: a point outside the source is missing, never extrapolated
- done: 2026-08-24, and this is where the measurement mattered. `vtkResampleWithDataSet` marks a
  point outside the source in `vtkValidPointMask` **and writes 0.0 into the field there** (E-140). A
  product returning the array as it comes hands an engineer a page of zeros where its mesh did not
  reach, and zero in a difference reads as "these agree".
  That is the behaviour E-056 records Tecplot having, arriving here as the toolkit's default with the
  mask available and unapplied. The mask is applied and those points are missing.
### TASK-010 - The report says what is in the number
- satisfies: AC-008
- depends_on: TASK-008, report/TASK-024
- done_when: a cross-mesh diff in a report states that physical difference and interpolation are both
  present in the value
- done: 2026-08-24. `disclosure()` is one sentence a report carries **with** the number rather than
  as a footnote: the value is physical difference plus discretisation plus interpolation, and a reader
  who is not told that reads it as the first alone.
  It also carries XC-038's fifth rule, which the task list does not name: where the difference is no
  larger than the round-trip error that produced it, the region is **undetermined**. A difference
  smaller than its own interpolation is not a small difference - it is a number the method cannot
  resolve, and shading it faintly says "almost no change here" when the honest statement is "this method
  cannot tell".