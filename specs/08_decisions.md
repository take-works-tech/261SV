---
status: draft
updated: 2026-08-26
---

# Decisions and open questions

Project-level decisions and what they ruled out. A feature-level choice belongs in that feature's
`plan.md`; this file holds the ones that constrain more than one feature.

**A superseded decision is marked, never deleted.** Delete it and the next reader re-proposes the
option that already lost, because nothing records that it lost.

## Decisions

### XC-030 - Numbers are computed on data, pictures are made from geometry
- decided: 2026-08-19
- status: active
- decision: every reported value is computed on the @Dataset in the canonical frame; display geometry
  is never measured
- alternatives: measuring what is drawn is simpler and is what a naive implementation does; it was
  rejected because decimation, tessellation and scaling all change it, silently
- basis: E-001 (T1)
- affects: INV-001, INV-002, XC-010
- decidedness: Fixed

### XC-031 - Blender is reached by exporting USD, not by embedding
- decided: 2026-08-19
- status: active
- decision: the product exports USD (and VDB where volumetric) and the user opens it in Blender; no
  Blender code, module or process is part of the product
- alternatives: embedding `bpy`, or driving Blender as a child process, both give tighter integration
  and both put the product inside Blender's GPL obligations; a one-way file handoff does not
- basis: E-010 (T1), E-011 (T1)
- correction: the basis is the GPL itself, not the four conditions in Blender's FAQ. **This product
  does not satisfy the fourth condition** - it does not execute Blender; the user does - so citing the
  FAQ as a safe harbour would contradict itself. The correct reasoning is simpler: the product never
  copies, links to or distributes Blender code, binaries or `bpy`, so no permission from Blender's
  copyright holders is needed at all. The FAQ is volunteer-written commentary, not an added permission,
  and the Blender Foundation cannot bind the other copyright holders
- affects: MOD-002, XC-050
- decidedness: Fixed

### XC-032 - The desktop build is the reference product
- decided: 2026-08-19
- status: active
- decision: the desktop application is the product whose behaviour defines correctness; the web
  service is the same core reached over a different transport
- alternatives: building the web product first is cheaper to ship and reaches more people; it was
  rejected because the buyers who cannot send geometry outside their network are the ones this
  product is for, and they are unreachable from a browser-first design
- basis: E-001 (T1)
- affects: MOD-009, XC-014, XC-050
- decidedness: Fixed

### XC-034 - Ship the published VTK wheel and discharge the gl2ps obligation by publication
- decided: 2026-08-19
- status: active
- decision: use the published VTK wheel as it is. The modified gl2ps it contains is redistributed
  under the GL2PS licence, and the obligation is discharged by naming the exact VTK version in the
  notices file and shipping the corresponding source archive alongside the installer, or a link to it
- alternatives: building VTK from source with the export module disabled removes the obligation
  entirely, but costs a toolchain, a multi-hour build and a per-release maintenance burden on three
  platforms - recurring cost against a duty that is discharged by a paragraph and an archive. The
  reason to build from source later is size (LIM-004) or disabling readers with open advisories
  (XC-047), and even the second is better served by never invoking those readers
- note: 2026-08-25, a **third reason** the alternatives above do not list, and a stronger one because it
  buys a capability rather than removing an obligation. The published wheel contains **no ray-tracing
  back end at all** - measured, 27 rendering modules and no OSPRay, ANARI, OptiX, OpenVKL or Embree
  among them (E-153). Any photorealistic path through VTK therefore requires the source build this
  decision declined. That does not reverse the decision - the obligation argument stands and the build
  cost is unchanged - but it means the trade is no longer "a paragraph and an archive against a
  toolchain", and OPEN-031 weighs it against two alternatives that did not exist when this was
  decided
- basis: E-045 (T1), E-051 (T1), E-052 (T1)
- affects: XC-041, XC-025, LIM-004
- decidedness: Fixed
- reversal_trigger: the installer exceeds LIM-004, or a reader must be removed rather than merely not
  called

### XC-035 - The first release is domestic business-to-business
- decided: 2026-08-19
- status: active
- decision: the first release targets Japanese small and medium manufacturers who cannot send geometry
  outside their network. Japanese interface, invoice-based purchase, a perpetual licence under
  JPY 399,000, and an offline installer. The free recipient-side viewer travels globally from the
  start; the paid self-serve English channel comes after the domestic motion has customers
- alternatives: global self-serve first is the only motion a single developer can scale, and it was
  the tempting answer - but the standalone visualisation vendors total about USD 5 million in revenue
  between them, so a volume motion is aiming at a market that has not existed for anyone. The
  differentiator - offline operation, declared units, provenance, a finished deliverable - is worth
  most to exactly the buyer who cannot use a hosted tool, and that buyer is reachable in Japan without
  a sales organisation
- basis: E-043 (T1), E-027 (T2), E-050 (T1)
- affects: XC-071, XC-021, XC-051
- decidedness: Fixed
- reversal_trigger: twelve months of domestic effort producing fewer than five paying customers, or an
  inbound English-language demand pattern that the free viewer surfaces

### XC-036 - Incorporation is deferred, with a stated trigger
- decided: 2026-08-19
- status: active
- decision: ship the first release as an individual. Code signing is available to an individual in
  Japan through an individual-validation certificate with cloud signing, so incorporation is not on
  the critical path. Incorporate when the first corporate customer requires an invoice the individual
  form cannot satisfy, or when annual revenue makes the tax position favourable
- alternatives: incorporating first unlocks the cheapest signing route and looks more credible to a
  procurement department, at a fixed annual cost against revenue that does not exist yet. Paying that
  before there is a customer is buying an option nobody has asked for
- basis: E-023 (T1)
- affects: XC-051, XC-071
- decidedness: Fixed
- reversal_trigger: a customer who cannot buy from an individual, or revenue crossing the threshold
  where the tax position favours a company

### XC-037 - Omniverse ships as an optional capability, never as a requirement
- decided: 2026-08-19
- status: active
- decision: the photorealistic path through Omniverse is offered as an optional feature. It is absent
  from the default experience, it is stated at install and at use to require an NVIDIA GPU or CPU, and
  every function of the product remains complete without it. Redistribution obligations - attribution,
  usage reporting on request, and flow-down of terms - are carried in the notices file
- decided_by: the product owner, 2026-08-19. The specification's role here was to establish that the
  legal path exists (E-041) and that the hardware restriction is real (E-009); the reach-versus-appeal
  trade-off is the owner's
- alternatives: shipping USD export alone would keep one experience for every machine and one build to
  test; it was not chosen because the photorealistic result is a visible differentiator and the
  restriction is stateable rather than hidden
- basis: E-009 (T1), E-041 (T1)
- affects: EXT-005, GL-009, OPEN-001, XC-042, XC-050
- decidedness: Fixed
- reversal_trigger: the optional path costing more in build, verification and support than the
  customers who can run it are worth, or NVIDIA narrowing the redistribution grant

### XC-038 - A comparison across different meshes is an explicit, disclosed operation
- decided: 2026-08-19
- status: active
- decision: when two cases share a mesh, the difference is computed directly with no interpolation.
  When they do not, the user chooses which mesh is the basis, the resampled result is created as a
  named dataset in its own right, and the comparison reports four things beside every number: the
  direction of the resampling, the count and proportion of points that fell outside the source, the
  round-trip interpolation error on the same scale as the difference, and the fact that the visible
  difference is physical difference plus discretisation plus interpolation. Where the difference is the
  same order as the round-trip error, the region is shown as undetermined rather than coloured
- alternatives: allowing only identical meshes is honest and cheap, but forbids mesh-convergence and
  redesign comparison - the work this product exists for. Comparing integral quantities alone avoids
  interpolation entirely and is kept as the one number that never passes through it, but on its own it
  cannot answer "where did it change"
- basis: E-054 (T1), E-055 (T2), E-056 (T1)
- affects: GL-011, MOD-004, INV-011
- decidedness: Fixed
- reversal_trigger: outside-point proportions routinely above 5 per cent in real customer data, or one
  reproducible case where round-trip error diverges systematically from true error on a discontinuous
  field - in which case the comparison refuses rather than reporting

**The round-trip error is close to a lower bound, not an upper one.** Errors can cancel between the
forward and reverse passes, and a field lying in both meshes' function spaces returns zero while the
one-way error is not zero. The interface must say this, because a number presented as an error bound
that is not one is worse than no number.

### XC-039 - Licence verification is local, and never stops the work
- decided: 2026-08-19
- status: active
- decision: a licence is a signed file bound to a user or organisation, delivered by e-mail and
  verified entirely offline with a public key embedded in the product. It carries an update-until date
  and **no run expiry**: the version a customer has keeps working indefinitely. A machine fingerprint
  is recorded locally but never enforced; a clock rolled backwards produces a warning and nothing else;
  and no licence check may block, discard or alter a computed result
- alternatives: node-locking and online activation both give real enforcement, and both were rejected
  for the same reason: an offline product cannot revoke anything anyway, so their only reliable effect
  is to break a customer's work on the day they change a machine. Comparable single-developer products
  bind per user and survive on the licence terms and pricing rather than on enforcement
- basis: E-057 (T1)
- affects: XC-028, XC-014, XC-071
- decidedness: Fixed
- reversal_trigger: one confirmed case of a licence file circulating outside its purchaser, or renewals
  becoming more than a few hours of manual work per month - and even then the change applies to new
  contracts, never by stopping software a customer already runs

### XC-080 - Generated content configures the view; it never computes a number
- decided: 2026-08-19, amended 2026-08-20
- status: active
- decision: the assistant emits a configuration in a schema of this product's own - enumerated values
  and identifiers, with no expression language and no evaluator - which is validated against an
  allow-list on arrival. **No model-generated code is ever executed.** Selection and filtering are
  expressed declaratively by default (CT-007). A user may opt in to writing their own code for
  selection, which runs under XC-089; a model may not write that code, and nothing written there
  reaches the numeric path
- alternatives: a declarative charting grammar looks like the safe answer and is not - the common one
  compiles expressions to JavaScript and has a history of sandbox escapes, so safety turns on whether
  the grammar contains an evaluator rather than on whether it is declarative. Restricted execution
  inside Python is ruled out by its own maintainers, who state plainly that it is not a sandbox
- basis: E-058 (T1)
- affects: assistant/REQ-006, XC-013
- decidedness: Fixed
- reversal_trigger: more than a third of real requests failing to fit the schema, which would mean the
  schema is too narrow - answered by widening the schema, never by adding an expression field

A sandbox protects the host, not the number. Since this product's claim is the number, the decision is
made one level earlier: nothing generated is on the path that produces one.

### XC-081 - Grouping cases is an offered suggestion, never an applied inference
- decided: 2026-08-19
- status: active
- decision: import proposes a hierarchy only from deterministic, explainable signals - a numbered file
  pattern, a shared directory, metadata already present - and shows the signal it used. The proposal is
  never applied by default, is accepted or rejected in one action, and a rejection is not re-proposed
  in the same session
- alternatives: general similarity inference covers more cases and cannot explain itself, which turns a
  wrong grouping into a mystery the user has to unpick
- basis: E-001 (T1)
- affects: workspace/REQ-006
- decidedness: Fixed
- reversal_trigger: users rejecting more proposals than they accept, which means the signals are wrong
  and the feature should be withdrawn rather than tuned

### XC-083 - The first release carries all four work areas
- decided: 2026-08-19
- status: active
- decision: ingest, visualisation, report and assistant all ship in the first release, with comparison
  included
- decided_by: the product owner, 2026-08-19
- alternatives: deferring the assistant would roughly halve the surface to build and verify, and the
  differentiator would survive without it. The owner chose the full scope; the specification's job is
  now to make that scope honest rather than to argue with it
- basis: E-001 (T1)
- affects: every feature
- decidedness: Fixed
- reversal_trigger: the assistant's verification cost delaying the first release past the point where
  a customer is waiting - at which point it becomes the first thing to defer, because everything else
  is what the customer came for

### XC-084 - There is no first customer yet, and the product must find one
- decided: 2026-08-19
- status: active
- decision: no design partner is identified. The free tier and the recipient-side report are therefore
  the discovery mechanism, not a marketing nicety: a report opened by a colleague is the only
  distribution this product has before it has customers. Two things follow for the first release - a
  report must be openable by someone who has never heard of the product, and the free tier must be
  useful enough that a stranger keeps it
- decided_by: the product owner, 2026-08-19, in answer to whether a first customer exists
- basis: E-001 (T1)
- affects: XC-035, XC-082, report/REQ-001
- decidedness: Fixed
- reversal_trigger: a design partner appearing, which would replace guesses about the workflow with
  observation and should immediately re-open the format priority below

### OPEN-012 - Which solvers the first customers actually use
- decidedness: Open
- open: OPEN-012
- question: the Verified format list - CGNS, EnSight Gold, Exodus, VTK XML - is fluid-dynamics leaning,
  while the largest group of certified computational engineers in Japan is in solid mechanics, where
  the format situation is materially worse: Abaqus ODB has no reader at all and Nastran support is
  minimal. If the first customers are structural analysts, the first release needs a different and
  harder format plan than the one currently written
- note: cannot be settled without a customer (XC-084). Deciding it from market statistics alone would
  be a guess wearing a citation
- affects: XC-049, EXT-004, ingest/REQ-015

### XC-085 - Test data is generated, not collected, wherever the format allows it
- decided: 2026-08-19
- status: active
- decision: fixtures are written by this product's own test code using the toolkit's writers, so they
  carry no third-party licence and can live in the repository. That covers EnSight, Exodus and IOSS,
  VTKHDF, the VTK XML family including partitioned files, and STL. **CGNS has no writer**, so its fixture
  was to come from an outside file whose source and terms are recorded before it is committed. Formats in the Offered tier that cannot be generated - OpenFOAM, Fluent,
  LS-DYNA, Tecplot, Plot3D - are verified manually against files the developer holds locally and does
  not redistribute, and the verification plan says so rather than implying automated coverage
- correction: this said "five of the six Verified formats" and named CGNS as the exception, on the
  correct premise that the toolkit ships no CGNS writer - measured again 2026-08-24 and still true, three
  reader classes and none that writes (E-137). The conclusion drawn from it was wrong. **A CGNS file can
  be generated without a CGNS writer**: CGNS/HDF5 stores every node as an HDF5 group with four attributes
  and an optional ` data` dataset, and h5py writes that directly. So the rule holds for **six of six**,
  no outside file is needed, and h5py joins the development dependencies for that one purpose. What the
  generated fixture does not cover - multi-zone, structured zones, boundary conditions, ADF-format CGNS -
  is named in the format's stated gaps rather than left to be assumed from the word Verified
- alternatives: collecting public sample files is faster and was the obvious first answer. It fails on
  terms: the CGNS examples are submitted as-is with no licence, the toolkit's own data repository
  declares none, and the public research resources state none either. Shipping data whose licence
  nobody can name is the kind of risk that surfaces at the worst moment
- basis: E-061 (T1), E-062 (T1)
- affects: the verification plan, ingest/REQ-015
- decidedness: Fixed
- reversal_trigger: a public dataset appearing with explicit redistribution terms and the properties
  that matter - high-order cells, partitioned pieces, missing parts - which would be better evidence
  than anything generated here, because generated data only contains the problems we thought of

### XC-086 - Two machine classes, measured at first start
- decided: 2026-08-19
- status: active
- decision: the product supports both a business laptop with integrated graphics and an analysis
  workstation with a discrete card. At first start it probes the machine, records the class, and
  applies the limits for that class; the chosen class is shown in settings and can be overridden by the
  user, who knows their machine better than a probe does
- decided_by: the product owner, 2026-08-19, choosing to support both rather than one
- alternatives: targeting the laptop alone keeps one set of numbers and one test matrix, at the cost of
  refusing work a workstation could do. Targeting the workstation alone loses the buyer with the lowest
  barrier to trying it. Two classes cost a second test pass and a probe
- basis: E-001 (T1), E-053 (T1)
- affects: LIM-001, LIM-002, LIM-006, ingest/REQ-014
- decidedness: Fixed
- reversal_trigger: the two classes needing different behaviour rather than different numbers, which
  would mean they are two products and the specification should say so

**The measurements taken so far are from the laptop class**, on integrated graphics, and are recorded
as such (E-051, E-053). The workstation row is unmeasured, and the specification does not pretend
otherwise - a limit inherited from the wrong class is worse than an admitted gap, because it looks
measured.

### XC-087 - Three renderer roles, one of them optional
- decided: 2026-08-19
- status: active
- decision: the product ships three rendering paths with separate jobs, and one optional fourth.
  **In the interactive view**, geometry is rendered in the shell by the scientific web renderer on
  WebGL2 - the default, and the only path a user meets unless they ask otherwise. **For datasets above
  the interactive budget** (LIM-002), and **for images destined for a report**, the engine renders
  offscreen with the native toolkit and sends the result as an image: it is already embedded for the
  readers, it has no browser memory ceiling, and report images want quality rather than interactivity.
  **WebGPU** is selectable and marked experimental. **Omniverse** is the optional path of XC-037
- rationale: the two main paths are not alternatives but a division of labour, and the measurement
  supports it - 11.5 million triangles render at about 43 frames a second on integrated graphics once
  readback is netted out, but the same geometry costs 16 MB compressed to move into a browser, and a
  report needs a still rather than a scene. Choosing one path for both jobs would either starve the
  interactive view or make every report a screenshot
- alternatives: browser-only keeps one code path and caps the dataset at what fits in a tab; native-only
  loses the web product entirely (XC-032); a streaming-first design is what large-data tools do and adds
  latency to every rotation on a laptop that does not need it
- basis: E-016 (T1), E-017 (T1), E-018 (T1), E-019 (T1), E-051 (T1), E-063 (T1)
- affects: GL-009, MOD-003, INV-002, XC-044
- decidedness: Fixed
- reversal_trigger: the interactive path and the offscreen path disagreeing on any reported number,
  which would mean INV-002 is broken and the division of labour has leaked into the numbers

### XC-088 - One variable list, with provenance never optional
- decided: 2026-08-20
- status: active
- decision: values a person declared, fields read from a @Dataset, and quantities computed by an
  expression appear in one list and are referenced the same way. **Each carries its provenance, shown
  wherever it is shown**: in the list, in an input it is bound to, on a graph axis, and in an exported
  report. A computed quantity carries the expression that produced it
- decided_by: the product owner, 2026-08-20, choosing unification with provenance displayed over
  keeping the concepts separate
- alternatives: keeping variables and fields as separate concepts makes origin obvious by construction
  and was the earlier decision; it also means a user maintaining a parameter study works in two lists
  that behave differently. Unifying without showing provenance was rejected outright: this product's
  claim is that a number can be traced, and a list where a typed value and a measured one look identical
  is the precise opposite
- basis: E-001 (T1)
- affects: GL-003, GL-006, GL-016, INV-004, INV-013, CT-001, workspace/REQ-002
- decidedness: Fixed
- reversal_trigger: users mistaking a declared value for a measured one despite the display, which
  would mean the unification is wrong rather than the display

### XC-089 - User-written code is allowed, in a separate process, off the numeric path
- decided: 2026-08-20
- status: active
- decision: a user may write Python that **selects, filters and orders** - which cases a graph draws,
  which cases a report covers, how a repeated study is grouped. It runs in a separate process with no
  network, a working directory it cannot leave, a time limit and a memory limit, and it receives
  metadata rather than datasets. **It cannot produce a reported value**: every number the product
  displays or exports is computed by the analysis module from the dataset, never by user code
- decided_by: the product owner, 2026-08-20, choosing declarative-by-default with code as an opt-in
- alternatives: declarative-only keeps one path to verify and cannot express what a real parameter
  study sometimes needs; code-only is simpler to build and puts an evaluator on the path this product
  exists to protect. The split follows the value: **the choice of what to show may be arbitrary; the
  values shown may not be**
- basis: E-058 (T1)
- affects: XC-080, assistant/REQ-006, CT-007
- decidedness: Fixed
- reversal_trigger: a request to compute a displayed value in user code - which is not a feature
  request but a change of product, and reopens this decision rather than bending it

**Restricting a language from inside itself does not work**, and this decision does not try: the
isolation is a process boundary and an operating-system permission set, not a restricted interpreter
(E-058). The guarantee this product offers is unaffected either way, because the guarantee is about the
numbers, and no number comes from here.

### XC-090 - A template applies as far as it resolves, and names what it could not
- decided: 2026-08-20
- status: active
- decision: applying a @Template resolves each reference - fields, units, time steps, assets - against
  the target and, after the user accepts the resolution result, creates a new independent workspace
  @View, @Graph or @Report. What resolves is copied into that artefact; what does not is listed, by name
  and by what was missing, before anything is drawn. A graph series whose field is absent is drawn as
  **no data** rather than omitted, and a report block whose source is absent says so in the document
- decided_by: the product owner, 2026-08-20, choosing partial application with the gaps named
- alternatives: applying only on an exact match makes the rule trivial and defeats the purpose - a
  template exists to cross studies. Asking the user to map every unresolved reference is more precise
  and turns a one-click action into a form; that mapping remains available, but not as the default
- basis: E-001 (T1), E-088 (T1)
- affects: GL-017, GL-018, CT-008
- decidedness: Fixed
- reversal_trigger: users applying templates and not reading the gap list, which would show as reports
  containing empty blocks nobody noticed - at which point application becomes a confirmation step

**Omitting is not the same as showing nothing.** A missing series drawn as no data leaves the shape of
the question visible; a missing series removed from the legend makes the reader believe they are
looking at everything.

### XC-091 - Driving external solvers is a later release, and this product never solves
- decided: 2026-08-20
- status: active
- decision: the simulation area exists in the layout from the first release and states that it is not
  yet available. Later, it will **drive external solvers** through their own interfaces to run repeated
  studies and collect results. **This product never computes a solution itself**, in any release
- alternatives: hiding the area until it works keeps the interface honest about what exists; showing it
  with a statement sets the expectation that this is a product for the whole loop, which is what the
  first release is a step toward. The second was chosen, on the condition that the area says plainly
  what it is not
- basis: E-001 (T1)
- affects: XC-092, ingest scope
- decidedness: Fixed
- reversal_trigger: the area being mistaken for a broken feature rather than an announced one

### XC-092 - The command surface ships from the start; the command-line product ships later
- decided: 2026-08-20
- status: active
- decision: the command surface and its adapters are built as the base structure from the first
  commit - the interface uses them, so they are exercised continuously rather than kept aside. A
  supported command-line product, including natural-language instructions entered at the command line,
  is released in the second release
- decided_by: the product owner, 2026-08-20
- alternatives: adding a command surface later means retrofitting undo, audit and headless operation
  onto an interface built without them, which is the change that never quite finishes. Releasing the
  command line first reaches developers rather than the analysts this product is for (XC-084)
- basis: E-001 (T1)
- affects: assistant/REQ-004, CT-002, CT-003, MOD-008
- decidedness: Fixed
- reversal_trigger: demand from customers who want the headless product before the interface, which
  would be evidence about who the customer actually is

**Building it first and releasing it later is deliberate.** A surface the product itself uses cannot
drift from the product; a surface built for an external audience and used by nobody internally becomes
a second implementation with its own defects.

### XC-093 - The pipeline is an editor, and the automation this product exists for
- decided: 2026-08-20
- status: active
- decision: the pipeline belongs to the @Workspace and stands above @Case. It is composed by dragging
  @Template into an ordered list, reordering and removing them, and it is executed to **produce** cases
  and then act on them: each execution of a simulation step is one case, and downstream steps run per
  produced case or once across the whole set, as the step states. It also carries built-in steps, including
  releasing loaded data so that a study larger than memory can run to the end. A simulation template
  may contain view, graph and report steps, nested to LIM-007 levels
- decided_by: the product owner, 2026-08-20, replacing the earlier reading of the pipeline as a display
- alternatives: a read-only view of what was done is simpler and is what the earlier draft assumed; it
  also leaves the product's central promise - do this for all forty runs - unimplemented
- correction: an earlier version of this decision placed the pipeline below the case, as something
  applied to a set of cases that already existed. That is backwards: the pipeline is what brings cases
  into existence, and a design that assumed they were already there would have had no place to put a
  simulation step's output
- basis: E-001 (T1)
- affects: GL-022, CT-009, LIM-007, MOD-007, MOD-011, XC-046, XC-099
- decidedness: Fixed
- reversal_trigger: users building pipelines they cannot predict the effect of, which would mean the
  composition needs constraining rather than the feature removing

**Correction, 2026-08-20.** An earlier version of this decision ended: *it composes; it does not
compute - a pipeline has no expressions, no branches and no user-written loops*. That is now wrong in
its conclusion and was wrong in its reasoning. Repetition driven only by the cases a step resolves to
cannot express "run this for each of these five inlet velocities", which is the ordinary parameter
study every user of this product runs. A pipeline **does** compute, in a bounded way: loops (XC-100),
variables and formulas (XC-101), and conditions. What survives from the old sentence is the line it was
trying to draw, now drawn where it belongs - **the language is restricted and has no interpreter behind
it** (XC-101), rather than absent.

### XC-094 - Destructive steps are authorised once, for a named scope, and never silently
- decided: 2026-08-20
- status: active
- decision: a pipeline containing a destructive step cannot run until the user authorises that step for
  the run, and the authorisation states which step and how many cases it covers. A dry run showing the
  same figures is available before authorising. In headless operation the authorisation must be
  supplied explicitly; its absence is a refusal, never an assumption (assistant/AC-006)
- alternatives: confirming per case is safer for one case and unusable for forty, which is how people
  learn to click through confirmations. Authorising once with an explicit scope keeps the decision
  deliberate while keeping the run possible
- basis: E-001 (T1)
- affects: CT-009, XC-062, MOD-007
- decidedness: Fixed
- reversal_trigger: an authorised run deleting more than the count it stated, which would mean the
  scope is computed at the wrong time

### XC-095 - A pipeline failure is isolated to its case
- decided: 2026-08-20
- status: active
- decision: a step that fails on one @Case does not stop the run; the remaining steps for that case are
  skipped rather than run on a broken state, and the case is reported as failed with the step that
  failed. Stopping the whole run is available and is chosen, not assumed. Nothing partial is written -
  a report whose figure failed is not exported with a gap
- rationale: a forty-case study where one file is truncated should produce thirty-nine results and one
  clear failure, not zero results and one clear failure. But continuing *within* a failed case would
  build a report on a state nobody checked, which is the silent-wrong-answer failure this product
  exists to prevent
- basis: E-001 (T1)
- affects: CT-009, XC-002, MOD-007
- decidedness: Fixed
- reversal_trigger: users not noticing failed cases in a large run, which would move the reporting
  rather than the isolation

### XC-096 - Numeric types, digits and tolerances are part of the data, not of the formatting
- decided: 2026-08-20
- status: active
- decision: every quantity carries its @Stored precision alongside its unit and provenance. Computation
  happens in 64-bit floating point; **reading a 32-bit field does not promote its precision**, and a
  value derived from mixed precision takes the weakest. Displayed and exported digits follow
  @Significant digits, never a formatter default. Counts and indices are integers throughout
  (INV-015). Comparisons of physical values use a stated tolerance (INV-016), and unit conversion is
  documented as introducing rounding rather than being assumed exact
- rationale: this product is bought for its numbers. Padding a 32-bit value to fifteen digits, or
  comparing two converted values for equality, are both cheap mistakes that produce confident nonsense -
  and both are the default behaviour of the languages and libraries underneath
- basis: E-001 (T1)
- affects: GL-023, GL-024, INV-014, INV-015, INV-016, CT-003, CT-005
- decidedness: Fixed
- reversal_trigger: a customer needing more digits than the source supports, which is a request to
  change the source rather than the display

### XC-097 - A language model never receives bulk numeric data
- decided: 2026-08-20
- status: active
- decision: models receive metadata, statistics the product computed, and text - never arrays of
  results, mesh coordinates or field values in bulk. A value a model states in commentary is one the
  product computed and passed to it explicitly, named as such, and re-checked against the dataset
  before it reaches a document (report/AC-012). What may be sent is bounded and stated per workspace
  before it is sent (assistant/AC-014)
- rationale: three reasons that point the same way. A model asked to read a million numbers cannot do
  arithmetic on them reliably, and will produce a plausible answer anyway. The data is the customer's
  and the product's promise is that it stays on the machine unless they say otherwise (XC-026). And
  the cost of sending it scales with the study while the value does not
- basis: E-031 (T1), E-058 (T1)
- affects: XC-013, MOD-008, assistant/REQ-003, report/REQ-005
- decidedness: Fixed
- reversal_trigger: a model capability that changes the arithmetic argument would still leave the
  other two, so this decision does not reopen on model improvements alone

### XC-098 - Every colour comes from one palette, and data colour never follows the theme
- decided: 2026-08-20
- status: active
- decision: interface colour is defined once as named tokens and used only through them; light and dark
  are two token sets, switched in settings. **Colour maps that encode values are not part of that
  switch**: a scientific colour map means what it means regardless of theme, and the missing-data
  treatment (XC-001) keeps its own fixed appearance in both
- rationale: the first half is ordinary discipline - a colour written inline is a colour nobody can
  change, and a dark mode built by exception is one that misses a panel. The second half is specific to
  this product: if a colour map shifted with the theme, the same value would look different in two
  screenshots of the same result, and readers compare screenshots
- basis: E-001 (T1)
- affects: XC-022, GL-013, MOD-010, 11_ui
- decidedness: Fixed
- reversal_trigger: a colour map that genuinely needs a dark variant - which would need the exported
  document to state which variant produced it, not a silent switch

## Open questions

An Open that survives is not a failure; an Open with no tracking ID is.

### OPEN-001 - Which renderer backends ship, and which is the default
- decidedness: Open
- open: OPEN-001
- status: superseded
- superseded_by: XC-087
- question: VTK, a web renderer, Omniverse and Gaussian-splat display each carry different licence,
  hardware and maintenance costs. Which combination ships in the first release, and which one runs
  when the machine cannot run the others?
- blocked_by: the licensing and rendering research of 2026-08-19; resolve before MOD-003 is built
- affects: GL-009, INV-002, XC-004

### OPEN-002 - What a Diff means between meshes that differ
- decidedness: Open
- open: OPEN-002
- status: superseded
- superseded_by: XC-038
- question: comparing two @Case with different meshes requires mapping one onto the other, and every
  mapping method changes the numbers. Which method, and how is the error it introduces reported?
- affects: GL-011, MOD-004

### OPEN-003 - The canonical frame and unit policy
- decidedness: Open
- open: OPEN-003
- status: superseded
- superseded_by: XC-033
- question: resolved on 2026-08-19 by XC-033 below, once the USD defaults were read rather than assumed
- affects: GL-021, INV-001, MOD-002

### XC-033 - Canonical frame is metres and Z-up, stated explicitly on export
- decided: 2026-08-19
- status: active
- decision: geometry is held in metres with Z up; every exported USD file writes `metersPerUnit` and
  `upAxis` rather than relying on defaults
- alternatives: following USD's defaults would have been less code and would have silently declared
  centimetres and Y-up to every downstream tool, which is the single most likely cause of a model
  arriving in Blender at the wrong scale
- basis: E-040 (T1)
- affects: GL-021, XC-048, MOD-002
- decidedness: Fixed

### OPEN-004 - Whether Omniverse can be embedded and redistributed
- decidedness: Open
- open: OPEN-004
- status: superseded
- superseded_by: XC-037
- question: the product intends to embed Omniverse for photorealistic rendering. Redistribution
  terms decide whether that is possible for a single-person commercial vendor, and no part of the
  architecture may assume it until the licence text says so
- affects: OPEN-001, MOD-003, XC-050

### OPEN-005 - Automatic hierarchy and variable inference on import
- decidedness: Open
- open: OPEN-005
- status: superseded
- superseded_by: XC-081
- question: proposing a hierarchy and the differing variables from a set of imported files is useful
  when it is right and expensive when it is wrong. What accuracy makes it worth offering, and what
  does the user see when it is unsure?
- affects: workspace/REQ-006 (import inference)

### OPEN-006 - How far generated visual configurations may go
- decidedness: Open
- open: OPEN-006
- status: superseded
- superseded_by: XC-080
- question: building graphs and views from a fixed template set is safe and limiting; executing
  generated code is powerful and unbounded. Where is the line, and what does the product do when a
  user asks for something outside it?
- affects: assistant/REQ-006 (generated configurations)

### OPEN-007 - How the product verifies its own licence offline
- decidedness: Open
- open: OPEN-007
- status: superseded
- superseded_by: XC-039
- question: an offline-first product cannot require a network to start, and an air-gapped machine may
  not see one for months. Node-locked file, signed entitlement with a long grace period, or honour
  system with per-organisation keys - each trades enforcement against the promise in XC-014
- affects: XC-028, XC-051

### OPEN-011 - Build VTK from source, or accept the gl2ps obligation
- decidedness: Open
- open: OPEN-011
- status: superseded
- superseded_by: XC-034
- question: the published wheel ships a modified gl2ps, so the obligation to publish those
  modifications applies unless VTK is built from source with the export module disabled. Building it
  costs a toolchain, build time and a maintenance burden per release; accepting the obligation costs
  publishing a patch set and keeping it current. Which is cheaper for a single-person vendor?
- affects: XC-041, XC-025, LIM-004

### OPEN-008 - The capacity limits are placeholders until measured
- decidedness: Open
- open: OPEN-008
- question: **LIM-001, LIM-002, LIM-004 and LIM-006 now carry measured values** (E-051, E-053, E-063).
  What remains unmeasured is LIM-005 (cases per workspace), and the two Bounded budgets that were set
  by argument rather than by measurement: LIM-009 (background primitives) and LIM-012 (output before
  the product asks). Each has a working number in force; none has been defended against a real case
- history: the first attempt to measure LIM-002 failed in a way worth keeping. Frame time was
  independent of triangle count and successive frames were byte-identical, so the harness had measured
  a cached readback rather than rendering. The correction was to hash every frame and assert they
  differ, which E-063 does - twelve frames, all distinct - and that measurement is why LIM-002 is now
  Fixed at ten million rather than the twenty million previously extrapolated from a published
  benchmark on somebody else's card. **The conclusion moved because the measurement contradicted it**,
  and the failed attempt stays recorded so the next person does not repeat the harness
- note: the export measurement also produced an unwelcome number - decimating a million-point surface
  to 10 per cent took 22 seconds, so reduction has to happen once at export and be cached, never per view
- affects: LIM-005, LIM-009, LIM-012

### OPEN-013 - What the pipeline view shows, and whether it can be edited
- decidedness: Open
- open: OPEN-013
- status: superseded
- superseded_by: XC-093
- question: the pipeline in the left sidebar is specified as a display of the operations applied to a
  case, corresponding to entries in the command log. Whether a user may reorder or remove an entry
  there - making it a second way of operating the product rather than a view of what was done - is
  not decided, and the answer changes whether it is a display or an editor
- affects: XC-046, MOD-007

### XC-099 - A pipeline carries one accumulating target set, and units act on all of it
- decided: 2026-08-20
- status: active
- decision: running a pipeline carries exactly one piece of state - the **target set**, the cases every
  unit below applies to. A **case unit** adds cases to it; dropping a multiple selection creates one
  unit holding all of them. A view, graph or report unit acts on **everything accumulated above it**,
  not on the case unit immediately preceding it. A **clear unit** empties the target set and releases
  the data those cases had loaded. This is what lets a pipeline run with no simulation at all: the
  entry point is cases the workspace already has
- decided_by: the product owner, 2026-08-20
- alternatives: naming a source per unit - the cases produced by step 4, or a selection - is more
  explicit and was the earlier design. It also means that adding one case to a study means editing
  every unit below, which is the work the pipeline exists to remove. The two are not exclusive: a case
  unit may hold an explicit list **or** a selection resolved at run time (CT-007), so a pipeline can
  pick up cases that did not exist when it was written
- basis: E-001 (T1), E-067 (T2)
- affects: CT-009, GL-025, GL-026, XC-093
- decidedness: Fixed
- reversal_trigger: users unable to say which cases a unit will act on without running it - which would
  mean the accumulation needs showing at every unit rather than replacing with per-unit sources

The accumulator is the reason a pipeline reads top to bottom like a procedure rather than like a graph.
**The cost is that the target set is invisible unless the editor shows it**, so it is shown: every unit
displays the case count it will act on, and the dry run lists them.

### XC-100 - Loops are bounded, and their count is known before the run starts
- decided: 2026-08-20
- status: active
- decision: a **loop unit** repeats the units it contains a number of times fixed before the loop
  begins - a literal count, the values of a @Variable, or one iteration per case in the target set.
  There is no `while`, and no user-written early exit. A condition that should stop the work goes
  inside the loop as a **conditional unit**, which skips its contents for that iteration
- basis: E-066 (T1)
- alternatives: an unbounded loop with a break is more expressive and makes the dry run impossible.
  That is the whole argument: a pipeline that cannot say what it will do before it does it cannot be
  authorised to delete data, and authorisation before destruction is XC-094
- affects: CT-009, LIM-008, MOD-011
- decidedness: Fixed
- reversal_trigger: a genuine convergence workflow - repeat until a residual falls - which would need
  a bounded iteration cap plus a stated stopping quantity, not an open `while`

