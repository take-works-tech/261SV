---
status: draft
updated: 2026-08-25
---

# Tasks: report generation

### TASK-001 - Document skeleton with values as text
- satisfies: AC-002
- depends_on: workspace/TASK-001
- done_when: an exported document contains every displayed value as readable text and opens with the
  network disabled
- done: 2026-08-25, `src/engine/report/document.py`. Every displayed value appears as readable text
  with its unit, its provenance and where it is in the source's own words - `GlobalNodeId 1003`, never
  an array index. REQ-001's own note is why: the free export path dropped a text annotation and a point
  label **with no warning** while the scalar bar survived, and a document whose values live only inside
  the 3D content stops being readable the moment the viewer fails.
  A value that is absent says why rather than leaving a blank cell (XC-001) - a blank is a value the
  reader supplies an explanation for, usually a wrong one.
  The document opens with the network disabled, checked **on the produced document** rather than
  trusted of the writers, and the check is proven able to fail against a document containing one
  external reference.
  Nothing here produces a number: the rows are handed in, because MOD-004 makes values and a report
  layer that computed would be a second place a value comes from (INV-001). No HTML is written yet -
  the document model is what the writers will agree on, so the same values reach the interactive
  document and the office formats without either being the definition of what a report contains.
### TASK-002 - Provenance block
- satisfies: AC-007
- depends_on: TASK-001
- done_when: the document records the @Workspace, the @Case, source files with modification times,
  declared units and the product version
- done: 2026-08-25. Workspace, cases, source files **with their modification times**, declared
  units and the product version. The time is the half that matters: without it the block says which
  files, and a reader cannot tell a delivered document from one whose inputs have moved since (INV-027).
  It is **mandatory and refuses to be partly filled**: a missing workspace, case list or product version
  raises and blocks the export, rather than writing a document with a gap where its provenance should be
  - which is a document somebody sends. Having no source files at all is **stated** rather than omitted,
  because an empty list and an absent list read the same on a page and only one of them means "this
  report read no file".
  The product version is handed in. Nothing here can know which build produced the document, so nothing
  here guesses.
### TASK-003 - Undeclared units in the document
- satisfies: AC-008
- depends_on: TASK-001
- done_when: a field with no declared unit appears with the undeclared marker and never with a guessed
  unit
- done: 2026-08-25. A value with no declared unit carries the marker where the unit would be, and
  which values those are is answerable from the document without reading it. The marker is **one string
  in one place** (`domain_core.reported_value.UNDECLARED_MARKER`): an axis label, a table cell and a
  report line cannot disagree about the same absence.
  Two defects found and fixed while writing this. The marker had been defined **three times** - the
  duplication gate caught two of them and the third was a different spelling inside the evaluator. And
  a genuinely **dimensionless** quantity was being reported as undeclared, which is the confusion
  `reported_value` explicitly warns about: it makes every safety factor look like a stress whose unit
  went missing. A ratio of two declared lengths now reads as `1` and a product of two bare numbers still
  reads as undeclared.
### TASK-004 - Embedded geometry and its viewer
- satisfies: AC-001
- depends_on: TASK-001
- done_when: the document shows the @View rotatable in a current browser with no installation and no
  network

### TASK-005 - Reduction for the report, marked
- satisfies: AC-003
- depends_on: TASK-004, ingest/TASK-015
- done_when: a dataset above the report budget (LIM-006) embeds a reduced representation, marked as
  reduced, while reported numbers stay computed on the full data

### TASK-006 - Partial coverage stated in the document
- satisfies: AC-004
- depends_on: TASK-002
- done_when: a report built on a partial @Dataset states the coverage every derived number was computed
  over

### TASK-007 - Annotations survive, or the export stops
- satisfies: AC-014
- depends_on: TASK-004
- done_when: annotations, labels and scales are present in the document, and anything that cannot be
  represented is named before the file is written rather than dropped (E-048)

### TASK-008 - Font subsetting for non-Latin text
- satisfies: AC-015
- depends_on: TASK-001
- done_when: a document containing Japanese and Chinese renders on a machine with only Latin fonts, and
  the embedded subset covers exactly the characters used

### TASK-009 - Unrenderable characters reported
- satisfies: AC-016
- depends_on: TASK-008
- done_when: a character outside the embedded subset is named with its element rather than written as
  an empty box

### TASK-010 - Office export from the same content
- satisfies: AC-005
- depends_on: TASK-001
- done_when: PowerPoint, Word, Excel and CSV output carry the same values and figures as the document,
  asserted field by field

### TASK-011 - Substitution stated where a format cannot carry an element
- satisfies: AC-006
- depends_on: TASK-010
- done_when: an element replaced by a static image is stated as substituted in the output

### TASK-012 - Art style applied to output
- satisfies: AC-009
- depends_on: TASK-001
- done_when: fonts, colour maps and figure styling from the selected @Art style appear in the document
  and in exported images

### TASK-013 - Missing style assets named
- satisfies: AC-010
- depends_on: TASK-012
- done_when: a missing asset falls back to the default style and is named rather than silently replaced

### TASK-014 - Mechanical summary without a model
- satisfies: AC-013
- depends_on: TASK-002
- done_when: a report is produced offline with no language model configured, carrying the mechanical
  summary only

