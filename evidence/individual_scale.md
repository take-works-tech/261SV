---
status: draft
updated: 2026-08-30
---

# Where a form is fixed outside the buyer, and the buyer is one person

A survey taken on 2026-08-30 under a constraint the owner set explicitly: **demand must exist at the
scale of an individual or a very small business**, or there is no first customer. Institutional
buyers - the 454 measurement institutions, the construction firms of `mandated_reporting.md` - fail
that test whatever their other merits.

The question this asks is therefore narrower than the earlier surveys: **where does one person have to
produce a document to somebody else's specification, and pay to get it right?**

## E-182 - Patent drawings: a fixed form, an individual filer, a per-figure price
- tier: T2
- url: Japanese patent-attorney fee schedules (lhpat.com, bon-gout-pat.jp, matsuda-pat.com,
  tsukahara-ip.com, ko-patent.com) and jpaa.or.jp FAQ
- verified: 2026-08-30
- says: patent firms publish **drawing preparation at about JPY 5,000-5,500 per figure** (one office
  quoting JPY 5,000 per drawing page, so five pages = JPY 25,000). A full individual filing is quoted
  at JPY 14,000 of official fees plus JPY 165,000-253,000 in attorney fees; some offices cap the whole
  document set at JPY 300,000
- justifies: OPEN-036, OPEN-037
- note: recorded T2 - these are law-firm marketing pages rather than a single authority. The structure
  is what matters and it is unusual: **the form is fixed by the patent office, the buyer is frequently
  an individual inventor or a very small firm, and the drawing is billed per figure.** JPY 5,000 a
  figure is a price an individual actually pays today

## E-183 - Journal figures: a fixed form, an individual author, and a documented rejection cycle
- tier: T2
- url: scholarviz.com and conceptviz.app guides to Nature/Science/Cell, Elsevier, PNAS and PLOS ONE
  figure requirements
- verified: 2026-08-30
- says: journals fix figure specifications in detail - **photographs at 300 DPI or more, combination
  figures 500, line art 1000** (600 where thin lines alias); **Nature rejects text outside 5-7 pt**
  while PLOS ONE permits 8-12 pt at final print size; PLOS ONE accepts **RGB or greyscale only, not
  CMYK**; TIFF must be LZW or uncompressed, never JPEG-compressed. The guides describe the failure
  plainly: "**Most figure rejections aren't about the science - they're a 2 mm width mismatch, a 96 DPI
  screenshot, or Calibri where the journal wanted Helvetica**", producing a "design → reject →
  redesign" cycle costing weeks
- justifies: OPEN-036, OPEN-037
- note: recorded T2 - these are the marketing blogs of tools that sell into this problem, quoting
  journal requirements. That they exist at all is part of the finding

## E-184 - The tools already selling into the journal-figure problem, and their prices
- tier: T2
- url: conceptviz.app, scholarviz.com, sci-draw.com, and directory listings
- verified: 2026-08-30
- says: **ConceptViz** sells AI-generated scientific diagrams at **USD 12-30 a month** with a limited
  free tier, the paid plans adding 4K output, watermark removal, a commercial-use licence and batch
  generation. **ScholarViz** produces "publication-ready scientific figures, graphical abstracts and
  slides with AI". **Sci-draw** claims **"35,000+ researchers, students and educators"**
- justifies: OPEN-037
- note: **the individual-scale price for a figure tool is USD 12-30 a month, and the market is being
  entered by AI diagram generators rather than by measurement tools.** They generate illustrations
  from prompts - they do not plot a researcher's own data, and nothing in their description addresses
  units, significant figures or provenance. That is the line between them and anything this project
  would build

## E-185 - The journal-figure gap is already served, at individual-scale prices
- tier: T2
- url: graphpad.com user guide "Exporting for publishing in journals" and FAQ 18/1402/1547;
  Prism pricing listings (capterra, saasworthy, freshscientific)