### XC-101 - Formulas and conditions use one restricted expression language, evaluated without Python
- decided: 2026-08-20
- status: active
- decision: **variable units**, **formula units** and **conditional units** all use the same small
  expression language: arithmetic, comparison, boolean operators, the ternary conditional, a fixed set
  of mathematical functions, numeric and string literals, and references to @Variable and to recorded
  quantities. No attribute access, no indexing into the product, no imports, no function definitions,
  no calls out. It is evaluated by this product's own evaluator - the one that already computes derived
  quantities - and never by a Python interpreter, so it runs identically whether or not scripting is
  enabled. Units follow through an expression: adding metres to seconds is refused, not coerced (INV-002)
- basis: E-065 (T1), E-067 (T2)
- alternatives: allowing Python here is one line of implementation and moves every pipeline into the
  trust decision of XC-102. Both products consulted drew the line in the same place, and one of them
  documents what it costs to have drawn it later
- affects: CT-009, MOD-004, XC-080, XC-102
- decidedness: Fixed
- reversal_trigger: users routinely hitting the limits of the language for legitimate engineering
  arithmetic, which would mean extending the function set rather than opening the evaluator

### XC-102 - Python builds and drives; what is stored is still declarative
- decided: 2026-08-20
- status: active
- decision: a pipeline may be written in Python, and the Python **constructs the pipeline document** -
  the same declarative structure the editor produces (CT-009). Opening a @Workspace never executes
  anything; running a stored pipeline never executes Python. A script is run when a person or an
  authorised agent runs it, and every mutation it makes goes through the one command surface (CT-002),
  so a script's effects appear in the log, undo as one step, and can be dry-run exactly like the
  editor's. Unattended execution - an agent running scripts with no one watching - is **off by default**
  and enabled per workspace, with the same capability limits as user-written selection code (XC-089)
- basis: E-064 (T1), E-065 (T1)
- alternatives: storing the Python itself as the pipeline is simpler and makes every workspace file an
  executable. The application whose data-block format allowed that had to retrofit a preference that is
  off by default, which is the shape of the mistake rather than an argument about it
- affects: CT-009, CT-002, XC-080, XC-089, MOD-013
- decidedness: Fixed
- reversal_trigger: none foreseen; if the declarative document cannot express something the Python
  surface can, the document is extended rather than the boundary moved

**Where this leaves a model.** The assistant's default output stays declarative (XC-080). A model may
also write a script, and the script is shown before it runs; it is not executed as a side effect of
having been asked a question. The difference between a configuration that was validated and code that
ran is the entire security boundary, and it does not become smaller because the author was a model.

Deliberately unlike the reference product: **a script's changes are undoable.** There, operators called
from Python skip the undo stack by default, for performance; here the customer who asks an agent to
build forty reports must be able to undo it in one step (XC-061), so commands issued by a script are
grouped and pushed like any other.

### XC-103 - One naming rule for everything a script can reach
- decided: 2026-08-20
- status: active
- decision: every object a script or an expression can reach - @Case, @Variable, @Template, @View,
  @Graph, @Report, library entry, pipeline - has a **stable identifier** and a **name unique within its
  kind**. Stored references use the identifier, never the name, so renaming rewires nothing. Lookup by
  name resolves to exactly one object or fails with what it found; it never returns a list for the
  caller to index into. A creation or rename that would duplicate a name is **refused with the conflict
  named** rather than silently suffixed
- basis: E-064 (T1), E-067 (T2)
- alternatives: automatic suffixing keeps uniqueness without ever interrupting the user, at the price of
  a name they did not choose and will not find again; the other product consulted allows duplicates and
  its own documentation warns that name lookup is only robust when names happen to be unique, with
  published examples taking the first match and hoping. Refusing is the only one of the three that never
  silently points a reference at the wrong object
- affects: CT-001, CT-008, CT-009, XC-102, MOD-013
- decidedness: Fixed
- reversal_trigger: bulk import routinely colliding, which would need an import-time renaming step the
  user confirms - not a silent rule change

### XC-104 - Generated commentary is checked against a written standard, not against a prompt
- decided: 2026-08-20
- status: active
- decision: the standard a generated passage must meet is specified in
  [14_reporting_standards.md](14_reporting_standards.md) and **enforced after generation**, not merely
  requested before it. Every statement answers four questions - the value, its precision, what is known
  about its error, and where it came from - and every statement carries which of four kinds it is:
  value, computed comparison, cited from reference material, or stated by the user. The language
  categories of E-071 are refused: superlatives, subjective language, ambiguous adverbs, unquantified
  comparatives, loopholes, promotional register. A passage that fails is **rewritten once and then
  omitted**, and the omission is recorded
- basis: E-068 (T1), E-070 (T1), E-071 (T1)
- alternatives: putting the rules in the prompt alone is what everyone does and it fails silently - the
  model complies most of the time, and the failures are exactly the sentences a reader would have
  wanted checked. A prompt cannot be tested; a check can
- affects: CT-006, MOD-006, MOD-008, XC-097, XC-105
- decidedness: Fixed
- reversal_trigger: the check omitting passages a reviewer judges correct, which would mean the check is
  wrong rather than that checking is wrong

**Omission is a correct outcome.** A report that says less and is entirely checkable is worth more than
one that reads well and contains one sentence nobody can trace. The product optimises for the first,
and says how many passages it dropped.

### XC-105 - A model selects citations; it never writes them
- decided: 2026-08-20
- status: active
- decision: every citation in a report resolves to a document the product **retrieved and holds** -
  reference material the user supplied, or a search result the user permitted. The model is given a
  list of what is available and selects from it by identifier; it is never permitted to emit a
  reference as text. A statement whose support is not in that list is omitted (XC-104). Every citation
  records what was retrieved, from where, and when
- basis: E-072 (T2)
- alternatives: letting the model write references and checking them afterwards requires resolving
  arbitrary text against the world, which is the problem being avoided rather than a solution to it
- affects: CT-006, MOD-006, MOD-008, XC-013
- decidedness: Fixed
- reversal_trigger: none foreseen

The measurement behind this: in a controlled study, **19.9 percent of a frontier model's citations were
entirely fabricated**, and across thirteen models the rate ran from 14 to 95 percent. The decisive
number is not any of those. It is that fabricated citations were found in about **1 percent of papers
accepted at a major conference after three to five expert reviews each** (E-072). Expert human review is
demonstrably not the control that catches this, so the control has to be mechanical - and the only
mechanical control that works is never letting the reference be free text.

### XC-106 - Reaching the network is a permission, default denied, and visible when used
- decided: 2026-08-20
- status: active
- decision: this product runs fully offline and **searching the web is off by default**. It is enabled
  per @Workspace, and the setting carries: which domains may be reached (an allow-list, empty meaning
  any permitted domain), whether the assistant may search without asking each time, and whether search
  is permitted at all. **The query is data leaving the machine**, so the product shows what it is about
  to send, never includes a value, case name or file path from the workspace unless the user has allowed
  it for that search, and records every request in an audit the user can read and export. Offline is a
  **first-class state**: the interface says what cannot be answered without a search, and produces the
  report without it
- basis: E-001 (T1), E-065 (T1)
- alternatives: a global preference is simpler and wrong - a laptop moves between a customer's isolated
  network and a home connection, and a setting that is not per-workspace is a setting nobody adjusts at
  the boundary that matters
- affects: EXT-008, MOD-014, XC-026, XC-102
- decidedness: Fixed
- reversal_trigger: none foreseen; if search proves essential rather than useful, the default stays and
  the first-run prompt gets clearer

**Why the query and not only the result.** A search for "convergence behaviour of the K7 impeller at
3200 rpm" tells an eavesdropper what is being designed, and no result ever comes back to reveal it.
Products that gate the *response* and not the *request* have the protection backwards.

### XC-107 - Verification, validation and convergence are used in their standard senses or not at all
- decided: 2026-08-20
- status: active
- decision: the product's own text, and any generated passage, uses **verification** only for statements
  about numerical error, **validation** only where measured data is present with its own uncertainty,
  **converged** only with the criterion and its value stated, **grid-independent** only where at least
  three refinement levels exist, and **accurate** only with the bound in the same sentence. Where
  discretisation error has not been quantified the report **states that**, rather than omitting the
  subject. Validation is reported as a quantified model error, never as pass or fail unless the user
  defined the threshold, which is then named
- basis: E-068 (T1), E-069 (T1), E-070 (T1)
- alternatives: leaving the vocabulary loose costs nothing until the report reaches someone who works to
  these standards, at which point it costs the report's credibility entirely
- affects: CT-006, MOD-006, XC-104
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-108 - Shipped samples are generic, and shippable
- decided: 2026-08-20
- status: active
- decision: every sample the product ships - report and view and graph @Template, materials, fonts,
  backgrounds, colour maps - is **generic**: no customer's branding, no single organisation's house
  format, no assumption about which solver produced the data. Report templates cover the common shapes,
  including a **journal-paper format**, a technical memorandum, a one-page summary, a design-review
  deck and a cross-case comparison. Every sample is redistributable under terms this product can ship
  (XC-085); a sample that cannot be shipped is not a sample, and a placeholder is preferable to an asset
  with unclear terms. The material samples are organised by **engineering material** - steel, aluminium,
  polymer, glass, composite - each paired with a colour map suited to the quantities usually shown on
  it, so that applying a material to a mesh is one drag rather than a session of parameter tuning. The shipped set also includes **generic reference material on reporting practice**
  - a digest of [14_reporting_standards.md](14_reporting_standards.md) and the sources behind it - so
  that commentary has something to be grounded in on a machine that will never be allowed to search
- basis: E-001 (T1), E-062 (T1)
- alternatives: shipping richer, more specific samples demonstrates the product better and makes the
  first thing every user does a deletion
- affects: CT-008, GL-019, MOD-006, XC-085
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-109 - Workspace artefacts and reusable templates are distinct
- decided: 2026-08-21
- status: active
- decision: a @Workspace owns multiple concrete @View, @Graph, @Report and simulation definitions,
  shown as lists of working artefacts rather than as templates. None is owned by a @Case. A @Template
  is a separate reusable blueprint, in workspace or shared @Library scope. Applying one creates a new
  independent workspace artefact by default; saving an artefact as a template copies its current
  definition into a new template revision. Editing either side later does not silently change the
  other. The Japanese interface labels the concrete collections `ビュー一覧`, `グラフ一覧` and
  `レポート一覧`, and reserves `テンプレート` for the reusable library. Live template linkage is
  outside r1 and, if added, must be explicit and visible
- decided_by: the product owner, 2026-08-21, after comparing the unified-template model with common
  report, document and workbook conventions
- correction: this supersedes the 2026-08-20 form of XC-109, which said the definition itself was the
  template. The shared definition schema remains; the product model and interface no longer collapse
  the working artefact and its reusable source into one object
- alternatives: calling every working artefact a template keeps one stored object but makes ordinary
  switching, editing and pipeline references ambiguous to users. Per-case artefacts remain rejected:
  the workspace owns each artefact and case selection is an argument or an explicit binding
- basis: E-088 (T1)
- affects: GL-008, GL-010, GL-015, GL-017, CT-001, CT-004, CT-005, CT-006, CT-008, CT-009, MOD-007
- decidedness: Fixed
- reversal_trigger: representative users consistently understand a unified definition/template object
  better and can predict edit propagation and pipeline behaviour without explanation

**Editing a view while looking at case B edits that workspace view**, so case A shows the edited view
when the same view is used there. It does not edit the template from which the view was created. A
deliberate `Save as template` action creates or revises a reusable blueprint.

### XC-110 - The locale formats what a person reads, and nothing else
- decided: 2026-08-20
- status: active
- decision: displayed numbers follow the interface language - decimal separator, digit grouping, date
  format. **Machine-readable output does not** (INV-018): CSV, JSON, script text and file names use a
  period and no grouping in every locale. Where a file is written for a person to read as well as a
  machine - a CSV opened in a spreadsheet - the product states which convention it used, in the file
- basis: E-001 (T1)
- alternatives: following the locale everywhere is what spreadsheet software does and is why a European
  colleague's export silently changes a value by a factor of a thousand
- affects: INV-018, CT-006, MOD-010
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-111 - The default colour map is perceptually uniform
- decided: 2026-08-20
- status: active
- decision: the default colour map for scalar data is **perceptually uniform** (a viridis-class map).
  Rainbow and jet remain available, because existing documents use them and a result that cannot be
  compared to last year's report is a result nobody trusts - but selecting one **records a note on the
  view and in any report using it**, stating that the map is not perceptually uniform. Colour maps do
  not follow the interface theme (XC-098)
- basis: E-001 (T1)
- alternatives: removing rainbow entirely is the technically correct choice and makes the product
  unusable next to a decade of existing reports
- affects: GL-018, CT-004, XC-098
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-112 - One window in the first release
- decided: 2026-08-20
- status: active
- decision: the first release runs in **one window**. A @View cannot be detached to a second monitor.
  Comparison across cases is met by the split layout of the view area (view/REQ-009) rather than by a
  second window
- basis: E-001 (T1)
- alternatives: detachable windows are what a dual-monitor user asks for first and they multiply every
  state question - which window owns the selection, what a modal blocks, where a run's progress appears
- affects: MOD-009, XC-060
- decidedness: Fixed
- reversal_trigger: the split layout proving insufficient for side-by-side work, which is a measurable
  complaint rather than a guess

### XC-113 - Where output goes, and what it is called
- decided: 2026-08-20
- status: active
- decision: artefacts are written under the @Workspace's own folder, at
  `output/<pipeline or report name>/<run timestamp>/<case name>/`, and **a run never overwrites an
  earlier run** - it writes a new timestamped folder. The name pattern is editable per pipeline or
  report, may reference @Variable, and a pattern that would collide within one run is refused before the
  run starts rather than resolved by silently appending a number
- basis: E-001 (T1)
- alternatives: writing beside the source data spreads a study across the disk; overwriting saves space
  and destroys the comparison the user was making
- affects: CT-006, CT-009, MOD-006, MOD-011
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-114 - Accessibility: what is committed, and what is not
- decided: 2026-08-20
- status: active
- decision: the first release commits to **full keyboard operation**, the contrast level of XC-022, and
  colour maps that do not rely on hue alone to be read (XC-111). It does **not** commit to screen-reader
  support: a 3D scene and a colour-mapped field have no meaningful reading, and a partial implementation
  would claim an accessibility it does not have
- basis: E-001 (T1)
- alternatives: claiming screen-reader support and delivering it for the panels only is worse than
  saying plainly what is and is not covered
- affects: XC-022, XC-098, MOD-010
- decidedness: Fixed
- reversal_trigger: a customer requirement to meet a specific procurement standard, which would define
  the scope rather than leave it to be guessed

### XC-115 - Deep research is a separate permission with a stated cost
- decided: 2026-08-20
- status: active
- decision: the chat area works like a conversation - it may search the web, run **deep research**, and
  the model and its effort level are chosen there. Deep research is a **separate toggle** from ordinary
  search, because it makes tens of requests and consumes tokens in a different order of magnitude, and
  it states **how many requests it intends and the estimated cost** before starting. Both ride on the
  permission of XC-106: search off by default, per @Workspace, host allow-list, query shown, every
  request audited. **Chat is not an exception to any of it** - an exception in chat is a hole in the
  guarantee an isolated site was given
- basis: E-001 (T1)
- affects: EXT-006, EXT-008, MOD-008, MOD-014, XC-106
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-116 - One model setting for the product, overridable for reports
- decided: 2026-08-20
- status: active
- decision: the model and its effort level are **one setting for the product**, changeable in chat for
  the current conversation, with **report generation able to override both** - a report has a different
  quality requirement and a different cost profile from a question in chat. The available models are
  **read from the provider** rather than compiled in, so a new model appears without an update; an
  unavailable model is reported by name and the previous choice is kept
- basis: E-006 (T1)
- alternatives: a per-feature model setting is more flexible and turns "why did this come out worse
  today" into an unanswerable question across four settings nobody remembers changing
- affects: EXT-006, MOD-008, XC-104
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-117 - Inheritance is decided per variable, and an inherited variable is read-only in the child
- decided: 2026-08-20
- status: active
- decision: each @Variable on a child @Case is in one of two states, chosen **per variable**:
  **inherited** - the child shows the parent's value, cannot edit it, and follows every change the
  parent makes - or **independent**, where the child holds its own value and the parent's changes do
  not reach it. Switching a variable from inherited to independent takes the current value as its
  starting point and says so. A child may **add** variables the parent does not have; it may not
  **delete** one the parent defines
- decided_by: the product owner, 2026-08-20
- correction: an earlier version described this as "inherited unless overridden", where a child could
  always type a new value and thereby detach silently. That makes detachment an accident: the user
  changes one number to try something, and three months later the parent no longer drives that child
  and nothing on screen said so. Detaching is now a deliberate act with a name
- basis: E-001 (T1)
- affects: GL-004, CT-001, MOD-007, XC-088
- decidedness: Fixed
- reversal_trigger: users detaching so routinely that the extra step is friction, which would mean the
  default state for a new child variable is wrong rather than the lock

### XC-118 - A report may span workspaces; a workspace still opens alone
- decided: 2026-08-20
- status: active
- decision: a @Report definition may name **several @Workspace** as its sources, so that a comparison
  across studies is one document. The report records which workspace each value came from, and a
  workspace referenced but not present is reported as unavailable with the report still produced from
  the rest. **This does not make workspaces depend on each other**: the reference is held by the report,
  resolved when it runs, and a workspace remains openable and complete on its own (CT-001)
- basis: E-001 (T1)
- alternatives: copying cases between workspaces to build a comparison is what users do without this,
  and it duplicates data that then drifts from its source
- affects: CT-006, MOD-006, MOD-007, GL-010
- decidedness: Fixed
- reversal_trigger: cross-workspace reports proving unusable because the workspaces move on disk, which
  would need a resolution rule rather than removal

**Every value still names its workspace.** A number in a cross-workspace report that does not say which
study it came from is worse than no comparison at all - and this is exactly where the provenance rule
(INV-013) earns its cost.

### XC-119 - Background: the rules are settled, the set of kinds is not
- decided: 2026-08-20
- status: active
- decision: **which background kinds ship is decided during implementation** (OPEN-016). Candidates are
  a solid colour, a single image, an HDRI environment, a 3D Gaussian splat scene (XC-043) and imported
  3D models placed as props, and the set may end up smaller or differently divided. What is settled, and
  holds whichever kinds exist: a background is **appearance and never touches a value** (INV-002); its
  cost is **stated before it is applied**, not discovered afterwards; and **result geometry is never
  reduced to make room for it** (LIM-009)
- decided_by: the product owner, 2026-08-20 - the kinds are to be chosen against what the renderer
  actually does with them rather than against a list written in advance
- basis: E-001 (T1)
- affects: CT-004, GL-018, LIM-009, MOD-003, OPEN-016
- decidedness: Bounded
- reversal_trigger: not applicable to the set of kinds, which is expected to change; the three rules
  above reverse only if a background is ever allowed to change a reported number, which would be a
  different product

**Why the rules are Fixed while the list is Open.** The rules are what a user is entitled to rely on -
that a prettier picture is not a different measurement, and that the tool does not quietly trade the
result's fidelity for scenery. None of that depends on whether splat scenes make the cut. Writing the
list down first would have been the part with no evidence behind it.

### OPEN-016 - Which background kinds ship
- question: which of solid colour, image, HDRI environment, splat scene and prop models are worth
  their implementation and performance cost, and whether the divisions are the right ones
- blocks: nothing. The rules that constrain any background are settled (XC-119), the budget exists
  (LIM-009), and a kind can be added at the same seam as any other asset
- resolve_by: implementation - measured against what the renderer does with each kind on the hardware
  class of E-063, not against a list decided beforehand
- decidedness: Open

### XC-120 - Tags are proposed automatically and confirmed by a person
- decided: 2026-08-20
- status: active
- decision: on import, tags are **proposed** from what can be read - solver, mesh size, which variables
  differ from siblings, file dates - and, where a model is configured, from the case's own naming. They
  are proposals: nothing is applied until accepted, in one action for a whole import. A rejected
  proposal is not offered again in the session (XC-081)
- basis: E-001 (T1)
- alternatives: applying tags automatically saves a click and produces a filter that quietly hides a
  case the user was looking for
- affects: MOD-007, MOD-008
- decidedness: Bounded
- reversal_trigger: none foreseen

### OPEN-015 - How much variation one workspace should span
- question: a @Workspace holds one investigation. Nobody would put a structural study and a fluid study
  in one - but where between "the same model at five inlet velocities" and "two unrelated analyses" does
  the boundary fall? It decides whether @Variable, tags and the quantity list stay comprehensible, and
  whether a @Template can be assumed to apply to every @Case in the workspace
- blocks: nothing today - the product does not enforce a boundary, and templates already report what
  they cannot resolve. It becomes urgent if the product ever starts assuming homogeneity for speed
- resolve_by: the first two real studies a customer keeps side by side
- decidedness: Open

### XC-121 - The derived-quantity catalogue is fixed, and its conventions are the field's
- decided: 2026-08-20
- status: active
- decision: the quantities this product derives are the catalogue of
  [15_derived_quantities.md](15_derived_quantities.md), with component order **XX, YY, ZZ, XY, YZ, XZ**
  and principal values **ordered largest to smallest**, matching the reference implementation (E-073).
  Each is computed in the analysis module and carries its formula (INV-020). Anything outside the
  catalogue is a user's @Expression and is shown wherever it appears
- basis: E-073 (T1)
- alternatives: computing whatever a user asks for through a general tensor algebra is more powerful and
  removes the one property that makes these values checkable - that the reader knows exactly which
  formula produced them
- affects: GL-032, INV-020, MOD-004, XC-101
- decidedness: Fixed
- reversal_trigger: a quantity engineers need routinely that the catalogue lacks, which is an addition
  rather than a change of approach

### XC-122 - Components are reported in named frames, never in an assumed one
- decided: 2026-08-20
- status: active
- decision: the default @Component frame is global Cartesian and is **named on every component**.
  Cylindrical, spherical and local frames are defined on the @Workspace with an origin and orientation
  and referenced by name. A component whose frame cannot be resolved is refused (INV-021). A frame
  change is a change to reported numbers and is recorded as such
- basis: E-073 (T1)
- affects: GL-033, INV-021, CT-004, MOD-004
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-123 - This product does not inherit the toolkit's averaging default
- decided: 2026-08-20
- status: active
- decision: cell-to-point conversion happens only on request (INV-003), never averages across a @Part or
  material boundary (INV-022), and labels its output as averaged. Integration-point values written by a
  solver are read as written; **this product does not extrapolate them to nodes**, because the
  extrapolation depends on the element formulation and the file does not carry it
- basis: E-074 (T1)
- alternatives: matching the reference default makes numbers agree with the other tool, including where
  the other tool is averaging across a material interface. Agreeing with a known hazard is not
  compatibility, and the difference is reported rather than hidden: where this product declines to
  average, it says so, which is what lets someone reconcile the two
- affects: INV-022, MOD-002, MOD-004, XC-121
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-124 - Identifiers are the file's, using the types the domain already has
- decided: 2026-08-20
- status: active
- decision: numeric **global identifiers** and optional **pedigree identifiers** are preserved from the
  source (E-075), shown with extreme values, and used to match locations between cases on the same mesh.
  Where a file has none, the product says so rather than substituting an index (INV-023)
- basis: E-075 (T1)
- affects: GL-034, INV-023, MOD-002, CT-006
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-125 - Measured data is data, not reference material
- decided: 2026-08-20
- status: active
- decision: measured values are imported **against a @Case** as @Measurement data, each able to carry
  its own uncertainty, and are a legitimate source of numbers. @Reference material remains documents
  only and may never supply a value (XC-013)
- decided_by: the product owner, 2026-08-20
- correction: the specification required measured data with its own uncertainty before the word
  **validation** could be written (XC-107), while providing no way to import a measured value and
  explicitly forbidding reference material from supplying one. As written, validation could never be
  reported. This closes that
- basis: E-070 (T1)
- affects: GL-035, GL-012, XC-107, XC-013, MOD-002
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-126 - Logs stay local, and a support bundle is assembled in the open
- decided: 2026-08-20
- status: active
- decision: logs are written locally, carry **no field values**, and are never sent anywhere on their
  own. A support bundle is assembled on request, **lists everything it contains before it is created** -
  including any case name or file path - and leaves the machine only through the egress module with the
  user's explicit consent, recorded in the same audit as every other outbound request (XC-106)
- basis: E-001 (T1)
- alternatives: automatic crash reporting produces better diagnostics and sends a customer's part names
  to a third party without anybody deciding to
- affects: MOD-014, XC-106, XC-026
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-127 - Keyboard reach and command reach are the same claim, and both are checked
- decided: 2026-08-20
- status: active
- decision: the keyboard scheme is written down in [11_ui.md](11_ui.md) rather than emerging per panel,
  and **a gate checks that every operation of CT-003 appears in the command surface of CT-002 and that
  every interface action dispatches a command** - the mechanism INV-006 has been asserting in prose. The
  gate reports what it checked and what it could not, so an unimplemented half never reads as a pass
- basis: E-001 (T1)
- alternatives: leaving it to review is what turns "every command is reachable" into a claim nobody has
  tested and nobody can test later
- affects: INV-006, CT-002, CT-003, MOD-002, XC-102
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-128 - The headless product authenticates before it does anything
- decided: 2026-08-20
- status: active
- decision: the requirements for the command-line and hosted forms are fixed now even though the
  implementation is later (XC-091): **authentication is required**, authorisation is **per @Workspace**,
  every operation is audited with the identity that issued it, and the default for an unknown caller is
  **refusal**. An agent driving the product is a caller like any other and gets no implicit trust
- basis: E-001 (T1)
- alternatives: adding access control to a working headless product later means retrofitting identity
  through every command, which is the retrofit that historically does not get done
- affects: MOD-013, MOD-014, CT-002, XC-102
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-129 - First run opens a View, and the tutorial points at the interface
- decided: 2026-08-20
- status: active
- decision: the product starts in the **View area**, showing either a shipped **sample @Workspace** or an
  empty one - whichever the user chooses at first start, with the sample offered first. The sample's data
  is **generated by this project**, not third-party CAE data, so it can be shipped (XC-085). A first
  tutorial runs over the real interface, **pointing at the control to use** and advancing as the user
  uses it, and it can be dismissed and resumed
- decided_by: the product owner, 2026-08-20
- basis: E-001 (T1)
- alternatives: an empty product with documentation is cheaper and leaves a first-time user with a blank
  canvas and a file dialogue, which is where trials end
- affects: MOD-009, XC-085, XC-108
- decidedness: Bounded
- reversal_trigger: none foreseen

### XC-130 - A shipped sample never overwrites the copy someone made from it
- decided: 2026-08-20
- status: active
- decision: when an update ships a changed sample, the new version appears **alongside**; copies a user
  made keep working untouched. A copy that records the sample as its origin shows that a newer version
  exists, and adopting it is the user's action
- basis: E-001 (T1)
- affects: CT-008, XC-108
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-131 - Results are indexed by an axis, which is not always time
- decided: 2026-08-20
- status: active
- decision: a @Case carries a @Result axis - none for steady, **time**, **mode number** with
  eigenfrequency, or **frequency with a phase angle** - and @Current time step is the position on
  whichever axis it has. A **complex result** keeps its real and imaginary parts together, with
  **amplitude** and **value at a phase** added to the derived-quantity catalogue (GL-037). Following the
  established tool, frequency and phase are **swept one at a time**: one is fixed while the other
  advances, and which is which is stated (E-076). A @Graph or @Report that would mix results from
  different axes must say so; it never places a mode index and a time on one axis silently
- basis: E-076 (T2)
- alternatives: treating everything as "time steps", which is what the file formats often do, is less
  work and puts "mode 3" and "t = 3 s" in the same column
- affects: GL-036, GL-037, CT-004, CT-005, MOD-002, MOD-004, XC-121
- decidedness: Fixed
- reversal_trigger: a result kind that fits none of the four, which would be an addition to the axis
  set rather than a change of approach

### XC-132 - Deformation is drawn at true scale by default, and the factor is in the picture
- decided: 2026-08-20
- status: active
- decision: the default @Deformation scale is **1.0**. Auto-scaling is offered as one action, with the
  same presets the established tool uses, and **the factor is drawn into the view and into every export**
  rather than only into a toolbar (INV-024). Measurements are taken on undeformed canonical coordinates
  unless the deformed configuration is explicitly asked for, and are labelled when it is
- basis: E-077 (T2)
- alternatives: defaulting to auto-scale is what the established tool does and is better for seeing a
  small deflection immediately. It also produces the recurring question in that vendor's own knowledge
  base - why the plot does not measure against the ruler - which is a user discovering, after the fact,
  that the picture was not the shape. This product takes the extra click
- affects: GL-038, INV-024, CT-004, MOD-003
- decidedness: Fixed
- reversal_trigger: users auto-scaling on nearly every view, which would argue for offering it at import
  time rather than for making it the silent default

### XC-133 - A seeded, integrated picture is a computation and is recorded as one
- decided: 2026-08-20
- status: active
- decision: streamlines and particle traces record seed source, integrator, step size, step limit and
  termination in the @View definition, regenerate identically from it, and are labelled **derived
  visualisation** wherever they appear beside measured quantities (INV-025)
- basis: E-078 (T1)
- affects: GL-018, INV-025, CT-004, MOD-003
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-134 - Display units are presentation, chosen per quantity
- decided: 2026-08-20
- status: active
- decision: a @Display unit is chosen **per quantity** on the @Workspace - length in millimetres, stress
  in megapascals - and applies wherever that quantity is shown, always beside the value. Storage and
  computation stay canonical (INV-026). A machine-readable export **states the unit it wrote**; it does
  not leave the reader to infer it. Conversion uses declared units only and refuses where none is
  declared (XC-003)
- basis: E-001 (T1)
- affects: GL-040, INV-026, CT-001, MOD-001, XC-110
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-135 - A deliverable knows what it was made from
- decided: 2026-08-20
- status: active
- decision: an exported @Report records the content identity of every input dataset and the @Workspace
  version it was produced from, and the product can state whether a given deliverable was produced from
  data that has since changed (INV-027). This is **not** a claim that the document updates itself: it is
  the difference between a stale document and one nobody can classify
- basis: E-001 (T1)
- affects: INV-027, CT-006, MOD-006
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-136 - A case has states, and they are the ones everything branches on
- decided: 2026-08-20
- status: active
- decision: a @Case is in exactly one of **unresolved, unloaded, loading, loaded, partial, failed**.
  Loading moves unloaded to loading to loaded or partial or failed; a missing or changed input file
  moves any state to unresolved; a clear unit moves loaded or partial back to unloaded (XC-099). The
  case tree shows the state, and the @Pipeline decides what to skip from it rather than from an
  ad-hoc check
- basis: E-001 (T1)
- alternatives: leaving the states implicit is what the specification did until now, and it meant the
  interface, the pipeline and the report each decided separately what "not ready" meant
- affects: GL-039, CT-001, CT-009, MOD-007, MOD-011
- decidedness: Fixed
- reversal_trigger: a state that is genuinely two states, which is an addition rather than a redesign

### XC-137 - Latency has budgets, and they are measured before they are promised
- decided: 2026-08-20
- status: active
- decision: two budgets exist - **time to first rendered result** from launch on the sample workspace,
  and **selection to reflected change** when a @Case is selected. Both are recorded as limits and both
  are **Open until measured on the hardware class of E-063**, in keeping with this project's rule that a
  number nobody measured is not a limit
- basis: E-063 (T1)
- affects: LIM-010, LIM-011, OPEN-017, MOD-009
- decidedness: Bounded
- reversal_trigger: none foreseen

### XC-138 - The assistant is measured, or its quality is a matter of opinion
- decided: 2026-08-20
- status: active
- decision: an **evaluation set** is kept and run in the build: recorded instructions with the commands
  they should produce, recorded datasets with the proposals that are acceptable, and passages with the
  verdicts the checker of XC-104 should reach. A pass bar is stated. Changing the model (XC-116) or the
  prompt re-runs it, so a regression is visible rather than reported by a customer months later
- basis: E-001 (T1)
- alternatives: judging the assistant by trying it is how every model change becomes an argument nobody
  can settle
- affects: MOD-008, XC-104, XC-116
- decidedness: Bounded
- reversal_trigger: none foreseen

### OPEN-017 - What the latency budgets should be
- question: how long may launch-to-first-result and selection-to-reflection take before the product
  feels broken, on the hardware class of E-063
- blocks: nothing today; the budgets exist as limits and are enforced once numbered
- resolve_by: measurement on the sample workspace, once there is an interface to measure
- decidedness: Open

### XC-139 - What the model is told about the product is generated, never written by hand
- decided: 2026-08-20
- status: active
- decision: the capability description a language model receives - the operations it may call, their
  parameters and what each returns - is **generated from CT-002 and CT-003**, not maintained as prose
  beside them. What it is given about the workspace is a **summary**: the case tree, the quantity list
  with units and @Provenance, the templates available, and the states of things - never bulk numeric
  data (XC-097). The glossary terms it uses are the ones in [00_glossary.md](00_glossary.md), so the
  words in a generated report are the words in the interface
- basis: E-001 (T1)
- alternatives: a hand-written description of the product is what everyone starts with, and it drifts
  from the command surface within one release. Then the model calls an operation that no longer exists,
  or never learns about one that does, and the failure looks like the model being poor
- affects: CT-002, CT-003, MOD-008, XC-104, XC-116, XC-138
- decidedness: Fixed
- reversal_trigger: none foreseen

**This is the same rule as everything else here**, applied to the model: one definition, generated
outward. It is also what makes the evaluation set of XC-138 meaningful - a regression is then in the
model or the prompt, never in a description that quietly went stale.

### XC-140 - A workspace can be packed, with its data, and opened by someone who has neither
- decided: 2026-08-20
- status: active
- decision: a @Workspace exports as a **pack** - the document, its workspace-scoped templates and
  assets, and, at the user's choice, the **input data files it references**. The pack states its size
  before it is written, lists what it contains, and **names anything it could not include** - a linked
  reference folder, an asset whose licence forbids redistribution (XC-085). Opening a pack recreates the
  workspace with its files beside it; opening one without data recreates it with every @Case in the
  unresolved state (XC-136) rather than appearing to work
- basis: E-001 (T1)
- alternatives: sending the workspace document alone is what happens today and produces a file that
  opens to a tree of cases pointing at paths on somebody else's machine
- affects: CT-001, CT-008, MOD-007, XC-136
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-141 - Output accumulates, so it is bounded and pruned on purpose
- decided: 2026-08-20
- status: active
- decision: every @Pipeline run writes a new timestamped folder and never overwrites an earlier one
  (XC-113), which means output grows without limit. The product therefore **reports how much space a
  workspace's output occupies**, and offers pruning **by run**, oldest first, always naming what would
  be deleted and never touching input data or the run records themselves - a deleted artefact stays
  reproducible because the record of how it was made survives (XC-046)
- basis: E-001 (T1)
- alternatives: automatic deletion after a period is what a service would do and is wrong here: the
  artefact somebody is about to send to a customer has no way to announce itself
- affects: LIM-012, CT-009, MOD-011, XC-113
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-142 - Recorded times are UTC, with the local offset kept beside them
- decided: 2026-08-20
- status: active
- decision: every timestamp this product stores - run records, audit entries, retrieval dates,
  deliverable provenance - is written in **UTC**, with the **local offset at the moment of writing**
  recorded alongside. Timestamps are **displayed** in the reader's own zone
- rationale: a study run in two offices, or across a daylight-saving change, produces run records that
  cannot be ordered if each carries only a local time. Keeping the offset as well means the local moment
  is still recoverable, which is what somebody reconstructing what happened actually wants
- basis: E-001 (T1)
- affects: CT-009, CT-010, CT-006, XC-046
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-143 - Dataset structure belongs in a View Outliner
- decided: 2026-08-21
- status: active
- decision: the selected @Dataset's file-authored components do not appear in the left sidebar. In the
  View area they appear in an @Outliner at the top of the right sidebar. Its visual and interaction
  grammar follows Blender: a hierarchy of rows with disclosure triangles, type icons, source names,
  synchronized selection, search and filter, and right-edge visibility controls. SOLVIA does not copy
  Blender's scene-editing commands: r1 cannot rename, reparent, delete or otherwise edit analysis
  geometry through the Outliner. A source with no hierarchy stays flat and is labelled as such. The
  header does not carry a static `Dataset` selector: it names no actual scope, while the exact dataset
  root already owns the first tree row
- basis: E-079 (T1), E-080 (T1)
- alternatives: keeping parts in the left sidebar mixes workspace navigation with the internal
  structure of one rendered dataset; inventing a SOLVIA-specific tree discards an established 3D-tool
  interaction language without gaining a product-specific capability
- affects: GL-042, INV-019, CT-003, view/REQ-012, 11_ui.md
- decidedness: Fixed
- reversal_trigger: analysis components become a cross-area subject independently selectable from a
  View, rather than structure used to inspect and control the rendered dataset

