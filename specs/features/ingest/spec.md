---
status: draft
updated: 2026-08-20
---

# Feature: result ingest

## Users and purpose

- intended user: an analysis engineer with a folder of solver output who does not want to write a
  reader, a converter or a pipeline
- job to be done: get results into the product by dropping files on it, and know immediately what was
  understood and what was not
- success condition: the mesh appears, the available @Field values are listed with their association,
  and anything the file did not say is shown as not said rather than filled in

## Out of scope

- generating meshes, boundary conditions or solver input
- editing geometry
- reading formats whose specification is not publicly available
- inferring units, boundary conditions or material properties from the data

## Files and interfaces involved

- the @Workspace document a read case is recorded in, including its state, result axis and measurements (CT-001)
- the engine operations that read, describe and probe a dataset (CT-003), and the failure shape they report in (CT-010)

- MOD-002 dataset-io, MOD-001 domain-core
- the format list of [../../06_external.md](../../06_external.md)
- the size and count limits of [../../05_limits.md](../../05_limits.md)

## Requirements

### REQ-010 - Files are imported by dropping them
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-020: When the user drops one or more supported files onto the window, the system shall create
    or update a @Case and shall list every @Field it read, with point or cell association shown
  - AC-021: If a dropped file is of an unsupported format, then the system shall name the format and
    shall state that it is not supported, without creating a partial @Case
  - AC-022: If a supported file is unreadable or truncated, then the system shall report the failure
    with the file name and shall leave the @Workspace unchanged

### REQ-011 - What the file did not say is not invented
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-023: When a @Dataset is loaded, the system shall show every @Field as having no declared unit
    until the user declares one
  - AC-024: If a value is requested in a unit while no unit is declared, then the system shall refuse
    the conversion and shall state that the unit is undeclared
  - AC-025: While a @Field has no declared unit, the system shall display and export its values as bare
    numbers carrying the undeclared marker

### REQ-012 - Time steps and multi-part files are one Case
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-026: When a series or a partitioned set is imported, the system shall present it as one @Case
    with a time axis, and shall state how many steps and parts it found
  - AC-027: If parts of a partitioned set are missing, then the system shall load what exists, mark the
    @Dataset as partial, and shall carry that mark into every number derived from it

### REQ-013 - Geometry is converted into the canonical frame on load
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-040 (T1)
- acceptance:
  - AC-028: When a file is read, the system shall convert its geometry into the canonical frame and
    shall record the source frame and scale it applied
  - AC-029: If a file declares a frame or scale the reader does not support, then the system shall
    refuse the import and shall name what it did not support

### REQ-014 - Large datasets degrade visibly, not silently
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-030: While a @Dataset exceeds the interactive display budget, the system shall show a reduced
    representation and shall mark the view as reduced
  - AC-031: If a reduced representation is displayed, then the system shall compute every reported
    number on the full @Dataset, not on the reduction

### REQ-015 - The support level of a format is stated before it is trusted
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-034 (T1), E-036 (T1)
- acceptance:
  - AC-032: When a file is imported, the system shall show the declared support level of its format -
    Verified, Limited or Unsupported - alongside the loaded @Case
  - AC-033: Where a format is Limited, the system shall name the specific gaps for that reader rather
    than a generic warning
  - AC-034: If a @Field carried unit information in the file that the reader did not read, then the
    system shall still treat the unit as undeclared rather than implying one

### REQ-016 - Identifiers and measured values are first-class inputs
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-075 (T1)
- acceptance:
  - AC-035: When a file carries global or pedigree identifiers, the system shall preserve them and use
    them to report extreme values and to match locations between cases (INV-023)
  - AC-036: If a file carries no identifiers, then the system shall say so and shall not present an
    array index as one
  - AC-037: When measured values are imported against a @Case, the system shall hold them as
    @Measurement data usable as a source of numbers, separate from @Reference material (XC-125)
  - AC-038: Where a measured value carries an uncertainty, the system shall keep it with the value so a
    comparison can state both (XC-107)
  - AC-039: If measured values are imported with no declared unit, then the system shall mark them
    undeclared rather than assuming the unit of the computed field they will be compared against
  - AC-040: When a solver wrote values at integration points, the system shall read them as written and
    shall not extrapolate them to nodes (XC-123)

### REQ-017 - Result kinds beyond time, read as what they are
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-076 (T2)
- acceptance:
  - AC-041: When a file carries modal results, the system shall read them indexed by mode number and
    shall carry each mode's eigenfrequency (GL-036)
  - AC-042: When a file carries harmonic results, the system shall keep the real and imaginary parts
    together as a @Complex result, indexed by frequency
  - AC-043: If a result kind cannot be determined from the file, then the system shall report it as
    unknown and shall not present the index as time
  - AC-044: When results of different @Result axis are placed in one @Graph or @Report, the system shall
    state that they come from different axes

## End-to-end verification

Drop a multi-step, partitioned result set with one part removed; confirm the @Case loads, is marked
partial, lists its fields with association and no declared unit; declare a unit for one field and
confirm every display and export of that field carries it; confirm a reported maximum equals the value
computed from the full data and not from the reduced display.
