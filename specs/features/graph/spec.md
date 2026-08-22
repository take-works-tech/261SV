---
status: draft
updated: 2026-08-21
---

# Feature: graph

## Users and purpose

- intended user: an analysis engineer comparing runs, who currently exports numbers to a spreadsheet
  and rebuilds the same figure every time the study changes
- job to be done: turn quantities into a figure that is presentable, reusable on the next study, and
  honest about where each series came from
- success condition: a figure that survives a parameter change, states its units and provenance, and
  can be applied to a different workspace without being rebuilt

## Out of scope

- a general-purpose plotting language - styles come from templates, adjusted rather than written
- computing new physical quantities inside the graph; derived values are computed by the analysis
  module and appear as quantities (XC-088)
- interactive statistical exploration beyond the recommendations described below

## Files and interfaces involved

- MOD-005 graph, MOD-004 analysis
- CT-005 graph definition, CT-007 selection, CT-008 library entry
- the right sidebar of [../../11_ui.md](../../11_ui.md)

## Requirements

### REQ-001 - A graph is a definition over quantities, with units and provenance
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-001: When a series is added, the system shall record which quantity it plots, in which unit, and
    with which provenance - declared, read from data, computed, or reference material (INV-013)
  - AC-002: While a series plots a quantity with no declared unit, the system shall label its axis with
    the undeclared marker rather than an assumed unit (XC-003)
  - AC-003: If two series are combined on one axis with incompatible units, then the system shall
    refuse and name both units
  - AC-004: When a graph is saved, the system shall store the definition rather than the plotted values

### REQ-002 - Manual construction over any available quantity
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-005: When the user builds a graph manually, the system shall offer every quantity of the
    selected cases, including computed quantities and values from an uploaded reference file
  - AC-006: Where a series is computed by an expression, the system shall show the expression beside
    the series and compute it in the analysis module, never in generated code (XC-080)
  - AC-007: If an expression cannot be evaluated for a case, then the system shall draw that case as no
    data and name the reason rather than dropping the series

### REQ-003 - Which cases a graph covers is a selection, not a guess
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-008: When no selection is given, the system shall plot the selected @Case and say so
  - AC-009: Where a selection is given, the system shall plot exactly the cases it resolves to and show
    which those are (CT-007)
  - AC-010: If a selection resolves to no cases, then the system shall state which condition emptied it
    rather than drawing an empty figure
  - AC-011: If user-written selection code fails or exceeds its limits, then the system shall select
    nothing and report the failure (XC-089)

### REQ-004 - Repeated studies are plotted deliberately
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-012: When cases form a repeated study, the system shall offer plotting each repeat separately or
    combining repeats, and shall state which was used
  - AC-013: If a case in the set lacks the plotted quantity, then the system shall draw it as no data
    and keep it in the legend, so the gap is visible

### REQ-005 - Recommendations are offered, never applied
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-014: When a @Case is loaded, the system shall be able to propose figures from the data alone -
    correlation, distribution, change over time - and shall name the signal behind each proposal
  - AC-015: Where a language model is configured, the system shall be able to propose figures with an
    inferred purpose, marked as inferred (XC-013)
  - AC-016: If a proposal is rejected, then the system shall not repeat it in the same session

### REQ-006 - Style comes from a library and travels
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-017: When a style is applied or a template is used to create a graph, the system shall take it
    from the library with its scope shown, and shall resolve as far as possible (XC-090)
  - AC-018: When a graph is saved as a @Template, the system shall allow creating an independent Graph
    from it in another @Workspace
  - AC-019: If creating a Graph from a @Template leaves series unresolved, then the system shall list
    them and draw them as no data

### REQ-007 - Output for documents
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-020: When a graph is exported, the system shall produce an image whose values match the figure
    on screen
  - AC-021: Where the data varies over time, the system shall be able to export an animation, stating
    the time mapping used

### REQ-008 - A summary statistic says how it was reduced
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-022: When a @Summary statistic is produced, the system shall record and display its reduction,
    its scope and its weighting, and shall default to volume-weighted for cell data and
    dual-volume-weighted for point data (INV-017)
  - AC-023: Where an unweighted arithmetic reduction is chosen, the system shall label it as unweighted
    everywhere it appears, including in exports and reports
  - AC-024: If a reduction is requested over a scope with no valid entries, then the system shall report
    it as unavailable rather than returning zero

### REQ-009 - Graphs are two-dimensional or three-dimensional
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-025: When a graph kind is chosen, the system shall offer three-dimensional kinds - surface,
    scatter and contour over two independent variables - alongside the two-dimensional ones
  - AC-026: Where a three-dimensional graph is exported, the system shall state the projection and the
    view direction used, because a surface read from one angle is a different claim from another

### REQ-010 - The graph display does not duplicate property editing with global Apply
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-080 (T1)
- acceptance:
  - AC-027: When an existing @Graph is displayed, its central heading shall not expose a persistent
    global `適用` button; current-item editing shall remain in the right property controls with shared
    Undo, while the material library shall retain its separately labelled non-drag `適用` action and
    recommendations shall remain proposals rather than applying automatically (XC-153)

## End-to-end verification

Build a graph over three cases of a parameter study with one case missing the quantity; confirm the
missing case is drawn as no data and stays in the legend. Apply a declared-unit change and confirm the
axis follows. Save as a template, create a new Graph from it in another workspace, and confirm the
unresolved list names the series it could not bind and later template edits do not change the created
Graph. Confirm the display heading has no global Apply button, property edits remain undoable, and the
material library still has its explicit non-drag Apply path. Export and confirm the exported values
match the screen.