### XC-144 - The established SOLVIA shell remains the visual source
- decided: 2026-08-21
- status: active
- decision: `cae-saa-s` owns the shell's visual language: light neutral sidebars, compact two-row top
  bar, conventional application menus, workspace/workspace-list segmented navigation, panel controls
  at the far left and right of the work toolbar, and the searchable thumbnail-card workspace list. In
  the design mockup its card images use the retained `cae-saa-s/public/thumbnails` raster fixtures in
  the same 4:3, cover-filled viewport; browser-default desktop layout shows four cards on one row, and
  they remain visibly identified as unconnected reference artwork.
  The design mockup also reuses the retained viewport's interaction composition through an interactive
  Three.js placeholder in every populated View pane: orbit, zoom, fit, auto-rotation, representation
  modes, grid and orientation gizmo. It is explicitly not the vtk.js product-renderer decision of
  XC-044 and carries no invented analysis value, unit, metadata or provenance. Its Canvas has no
  decorative outer frame or duplicate status footer.
  Blender supplies the @Outliner interaction grammar through XC-143, not a dark Blender colour theme.
  In the design mockup its source names use 10 px type in 27 px rows, with separate light-neutral
  header, tools and tree surfaces and a pale-blue selected row carrying a left accent. The tree has no
  persistent `Shift`/`Ctrl` shortcut footer; that space remains available to source rows.
  Generic headings that only restate location, including `View objects`, `Simulation items`, `Graph
  items` and `Report items`, are absent; a non-View right sidebar begins with its functional tabs.
  Sections are named by their actual function. Sidebars never repeat the panel toggles already fixed to
  the work toolbar.
  The left sidebar also omits the redundant `Workspace`/`Conversation` plus-button title row: the shell
  is already inside one workspace, and new-workspace creation belongs to Workspace list. The reference
  mockup's `Case list` label is corrected to `Workspace list`
- basis: E-080 (T1)
- alternatives: replacing the retained shell with a second art direction loses a user-selected asset;
  retaining `Case list` gives a workspace card collection the wrong domain meaning; duplicate panel
  buttons obscure which control owns visibility, while an in-workspace plus button suggests the wrong
  creation scope
- affects: 11_ui.md, workspace/REQ-017, view/REQ-009
- decidedness: Fixed
- reversal_trigger: the owner selects a different shell as the product's visual source

### XC-145 - View navigation is one upper-right cluster
- decided: 2026-08-21
- status: active
- decision: in each populated View pane, display/representation controls occupy the upper-right row
  and the interactive XYZ orientation gizmo is placed directly beneath them, right-aligned with the
  same inset. This follows the upper-right navigation convention used by Blender and Maya while
  preserving SOLVIA's existing control styling. The gizmo remains below the icons in split panes and
  does not return to the lower-right corner; its compact size preserves a visible gap below the icon
  row without clipping its axis heads, but shall not shrink the head circles or their X/Y/Z letters
  below easy recognition at browser-default zoom
- basis: E-080 (T1), E-081 (T1), E-082 (T1)
- alternatives: a lower-right gizmo separates orientation from the controls that change the viewport
  and competes with status and timeline overlays; putting it on the same row as representation icons
  causes overlap first in split views
- affects: 11_ui.md, view/REQ-009
- decidedness: Fixed
- reversal_trigger: the product adopts a different complete viewport interaction system whose own
  navigation convention requires another location

### XC-146 - Editing sections use a labelled vertical icon rail
- decided: 2026-08-21
- status: active
- decision: every non-chat right sidebar replaces its horizontal text-tab strip with a compact
  vertical icon rail on the left of the editing region. The selected section's Japanese name remains
  visible by itself in a sticky content header, and every icon exposes the same name on hover, keyboard
  focus and to assistive technology. The header does not repeat the selected work-area name above it.
  Selection uses an accent bar, colour and surface treatment rather than
  colour alone. View keeps its Outliner full-width above the rail. Shared sections keep one icon and
  relative ordering across work areas, and the rail supports ArrowUp, ArrowDown, Home and End
  keyboard movement. Within View, `全体`, `描画`, `背景` and `出力` form the first whole-View group;
  one quiet separator, hidden from assistive technology and excluded from focus, precedes the active-object group ordered `オブジェクト`,
  conditional `テキスト`, then `マテリアル`. This remains one tablist and one arrow-key sequence.
  Accessible names include the scope while tooltips retain the concise tab name
- decided_by: the product owner, 2026-08-21, after reviewing the horizontal icon-strip and
  Blender-derived alternatives, with the two View scopes and their grouping confirmed on 2026-08-22
- basis: E-083 (T1), E-084 (T1)
- alternatives: horizontal text tabs become scroll-dependent at the seven View sections; horizontal
  icon-only tabs fit today but repeat the same limit as sections grow. Copying Blender's unlabeled
  rail exactly is denser but asks analysis engineers to learn abstract icons such as Template and
  Output before they can navigate
- affects: 11_ui.md, workspace/REQ-017, view/REQ-012
- decidedness: Fixed
- reversal_trigger: representative analysis engineers complete section-finding tasks faster and with
  fewer wrong selections using a horizontal labelled pattern, or the editing panel becomes too narrow
  for its controls after reserving the rail width

### XC-147 - Material-library categories share one searchable and sortable composition
- decided: 2026-08-21
- status: active
- decision: the centre-bottom material library uses one composition for View's Template, Object,
  Material, Background and Font categories; Graph's Template, Style and Font; and Report's Template,
  Layout, Style and Font. Immediately below the selected category, Sample and Original appear as
  horizontal peer tabs; one primary text search, a compact Tag filter trigger and a compact sort
  button follow; the remaining region shows results or an explicit icon-labelled empty/no-match state
  named for the selected section. The Tag trigger opens a filterable
  multi-select suggestion list populated only from tags present in the selected source and scope, and
  selections remain visible as removable chips. Sort offers Default, Name ascending and Name
  descending; it does not invent update, popularity or analysis metadata. Tag and sort popovers do not
  remain open together. The mockup does not invent catalogue entries or tag suggestions. Simulation
  has no material library because its solver workflow is distinct
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1), E-085 (T1), E-086 (T1), E-087 (T1)
- alternatives: area-specific arrangements make the same library operation move between modes;
  putting source selection in the right property rail confuses reusable-resource browsing with current-state editing;
  two equal always-visible search fields spend scarce sidebar height and give tag vocabulary the same
  free-text affordance as template content; a wide labelled sort control unnecessarily reduces the
  primary search field; showing fabricated sample cards, tag suggestions or unsupported sort fields
  makes unavailable content look implemented
- affects: 11_ui.md, workspace/REQ-017
- decidedness: Fixed
- reversal_trigger: one of the named library categories gains a materially different retrieval workflow

### XC-148 - Work-area headers create named workspace items, not templates
- decided: 2026-08-21
- status: active
- decision: the persistent header at the top of Simulation, View, Graph and Report shows the current
  workspace artefact and exactly one type-specific primary action: `＋ 新規シミュレーション`,
  `＋ 新規ビュー`, `＋ 新規グラフ` or `＋ 新規レポート`. It does not use the ambiguous generic label
  `＋ 新規作成` and does not show `テンプレート` or `テンプレートとして保存`. Simulation remains the
  later-release external-solver-driving feature of XC-091, so the r1 unavailable state must not claim a
  definition was created. Template discovery remains in the centre-bottom material library; saving an
  existing item as a template remains a secondary item command and shall not return as a persistent
  header button
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1), E-088 (T1)
- alternatives: keeping both template buttons in the header duplicates the right-sidebar library and
  makes the current workspace item look like a template; removing all actions makes the common act of
  adding a second View, Graph or Report unnecessarily indirect
- affects: 11_ui.md, workspace/REQ-017
- decidedness: Fixed
- reversal_trigger: usability testing shows that creation belongs in the item list itself and the
  header action causes repeated accidental blank items
  that cannot retain the common source, search, tag, sort and result hierarchy

### XC-149 - Reusable resources use a bottom shelf; the right side edits current state
- decided: 2026-08-21
- status: active
- decision: View, Graph and Report place their reusable-resource browser in a collapsible material
  library docked to the bottom of the centre column, immediately above the persistent instruction bar.
  Its top bar is labelled only `素材ライブラリ` in collapsed and open states. A compact chevron sits
  immediately after the title, pointing up to expand while collapsed and down to collapse while open;
  it is not detached at the row's far edge. When open, category tabs share that row, and
  Sample/Original, search, Tag and sort share the next row. The whole collapsed bar
  opens it by pointer or keyboard; the whole open bar closes it except that category tabs and the
  top-edge resize splitter performs its own action without closing. It opens to one complete thumbnail
  row and may be resized to multiple
  complete rows without reducing the right property editor's height. At narrow widths an open shelf
  overlays the lower centre canvas as a bottom drawer. Chat and Simulation show no shelf. Click selects
  and previews; drag applies to a target; an explicit Apply action provides a non-drag path. The right
  vertical rail retains its existing functional sections but removes Sample/Original, search, Tag,
  sort and result browsing; those sections edit the current whole item or current selection. Its former
  Template section is named `全体`, while Template remains a category in the material library. A future
  full Asset Browser owns import, metadata and bulk organisation. Each visible sidebar uses its full
  inner boundary as a horizontal resize splitter, and an open material shelf uses its full top boundary
  as a vertical resize splitter. A splitter is visually the ordinary thin boundary until hover, focus
  or drag, but has a larger transparent hit area. It exposes the WAI-ARIA Window Splitter separator,
  orientation, controlled panel, current value and bounds. All splitters support pointer drag and
  directional arrow keys, stop before the centre becomes unusable, and are absent when their panel is
  hidden. Material-shelf pointer resizing takes the rendered height at pointer-down as its baseline and
  applies pointer displacement directly without a height animation; switching from one-row to expanded
  therefore cannot jump to a previously stored expanded height. Its maximum is the current centre-column
  height minus the rendered persistent bars, capped by the library's own upper bound. The application
  shell and centre column remain viewport-bounded and hide layout overflow, so resizing the shelf cannot
  create application-level vertical scrolling. The
  shelf stays docked to the centre column, so sidebar resizing changes its width rather than giving it
  an independent horizontal extent. There is no corner decoration and no separate one-row/multi-row
  icon after the boundary splitter is available, because the latter control would own the same
  adjustment
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1), E-083 (T1), E-089 (T1), E-090 (T1), E-091 (T1), E-092 (T1), E-093 (T1)
- alternatives: retaining reusable-resource browsing in the right rail conflates browse/apply with
  inspect/edit; a permanently open bottom panel removes too much vertical space from CAE geometry,
  charts and reports; placing the shelf below the instruction bar separates the command entry from its
  target and moves the high-frequency bottom control; a floating-only palette obscures the work surface
  unpredictably; a full Asset Browser is efficient for organisation but too indirect for frequent apply
- affects: 11_ui.md, workspace/REQ-017
- decidedness: Fixed
- reversal_trigger: measured workflows show that resources are applied too rarely to justify a shelf,
  or that users keep it permanently expanded and need a full Asset Browser as the primary surface

### XC-150 - Instruction bar and Chat mode render one conversation
- decided: 2026-08-21
- status: active
- decision: the centre-bottom natural-language instruction bar and full-height Chat mode are two UI
  renderings of one active conversation. They share one conversation identifier, ordered message and
  response history, draft, pending operation, confirmations, failures, activity, model/effort choice,
  search and deep-research permissions, provenance and audit path. Submitting from either surface
  appends exactly one message and produces one result in that same history. Moving between a work area
  and Chat changes only presentation: the compact bar becomes the full conversation or vice versa; it
  never creates, copies, replays or resets a conversation. Selecting another conversation in Chat also
  changes the conversation addressed by the instruction bar. The compact surface may omit full-history
  chrome, but may not own separate behaviour or state
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: an independent quick-command history makes the same prompt appear to vanish on entering
  Chat and creates two places for permissions, errors and audit state; mirroring messages between two
  stores creates duplicate and ordering failure modes without adding user value
- affects: 11_ui.md, assistant/REQ-013, MOD-008
- decidedness: Fixed
- reversal_trigger: a future explicitly named, user-created conversation type has different retention
  or permission semantics and is intentionally shown as separate rather than presented as the same chat

### XC-151 - Work areas reveal the shared conversation in a right overlay drawer
- decided: 2026-08-21
- status: active
- decision: every non-Chat work area keeps the compact instruction bar at centre-bottom while the
  assistant is closed. Opening it replaces that compact composer with a conversation drawer anchored to
  the right edge of the central work surface, immediately left of the existing right properties sidebar.
  The drawer overlays the canvas by default instead of creating a fourth permanent column, so opening a
  conversation does not resize the right properties sidebar or the material library. It renders the same
  ordered conversation as Chat and moves the one composer to the drawer bottom; it never leaves a second
  active input underneath. Closing restores the compact composer with its draft intact. `チャットで開く`
  changes only to the full-height presentation of that same conversation. At narrow widths the drawer may
  cover the available central work surface, but remains dismissible and does not create page overflow
- decided_by: the product owner, 2026-08-21
- basis: E-094 (T1)
- alternatives: replacing the properties sidebar removes the selected-object editor precisely while the
  user is discussing that object; a permanent fourth column makes the CAE viewport too narrow; placing a
  full transcript above or below the canvas competes with the material shelf and result-axis controls;
  duplicating the bottom composer while the drawer is open creates ambiguous focus and submission targets
- affects: 11_ui.md, assistant/REQ-013
- decidedness: Fixed
- reversal_trigger: task observation shows that users must continuously see the complete conversation and
  full-width canvas together, in which case an explicit pinned split-view option may be added

### XC-152 - Graph and Report keep Output last in the property-tab sequence
- decided: 2026-08-21
- status: active
- decision: Graph and Report both expose an `出力` section using the shared File Output icon. It is the
  final tab in keyboard, DOM and visual sequence, using the same spacing as the tab immediately before it;
  it is not detached or anchored to the physical bottom of the vertical rail. Graph Output owns image,
  vector and tabular-data export conditions; Report Output owns document format and delivery conditions.
  Output remains a property section for the current item and does not browse reusable resources
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: placing Output before layout, style or detail obscures the progression from editing to
  delivery; detaching it at the physical rail bottom adds an unintended gap and overstates its difference
  from other property sections; omitting Graph Output forces export settings into unrelated sections
- affects: 11_ui.md, workspace/REQ-017
- decidedness: Fixed
- reversal_trigger: representative workflows show another order reduces wrong section choices or better
  matches the actual editing sequence

### XC-153 - The Graph display has no global Apply button
- decided: 2026-08-21
- status: active
- decision: the central Graph display is the current graph preview and carries no persistent `適用`
  button in its heading. Editing the current Graph remains owned by the right property sections and each
  control's normal interaction, with changes participating in shared Undo; applying a reusable resource
  remains the separate material-library selection/drag/`適用` path, and creating from a Template remains
  an explicit new-item action. Removing the canvas button does not make recommendations auto-apply
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: a global Apply button duplicates the property controls without identifying which pending
  changes it commits; removing every explicit Apply action would also remove the required non-drag path
  for reusable resources and is therefore a different decision
- affects: 11_ui.md, graph/REQ-010
- decidedness: Fixed
- reversal_trigger: future Graph editing introduces an explicit staged transaction containing several
  named pending changes that must be reviewed and committed atomically

### XC-154 - A Simulation is a saved multi-execution flow owned by the Workspace
- decided: 2026-08-21
- status: active
- decision: a @Workspace may own multiple independently named, ordered and revisioned @Simulation
  items. Each Simulation is a declarative flow containing the explicit run conditions for one or more
  external-solver executions; it is not one execution and not the result Case. The Simulation area owns
  `シミュレーション一覧` with new, open, duplicate, rename, reorder and delete actions matching the
  concrete View, Graph and Report item lists. Running a Simulation is later-release functionality under
  XC-091 and produces or updates Cases only from solver-written outputs with solver, input, condition,
  execution and file provenance retained. A @Pipeline is the broader result-processing orchestration:
  its simulation unit pins a saved Simulation identifier and revision, adds each successful execution's
  Case to the target set, and can then apply Views, Graphs and Reports. Editing a Simulation does not
  silently retarget a pinned Pipeline unit
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: treating every solver execution as a separate top-level item duplicates shared setup and
  makes a parameter study hard to manage; treating Simulation as another name for Pipeline conflates
  producing solver results with consuming results for visualisation and reporting; storing it on a Case
  makes the result own the recipe that may produce several sibling results
- affects: GL-001, GL-022, GL-025, CT-001, CT-009, 11_ui.md, workspace/REQ-018, EXT-009
- decidedness: Fixed
- reversal_trigger: solver integrations prove that one saved flow cannot represent their execution model
  without hiding order, dependencies or provenance, requiring a separately named higher-level object

### XC-155 - Automation is a dedicated rightmost work area; Pipeline is its saved object
- decided: 2026-08-21
- status: active
- decision: the top work-area label is `自動化`, while the editable, named and revisioned definition
  managed inside it remains a @Pipeline. Automation is the rightmost work area because it composes and
  executes saved Simulations, Views, Graphs, Reports and outputs after those items have been prepared;
  the mode-tab order is Chat, Simulation, View, Graph, Report, Automation. Chat is a cross-cutting shared
  conversation rendered as the first full work-area tab, rather than a workflow stage or a separate
  utility button. Simulation, View, Graph,
  Report and Automation keep the same Case, Variable and Reference-material left sidebar. Their saved
  workspace items are switched from one shared searchable selector in the centre header; Automation's
  selector lists Pipelines and offers their item actions, while the adjacent primary action remains
  `＋ 新規パイプライン`. Pipeline is therefore not a left-sidebar section in any mode. The Automation
  centre owns flow composition, dry run and run outcomes, and the right sidebar owns the unit palette,
  selected-unit settings and run history. Simulation remains separate and keeps its existing
  name because it owns external-solver execution conditions rather than cross-product orchestration
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: `パイプライン自動化` is more explicit but too long for the persistent mode rail and
  repeats the object name; `フロー自動化` conflicts with the saved Simulation flow; merging Simulation
  and Automation makes ordinary solver setup carry loops, branches, output and delivery concepts that
  are irrelevant until orchestration is needed; adding the Pipeline list to every mode exposes an
  unrelated concept and reduces Case navigation space, while keeping it only in Automation breaks the
  shared left-sidebar grammar. A common centre-header item selector also gives Simulation, View, Graph
  and Report the same mechanism for switching their own multiple saved items. Keeping Chat as the first
  tab makes the shared conversational entry point easy to discover while preserving Automation as the
  final workflow tab
- affects: 11_ui.md, pipeline/REQ-001, XC-093, XC-154
- decidedness: Fixed
- reversal_trigger: task observation shows that users consistently interpret `自動化` as application
  preferences rather than executable pipeline authoring even after the screen subtitle and empty state
  identify the purpose

### XC-156 - View remains the work-area and saved-item name without a redundant current prefix
- decided: 2026-08-21
- status: active
- decision: the Japanese work-area label and saved workspace-item type remain `ビュー`. The centre
  header's small type label is also `ビュー`, not `現在のビュー`, because the selected item name shown
  immediately below already identifies the current item. The closed selector therefore reads as a type
  followed by an exact item name such as `標準ビュー`; its creation action remains `＋ 新規ビュー`
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: `可視化` overlaps the separately named Graph work area; `3Dビュー` excludes the
  specified 2D and multi-pane cases; `結果` names the solver output rather than its saved presentation;
  `ビューワー` implies a read-only tool. Keeping `現在のビュー` repeats information already expressed
  by the selected item and adds visual noise to the compact persistent header
- affects: GL-008, 11_ui.md, view/REQ-010
- decidedness: Fixed
- reversal_trigger: user testing shows that `ビュー` is consistently mistaken for an application-wide
  View menu or camera-only control despite the selected item name and View editor beneath it

### XC-157 - Work-area headers omit the redundant current prefix in every mode
- decided: 2026-08-21
- status: active
- decision: the persistent centre-header type label uses the exact mode names `シミュレーション`, `ビュー`,
  `グラフ`, `レポート` and `自動化`. It never prefixes them with `現在の`; the selected saved item name
  directly below identifies what is currently open. Automation keeps `パイプライン` as the saved-item type
  label because it describes the item being edited, while `自動化` names the work area.
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: repeating `現在の` adds noise and duplicates the selected item name; using `パイプライン`
  as the work-area label obscures the broader automation authoring mode
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: user testing shows that users cannot distinguish the work-area mode from its selected
  saved item without the prefix

### XC-158 - Chat history uses the left sidebar while reference insertion remains deferred
- decided: 2026-08-21
- status: active
- decision: Chat uses the left sidebar for its conversation list, matching the familiar ChatGPT/Gemini
  interaction pattern. The Case, Variable and Reference-material navigation remains in the other work
  areas. Inserting a Case or Variable into a prompt is deferred; a later design may add a composer-level
  reference picker or `@` mention flow without adding persistent context rails to Chat.
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1)
- alternatives: sharing the Case/Variable sidebar in Chat increases clutter and weakens conversation
  history visibility; adding a secondary rail duplicates navigation and reduces the central chat width;
  putting references in the left sidebar makes prompt composition overly persistent
- affects: 11_ui.md
- decidedness: Bounded
- reversal_trigger: usability testing shows that users cannot find or switch conversations from the header

### XC-159 - View uses a CAE-specific Blender-inspired object taxonomy
- decided: 2026-08-21
- status: active
- decision: the first-release View object taxonomy is `解析メッシュ`, `参照メッシュ`, `スカラー場`,
  `ベクトル場`, `流線・軌跡`, `点群`, `テキスト・注釈` and `エフェクト`. The first two are roles of
  the Mesh family; the next four distinguish source-linked or derived CAE representations; text and
  effects are display-only layers. Every derived representation records its source field, units,
  coordinates, sampling and generation parameters where applicable.
- decided_by: the product owner, 2026-08-21
- basis: E-095 (T1), CAE provenance and no-invented-values requirements
- alternatives: treating background mesh as a new technical type duplicates Mesh semantics; using only
  generic Blender names hides the difference between solver-linked results and display overlays; adding
  Volume, Camera, Light and Image now would expand the contract before their provenance and editing
  behaviour are defined
- affects: GL-018, GL-044, 11_ui.md, view/REQ-020
- decidedness: Bounded
- reversal_trigger: a required CAE source or display workflow cannot be represented without adding a
  type, or usability testing shows that users consistently confuse source results with display effects

### XC-160 - View playback controls are a hover overlay on the canvas
- decided: 2026-08-21
- status: active
- decision: View playback controls appear as a compact, dark translucent overlay anchored to the bottom
  of the canvas while the pointer is over the canvas. The overlay provides play/pause, first/last,
  previous/next, a result-axis scrubber, position text and playback speed. It does not reserve permanent
  vertical space or duplicate the right property sidebar; steady results have no playback overlay. The
  axis name is not printed as a permanent `時間軸` label. Hovering or scrubbing the range shows a compact
  timestamp tooltip at the pointer position, formatted as `m:ss` for time-based results; other result
  axes use their own explicit value format.
  Clicking the scrubber commits exactly the pointer-derived position to the current-result marker and
  displayed value; it never snaps to a nearby step unless the source axis itself is discrete.
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1), E-081 (T1)
- alternatives: a permanently visible footer consumes canvas height and makes steady results appear
  playable; placing playback in the right sidebar hides a time-critical viewport operation
- affects: 11_ui.md, view/REQ-010
- decidedness: Fixed
- reversal_trigger: pointer and keyboard testing shows the overlay is not discoverable or disappears while
  a user is scrubbing

### XC-161 - Panel resizing preserves the View camera pose
- decided: 2026-08-21
- status: active
- decision: resizing either side panel or the material-library shelf changes only the 3D viewport
  dimensions. The scene stays mounted, the camera pose and orbit target are preserved, and automatic
  bounds observation must not refit the model on every resize. The viewport uses containment so layout
  changes do not leak scroll or paint effects into adjacent panels.
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1), E-081 (T1)
- alternatives: refitting on every resize makes the model jump and changes the user's framing; remounting
  the scene resets selection, orbit and renderer state; a permanent footer would consume view space
- affects: 11_ui.md, view/REQ-010
- decidedness: Fixed
- reversal_trigger: a renderer or accessibility test demonstrates that preserving the camera prevents a
  necessary explicit fit action from being discoverable

### XC-162 - Saved-item selection uses an explicit combo-button treatment
- decided: 2026-08-21
- status: active
- decision: the persistent Simulation, View, Graph, Report and Automation headers present the selected
  saved item in one bordered combo button. The control groups the item kind, selected name and chevron,
  exposes the matching accessible label (`<kind>を選択`) and opens the searchable listbox on click.
  A bare title with a visually detached chevron is not used because it obscures the relationship between
  the title and the switching action.
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1), E-081 (T1)
- alternatives: a separate `ビューを選択` button consumes header space and duplicates the title; a bare
  text link and chevron are easy to overlook; a native select hides the searchable item metadata
- affects: 11_ui.md, view/REQ-010
- decidedness: Fixed
- reversal_trigger: usability testing shows that users still fail to identify the bordered title control
  as the saved-item switcher

### XC-163 - Saved View and Graph options show hover still previews
- decided: 2026-08-21
- status: active
- decision: hovering or keyboard-focusing a saved View or Graph option in the central item selector
  displays a small still preview beside the list. View previews use a representative rendered image;
  Graph previews use a static chart image. The preview is not live, carries no invented result values,
  and disappears when the option is no longer focused. It is anchored immediately to the right of the
  focused option and vertically centered on that row rather than following the pointer, keeping the
  option-to-preview relationship stable and avoiding cursor occlusion. Other item kinds stay compact until their own
  preview content and provenance are defined.
- decided_by: the product owner, 2026-08-21
- basis: E-080 (T1), E-081 (T1)
- alternatives: showing previews for every item kind increases noise and requires undefined provenance;
  opening a full preview on click slows selection; omitting previews makes similarly named saved items
  harder to distinguish
- affects: 11_ui.md, view/REQ-010
- decidedness: Bounded
- reversal_trigger: preview rendering obscures the option list or users mistake a still preview for live
  analysis output

### XC-164 - Saved-item catalogue replaces the centre editor while preserving the composer
- decided: 2026-08-21
- status: active
- decision: Simulation, View, Graph, Report and Automation share a persistent `編集｜一覧` segmented
  switch at the left edge of the centre title bar. It precedes the item title while the type-specific
  create button is fixed at the right edge, remains in the same position in both states, and does not
  overlay the canvas. `編集` uses the
  searchable current-item selector. In catalogue state that selector and its outline are removed rather
  than replaced by a redundant `ビュー一覧`-style title: the selected mode tab and `一覧` segment already
  provide the context. Text search, filtering and grid/list display controls follow the segmented switch
  on the same title-bar row; no second toolbar or item-kind eyebrow is shown. The catalogue replaces the centre editor, retains the shared natural-language
  instruction bar, and hides the right properties sidebar and material library. Choosing an item or
  activating `編集` restores the editor and its previous sidebar state; no separate close button is
  shown.
- decided_by: the product owner, 2026-08-21
- basis: E-088 (T1), E-089 (T1)
- alternatives: keeping the properties sidebar shows stale editor state beside a catalogue; putting the
  catalogue in the sidebar duplicates the centre list and reduces usable width; hover-only controls are
  less discoverable and can shift or obscure adjacent mode tabs
- affects: 11_ui.md, MOD-007
- decidedness: Bounded
- reversal_trigger: users need persistent metadata or filtering that cannot fit in the centre catalogue

### XC-165 - Settings uses a full-width page without workspace sidebars
- decided: 2026-08-22
- status: active
- decision: Settings retains the global application header and its own internal category navigation,
  but hides the workspace left sidebar, right properties sidebar, both sidebar toggles and the shared
  natural-language instruction bar. Workspace-specific preferences are named sections inside Settings;
  they do not reuse case, variable or selected-object panels whose scope would be ambiguous.
- decided_by: the product owner, 2026-08-22
- alternatives: retaining the right sidebar duplicates the settings content; retaining the left sidebar
  implies that global settings apply only to the selected case; presenting Settings as a workspace mode
  leaves unrelated editing controls visible
- affects: 11_ui.md, MOD-007
- decidedness: Bounded
- reversal_trigger: a future settings task requires persistent workspace context that cannot be stated
  safely inside the settings category and content panes

### XC-166 - Object names View state and Asset names reusable library state
- decided: 2026-08-22
- status: active
- decision: `Object` is the project-wide term for one instantiated, selectable display entity owned by
  a @View. `Asset` is the project-wide term for a reusable packaged resource in sample, workspace or
  shared library scope. A @Dataset is neither: it is source analysis data. An Object may be saved as an
  Object asset; applying that Asset creates a new independently editable View object and records the
  source Asset identifier and revision as provenance. Materials and other appearance Assets are
  referenced by the View object's slots or display definition rather than becoming Objects themselves.
  The current-state right sidebar and Outliner therefore say `Object`; library, import, export, scope,
  licence and reuse flows say `Asset`.
- decided_by: the product owner, 2026-08-22
- basis: E-095 (T1), E-001 (T1)
- alternatives: calling every displayed entity an Asset conflates current View state with reusable
  library state; calling every reusable resource an Object erases scope, revision, origin, licence and
  import/export semantics and does not fit materials, fonts or backgrounds
- affects: GL-018, GL-044, CT-008, 11_ui.md, view/REQ-020, workspace/REQ-017
- decidedness: Fixed
- reversal_trigger: the product removes the library lifecycle entirely or replaces View instances with
  live library aliases whose edits intentionally propagate

### XC-167 - Reference UV is preserved; analysis-mesh texture mapping is lazy derived display data
- decided: 2026-08-22
- status: active
- decision: a reference Mesh View object preserves every authored UV set, its name, values, indexing
  and interpolation, and the product never overwrites it with an automatically generated set. An
  analysis Mesh has no inferred or canonical UV. Uniform appearance, PBR parameters and field-driven
  `ColorBinding` generate no UV at all. When an applied Material Asset explicitly requires texture
  coordinates, MOD-003 resolves its declared mapping profile: object-space triplanar or an explicit
  plane, cylinder or sphere projection needs no atlas; a two-dimensional texture that requires unique
  UVs triggers a deterministic charted atlas on the display surface, lazily in the rendering backend.
  Generated coordinates, seams and any duplicated render vertices are derived display data, never
  written into the source @Dataset and never used for a reported value, selection identity or material
  boundary. The View definition stores the mapping mode, scale in canonical metres, rotation, declared
  fallback and the atlas generator name, version and parameters where applicable; a cache additionally
  keys the result by display-topology identity. The Materials properties show mapping mode, scale,
  rotation and generation status but provide no UV editor. Unsupported or failed generation is named;
  only a fallback explicitly declared by the Material Asset may be used. Mapping every triangle to an
  identical right triangle is not a general-purpose mode because it makes every edge a seam, destroys
  continuous texture placement and expands render data for large CAE surfaces
- decided_by: the product owner, 2026-08-22
- basis: E-096 (T1), E-097 (T1), E-098 (T1), E-001 (T1)
- alternatives: always generating an atlas spends memory and time for materials and analysis colours
  that do not consume UVs; generating UVs in the front end duplicates backend capability and makes
  native, web and exported views disagree; a per-triangle right-angle layout is simple but preserves
  neither continuity nor proportional texel density; rejecting every textured material on analysis
  meshes keeps the data model simple but needlessly removes presentational use cases
- affects: CT-004, 11_ui.md, view/REQ-004, view/REQ-021, MOD-003
- decidedness: Fixed
- reversal_trigger: measured representative CAE surfaces show that deterministic chart atlasing cannot
  meet the display budget and an object-space mapping cannot provide the required appearance, or the
  product narrows texture use to per-face constant lookup where continuity and texel density are
  explicitly irrelevant

### XC-168 - Persistent peer-tab groups use equal widths within the group
- decided: 2026-08-22
- status: active
- decision: the six persistent top work-area tabs and every material-library category-tab group use one
  equal width for all tabs in that group; Sample/Original already follows the same rule. The top group
  and a library group need not share the same pixel width, and View, Graph and Report library groups may
  have different unused trailing space because their category counts differ. Equal width is computed or
  implemented from the group's widest supported label rather than from each label independently, so a
  selected tab never changes size and peers remain visually balanced. At widths where labelled tabs do
  not fit, the top work-area group switches to equal-width icon tabs and the library category group
  retains equal tab widths with horizontal scrolling; labels are not silently truncated into ambiguous
  text. Exact responsive widths remain an implementation value bounded by full-label fit, target-size
  accessibility and the available toolbar width
- decided_by: the product owner, 2026-08-22
- basis: E-099 (T1)
- alternatives: content-width tabs use space efficiently but make peer categories look uneven and move
  neighbouring hit targets when labels or locale change; stretching every library group across all
  available space produces excessively wide tabs in Graph and Report; shrinking unequal labels until
  all fit preserves neither predictable targets nor readable names
- affects: 11_ui.md, workspace/REQ-017
- decidedness: Fixed
- reversal_trigger: localisation or observed task use shows that the supported labels cannot remain
  readable within the available desktop toolbar, requiring a content-width scrollable-tab pattern for
  the affected group

### XC-169 - Result colour and PBR appearance are typed slots, not an arbitrary material stack
- decided: 2026-08-22
- status: superseded
- superseded_by: XC-174
- decision: each @View object has at most one ordinary PBR appearance Material Asset and at most one
  field-driven result-colouring binding. They are stored and edited as two named slots rather than as
  interchangeable layers. `結果カラー` gives the colour transfer function exclusive ownership of base
  colour and never alpha-blends a PBR base-colour texture or metallic tint into the value-to-colour
  mapping. `マテリアル` shows the PBR material and hides result colouring. An explicit
  `結果カラー＋表面ディテール` option may retain non-colour normal and roughness detail, is off by default,
  and remains labelled as a presentation change; it does not change the field, range, legend, probe or
  reported value. r1 has no general material layer stack, channel mixer or material-authoring graph
- decided_by: the product owner, 2026-08-22, after reviewing the proposed Blender, Substance and
  ParaView alternatives
- basis: E-100 (T1), E-101 (T1), E-103 (T1), E-001 (T1)
- alternatives: one undifferentiated material slot cannot retain both an engineering result binding
  and a reusable PBR appearance; an unrestricted Painter-like stack is a material-authoring system,
  makes the active colour authority difficult to audit and exceeds the r1 scope; silently multiplying
  result colour by a PBR base colour changes the visible transfer function while leaving the legend
  looking authoritative
- affects: CT-004, 11_ui.md, view/REQ-004, view/REQ-022, view/REQ-023, MOD-003
- decidedness: Fixed
- reversal_trigger: a validated rendering method can layer several appearance assets while proving
  that the displayed result colour remains perceptually and numerically traceable to its legend, or
  customers require in-product material authoring strongly enough to bring a typed layer graph into scope

### XC-170 - View properties follow object type and material application starts with an explicit target
- decided: 2026-08-22
- status: superseded
- superseded_by: XC-171
- decision: the View right sidebar's Object and Material sections always name the selected View object
  and its CAE object type. Object properties change by that type; controls that do not apply are absent
  or say why rather than remaining enabled with a plausible default. Applying a Material Asset enters
  one target-selection mode shared by the viewport and Outliner: compatible candidates are highlighted,
  click replaces the selection, `Shift` adds a candidate, and `Escape` cancels without changing the
  View. The confirmation names every target, the appearance slot that will change and unresolved
  references before application. Both sections may retain a live material viewer at the bottom of the
  property region. It uses a neutral sphere by default and offers cube, plane and cylinder primitives;
  it never maps invented analysis values onto that geometry. Result colouring is previewed separately
  as a value-free colour-map strip
- decided_by: the product owner, 2026-08-22
- basis: E-100 (T1), E-101 (T1), E-102 (T1), E-103 (T1), E-001 (T1)
- alternatives: a permanently global target makes multi-object views unsafe to edit; a modal target
  picker hides the viewport context needed to choose; using the selected CAE mesh as the only material
  swatch makes tessellation, UVs and analysis colour hard to distinguish from material behaviour; a
  fixed sphere cannot expose planar mapping and edge behaviour
- affects: 11_ui.md, view/REQ-020, view/REQ-021, view/REQ-022, view/REQ-023, MOD-007
- decidedness: Fixed
- reversal_trigger: usability testing shows that synchronized viewport and Outliner selection causes
  more wrong-target applications than a staged chooser, or a material class requires a standard test
  geometry not represented by sphere, cube, plane or cylinder

### XC-171 - View property tabs follow one last-selected active object
- decided: 2026-08-22
- status: active
- decision: the viewport and Outliner own one shared View-object selection. When several objects are
  selected, the most recently selected or reselected object is the sole active object and drives the
  Object, Materials and contextual Text property tabs; the other objects remain selected but do not create an
  aggregate property form. Those tabs do not introduce another target picker or repeat a recipient
  object summary. The Object tab may show the active object's name and type because they identify its
  type-specific form. The View rail calls the object-specific typography tab `テキスト`, not `フォント`,
  and includes it only when the active object has the `テキスト・注釈` capability. It owns content and
  typography; Object retains kind, anchor and provenance. Other object types omit the tab rather than
  showing an empty-font state. Object, conditional Text and Materials are adjacent in that order after
  the divider from the whole-View tabs. This decision originally retained `フォント` for reusable Asset
  categories and Graph/Report typography; XC-183 later changes those user-facing tab labels to
  `テキスト` while keeping Font as the internal Asset kind. Within the same vertical property scroll,
  Materials places its Material Slot list
  above the live appearance preview and its editing tabs below. Object does not repeat or reserve space
  for that preview; it remains limited to identity and type-specific object settings. Following Blender's
  compact active-material preview pattern, the render well is the panel: it has no separate header or
  result-colour footer row. Sphere, cube, plane, cylinder and a fixed non-rotating `2D面` are icon-only
  controls in one vertical rail on its right; an independent left rail selects the combined material or
  an evaluated PBR/result output. The rails use the right sidebar's border and selected-control tokens while the
  render well remains a neutral inspection scene; icon labels remain available to assistive technology
  and tooltips
