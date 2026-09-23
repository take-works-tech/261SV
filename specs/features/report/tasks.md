---
status: draft
updated: 2026-09-23
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
- done: 2026-08-25. The coverage is attached to the **value**, not to the block, because AC-004 is
  about a number computed over part of the data rather than about a figure drawn from it. A value
  carrying `PARTIAL_DATASET` **refuses to be put in a document without its coverage**: a caveat saying
  "part of the dataset was missing" with no figures behind it is a warning nobody can act on, because
  the reader cannot tell whether one part of fifteen was absent or twelve were.
  Which values are partial, and what each covered, is answerable from the document, and the mechanical
  summary carries it as something to know before reading rather than as one more line among the
  figures.
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
- done: 2026-08-25, `src/engine/report/summary.py`. A report is produced with no language model and
  no network, carrying counts, the extremes **named with their labels** - "the maximum is 240 MPa" is a
  number without a subject - and what a reader must know to act on the numbers.
  The mechanical summary is **not the degraded version** of a generated one: AC-013 makes it the part
  that is always there, and generated commentary is what may be added to it. It is marked as mechanical,
  because a reader who cannot tell which sentences a model wrote has to treat all of them as if one did.
  It composes no prose, and the test that matters is the negative one: none of the language E-071
  enumerates - superlatives, subjective assessments, ambiguous adverbs - can appear, because nothing
  here assembles a sentence. It states quantities and stops. A clean report gets **no** concerns rather
  than a manufactured caution to look thorough.
  AC-012 holds by construction rather than by restraint: the summary is derived from the document's own
  rows and has nothing else it could say.
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
- done: 2026-09-20 (XC-274, XC-275). `report.export` draws a view block from the definition the
  document holds - the one the interface writes, camera and `partVisibility` included - and the
  area's preview shows the frame the screen drew from it, saying the document's figure is drawn
  at export from the same definition

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

### TASK-045 - The report area edits the document's report
- satisfies: AC-007, AC-022
- depends_on: TASK-002, TASK-022
- done_when: with an engine connected the area reads the document's report back before it writes
  it, the block list a person edits reaches the document, the mandatory content is shown from
  `report.provenance` or its refusal is shown as the item that blocks the export, and the export is
  one control whose answer is shown
- done: 2026-09-20 (XC-275, CT-003 3.6.0). `report.update` and `report.get` are registered; the
  store keeps the document's report, adopts it by the dataset's name and makes it once - every
  export used to create one and the second was refused as a name already held. What is not built:
  drafting, style, templates, renaming, the preflight; the canvas shows engine answers only and
  says the rest is computed at export
### TASK-046 - The exported document opens where it arrives
- satisfies: AC-036
- depends_on: TASK-045
- done_when: the exported document and a probe carrying every kind of inline dependency open the
  same from a local file, from a file marked as downloaded and through a network share, in the
  browsers present
- done: 2026-09-21 (XC-295, #255). Measured with Edge 153.0.4234.48 and Chrome 153.0.8010.52 (E-218):
  an inline classic script, an inline module script, inline style and a data-URI image run, apply
  and load the three ways, and this build's document renders the identical DOM the three ways.
  `tests/test_exported_document_opens.py` keeps it, skipping by name where no browser or share is
  present and printing the versions it used. A mail client's preview pane, SmartScreen and a
  double-click from a folder are not measured and are said so; the browser range is #256.
### TASK-047 - The exported document prints as pages
- satisfies: AC-037
- depends_on: TASK-046
- done_when: printed to PDF from the browsers present, a page-break block adds a sheet, a figure sits
  whole with its heading, a table row and each trust section stay whole, the sheet is A4, and the
  two browsers agree on the pages of one document
- done: 2026-09-21 (XC-296, #267). Measured with Edge 153.0.4234.48 and Chrome 153.0.8010.52
  (E-219): before the rules a heading was left at the foot of a sheet with its figure on the next;
  with them the five measured documents print to the same sheets in both browsers, on A4.
  `tests/test_exported_document_prints.py` reads the sheets back from the PDF. The provenance list
  items were written without a list around them and now are in one. Not measured: a physical
  printer and the browser's own print dialogue.
### TASK-048 - The application's print action is the exported document
- satisfies: AC-037
- depends_on: TASK-047
- done_when: printing from the application exports the report to the directory the shell owns
  (XC-262) and prints that file, and the screen's own print stylesheet says the screen is not the
  document rather than printing the workbench

### TASK-049 - What a table's number left out
- satisfies: AC-045
- depends_on: TASK-047
- done_when: the value table of a holed field says beside each number how many entries it left
  out, and no cell is a blank, a zero for a missing value or "nan"
- done: 2026-09-22 (XC-303, #215). `caveat_text` renders the missing-values caveat with its
  count in the HTML document and its text form, from the count the value carries. Proven by
  `tests/test_missing_values.py::TestAGraphAndADeliverable::test_the_deliverable_s_table_says_what_a_number_left_out_and_states_an_absence`.

### TASK-050 - The document names the browsers it was verified in
- satisfies: AC-046
- depends_on: TASK-047
- done_when: the exported document's footer names each browser the gate opened and printed it in
  with the oldest version measured and says that older versions and other browsers are unverified;
  the gate fails where a browser it measured is older than the version named and warns where it
  measured one the list does not name; the probe reports every CSS feature the stylesheet relies
  on, per browser
- done: 2026-09-23 (XC-309, E-228, #256). `VERIFIED_BROWSERS` in `src/engine/report/html.py` is the
  one place, printed by the footer; `tests/browsers.py` holds what the two browser tests share -
  Edge and Chrome through their command line, Firefox through geckodriver's WebDriver endpoint
  where a machine has both; the probe in `tests/test_exported_document_opens.py` reports each
  feature and the data-URI face, and `TestTheDocumentClaimsWhatWasMeasured` holds the footer to the
  measurement. Measured here with Edge 153 and Chrome 153, and on the runner with Edge 152 - which
  the gate refused against a claim of 153, so the claim is 152; Firefox's first pass is a
  measurement said in the runner's summary, not yet a claim.
