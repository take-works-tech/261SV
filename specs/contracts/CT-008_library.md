---
status: draft
updated: 2026-08-22
---

# Contract: template and asset library

### CT-008 - Library entry
- purpose: how a @Template or an @Asset is stored, found, moved between scopes, imported and exported.
  The same envelope for a material, a font, a background, a camera path, an Object asset, a view, a
  graph and a report
- schema: schema/CT-008.json
- version: 2.2.0
- strictness: unknown fields are **preserved** - an entry authored by a newer build must survive being
  opened, moved between scopes and saved by an older one (CT-001)
- compatibility: an entry states the contract version of the definition it carries, so a view saved
  under CT-004 1.0.0 is recognisable as such after the definition format moves on. A 2.0 reader that
  does not support `viewObject` preserves the entry and reports it unsupported; it never partly applies
  the definition as another kind
- migration: on open, in memory; an entry is rewritten only when the user saves it
- decidedness: Fixed
- basis: E-001 (T1), E-088 (T1), E-095 (T1)

## Where entries live

| Scope | Where it is stored | What it travels with |
|---|---|---|
| sample | with the product | the installation; never edited in place, only copied into another scope |
| workspace | inside the @Workspace file | that workspace, including when it is sent to somebody else |
| shared | in the user's own library on this machine | nothing - it stays behind when a workspace is sent away |

A **shared** entry is bound to no @Workspace: it is available in every workspace on the machine, which
is what makes a house view or a report format a thing the whole team applies rather than a thing each
study reinvents. A **file** is the fourth destination - see below - and is how an entry crosses to
another machine or another person.

**Moving an entry between scopes is a copy with a recorded origin**, not a move: a workspace-scoped
material dragged into the shared library leaves the workspace able to open on its own. This is the
property that makes a workspace file self-sufficient, which matters most at the moment somebody sends
one to a colleague.

Editing a sample entry is not possible; the first edit creates a copy in the workspace scope, and the
copy records which sample it came from. That is what makes a shipped sample updatable without
overwriting somebody's work.

A View, Graph or Report template is never the corresponding working artefact (XC-109). Applying a
template previews the resolution result and then creates a new independent item in `workspaceItems`;
saving an item as a template snapshots its current definition into the chosen scope. The new item
records the source template identifier and revision only as provenance. Editing or deleting the
template later does not alter or invalidate that item. Live linkage and automatic propagation are not
part of r1.

## What an entry contains

- an identifier, a name, and the kind - `view`, `graph`, `report`, `viewObject`, `material`,
  `colourMap`, `font`, `background`, `displayStyle` or `cameraPath`; `viewObject` is the reusable Object
  category and never denotes the independently editable Object already owned by a View
- the definition itself, with the contract and version it conforms to
- the scope, immutable integer revision, the origin if it was copied, and when it was last changed
- for imported entries: what was imported, from where, and its licence if one was stated - a font or
  an environment image carries redistribution terms, and a product that ships user-imported assets
  inside an exported report has to know them (XC-025)

A `material` entry always carries CT-011. It has no PBR/result/composite subtype: MaterialX and the
typed CT-011 requirements are the definition, while dependency badges are derived. Editing a graph,
binding, resource or dependency creates the next immutable CT-008 revision. A reference from CT-004
therefore always names both entry identifier and revision (XC-174).

## What a template needs from its target

An entry that will be applied outside the workspace it was made in must say what it expects, because
the resolution report (below) is only useful if it can name what is missing rather than what is absent.
Every template therefore declares:

- **required references** - field names, units, @Variable names, part names it binds to. A reference
  that was implicit in the originating workspace becomes an explicit requirement on promotion or export
- **arity** - whether it applies to **one case**, to **many cases together**, or to either. A graph
  comparing five cases is inherently multi-case; a view of one geometry is not. Stating it is what lets
  a @Pipeline apply the template correctly without guessing (CT-009 `appliesTo`)
- **dependent entries** - assets it refers to, by identifier

Promotion to **shared**, and export to a file, both run this check first and report anything that was
only resolvable inside the originating workspace. **The entry is still promoted**; what changes is that
its requirements are now written down instead of assumed.

## Exporting an entry as a file

An entry exports to a **single self-contained file** carrying the definition, the declared
requirements, the contract version, and its dependent assets **embedded** - a template that arrives
without its colour map is a template that does not look like the one that was sent.

- an asset whose licence does not permit redistribution is **not embedded**; it is listed as a
  requirement by name, and the import says what to supply (XC-025)
- importing places the entry in the scope the user chooses - workspace or shared - and records where it
  came from and when
- an entry exported by a newer build opens in an older one, keeping the fields it does not understand
  (CT-001), and reports any part of the definition it cannot apply rather than applying it partly and
  silently

## Applying an entry

Applying a template is resolution followed by creation, not in-place substitution (XC-090, XC-109).
Every reference in the definition is looked up in the target: field names, units, time steps, and
other entries it depends on. Before creation, the user sees what will resolve and a list of what will
not, with the reason for each. Acceptance creates a new workspace item containing the resolved
definition and the unresolved list. Applying a `viewObject` entry creates a new independent @View object
inside the open View and records the source entry identifier and revision as provenance; later entry
edits never propagate silently. Applying any other Asset remains an edit to the open item after preview.
Neither path creates another View, Graph or Report.

Applying a Material Asset creates or replaces one targeted CT-004 Material Binding after preview. A
structurally incompatible target is refused without change. An accepted Asset whose declared
`solviaResult` or other required input is not available remains as a failed, repairable binding and is
drawn diagnostic magenta rather than inheriting the previous successful material (XC-175, XC-176).

**An asset never changes a value.** A material, a colour map or a font changes what a picture looks
like, while an Object asset instantiates a display definition. The numbers reported beside either are
computed from the dataset and are identical whichever Asset is applied (INV-002). This is why Assets
can be shared freely between studies that have nothing else in common.