- decided_by: the product owner, 2026-08-22, after asking to follow the general multi-selection
  convention, remove redundant recipient information, and make the renamed Text tab conditional on
  the active text-bearing object, followed by explicitly removing the duplicate Object-tab material preview
- basis: E-104 (T1), E-105 (T1), E-102 (T1), E-100 (T1), E-001 (T1)
- alternatives: the superseded XC-170 target mode duplicates selection state and makes the Materials
  tab appear to edit a destination other than the Outliner selection; first-selected context is less
  familiar in the referenced DCC convention and does not let reselecting an existing member make it
  active; repeating object identity in every property tab consumes scarce sidebar space without adding
  context already visible in the Outliner
- affects: 11_ui.md, view/REQ-022, view/REQ-023, MOD-007
- decidedness: Fixed
- reversal_trigger: observed wrong-object edits show that last-selected active context is not visible
  enough, or a validated batch-edit workflow requires an explicit aggregate property state

### XC-172 - Material choices use shared rendered-sphere thumbnails
- decided: 2026-08-22
- status: superseded
- superseded_by: XC-177
- decision: each PBR Material Asset has one square transparent-background thumbnail rendered on a
  neutral sphere. The material library and the Materials property slot reference the same thumbnail for
  the same Material Asset rather than substituting category icons or independent previews. Names,
  source and state remain text outside the image. A result-colouring binding is not a PBR Material Asset
  and retains its distinct analysis representation. If a material thumbnail is unavailable, the UI
  names that state instead of showing another material's sphere or a plausible generic material
- decided_by: the product owner, 2026-08-22, after requesting the Substance Painter material-selection
  pattern in both the library and Materials properties
- basis: E-106 (T1), E-101 (T1), E-001 (T1)
- alternatives: a shared palette icon does not show colour, roughness, metallic or transmission
  differences; rendering a second unrelated preview for the assigned slot can make one asset appear to
  have two identities; using a CAE result-coloured sphere as a material thumbnail would confuse the
  reusable PBR asset with a field binding
- affects: 11_ui.md, view/REQ-023, MOD-007
- decidedness: Fixed
- reversal_trigger: measured shelf density or rendering cost makes pre-rendered thumbnails unusable,
  or a material class needs a standard preview geometry other than the sphere to remain identifiable

### XC-173 - Material properties use purpose-specific DCC terminology without a redundant slot heading
- decided: 2026-08-22
- status: superseded
- superseded_by: XC-177
- decision: the Materials property tab omits the redundant `外観スロット` heading and `各1件`
  cardinality badge. Its two typed entries are labelled `サーフェス` and `結果カラー`; its setting
  groups are labelled `表示` and `マッピング`. The three display choices are `結果カラー`,
  `マテリアル` and `結果カラー＋表面ディテール`. These are presentation labels only: CT-004 keeps
  the separately auditable PBR Material Asset and result-colouring binding defined by XC-169
- decided_by: the product owner, 2026-08-22, after requesting terminology consistent with common DCC
  applications and removal of headings that do not add context
- basis: E-107 (T1), E-105 (T1), E-001 (T1)
- alternatives: keeping `外観スロット` repeats the surrounding Materials tab without explaining an
  action; exposing `0/1` cardinality makes a storage constraint look like an editing concept; using
  `解析表現` beside a PBR material does not identify the colour authority as directly as
  `結果カラー`
- affects: 11_ui.md, view/REQ-023, MOD-007
- decidedness: Fixed
- reversal_trigger: terminology testing with target users shows that the DCC-aligned labels obscure
  the distinction between the surface Material Asset and the result-colouring binding

### XC-174 - One MaterialX-backed Material Asset model replaces PBR and result-material kinds
- decided: 2026-08-22
- status: active
- decision: CT-011 defines one Material Asset kind whose source of truth is a qualified root MaterialX
  material graph. The stored contract has no `appearance`, `analysis` or `composite` kind enum. A graph
  with no SOLVIA-result requirement is data-independent; a graph with one or more such requirements is
  data-dependent; a graph combining them with textures or referenced material graphs is composite.
  Those labels are derived badges, never identities a user or importer must keep in sync with the
  graph. MaterialX owns graph values and connections; CT-011 owns SOLVIA identity, immutable revision,
  dependencies, provenance, traceability and capability requirements without duplicating shader values
- decided_by: the product owner, 2026-08-22, after reviewing the MaterialX, USD, VTK and Omniverse
  architecture proposal and asking to remove the material-kind distinction
- basis: E-108 (T1), E-109 (T1), E-114 (T1), E-001 (T1)
- alternatives: separate PBR and result-material contracts duplicate graph, thumbnail, revision and
  dependency machinery and prevent one graph from using both sources; VTK-native storage loses the
  graph when the renderer changes; an untyped opaque shader file cannot state what data it requires
- affects: CT-004, CT-008, CT-011, 01_boundaries.md, 09_technology.md, 11_ui.md, view/REQ-023,
  view/REQ-024, MOD-003
- decidedness: Fixed
- reversal_trigger: MaterialX ceases to preserve the graph or cannot generate any supported target,
  or a future interchange standard demonstrably carries the same graph, typed interface, provenance
  and cross-renderer semantics with less conversion loss

### XC-175 - Result data enters a MaterialX graph through a declared SOLVIA binding and fails visibly
- decided: 2026-08-22
- status: active
- decision: a MaterialX graph may declare zero or more typed `solviaResult` requirements. A CT-004
  Material Instance binds each requirement to field identifier, component, association, result position
  and declared unit; the renderer resolves it to a VTK/GPU attribute or USD primvar and lowers the graph
  to standard `geompropvalue` access. Shader code never opens a Dataset, path, database or network
  resource. If any required binding, component, position, unit dimension, resource or backend feature
  cannot be resolved, the whole affected material target renders with the reserved diagnostic magenta
  material, the instance state is failed, its ordinary legend is suppressed and the exact missing
  requirement is shown. No zero, previous field, previous time step or undeclared fallback is used.
  Missing values inside an otherwise resolved field mark only the affected elements
- decided_by: the product owner, 2026-08-22, after proposing a Blender-like all-pink material failure
- basis: E-108 (T1), E-001 (T1)
- alternatives: letting shader code query SOLVIA storage directly is renderer-specific, unsafe and not
  portable to USD; refusing to retain an unresolved instance prevents a transferable template from
  naming what its target lacks; keeping the previous successful pixels would make stale data look live
- affects: CT-004, CT-010, CT-011, 03_failure_policy.md, 11_ui.md, view/REQ-023, view/REQ-024, MOD-003
- decidedness: Fixed
- reversal_trigger: a portable MaterialX-standard data resolver gains bounded offline access with the
  same identity, association, unit and failure semantics on every supported renderer

### XC-176 - Objects have several targeted material slots and one resolved root per surface element
- decided: 2026-08-22
- status: active
- decision: a View object has zero or more CT-004 Material Bindings. Each names an immutable Material
  Asset revision and targets the whole object, a part or an explicit element set. A whole-object binding
  may be overridden by mutually non-overlapping subsets; overlapping subset bindings are invalid. Each
  rendered surface element resolves to exactly one root MaterialX material. That root may reference and
  compose other Material Definitions inside its graph, including several result inputs, but independently
  assigned materials are never ordered as an implicit layer stack. USD export uses non-overlapping
  `materialBind` GeomSubsets for the same partition
- decided_by: the product owner, 2026-08-22, after asking for multiple material definitions on one object
- basis: E-100 (T1), E-108 (T1), E-111 (T1), E-001 (T1)
- alternatives: one material id per object cannot represent bolts, seals or face-level assignments;
  arbitrary overlapping bindings have backend-dependent precedence and cannot identify which material
  produced a pixel
- affects: CT-004, CT-011, 11_ui.md, view/REQ-023, MOD-003
- decidedness: Fixed
- reversal_trigger: a supported scene standard defines portable, deterministic multi-material
  resolution for the same surface element and every SOLVIA renderer proves the same result

### XC-177 - Material UI derives dependency badges and previews every graph through one slot model
- decided: 2026-08-22
- status: active
- decision: the Materials properties and library expose one Material Asset and Material Slot model.
  They do not ask the user to choose PBR, analysis or composite type. The UI derives `解析データ依存`,
  resource and unresolved badges from CT-011 requirements, lists every required input binding and offers
  variants declared by the MaterialX graph instead of three hard-coded display modes. The material
  library uses each Asset revision's transparent rendered thumbnail, but the selected object's compact
  slot list shows material names only and sits immediately above the live viewer, which shows the active
  slot's appearance.
  Adjacent add and remove controls create or remove slots, and the list may contain several slots. A
  data-dependent library thumbnail may use the versioned synthetic preview fixture and says
  `サンプルデータ`; a selected object's live preview uses its real bindings and becomes diagnostic
  magenta when a required input is unresolved. Below the active slot, `基本`, `ノード` and `ソース`
  are three synchronised authoring views of that one MaterialX graph: Basic edits published inputs by
  constant, texture, colour map or restricted expression. Base Color names these `単色`, `画像`,
  `カラーマップ` and `数式`; it uses `単色` rather than the encoding name `RGB`, and has no separate
  `解析結果` mode. Analysis results, coordinates and other declared inputs are typed variables available
  within every compatible mode. For a colour map, the sidebar retains only the variable and a horizontal
  bar between editable numeric bounds. Values outside those bounds have alpha zero. Activating the bar
  opens a dedicated transfer-function dialog with independent opacity points above colour points,
  exact point values, point insertion/removal, interpolation and presets. This follows ParaView's
  colour/opacity transfer-function separation and Blender's stop-based colour-ramp interaction while
  keeping detailed editing out of the narrow property rail (E-117). Basic does not offer Node Connection as a source choice because graph-edge authoring
  belongs to Node; an existing arbitrary connection is retained and remains editable in Node or Source.
  Nodes exposes typed graph
  connections and expands into the central work area; Source edits the MaterialX XML and validates it.
  The three views do not repeat an output-preview canvas. The live viewer above them shows either the
  combined material or one evaluated OpenPBR/SOLVIA-result output, selected from an independent labelled
  vertical rail at its left edge. Material uses one shaded sphere icon in the Materials property rail,
  material library category and combined-material output; a palette remains specific to Base Color and
  a brush remains specific to style. The viewer's right-edge rail selects sphere, cube, plane, cylinder or a fixed,
  non-rotating `2D面`. Loaded documents and every edit are validated automatically; the common save
  action validates again and creates the immutable revision, so Source has no redundant manual `検証`
  button. Source names the active Asset revision's `.mtlx` file. Basic groups published Surface and
  SOLVIA-result inputs without a one-option shader picker. It omits a generic `Height` because a scalar
  height-to-normal operation and a true displacement shader have materially different rendering and
  geometry effects; either remains explicit in Node and Source. Mapping is not removed: Basic shows the
  per-binding Mapping group only when CT-011 declares a coordinate source other than `none`, since image
  and procedural textures require placement while uniform PBR values and field-driven colour do not.
  Node mirrors the active graph without invented result nodes. Content that Basic cannot represent remains
  in the graph. `ソース` is used
  instead of `コード` because MaterialX is a
  declarative document, and `基本` is used instead of `かんたん` because it names scope rather than user skill
- decided_by: the product owner, 2026-08-22, after unifying analysis display with code-managed MaterialX
  and accepting the recommendations to remove ambiguous Height, retain conditional Mapping, make
  Base Color source-specific without a Node Connection choice, and adopt the compact colour-map plus
  dedicated colour/opacity editor, followed by the explicit choice of a sphere for the Material icon
- basis: E-105 (T1), E-106 (T1), E-108 (T1), E-116 (T1), E-117 (T1), E-001 (T1)
- alternatives: separate Surface and Result Colour cards expose an implementation distinction that no
  longer exists; an unlabelled synthetic result looks like analysis evidence; an unbound analysis
  thumbnail rendered only as magenta makes reusable programs impossible to distinguish
- affects: CT-004, CT-011, 11_ui.md, view/REQ-023, mockups/ui
- decidedness: Fixed
- reversal_trigger: usability testing shows that graph-derived dependencies cannot be understood or
  repaired without a separate task surface, while the stored Material contract remains unified

### XC-178 - MaterialX is canonical, USD transports it and VTK-family renderers are explicit adapters
- decided: 2026-08-22
- status: active
- decision: SOLVIA code-manages and validates MaterialX 1.39 documents with the 1.39.5 library and uses
  OpenPBR Surface 1.1.1 for newly authored PBR surfaces. Imported source bytes and every dependency are
  retained and hashed; unknown nodes, attributes, looks, variants and implementations are inventoried
  and never silently discarded or executed. Each native VTK and vtk.js adapter reports every required
  feature as `exact`, `baked` or `unsupported`; baking is an explicit, provenance-recorded operation.
  USD writes an `mtlx` render context using `sourceAsset` plus `subIdentifier`, a universal
  UsdPreviewSurface fallback only for exact or explicitly baked channels, and SOLVIA identity metadata
  independently because UsdMtlx ignores `attributedef`. Omniverse and OpenUSD/MaterialX compatibility
  are tested as version tuples; generated MDL is never canonical. All file and include resolution is
  package-bounded, offline, traversal-safe and non-executing for untrusted source implementations
- decided_by: the product owner, 2026-08-22, after requesting a detailed VTK, Omniverse, USD,
  MaterialX and SOLVIA-metadata architecture
- basis: E-109 (T1), E-110 (T1), E-112 (T1), E-113 (T1), E-114 (T1), E-001 (T1)
- alternatives: adopting VTK properties as storage loses unsupported graph content; adopting USD alone
  inherits UsdMtlx omissions; adopting MDL makes an optional NVIDIA consumer the product's source of
  truth; silent approximation violates the product's failure policy
- affects: CT-011, 06_external.md, 09_technology.md, view/REQ-008, view/REQ-024, MOD-003, MOD-006
- decidedness: Fixed
- reversal_trigger: measured cross-renderer tests show a different canonical representation preserves
  more authored semantics while retaining offline code generation, lossless source round-trip and
  explicit failure on every supported backend

### XC-179 - Rendering appearance never supplies engineering material properties
- decided: 2026-08-22
- status: active
- decision: a CT-011 Material Asset describes rendering appearance and data-driven visualisation only.
  Density, elastic modulus, Poisson ratio, yield strength, temperature dependence and other engineering
  properties belong to a separate engineering-material contract with declared units and provenance.
  Calling an appearance `steel` never supplies, infers or changes any physical property
- decided_by: the product owner, 2026-08-22, while confirming the unified MaterialX model
- basis: E-001 (T1)
- alternatives: combining appearance and engineering properties makes a visual preset capable of
  silently changing analysis inputs and lets a familiar name stand in for undeclared numbers
- affects: CT-011, 00_glossary.md, 02_invariants.md, view/REQ-024
- decidedness: Fixed
- reversal_trigger: none; a future combined editor may link the two contracts, but may not infer one
  from the other

### XC-180 - Material opacity and object presentation remain two explicit layers
- decided: 2026-08-22
- status: active
- decision: Materials Basic exposes the active MaterialX graph's OpenPBR `geometry_opacity`; this is
  the reusable material's intrinsic cutout opacity and may be driven by any type-compatible graph
  input. Object separately owns one instance-level `表示不透明度` multiplier and one representation per
  View object. Final surface alpha is the product of that multiplier and the resolved MaterialX
  opacity. Mesh edges are a topology overlay, not a Material Slot property: one `表示形式` selector owns
  Surface, Surface plus Edges and Wireframe, with no duplicate Edge checkbox. An edge-bearing mode
  reveals one object-level Edge group containing sRGB colour, output-pixel width and opacity; plain
  Surface hides it. Edge alpha is its opacity times the object multiplier. CT-004 3.1 stores this
  presentation separately from CT-011 and Material Bindings, and none of it changes analysis values
- decided_by: the product owner, 2026-08-22, after accepting the explicit recommendation to separate
  material-intrinsic opacity from instance display opacity and to keep one edge setting per object
- basis: E-109 (T1), E-001 (T1)
- alternatives: putting all opacity in MaterialX prevents fading one instance without revising a
  reusable Material Asset; putting material opacity only on the object cannot represent cutouts or
  graph-driven transparency; assigning edges per Material Slot creates conflicts wherever one object
  has several targeted materials; retaining both Surface-plus-Edges and an Edge checkbox creates two
  controls for one state
- affects: CT-004, CT-011, 11_ui.md, view/REQ-022, view/REQ-023, mockups/ui
- decidedness: Fixed
- reversal_trigger: a portable material standard adopted by every supported backend defines topology
  edge rendering as material semantics without conflicting across non-overlapping Material Slots

### XC-181 - Basic exposes one binding-level texture-mapping control path
- decided: 2026-08-22
- status: active
- decision: the Materials `基本` view does not place a `座標` selector under Base Color or another
  published Surface input. Those rows select the value or resource; the conditional binding-level
  `マッピング` group is the single owner of coordinate source, projection and transform. Its `方式`
  selects authored UV, generated UV, object-space triplanar, planar, cylindrical or spherical mapping.
  Authored UV alone reveals `UVセット`; planar alone reveals `投影面` with XY, XZ or YZ; scale,
  rotation and resolution status remain common. Per-node coordinate networks that intentionally use
  different mappings remain in Node and Source instead of being misrepresented as one Basic control
- decided_by: the product owner, 2026-08-22, after identifying the duplicate Surface coordinate and
  Mapping controls and explicitly requesting the recommended consolidation
- basis: E-096 (T1), E-097 (T1), E-098 (T1), E-001 (T1)
- alternatives: retaining both selectors permits contradictory combinations such as Base Color XY and
  binding-level triplanar; moving every mapping control beside each Surface input repeats the common
  case and cannot faithfully flatten arbitrary graph-local coordinate networks
- affects: 11_ui.md, view/REQ-021, view/REQ-023, mockups/ui
- decidedness: Fixed
- reversal_trigger: usability testing shows that published Surface inputs routinely need independent
  mappings and a reviewed per-input Basic representation can preserve those graph semantics without
  duplication

### XC-182 - Every right-rail tab owns a complete, non-overlapping editor
- decided: 2026-08-22
- status: active
- decision: every visible Simulation, Automation, View, Graph, Report, Settings and Network property
  tab renders an editor for its stated responsibility; no tab falls back to a generic Name, Enabled and
  Opacity form. View separates whole-view layout/camera/guides, rendering, background and image/video
  output from active-object properties. Graph separates definition, 2D/3D kind, style, text, case and
  series detail, and image/vector/table/animation output. Report separates document identity and
  mandatory trust content, layout, style, embedded text, source/content/commentary detail, and all
  contract output kinds. Settings separates general, declared units, coordinate frames and renderer
  policy; Network separates permission from audit. A control appears only when its mode needs it, and
  unavailable solvers, renderers, variables, models, permissions and generated artefacts remain named
  as unavailable or unresolved rather than looking usable
- decided_by: the product owner, 2026-08-22, after explicitly requesting the contents of Overall,
  Rendering and every tab in every other mode to be completed with considered interaction design
- basis: E-080 (T1), E-001 (T1)
- alternatives: one generic form makes unrelated tabs appear complete while duplicating controls and
  hiding mode-specific failure states; putting every control in Overall removes the rail's ownership
  boundaries and forces users to scan irrelevant options
- affects: 11_ui.md, workspace/REQ-017, mockups/ui
- decidedness: Fixed
- reversal_trigger: observed task testing proves that a different grouping reduces wrong-scope edits
  without duplicating controls or hiding unsupported and unresolved states

### XC-183 - Every user-facing typography tab is named Text
- decided: 2026-08-22
- status: active
- decision: every user-facing property-rail and material-library category tab that edits or selects
  typography is labelled `テキスト` across View, Graph and Report. The existing internal `fonts` tab and
  category identifiers and CT-008 Font `assetKind` remain unchanged for stored-document compatibility;
  precise field labels such as `フォント`, `書体`, size and embedding remain inside the Text editor
- decided_by: the product owner, 2026-08-22, explicitly replacing the remaining project-wide Font tab
  labels with Text
- basis: E-001 (T1)
- alternatives: retaining Font for Graph, Report or the library creates two names for the same
  typography destination; renaming the contract kind and stable identifiers adds migration risk without
  changing the user-visible interaction
- affects: 11_ui.md, workspace/REQ-017, mockups/ui
- decidedness: Fixed
- reversal_trigger: terminology testing demonstrates that users consistently expect a resource-only
  Font label and mistake Text for editable content in library contexts

### XC-184 - Lighting stays inside Rendering and may reference the visible environment
- decided: 2026-08-22
- status: active
- decision: View lighting remains one `照明` group inside `描画`; it is neither a separate property-rail
  tab nor part of `背景`. Lighting owns source, lighting strength, key light where applicable, shadows
  and ambient occlusion. Background owns visible kind, environment Asset, environment rotation, display
  strength and camera visibility. A lighting source may select `背景の環境`, which references the
  Background-owned Asset and rotation without copying them; lighting strength remains separate, so a
  background hidden from the camera may still illuminate the scene. A dedicated Lighting tab is deferred
  until the product exposes multiple editable light entities, rigs, placement or animation
- decided_by: the product owner, 2026-08-22, after accepting the recommendation to retain Lighting in
  Rendering and keep Background limited to visible environment presentation
- basis: E-063 (T1), E-001 (T1)
- alternatives: placing lighting in Background conflates camera visibility with illumination and fails
  for transparent backgrounds; a dedicated tab adds rail density for one small group and suggests a
  light-authoring workflow the current product does not provide
- affects: 11_ui.md, view/REQ-002, mockups/ui
- decidedness: Fixed
- reversal_trigger: a multi-light workflow with selectable light entities, rigs, placement, per-light
  shadows or animation becomes an accepted product requirement

### XC-185 - A version pinned in a package manifest is checked like any other Fixed value
- decided: 2026-08-22
- status: active
- decision: every dependency version this specification set declares is compared against the manifest
  that actually pins it - `pyproject.toml` for the engine, `mockups/ui/package.json` for the interface
  catalogue - by `validate/check_dependency_pins.py`, which runs in the same gate set as the spec
  linter. A declared version with no manifest entry, a manifest entry with no declaration, and a
  disagreement between the two are all findings
- decided_by: found on 2026-08-22 while reviewing the specification set against its own evidence
- basis: E-051 (T1), E-060 (T1)
- alternatives: relying on check 7 leaves the hole that produced this defect - it compares
  `SYMBOL = literal` inside source files, and a pin written as `"vtk==9.5.2"` in a TOML array matches
  nothing it looks at; moving every pin into a Python constant creates a second definition of the
  version, which is the duplication defect this project spends a separate gate on
- affects: EXT-001, EXT-002, EXT-010, XC-040, XC-041, 09_technology.md
- decidedness: Fixed
- reversal_trigger: the packaging toolchain gains a lock format the spec set can reference directly,
  making the comparison a link rather than a check

### XC-186 - This repository publishes to one named GitHub repository
- decided: 2026-08-22
- status: active
- decision: the repository is published to
  `take-works-tech/261SV`, private, and to nowhere else. Pushing, adding a
  remote and creating a repository are permitted for that one target; force-push, hard reset, rebase
  and history rewriting are refused, because the record of a correction is part of this project's
  deliverable. `.claude/hooks/local_only_guard.py` enforces the remote name, and
  `tests/test_environment_gates.py` proves the guard can still fail
- renamed: 2026-08-22, from `take-works-tech/202604-sim-analysis-visualization`, by the product owner.
  The decision is unchanged - one named repository, private, and nowhere else - and only the name it
  names has moved. **The old name is not an alias.** GitHub serves a redirect from it, and the guard
  deliberately does not accept it: a redirect is a convenience GitHub may withdraw, and the old name is
  now free for anyone to claim, at which point a push aimed at it would reach a stranger's repository
  rather than failing. The remote was repointed explicitly for the same reason. The local working
  directory is renamed separately and by hand, because a session cannot rename the directory it is
  running inside
- enforcement: **client-side only, and this is a real gap rather than a design choice.** Measured
  2026-08-22: both the rulesets API and the classic branch-protection API return HTTP 403,
  "Upgrade to GitHub Pro or make this repository public", because the repository is private under a
  free personal account. So there is no server-side required-status-check, no protected branch and no
  server-side refusal of a force-push. What is in force instead: the hook, which runs only in an agent
  session on this machine; rebase merges disabled at the repository level, which the free plan does
  allow; Dependabot alerts and automated security fixes enabled. A developer typing `git push --force`
  in a plain terminal is refused by nothing. Tracked as OPEN-020
- decided_by: the product owner, 2026-08-22, explicitly authorising GitHub integration
- basis: E-001 (T1)
- supersedes: the working agreement recorded in AGENTS.md that this repository is local only and
  configures no remote. That agreement was correct while nothing had been authorised; it is now
  narrowed to one repository rather than removed, because the risk it guarded against - a product
  plan and its market analysis reaching an audience nobody chose - is unchanged for every other target
- alternatives: leaving the guard as a blanket refusal makes the authorised push impossible without
  disabling the guard entirely, and a guard that is routinely disabled protects nothing; allowing any
  remote returns the project to the state the guard was written to prevent
- affects: AGENTS.md, .claude/settings.json, .claude/hooks/local_only_guard.py, .github/workflows
- decidedness: Fixed
- reversal_trigger: the product owner withdraws publication, or a second authorised repository is
  named - in which case the guard takes a list rather than being removed

### OPEN-014 - How many loop iterations is too many
- question: LIM-008 caps a loop unit at a thousand iterations. That number is a guess at where a
  parameter sweep stops being something an engineer reads and starts being something that ran by
  mistake; no user has yet hit it
- blocks: nothing - the limit is enforced and reported, so the cost of it being wrong is a refusal a
  user can report rather than a study that silently truncated
- resolve_by: the first study a customer runs that the limit refuses
- decidedness: Open

### XC-202 - Splitting is session state; a saved comparison is a second kind of @View item
- decided: 2026-08-23
- status: active
- decision: comparing is two mechanisms, separated by what the user is doing.
  **Splitting** the canvas into one to four panes is **session state**: each pane may show anything, it
  is never written into a @View definition, and it produces no deliverable at all (XC-204 moved its
  control to the area bar; XC-210 removed the export it was to have had).
  A **@Comparison** is a **second kind of workspace item in the View area**, created from
  `＋ 新規ビュー` beside a single View. Its definition names **one** base @View and varies **exactly one
  axis** over an ordered list of members, arranged either as a grid or as one overlaid picture. The axis
  is a set of subjects - @Case or position on the @Result axis - a named object the base View owns -
  a camera - or **one published property of that base View**: the quantity a field is coloured by, the
  @Deformation scale, the representation, a slice's placement. It owns no materials, lighting,
  background or guides: it borrows every one of them from its base @View, and even the varied property
  is a property of that View. A comparison is reproducible, nameable, and a @Pipeline can produce one
  per @Case.
  **The reference is live**, deliberately unlike a @Template (XC-109): editing the base View changes
  every pane at once, which is why the comparison holds nothing of its own. Deleting a base View
  therefore names the comparisons that point at it before it happens (XC-062), and those comparisons
  are left unresolved rather than silently repointed at another View.
  **An ordered axis may define its members as a range rather than a list.** For a position on the
  @Result axis - and for any numeric property - the members are either picked one by one from the saved
  positions, or generated by dividing a from/to range into a stated number of members. A generated
  member lands on a position that exists and says when it snapped (view/AC-033), and where two of them
  snap to the same stored position that is reported rather than drawn as two identical panes.
  Two consequences for the interface. **The axes not chosen are bound once, in the same group as the
  axis**: a comparison over cases states which single camera and which single result position every
  pane uses, because "everything else is shared" is only checkable if the shared values are written
  down. And **the property rail keeps its full set of tabs but marks the borrowed ones**: removing them
  would leave "where did the material go" with no answer on screen, while leaving them unmarked makes a
  reader click six tabs to find the two that are this item's own
- decided_by: the product owner, 2026-08-23
- rationale: the measured reference separates the same two and gives the second almost nothing of its
  own - a layout carries three properties and no per-pane meaning, while a comparative view's only
  comparison-specific properties are the grid dimension and one grid-or-overlay switch, everything else
  being inherited from an ordinary render view (E-123). Making comparison a work area of its own, or a
  mode with settings inside every View, would give this product a second place to configure materials,
  lighting and background - the duplication P7 exists to prevent. One axis is what keeps the panel
  readable: the reference allows a two-parameter sweep, and that is the setting that makes its panel
  unreadable
- correction: the axis first allowed only the three sets, which cannot express comparing stress against
  temperature, or a surface against a section - both everyday figures in a CAE report. Widening it to
  one published property of the base View costs nothing: the reference measures exactly this, sweeping
  `AnimatedPropertyName` on a named proxy (E-123), and "everything comes from the base View" stays true
  because the varied property is one of that View's own
- alternatives: allowing several saved Views as the members is the obvious flexibility and destroys the
  only thing a comparison is for - two panes from two Views may differ in materials, lighting, colour
  map and camera at once, so the reader cannot say what caused the difference. That case is the split,
  whose export is labelled a layout capture. Keeping only the split costs least and removes the path a
  @Pipeline needs to produce forty comparison figures, and with it any guarantee of a shared colour map
- basis: E-120 (T1), E-121 (T1), E-123 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a comparison that genuinely needs two axes, which would be two nested comparisons
  before it was one panel with a matrix

### XC-203 - Every member of a comparison shares one colour map and one range, or the figure says it does not
- decided: 2026-08-23
- status: active
- decision: within one @Comparison, every member resolves its colour through **one colour-map object
  and one range** (XC-194). Where a range genuinely cannot be shared - a member whose quantity has a
  different @Declared unit, or a per-member automatic range the user chose deliberately - the figure
  states that per pane, beside the member label, and the export carries the same statement. In the
  **overlay** arrangement at most **one** member may carry result colouring; the others are drawn as
  reference geometry, because two colour-mapped fields in one picture encode nothing
- rationale: independently rescaled colour maps in adjacent panes is the standard way to publish a
  misleading comparison, and both references make it the easy path - a per-representation lookup table
  rescaled to visible data. This product's whole claim is that a value looks the same wherever it is
  shown (XC-098); across the panes of one figure that claim is either enforced or abandoned
- alternatives: leaving the range per pane and trusting the author is what the references do, and it
  produces a figure whose two halves cannot be compared by eye - which is the only thing a comparison
  is for
- basis: E-121 (T1), E-123 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-201 - Type is a scale of named tokens, and no rule sets a size, family or weight of its own
- decided: 2026-08-23
- status: active
- decision: type is declared the way colour already is (XC-098, XC-187): a **primitive layer** of six
  size steps, two families, two weights, four line heights and two letter-spacings, and a **semantic
  layer** naming what each step is for. No rule anywhere sets a raw `font-size`, `font-family`,
  `font-weight`, `line-height` or `letter-spacing` value; every rule references a token. Three further
  rules ride on it:
  **a component library's own type is replaced, not inherited** - a primitive that ships with
  `text-sm` renders one and a half times the label beside it and must be given the scale;
  **figures are tabular everywhere**, set once on the document rather than per table, because
  11_ui.md requires numbers to align in columns wherever they appear and a per-site rule is a rule
  somebody forgets; and **the deliverable's typeface is a separate, named token** from the shell's,
  because the tool's own theme and the @Art style of what it produces are different things (GL-013)
- rationale: the catalogue had grown twenty distinct sizes across 368 declarations, four of them within
  one pixel of each other and sixteen sites at 5 or 6 pixels, while the button primitives rendered at
  14. That is not a density choice, it is the absence of one: nobody chose 6px next to 8px next to 14px,
  they each arrived separately and no check could see it. The same argument that made every colour a
  token applies unchanged - a value with no name is a value the next contributor guesses at
- alternatives: keeping the literals and reviewing them by eye is what produced the twenty values. A
  scale with no gate produces them again within a release, which is why the rule is checked rather than
  written down
- basis: E-122 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a step the design genuinely needs between two existing ones, which adds a step to
  the scale rather than a literal to a rule

### XC-199 - A @View owns several named cameras and several named timelines
- decided: 2026-08-23
- status: active
- decision: a @View holds **zero or more named cameras** and **zero or more named timelines**, both
  saved in the View definition. A camera is one object carrying its pose, projection, lens, clipping,
  shift, focus target and depth of field - there is no separate viewpoint concept. A timeline is one
  object carrying the @Result axis range, stride, playback speed, frame rate, loop, the camera path and
  the animation cues. A **pane names the camera it looks through**; an **output names the camera it
  renders from, or the timeline it plays**. One camera and one timeline are active for interactive work,
  and neither the pane binding nor the output binding is limited to the active one
- decided_by: the product owner, 2026-08-23
- rationale: the comparison this product exists for needs several cameras at once - four panes looking
  from four places at four cases - and one camera per View cannot express it. The same argument applies
  to motion: a study needs "the first five seconds slowly", "the whole run at four times speed" and "the
  mode sweep" as three saved configurations, not as three edits to one. The measured reference keeps as
  many camera objects as a scene needs and binds one to a timeline marker (E-120), which is this shape
  with the timeline held singular; holding several is what a @View comparing @Case needs and a 3D
  authoring tool does not
- alternatives: one camera plus a list of poses is what the first attempt shipped, and it separates the
  lens from the position for no reason a user can act on - changing the lens for one saved position then
  changes it for all of them. One timeline per View forces the export settings of two different videos
  to overwrite each other
- basis: E-120 (T1), E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a camera or timeline list long enough that finding one is the slow step, which would
  add scoping and search to the list rather than removing the multiplicity

### XC-200 - A @Timeline is a named playback preset, and camera work is not part of it
- decided: 2026-08-23
- status: active
- decision: a @Timeline holds **six values and nothing else**: the start and end positions on the
  @Result axis, both saved positions that may be rules, the stride, the playback speed, the frame rate
  and whether it loops. It carries **no camera, no shot list and no cues**. A video output names one
  @Timeline and one camera. A @View may hold several timelines, so "the first five seconds slowly" and
  "the whole run at four times" remain two saved objects
- correction: this said twice before that a timeline owns camera work - first as keyframes, then as an
  ordered list of shots each holding one camera. Both were wrong for the same reason, which only became
  visible when comparison was designed: a timeline that owns cameras cannot be paired with a different
  camera, so "the same motion seen from somewhere else" needs a duplicate timeline, and camera stops
  being usable as an axis of comparison. Separating them makes both smaller. The cost is stated rather
  than hidden: a cut from a wide shot to a close-up at the critical moment is now two exported clips
  joined outside this product, not one file
- rationale: the two questions a video answers - **when**, and **from where** - were entangled in one
  object. Held apart, `いつ` is six fields the user can read at a glance and `どこから` is the camera
  list that already exists for stills. The measured reference keeps them apart too: its animation scene
  carries the time behaviour and its cameras belong to the views the scene drives (E-121)
