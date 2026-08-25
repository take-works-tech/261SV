---
status: draft
updated: 2026-08-25
---

# Tasks: graph

### TASK-001 - Graph definition with units and provenance
- satisfies: AC-001
- depends_on: workspace/TASK-001
- done_when: each series records its quantity, unit and provenance, and the definition rather than the
  values is what is saved
- done: 2026-08-25, `src/engine/graph/definition.py`. Each series records its quantity, its unit and
  its provenance, and **the definition is what is saved** - asserted by sweeping the stored document for
  anything that looks like cached values, because a figure that kept its numbers would still draw after
  the study changed, showing last week's answer under this week's title.
  There are four provenances and no fifth for "unknown" (INV-013). A value whose origin nobody recorded
  is not a fifth kind of origin - it is a value this product should not be plotting, so there is nowhere
  to put it. A computed series without its expression is refused at construction for the same reason.
### TASK-002 - Undeclared units on axes
- satisfies: AC-002
- depends_on: TASK-001
- done_when: a series with no declared unit labels its axis with the undeclared marker
- done: 2026-08-25. An axis with nothing declared on it says so, in one spelling held in one
  place so a graph, a table and a report cannot disagree about how the same absence is written.
  An axis that **does** carry declared units is labelled with the internal unit of the quantity rather
  than with whichever symbol the first series happened to use - MPa and kPa on one axis are plotted as
  Pa, and labelling it "MPa" would be a number shown in one unit and labelled with another.
### TASK-003 - Incompatible units refused
- satisfies: AC-003
- depends_on: TASK-002
- done_when: combining incompatible units on one axis is refused with both units named
- done: 2026-08-25, naming both. Two refusals, and the second is the one that looks harmless.
  Different dimensions is the obvious one - a length beside a time. **A declared unit beside an
  undeclared one** is the quiet one: the figure reads as a comparison, and nothing ever said the
  undeclared series was in the same unit (XC-003). All-undeclared together is allowed, because AC-002
  requires that case to be drawable with the marker on its axis.
  A refused addition leaves the definition exactly as it was, so a graph is never briefly holding a
  combination the product would refuse to draw.
### TASK-004 - Declarative selection
- satisfies: AC-009
- depends_on: TASK-001
- done_when: a selection resolves to a case set, the set is shown, and an empty result names the
  condition that emptied it

### TASK-005 - Default selection is the selected case
- satisfies: AC-008
- depends_on: TASK-004
- done_when: with no selection given, the selected case is plotted and stated

### TASK-006 - Selection code, isolated
- satisfies: AC-011
- depends_on: TASK-004
- done_when: user-written selection runs in a separate process with metadata only, and a failure or
  limit breach selects nothing and reports why

### TASK-007 - Manual construction over quantities
- satisfies: AC-005
- depends_on: TASK-001
- done_when: every quantity of the selected cases is offered, including computed ones and
  reference-file values

### TASK-008 - Expressions computed in the analysis module
- satisfies: AC-006
- depends_on: TASK-007
- done_when: an expression series shows its expression and is computed by the analysis module, never in
  the graph layer

### TASK-009 - Expression failure drawn as no data
- satisfies: AC-007
- depends_on: TASK-008
- done_when: a case where the expression fails is drawn as no data with the reason, and the series stays

### TASK-010 - Repeated studies
- satisfies: AC-012
- depends_on: TASK-004
- done_when: per-repeat and combined plotting are both available and the choice is stated

### TASK-011 - Missing quantity kept visible
- satisfies: AC-013
- depends_on: TASK-010
- done_when: a case lacking the quantity is drawn as no data and remains in the legend

### TASK-012 - Styles and templates from the library
- satisfies: AC-017
- depends_on: TASK-001
- done_when: styles apply from any scope, partially where they resolve, with the scope shown

### TASK-013 - Templates across workspaces
- satisfies: AC-018
- depends_on: TASK-012
- done_when: a graph template creates an independent Graph in another workspace, listing unresolved
  series and drawing them as no data

### TASK-014 - Export matching the screen
- satisfies: AC-020
- depends_on: TASK-001
- done_when: exported values match the figure on screen, asserted by test

### TASK-015 - Animation export
- satisfies: AC-021
- depends_on: TASK-014
- done_when: a time-varying graph exports an animation stating its time mapping

### TASK-016 - Mechanical recommendations
- satisfies: AC-014
- depends_on: TASK-007
- done_when: proposals are produced from the data alone and each names the signal behind it

### TASK-017 - Model-assisted recommendations
- satisfies: AC-015
- depends_on: TASK-016
- done_when: proposals with an inferred purpose are marked as inferred, and a rejected proposal is not
  repeated in the session

### TASK-018 - Weighted reductions
- satisfies: AC-022
- depends_on: TASK-001
- done_when: reduction, scope and weighting are recorded and displayed, with the weighted default

### TASK-019 - Unweighted is labelled
- satisfies: AC-023
- depends_on: TASK-018
- done_when: an unweighted reduction carries its label into tables, exports and reports

### TASK-020 - Empty scopes
- satisfies: AC-024
- depends_on: TASK-018
- done_when: a scope with no valid entries reports unavailable rather than zero

### TASK-021 - Three-dimensional graph kinds
- satisfies: AC-025
- depends_on: TASK-001
- done_when: surface, scatter and contour over two independent variables are available

### TASK-022 - Projection stated on 3D export
- satisfies: AC-026
- depends_on: TASK-021
- done_when: an exported 3D graph names its projection and view direction

### TASK-023 - Remove the Graph display Apply button
- satisfies: AC-027
- depends_on: TASK-001
- done_when: the central Graph heading contains no global Apply action, right property edits use shared
  Undo, material-library Apply remains available as the non-drag resource path, and recommendations do
  not auto-apply
