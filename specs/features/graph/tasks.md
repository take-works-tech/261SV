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
- done: 2026-08-25, `src/domain_core/selection.py`. CT-007's declarative tree resolves to a case set,
  the set size and the number considered are reported, and **an empty result names the condition that
  emptied it** - narrowed one condition at a time, so the answer is the step that did it rather than an
  inference from a whole tree that came back with nothing. An empty graph with no explanation reads as
  "no data" when it means "your filter excluded everything", and those are different problems.
  Two refusals rather than silences. An **unrecognised condition** is refused, because ignoring one is
  how a filter quietly becomes "everything", and the refusal happens before any case is examined so a
  bad selection does not work until the data changes. A **comparison with no unit on both sides** is
  refused (XC-003); when both sides have one they are converted before comparing, so 12 m/s satisfies
  `greaterThan 10000` in mm/s.
  It lives in MOD-001 rather than in MOD-005 or MOD-007: a selection reads case metadata only and
  depends on no toolkit, and the graph module cannot import a service module without pointing a
  dependency upward. That also makes it reachable by pipeline/TASK-009 and by templates.
  This needed XC-244 first - CT-007's own worked example compares against `m/s`, and the unit registry
  refused every composed symbol, so the contract's example could not be evaluated.
### TASK-005 - Default selection is the selected case
- satisfies: AC-008
- depends_on: TASK-004
- done_when: with no selection given, the selected case is plotted and stated
- done: 2026-08-25. With no selection written, the cases already selected are used **and the
  result says so**: a graph that plotted the selected case silently looks identical to one that was told
  to plot it.
  A selection of nothing at all chooses **nothing**, not everything. "No selection" and "select all" are
  different intentions, and the expensive direction is the one where a study silently covers every case
  in the workspace.
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
- done: 2026-08-25, `src/engine/graph/series.py`. Every quantity the selected cases hold is offered,
  together with computed ones and values from an uploaded reference file - a builder that offered only
  what came out of the solver would make the other two second-class, and they are the ones a comparison
  usually needs.
  A quantity that only some cases have is offered **once**. Offering it per case would put the same
  name on the list three times, and the cases that lack it become no-data points when it is plotted
  rather than a reason not to offer it.
### TASK-008 - Expressions computed in the analysis module
- satisfies: AC-006
- depends_on: TASK-007
- done_when: an expression series shows its expression and is computed by the analysis module, never in
  the graph layer
- done: 2026-08-25. The expression is evaluated by MOD-004 and this module records what came
  back (AC-006, XC-080, XC-088). A graph layer that computed would be a second place where numbers are
  produced, and the two would disagree the day one of them was fixed. The expression travels with the
  series, which is INV-013's last clause.
### TASK-009 - Expression failure drawn as no data
- satisfies: AC-007
- depends_on: TASK-008
- done_when: a case where the expression fails is drawn as no data with the reason, and the series stays
- done: 2026-08-25. A case where the expression fails is **that case's** no-data with the
  evaluator's own reason, and the series stays: one that vanished would take the other cases' answers
  with it. The reason is the evaluator's rather than a summary of it, because that is what tells
  somebody whether the expression is wrong or the case is.
  No-data is `None`, never zero. A missing value arriving as zero is the failure XC-001 exists to
  prevent, so there is no numeric stand-in here to be mistaken for a measurement.
### TASK-010 - Repeated studies
- satisfies: AC-012
- depends_on: TASK-004
- done_when: per-repeat and combined plotting are both available and the choice is stated
- done: 2026-08-25. Both are available and **which was used is stated** (AC-012). Neither is a
  default applied silently: one drifting repeat is visible when repeats are separated and hidden when
  they are combined, and a product that picked would be choosing which of those somebody saw.
  Combining does **not** average. An average is a number nobody asked for, and it would appear on the
  axis as though it had been measured. Separating without a rule for which case is which repeat is
  refused - grouping by similar names would be a grouping the user never stated.
### TASK-011 - Missing quantity kept visible
- satisfies: AC-013
- depends_on: TASK-010
- done_when: a case lacking the quantity is drawn as no data and remains in the legend
- done: 2026-08-25. The case is drawn as no data and stays in the points and in the legend,
  and a series with nothing plotted at all still appears there marked as such. Dropping it would make
  the figure look complete - two cases plotted where three were asked for, and nothing on the page
  saying which is gone.
  What is missing is answerable from the figure rather than collected while drawing, so a renderer that
  never ran gives the same answer.
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