- alternatives: keeping shots optional was the previous answer and leaves the expensive surface -
  shots, cues and camera paths - in the View area for a capability whose demand here is unmeasured
  (OPEN-022's neighbour question, recorded and then decided by the owner)
- basis: E-120 (T1), E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: users routinely exporting two clips and joining them, which would mean the cut
  belongs in the product after all - as a sequence of timelines rather than as cameras inside one

### XC-196 - Camera is its own property tab, and projection and lens leave `全体`
- decided: 2026-08-23
- status: active
- decision: the View property rail's whole-View group is `全体`, **`カメラ`**, **`タイムライン`**,
  `描画`, `背景`, `出力`. `全体` keeps the item's identity, the pane layout with its per-pane @Case and
  camera binding, camera synchronisation, and the guides drawn over the canvas. `カメラ` owns the
  @View's named cameras: projection, lens - focal length or parallel scale, sensor, near and far
  clipping, shift - pose, focus target, depth of field and navigation behaviour, one set per camera.
  `タイムライン` owns the @View's named timelines: the @Result axis range, stride, speed, frame rate,
  the saved result positions, the camera path and the animation cues. `出力` keeps what produces a
  file - kind, format, resolution, destination and preflight - and names which camera or which timeline
  it uses. Nothing appears in two of them
- correction: this first said five tabs, with motion properties left in `出力` and one camera per @View.
  Both were wrong for the same reason: `出力` held the speed, the frame rate and the camera path, which
  describe the motion rather than the file, and a single camera cannot express a four-pane comparison
  where each pane looks from somewhere different. XC-199 records the multiplicity; this row records
  that the rail grew a tab to hold it
- rationale: both measured references treat the camera as an object rather than a line in a general
  section. ParaView's render view carries 31 camera properties and reaches them through a dedicated
  dialogue; Blender's camera is a data-block with its own tab and five sub-panels, and a scene holds as
  many of them as it needs. `全体` held camera as one selector, which stops being tenable the moment
  named cameras, a focus target and depth of field exist - and those are what XC-197 and XC-199 add
- alternatives: keeping camera in `全体` costs no spec change and turns `全体` into the section that
  holds whatever has no home, which is the failure the named-responsibility rule of XC-182 exists to
  prevent
- basis: E-120 (T1), E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a rail that no longer fits its column at the supported widths, which would collapse
  labels to icons before it removed a responsibility

### XC-197 - A saved viewpoint and a saved result position store the rule, not the number
- decided: 2026-08-23
- status: active
- decision: a @View's cameras and its saved **result positions** each store either an explicit value or
  the rule that produces one. A camera's pose is an explicit position, focal point and up vector, or a
  framing of a target - a @View object, a named selection, a coordinate, or **an extremum of a
  quantity**. A result position is an index on the @Result axis, or an extremum of a quantity, or the
  first crossing of a threshold. A rule **resolves per @Case**, so one entry named `最大応力時` shows
  each pane its own critical position. Resolution obeys three rules: it lands on a position that exists
  on the axis and says so when it snapped; it reports the value it resolved at with its @Declared unit
  and @Provenance; and where it cannot resolve it names the missing quantity and **leaves the camera and
  the position where they were**
- rationale: this is the rule CT-004 already applies to a colour range - the definition records the rule
  that produced a number, never numbers pretending to be a choice - applied to the two other places a
  number is chosen from data. It is also established need rather than invention: ParaView ships a
  `CriticalTime` filter whose whole purpose is the position at which a value crosses a threshold, and
  Blender binds a camera to a timeline marker and focuses depth of field on an object rather than a
  distance
- alternatives: storing the resolved numbers is simpler and silently wrong the moment the @Case changes:
  a four-pane comparison would show four panes at one case's critical moment
- basis: E-120 (T1), E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a rule whose resolution is too slow to run on selection change, which would cache the
  resolution with its inputs rather than store the number as a choice

### XC-198 - Grading is a group inside `描画`, defaults to no grade, and never leaves the legend disagreeing
- decided: 2026-08-23
- status: active
- decision: exposure, contrast, tone mapping, white balance and the other image treatments form one
  `現像` group inside `描画`, after `照明`, with a preset at its head - `計測`, `標準`, `技術文書`,
  `プレゼン`, `フォトリアル`. **The default is `計測`, which applies no grade.** Where a grade would
  change pixels that encode a value, one of two things must hold: the legend is rendered through the
  same grade, or the export records the grade by name and parameters in the deliverable. A treatment the
  active backend cannot perform is named rather than offered
- rationale: both references ship this and neither has this product's constraint. ParaView's render view
  carries tone mapping with filmic presets, exposure, contrast, ACES, antialiasing, ambient occlusion,
  shadows, sample count, denoising and depth of field; Blender puts view transform, look, exposure and
  white balance in scene colour management. Applied here without a rule, a tone curve makes two
  screenshots of one result show one value as two colours, which is exactly what XC-098 forbids
- alternatives: refusing grading entirely keeps the guarantee and produces pictures nobody wants to put
  in front of a customer, which is the job this product exists to do. A group with a measurement default
  and a disclosure rule keeps both
- basis: E-120 (T1), E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a grade that cannot be applied to the legend and cannot be described in the export,
  which would make that treatment unavailable rather than undisclosed

### XC-190 - The shell is Window, Screen, Area, Region - and the six work areas are Screen presets
- decided: 2026-08-22
- status: active
- decision: the application shell is four nested things. A **Window** holds one open @Workspace. A
  **Screen** is a named, saveable layout: a binary split tree of Areas. An **Area** hosts exactly one
  editor kind and is the unit of split, join and maximise. A **Region** is a sub-surface of an Area
  drawn from one fixed vocabulary - `main`, `header`, `navigator`, `properties`, `shelf`, `composer`,
  `overlay`, `footer` - and an Area declares which of them it may show. The six workflow tabs
  (Simulation, View, Graph, Report, Automation, Chat) are **built-in Screen presets**, not six
  different shells, and the three-column layout of [11_ui.md](../specs/11_ui.md) is the default preset
  rather than the definition of the product's window
- rationale: the measured reference (E-120) reaches nineteen editors and sixteen region kinds with one
  grammar, and every panel in it is located by four fields. Without such a grammar each new surface -
  a table, a diff, a node graph, a log - arrives as a bespoke screen, and the shared components of
  11_ui.md gain a second implementation each time, which is exactly the failure P7 names
- alternatives: keeping the fixed three-column shell is simpler and is what r1 ships. It cannot express
  a second canvas beside the first, which the complete product needs for Diff, Table and the node
  editor; adding those as modes of the centre column makes the centre column a switch statement over
  unrelated editors
- basis: E-120 (T1), E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a saved Screen that cannot be reproduced on another window size, which would mean
  layout must be derived rather than stored

### XC-191 - A table and a chart are areas beside the 3D viewport, not features inside it
- decided: 2026-08-22
- status: active
- decision: the complete product has a **Table area** and a **Chart area** as peers of the viewport,
  each editing a saved @Workspace item of its own kind, each with the same regions and the same
  property rail grammar. A table is not a panel inside View, and a chart is not an export of a table.
  The Table area shows values with their @Declared unit, @Significant digits and @Provenance - the
  `Number cell` component of 11_ui.md - over a chosen association (point, cell, field, case or
  variable), with row filters, sorting and column selection
- rationale: the measured reference (E-121) reaches eighteen view types through one representation
  model, of which the spreadsheet is one; the product's own claim is trustworthy numbers, and until
  now the only place a number appeared at full precision was a probe readout and a report table. A
  reader who wants to check a figure has nowhere to look
- alternatives: a table dialogue over the current view is less work and cannot be saved, cited from a
  report, or produced by a @Pipeline unit, so the number in the deliverable and the number on screen
  would come from two paths - the failure INV-001 exists to prevent, one level up
- basis: E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: none foreseen

### XC-192 - Display state is stored on the display object, never on the data
- decided: 2026-08-22
- status: active
- decision: no display property is stored on a @Dataset, a @Field or a @Case. Representation,
  opacity, colour, visibility, overlays, guides and camera live on the @View and its @View object; the
  colour map lives on the workspace colour-map object; the data carries only what was read from the
  file plus its @Provenance. Reading a file twice yields the same @Dataset whatever any View looks like
- rationale: the measured reference (E-120) keeps 40 shading properties and 95 overlay properties on
  the viewport and none of them on the mesh, which is why the same mesh can appear in two editors at
  once without one of them changing the other. INV-001 already separates the reported number from the
  drawn picture at computation time; this states the same separation at rest, so a workspace cannot
  reach a state where deleting a View changes what a number is
- basis: E-120 (T1)
- affects: 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a display property that genuinely belongs to the data - a solver-authored preferred
  colour map, say - which would be read as data with provenance rather than written as display state

### XC-193 - A key binding is scoped to an area, and a destructive command may hold none
- decided: 2026-08-22
- status: active
- decision: the keyboard scheme is a set of **keymaps scoped by area**, each holding bindings of
  `command` plus a key descriptor - key, press or release or drag or double-click, the modifier set, an
  optional second key, and the command's own parameters. A binding names a command from the command
  surface (CT-002) and nothing else, so a key can do only what a click can do. Global bindings live in
  one `global` keymap; an area keymap may shadow it, and the resolved binding for any key is reported
  in the command list. A command whose descriptor says `destructive` is refused a binding at
  registration time, in every keymap, rather than being left unbound by convention (XC-062, XC-094)
- rationale: the measured reference (E-120) resolves 2442 operators through 105 area-scoped keymaps,
  which is how the same key means one thing in a tree and another on a canvas without either area
  inventing its own dispatch. The prohibition is the part a convention cannot hold: 11_ui.md already
  says nothing destructive has a single-key shortcut, and until it is a property of the command that
  the registration checks, it is a promise the next contributor breaks by accident
- alternatives: one flat keymap is simpler to display and forces every area to prefix its keys, which
  is how a product ends up with three-key chords for the operation used most
- basis: E-120 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a command that is destructive in one area and not in another, which would move the
  flag from the command to the binding rather than removing it

### XC-194 - A colour map is a workspace object that bindings reference, never a copy per object
- decided: 2026-08-22
- status: active
- decision: a colour map - its control points, opacity points, interpolation, out-of-range treatment,
  missing-value colour and the rule that produced its range - is a **named object owned by the
  @Workspace**. A @View object, a @Graph series and a @Report table cell reference it by identifier and
  revision. Changing the map changes every place that references it, and a place that must not follow
  takes its own copy explicitly. The scalar bar is a separate object referencing the same map, so two
  panes may show one map with different bar placement
- rationale: the measured reference (E-121) makes the lookup table its own proxy that representations
  point at, and the scalar bar a second one - which is why re-colouring a comparison changes both panes
  at once. XC-098 already says a colour encoding a value must look the same in light and dark; the same
  argument applies across panes and across the report, and it only holds if there is one object to be
  the same
- alternatives: embedding the map in each Material Binding is what CT-004 does today and is right for
  r1, where one View has one binding. Across a four-pane comparison and a report of the same study it
  produces four maps that drift apart, and two screenshots of one result that do not match
- basis: E-121 (T1)
- affects: 16_application_model.md
- decidedness: Fixed
- reversal_trigger: none foreseen; the r1 embedded form migrates by promotion, each embedded map
  becoming a named object on first save of the complete format

### XC-195 - The @Case tree is the navigation, and a derived quantity does not become a node in it
- decided: 2026-08-22
- status: active
- decision: the left navigator lists @Case, @Variable and @Reference material, and nothing else. A
  @Derived quantity, a filter, a slice, a resampling or a @Diff produces a quantity or a @View object
  with its own @Provenance; it does not add a row to the case tree, and it never renames or reparents a
  @Case. Batch composition of such steps is the @Pipeline, which is a saved document of its own and is
  reached from Automation
- rationale: the measured reference (E-121) makes the pipeline browser the primary navigation, so every
  operation adds a node and the tree grows to the length of the session. That is coherent there because
  its subject is a dataset being transformed. This product's subject is the @Case, which the user named
  and can find again tomorrow; a tree that also holds `Clip1`, `Clip2`, `Threshold3` stops answering
  the question it exists to answer. Keeping derivation in provenance rather than in navigation is also
  what lets a @Pipeline replay it over forty cases without forty trees
- alternatives: a pipeline browser is more discoverable for exploratory work and is how a ParaView user
  expects to work; the Automation area is where that expectation is met, with the derivation explicit
  and repeatable rather than accumulated by accident
- basis: E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: users unable to retrace how a quantity was produced, which would mean provenance is
  not visible enough - a display problem, not a navigation one

### XC-189 - The required screen states live in the specification, not in the test that checks them
- decided: 2026-08-22
- status: active
- decision: `specs/11_ui.md` carries a **Required screen states** table, and
  `tests/test_ui_mockup_catalog.py` reads it. The design catalogue in
  `mockups/ui/lib/screen-catalog.json` must match that table exactly, in both directions
- decided_by: found on 2026-08-22 while auditing the mockup against the interface specification
- basis: E-001 (T1)
- why: the test held the same list hand-copied into a Python set and compared the catalogue against
  that copy. **A state this specification required, absent from both, was undetectable** - the check
  reported coverage while measuring only that two copies of one list agreed. It is the defect of a gate
  nothing invokes, one level up: the gate ran, and what it measured was not what it claimed
- what_it_found_immediately: six states the specification requires and the catalogue never had -
  `simulation.default`, `simulation.empty`, `simulation.unresolved`, `view.deformation`, `view.probe`
  and `settings.shortcuts`. `view.deformation` and `view.probe` are the interface halves of INV-024 and
  of the probe readout, both of which the specification has required throughout
- alternatives: deriving the list from the catalogue makes the artefact its own contract; leaving it in
  the test keeps two copies and the defect that produced this decision
- affects: 11_ui.md, mockups/ui, tests/test_ui_mockup_catalog.py
- decidedness: Fixed
- reversal_trigger: the product interface exists and its own routing becomes the enumerable source, at
  which point this table states what that routing must cover

### XC-188 - A check that cannot pass is turned off, never made to pass
- decided: 2026-08-22
- status: active
- decision: the automated Claude review and the `@claude` interaction workflow do not trigger on a
  pull request. Both keep their files, their prompts and their guards, and both remain runnable by
  hand through `workflow_dispatch`. A pull request is therefore judged by CI alone: `repository gates`,
  `tests` and `mockup catalogue typecheck`
- decided_by: the product owner, 2026-08-22, deferring CLAUDE_CODE_OAUTH_TOKEN
- basis: E-001 (T1)
- why: with no token the review job failed on every pull request. That is the correct failure mode -
  a review that did not happen must not report success - and it is the wrong thing to leave on a
  screen. **A check that is red for a reason unrelated to the change teaches everyone to read red as
  normal**, which is precisely how the next real failure gets waved through. The same argument the
  spec model makes about a linter that is normally red (6.5)
- what_was_not_done: the job was not given a "skip when the secret is absent" branch. That version
  reports success for a review nobody received, which is the one outcome worse than a visible failure
- alternatives: deleting the workflows loses the review prompt, the model policy and the
  silent-success guard, and re-creating them later is a design session rather than a two-line change;
  `gh workflow disable` turns them off invisibly, so a reader of the repository would believe reviews
  run - the "looks enforced and is not" state this project keeps finding and refusing
- affects: .github/workflows/claude-code-review.yml, .github/workflows/claude.yml, CONTRIBUTING.md
- decidedness: Fixed
- reversal_trigger: `CLAUDE_CODE_OAUTH_TOKEN` is set as a repository secret, at which point the
  commented triggers in both files are restored and this decision is superseded rather than deleted
- superseded_by: XC-219, which decides what happens on that day - the review returns as a **merge
  condition**, not merely as a check - and adds the CI job that fails if the secret is set while the
  trigger is still commented out. This decision stays in force until both are true
### XC-187 - A colour, a size or a duration has one definition, and roles are layered
- decided: 2026-08-22
- status: active
- decision: every colour, spacing, radius, duration and z-index the interface uses is a **token**, and
  tokens come in two layers that may not be collapsed. A **primitive** names a value once
  (`--white`, `--blue-500`); a **semantic** token names a role and references a primitive
  (`--card: var(--white)`). Component styles reference semantic tokens and never a raw literal. One
  name carries one role, and one colour is written in one notation. Enforced by
  `validate/check_constant_duplication.py`, which reads CSS as well as source files
- decided_by: found on 2026-08-22 while incorporating the owner's design rules into the project
- basis: E-001 (T1)
- why_two_layers: a single flat layer forces a false choice the moment a literal has to be replaced.
  `#ffffff` appearing in a component is either the card background or a label drawn on blue, and a
  flat token set offers only `--card` - so the honest options are to guess a role or to leave the
  literal. A primitive layer lets the value be centralised without asserting a meaning it may not have
- measured_2026_08_22: `mockups/ui/app/globals.css` held 611 colour literals of 329 distinct colours
  against 51 declared tokens. `--muted` was declared twice in one `:root` block - once as a light
  background (`#f1f4f6`, the shadcn role) and once as grey body text (`#6f7e88`) - and the second won,
  so every `bg-muted` rendered dark with nothing reporting it. White was written both `#fff` and
  `#ffffff`, which defeats any count of either
- alternatives: a linting rule that forbids literals outright fails on the cases where no token should
  exist yet and teaches people to disable it; a single flat token layer produces the false-role guess
  described above
- affects: 11_ui.md, MOD-010, mockups/ui
- decidedness: Fixed
- reversal_trigger: the interface adopts a design-token toolchain that owns the layering itself, at
  which point this states the contract that toolchain must satisfy rather than the mechanism

### OPEN-022 - Whether the mockup may show a number at all, given that it may not invent one
- question: `mockups/ui/AGENTS.md` says the catalogue must never invent analysis values, and the
  catalogue nevertheless shows several: the probe readout gives 182.4 MPa and 0.00317 m, and the
  variable list gives a computed safety factor of 1.83. They are there because `Number cell`,
  `Variable row` and `Probe readout` exist to demonstrate INV-013 and INV-014 - a value with its
  unit, its significant digits and its provenance - and a placeholder demonstrates none of that: `—`
  has no digits to be correct to
- why_open: the two rules pull in opposite directions and only a person can decide which loses. A
  reviewer reading the probe state cannot tell whether 182.4 MPa is a placeholder or a claim, which is
  the confusion the no-invented-values rule exists to prevent; but replacing it with `［値］` removes
  the only place the significant-digits and provenance rules are visible before the product exists
- blocks: nothing today. The catalogue is design states and never evidence of implemented behaviour
- closes_when: either the catalogue adopts one marked fixture - a named synthetic dataset whose values
  are stated to be fixture values wherever they appear, as the material library already does with
  `サンプルデータ` - or the demonstration moves to the product and the catalogue drops the numbers
- affects: mockups/ui, INV-013, INV-014
- decidedness: Open

### OPEN-021 - Which of the remaining colour literals should become tokens, and as which role
- question: after the duplicate declaration and the two spellings of white were fixed,
  **133 colour literals across 18 colours remain in `mockups/ui/app/globals.css` whose exact value is
  already held by a declared token** - 100 of them white, where `--card`, `--background`, `--popover`,
  `--primary-foreground` and `--destructive-foreground` all hold `#ffffff`. Which token each site
  should reference is a question about what that pixel *means*
- why_open: it cannot be answered mechanically, and answering it mechanically is the failure mode this
  project spends most of its rules on. Replacing every `#ffffff` with `var(--card)` would centralise
  the value and assert a role at 100 sites without checking one of them, producing a file that looks
  disciplined and misleads the next reader about what each element is
- blocks: nothing today. The catalogue is design states and never shipped code; XC-187 governs the
  product interface, which does not exist yet and can be built with the layering from the first line
- closes_when: the primitive layer of XC-187 exists, and each remaining literal is either replaced by
  the semantic token whose role it actually has, or replaced by a primitive where no role is settled
- affects: XC-187, mockups/ui
- decidedness: Open

### OPEN-020 - How the append-only rule is enforced on the server, not only on this machine
- question: XC-186 refuses force-push, hard reset and history rewriting, and `check_specs.py` and the
  other six gates decide whether a change may land. **None of that is enforced by GitHub.** Measured
  2026-08-22: `POST /repos/{owner}/{repo}/rulesets` and
  `PUT /repos/{owner}/{repo}/branches/main/protection` both return HTTP 403 with
  "Upgrade to GitHub Pro or make this repository public" - branch protection is not available for a
  private repository on a free personal account
- why_open: the three ways out are a paid plan, an organisation account, or making the repository
  public, and each is a decision about the business rather than about the code. Making it public is the
  one that must not be taken casually: `specs/12_business_model.md` carries pricing, revenue model and
  competitor analysis, and XC-082 publishes the **source** under FSL-1.1-MIT without publishing that
- what_is_in_force_meanwhile: `.githooks/pre-push`, versioned and installed with
  `git config core.hooksPath .githooks`, which refuses a non-fast-forward push, a branch deletion by
  push, and a push whose gates are red - **the only one of these guards that runs in a plain
  terminal**, which is where a force-push typed from muscle memory actually happens. Client-side, and
  skippable with `--no-verify`: it catches the push nobody meant to make, not the one somebody
  insists on. Beside it: the pre-tool-use hook, which runs only inside an agent session; rebase merges
  disabled at the repository level, which the free plan does permit; Dependabot alerts and automated
  security fixes enabled. CI runs on every push and pull request and reports honestly - it simply
  cannot **block** a merge
- blocks: **XC-218, as of 2026-08-23.** Automatic merge needs a gate that a change cannot walk past,
  and with no server-side enforcement the gate is a workflow in the same repository the change is
  editing - which is why that workflow refuses to merge anything touching `.github/` or `validate/`, and
  why the reference design keeps merge authority off the agent entirely (E-129). Before that it blocked
  nothing, with one maintainer and no other contributors; it becomes urgent the moment a second person
  can push, because at that point the rule exists only in a document
- closes_when: a plan or account type is chosen that permits a ruleset, and the ruleset requires the
  three CI jobs by name - `repository gates`, `tests`, `mockup catalogue typecheck` - with
  non-fast-forward and deletion refused. The ruleset JSON is written and was rejected only by the plan
- affects: XC-186, CONTRIBUTING.md
- decidedness: Open

### OPEN-019 - Whether to move the engine from VTK 9.5.2 to 9.7.x, and what it costs to do so
- question: 9.7.0 was released 2026-08-15 and is the version whose source was read for the module
  licence set (E-045). The engine pins 9.5.2, and every first-hand measurement this specification
  relies on was taken on 9.5.2: the 393.8 MB install and the gl2ps binaries (E-051), the 184 reader
  classes and the 23 of 24 filter families (E-060), and the per-point memory cost (E-053). Moving the
  pin invalidates all of them at once
- why_open: the move is not a version bump, it is a re-measurement. LIM-001, LIM-002, LIM-004 and
  XC-049 each cite a number taken on 9.5.2, and XC-041's obligation table is **already** read from a
  different release than the one that ships - the 27 Sandia-variant modules are counted in the 9.7.0
  source while the binaries whose notices must travel are 9.5.2's. Deciding the move without redoing
  the spikes would replace measured values with values that merely look measured
- blocks: nothing today. 9.5.2 is pinned, checked by XC-185, and every value describing it is true of it
- closes_when: the spikes under `spike/` are re-run against a 9.7.x environment and either confirm the
  existing numbers within their stated tolerance or replace them, and the module licence set is read
  from the tree that actually ships rather than from the newer source release
- affects: EXT-001, LIM-001, LIM-002, LIM-004, XC-041, XC-049
- decidedness: Open

### OPEN-018 - Measured hostile MaterialX parser and image limits
- question: LIM-013 requires independent XML/tree depth, XInclude/dependency, expanded-byte and decoded-
  pixel ceilings. What values keep the pinned MaterialX 1.39.5 parser and image stack within the target
  workstation memory and response budgets while accepting the largest real material corpus?
- why_open: MaterialX now validates unusually deep XML/XInclude trees, but its safe application-level
  package and decoded-image limits depend on the exact build and image handlers. No local hostile-input
  spike or representative maximum corpus has been measured, and inventing four numbers would create a
  false security boundary
- closes_when: a checked-in spike exercises recursive includes, broad dependency graphs, compressed
  expansion and oversized decoded images against the target hardware, records peak memory/time and
  selects the lowest ceilings that admit the representative corpus with stated headroom
- decidedness: Open

### XC-204 - A split control belongs to the area bar, and the canvas stays a picture until it is split
- decided: 2026-08-23
- status: active
- decision: the pane count and camera synchronisation are set from **one menu in the work area bar**,
  behind a single icon that names the current count when the layout is divided. **The 3D canvas carries
  no split control at all.** Once the canvas is divided it gains a strip that states the split is not
  saved, points at the pane badges for what each pane shows, and offers `この比較を保存` and
  `1画面に戻す` - all of them things that only make sense once there is more than one pane. Each pane's
  @Case and camera stay on the pane badge. The control is absent for a @Comparison, whose pane count
  comes from its member list, and in every area with no panes
- decided_by: the product owner, 2026-08-23
- rationale: the two placements answer different questions. What each pane shows is a property of that
  picture and belongs on it; how many panes there are is a property of the layout, and the work area bar
  is the layout's own header - the same place the edit/list mode switch and the item selector already
  sit. Placing the count on the canvas made a control for a rarely-used feature into permanent chrome
  over the picture, which is what the product is for looking at
- correction: XC-202 said every split control is on the canvas, and that produced a strip of four
  buttons standing over the 3D view of every single-pane @View, permanently, for a feature most sessions
  never reach. Trimming its prose was a symptom fix and left the buttons; the placement was the cause.
  XC-202's separation of session state from the saved item is unchanged - only where the session control
  is drawn
- alternatives: removing ad-hoc splitting outright is simpler still and was rejected because comparing
  while working is a stated need and a @Comparison is a saved item, not a glance. Keeping the count in
  both places would give one value two controls
- basis: E-121 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a measurement showing users hunt for the split, which would make an on-canvas
  affordance worth its permanent cost

### XC-205 - A comparison's grid sets its columns only, and its rows follow from the member count
- decided: 2026-08-23
- status: active
- decision: a @Comparison arranged as a grid exposes **one** arrangement control in the property rail:
  the **column count**, either `自動` or one to four. **The row count is always derived** as
  `ceil(members / columns)`, so no setting can produce a grid that leaves a member undrawn. `自動` places
  the members on one line and wraps only when they no longer fit. The canvas is laid out from that same
  computed value rather than from a rule of its own. The area bar's split control stays absent on a
  comparison: a comparison's panes are its members, and a session control that overrode them would be a
  second source for one number
- decided_by: the product owner, 2026-08-23
- rationale: the measured reference carries the grid dimension as a real property of a comparative view
  (E-123), and the reason this product had removed it - that a hand-set grid hides members - applies
  only to setting **both** dimensions. Setting the columns alone cannot hide anything, because the rows
  are what absorbs the remainder. `自動` wraps rather than squares because the members are an ordered
  axis and one line is the reading order
- correction: the grid was made read-only and derived as `min(members, 4)` columns after a defect where
  the panel stated a grid the canvas did not draw. That fixed the disagreement by removing the user's
  say, and left two further faults: six members drew as four and two rather than the three and three a
  reader would ask for, and the canvas stylesheet still forced **one row** whatever the panel said, so
  the disagreement it was meant to end was still present above four members
- alternatives: keeping it derived costs nothing to build and leaves no way to produce a 3x2 contact
  sheet, which is an ordinary figure. A free rows-and-columns pair is what the reference offers and is
  the thing that can hide a member
- basis: E-123 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a comparison whose members should be read down the columns rather than along the
  rows, which would make the row count the chosen one

### XC-206 - The area bar's layout menu answers one question for both kinds of View item
- decided: 2026-08-23
- status: active
- decision: the work area bar carries **one** layout control, and what it sets depends on the kind of
  item open. On a single @View it is the **session split**: one to four panes, and camera
  synchronisation. On a @Comparison arranged as a grid it is the **column count** its members wrap at -
  `自動`, or one to four - with the menu stating that the pane count is the member count and cannot be
  set. The control is absent only where there is no canvas of panes to lay out: an overlaid comparison,
  which draws one picture, and every area with no panes. The property rail no longer offers a second
  control for the column count; it reports the row and column the layout resolved to
- decided_by: the product owner, 2026-08-23
- rationale: a control that vanishes when the item changes reads as a feature that is missing rather than
  one that does not apply, and the reader has nothing on screen to tell the two apart. Binding it to the
  one question both kinds answer - how this canvas is laid out - keeps it in place across the switch, and
  costs nothing, because each kind already had that value: the split for a @View, the column count for a
  @Comparison
- correction: XC-204 made the control conditional on `!isComparisonItem`, so opening a comparison made it
  disappear with no explanation. The reasoning behind that - that a session split must not override
  member-derived panes - was sound and is unchanged; what was wrong was concluding that the control had
  to be removed rather than bound to the comparison's own arrangement. XC-205 then placed the column
  count in the property rail, which is the second control this decision removes
- alternatives: showing the control disabled with a reason keeps the position and gives the comparison no
  way to arrange itself, which is the state that prompted this. Leaving the column count in the rail as
  well would give one saved value two controls, and the two can be reached from different places with
  different labels
- basis: E-121 (T1), E-123 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a third kind of View item whose canvas has no arrangement at all, which would make
  the control conditional again

### XC-207 - An area opens in its resting state, and a control is named and sized for what it is
- decided: 2026-08-23
- status: active
- decision: four rules the interface had been breaking in four places.
  **Entering a work area lands on that area's declared baseline state**, never on whichever of its
  catalogue states happens to sort first.
  **The property rail's first View section is named after the item it edits** - `ビュー`, or `比較` when
  a @Comparison is open - not `全体`. Graph and Report keep `全体`, where the contrast with their
  per-selection tabs is real.
  **A control is sized for its content**: only an icon-only button is a fixed-size circle, and a button
  carrying a label is sized to that label and never wraps it. Where a surface is too narrow for the
  labels, the button keeps its meaning as its accessible name and tooltip rather than keeping a label it
  cannot draw.
  **The assistant's identity mark is a chat mark**, not a four-point sparkle.
  **A row that can be dragged is drawn as an object that can be picked up**: a frame, a grip and a grab
  cursor
- decided_by: the product owner, 2026-08-23
- rationale: each of these is a case of the interface asserting something untrue. Opening the View area
  on `assistant-drawer` presented a demonstration state as the product's resting state, with the chat
  covering the 3D view before the user had asked for it. `全体` named a bucket in a rail where four other
  tabs are equally "the whole view". A blanket `.chat-composer button` rule sized every button as a 27px
  circle, so the two text buttons wrapped one character per line and spilled through the composer's
  frame - the defect is in the blanket rule, not in the two buttons. A four-point sparkle is another
  assistant's brand mark. A draggable row drawn as plain text says nothing about the drag, and the
  sentence under the list was the only place it was stated
- alternatives: opening the drawer by default is defensible if the assistant is the intended entry point,
  and it is not: the area is for looking at geometry, and the instruction bar already offers the
  conversation in one line. Naming the section `項目` covers both kinds without saying which is open
- basis: E-120 (T1), E-121 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: usage showing the assistant is the first thing reached in the View area, which would
  make the drawer the resting state rather than an opened one

### XC-208 - Every rail section is named for what it holds, and no icon stands for two of them
- decided: 2026-08-23
- status: active
- decision: **the first section of View, Graph and Report is named after the item it edits** - `ビュー`
  (`比較` when a @Comparison is open), `グラフ`, `レポート` - not `全体`, and the three share one icon
  because they are one concept. **`詳細` is replaced by what the section actually holds**: Graph
  `データ`, which is the cases and series the graph is drawn from with their quantity, unit and
  provenance; Report `内容`, which is the reference scope, the blocks collected and the commentary
  method. **`LayoutTemplate` is reserved for @Template** and appears on no rail tab. **The background
  tab uses a world icon**, not a picture. And **no icon stands for two unrelated sections**: one icon
  may cover several tabs only where they are the same concept, either one shared id named per area or
  one shared label
- decided_by: the product owner, 2026-08-23
- rationale: `全体` and `詳細` are both bucket names - they say where something was put, not what it is,
  and a reader cannot predict either from the rail. The icons were worse than the names: the section
  XC-149 renamed away from `テンプレート` was wearing the Template icon, so the rail said the word the
  name was chosen to avoid, and in Report it sat next to `LayoutGrid` as a second grid glyph meaning
  something else. `SlidersHorizontal` stood for Pipeline `設定` and for both `詳細` buckets at once,
  which is a symbol taught and then contradicted. The measured reference names the background tab World
  and the panel is solid, gradient, image or environment, so a picture icon names one of its four cases
  (E-120)
- correction: XC-149 renamed the former Template section to `全体`, which fixed the confusion with the
  material library and left a name that says nothing. The rename it needed was to the item, not to a
  word for "not one of the others"
- alternatives: `定義` for all three avoids repeating the area's own word in its rail, and gives up
  telling the reader which kind of item is open - which View needs, having two. `項目` is the same
  trade with a vaguer word
- basis: E-120 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a fourth editing area whose first section is not an item, which would make the
  shared icon a claim about something it is not

### XC-209 - The canvas carries no split chrome at all; the split's own two facts are in its menu
- decided: 2026-08-23
- status: active
- decision: the 3D canvas shows no split control or caption at **any** pane count. The strip that used
  to appear once the canvas was divided is removed, and the two things in it that existed nowhere else
  move into the work area bar's layout menu, shown only while `panes > 1`: the statement that the split
  is session state and is not saved, and the action `この比較を保存`. The dialogue that action opens is
  unchanged; only its trigger and its open state move
- decided_by: the product owner, 2026-08-23
- rationale: of the strip's parts, `3画面` repeated the bar's own button, `1画面に戻す` repeated the
  menu's first item, `カメラ同期はオンです` repeated a checked item in the same menu, and the sentence
  telling the reader to click a pane's badge described a dropdown trigger that already draws a chevron.
  Four of six parts were a second rendering of a control one row above, and the two that were not are
  the ones worth keeping. A caption band over the picture is the most expensive place in this product to
  restate something
- correction: XC-204 removed the strip at one pane and kept it once split, on the reasoning that what it
  said only made sense once divided. That was true of two of its parts and false of the other four -
  they made sense at any pane count and were already on screen. The placement rule XC-204 established,
  that the layout belongs to the area bar and the picture to the canvas, is unchanged; this carries it
  the rest of the way
- alternatives: keeping a one-line `保存されません` caption on the canvas keeps the warning in view
  without a click, at the cost of a permanent band over the picture for a state the bar already shows by
  reading `3画面`; the export path states the same thing where it decides something (XC-202)
- basis: E-121 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a user exporting a split believing it reproducible, which would mean the statement
  needs to be in view rather than in the menu that sets it

### XC-210 - A split is for looking, not for output; the deliverable comes from the item
- decided: 2026-08-23
- status: active
- decision: splitting the canvas is a way of **looking while working** and is **not an export path**.
  The output tab writes the one camera it names, whatever the canvas is divided into, and while
  `panes > 1` it states that the split is not included and names the route that is: `この比較を保存`,
  which creates a @Comparison. The layout menu says the same where the split is made. The split keeps
  its freedom - each pane may show any @Case and any camera - precisely because it produces no
  deliverable: that freedom is what makes a pair of panes able to differ in several ways at once, which
  is useful to look at and is not a figure anyone should publish
- decided_by: the product owner, 2026-08-23
- rationale: this product's claim is that a picture supports the comparison it invites. A @Comparison
  earns that by varying exactly one axis and sharing one colour map and range (XC-202, XC-203); a split
  earns none of it. Offering a split export with a label attached puts the burden on a caption, and a
  caption is read after the figure has already been believed. Keeping the split as a working tool costs
  nothing and removes the case entirely
- correction: XC-202 said the split's export is "labelled a capture of a layout", and that export was
  never built - the output tab has only ever written a single named camera. So the specification claimed
  a guard for a path that did not exist, which is worse than either answer: a reader of the spec would
  conclude the case was handled. It is resolved by removing the path rather than adding it, and by
  saying so in the two places a user meets it
- alternatives: building the labelled export matches the measured reference, which can save a screenshot
  of a whole layout (E-121), and gives this product a second route to a multi-pane figure whose only
  protection is its caption. A screenshot of the application window remains available to anyone who
  wants exactly that, and it is not this product asserting the picture is a result
- basis: E-121 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a comparison that cannot express a figure users legitimately need, which would mean
  the split has to become reproducible rather than the export being removed

### XC-211 - A pipeline unit names the item it produces, and will not run until it does
- decided: 2026-08-23
- status: active
- decision: a @Pipeline unit that produces a @View, @Graph or @Report names **which** item - chosen from
  the workspace items of that kind, or from a template - and a @Comparison is one of the choices. Until
  an item is named the unit is unresolved and the run is refused; no default item is substituted
- decided_by: the product owner, 2026-08-23
- rationale: XC-202 says a @Pipeline can produce one @Comparison per @Case, and the unit editor offered
  only `ワークスペース項目` or `テンプレート` with no way to say which - so the capability the decision
  claimed could not be expressed at all. Refusing rather than defaulting is XC-001 applied to a
  definition: a run that quietly picked the first View would produce forty figures of the wrong thing
- basis: E-121 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a unit kind whose output is not a workspace item

### XC-212 - A comparison's output writes the grid, and asks nothing its definition already answers
- decided: 2026-08-23
- status: active
- decision: a @Comparison's `出力` tab writes the whole grid as an image or a video. It **does not ask
  for the camera or the position on the @Result axis**: each is either the axis being varied or the shared
  binding named in the `比較` tab, and the tab reports which. A comparison whose axis **is** the
  @Result axis
  **cannot be written as a video** - every pane is pinned to its own position - and the tab says so and
  names what to change; over any other axis every pane advances together along the shared position
- decided_by: the product owner, 2026-08-23
- rationale: the output tab was the single-@View one, unchanged, so it offered a camera picker beside a
  comparison whose axis was already the camera. That is two controls for one value with no way to tell
  which the written file used - the failure this project treats as worse than a missing feature, because
  the file leaves the building. Reporting the binding instead keeps one definition and still answers the
  question the tab is opened to answer
- correction: XC-202 established that a comparison keeps `出力` as its own tab rather than borrowing it,
  and nothing was done to that tab, so "its own" meant "the View's, applied to something else"
- alternatives: letting the output tab override the comparison's camera for one export is the flexible
  reading and produces a file that does not match the item that names it
- basis: E-123 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a comparison over the result axis that should animate some other axis instead, which
  would make the video rule depend on two axes rather than one

### XC-213 - The Graph rail is five sections, and one of them is the axis it never had
- decided: 2026-08-23
- status: active
- decision: the Graph property rail is **`グラフ` / `データ` / `軸` / `スタイル` / `出力`**, five sections
  where there were six.
  `種類` folds into `グラフ`: the dimension and the chart form are two fields and the first thing chosen.
  `テキスト` folds into `スタイル`: type is part of how a chart looks, and a separate tab split one look
  across two places.
  **`軸` is new.** One axis is chosen - `X（横）`, `Y（左）`, `第2Y（右）` - and the same fields serve
  whichever is chosen: title, unit annotation, range (data-fitted or fixed), log scale, tick interval,
  notation and precision, and grid lines. **A fixed range that excludes data says so on the figure and
  in its export.**
  **A series carries its own colour, line, marker and axis pair, on its own row in `データ`**, beside its
  quantity, unit and provenance. `スタイル` keeps only the defaults a new series starts from
- decided_by: the product owner, 2026-08-23
- rationale: the measured reference spends 100 of a chart's 115 properties, in 20 of its 23 panel
  groups, on four axes carrying an identical 25-property pattern (E-124) - and this product's Graph rail
  had **no axis settings at all**, so a chart's title, range and log scale could not be set while two
  tabs existed for its dimension and its fonts. Choosing the axis rather than repeating the fields keeps
  the same reach in a twentieth of the panel. The same measurement keys line, marker and colour to the
  series, which is why they move onto the series row: with them in `スタイル` a reader changed one
  series' look in one tab and its quantity in another, and with several series the global controls could
  not distinguish them at all. An axis range is not a cosmetic setting in this product - a fixed range
  that cuts off data produces a chart that reads as if the data ended there (XC-001)
- alternatives: making the rail contextual on the selected chart element, as Office does (E-125), is the
  better model for a mouse-driven chart and needs a chart canvas that supports selecting an axis, a
  legend and a series; the selection can drive which of these five sections is shown once it exists,
  without changing them
- basis: E-124 (T1), E-125 (T1), E-127 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a chart form with more than three axes, which would make the axis picker a list

### XC-214 - The Report rail is five sections, and writing is a reviewed draft rather than a setting
- decided: 2026-08-23
- status: active
- decision: the Report property rail is **`レポート` / `内容` / `執筆` / `スタイル` / `出力`**, five
  sections where there were six.
  `レイアウト` and `テキスト` fold into `スタイル`, which becomes the **document theme**: page, margins,
  columns, shared elements, palette, figure treatment, type and font embedding.
  **`執筆` is new and holds what was a `コメント` group inside `内容`.** It is shaped as a sequence, not a
  set of settings: choose the method (mechanical summary, or generated), state the direction, depth,
  model and search permission, then **`下書きを作る`**, which produces a draft that is **reviewed before
  it enters the report** - each statement with its kind and its source, and the statements the standard
  excluded, shown together. The state - not made, awaiting review, taken in - is named in the rail.
  Nothing is generated without the user asking, and an unset model blocks the action rather than
  annotating it
- decided_by: the product owner, 2026-08-23
- rationale: the measured tool produces an outline **before** any content, lets the user refine it, and
  generates on the user's word; its own vendor states the output "should be human-reviewed and edited
  accordingly" (E-126). This product cannot discharge that with a caption, because a generated sentence
  here may cite a number: the review already exists on the canvas (XC-104) and the rail had no way to
  reach it and no state to say where a draft stood, so a reviewed flow was rendered as four settings in
  a group called `コメント` inside a tab about contents. Page, palette and type are one theme in the
  measured reference, which keeps a document-wide theme and reaches per-block styling from the block
  (E-127) - so three tabs for one look was three places to change one thing
- alternatives: a selection-scoped `ブロック` tab matches how the reference reaches per-block styling and
  needs the report canvas to support selecting a block; per-block placement stays in the `内容` list
  until it does
- basis: E-126 (T1), E-127 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a report whose blocks need placement per block, which makes the selection scope
  worth its tab

### XC-215 - A choice about appearance is shown as an appearance, with its name kept beside it
- decided: 2026-08-23
- status: active
- decision: wherever the thing being chosen is **how something will look**, the options are **drawn** and
  laid out as a grid of samples with the name beneath each: chart form, palette, background, line style,
  marker, page orientation, margin, columns, figure treatment, mesh representation, develop preset, and
  the typeface, which is rendered in itself. **The name is never removed** - a picture cannot be
  searched, read aloud, or quoted in a specification, so every sample carries its label and its
  accessible name. One control implements this (`VisualOptions`) and one module draws the samples; a
  second implementation of either is the duplication `check_commands.py` exists to catch. Choices that
  are **not** about appearance - a file format, a unit, a case, a quantity - stay as text, because a
  picture of `PNG` teaches nothing.
  In the mockup the samples are **drawn**, not photographed: inline SVG and CSS gradients, carrying no
  asset, following the theme tokens, and staying crisp at any size. They illustrate a design state and
  are never evidence that the renderer produces that picture (the standing rule for `mockups/ui/`)
- decided_by: the product owner, 2026-08-23
- rationale: both measured references refuse the word list for exactly these choices. ParaView ships
  `pqPresetToPixmap` whose only job is to render a colour map into an image for the chooser, and reflows
  those images into a grid; Blender ships 42 studio-light previews and 147 icon preview files and draws
  them into the pickers (E-128). A word like `フラット` or `Filmic` names a result the reader has to
  imagine, and the cost of imagining wrongly here is a figure that goes into a report
- alternatives: showing the sample only on hover keeps the panel small and hides the comparison, which is
  the whole reason to draw them - the choice is made by looking at them side by side. Replacing the name
  with the picture saves a line and makes the setting unquotable
- basis: E-128 (T1), E-120 (T1), E-121 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a set of appearance options too numerous to draw at a readable size, which would
  make a searchable list with previews the better control

### XC-216 - The shelf chooses a reusable resource; the rail adjusts the item and names what is applied
- decided: 2026-08-23
- status: active
- decision: the centre-bottom @Material library and the right property rail divide as follows, and the
  interface says so at every seam.
  **The shelf is the reusable resources**: things that exist independently of the open item and can be
  applied to many of them - templates, styles, layouts, fonts, materials, backgrounds, objects. It is
  where one is found and applied, and it keeps the browsing apparatus: Sample/Original, search, tag,
  sort, preview.
  **The rail is the open item's current state**: the values in effect now, and a field named **`適用中`**
  saying which library resource they came from. The same field carries the same name in every area; it
  was `アセット` in Graph and `スタイル` in Report.
  **Where several library categories write into one rail tab, each writes a different group and the tab
  says which.** In Report's theme, `レイアウト` supplies the page and shared elements, `スタイル` the
  palette and figure treatment, `テキスト` the type - so applying two resources is composition, not a
  conflict, and the tab states that rather than leaving a reader to guess which one won
- decided_by: the product owner, 2026-08-23
- rationale: the division itself is XC-149's and is sound - the measured reference separates the two the
  same way, with a side panel of things to add and the properties of what is selected reached elsewhere
  (E-127). What was missing was that the seam is only legible where it is stated: one concept had two
  names across two areas, Report's theme said nothing about where a reusable theme comes from while
  Graph's and View's did, and after XC-214 merged three tabs into one theme, three library categories
  wrote into that one tab with nothing saying they do not overwrite each other
- alternatives: merging Report's `レイアウト` and `スタイル` into one `テーマ` resource removes the
  question by removing the ability to change the page without changing the palette; the measured
  reference keeps layout out of its theme for that reason (E-127)
- basis: E-127 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: two library categories that genuinely write the same property, which would need a
  stated precedence rather than a statement that they do not overlap

### XC-217 - A filter sits inside the section it filters
- decided: 2026-08-23
- status: active
- decision: the left sidebar's case search is **inside the `ケース` section**, directly above the tag
  filter, not above the section heading. The general rule: a control that narrows a list is placed
  within the boundary of that list, so its reach is visible without reading its placeholder
- decided_by: the product owner, 2026-08-23
- rationale: the field sat above every section in the sidebar - `ケース`, `変数` and `参考資料` - while
  filtering only the first. Position is a claim about scope, and this one was wider than the truth; the
  placeholder said `ケースを検索` but a placeholder disappears as soon as anything is typed. It also sat
  apart from the tag filter, which narrows the same list and was already inside the section
- basis: E-120 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a search that genuinely spans the sidebar's sections, which would belong above them
  and would have to say so in its own label rather than its placeholder

### XC-218 - Automatic merge until the first working prototype, and what that period accepts
- decided: 2026-08-23
- status: active
- decision: until the first working prototype exists, a change reaches `main` **without a person reading
  it**. `.github/workflows/auto-merge.yml` squash-merges a pull request when, and only when, every one
  of these holds: the repository variable `AUTO_MERGE_ENABLED` is `true`; the run that woke it concluded
  success and was for a pull request; the head is not on a fork; exactly one open pull request has that
  commit as its head; that pull request is open, not a draft, based on `main`, and still at that commit;
  it does not carry `no-auto-merge`; its merge state is not dirty, blocked or undecided; **every check
  run on the commit** - not only the workflow that triggered this one - has completed with success,
  skipped or neutral. **The path condition was removed on 2026-08-24 (XC-238)**; the sentence that stood
  here required the change to touch nothing under `.github/`, `validate/` or `.claude/`.
  **Every branch leaves without merging.** An answer the job cannot read, a check still running, a count
  it did not expect: each ends the run having merged nothing. An error in the job merges nothing at all.
  **A pull request in conflict receives no checks at all**, so it never reaches those conditions: GitHub
  does not run `pull_request` workflows while the merge commit cannot be computed. Measured 2026-08-23
  on pull request #20, which sat with no check run of any kind while a manual dispatch on the same ref
  ran normally; the cause was `mergeStateStatus: DIRTY`, and merging `main` into the branch produced the
  event. This is correct - a conflicted change must not merge - and it reads exactly like the mechanism
  being broken, so it is written down here rather than rediscovered.
  **What this accepts, stated rather than discovered later.** Every path merges unread since XC-238 -
  including `specs/`, `AGENTS.md`, `evidence/` and the merging machinery itself. And nothing enforces
  that work arrives by pull request: a direct push to `main` skips every condition above, because there
  is no branch protection to prevent it (E-129, OPEN-020). Both are open on purpose for the length of the
  prototype.
  **The agent does not merge.** `.claude/settings.json` denies `gh pr merge` - `ask` was not that rule,
  because an unattended run has nobody to answer a prompt. An agent opens the pull request; the workflow
  lands it.
  **The switch is a repository variable, not a file.** `gh variable set AUTO_MERGE_ENABLED --body false`
  is one command with no diff and no pull request. A temporary measure that needs a pull request to end
  becomes a permanent one. `no-auto-merge` stops a single pull request without touching the switch -
  **and a label that does not exist cannot be applied**, which is why `ci` fails when one the automation
  names is absent. The repository had only GitHub's nine default labels when this was written.
  **How the period ends**: the variable goes to `false`, `.github/workflows/auto-merge.yml` is deleted,
  and this decision becomes `superseded`. `check_automerge_policy.py` fails if the workflow is present
  while the decision is superseded, or absent while it is active, so the period cannot end in the record
  alone. After it, the arrangement is the reference design's A1: the agent opens a ready pull request
  with its evidence attached, and a person merges
- decided_by: the product owner, 2026-08-23
- rationale: the reference design separates "the freedom to create a pull request" from "the authority to
  change `main`" and never grants the second, on evidence of goal drift over long horizons and the
  vendor's own "powerful and occasionally wrong" (E-129). The argument holds for a product whose claim is
  trustworthy numbers, and the product owner has asked for the authority anyway, bounded to the period
  before a prototype exists - when the cost of a bad merge is a revert rather than a wrong number in
  someone's report. The honest way to grant it is to make the automatic decision **narrower and more
  explicit** than a human one, to write down what it lets through rather than only what it stops, and to
  make switching it off cheaper than leaving it on by accident
- correction: the catalogue sweep ran by hand before every push while CI only typechecked. Defensible
  while a person decided each merge; not defensible when a workflow decides on CI's word. `ci` now
  renders all 88 states through a browser (`check_mockup_states.py`) - an HTTP fetch returns the same
  6 KB shell for every state and would have passed while all of them threw
- alternatives: staying at A1 is safer and is what this becomes at the boundary. A path **allowlist**
  rather than a deny-list would stop the unread merge of `specs/` too, and would refuse most ordinary
  work, which is the throughput this measure exists to buy. Making the repository public would restore
  branch protection and the merge queue and is refused by XC-186; upgrading the plan would put the gate
  where a pull request cannot edit it, and remains the better arrangement if this period lasts
- basis: E-129 (T1)
- affects: AGENTS.md, 08_decisions.md
- decidedness: Fixed
- reversal_trigger: the first working prototype. Also any merge that reaches `main` in a state a person
  would have stopped, which ends the period early

### XC-219 - The Claude review becomes a merge condition, on the day it can authenticate and not before
- decided: 2026-08-23
- status: active
- decision: the automated review runs on every pull request and its result is a **merge condition**:
  `auto-merge` waits on every check run on the commit (XC-218), so a review that is not green stops the
  merge. This takes effect when `CLAUDE_CODE_OAUTH_TOKEN` exists as a repository secret and the
  `pull_request` trigger in `.github/workflows/claude-code-review.yml` is restored - **both, and until
  then neither**. XC-188 stays in force meanwhile.
  **The day the secret appears is not left to memory.** `ci` carries a `review wiring matches the
  secret` job that fails when the secret is present and the trigger is not, and equally when the trigger
  is present and the secret is not. The secret is only visible from inside a workflow, so the check
  lives in CI rather than in `validate/`. It is deliberately loud: once the secret is set every run is
  red until the two commented lines are restored, and while auto-merge is on that red also stops
  everything merging - which is the point, because the alternative is a review that silently is not one
- decided_by: the product owner, 2026-08-23
- rationale: an automated review that nobody has to act on is a comment, and this repository is merging
  without a human reader for the length of the prototype (XC-218). Making the review a condition is the
  one thing that puts a reader back in the path, even an imperfect one. Deferring it until the token
  exists is XC-188's argument unchanged: a check that cannot authenticate fails on every pull request
  for a reason unrelated to the change, and that teaches everyone to read red as normal
- what_this_accepts: **a non-deterministic judge becomes a merge condition.** The same change may be
  passed on Monday and stopped on Tuesday, and a review that fails for a rate limit or a model-side
  outage stops a pull request for a reason that is not about the code. The answer to that is a re-run,
  not the `no-auto-merge` label, and not weakening the condition. The alternative - a review whose
  verdict changes nothing - was rejected because it is indistinguishable from no review at all
- alternatives: keeping the review advisory and merging on CI alone is what happens today and is what
  the prototype period already accepts; making the review advisory *permanently* would mean the only
  reader of an auto-merged change is a set of static gates
- basis: E-001 (T1), E-129 (T1)
- affects: .github/workflows/claude-code-review.yml, .github/workflows/ci.yml, 08_decisions.md
- decidedness: Fixed
- reversal_trigger: a review that stops correct work more often than it stops incorrect work, measured
  rather than felt

### XC-220 - The two pins this specification declares are not proposed by a bot
- decided: 2026-08-23
- status: active
- decision: Dependabot does not open version-update pull requests for `vtk` or `numpy`. Both are
  declared in `specs/06_external.md`, so a pull request that moves only `pyproject.toml` fails
  `check_dependency_pins.py` by construction and the bot cannot complete it - it does not edit
  specifications, cannot re-read a wheel's declared licence set, and cannot re-run a spike. Moving
  either pin is deliberate work with a re-measurement attached. **Security advisories are unaffected**:
  Dependabot alerts and automated security fixes are enabled at the repository level and do not run
  through `dependabot.yml`. Every other dependency - development, mockup, GitHub Actions - is still
  proposed, because no specification declares a version for any of them
- decided_by: the product owner, 2026-08-23
- rationale: the two pull requests this closes had been open and red for a day, each failing on the one
  line the bot is structurally unable to add. A pull request that can never go green is the state
  XC-188 refused: red for a reason unrelated to the change, teaching everyone to read red as normal.
  Leaving them open also costs nothing to nobody and quietly raises the cost of every future red
- correction: `dependabot.yml` already described this failure as "the intended behaviour" and called the
  pull request "a prompt to do the rest". It is a prompt that arrives monthly, cannot be completed by
  its author, and sits red in the meantime - which is a different thing from a prompt
- alternatives: completing each bump by hand as it arrives keeps the notification and pays the
  re-measurement on the bot's schedule rather than on the project's; VTK's is five measured values and a
  licence table (OPEN-019), which is not monthly work
- basis: E-001 (T1)
- affects: .github/dependabot.yml
- decidedness: Fixed
- reversal_trigger: a specification that stops declaring a version for one of these, at which point the
  bot can complete the change on its own

### XC-221 - The graph rail's sections are named for what they hold, and a default is not a second control
- decided: 2026-08-23
- status: active
- decision: three corrections to XC-213's rail.
  **`データ` becomes `系列`.** The tab holds each series and, by XC-213, how each series looks - so a name
  that says "data" described half of it. What genuinely is data and not a series moves to the item tab:
  **the @Case selection, the iteration handling and the reduction**, because a series spans every
  selected case and none of the three belongs to one.
  **The theme's default and the series' override stop being two identical pickers.** Each appearance
  field on a series offers **the theme's value first**, drawn as the theme currently resolves it, so the
  relationship is on screen: `テーマ` for the marker with the theme's own shape as its picture, and
  `テーマに従う（2 px）` for the width. Line width is stated **in px in both places**, where the series
  said `細い`/`太い` and the theme said a number.
  **The panels are written in the order the rail shows them**
- decided_by: the product owner, 2026-08-23
- rationale: the tab division was reviewed after the product owner observed style controls inside a tab
  called `データ`, and the review found more than the name. The marker picker existed twice with the same
  four options and no way to say "follow the default", so the two tabs could disagree with nothing
  saying which won; and because the theme's own value was `auto` - not one of its four options - that
  control **rendered with nothing selected**, which is the empty display the owner also saw. XC-213's
  own basis says appearance is keyed to the series (E-124); it did not say what happens to the value the
  series does not set, and that gap is what produced the duplicate
- correction: XC-213 kept a `系列の既定` group in `スタイル` while giving the series the same fields, and
  called the result "the defaults a new series starts from". They were not defaults: nothing referred to
  them, and a series set at creation cannot follow a default that changes afterwards
- alternatives: moving appearance out of the series and back into `スタイル` answers the owner's first
  observation directly and re-creates what XC-213 removed - one series' look and its quantity edited in
  two tabs, and several series indistinguishable. Splitting into `データ` and `系列` keeps six tabs to
  avoid renaming one
- basis: E-124 (T1), E-127 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a theme that cannot express a default some series needs, which would make the
  per-series field the only one and the theme group pointless

### XC-222 - One name means one thing across the graph rail, and a control that does nothing is removed
- decided: 2026-08-23
- status: active
- decision: within one area's property rail, **a control name means one thing**. In the graph rail five
  names meant two: `軸` was both the axis a series is drawn against and the size of an axis label,
  `種類` was both the chart's kind and the output's, and `マーカー` and `線幅` each named a value and its
  default in adjacent tabs. They are now `使用する軸` and `軸ラベル`, `成果物の種類`, `既定のマーカー` and
  `既定の線幅`. **One exemption, stated rather than silent**: `タイトル` is the graph's title in the item
  tab and its type size under `書体`, where the group name and the `pt` value carry the difference and
  the unambiguous alternatives wrap in a 68-pixel label column.
  **A control that has no effect in its current state is not drawn.** A series' colour well sat beside
  the mode selector and did nothing while the mode was `パレット順`, with the palette it would have drawn
  from reported again on a row of its own - three elements for one decision, one of them inert. The row
  now shows the mode, and beneath it either the palette position this series takes or the colour well,
  never both and never neither
- decided_by: the product owner, 2026-08-23
- rationale: the owner reported the same thing twice - style controls in a tab called データ, and
  apparent duplication and empty displays - which is what prompted counting every control in the five
  tabs rather than answering from the last change. XC-221 fixed the pair that was genuinely one value in
  two places; this fixes the pairs that were **different values wearing one name**, which read as
  duplicates to anyone scanning, and the one control that was actually inert. A name that needs its
  group to be understood is a name that fails when the reader is scanning, which is how a rail is read
- correction: XC-221 introduced `既定` as a concept and left the rows named exactly as the series' own,
  so the change that removed the duplicate left it looking like one
- alternatives: renaming the graph's title text instead of the type size moves the ambiguity rather than
  removing it, and the title is what that field holds
- basis: E-124 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a third meaning for one of these names, which would mean the rail has outgrown a
  flat set of labels

### XC-223 - The picture is the content, so nothing is spent on air around it
- decided: 2026-08-23
- status: active
- decision: two rules, both about making the visible thing visible.
  **Anything the product can show, it shows.** XC-215 covered choices about appearance; this extends it
  to every subject that has a picture, whether or not the setting is about styling. A **colour map** is
  chosen from its gradient, wherever one is chosen - the scalar object's map and the material editor's
  preset alike. A **view direction** is a cube seen from that direction. A **glyph** is its shape. A
  **typeface** is rendered in itself, in Graph as it already was in Report. An **applied style asset**
  shows the palette and background it applies. Non-visual settings stay as text (XC-215).
  **No chrome between the sample and the tile edge.** A sample fills its tile: the tile carries no
  padding, only the label beneath it does, and the tile clips the sample to its own radius. At four
  columns in a 286-pixel rail the old five pixels of padding on each side, plus the border, spent about
  a fifth of every sample's width on air
- decided_by: the product owner, 2026-08-23
- rationale: the owner asked for both together, and they are one point: a picture that is drawn small
  teaches less than a picture, and the padding was not protecting anything - the tile already has a
  border and a gap between tiles. The colour map is the case the measurement is most pointed about:
  ParaView ships `pqPresetToPixmap` whose only purpose is rendering a map into an image for the chooser
  (E-128), and in this product a wrong colour map is a wrong picture rather than an ugly one
- alternatives: keeping a little padding reads as tidier at rest and costs the sample the width it is
  there to use; the border and the four-pixel gap already separate one tile from the next
- basis: E-128 (T1), E-120 (T1), E-121 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a sample whose own edges are meaningful and read as clipped against the tile, which
  would need padding on that kind alone rather than on all of them

### XC-224 - A series' appearance has two levels, not three: the applied asset, and the series
- decided: 2026-08-23
- status: active
- decision: the chart-wide `系列の既定` group is **removed as a control**. What a series follows unless it
  overrides comes from the **applied style @Asset**, named in `適用中`, and the style tab **reports** what
  that asset supplies rather than offering a second place to set it. Changing the asset changes what
  every series following the theme is drawn with. Each appearance property therefore has exactly one
  editable control: line, marker, width and colour on the series; palette and background chart-wide,
  where there is no per-series counterpart at all
- decided_by: the product owner, 2026-08-23
- rationale: **the measurement says there is no such level.** ParaView's chart view carries 115
  properties and every one of them is an axis, the legend, the annotation or the tooltip; appearance is
  keyed to the series on the representation, one value per series addressed by name (E-124). The
  chart-wide default between the asset and the series was invented here. It is also the level the style
  asset already occupies - XC-216 says the shelf holds the reusable resource and the rail names which
  one is applied - so it was a third place defining what two places already defined
- correction: XC-221 introduced the level to explain the duplicate, and XC-222 renamed its rows to
  `既定の…` so they would stop reading as one. Both treated the symptom. The product owner asked a third
  time, and the third answer is the one the measurement supported from the start: remove the level.
  What XC-221 got right and this keeps is the series' first option being the theme's, drawn as the theme
  resolves it
- what_is_lost: setting a default for every series without editing the asset. With the reference having
  no such control, and a reusable default belonging to the asset by XC-216, that is where it goes if it
  is ever wanted
- alternatives: keeping the group and marking it read-only leaves a group whose only content is a
  read-out; the read-out is one row inside `スタイル` instead
- basis: E-124 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: a chart with enough series that setting each one is the bulk of the work, which
  would argue for an apply-to-all action on the series list rather than for a third level

### XC-225 - Within one property rail, two controls never change the same thing
- decided: 2026-08-23
- status: active
- decision: the rule XC-222 and XC-224 established for the graph applies to **every** property rail, and
  is checked for every rail rather than argued case by case. Within one editor, a control name means one
  thing and one property has one editable control. Across editors the same word is fine and expected -
  every item has a `名前`, every area has a `種類` of its own - so the check is per rail.
  The View rail carried five: `開始`/`終了` were a @Comparison's member range and a @Timeline's playback
  range, `配置` was a comparison's arrangement and an image's placement, `種類` was the background's kind
  and the output's, and `名前` was the open item, a camera, a playback preset and a camera being created.
  They are `範囲の先頭`/`範囲の末尾` against `再生の先頭`/`再生の末尾`, `並べ方` against `画像の配置`,
  `背景の種類` against `成果物の種類`, and `カメラ名`/`プリセット名`/`新しい名前` beside the item's own
  `名前`. **One exemption, stated**: the graph's `タイトル`, its text and the size of its type (XC-222)
- decided_by: the product owner, 2026-08-23
- rationale: the owner asked three times about one such pair in the graph before it was removed rather
  than renamed, and then asked for the mockup as a whole. Counting them showed the graph was not
  unusual: the View rail had five, none of them noticed because each reads correctly inside its own
  group. A group heading disambiguates for a reader who is already there and not for one scanning a
  rail, which is how a rail is used
- correction: XC-222 wrote this rule for the graph rail and left every other rail unchecked, which is
  the same shape of mistake as fixing one visible site of a defect
- alternatives: relying on the group heading keeps the shorter labels and puts the burden on the reader
  each time
- basis: E-124 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a rail where the distinguishing prefixes make every label too long for its column,
  which would mean the rail has too many properties rather than that the rule is wrong

### XC-226 - The graph rail divides what a series is from how it looks
- decided: 2026-08-23
- status: active
- decision: **`系列` holds what each series plots** - its X source, Y quantity, @Declared unit,
  @Provenance, missing-value policy and the axis it is read against - and **`スタイル` holds how it
  looks**, per series: colour, line style, width and marker, beneath the chart-wide palette, background
  and type. **Both address the same selection**: a chip row in `スタイル` and the list in `系列` set the
  same series, so no list is repeated and switching tabs keeps the series you were working on.
  Appearance stays **per series**. That is not what changes here
- decided_by: the product owner, 2026-08-23
- rationale: the two are different kinds of work - deciding what a figure shows, and making it readable -
  and the owner reads the rail that way. The measurement constrains the **model**, not the panel: E-124
  says appearance is keyed to the series and addressed by series name, which this keeps, and it also
  records that the reference groups the series' parameters separately from the array selection. A panel
  that follows the selected element is the measured behaviour of the other reference (E-125)
- correction: XC-213 moved appearance onto the series row and argued against exactly this split, on the
  grounds that it means editing one series' look and its quantity in two tabs. What XC-213 was actually
  fixing was appearance that could only be set **chart-wide**, which left several series
  indistinguishable; it over-corrected from "not global" to "on the same row". Sharing the selection
  answers the two-tab objection, which is what the reference does anyway
- alternatives: a table in `スタイル` with one row per series and a column per property matches the
  reference's own grouping most closely and does not fit four properties across a 286-pixel rail;
  keeping everything on the series row is what three rounds of review kept objecting to
- basis: E-124 (T1), E-125 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: users reporting that they cannot find where a series' colour is set, which would
  mean the shared selection is not visible enough to carry the split

### XC-227 - An object's tab separates what it is from how it is drawn, by group
- decided: 2026-08-24
- status: active
- decision: the division XC-226 made across two tabs in the Graph rail is made **by group** in the
  @View object tab, because there is only one tab there - the selected object's. For every object type,
  the first group holds **what the object is** (its role, its source, the field it reads, the frame that
  field is in) and a later group holds **how it is drawn** (representation, opacity, glyph, point size,
  colour, edges). A scalar field already read this way, with `色と範囲` separate from the field
  selection; mesh, vector field, trajectory and point cloud did not
- decided_by: the product owner, 2026-08-24
- rationale: the owner's argument for the Graph rail - that deciding what a figure shows and making it
  readable are two kinds of work - is about the work, not about tabs, so it applies wherever both kinds
  sit together. The object tab cannot use the same answer as the Graph rail because there is nothing to
  split into: a second tab for an object's appearance would be a tab whose contents change with the
  selection twice over. Groups are the unit available, and a collapsed group is a section a reader can
  skip, which is most of what the split buys
- alternatives: moving appearance to the `マテリアル` tab confuses a display setting with a surface
  @Asset - a representation is not a material - and leaves the object tab holding only two fields
- basis: E-124 (T1), E-125 (T1)
- affects: 11_ui.md, 16_application_model.md
- decidedness: Fixed
- reversal_trigger: an object type whose appearance is one field, where a group of its own is heavier
  than the field

### XC-228 - The axis prints the unit its series declare, and says so when they disagree
- decided: 2026-08-24
- status: active
- decision: three seams between `系列` and `軸`, which hold no duplicated function and did not say how
  they relate.
  **The axis's unit is the series' unit.** `単位の併記` writes what the series **on that axis** declared,
  and nothing else - an undeclared unit is not written, and no unit is inferred (XC-003). **Two series
  on one axis declaring different units is not resolved by choosing one**: the axis states that the
  units are mixed, and the units go to the legend beside each series. A scale labelled `MPa` under a
  series measured in `mm` is a figure that reads wrongly and looks right.
  **Choosing an axis means two things, so each says which.** The `軸` tab's picker chooses the axis you
  are **editing** and now carries that as a visible caption; `使用する軸` on a series chooses the axis it
  is **drawn against**. Both tabs name the axes identically - `Y（左）`, `第2Y（右）` - where the series
  said `左（Y）` and the axis tab said `Y（左）`.
  **`範囲` named two things in one rail**: the reduction's range and the axis's. The reduction's is
  `集約範囲`
- decided_by: the product owner, 2026-08-24
- rationale: asked whether `系列` and `軸` overlap. They do not overlap in function - one says what is
  drawn, the other how the scale reads - but the unit crosses between them and nothing said in which
  direction, which is the kind of gap that produces a confidently wrong figure rather than a confusing
  one. The mixed-unit case has no correct silent answer: printing either unit mislabels the other
  series, and printing neither without saying so leaves a reader to assume
- basis: E-124 (T1), E-001 (T1)
- affects: 11_ui.md
- decidedness: Fixed
- reversal_trigger: a chart form where two units on one axis is meaningful and conventional, which would
  need the axis to carry both rather than to report the conflict

### XC-229 - A language model writes the code and the sentence; the data never reaches it
- decided: 2026-08-24
- status: active
- decision: **no @Dataset value is sent to a language model, ever.** What a model may receive is
  structure and the user's words: field names, whether each is held at points or cells, the @Declared unit of a quantity,
  counts, the @Case and @Part names, the command surface, and the instruction itself. What it may not
  receive is the numbers those names refer to.
  A model therefore produces one of two things. **Code or a command sequence**, executed by the product
  through the same command surface the interface uses (assistant/REQ-001), against the dataset. Or a
  **statement template with slots** - `最大応力は［値］［単位］でした` - which the product fills from the
  dataset in the canonical frame, at the @Significant digits the value honestly carries, and then checks
  against the written standard (XC-104).
  A number that appears in a deliverable has therefore never been through a model. It was read from the
  file, computed by this product, and formatted by this product
- decided_by: the product owner, 2026-08-24
- rationale: this product's claim is trustworthy numbers, and a value that has passed through a model is
  a value that may have been altered with nothing downstream able to tell - not because the model is
  dishonest, but because a token sequence carries no provenance and no arithmetic. The rule also removes
  a whole class of failure that would otherwise need detecting: a transposed digit, a plausible unit
  conversion, a rounded figure quoted back as exact. It costs the model the ability to comment on what
  the numbers *are*, which is why the template carries slots and the product carries the values
- what_this_forbids: pasting a table of results into a prompt; asking a model to summarise a field;
  letting a model compute a comparison, a ratio or a maximum; quoting a model's arithmetic anywhere
- alternatives: sending values and validating the output against the dataset afterwards is what a
  checking layer would do, and it can only catch a wrong value it can attribute to a field - a sentence
  that invents a plausible number for a quantity nobody reported passes
- basis: E-001 (T1)
- affects: features/assistant/spec.md, 14_reporting_standards.md
- decidedness: Fixed
- reversal_trigger: none foreseen; the rule is the product's claim expressed as an architecture

### XC-230 - A reported value is computed in as few operations as the specification allows
- decided: 2026-08-24
- status: active
- decision: the path from a stored value to a reported one is **as short as the meaning permits**, and
  what it consists of is stated.
  **No operation consumes a value that was rounded for display.** A displayed figure is an output, never
  an input: a percentage, a ratio, a difference or a maximum is computed from the stored values, not
  from what the screen shows.
  **A conversion happens once, at a stated point.** The canonical frame and unit are applied on load
  (INV-001, ingest/AC-028) and not re-applied afterwards; nothing converts a second time "to be sure".
  **A derived quantity is computed from source fields**, and where it is computed from another derived
  quantity, that chain is what the definition says it is and each step keeps full precision until the
  last.
  **Computed once, then reused.** A reduction, an aggregate or a decimation is computed once and cached
  against its inputs, so the same figure asked for twice is the same figure rather than two roundings of
  it (ingest/TASK-017)
- decided_by: the product owner, 2026-08-24
- rationale: every floating-point operation is a chance to lose a digit, and the losses compound in the
  order the operations happened to be written. A product whose claim is trustworthy numbers cannot leave
  that to chance: the shortest path from the file to the figure has the fewest chances to be wrong, and
  where a path must be long, saying what it is makes the error attributable instead of mysterious. The
  worst case this rules out is the quiet one - a figure recomputed from a rounded figure, which is
  wrong by an amount nobody can reconstruct later
- alternatives: computing in higher precision throughout and rounding only at the end reduces the error
  without reducing the operations, and does not help when the input was already rounded; it is a
  complement to this rule rather than a substitute
- basis: E-001 (T1)
- affects: 02_invariants.md, 15_derived_quantities.md, features/ingest/tasks.md
- decidedness: Fixed
- reversal_trigger: a quantity whose definition genuinely requires a longer chain, which is recorded as
  part of that quantity rather than as an exception to this

### XC-231 - Which entries a reported number is computed over is read from the ghost array
- decided: 2026-08-24
- status: active
- decision: the entries a count, sum or mean is computed over are the ones **not** marked in the
  `vtkGhostType` array, and the bits that exclude an entry are exactly the ones VTK's own integrator
  excludes: `DUPLICATECELL | HIDDENCELL` for a cell and `DUPLICATEPOINT | HIDDENPOINT` for a point
  (E-131). No other bit disqualifies an entry.
  **The mask cannot be built without the association.** The point array and the cell array carry the
  same name and the same byte width, and bit 2 means `HIDDENPOINT` for a point and
  `HIGHCONNECTIVITYCELL` for a cell. `counted()` therefore takes the association and has no default for
  it, and a @Dataset holds the two ghost arrays in a mapping keyed by association rather than among the
  fields - which is also the only way to hold both, since a dictionary keyed by name could hold one
- decided_by: the product owner, 2026-08-24
- rationale: the exclusion set is not a judgement to make here. It is what the toolkit that produced the
  file already means by those bits, and choosing differently would make this product's integral disagree
  with ParaView's over the same file for no stated reason. Reading it from `vtkIntegrateAttributes`
  rather than from documentation is what makes it checkable.
  The association requirement exists because of a specific silent failure: a mask built with the point
  vocabulary over a cell array drops every high-connectivity cell from the integral. The result is a
  number a few per cent low, with nothing about it that looks wrong
- alternatives: excluding `REFINEDCELL` as well is defensible for an AMR hierarchy, where counting a
  coarse cell and its refinements double-counts the volume. It is not done here because the integrator
  does not do it, and diverging from the reference on a case this product cannot yet produce would be a
  difference nobody could test. Recorded as the reversal trigger
- basis: E-131 (T1)
- affects: 02_invariants.md, 01_boundaries.md, features/ingest/tasks.md
- decidedness: Fixed
- reversal_trigger: this product reads an AMR hierarchy, at which point whether `REFINEDCELL` is
  excluded has to be settled against a measured integral rather than assumed

### XC-232 - An unmarked partitioned set refuses the affected numbers rather than merging by coordinate
- decided: 2026-08-24
- status: active
- decision: when a @Dataset is in more than one part and no ghost array marks the duplicates, the sums,
  means and counts over the affected association are **not reported**; each comes back as a missing
  value carrying the reason. Nothing merges points by coordinate to recover them.
  Which numbers are affected is not all of them, and the difference is stated rather than assumed:
  - an **extremum is reported**, because the largest of a set is the largest of that set with part of it
    written twice;
  - **cell quantities are reported when the manifest declares `GhostLevel="0"`**, because at zero ghost
    layers a cell belongs to exactly one piece - an interface repeats points, not cells (E-131);
  - **point counts, sums and means are refused** whenever there is more than one part, at any ghost
    level, because an interface always repeats its points
- decided_by: the product owner, 2026-08-24
- rationale: `GhostLevel="0"` is the writer's default (E-131), so the file with no ghost array is the
  common case rather than an edge one, and this decision governs most partitioned runs this product will
  meet. Merging by coordinate is the obvious alternative and it is the dangerous one: it needs a
  tolerance, and a tolerance welds together the coincident points that a crack face, a contact pair or a
  shell-solid interface exists to keep apart. That trades a visible over-count for an invisible change of
  geometry, which is the worse of the two by this product's own standard.
  Refusing costs less than it appears to, because the number an engineer reports from a stress result is
  the maximum, and the maximum survives duplication untouched
- alternatives: reporting the sum with a caveat was considered and rejected - the error is a fraction of
  a per cent, which is exactly the size that a caveat does not stop anyone acting on. Refusing the
  number is the only form of the warning that cannot be read past
- basis: E-131 (T1), E-039 (T1)
- affects: 02_invariants.md, features/ingest/tasks.md
- decidedness: Fixed
- reversal_trigger: a way to identify the duplicates that does not need a tolerance - a global point ID
  array, which some writers emit - at which point those numbers are computable and are computed

### OPEN-023 - How a background and its environment cross the renderer paths
- question: XC-119 settles what any background must obey and leaves the set of kinds to implementation
  (OPEN-016). Neither says how one crosses a renderer boundary. An HDRI environment has a defined
  meaning in vtk.js, in native VTK and in USD (`UsdLuxDomeLight`), and the three do not agree on how
  rotation, display strength and camera visibility are expressed. Which representation is canonical,
  how the others map onto it, and what happens on a path that cannot carry it, is undecided
- why_open: the gap is between two things that are each settled. AC-089 specifies the **interface** for
  the background and its environment - one Asset, one rotation, a display strength independent of the
  lighting strength, and camera visibility - and CT-011 specifies the **transport** of a material across
  the same boundary in full. Nothing specifies the transport of a background. `UsdLux` appears nowhere
  in this specification set, checked 2026-08-24, so the USD end of it is not merely undecided but
  unwritten. Deciding it by whichever renderer is implemented first would make that renderer's
  convention canonical by accident, which is how a background ends up rotated differently in the report
  than in the view it was composed in
- blocks: nothing today - MOD-003 does not exist. It blocks the first background that is not a solid
  colour, because a solid colour is the one kind on which the three paths cannot disagree
- closes_when: a background Asset contract exists that names the canonical representation and classifies
  every path's support for it the way CT-011 classifies a material's - `exact`, `baked` or
  `unsupported` - measured against what each renderer does with an environment on the hardware class of
  E-063, not decided in advance
- affects: view/REQ-002, view/REQ-008, view/REQ-013, CT-004, CT-008, MOD-003, XC-119, OPEN-016, OPEN-024
- decidedness: Open

### OPEN-024 - What the interactive path and the offscreen path guarantee about the picture
- question: XC-087 ships three rendering paths - vtk.js on WebGL2 for the interactive view, the native
  toolkit offscreen for large datasets **and for report images**, and WebGPU marked experimental. Every
  guarantee written about them is about numbers: XC-087's reversal trigger fires when the paths disagree
  on a reported value, and view/AC-005 requires identical values across a renderer switch. What the
  product promises about the **picture** - which a user composes on one path and receives on another -
  is not stated anywhere
- why_open: this is not a request for pixel equality, which no two renderers give. It is that the
  difference is currently unnamed, and an unnamed difference is discovered by the recipient of a report.
  The mechanism to name it already exists and is already restricted to one asset kind: CT-011 gives
  native VTK and vtk.js **separate versioned capability manifests** and classifies every material
  feature `exact`, `baked` or `unsupported`. Backgrounds, lighting and the composed View have no
  equivalent, so a View is currently a thing whose material half can state its own fidelity and whose
  other half cannot
- blocks: nothing today. It blocks report/REQ work that embeds a rendered image, because the image in
  the deliverable is the one rendered on the path the user did not use
- closes_when: the capability classification is defined for a whole @View rather than for a material
  alone, and a stated difference between the composing path and the rendering path is reported before
  the image is produced rather than after
- affects: view/REQ-002, view/REQ-007, report/REQ-001, CT-011, MOD-003, INV-002, XC-087, OPEN-023
- decidedness: Open

### OPEN-025 - What an imported 3D prop carries, and whether it may be imported at all
- question: view/AC-037 requires that placing an imported 3D model state its cost against LIM-009, and
  XC-119 lists prop models as a candidate background kind. Neither says what the Asset **is**. Three
  things are unanswered: what the prop's own materials are, and how they relate to CT-011 - a glTF or
  OBJ prop arrives with materials that are not MaterialX graphs, and preserving, converting or ignoring
  them are three different products; what the prop's unit and scale are on import; and which formats may
  be read at all
- why_open: the third part is already decided in a way that constrains the other two. XC-047 disables by
  default any format whose reader carries an unfixed advisory, and four heap-overflow and use-after-free
  advisories at CVSS 7.5 affect VTK's glTF loader with no fixed version indicated (E-033). The obvious
  prop format is therefore the one this product has already decided not to open by default, and a prop
  contract written without settling that would specify an import path that XC-047 refuses.
  The scale question is separate from the one already solved: `domain_core/frame.py` resolves the frame
  of a **result** file, where XC-003 forbids inferring a unit. A prop is not a result and carries no
  reported number, so the same prohibition may not be the right answer - but the canonical frame is
  Z-up metres either way, and a prop placed at the wrong scale is a picture that misleads about size
- blocks: nothing today. It blocks view/AC-037, which cannot be implemented past a cost statement
- closes_when: a prop Asset contract exists stating its permitted formats against XC-047, the treatment
  of its own materials against CT-011, and how its unit and scale are established - declared, read, or
  refused
- affects: view/REQ-013, CT-008, CT-011, MOD-002, MOD-003, XC-047, XC-119, OPEN-016
- decidedness: Open

### XC-233 - A dataset holds the geometry it was read from and the geometry it is drawn as, separately
- decided: 2026-08-24
- status: active
- decision: a @Dataset carries **two geometries**. `points_m` and `cells` are what the file declared,
  in the toolkit's own three-array connectivity layout - offsets, connectivity and cell types - with
  nothing tessellated and nothing dropped. `display` is the triangulated surface, and it carries the
  index of the dataset point and dataset cell each of its own entries came from.
  **A field is checked against the geometry it is attached to when the @Dataset is constructed.** A
  point field whose length is not the point count, or a cell field whose length is not the cell count,
  is refused rather than stored.
  A format that stores no explicit connectivity - an image, a rectilinear or a structured grid - is
  refused by name rather than approximated by its surface
- decided_by: the product owner, 2026-08-24, on a measured defect rather than on preference
- rationale: INV-001 is a statement about **two point sets**, and a product that keeps one of them
  cannot honour it whichever one it keeps. Until this decision the reader kept the drawn one: it stored
  the extracted surface as the dataset's geometry while reading the fields from the original grid. That
  is not a near miss. Measured on a 3x3x3 block of hexahedra (E-132), the dataset came back with 26
  points, 27 field values and 48 triangles where the file had 27 points and 8 cells, and the surface
  points arrive in the order 0, 1, 10, 9, 3 - so `points_m[3]` was at (0, 0, 1) while `stress[3]` was
  the value of the point at (0, 1, 0). **Every index correspondence was wrong, and every value returned
  was a real value from somewhere else** - the shape of error this product exists to prevent. Reported
  aggregates happened to stay correct, because the fields were read from the full grid; anything
  computed from a coordinate was not.
  The connectivity layout is the toolkit's rather than one chosen here so that reading is a copy in
  each direction. A product storing triangles as `(n, 3)` has to decide what to do the first time it
  meets a hexahedron, and the decision it reaches for is to triangulate - which is the display path
  wearing the canonical path's name
- alternatives: keeping one geometry and a flag saying which it is was the shape that produced the
  defect; deriving display geometry on demand and never storing it repeats a reduction measured at 22
  seconds for a million-point surface (ingest/TASK-017); merging the surface back onto the original
  points needs a tolerance, and E-132 shows the map is available for free from the filter that already
  ran
- basis: E-132 (T1)
- affects: 02_invariants.md, MOD-001, MOD-002, features/ingest/tasks.md, INV-001, INV-009
- decidedness: Fixed
- reversal_trigger: a reader for a format whose connectivity is implicit, at which point what `cells`
  means for it is decided rather than assumed - not by extracting its surface

### XC-234 - A part and a partition are two things, and the composite says which
- decided: 2026-08-24
- status: active
- decision: a **partition** is one dataset cut up for parallel input and output - its pieces recombine,
  their interface points are duplicates of each other, and INV-010 governs them. A **part** is a distinct
  thing in the model - an element block, a side set, a material - whose points are not duplicates of
  another part's and across which nothing is summed unless it was asked for.
  Which one a composite carries is read from its type and never inferred from its shape:
  `vtkPartitionedDataSet` and `vtkMultiPieceDataSet` are partitions, `vtkMultiBlockDataSet` is parts,
  and `vtkPartitionedDataSetCollection` is parts each of which may be partitioned. A @Case therefore
  counts both, and `CaseContents.parts` counts parts alone
- decided_by: the product owner, 2026-08-24
- rationale: conflating them produces exactly two errors and this product can afford neither. Treating
  parts as partitions deduplicates points that were never duplicates and quietly drops geometry;
  treating partitions as parts counts every interface twice.
  It is the common case rather than an edge one, which is what makes it worth a decision of its own. Of
  the 40 CAE readers in the pinned build, **19 return `vtkMultiBlockDataSet` and 6 return
  `vtkPartitionedDataSetCollection`** - CGNS, Exodus, every EnSight variant, OpenFOAM, LS-DYNA, Fluent,
  Tecplot, IOSS - while only 4 return a `vtkUnstructuredGrid` directly (E-133). Every format this
  product's users work in arrives as a composite, so a read path whose signature is `vtkDataSet` meets
  none of them, and the survey written against `.pvtu` pieces had counted the one kind of multiplicity
  that is not the common one
- alternatives: flattening every composite to one mesh on load is what a viewer does, and it is why a
  viewer cannot tell you the maximum in the flange rather than in the assembly; carrying only the block
  names as tags keeps the words and loses the boundary that makes an aggregate meaningful
- basis: E-133 (T1)
- affects: CT-012, GL-002, MOD-002, INV-010, features/ingest/spec.md
- decidedness: Fixed
- reversal_trigger: a composite type whose blocks are neither clearly parts nor clearly partitions, which
  would be read from the file rather than decided by type - and would be an addition to CT-012's table,
  not an exception to it
### XC-235 - Display geometry is produced by the renderer, reduced by vtkDecimatePro, and kept
- decided: 2026-08-24
- status: active
- decision: three things, decided together because each is the reason the next one works.
  **Display geometry is MOD-003's, not the reader's.** `reader.read` returns the file in the canonical
  frame and draws nothing; `engine.visualization.display.display_geometry` takes a @Dataset and produces
  the surface. It takes a @Dataset rather than a toolkit object, so the boundary is real rather than
  maintained by the reader handing the renderer something extra.
  **The decimator is `vtkDecimatePro`, chosen on correctness.** It carries `vtkOriginalPointIds` through
  and moves no surviving point; `vtkQuadricDecimation` drops the array entirely (E-134). A reduced
  surface built with the second cannot answer a pick, because nothing says which dataset point a vertex
  was. `PreserveTopology` on and boundary-vertex deletion off, so a reduced picture does not close a
  hole and show a different part.
  **It is cached on the @Dataset, keyed by triangle budget.** Two views of one @Case may have different
  budgets and neither evicts the other. Where a decimated triangle spans more than one cell, its source
  cell is **-1** rather than one of the cells it partly covers
- decided_by: the product owner, 2026-08-24
- rationale: the decimator choice is the load-bearing one and it is not the choice a quality comparison
  would make. Quadric decimation is the better-looking algorithm and it is unusable here, because this
  product's reduced view still has to answer "what is the value at that point" and the only thing that
  can answer is the map back. Measured rather than assumed: same input, same reduction, one filter keeps
  the array and the other does not (E-134).
  The cache is on the @Dataset because it is derived entirely from the @Dataset and should die with it -
  a cache keyed by object identity in a module outlives what it describes. And it has to exist: 2.63 s
  for a million triangles here, 22.34 s for 2.25 million in the export spike, against a frame budget of
  about 23 ms (LIM-002).
  -1 for a spanning triangle rather than a nearest cell is the same rule as everywhere else here: a
  value attached to a place it is not true of is worse than no value (XC-001)
- alternatives: reducing in the reader keeps one code path and makes every load pay for a picture nobody
  asked to see; re-deriving the map by nearest-point search after decimation needs a tolerance and is
  slower than the array the filter already produced; quadric decimation with a separate locator to
  rebuild the map is two passes to recover what one filter gives free
- basis: E-134 (T1), E-063 (T1)
- affects: MOD-002, MOD-003, INV-001, LIM-002, features/ingest/tasks.md
- decidedness: Fixed
- reversal_trigger: a decimator that both preserves the map and beats `vtkDecimatePro` on the silhouette,
  which would be measured against the same sphere rather than adopted on its description

### XC-236 - An identifier is not a field, and an absent identifier is not an index
- decided: 2026-08-24
- status: active
- decision: the identifiers a source wrote are held on the @Dataset **apart from its fields**, as
  `SourceIdentifiers` per association: a global identifier as **int64**, a pedigree identifier as text,
  and the name the file gave each. Which arrays those are is read from the attribute role the file
  declared - `<PointData GlobalIds="...">` - and never from an array's name (E-135).
  An extreme value is reported **at** its identifier. Where the file wrote none, the product says that
  the file wrote none; **the array position is never offered**, in any wording, as a location.
  In an assembly the location names the part and then the place in it, because every part may number
  its own nodes from one
- decided_by: the product owner, 2026-08-24
- rationale: three separate things each rule out holding an identifier as a @Field, which is what the
  reader did until this decision. It is not a physical quantity, so offering `GlobalNodeId` in the list
  a user picks a @Variable from invites a plot of node numbers against node numbers. Its exactness is
  the whole of its value and the field store is float64, which stops being exact above 2^53 - node
  9007199254740993 becomes node 9007199254740992 with nothing said. And a pedigree identifier **may be
  a string** (E-135), which no numeric array can hold at all.
  The second half is INV-023 restated as a rule the code can obey: "the maximum is at node 12345" is
  checkable in the solver and "the maximum is at index 8412" is checkable nowhere and changes when the
  file is written again. The absence is phrased as a fact about the file rather than a failure of the
  reader, because only one of those two can be fixed - by asking the solver to write identifiers
- alternatives: keeping identifiers among the fields and filtering them at each display site is the
  arrangement that produced the defect: every new site is a new chance to forget, and the one that
  forgets is the one nobody tested. Falling back to the array index when a file has none is the
  friendlier-looking option and is the one INV-023 exists to forbid
- basis: E-135 (T1), E-075 (T1)
- affects: MOD-001, MOD-002, INV-023, GL-034, features/ingest/tasks.md
- decidedness: Fixed
- reversal_trigger: a format that carries a stable identifier this product can construct rather than
  read - at which point what constructs it is recorded with the value, and it is still not an index

### XC-237 - A reader states what it had to switch on, and proves nothing was dropped
- decided: 2026-08-24
- status: active
- decision: where a toolkit reader does not read a file's contents by default, this product **switches
  everything on and then checks that everything arrived**. The two halves are not the same promise: the
  switching is an attempt that can fall behind the toolkit, and the check is the guarantee.
  Concretely for Exodus: every one of the 26 plain array categories is enabled by name, global and
  pedigree identifier generation is turned on, and after the read every result the file offered is
  looked for by name in what came back. A result that is missing **stops the read** rather than being
  reported as an absent value - the file has it, so a @Dataset without it is not a partial reading of
  that file but a wrong one.
  The need for it is a named gap on the format (ingest/AC-033), not a detail of the implementation
- decided_by: the product owner, 2026-08-24
- rationale: `vtkExodusIIReader` reads **no results at all** unless each array is switched on by name,
  across 27 categories that all start off, and it says nothing about it (E-136). A file written with
  three results comes back as geometry with none. That is the exact failure this product exists to
  prevent, arriving from the library rather than from this code, and a reader that enabled the two
  obvious categories would have dropped the other twenty-four just as silently.
  Checking by name rather than trusting the switching is what makes the guarantee survive a toolkit
  upgrade: a category added in a later release is not in the list here, and the check notices that the
  file offered something that did not arrive
- alternatives: enabling categories by reflecting over the reader's methods removes the list to
  maintain and replaces a reviewable surface with a clever one; trusting the defaults is what produced
  the measurement; reporting the missing results as absent values (XC-001) is wrong here because the
  value is not absent - it is in the file, unread
- basis: E-136 (T1)
- affects: MOD-002, ingest/REQ-015, features/ingest/tasks.md
- decidedness: Fixed
- reversal_trigger: a toolkit release whose Exodus reader reads its results by default, which would be
  measured rather than assumed from a changelog

### XC-238 - No directory is held back from automatic merge
- decided: 2026-08-24
- status: active
- decision: the path condition of XC-218 is removed. **Every path merges unread**, including
  `.github/workflows/auto-merge.yml` itself, the checks in `validate/`, and `.claude/settings.json`.
  A pull request touching those three is still detected and is **written to the workflow log** as
  having merged unread, because nobody sees it beforehand and the log is the only place it can be found
  afterwards.
  Two brakes remain, and they are brakes only because neither can be set from inside a pull request:
  the `no-auto-merge` label on one, and `gh variable set AUTO_MERGE_ENABLED --body false` on all
- decided_by: the product owner, 2026-08-24, asked for it, was told what it removes, and confirmed
- rationale: the owner's reason is throughput - three of the last five pull requests needed a manual
  merge for touching a gate or a workflow, and the manual step was the slowest part of the loop.
  The reason it was not this way before is unchanged and is the thing to keep in view: **this gate will
  now merge its own weakening, and can merge its own removal.** A pull request that deletes a check in
  `validate/`, or removes the `gh pr merge` deny that stops an agent merging directly, lands the same
  way as a typo fix. The three directories were the structural part of the arrangement; what is left in
  their place is judgement, which is not nothing but is not a mechanism either.
  Written here at length rather than settled quietly, because XC-218's own standard is to state what
  the period accepts rather than only what it stops, and this is the largest thing it now accepts
- alternatives: keeping a single-file guard on `.claude/settings.json` - the deny that stops an agent
  merging directly - would have kept the smallest structural piece at almost no cost to throughput. It
  was offered and not taken; the owner asked for no exceptions. Requiring a label to *permit* a
  machinery change, rather than a label to stop it, inverts the default at the price of a step on every
  such change
- basis: E-129 (T1)
- affects: XC-218, AGENTS.md, OPEN-020
- decidedness: Fixed
- reversal_trigger: a merge that weakens the merging machinery and is noticed only afterwards in the
  log - which is the event this decision makes possible and the one that would settle whether the
  throughput was worth it

### XC-239 - The completeness check is shared, because the defect is not one reader's
- decided: 2026-08-24
- status: active
- decision: switching on every array a file offers, and then **checking by name that every one arrived**,
  is one concern held in `engine.completeness` rather than repeated per format. A reader supplies only
  what is its own: how to list what the file offers, and how to switch it all on. The check is shared,
  and a result that is missing stops the read
- decided_by: the product owner, 2026-08-24
- rationale: two of the toolkit's readers for formats this product's users actually work in read **no
  results at all** by default, through unrelated APIs and with no error either time - Exodus across 27
  count/name/status triples (E-136), CGNS across three `vtkDataArraySelection` objects (E-137). Two
  formats, two mechanisms, one defect: that is a pattern, and writing the answer a second time in the
  Exodus module would have been the beginning of writing it a third.
  The division is deliberate. The **switching** is an attempt that can fall behind a toolkit release,
  misspell a category, or miss an API that did not exist when it was written. The **check** cannot: it
  compares what came back against what the file said it held. So the shared half is the half that
  guarantees, and the per-format half is the half that can be wrong without costing anyone their results
- alternatives: a reader-agnostic sweep by reflection over `Get*ArraySelection` and `GetNumberOf*Arrays`
  would cover both without a per-format module, and replaces a reviewable surface with a clever one that
  nobody can audit against a specification
- basis: E-136 (T1), E-137 (T1)
- affects: MOD-002, ingest/REQ-015, XC-237
- decidedness: Fixed
- reversal_trigger: a third format whose reader reads everything by default, which would make this a
  two-format special case rather than a rule - measured, not assumed

### XC-240 - The values of a result sequence are read; what they mean is not guessed
- decided: 2026-08-24
- status: active
- decision: a @Case's sequence **values** are read from the pipeline's `TIME_STEPS` key, which every
  reader with a sequence publishes. Its **kind** is `UNDECLARED` unless a file states it in a way this
  product can read, and today none does - so every sequence this build reads is undeclared, carrying its
  values.
  Three consequences, each of which had to be decided rather than fallen into:
  - **`ResultAxis` may carry positions with an undeclared kind.** An earlier version refused that
    combination; it is the ordinary case.
  - **A lone `[0.0]` is discarded as the reader's placeholder**, so a steady case reports no axis rather
    than a position nobody wrote.
  - **Any undeclared axis put beside another result produces a statement** (ingest/AC-044), including
    beside another undeclared one carrying the same values
- decided_by: the product owner, 2026-08-24
- rationale: `vtkExodusIIReader` will answer the question if asked, and its answer is a guess it
  documents: mode shapes are inferred from two time values being identical (E-138). Two equal values in
  a transient restart would make a run modal, and `SetModeShape(n)` is `SetTimeStep(n-1)` - the same
  index with a different label. GL-036 exists for exactly this: a modal run and a transient run are the
  same numbers in the same shape of file, and calling mode 3 three seconds is a figure that is wrong
  about the physics while looking entirely right.
  Reading the values while refusing the kind is not half an answer. The values are what a file states
  and the kind is what it does not, and a product that showed one without the other would be choosing
  which of the two to invent
- alternatives: adopting the toolkit's guess makes this product agree with ParaView on the same file,
  including where ParaView is wrong, and agreeing with a known hazard is not compatibility (the same
  argument as XC-123); dropping the values because the kind is unknown throws away what the file did
  state; asking the user to name the axis on import is right and is a later task - it does not change
  what is read
- basis: E-138 (T1)
- affects: MOD-002, GL-036, features/ingest/tasks.md, XC-123
- decidedness: Fixed
- reversal_trigger: a reader that surfaces a file's own statement of its axis kind - CGNS's
  `SimulationType_t` is the nearest - at which point the kind is read from it and this product stops
  reporting undeclared for that format

### OPEN-026 - Where a variable bound to an input is recorded
- question: workspace/AC-009 requires that dropping a @Variable onto a numeric input binds that input, so
  later changes to the variable reach it. Nothing in the contracts has a place to record that binding.
  CT-001 has no field for it, and CT-004's `inputBindings` belongs to a MaterialX material's inputs
  rather than to a numeric field of a @View, @Graph or @Report definition
- why_open: the answer decides the shape of three contracts at once, and the two candidate shapes differ
  in a way that is hard to reverse. Either **an input holds a value or a reference** - every numeric
  field in CT-004, CT-005 and CT-006 becomes a union type, which is invasive and puts the binding where
  the input is - or **the workspace holds a table of bindings** keyed by a path into a definition, which
  leaves the definitions alone and makes a binding something that can be orphaned by an edit the table
  never sees.
  The second failure mode is the one to weigh: an orphaned binding is a variable a user believes drives
  something and does not
- blocks: workspace/TASK-011 and workspace/TASK-012, which cannot be written until there is somewhere to write to.
  workspace/AC-010's refusal - a binding whose units differ is refused naming both - is decided (XC-003's shape)
  and is only waiting on this
