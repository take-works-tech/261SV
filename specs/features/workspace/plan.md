---
status: draft
updated: 2026-08-19
---

# Plan: workspace, cases and variables

- approach: the @Workspace document is the product's only persistent state and is treated as a
  contract from the first commit (CT-001). Values are stored as declarations rather than resolved
  results: a child @Case records that it inherits or that it overrides, never a copy of its parent's
  number, so inheritance is reconstructed on load rather than baked at save. Unknown fields are
  preserved through a load-and-save cycle
- modules touched: MOD-007 workspace, MOD-001 domain-core. Blast radius: every module reads the
  hierarchy, so a change to the document shape reaches all of them - which is why the schema is
  versioned before there is anything to version
- contracts touched: CT-001
- technology: a plain file the user can copy, with a JSON document inside a container; no database
- risks: the save path is the one place where a defect destroys work rather than annoying someone.
  Everything about it is written defensively and tested by damaging files on purpose

## Order of work

1. the document schema and its round trip, including unknown-field preservation (REQ-004)
2. the hierarchy and its guards (REQ-001)
3. variables, inheritance and override (REQ-002)
4. binding variables into inputs (REQ-003)
5. tags and filtering (REQ-005)
6. import suggestions, last and optional (REQ-006)

The document comes first because everything else writes into it, and a format changed after three
features are storing data is a migration rather than an edit.

## What must be proven before this feature is called done

- a saved @Workspace reopens to the same output (INV-005)
- a @Variable has one definition, and inheritance resolves rather than copies (INV-004)
- a damaged file never overwrites the original (workspace/AC-013)
- a document written by a newer version keeps its unknown fields when an older version saves it (CT-001)
