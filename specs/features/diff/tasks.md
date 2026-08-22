---
status: draft
updated: 2026-08-20
---

# Tasks: diff

### TASK-001 - Same-mesh difference
- satisfies: AC-001
- depends_on: ingest/TASK-001
- done_when: the difference keeps the association of its sources and matches a hand-computed value

### TASK-002 - Identifier matching
- satisfies: AC-002
- depends_on: TASK-001
- done_when: locations match by source identifier where present, not by array position

### TASK-003 - Unit compatibility
- satisfies: AC-003
- depends_on: TASK-001
- done_when: differing declared units are refused with both named

### TASK-004 - Missing propagates
- satisfies: AC-004
- depends_on: TASK-001
- done_when: a missing value on either side yields missing, never zero

### TASK-005 - Diff as a field
- satisfies: AC-009
- depends_on: TASK-001
- done_when: the result is a field with unit and provenance naming both cases and the method

### TASK-006 - Relative difference
- satisfies: AC-010
- depends_on: TASK-005
- done_when: the reference must be named, and a zero reference reports undefined rather than infinite

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