- closes_when: one of the two shapes is chosen, with the orphaning question answered rather than
  deferred, and the contracts it touches carry it
- affects: CT-001, CT-004, CT-005, CT-006, workspace/REQ-003, MOD-007
- decidedness: Open

### XC-241 - A lock is never broken automatically, and liveness fails towards keeping it
- decided: 2026-08-24
- status: active
- decision: a @Workspace lock records who took it - process, host, user and when - and is **never broken
  by the product**. A second open succeeds read-only and names the holder; a lock whose process cannot
  be found is reported as stale, read-only is offered, and the file is left where it is.
  Liveness is decided in one direction only: **anything not clearly dead counts as alive**. A pid on
  another host is never examined at all
- decided_by: the product owner, 2026-08-24
- rationale: the two answers a product usually gives are both wrong here. Refusing to open leaves a user
  who knows the other window is theirs, on the other monitor, with nothing to do. Opening twice for
  editing loses whichever save happens second, and loses it silently.
  The asymmetry in the liveness rule is the part with a measurement behind it. A pid says less than it
  appears to: ids are reused, protected processes cannot be signalled, and on Windows a missing process
  raises `OSError` with `winerror == 87` rather than `ProcessLookupError`, while pid 4 raises
  `SystemError` (E-139). A probe written for POSIX finds every lock alive here, and one that treats any
  error as "gone" declares the System process dead. Since neither error distinguishes the cases, the
  choice is which way to be wrong - and **a lock wrongly called stale is the failure that opens a second
  editor**, while a lock wrongly kept costs somebody a read-only window and a question
