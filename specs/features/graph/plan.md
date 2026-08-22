---
status: draft
updated: 2026-08-20
---

# Plan: graph

- approach: a @Graph is a definition (CT-005) over quantities, resolved through the same selection
  contract the report uses (CT-007). Every value plotted comes from the analysis module; the graph
  module arranges and draws, and computes nothing of its own
- modules touched: MOD-005 graph, MOD-004 analysis. Blast radius: the report embeds graphs, so the
  definition shape reaches MOD-006
- contracts touched: CT-005, CT-007, CT-008
- technology: a plotting library chosen for style range, wrapped so that the definition rather than the
  library is what a workspace stores
- risks: the temptation to let the graph compute - a derived series is one line of code inside the
  plotting layer and a permanent breach of the rule that numbers come from one place

## Order of work

1. definition, series, units and provenance (REQ-001)
2. selection, declarative first (REQ-003)
3. manual construction over available quantities (REQ-002)
4. repeated-study handling and no-data drawing (REQ-004)
5. styles and templates from the library (REQ-006)
6. export, including animation (REQ-007)
7. recommendations, mechanical then model-assisted (REQ-005)

Recommendations come last deliberately: a proposal engine built before the manual path exists ends up
proposing what is easy to compute rather than what an engineer would draw.

## What must be proven before this feature is called done

- a series with an undeclared unit is labelled as undeclared, never assumed (XC-003)
- a case missing the quantity is drawn as no data and stays in the legend
- a failing selection selects nothing and says so, rather than yielding an empty figure (XC-089)
- every plotted value equals the value the analysis module reports for the same quantity
