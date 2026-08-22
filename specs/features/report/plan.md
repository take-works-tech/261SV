---
status: draft
updated: 2026-08-19
---

# Plan: report generation

- approach: a report is assembled from the same definitions the interface renders - @View, @Graph,
  values with their units - into a document that carries its own viewer. The 3D content is written as
  compressed geometry the page loads, and **everything else is text in the document**: values, units,
  annotations, provenance. That inversion is the product: the free path serialises a scene and loses
  the annotations; this writes a document that happens to contain a scene
- modules touched: MOD-006 report, MOD-003 visualization, MOD-005 graph
- contracts touched: the report is an output format, versioned like one
- technology: the report's own viewer is built on the same web renderer as the interactive view, so a
  scene looks the same in both. Office formats go through their own libraries; nothing here writes a
  layout engine
- risks: file size is the constraint that bites first - measured at 16 MB compressed for a million-point
  surface, and 34 MB through the free path

## Order of work

1. the document skeleton with values, units and provenance as text (REQ-003)
2. embedded geometry with the reduction path and its marking (REQ-001)
3. annotation and label survival, with refusal rather than silent loss (AC-014)
4. font subsetting for non-Latin text (AC-015)
5. office formats from the same content (REQ-002)
6. art style (REQ-004)
7. generated commentary, marked and grounded (REQ-005)

Text before geometry, deliberately: a report that is only text is still useful, and a report that is
only geometry is what the free tools already produce.

## What must be proven before this feature is called done

- the exported document opens with the network disabled and no installation
- every number in it equals the number the interface showed, and the ones from partial data say so
- an annotation that cannot be represented stops the export rather than disappearing (E-048)
- a Japanese or Chinese report renders on a machine with only Latin fonts (AC-015)