- alternatives: a heartbeat written into the lock would let staleness be judged by time rather than by
  pid, and it makes a machine that suspends look dead; breaking a lock older than some age is the same
  bet with a longer fuse
- basis: E-139 (T1)
- affects: MOD-007, workspace/AC-028, workspace/AC-029
- decidedness: Fixed
- reversal_trigger: a lock mechanism the operating system enforces - an exclusive file handle held open
  for the session - which would replace the judgement with a fact


### OPEN-027 - Whether a linter is one of the gates, and which rules it would enforce
- question: `ruff` is not a declared dependency, carries no configuration in this repository, and is run
  by no workflow. It runs only when whoever is working happens to have it installed, which is how two
  findings - an unused import and an unused local - stood in `tests/` across several merges without
  anything noticing. Either lint is a gate like the other ten, pinned and wired into
  `.github/workflows/ci.yml`, or it is not part of this project and should stop being run ad hoc
- why_open: the choice is not "lint: yes or no" but **which rules**, and a rule set adopted wholesale
  rewrites files for reasons nobody here chose. This project's existing gates each encode a stated
  reason - one definition per value, one implementation per shared component, evidence tiers - and a
  linter's default set does not. Two of its habits actively conflict with how this code is written:
  line-length reflow would break the comment paragraphs that carry the rationale, and import-order
  rewriting would move the `requires_vtk()` call that must run before the VTK imports beneath it.
  There is also a cost the other gates do not have: a pinned linter version turns a new release's new
  rule into a red build on a commit that changed nothing
- blocks: nothing. The tree is lint-clean as of 2026-08-24 and stays so by hand until this is settled
- closes_when: either a pinned `ruff` with an explicit rule selection is wired into CI and
  `check_gates_wired.py` sees it, or the decision is recorded that lint is not a gate here and the
  ad-hoc runs stop
- affects: pyproject.toml, .github/workflows/ci.yml, validate/check_gates_wired.py
- decidedness: Open

### XC-242 - A unit travels through an expression as a dimension, and an offset unit does not travel at all
- decided: 2026-08-25
- status: active
- decision: a value in the expression language carries a **dimension** - integer exponents over mass,
  length, time and temperature - together with the factor that takes it to the internal unit of that
  dimension. Not a unit symbol, and not a member of an enumeration of quantities.
  What each operator does with it:
  - `+ -`, every comparison, and `min max sum mean median std clamp` require **equal dimensions** and
    refuse otherwise, naming both units (INV-002, pipeline/AC-031)
  - `* /` add and subtract the exponents; `**` accepts only an integer literal exponent; `sqrt` halves
    them and refuses an odd exponent rather than producing a fractional one
  - `exp log log10 sin cos tan` require a **dimensionless** argument; `atan2` requires its two arguments
    to agree and returns a dimensionless value
  - `abs floor ceil round` keep the dimension they were given
  A result's unit is reported as the registered symbol whose dimension it matches - `Pa` for
  (1, -1, -2, 0) - and otherwise as a symbol composed from the internal base symbols in a fixed order,
  `m·s^-1`.
  **A unit that carries an offset may not be multiplied, divided, raised to a power, or passed to any
  function that is not `abs min max clamp`.** Absolute and difference (INV-028) then decide addition:
  absolute minus absolute is a difference, absolute plus or minus a difference is an absolute,
  difference plus difference is a difference, and **absolute plus absolute is refused**.
  **A bare number is dimensionless and undeclared** (XC-003). It may scale - `2 * p` is a pressure - and
  it may not be added to, subtracted from, or **compared with** a declared quantity: `stress > 200` is
  refused naming the unit the other side declared
- decided_by: the product owner, 2026-08-25
- rationale: the specification requires a length divided by a time to yield a velocity, which rules out
  an enumeration of quantities: a closed list cannot hold an open set of products, and every new
  combination would be a code change rather than an expression somebody wrote.
  The offset rule is the part with a measurement behind it. Doubling a value and converting it, against
  converting it and doubling it, agree exactly for every pure scale factor and differ by the offset for
  every unit that has one: 273.15 K for degC, 255.37 K for degF, 0.0 for K and for mm (E-141). So
  "twice this temperature" has no single answer, and whichever the evaluator returned would be one it
  invented - the failure this product exists to not commit.
  Refusing `stress > 200` is the expensive half of this decision and it is deliberate. A threshold
  written without a unit is the mistake that reads as correct: the comparison succeeds, the verdict
  prints, and whether it meant 200 Pa or 200 MPa is nowhere in the record. The cost is a unit somebody
  has to type once; the alternative cost is a wrong pass or a wrong fail with a plausible label
- alternatives: enumerating the derived quantities keeps the existing `Quantity` shape and cannot
  express an arbitrary product, so it fails the specification's own example. Treating units as opaque
  strings and requiring exact matches refuses `length / time`, which the language must support.
  A third-party unit library would supply all of this and brings a dependency into the distribution
  closure with the notice obligation that attaches to it (XC-025), and its defaults are the wrong ones
  here - the usual behaviour is to treat a bare number as matching whatever it is combined with
- basis: E-141 (T1)
- affects: MOD-004, MOD-011, pipeline/AC-030, pipeline/AC-031, pipeline/AC-033, specs/13_scripting.md
- decidedness: Fixed
- reversal_trigger: a unit these four exponents cannot express - a plane angle treated as dimensioned,
  an amount of substance, or a per-object unit such as "per cell" - which would need the dimension to
  carry more than the four

### XC-243 - A headless run reports one JSON object per line, and its exit code answers one question
- decided: 2026-08-25
- status: active
- decision: a headless run writes **JSON Lines** to standard output - one object per line, flushed as
  each line is written - with an `event` field naming the kind: `plan` before anything runs, `start`,
  one `unit` per unit per case as it finishes, and `finished` last. A run refused before it started
  emits `refused` and nothing else.
  The exit code answers **did any case fail**: `0` none, `1` one or more, `2` the run was refused before
  it started
- decided_by: the product owner, 2026-08-25
- rationale: pipeline/AC-022 asks for progress and outcome, and a single JSON document written at the end
  reports neither for the run that most needs reporting - the one killed at case thirty of forty. Line
  delimited output survives truncation, can be followed while it runs, and can be read by a program
  interested only in the last line. Flushing per line rather than per buffer is the same argument
  carried to the end: a buffered line is a line that is lost.
  `2` is separate from `1` because "a case failed" and "the run never happened" are different facts to
  whatever is calling. A caller that retries on failure should not retry a pipeline that will be refused
  again for the same reason.
  The tie-breaker where this could have gone either way is XC-012, reproducibility before convenience:
  the plan is emitted **before** the first unit so the log is usable as the record of what was
  authorised, rather than something reconstructed afterwards from what happened
- alternatives: a single JSON document at the end is smaller, easier to parse in one call, and silent
  about an interrupted run. A human-readable progress format needs a second machine-readable one beside
  it, and two formats of the same facts drift. A binary or length-prefixed stream is more robust to
  interleaving and unreadable without a tool
- affects: MOD-011, pipeline/AC-021, pipeline/AC-022
- decidedness: Bounded
- reversal_trigger: a consumer that needs interleaved output from several runs on one stream, which
  line delimiting alone does not disambiguate and which would need a run identifier on every line

### OPEN-028 - What a command's parameters are, in a form something can check
- question: CT-003's catalogue states each operation's parameters as prose in a table column - "case id,
  file paths", "view id, width, height, format". A handler in `src/service/command` declares the names
  it accepts, and the two are compared by nobody. CT-002 promises that an unknown parameter is rejected,
  and today that promise is kept against whatever the handler happens to have declared rather than
  against the contract
- why_open: the prose column is doing two jobs and only one of them can be mechanised. It names the
  parameters, which a machine could use, and it says what they mean in context - "source template id and
  revision?", "region?" - which is what makes the table readable to a person deciding whether an
  operation is the one they want. A parameter list generated from the prose would be a guess at where
  the names stop; a second machine-readable list beside the prose is two places to edit, and the day
  they disagree the checkable one wins silently
- blocks: nothing yet. The surface refuses an unknown parameter against what its handler declares, so
  the behaviour CT-002 asks for is present - what is missing is the check that a handler declares what
  the contract says
- closes_when: either CT-003's parameters become machine-readable in a form a person still reads
  comfortably - a schema per operation, or a stricter column grammar - and `check_commands.py` compares
  handler declarations against it, or a decision is recorded that the handler is the authority and the
  contract's column is documentation
- affects: CT-002, CT-003, MOD-012, validate/check_commands.py
- decidedness: Fixed
- status: superseded
- superseded_by: XC-249
- decided: 2026-08-25
- resolution: the first of the two candidates. `specs/contracts/schema/CT-003.json` gained
  `$defs.operationParameters` - one JSON Schema per operation, naming each parameter, its type and
  whether it is required - and the prose column stayed, doing the job it is good at: saying what a
  parameter **means** in context. The two are not two lists of the same thing, which is what made a
  second machine-readable list beside the prose the wrong answer.
  `validate/check_commands.py` now fails an operation with no parameter schema and a schema for an
  operation not in the catalogue, generates `PARAMETERS` into `src/service/command/catalogue.py`, and
  `service/command/surface.py` reads a handler's accepted and required parameters **from there**. A
  handler can no longer declare its own, so the enforcement holds against the contract.
  Authoring it found three operations the prose said were "A or B" - `variable.declare`, `script.run`,
  `report.provenance` - whose first schema required neither, and so would have accepted a call with
  neither
- basis: E-001 (T1)

### OPEN-029 - Which commands a pipeline unit issues, given that the catalogue has no shape for one
- question: pipeline/TASK-020 requires every unit to execute as commands from CT-002, with no execution
  path that bypasses them. Attempting it stops at the catalogue: **CT-003 has no operation shaped like
  "apply this pinned definition to this case"**, which is what every acting unit does. A `view` unit
  under three cases produces three pictures from one definition; `view.render` takes a view id, and a
  view id is a workspace item bound to its own source. The same gap holds for `graph`, `report` and
  `export`, and `tag` is the only acting kind with an operation that already takes a case (`case.tag`)
- why_open: there are three candidate answers and they differ in what the product *is*, not in how it
  is written.
  **One:** a unit is a sequence of existing operations - create a workspace item from the definition
  with this case substituted, render it, remove it. Nothing new in the contract, and every pipeline run
  litters the workspace with items it then deletes, which the undo history and the run record both see.
  **Two:** the catalogue gains a per-case form of each artefact operation, taking a definition reference
  and a case rather than an item id. Honest about what a pipeline does and it doubles part of the
  catalogue, which INV-006 then requires the interface to be able to do as well.
  **Three:** `template.apply` is already "apply a definition to a target selection" and a unit is that
  operation with the pipeline's target set as the selection. Closest to what exists, and it makes a
  workspace item's definition and a template behave alike in a place XC-109 deliberately separated them.
  Guessing between them here would settle the product's semantics as a side effect of an implementation
- blocks: pipeline/TASK-020, and through it the first half of pipeline/AC-021 - a headless run currently
  executes the identical units because it calls the same runner, not because it goes through the same
  command surface. pipeline/TASK-035 and pipeline/TASK-036 do not depend on this
- closes_when: one of the three is chosen and CT-003 carries it, including what the operation returns
  for a case that produced nothing
- affects: CT-002, CT-003, CT-009, MOD-011, MOD-012, pipeline/AC-021, INV-006
- decidedness: Open

### XC-244 - A declared unit may be a product or quotient of units this product knows
- decided: 2026-08-25
- status: active
- decision: a declared unit symbol may be a single known symbol or a **product or quotient of them with
  integer powers** - `m/s`, `kg/m^3`, `MPa·s`, `m·s^-1`. `/` inverts the term that follows it and every
  term after it. The components must be symbols the unit registry holds; composing combines declared
  units and does not invent new ones, so `N` is not a unit until somebody adds it.
  **A component carrying an offset is refused**: `degC/s` has no answer that survives the arithmetic,
  and a temperature rate is written `K/s`. A unit is printed back in the canonical composed form
  (`m·s^-1`), which may differ from what the user typed, for the same reason a value in MPa is labelled
  Pa - the printed unit is the one the number is in
- decided_by: the product owner, 2026-08-25
- rationale: this was a gap rather than a choice. CT-007's own worked example compares against
  `"unit": "m/s"`, and the registry held fourteen simple symbols and refused everything else - so the
  contract's example could not be evaluated, and **no user could declare a velocity, a density or a
  rate anywhere in the product**. XC-242 already made expressions produce composed dimensions; the
  asymmetry was that the product could write `m·s^-1` and could not read it.
  The offset rule is XC-242's, restated where it bites again: doubling before converting and converting
  before doubling differ by the offset, measured at 273.15 K for degC and 255.37 K for degF (E-141)
- alternatives: keeping only simple symbols and adding `velocity`, `density` and the rest to the
  registry as named quantities is the enumeration XC-242 already rejected - a closed list cannot hold an
  open set of products. Accepting any string and comparing symbols textually would make `m/s` and
  `mm/ms` different units, which they are not
- basis: E-141 (T1)
- affects: MOD-001, CT-007, CT-005, GL-020, XC-003, XC-242
- decidedness: Fixed
- reversal_trigger: a unit whose components are not integer powers of the four base quantities - a
  logarithmic unit such as a decibel, where a product of two values is a sum of two units

### XC-245 - Geometry is held in double precision, and a dataset refuses anything else
- decided: 2026-08-25
- status: active
- decision: `Dataset.points_m` is **float64**, checked at construction and refused otherwise. The
  readers convert on load, at the same place the canonical-frame conversion already happens (INV-001),
  and nothing downstream converts again
- decided_by: the product owner, 2026-08-25
- rationale: `vtkPoints` stores coordinates in float by default, and a cell volume computed from them
  carries about 5e-8 of relative error where the same coordinates in double are exact (E-142). That
  error does not stay in the geometry: INV-017 makes a summary statistic volume-weighted by default, so
  every reported average multiplies field values by those volumes.
  The measurement also shows why this had to be checked rather than assumed. Cubes of side 1.0 and 2.0
  agree to 1.1e-16 in both precisions, because those coordinates are exactly representable - a test
  written against a unit cube would have found nothing and reported that single precision was fine.
  The readers were already converting. What was missing was the guarantee: a habit in one function is
  not a property of the product, and the next reader is written by somebody who did not read that one