### TASK-015 - Generated commentary marked and grounded
- satisfies: AC-011
- depends_on: TASK-014, assistant/TASK-008
- done_when: each generated passage is marked as generated and names the values it was derived from

### TASK-016 - Ungrounded statements omitted
- satisfies: AC-012
- depends_on: TASK-015
- done_when: a statement about a value not present in the @Dataset is omitted from the document rather
  than published

### TASK-017 - Commentary depth and its cost
- satisfies: AC-017
- depends_on: TASK-015
- done_when: a depth is chosen, and what will be sent and its approximate cost are stated before
  anything leaves the machine

### TASK-018 - A direction shapes the words, never the values
- satisfies: AC-018
- depends_on: TASK-017
- done_when: a written direction changes what is discussed, and a test asserts no value in the document
  changes with it

### TASK-019 - Budget exhaustion stops rather than degrades
- satisfies: AC-019
- depends_on: TASK-017
- done_when: exceeding the configured budget stops and reports what was produced

### TASK-020 - Cited documents are marked as such
- satisfies: AC-020
- depends_on: TASK-016
- done_when: a statement drawn from reference material names the document and is marked

### TASK-021 - Data beats documents, visibly
- satisfies: AC-021
- depends_on: TASK-020
- done_when: where a document contradicts the data, the data value is published and the disagreement
  stated (XC-013)

### TASK-022 - Blocks render from view definitions
- satisfies: AC-022
- depends_on: TASK-002
- done_when: a block naming a view renders through the same definition the interface uses

### TASK-023 - Video blocks
- satisfies: AC-023
- depends_on: TASK-022
- done_when: a video block is produced from a camera path and states its time mapping

### TASK-024 - The statement checker
- satisfies: AC-024
- depends_on: TASK-015
- done_when: each category of 14_reporting_standards.md is detected, with a test case per category

### TASK-025 - Rewrite once, then omit
- satisfies: AC-025
- depends_on: TASK-024
- done_when: a failing statement is retried once and dropped, and the omission count reaches the document

### TASK-026 - Guarded vocabulary
- satisfies: AC-026
- depends_on: TASK-024
- done_when: each of the five terms is published only when its precondition is present in the case

### TASK-027 - Unquantified error is stated
- satisfies: AC-027
- depends_on: TASK-026
- done_when: a single-mesh case produces the statement rather than silence

### TASK-028 - Citations by identifier
- satisfies: AC-028
- depends_on: TASK-020
- done_when: generation receives a list and returns identifiers; free-text references cannot enter

### TASK-029 - Unsupported statements omitted
- satisfies: AC-029
- depends_on: TASK-028
- done_when: a statement with no matching document does not reach the document

### TASK-030 - Retrieval recorded with the citation
- satisfies: AC-030
- depends_on: TASK-028
- done_when: address, date and retrieved text are stored and rendered

### TASK-031 - The limitations section
- satisfies: AC-031
- depends_on: TASK-001
- done_when: every produced report contains one, with a default sentence when nothing else applies

### TASK-032 - Comparison sentences
- satisfies: AC-032
- depends_on: TASK-003
- done_when: magnitude, direction and reference are produced from the computed comparison

### TASK-033 - Below-tolerance differences
- satisfies: AC-033
- depends_on: TASK-032
- done_when: a difference under the tolerance reports as not distinguishable

### TASK-034 - The sample template set
- satisfies: AC-034
- depends_on: TASK-012
- done_when: five generic report templates ship and each creates an independent Report in a workspace
  without requiring template edits

### TASK-035 - Sample licence inventory
- satisfies: AC-035
- depends_on: TASK-034
- done_when: every shipped asset's terms are recorded and checked at build time, placeholders otherwise

### TASK-036 - Output location and run folders
- satisfies: AC-036
- depends_on: TASK-001
- done_when: artefacts land in a timestamped run folder and no earlier run is overwritten

### TASK-037 - Collision refused before the run
- satisfies: AC-037
- depends_on: TASK-036
- done_when: a colliding pattern stops the run at the start, naming the pattern

### TASK-038 - Colour-map note
- satisfies: AC-038
- depends_on: TASK-002
- done_when: a non-perceptually-uniform map produces a note in the report

### TASK-039 - Cross-workspace sources
- satisfies: AC-039
- depends_on: TASK-001
- done_when: several workspaces resolve into one document with per-value workspace provenance

### TASK-040 - Missing sources named
- satisfies: AC-040
- depends_on: TASK-039
- done_when: an unavailable workspace is named and the rest of the report is produced

### TASK-041 - Plain text and Markdown kinds
- satisfies: AC-041
- depends_on: TASK-009
- done_when: one definition produces every listed kind

### TASK-042 - Substitutions stated
- satisfies: AC-042
- depends_on: TASK-041
- done_when: a block that cannot be carried states what replaced it

### TASK-043 - Deliverable records its inputs
- satisfies: AC-043
- depends_on: TASK-001
- done_when: content identity of each input and the workspace version are written into the export

### TASK-044 - Stale deliverables identifiable
- satisfies: AC-044
- depends_on: TASK-043
- done_when: a changed input lets the product name the deliverable as produced from changed data
