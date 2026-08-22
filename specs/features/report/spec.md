---
status: draft
updated: 2026-08-20
---

# Feature: report generation

## Users and purpose

- intended user: an analysis engineer who must hand a result to a customer, a manager or a reviewer,
  and who currently rebuilds that document by hand from screenshots
- job to be done: turn what is already on screen into a deliverable someone else can open, read and
  interrogate, without re-deriving anything
- success condition: the recipient opens one file, rotates the model, reads the numbers, and needs no
  installation and no explanation of where the numbers came from

## Out of scope

- editing the report after export inside this product (the office formats exist for that)
- hosting or sharing the report on the vendor's behalf in the first release
- writing engineering conclusions the user has not approved
- any layout engine of our own: office output goes through the formats' own libraries

## Files and interfaces involved

- the @Report definition and its schema (CT-006), including sources, output kinds, commentary settings and what the deliverable was produced from
- the library entry a report @Template is stored as (CT-008), and the failure shape an export reports in (CT-010)

- MOD-006 report, MOD-003 visualization, MOD-005 graph
- the art style of GL-013 and the shared components of [../../11_ui.md](../../11_ui.md)

## Requirements

### REQ-001 - An interactive 3D HTML report is the primary output
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1), E-048 (T1), E-051 (T1)
- note: measured here, the free export path produced 34.4 MB in 21.4 seconds for a 1.13 million point
  surface, and **the text annotation and point label added to that scene were absent from the exported
  file with no warning**, while the scalar bar survived. The same geometry compresses to 16.1 MB, so
  roughly half that file is serialisation overhead. AC-002, AC-003 and AC-014 exist because of those
  measurements, not as general good practice
- acceptance:
  - AC-001: When the user exports a report, the system shall produce a single HTML file that opens in a
    current browser with no installation and no network access, showing the @View rotatable
  - AC-002: When the report is produced, the system shall include every number shown as text, so the
    document is readable without interacting with the 3D content
  - AC-014: If an annotation, label or scale cannot be represented in the exported document, then the
    system shall say so before writing the file rather than omitting it silently
  - AC-015: When a report contains characters outside the basic Latin set, the system shall embed a
    subset of a licensed font covering them, so the document renders identically on a machine with no
    such font installed
  - AC-016: If a character cannot be rendered with the fonts available, then the system shall report
    which characters and in which element, rather than writing a document containing empty boxes
  - AC-003: If the @Dataset is too large for the interactive budget, then the system shall include a
    reduced representation, mark it as reduced in the document, and keep every reported number computed
    from the full data
  - AC-004: If any exported number came from a partial @Dataset, then the report shall state the
    coverage it was computed over

### REQ-002 - Office formats carry the same content
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-005: When the user exports to PowerPoint, Word, Excel or CSV, the system shall produce the same
    values and the same figures as the HTML report for the same @Case
  - AC-006: If a format cannot represent an element, then the system shall substitute a static image of
    it and shall state the substitution in the document

### REQ-003 - Reports carry their provenance
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-007: When a report is produced, the system shall record in it the @Workspace, the @Case, the
    source files with their modification times, the declared units, and the product version
  - AC-008: If a @Field used in the report has no declared unit, then the report shall show that value
    with the undeclared-unit marker rather than a guessed unit

### REQ-004 - The user's art style is applied to output
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-009: When an @Art style is selected, the system shall apply its fonts, colour maps and figure
    styling to the report and to exported images
  - AC-010: If an @Art style asset is missing, then the system shall export with the default style and
    shall name the missing asset rather than silently substituting

### REQ-005 - Machine-written commentary is optional and marked
- priority: SHOULD
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-011: Where commentary is generated, the report shall mark each generated passage as generated
    and shall name the values it was derived from
  - AC-012: If commentary would state a value that is not present in the @Dataset, then the system
    shall omit that statement rather than publishing it
  - AC-013: While no language model is configured, the system shall produce reports with the
    mechanical summary only, and shall not require a network

### REQ-006 - Commentary depth is chosen, and its cost is stated before it is spent
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-017: When generated commentary is requested, the system shall offer a depth and shall state what
    it will send and roughly what it will cost before sending anything
  - AC-018: Where a direction for the commentary is given in words, the system shall use it to choose
    what to discuss, and shall not use it to change any value
  - AC-019: If the configured budget for a report would be exceeded, then the system shall stop and
    report what was produced so far rather than continuing silently

### REQ-007 - Reference material informs commentary, never numbers
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-020: When commentary cites a document, the report shall name the document and mark the statement
    as drawn from reference material (INV-013)
  - AC-021: If a document contradicts the loaded data, then the report shall carry the data value and
    state that the document disagrees (XC-013)