- alternatives: converting silently inside the dataset accepts single-precision input and hides where
  the conversion happened, which is the arrangement that makes a second conversion invisible when
  somebody adds one. Holding single precision to halve the memory is a real trade for **display**
  geometry, which is decimated and tessellated anyway and is already a separate object (XC-233) - it is
  not a trade for the geometry numbers are computed on (INV-001)
- basis: E-142 (T1)
- affects: MOD-001, MOD-002, INV-001, INV-017, graph/AC-022
- decidedness: Fixed
- reversal_trigger: a dataset large enough that double-precision coordinates do not fit in LIM-001's
  budget while single precision would, which would make this a choice between a wrong number and no
  number rather than between two representations

### XC-246 - Arithmetic happens in double precision; the source bounds what is shown, not what is computed
- decided: 2026-08-25
- status: active
- decision: every reduction, difference and derived quantity is computed in **float64**, whatever the
  field is stored in, with pairwise or better accumulation. Fields are stored at the precision the file
  gave them - a float32 result stays float32 in memory - and INV-014 continues to bound the digits that
  may be **displayed**. Converting the storage to double, and refusing to compute in double, are both
  wrong and in opposite directions
- decided_by: the product owner, 2026-08-25
- rationale: the two rules get confused because they both mention precision, and the confusion is
  expensive in both directions. Computing in the storage precision loses the answer: a float32 field of
  300.0 ± 1e-3 has an exact mean of 299.999999895342 and a float32-accumulated mean of exactly
  300.000000000000 - the variation is gone and the offset is printed to full width (E-143). Promoting
  the storage to float64 doubles the memory a case occupies against LIM-001 and buys nothing, because
  the digits beyond the source's precision are noise INV-014 already refuses to show.
  So: **store what the file gave, compute in double, show what the source supports**. Three separate
  decisions that a single word would have collapsed into one wrong one.
  Geometry is the exception, and it is an exception about storage rather than about arithmetic: the
  canonical frame holds float64 coordinates because volumes computed from them weight every average
  (XC-245)
- alternatives: accumulating in the storage precision is what a naive implementation does and is the
  measured failure above. Promoting every field to float64 on load is simple and halves the case size
  the memory budget allows. Compensated summation everywhere (Kahan, or `math.fsum`) is exact and is
  measurably slower than pairwise for a gain of 1.6e-16 against 2.2e-12, which is below what any of
  this product's inputs carry
- basis: E-143 (T1)
- affects: MOD-001, MOD-004, INV-014, INV-031, XC-245
- decidedness: Fixed
- reversal_trigger: an input format that stores more than float64 - a solver writing quad precision -
  which would make double the lossy choice rather than the safe one

### XC-247 - An averaged peak is never reported without the spread it was averaged from
- decided: 2026-08-25
- status: active
- decision: element values at a shared node are kept as the several values they are. A reported
  extremum states **averaged** or **unaveraged**; both are available; and an averaged figure is
  accompanied by the **spread** at that node - the difference between the largest and smallest
  contributing element value, and that difference as a fraction of the average.
  Neither is the default that gets applied silently. Where a report states one and not the other, the
  one it states is named in the sentence that states it
- decided_by: the product owner, 2026-08-25
- rationale: measured here, the averaged maximum of a stress concentration inside a body is **110 MPa
  against an element maximum of 200 MPa** - 55 per cent of it (E-144). Neither number is wrong; they
  answer different questions, and a report that gives one without saying which has answered neither.
  The spread travels with the averaged value because it is the **only discretisation indicator a
  post-processor can compute from a single solve**, and because the combination that misleads is
  precisely the smoothed peak shown alone: it looks converged. The reference product publishes the same
  quantity as Nodal Difference and states that a large one means the mesh needs refining there (E-145),
  so this is the field's existing vocabulary rather than a convention invented here.
  The measurement also fixes where the test has to be. The same concentration at an end face gives
  200 MPa either way, because that node belongs to one element - so a check placed at a boundary reports
  that averaging is harmless
- alternatives: reporting the unaveraged extremum alone is defensible and overstates a peak that is one
  element's integration artefact. Reporting the averaged one alone is what a smooth contour invites and
  is the measured under-report. Treating averaging as a display option rather than as two numbers is how
  a figure and a table on the same page come to disagree
- basis: E-144 (T1), E-145 (T1)
- affects: MOD-004, MOD-005, MOD-006, INV-017, INV-022, INV-032, INV-033
- decidedness: Fixed
- reversal_trigger: a solver that writes genuinely nodal results rather than element ones, where there
  is no spread because there was never more than one value

### XC-248 - ParaView's own code may be taken, and each piece taken becomes ours to maintain
- decided: 2026-08-25
- status: active
- decision: ParaView is BSD-3-Clause, so its readers and its application-level filters may be embedded
  in this product on the same terms as VTK (E-147, E-002). **The licence is not the constraint; the
  maintenance is.** Anything taken from ParaView is taken **by copying the source into this repository
  with its notice**, not by depending on the ParaView application, and it is recorded in the notices
  file beside VTK's.
  The rule for deciding is one question: **is this a reader, or is it behaviour?** A reader ParaView has
  and VTK does not - the Nastran BDF reader is the named example - is worth taking when a customer's
  format needs it, because a format is a fixed target and the cost ends. An application-level filter -
  plot-over-line - is **rebuilt rather than copied**, because it is behaviour this product will change,
  and a copied implementation diverges from its origin on the first change and then carries somebody
  else's structure forever
- decided_by: the product owner, 2026-08-25
- rationale: the specification already says the promise is written about VTK's readers rather than
  ParaView's menu, and that was read as though ParaView were unavailable. It is not: the licence
  expressly permits it, and reading a maintenance decision as a legal one leaves capability on the table
  for a reason that does not exist.
  The reader-versus-behaviour split is where the cost actually differs. A format does not change its
  mind; a filter does. Copying a reader buys a fixed amount of maintenance for a fixed amount of
  capability. Copying a filter buys an unbounded amount of both, and the first time this product wants
  it to behave differently the copy stops being an import and becomes a fork nobody named
- alternatives: depending on the ParaView application rather than copying from it would inherit
  upstream fixes and requires shipping and launching ParaView, which is a second application inside the
  product. Taking nothing keeps one dependency and refuses formats this product's own specification
  lists as Absent when the reader exists three metres away
- basis: E-147 (T1), E-002 (T1)
- affects: MOD-002, XC-049, XC-025, specs/09_technology.md
- decidedness: Fixed
- reversal_trigger: ParaView relicensing, or a reader whose upstream changes often enough that the copy
  is a liability rather than an import - which would make the dependency the cheaper of the two

### OPEN-030 - Whether this product is a "competing product" under the Omniverse terms
- question: XC-037 makes the Omniverse path optional and carries its attribution, usage-reporting and
  flow-down obligations. Two clauses of the same terms are recorded in E-009 and are **not** addressed
  anywhere: **8.12 forbids use in developing competing products**, and **8.9 forbids publishing
  benchmark or performance data**. This product is a CAE post-processor whose photorealistic path would
  be Omniverse; whether that makes it a competing product under 8.12 is a question about NVIDIA's terms
  and not about this architecture
- why_open: it cannot be settled by reading harder. 8.12's reach depends on what NVIDIA treats as
  competing, and the answer changes what may be built rather than how: if the photorealistic path is
  barred, XC-037's optional capability is not optional but absent, and the differentiator it was chosen
  for goes with it. Guessing in either direction is expensive - assuming permission builds a feature
  that may have to be removed after release, and assuming prohibition abandons a capability the terms
  may well allow.
  8.9 is narrower and also real: this project measures and publishes render performance as evidence
  (E-063 among others), and a measurement of the Omniverse path could not be recorded the way every
  other measurement here is
- blocks: nothing today - MOD-003 has no renderer at all and the Omniverse path is not built. It blocks
  the first line of code that links against it
- closes_when: NVIDIA states in writing whether a CAE post-processing product embedding Omniverse for
  rendering falls under 8.12, or counsel reads the current terms and records the reading here with its
  date - the terms are versioned and the answer is only good for the version it was read against
- affects: XC-037, MOD-003, OPEN-023, specs/09_technology.md
- confirmed: 2026-08-25, the same day, and by a second primary source rather than by re-reading the
  first. The Omniverse License Agreement shipped with `kit-cae` states it in as many words: **"you may
  not use the Omniverse Products for the purpose of developing competing products or technologies"**
  (E-151). A summarised fetch of the Product Specific Terms page taken minutes earlier reported that no
  such clause existed; the licence text is what settles it, and the recorded evidence (E-009) was right.
  So the question is not whether the clause exists - it does - but whether a CAE post-processor is a
  competing product under it. That remains an answer NVIDIA gives, not one this project reads out.
  Two further restrictions surfaced with it and narrow the question further: **the Kit itself may not be
  distributed at all**, and public distribution must go through NVIDIA's Exchange or a fork of NVIDIA's
  repository. XC-250 therefore places the whole Kit path outside what this product may embed, whatever
  8.12 turns out to mean - which lowers what this question is worth deciding, without closing it
- decidedness: Open

### XC-249 - What a command takes is stated by the contract, and a handler may not restate it
- decided: 2026-08-25
- status: active
- decision: every operation of CT-003 carries a **JSON Schema for its parameters** - the name, the type
  and whether it is required - in `$defs.operationParameters`. The prose column of the catalogue table
  stays and says what each parameter **means** in context; it is not a second copy of the same list.
  `validate/check_commands.py` generates the names into `src/service/command/catalogue.py`, and a
  handler registered with the command surface takes its accepted and required parameters **from there**.
  A handler has no field in which to declare its own
- decided_by: the product owner, 2026-08-25
- rationale: CT-002 promises that an unknown parameter is rejected, and until this the promise was kept
  against whatever the handler happened to declare - so the strictness held against a copy rather than
  against the contract, and a handler that listed one parameter too many widened the surface with
  nothing noticing.
  The prose was doing two jobs and only one of them can be mechanised: naming the parameters, which a
  machine can use, and saying what they mean in context - "source template id and revision?",
  "region?" - which is what makes the table readable by somebody deciding whether an operation is the
  one they want. Splitting the two jobs rather than replacing one with the other is why this is not the
  "second list beside the prose" that OPEN-028 rejected.
  Authoring the 134 parameters found three operations the prose stated as "A or B" whose schema at first
  required neither, and so would have accepted a call with neither
- alternatives: generating the schema from the prose column is a guess at where a name ends. Keeping a
  second machine-readable list beside the prose is two places to edit, and the day they disagree the
  checkable one wins silently. Leaving the handler as the authority makes CT-002's strictness a
  statement about implementations rather than about the contract
- basis: E-001 (T1)
- affects: CT-002, CT-003, MOD-012, MOD-013, validate/check_commands.py
- decidedness: Fixed
- reversal_trigger: an operation whose parameters genuinely depend on another parameter's value, which
  a flat per-operation schema cannot express and which would need the contract to carry a conditional

### XC-250 - What may be embedded is decided by the licence on the part, not by the name on the box
- decided: 2026-08-25
- status: active
- decision: "Omniverse" and "ParaView" are not single things, and this product decides part by part.
  **Embeddable, and used freely**: VTK (BSD-3, E-002), ParaView's own readers (BSD-3, E-147, under
  XC-248's reader-or-behaviour rule), **NVIDIA PhysX** (BSD-3, E-148), **NVIDIA MDL SDK** (BSD-3,
  E-149), **NVIDIA Warp** (Apache-2.0, E-150), OpenUSD (E-005), OpenVDB (E-006), OpenUSD Exchange SDK
  (E-007). None of these carries a hardware restriction, a field-of-use restriction or a
  competing-products restriction; each carries a notice obligation, which goes in the notices file
  (XC-025).
  **Not embeddable**: the **Omniverse Kit SDK and everything that requires it** - the RTX and IndeX
  render paths, and `kit-cae`. The agreement forbids distributing the Kit at all, requires public
  distribution to go through NVIDIA's Exchange or a fork of NVIDIA's repository, and forbids use "for
  the purpose of developing competing products or technologies" (E-151, E-152).
  Where a capability exists on both sides of that line, **the permissive part is taken and the
  restricted part is rebuilt or left out**, never depended upon
- decided_by: the product owner, 2026-08-25
- rationale: the question "can we use Omniverse" has no answer, and asking it that way produced two
  wrong ones in this project already - first that Omniverse was simply available (XC-037's optional
  path), then that ParaView was simply unavailable (XC-248's correction). The licence sits on the
  **part**.
  `kit-cae` is the case that makes the line visible. NVIDIA publishes OpenUSD file-format plugins for
  CGNS, EnSight, VTK and OpenFOAM that compose scientific datasets without conversion - which is this
  product's subject exactly - and they run on a Kit that may not be shipped inside somebody else's
  application. What is worth taking from it is the **idea**, which is not licensed: composing a result
  file as USD layers rather than converting it.
  MDL is the piece that changes what is possible. MaterialX is already this product's canonical
  material graph, MDL is what NVIDIA's renderers consume, and the SDK that translates between them is
  BSD-3 with no hardware restriction - so the photorealistic direction is reachable without the
  component that cannot be redistributed
- alternatives: treating the Omniverse licence as governing everything NVIDIA publishes leaves PhysX,
  MDL and Warp on the table for a restriction that does not apply to them. Treating BSD-3 on some NVIDIA
  repositories as evidence about others is the same error in the other direction, and it is the one that
  ends in a distribution somebody has to recall
- basis: E-148 (T1), E-149 (T1), E-150 (T1), E-151 (T1), E-152 (T1), E-147 (T1), E-002 (T1)
- affects: MOD-003, XC-025, XC-037, XC-248, OPEN-030, specs/09_technology.md
- decidedness: Fixed
- reversal_trigger: NVIDIA relicensing the Kit SDK permissively, which would move the whole RTX path
  across the line - or any of PhysX, MDL or Warp gaining a field-of-use restriction, which would move
  them back

### OPEN-031 - How a photorealistic path is reached, now that both candidates are unavailable as shipped
- question: XC-087 gives the product a photorealistic direction and XC-037 named Omniverse as the
  optional path to it. Measured on 2026-08-25, **neither candidate is reachable from what this product
  ships**, and for two unrelated reasons. Omniverse's Kit may not be distributed inside another
  application at all (E-151, XC-250). And the pinned VTK 9.5.2 wheel contains **no ray-tracing back end
  whatsoever** - no OSPRay, ANARI, OptiX, OpenVKL or Embree module among its 27 rendering modules
  (E-153) - so the path ParaView offers is absent from the build here
- why_open: the three ways forward cost different things and none is obviously right.
  **Build VTK from source with OSPRay enabled.** XC-034 chose the published wheel and listed two reasons
  to build later - size and disabling readers with advisories. This is a **third reason nobody had**,
  and it is a stronger one: it buys a capability rather than removing an obligation. It costs a
  toolchain, a multi-hour build and a per-release burden on three platforms.
  **Use OSPRay directly, beside VTK rather than through it.** OSPRay, Embree and Open Image Denoise are
  plain Apache-2.0 with no restrictions (E-154), run on CPU, and render **unstructured volumes** - which
  is CAE data. It avoids the VTK build and means writing the bridge from a @Dataset to OSPRay's scene,
  which VTK's own module already is.
  **Ship no photorealistic path in the first release.** XC-087 already makes the interactive and
  offscreen paths a division of labour, and both work today; the photorealistic one is the
  differentiator XC-037 was chosen for, not a requirement of any acceptance criterion.
  The measurement that would decide it does not exist yet: what OSPRay costs to render this product's
  own worst case (LIM-002's ten million triangles, LIM-001's eight gigabytes) on the integrated-graphics
  machine class, against what the OpenGL path already does there (E-063)
- blocks: nothing today - MOD-003 has no renderer. It blocks the first decision about how MOD-003 is
  built, which is the next substantial piece of work
- closes_when: OSPRay is measured on this product's worst case on the measured machine class, and one
  of the three is chosen against that figure rather than against the licence position, which is now
  settled either way (XC-250)
- affects: MOD-003, XC-034, XC-037, XC-087, OPEN-023, LIM-002
- decidedness: Open

### XC-251 - The renderer is reached through ANARI, so changing it is a back end and not a rewrite
- decided: 2026-08-25
- status: active
- decision: where this product renders by ray tracing, it targets **ANARI** - the Khronos scene API -
  rather than any one renderer's own interface. The back end is then a **choice made at run time from
  what the machine has**: Intel **OSPRay** on any CPU, NVIDIA **VisRTX** where there is an NVIDIA GPU,
  AMD **RadeonProRender** where there is a Radeon, and the SDK's own **`helide`** CPU reference where
  there is nothing else (E-155, E-156). All five of those - the SDK and the four devices - are
  Apache-2.0 or BSD-3-Clause with no field-of-use restriction.
  This does **not** decide that ray tracing ships (OPEN-031) or which back end is the default (XC-087
  governs the paths that exist today). It decides the shape of the seam, before anything is written
  against a shape that would have to be undone
- decided_by: the product owner, 2026-08-25
- rationale: the renderer is the single most likely part of this product to change, and the reasons are
  already visible: the licence position moved twice in one day of reading, the shipped build has no ray
  tracer at all (E-153), and the hardware a customer has is not something this product chooses. A seam
  that makes that change a back end rather than a rewrite is worth taking before the first line, and
  ANARI is that seam - it exists, it is Khronos, three vendors implement it, and Kitware already
  maintains a `Rendering/ANARI` module in VTK's source.
  It also settles the vendor question without settling it. Writing to OSPRay's interface would make
  Intel a dependency; writing to OptiX would make NVIDIA one and re-open everything XC-250 just closed.
  Writing to ANARI makes **none of them** a dependency, and a customer with an RTX card gets RTX while a
  customer with a laptop gets the same picture more slowly
- alternatives: writing to one renderer's interface is less code today and is the change this decision
  exists to avoid. Writing an abstraction of our own is the same work as ANARI with none of the
  conformance suite, none of the vendors and none of the specification. Rendering only through
  OpenGL - what the shipped build does - is what happens if OPEN-031 chooses the third way, and this
  decision costs nothing in that case because nothing is written
- basis: E-155 (T1), E-156 (T1), E-153 (T1)
- affects: MOD-003, XC-087, XC-250, OPEN-031, INV-002
- decidedness: Fixed
- reversal_trigger: ANARI failing to ratify - it is 1.0 since August 2023 with 1.1 in preview, and
  conformance still waits on the Adopters Program (E-155). A standard that stalls is an abstraction
  with one implementation, which is worse than the vendor interface it replaced
### XC-252 - The vocabulary crosses the language boundary by generation, not by a second definition
- decided: 2026-08-25
- status: active
- decision: `domain-core` is Python and the four layers above `service` are TypeScript, and the layer
  table says every one of them may depend on `domain-core`. That dependency is satisfied by
  **generating TypeScript types from the contract schemas** - CT-001 to CT-012 - into `src/ui/client`,
  by a gate that regenerates and compares, exactly as `object_compatibility.py` and `catalogue.py` are
  generated on the Python side. Neither language's types are written by hand, and neither is derived
  from the other: **both are derived from the schema**.
  What is generated is the **shape of what crosses the wire** - documents, definitions, commands,
  results. What is not generated is behaviour: units, dimensions, precision and the invariants stay in
  Python and are reached by asking the service, never reimplemented above it
- decided_by: the product owner, 2026-08-25
- rationale: there are only three ways for a TypeScript interface to know what a @Case is, and two are
  wrong. Writing the types by hand is a second definition of every contract, and the day it disagrees
  with the schema the interface is confidently wrong about the shape of a document. Generating
  TypeScript **from the Python** makes the Python the contract, which it is not - the schema is, and the
  Python is generated from it too in the places that matter.
  The behaviour half is the more important half. A TypeScript unit conversion, or a TypeScript
  significant-digits rule, would be a second implementation of the thing this product's claim rests on,
  and INV-002's promise that a renderer choice does not change numbers would become a promise about two
  codebases agreeing. The interface formats what it is given and asks for what it does not have
- alternatives: hand-written types are what most products do and are the source of the drift this
  avoids. A shared IDL other than JSON Schema would be a third description of contracts that already
  have one. Running Python in the interface through a bridge removes the duplication and puts an
  interpreter in the render loop
- basis: E-001 (T1)
- affects: MOD-015, MOD-016, MOD-017, MOD-009, MOD-010, CT-001, CT-003, XC-015
- decidedness: Fixed
- reversal_trigger: a contract whose shape cannot be expressed in JSON Schema well enough to generate
  from - which would mean the schema had stopped being the contract, and that is a larger problem than
  this decision

### XC-253 - What a command answers is stated by the contract, and a number in it arrives with its unit
- decided: 2026-08-25
- status: active
- decision: every operation of CT-003 carries a **JSON Schema for its result** - the field names, their
  types and which of them are required - in `$defs.operationResults`, the mirror of the parameter
  schemas XC-249 settled. Where a result carries a measured number it uses `$defs.reportedValue`, whose
  `value`, `unit`, `digits` and `provenance` are **required rather than optional**. The exceptions are
  three and each is checkable: a field whose own name carries the unit in the manner of GL-020
  (`minM`), a number the schema bounds to a ratio, and a number under an object that declares the unit
  once for a series of them (`graph.data`). `validate/check_commands.py` generates the field names into
  `src/service/command/catalogue.py` as `RESULT_FIELDS`, checks that no answer holds a bare number, and
  the command surface fails a handler whose effect carries a field the contract does not declare or
  omits one it requires - `failed` and not `refused`, because the caller did nothing wrong
- decided_by: the product owner, 2026-08-25
- rationale: the parameters became machine-readable and the results did not, which left the contract
  stating half of an interface. `result` was `additionalProperties: true` for all 61 operations, so no
  answer could disagree with the contract and every type generated above the service would have been
  `any` - the interface would have learned the shape of an answer by reading the engine, which is the
  coupling MOD-012 exists to prevent.
  The part worth the work is not the shapes. Several invariants are statements about **what a result
  carries** - a number with its unit (XC-003), its provenance (INV-013), the digits it honestly has
  (INV-014), the weighting a reduction used (INV-017) - and prose can only ask for those while a schema
  can require them. Making `unit` required of `reportedValue` turns "a value shown without its unit is a
  value in whatever unit the reader assumed" from a rule somebody remembers into one a build cannot
  break.
  The check found one on its first run: `dataset.describe` answered with the positions of the result
  axis and no unit, so a time axis in seconds and one in milliseconds were the same answer
- alternatives: leaving `result` open and validating in the interface puts the check downstream of the
  place that could still be wrong, and each client would carry its own copy. Describing results in the
  catalogue's prose column only repeats XC-249's problem one column to the right. Requiring the unit on
  every number without exception would force it onto ratios and onto coordinates whose name already
  carries it, and a rule with unstatable exceptions is one people disable
- basis: E-001 (T1)
- affects: CT-002, CT-003, MOD-012, MOD-013, validate/check_commands.py, src/service/command/surface.py
- decidedness: Fixed
- reversal_trigger: an operation whose answer is genuinely open-ended - a passthrough of a format's own
  metadata, say - which a closed field list cannot hold and which would need the contract to name the
  one place `additionalProperties` is allowed, rather than allowing it everywhere by default

### OPEN-032 - Which licensed font is embedded, now that every report needs one
- question: report/AC-015 requires a subset of a licensed font covering the characters a report holds, so the
  document renders identically on a machine with no such font installed. No decision names the font, and
  none names how the subset is produced
- why_open: the answer is a licence question and this project may not settle one from a summary. A font
  whose terms permit **embedding in a document that is redistributed** is a narrower set than a font
  that is free to use, and the difference is exactly the case here: a deliverable is sent to a customer
  who did not install this product. It also decides a build step - producing a subset needs a tool, and
  a tool is a dependency with its own licence and pin
- found: **the font is required of every report this product writes, not only of reports containing
  Japanese.** Expected the opposite and the check said otherwise on 2026-08-26: a document whose content
  is entirely Latin still carries characters outside the basic Latin set, because this product's own
  labels are Japanese - the provenance block says `ワークスペース`, `元ファイル`, `宣言された単位`. So a
  build with no embedded font produces empty boxes on any machine without a Japanese font installed, for
  every document it writes. That moves the font from a provision for some reports to a condition of the
  deliverable
- blocks: report/AC-015 and report/AC-016 in full. Not the writer: `engine.report.html` states the uncovered
  characters and the element each is in, and refuses to write until that list is accepted (report/AC-014), so a
  build without a font is honest rather than broken
- closes_when: a font is chosen whose **licence text**, read first-hand, permits embedding a subset in a
  redistributed document, and the subsetting tool is named and pinned
- affects: MOD-006, report/AC-015, report/AC-016, XC-024
- decidedness: Open

### XC-254 - An exported document states what it could not carry, and never substitutes something lesser
- decided: 2026-08-26
- status: active
- decision: the HTML writer answers `unrepresentable(document, capability)` **before** anything is
  written, `write()` refuses while that list is non-empty and unaccepted, and once accepted the same
  list is written **into** the document so the recipient reads it too. A rotatable @View is declared
  unsupported by a build without the vtk.js bundle rather than replaced with a still image. Characters
  no embedded font covers are named as characters, with the element each appears in, rather than
  counted. And the produced text is searched for an external reference and refused if one is found -
  checked of the output rather than trusted of the writer
- decided_by: the product owner, 2026-08-26
- rationale: the free export path measured here produced 34.4 MB for a 1.13 million point surface and
  **left the text annotation and the point label out of the file with no warning** while the scalar bar
  survived (spike/results.json). That is what a writer that drops what it cannot represent looks like
  from the outside: a document that appears complete, with no way for the reader to learn otherwise.
  Refusing before the file exists is what report/AC-014 asks for in its own words - "say so before writing the
  file". Writing the statement into the document as well is not in report/AC-014 and is the other half of the
  same argument: a refusal the operator accepted and the recipient never sees moves the silence one step
  along rather than ending it.
  A still image in place of a rotatable view would satisfy report/AC-001's sentence and not its requirement,
  and would be the harder failure to find later, because the document would look right
- alternatives: substituting a still image and stating the substitution is what report/AC-006 asks of the
  office formats, where the format genuinely cannot carry a scene; the interactive document can, and a
  build that has not yet been given the means is a different fact from a format that cannot. Writing the
  file and listing the omissions afterwards makes the list something somebody finds. Trusting the writer
  not to emit an external reference holds until a block's text carries one, which is the case that
  matters
- basis: E-001 (T1)
- affects: MOD-006, CT-006, report/AC-001, report/AC-014, report/AC-016, INV-007
- decidedness: Fixed
- reversal_trigger: a deliverable kind where partial output is worth more than none - a very large
  report where one unrepresentable block should not stop the other forty - which would need the refusal
  to become per-block rather than per-document
### OPEN-033 - The paid boundary is a capability, and the licence permits building it yourself
- question: XC-082 puts the finished deliverable - report generation and export - and the assistant on
  the paid side, and publishes the whole source under the Functional Source License. FSL forbids
  offering a competing commercial substitute; **it permits internal use**. A customer with a developer
  may therefore build the paid part from the published source and use it inside their own organisation,
  legally and without paying. Nothing in the record says whether that is intended
- why_open: it decides what is actually being sold. The comparison worth making is BioRender, whose
  free tier produces a figure with a watermark that cannot be removed and whose terms forbid using it
  in a paper, a grant application or anything commercial: what is sold there is **the right to publish**,
  not a feature. This product sells a feature, and a feature whose source the buyer holds is a feature
  the buyer can decline to buy.
  The alternative shape fits this product's own differentiator unusually well - the paid tier would be
  the right to send the deliverable to somebody outside the organisation, which is exactly the thing the
  free tools cannot produce and exactly what the customer wants it for. But it collides head-on with
  XC-082: a watermark whose source is published is a watermark somebody removes, and forbidding that
  is a licence term rather than a mechanism
- blocks: nothing today; the paid tier does not exist. It blocks the first pricing page and the licence
  text (both in the release backlog), and it should be settled before either is written
- closes_when: the record states which of the three it is - a capability gate accepting the self-build
  hole, a rights gate accepting the watermark hole, or a different mechanism - and says why
- affects: XC-082, XC-071, XC-028
- status: superseded
- superseded_by: XC-255
- decidedness: Open

### OPEN-034 - No asset is designated as the thing that takes time to copy
- question: XC-082's defence is a licence, and the "Attacking the recommendation" section already
  concedes that the differentiator is a user interface and that interfaces are copied. Nothing in the
  record names an asset whose reproduction costs **time** rather than effort
- why_open: a moat made of software logic is reproduced by anyone who decides the segment is worth
  having, and a moat made of "our users find the alternative hard to learn" is the barrier a capable
  language model removes fastest - which the same section names as the vulnerability without recording
  a defence.
  There is a candidate already half-built. XC-049's two tiers - verified and offered - describe a
  claim about **real files from real solvers**, checked round-trip, with what was dropped named. A
  corpus of those, accumulated through customers over years, cannot be generated: it needs the files,
  and the files come with relationships. That is the shape of BioRender's fifty thousand curated icons
  rather than the shape of a feature.
  A second candidate, unclaimed: this product's discipline is that a number arrives with its unit, its
  provenance and its honest digits, and that discipline is enforced by contract and gate rather than by
  habit (XC-253). As ungrounded output becomes cheap and abundant, a deliverable that cannot carry an
  unsourced figure is worth **more**, not less. The record notes the vulnerability to better models and
  does not note this
- blocks: nothing mechanical. It blocks knowing which work compounds, which is what decides the order
  of the release backlog
- closes_when: one asset is named as the moat, with what it costs to build and what it would cost a
  competitor to reproduce
- affects: XC-082, XC-049, XC-070
- status: superseded
- superseded_by: XC-255
- decidedness: Open

### OPEN-035 - The sales channel decided in XC-035 conflicts with the owner's stated constraints
- question: XC-035 fixes the first release as **invoice-based domestic business-to-business**: Japanese
  interface, a perpetual licence under JPY 399,000, an offline installer, sold directly. The owner's
  evaluation constraints of 2026-08-26 require a marketplace channel precisely to avoid the friction of
  internal approval, invoicing and contracts, and say direct business-to-business selling is to be
  avoided at first for reasons of credibility. **These are not compatible**, and one of them is wrong
- why_open: the reasoning behind XC-035 is strong and measured - the independent visualisation vendors
  total about USD 5 million between them (E-043), so a volume self-serve motion aims at a market that
  has not existed for anybody, while the differentiator is worth most to the buyer who cannot use a
  hosted tool. The reasoning behind the constraint is also strong: a single individual invoicing a
  manufacturer is a credibility problem before it is a sales problem.
  What makes it a real fork rather than a preference is that **there is no marketplace for this shape of
  product**. A standalone desktop application has no store; the stores that exist in this field sell
  add-ons to a host application, and becoming an add-on changes what the product is - it would mean
  selling deliverable generation inside somebody else's tool, which fits XC-082's paid boundary and does
  not fit XC-035's offline buyer
- blocks: the pricing page, the licence text, and the decision about whether the first release is a
  standalone application at all
- closes_when: either XC-035 is reaffirmed and the constraint relaxed for this product with the reason
  recorded, or XC-035 is superseded by a channel decision that satisfies the constraint
- affects: XC-035, XC-036, XC-071, XC-050
- decidedness: Open

### OPEN-036 - The buyer population is measured in people, and the buyer is an organisation
- question: E-029 measures 14,128 cumulative passes of the JSME computational mechanics certification
  from 2003 to 2025. XC-035's buyer is a **company**. No source in the record says how many
  organisations perform this work
- why_open: the target decides everything downstream and cannot be checked without this number. At the
  published prices of E-027 (USD 3,330 a year), JPY 20 million of annual revenue is about 40 seats; at
  XC-071's JPY 399,000 perpetual licence it is about **50 sales every year**, because a perpetual
  licence produces no recurring revenue. Fifty a year against a population of a few thousand people is
  a plausible share; fifty a year against a few hundred organisations is most of the market, every year.
  **The two readings differ by an order of magnitude and the record cannot tell them apart.**
  E-029 is also an upper bound on people, not a count of practitioners: it is cumulative over
  twenty-two years, it counts one person once per field across three fields, and the certification is
  voluntary, so it over-counts and under-counts at the same time
- blocks: any statement about whether the revenue target is reachable
- closes_when: a primary source gives the number of organisations performing this work in the first
  release's market, and the required customer count is restated against it
- affects: XC-070, XC-035, XC-071
- decidedness: Open

### OPEN-037 - The specification frames the product as CAE, and the owner states it is not CAE-specific
- question: every document in this set is written about CAE result files, and the market analysis of
  12_business_model.md is bounded by that framing - the category size, the vendor comparison and the
  population evidence are all CAE. **The owner stated on 2026-08-26 that the software is not
  CAE-specific.** Nothing records how far the scope extends, and the whole commercial analysis inherits
  the narrower reading
- why_open: the code already reaches past CAE, so this is not a hypothetical. Measured in this
  repository on 2026-08-26: the readers accept `.stl` alongside `.vtu`, `.vtp`, `.pvtu`, `.cgns`,
  `.e`, `.ex2` and `.exo` - and `.stl` is generic geometry, not a solver result. More telling,
  `domain_core/measurement.py` carries **metrological uncertainty** - standard and expanded, with the
  coverage factor required rather than optional (E-070) - which is the vocabulary of a test rig, a
  sensor and a calibration laboratory, not of a solver.
  What the engine actually is, on the evidence of its own code, is a path from a field dataset to a
  self-contained deliverable whose numbers carry their units and their provenance. CAE is the first
  vertical rather than the boundary. If that is right, then the population evidence in E-029, the
  vendor comparison in E-043 and the category size in XC-070 all describe **one segment of the
  addressable market**, and OPEN-036's arithmetic is being done against the wrong denominator
- blocks: XC-070's estimate, OPEN-036's denominator, and the priority order of the format work, which
  currently follows a CAE reading of OPEN-012
- closes_when: the scope is stated - which domains the first release serves and which it does not - and
  12_business_model.md says which of its figures are segment figures rather than market figures
- affects: XC-070, XC-035, XC-049, OPEN-012, OPEN-036
- decidedness: Open

### XC-255 - What is sold is that a result can be checked by somebody who was not there
- decided: 2026-08-26
- status: active
- decision: the product is repositioned around **verification rather than presentation**. The free side
  becomes reading, viewing **and checking**: a verifier that takes a deliverable and re-establishes its
  claims - that each number came from the named input, at the digits the source supports, in the unit
  somebody declared, and that the inputs have not changed since - is published, source-available,
  offline, and free permanently. The paid side becomes **issuing**: a deliverable carries an attestation
  naming the installation that produced it, and only a licensed installation can produce one that
  checks. The assistant's commentary is issued only with its check result attached (report/AC-024,
  report/AC-025, report/AC-026)
- decided_by: the product owner, 2026-08-26
- rationale: three things make this the answer rather than a repositioning for its own sake.
  **The mechanism is already specified and mostly built.** report/AC-007 records the workspace, the
  cases, the source files with their times, the declared units and the product version *inside the
  document*; report/AC-043 records the content identity of every input; report/AC-044 can state that an
  input has changed since; report/AC-028 to report/AC-030 resolve every citation to a retrieved document and
  keep the retrieved text; XC-253 makes a number's unit, provenance and honest digits required by the
  contract rather than by habit. **A deliverable this product produces already contains what a third
  party needs in order to check it.** What does not exist is the act of checking, the claim, and the
  issuer - and none of the three is large work.
  **It is the one asset a better model makes more valuable, not less.** Generation is what models make
  cheap, and organisations are about to receive many more engineering reports than anybody can read,
  each one plausible. The scarce question stops being "can this be produced" and becomes "which of
  these can be trusted". A deliverable that can be re-checked mechanically is worth **more** the more
  unverifiable ones exist - it is an asset anti-correlated with the thing that threatens the rest of
  the product, which is what resistance to model progress actually means. The previous defence -
  that the intended user cannot write the script - is the barrier a capable model removes fastest, and
  12_business_model.md already concedes it.
  **It closes the hole in the paid boundary.** A capability gate is bypassed by compiling the published
  source, which OPEN-033 recorded. An issuer identity is not: anybody may compile a signer and nobody
  may produce a signature that chains to a trusted root. This project already pays for exactly that
  economics under XC-051, because an unsigned installer is an installation failure rather than a saving.
  And publishing the verifier's source is not a giveaway here - **verification you cannot inspect is not
  verification**, so the source-available position of XC-082 stops being a risk to the business model
  and becomes a requirement of it
- alternatives: keep the capability gate - bypassed by the source, and it competes on usability, which
  is the barrier a model removes first. Close the source - forfeits the strongest form of the claim in
  XC-026, which is the thing this buyer wants most. Sell support and deployment (option C of
  12_business_model.md) - demonstrably where money moves in this category, and revenue scales with
  hours rather than copies, which is the one thing a single developer cannot scale
- basis: E-001 (T1), E-050 (T1)
- affects: XC-082, XC-071, XC-072, OPEN-033, OPEN-034
- decidedness: Bounded
- reversal_trigger: **the willingness to pay is a hypothesis and no evidence in this set establishes
  it.** Five conversations with the intended buyer in which nobody can name an occasion when a result
  was doubted, disputed or re-run because its provenance was unclear, would refute it. So would an
  incumbent shipping attested output first, which would make this a feature rather than a position
