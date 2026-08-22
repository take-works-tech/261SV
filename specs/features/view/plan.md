---
status: draft
updated: 2026-08-22
---

# Plan: view

- approach: a @View is a definition (CT-004) resolved against a @Case at draw time. Resolution is the
  same operation whether the view was just created, reopened from a saved workspace, or applied from a
  template made in another study - so there is one code path and one unresolved list, not three
- modules touched: MOD-003 visualization, MOD-002 dataset-io. Blast radius: the report module renders
  through the same definitions, so a change to resolution reaches MOD-006
- contracts touched: CT-004, CT-008
- technology: the web renderer for interaction, the native renderer for large data and for images
  destined for a document (XC-087); the optional photorealistic path is behind the same interface
- risks: two rendering paths that must agree on numbers while differing on pixels (INV-002); confusing
  View-local Object identity with reusable Asset identity (XC-166); and an Asset library whose imported
  entries carry licence terms into exports (XC-025); treating generated UVs as analysis data, or paying
  the atlas and seam-vertex cost for appearances that consume no texture coordinates (XC-167)

## Order of work

1. definition, save and reopen (REQ-001)
2. resolution and the unresolved list - shared with templates from the start (REQ-005)
3. renderer selection, capability probe, and the reduced path (REQ-002)
4. View-object identity and independent Object-asset instantiation (REQ-020)
5. library: materials, colour maps, fonts, backgrounds, scopes (REQ-004)
6. authored-UV preservation and lazy analysis-mesh texture mapping (REQ-021)
7. time navigation (REQ-006)
8. drawing presentations and dimensions (REQ-003)
9. image and video output (REQ-007)
10. USD export for external work (REQ-008)

Resolution is built second, before anything that uses it, because creating an item from a template is the
same operation - writing it twice is how the two versions come to disagree.

## What must be proven before this feature is called done

- switching renderer changes no reported value (INV-002)
- a dimension measures the dataset, not the reduced display geometry (INV-001)
- a template that resolves partly may create an independent View with the gaps named (XC-090, XC-109)
- an Object asset creates an independent View object and later Asset edits do not propagate (XC-166)
- authored UV sets round-trip unchanged, while UV-free analysis appearances allocate no UV data and a
  generated atlas remains derived display data (XC-167)
- an exported USD file states its unit and up-axis (XC-048)