### REQ-008 - Video and image blocks come from view definitions
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-022: When a report block names a @View, the system shall render it through the same definition
    the interface uses, so the document and the screen agree
  - AC-023: Where a block requests a video, the system shall produce it from a camera path and state
    the time mapping used

### REQ-009 - Commentary is checked against the written standard, statement by statement
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-071 (T1)
- acceptance:
  - AC-024: When commentary is generated, the system shall check every statement against
    [../../14_reporting_standards.md](../../14_reporting_standards.md) and shall not publish one that
    fails (XC-104)
  - AC-025: When a statement fails the check, the system shall attempt one rewrite and then omit it,
    and the report shall state how many passages were omitted
  - AC-026: Where a passage uses **verification**, **validation**, **converged**, **grid-independent**
    or **accurate**, the system shall publish it only when that term's precondition holds (XC-107)
  - AC-027: If discretisation error has not been quantified for a @Case, then the report shall state
    that it has not, rather than omitting the subject or implying convergence

### REQ-010 - Citations resolve to documents the product holds
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-072 (T2)
- acceptance:
  - AC-028: When a passage carries a citation, the system shall resolve it to a retrieved document held
    by the product, selected by identifier from what was offered (XC-105)
  - AC-029: If a statement's support is not among the retrieved documents, then the system shall omit
    the statement rather than publish it with a reference it composed
  - AC-030: When a citation is rendered, the system shall record what was retrieved, from where, and on
    what date, and shall keep the retrieved text so the report stays readable if the source changes

### REQ-011 - Every report says what is not known
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-068 (T1)
- acceptance:
  - AC-031: When a report is produced, the system shall include a limitations section, even where its
    content is a single sentence stating that error was not quantified and no measured data was present

### REQ-012 - A comparison is a computed result, and reads like one
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-070 (T1)
- acceptance:
  - AC-032: When a comparison is stated, the system shall give its magnitude and direction and shall
    name what it is relative to
  - AC-033: If a difference is smaller than the stated tolerance or uncertainty, then the system shall
    report it as not distinguishable at that tolerance, and shall not report it as equal or as a change
    (INV-016)

### REQ-013 - Shipped samples are generic and shippable
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-062 (T1)
- acceptance:
  - AC-034: When the product is installed, the sample library shall contain report templates covering a
    journal-paper format, a technical memorandum, a one-page summary, a design-review deck and a
    cross-case comparison, none carrying an organisation's branding or assuming a solver (XC-108)
  - AC-035: If a sample asset's terms do not permit redistribution, then the product shall ship a
    placeholder in its place rather than the asset (XC-085)

### REQ-014 - Output goes somewhere predictable, and never overwrites the last run
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-036: When artefacts are written, the system shall place them under the @Workspace folder at
    `output/<name>/<run timestamp>/<case name>/` and shall not overwrite an earlier run (XC-113)
  - AC-037: If a name pattern would produce a collision within one run, then the system shall refuse
    before the run starts, naming the pattern, rather than appending a number
  - AC-038: Where a @View uses a colour map that is not perceptually uniform, the report shall carry a
    note saying so (XC-111)

### REQ-015 - A report may draw on several workspaces
- priority: SHOULD
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-039: When a @Report names several @Workspace as sources, the system shall produce one document
    and shall record which workspace each value came from (XC-118, INV-013)
  - AC-040: If a named @Workspace is unavailable, then the system shall produce the report from the rest
    and shall state which source was missing

### REQ-016 - Output kinds include plain text and markup
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-041: When an output kind is chosen, the system shall offer the interactive document, PowerPoint,
    Word, Excel, CSV, image, video, **plain text and Markdown**, from one report definition
  - AC-042: Where a kind cannot carry a block - a 3D scene in plain text - the system shall state what
    it replaced it with rather than dropping it silently

### REQ-017 - A deliverable records what it was made from
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-043: When a @Report is exported, the system shall record the content identity of every input
    dataset and the @Workspace version it used (INV-027)
  - AC-044: If an input has changed since a deliverable was produced, then the system shall be able to
    state that the deliverable came from data that has since changed

## End-to-end verification

Build a @Case with a @View and two @Graph, one field with a declared unit and one without; export the
HTML report and open it in a browser with networking disabled; rotate the model, read the values, and
confirm the undeclared field carries its marker; export the same case to PowerPoint and confirm the
numbers match the HTML exactly; regenerate the report after reopening the saved @Workspace and confirm
the two exports are identical.
