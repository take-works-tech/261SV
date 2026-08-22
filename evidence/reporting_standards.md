---
status: draft
updated: 2026-08-20
---

# Evidence: what makes an engineering analysis report defensible

The product writes commentary with a language model. The question this evidence answers is not "how do
we make it sound professional" but **what an engineering audience will reject a report for**, and the
answer turns out to be written down in several places, by people who had to reject things.

### E-068 - The archetypal numerical-accuracy policy: no accuracy estimate, no publication
- tier: T1
- url: https://asmedigitalcollection.asme.org/fluidsengineering/article/108/1/2/409997/Editorial-Policy-Statement-on-the-Control-of
  and https://www.asme.org/wwwasmeorg/media/ResourceFiles/Shop/Journals/JFENumAccuracy.pdf and
  https://asmedigitalcollection.asme.org/fluidsengineering/article/130/7/078001/444689/Procedure-for-Estimation-and-Reporting-of
- verified: 2026-08-20
- says: the ASME *Journal of Fluids Engineering* has, since 1986 and in revised form since 1993, refused
  to accept any paper reporting a numerical solution that **fails to address systematic truncation error
  testing and accuracy estimation**. Acceptable means include Richardson extrapolation, high- and
  low-order methods on the same grid, and repeat calculations on finer or coarser grids; results should
  be shown over a range of significantly different grid resolutions to demonstrate grid convergence. The
  journal's normative procedure for reporting discretisation uncertainty is the Grid Convergence Index
  (Celik et al., *J. Fluids Eng.* 130(7):078001, 2008)
- justifies: XC-104, XC-107
- note: this is a fluid-dynamics journal's policy, not a general standard. It is cited as the archetype
  of the requirement rather than as a rule this product enforces: what transfers is that **a result
  presented without a statement about its numerical error is treated as unpublishable**, and that a
  single-grid result is the thing most often presented anyway

### E-069 - Verification and validation are different questions, and mixing them is a defect
- tier: T1
- url: https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics
  and https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-fluid-dynamics-and-heat-transfer
- verified: 2026-08-20
- says: ASME V&V 10 exists to give computational solid mechanics a **common language and conceptual
  framework** for verification, validation and uncertainty quantification. ASME V&V 20 specifies an
  approach that quantifies the accuracy inferred from comparing a solution against data at a specified
  validation point, using experimental-uncertainty concepts to account for errors in **both** the
  solution and the data. In V&V 20-2009, validation assesses model error and is explicitly **not a
  pass/fail exercise**
- justifies: XC-107
- note: the standards themselves are paid documents; what is verified here is their stated scope and
  the pass/fail point, from ASME's own pages

### E-070 - How a measured value is reported, from the metrology institute's own guidance
- tier: T1
- url: https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-7-reporting-uncertainty
- verified: 2026-08-20
- says: a reported result carries either the expanded uncertainty *U* **with its coverage factor k**, or
  the combined standard uncertainty *u_c*; U = 2u_c corresponds to roughly 95 percent and u_c to roughly
  68 percent, and **if the level of confidence differs significantly from those, it must be stated**. A
  full report lists the components of standard uncertainty with their degrees of freedom, describes how
  each was evaluated, and explains any choice of k other than 2. The guidance is explicit that it is
  **preferable to err on the side of providing too much information rather than too little**, and that
  uncertainty must not be inflated for anticipated uses
- justifies: XC-107, XC-104

### E-071 - The language that makes a statement unverifiable, enumerated by standard
- tier: T1
- url: ISO/IEC/IEEE 29148 (Systems and software engineering - Requirements engineering), and the INCOSE
  Guide for Writing Requirements, rule R7 "avoid vague words, terms and expressions"
- verified: 2026-08-20
- says: the categories of language that make a statement impossible to verify are enumerated:
  **superlatives** (best, most), **subjective language** (user friendly, easy to use, cost effective),
  **vague pronouns**, **ambiguous adverbs and adjectives** (almost always, significant, minimal),
  **open-ended non-verifiable terms**, **comparative phrases** (better than, higher quality), and
  **loopholes** (if possible, as appropriate). Such terms are to be avoided because they produce
  statements that are difficult or impossible to verify, or that admit multiple interpretations
- justifies: XC-104
- note: written for requirements, applied here to report sentences. The transfer is exact: a requirement
  and a report statement are both claims someone must be able to check

### E-072 - Fabricated citations survive expert review, in measured quantity
- tier: T2
- url: https://pmc.ncbi.nlm.nih.gov/articles/PMC12658395/ and https://arxiv.org/pdf/2602.05930 and
  https://www.tandfonline.com/doi/full/10.1080/08989621.2026.2645390
- verified: 2026-08-20
- says: in a controlled study of six simulated literature reviews, **19.9 percent of citations generated
  by a current frontier model were entirely fabricated**; a 2026 benchmark of thirteen models reports
  citation-hallucination rates between 14 and 95 percent depending on vendor. An audit of 2.5 million
  papers attributes roughly 146,900 fabricated citations to 2025 alone. Most decisively: fabricated
  citations were found in about **1 percent of papers accepted at a major 2025 conference, each of which
  had passed three to five expert reviewers**
- justifies: XC-105
- note: tier T2 because the individual rates come from studies of differing method and scope and should
  not be treated as one number. The conclusion drawn here does not depend on which rate is right - it
  depends only on the rates being far from zero and on expert review having demonstrably failed to catch
  them

## What this evidence settles

That a report of a computed result is judged on four things an author cannot talk their way past: the
number, its unit, what is known about its error, and where each claim came from. Everything in
[../specs/14_reporting_standards.md](../specs/14_reporting_standards.md) follows from those four, and
the generation design follows from the last of them being measurably unreliable when a model is left to
supply it.
