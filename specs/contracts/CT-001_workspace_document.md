---
status: draft
updated: 2026-08-24
---

# Contract: workspace document

### CT-001 - Workspace document
- purpose: the saved form of a @Workspace - its @Case hierarchy, @Variable declarations and
  inheritance, @Simulation, @View, @Graph and @Report definitions, tags, and references to the result files it
  reads. Exchanged between the product and the user's disk, and between product versions over years
- schema: schema/CT-001.json
- version: 4.0.0
- strictness: unknown fields are **preserved**, not rejected and not dropped
- compatibility: a reader of an older version opens a newer document, keeps every field it does not
  understand, and refuses to write it back under the older version
- migration: a document written by an older version is upgraded on open, in memory; the file on disk
  is rewritten only when the user saves, and the pre-upgrade file is kept alongside until that save
  succeeds
- decidedness: Fixed
- basis: E-001 (T1), E-088 (T1)

## Why preserve rather than reject

The three options are not equivalent and the choice has to be made once, here.

**Rejecting** unknown fields catches typos at the boundary and is right for a contract between two
programs that ship together. **Dropping** them silently is never right: a user who opens a document in
an older build and saves it loses work with no error. **Preserving** them costs a little care in the
writer and is the only option that survives a user with two machines on two versions, which is the
normal case for a desktop product.

## Two corrections found by implementing it, 2026-08-24

**A case was required to carry a field the schema never defined.** `cases.items.required` listed
`variableOverrides`, and `properties` had no entry for it at all - so a conforming document had to carry
something of undefined shape. Worse, it is the concept XC-117 **corrected away**: the earlier model was
"inherited unless overridden", and the field that expresses the model this product actually has is
`variableStates`. Removed from `required`; documents that carry it keep it, as they keep any field
(`additionalProperties` is true). The version is unchanged, because no document could have conformed
meaningfully to a requirement with no definition.

**A variable had nowhere to say which case it belongs to.** workspace/AC-006 requires that a variable
added to a child @Case is not added to the parent, and every variable was declared in one workspace-wide
list with no field recording where it was declared - so a resolution written against that shape would
have shown a child's variable on its parent. `declaredOn` is that field: absent means the whole
workspace, and one case id means that case and its descendants. One field rather than a copy on each
case, for the same reason as INV-004.

`provenance` was added beside it, because GL-003 requires every variable to carry it and the schema had
no place for it either.

## What the document does not contain

- the result files themselves - only references with a recorded modification time and size, so a
  changed input is detected rather than silently re-read (workspace/AC-012)
- rendered images or reports - both are regenerated from definitions (XC-012)
- any absolute path that is not also recorded relative to the document, so a moved project still opens

Version 3.0.0 added what a @Case turned out to need beyond its files: its **state** (GL-039) and why it
is in it, its **@Result axis** - which may be a time, a mode number, or a frequency (XC-131) - and
**@Measurement data**, because validation requires measured values and reference material may not
supply them (XC-125). At workspace level it added **display units** (XC-134), **component frames**
(XC-122) and the workspace's **pipelines** (CT-009). Every one of these had been decided and was not in
the document; each was found by comparing a decision's date against the file it said it changed.

Version 4.0.0 separates `workspaceItems` from `templates` (XC-109). `workspaceItems` owns the concrete
simulations, views, graphs and reports that appear in each work area's list. Each entry in
`workspaceItems.simulations` is one @Simulation flow with one or more explicitly ordered external-solver
execution conditions; the array may contain multiple independently named flows (XC-154). The serialized
field keeps the historical name `templates` for version-4 compatibility, but contains workspace-scoped
reusable library entries (Templates and Assets under CT-008); shared and sample entries remain outside the
workspace document. Both may carry the same CT-004/005/006 definition shape, but they have different
identity and lifecycle.

A version 3 document used each entry in `templates.views`, `templates.graphs` and `templates.reports`
as both working artefact and reusable source. Migration preserves the old entry and identifier as a
workspace-scoped template so stored pipeline references remain valid, and creates a separate
workspace item with a new identifier, the same definition, and `sourceTemplate` pointing at that
template revision. `templates.simulations` becomes `workspaceItems.simulations`, because Simulation
has no template library in r1 (XC-147). Migration never merges or discards divergent definitions.

## Identity and ordering

Every @Case, @Variable, @Simulation, @View, @Graph and @Report carries an identifier that is unique inside the
document and never reused after deletion. Ordering shown to the user is stored explicitly rather than
implied by position in a list, so that a reordering is a change the format can express and a merge can
see.

Every workspace item and template carries an integer revision starting at one. An edit creates the next
revision under the same identifier; retained revisions make a pinned @Pipeline reference reproducible.
Creating an item from a template records the source identifier and revision as provenance only, not as
a live dependency (XC-109).