- verified: 2026-08-30
- says: **GraphPad Prism prices**: about **USD 18 a month for students**, **USD 142 a year** for a
  personal subscription, USD 500 for an academic group, and over USD 800 for an individual perpetual
  corporate licence. **Prism's own documentation covers journal submission directly**: a dedicated
  "Exporting for publishing in journals" chapter, TIFF/EPS/SVG guidance, DPI advice up to 1200 with a
  warning against 100, the white-background and alpha-channel handling journals require, RGB versus
  CMYK selection, and font-to-outline conversion on export
- justifies: OPEN-037
- note: **this closes the journal-figure candidate.** The gap proposed was "plot your own data to the
  journal's specification"; Prism does exactly that, documents it chapter and verse, and sells to
  individuals at USD 18-142. Origin sits beside it from USD 495. The AI illustration tools at
  USD 12-30 occupy the neighbouring concept-diagram niche. There is no vacant band and no unserved
  requirement - what remains is a crowded, mature, individually-priced market with two established
  incumbents and a wave of AI entrants

## E-186 - Safety data sheets: a mandate expanding threefold, and no small-scale price
- tier: T2
- url: journal.smartsds.jp, asahi-ghs.com/ghs_assistant/price.html, jei-inc.co.jp, ecoangel.jp,
  jcdb.co.jp/service/ezsds/
- verified: 2026-08-30
- says: SDS preparation is mandated in Japan by three laws (the chemical-substance management act,
  the occupational safety and health act, and the poisonous and deleterious substances control law)
  and the form is fixed by **JIS Z 7253**. **The scope is expanding sharply: 896 substances subject
  to the exchange obligation as of 2024-04-01, rising to roughly 2,900 by April 2026**, with further
  expansion planned for 2027.
  Prices: **outsourced preparation at JPY 39,800, JPY 45,000 and JPY 82,500 per sheet** depending on
  provider, the last adding a per-substance charge beyond ten components.
  **GHS Assistant**, a preparation tool, is **JPY 75,000 a month** for the single-PC Japanese-only
  Personal edition, JPY 110,000 with one extra language, JPY 150,000 for the multi-user Server
  edition, **minimum term one year** - and its page does not state a sheet-count limit
- justifies: OPEN-036, OPEN-037
- note: recorded T2 - vendor and agency pages. **This is the first candidate in the whole survey where
  every condition holds at once**: the form is fixed by a JIS standard, the obligation is legal, the
  obliged party includes very small chemical handlers, the numbers on the sheet are concentrations and
  physical properties that must be sourced, **and the cheapest tool costs JPY 75,000 a month against
  an outsourcing price of JPY 40,000 per sheet**. A business preparing two or three sheets a year has
  no software option at all - only the agency

---

## What the two have in common, and what separates them from everything earlier

Both satisfy the constraint the owner set, and no earlier candidate did:

| | Buyer | Form fixed by | Price the buyer already pays |
|---|---|---|---|
| Patent drawings | **an individual inventor or micro-firm** | the patent office | **JPY 5,000 per figure** |
| Journal figures | **an individual researcher** | the journal | **USD 12-30 / month** for tools, weeks of delay otherwise |
| (as-built management) | a construction firm | MLIT | not published |
| (workplace measurement) | one of 454 institutions | the labour ministry | not published |
| (CAE reporting) | a company | nobody | not published |

The first two are **the only measured cases in this whole survey where a form is mandated AND the
buyer is one person AND a price is published**.

## What is not settled

**Whether either needs this product's discipline.** A patent drawing needs correct line work, not
correct units. A journal figure needs correct axes, units and error bars - which is this product's
subject - but the tools currently selling into that space are illustration generators, which suggests
the money there is in drawing pictures rather than in plotting data honestly.

**And the population of neither is measured here.** Sci-draw's "35,000+" is a vendor claim about
users of one tool, not a market.
