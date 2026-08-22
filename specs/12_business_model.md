---
status: draft
updated: 2026-08-19
---

# Business model

What is sold, to whom, at what price, and why they pay. Kept in the spec set because it constrains the
product: the priority of a requirement depends on which buyer it is for.

## The finding that changes the premise, and its correction

**A first pass concluded that an interactive 3D report in a single HTML file is not a differentiator,
because it has been free since 2019. An independent check measured the free path and narrowed that
sharply.** Both halves are recorded, because the corrected version is what the product is built on.

### What is genuinely free

- ParaView exports a scene into a standalone Glance HTML file since 5.7.0, and since 6.0.0 (2025-08-01)
  can do it with network access disabled (E-028)
- PyVista produces the same thing from one method call
- Ansys Dynamic Reporting, shipped with EnSight and Fluent, holds 3D scenes as report items and
  exports HTML, PDF and PowerPoint
- Siemens STAR-CCM+ has shipped a web viewer since 2022.1, with no licence needed on the viewing side
- VCollab is an entire company selling "3D digital CAE reports"

So "nobody offers a 3D scene in a browser" is false, and any pitch built on that sentence is empty.

### What the free path does not do, measured

An independent check exported a 1,128,448-point surface through the free path and read the exporter
source. Four limits are not opinions:

- **Text and labels are dropped, silently.** vtk.js does not serialise text actors or point labels, and
  VTK's JSON scene exporter writes only props that are `vtkActor`, discarding `vtkActor2D` - scalar
  bars, annotations, legends - with no warning. A measured value annotated on the geometry does not
  survive the export, and nothing tells the author it was lost
- **Size and time.** That one surface produced a 35.5 MB scene and a 48.5 MB HTML file in about 19
  seconds. Glance's own documentation scopes it to small and medium data
- **Time series are excluded.** ParaView's standalone-HTML option is disabled when exporting a series
- **The scene is one view.** There is no document structure - no table of values, no graph, no
  commentary, no verdict - because a scene exporter exports a scene

And the paid alternatives are not licence-free for the recipient: Ansys Dynamic Reporting requires a
licensed Ansys product, the Siemens viewer requires a STAR-CCM+ licence and a hosted service, and
VCollab requires a Pro licence and a server. **A single file that a recipient opens with nothing
installed is not what any of them ship.**

### The corrected position

The differentiator is not 3D in a browser. It is a **complete, self-contained deliverable**: geometry,
the numbers with their units, the graphs, the commentary and the verdict in one file, generated without
a person assembling a scene, and readable by someone who has bought nothing. Each clause of that
sentence is a thing the free path measurably does not do.

What remains unmeasured is how long the manual assembly currently takes. That gap is recorded rather
than papered over (evidence, "not verified here").

### XC-070 - Market size
- statement: the visualisation and reporting layer of CAE is roughly USD 650 million a year worldwide
  (estimate), the self-serve segment reachable by this product is USD 42-132 million (estimate), and a
  realistic three-year target for a single developer is USD 120,000-1,200,000 of annual recurring
  revenue (estimate)
- method: pure-play CAE vendor revenue identified from filings totals about USD 3.73 billion (Ansys
  2.545 B, Altair 0.666 B, and the smaller disclosed vendors); Siemens and Dassault do not disclose
  their simulation lines, so the world total cannot be closed from primary sources alone. The
  visualisation layer is estimated at 10 per cent of an assumed USD 6.5 billion software market, and
  **that 10 per cent attribution has no primary source - it is an assumption**
- decidedness: Bounded
- basis: E-025 (T1), E-026 (T1), E-029 (T1), E-042 (T1), E-043 (T1)
- correction: an independent check narrowed this twice. First, the USD 159 million figure for BETA CAE
  came from an internal-controls scoping statement, not a revenue disclosure; a narrower primary source
  exists - the CFO commentary of 2024-07-22 gives about USD 40 million for seven months, annualising to
  roughly USD 69 million, and a transaction-multiple triangulation gives about USD 121 million, so the
  real figure sits somewhere near USD 70-125 million. Second, BETA CAE is mostly ANSA, a
  pre-processor, so using it as the visualisation proxy overstates the layer. Third, and most
  important: the independent visualisation vendors that sell exactly this product shape are tiny -
  Ceetron's two entities report about USD 5 million between them

**The category is thinner than the first estimate suggested, and that is the central commercial fact.**
The USD 650 million figure describes visualisation *inside suites* - capability bundled with a solver
licence and never bought separately. The market for a standalone product that a customer buys on its
own merit is better indicated by the standalone vendors, and those are around USD 5 million in total
revenue. **The self-serve segment estimate of USD 42-132 million should be read as an upper bound that
is probably an order of magnitude too high**, and the honest planning number is closer to the standalone
vendors' scale.

That is not a reason to stop. It is a reason to price for a small number of customers who care a lot,
rather than for a large number who care a little - which is the opposite of the self-serve motion, and
is exactly the tension recorded in OPEN-009.

### XC-082 - Source-available, with the deliverable as the paid boundary
- decided: 2026-08-19
- status: active
- decision: the product's source is published under the Functional Source License, which permits every
  use except offering a competing commercial substitute and converts each release to MIT after two
  years. Ingest, visualisation and the interactive view are free to use. **The finished deliverable -
  report generation and export - and the assistant are the paid boundary**, sold as an annual
  per-seat subscription with an invoice. Language-model access is the customer's own key; this product
  never resells tokens
- alternatives: a fully permissive licence lets anyone offer the same product as a service on day one,
  which for a single developer is the whole business; a closed product forgoes the one thing this
  buyer wants most - the ability to read what runs inside their network. Charging for the viewer and
  giving away the report inverts the measured differentiator, since the report is the part the free
  tools cannot produce (E-048)
- basis: E-048 (T1), E-049 (T1), E-059 (T1)
- affects: XC-071, XC-014, XC-026, assistant/REQ-005
- decidedness: Fixed
- reversal_trigger: a competitor shipping a substitute from the published source despite the licence,
  or customers refusing to buy software whose source they can read - the second would be evidence the
  positioning is wrong, not the licence

**Why source-available rather than open or closed.** The buyer this product is for cannot send geometry
out of their network, and that same buyer wants to know what a binary does before it runs on it.
Publishing the source is not a giveaway to them - it is the strongest possible version of the claim in
XC-026, verifiable rather than promised. The licence keeps the one thing a permissive licence would
give away: the right to sell the same thing back.

**Why the report is the paid side.** It is the only part measured to be beyond the free tools: the free
export path drops annotations silently and costs 34 MB for a surface this product must handle
routinely. Making the free tier stop exactly where the free alternatives already stop is honest, and it
means the paid tier is defined by a measurement rather than by a marketing decision.

### XC-071 - Revenue model
- statement: an annual per-seat subscription, invoiced, is the primary form (XC-082). A perpetual
  licence with a twelve-month update window remains available for customers whose purchasing requires
  a capital item, priced under JPY 399,000 so it stays immediately deductible; support with a named
  response route is priced separately
- rationale: published prices in this category cluster where Tecplot sits - USD 3,330 a year,
  USD 7,860 perpetual, USD 1,820 maintenance, a maintenance ratio of 23.2 per cent. Everything above
  that line is quote-only. The Japanese threshold matters: a purchase under JPY 400,000 is immediately
  deductible for a small or medium company, which turns a purchase decision into an expense decision
- decidedness: Bounded
- basis: E-027 (T2)
- note: a subscription is fully deductible as an expense in any case, so the JPY 399,000 threshold
  argues for the perpetual option and is neutral for the subscription - which is why the subscription
  can be priced on value rather than against a tax line. XC-035 settles which of these channels comes
  first. The perpetual licence under JPY 399,000
  with invoice-based purchase is the first release; the card-paid subscription follows the domestic
  motion rather than running beside it, because a single developer supporting two purchase paths in
  two languages supports neither

### XC-072 - What the buyer is actually paying for
- statement: the product sells (a) that the customer's own files open without a scripting session,
  (b) that the numbers in the deliverable are traceable to the data, and (c) that the deliverable is
  finished rather than assembled. It does **not** sell the ability to display 3D in a browser, and it
  does not claim that capability is irrelevant to buyers - the evidence says the opposite
- rationale: the clearest evidence of what people pay for in this category is the pricing of the
  organisation that gives the software away. Kitware sells ParaView deployment at roughly USD 10,000,
  a response process at USD 15,000-35,000 a year, and patches for known vulnerabilities in older
  versions at USD 8,700 a year - each priced separately, and the maintenance scoped by a named list of
  formats
- decidedness: Bounded
- basis: E-027 (T2), E-028 (T1), E-044 (T1), E-048 (T1), E-049 (T1), E-050 (T1)
- correction: an independent check read the contract itself and narrowed this claim. What is sold is
  deployment work, a response process, and old-version patches. It is **not** a promise about results:
  the agreement disclaims any warranty as to results attained, caps liability at the lesser of fees
  paid and USD 10,000, defines an issue as a reproducible deviation from documented behaviour, and
  counts telling the customer that a problem is known and unresolved as resolving it. So (b) numbers
  are traceable and (c) the deliverable is finished are **this product's proposed differentiators, not
  observed market behaviour**. Nobody in this category currently sells them, which is either the
  opportunity or the reason nobody bothers - and the spec must not pretend the evidence settles which.
  A second correction: buyers demonstrably do pay for capability. United States federal sole-source
  records show the Air Force justifying Tecplot on best capability and interoperability, and NASA
  justifying FieldView as having no other known product performing the same function - organisations
  with free ParaView available, renewing paid licences on capability grounds. "They are not paying for
  the software itself" is therefore too strong, and the honest statement is that support, deployment
  and old-version patching are priced *separately and highly*, not that the product has no value

## The options considered

Each was scored on probability of success, revenue at success, scalability, reproducibility,
profitability and market size, with the weights set by a single-developer starting point.

| # | Option | The pitch | Why it wins | Why it loses |
|---|---|---|---|---|
| A | Perpetual desktop licence | one price, own it, updates for a year | matches how Japanese small manufacturers buy, and the sub-JPY 400,000 threshold makes it an expense | no recurring revenue until maintenance renewals accumulate |
| B | Self-serve subscription | card payment, per seat, monthly or yearly | reachable globally without a sales motion, which is the only motion a solo developer has | the buyers most likely to pay are behind procurement that does not use cards |
| C | Format assurance and support | "your files open, or we make them open" | this is demonstrably where money moves (XC-072); highest revenue per customer | it is a service business: revenue scales with hours, not copies |
| D | Report productisation | templates and conventions for a specific industry | highest willingness to pay per document; VCollab proves the demand | narrow, and close to consulting |
| E | OEM to solver vendors | the viewer inside somebody else's product | one deal replaces a hundred seats | a solo vendor is a supply-chain risk to any vendor large enough to want this |
| F | Free viewer, paid authoring | recipients read for free, authors pay | the free side is distribution, and Siemens already validates the shape | gives away the part that is easiest to demonstrate |

**Recommended combination: F as the distribution mechanism, A and B as the revenue, C as the entry into
larger accounts.** The free viewer is what travels inside a customer's organisation - the reason the
recipient of a report becomes the next buyer. A and B monetise authoring. C is what converts a company
that has already adopted the free viewer, and is priced as a service rather than as software.

D and E are declined for now, and the reason is recorded so it is not re-proposed: D narrows the
product to one industry before the product knows which industry it serves best; E requires a
counterparty to accept a single-person supplier, which is a conversation to have after there is a
customer list, not before.

## Attacking the recommendation

The strongest case against it, stated as strongly as it deserves:

**The moat is a user interface, and interfaces are copied.** Everything this product does can be done
today with ParaView plus a Python script. The defensible part is that the intended user cannot write
that script - which means the product competes on usability, and usability is what a well-funded
incumbent adds in a release when it decides the segment is worth having.

**The revenue arithmetic is tight.** At JPY 60,000 per seat per year, USD 500,000 of annual recurring
revenue needs roughly 800 paying seats. In a category whose largest specialist vendor is under
USD 159 million, and against a free alternative, 800 self-serve seats is a genuine sales problem, not
a rounding error.

**The two strengths pull apart.** The strongest wedge - Japanese small and medium manufacturers who
cannot send geometry outside their network and buy under a tax threshold - is a domestic, relationship
led, low-volume motion. The only motion a single developer can scale is global self-serve. Choosing
both means doing neither well, and this is the decision the founder has to make rather than the spec.

**What survives the attack.** Three things do. Offline operation is a real constraint that the free
web-based alternatives do not satisfy and that large vendors satisfy only inside expensive suites.
Trustworthy numbers - stated units, point-versus-cell association, provenance in the document, no
guessed values - is a positioning no free tool asserts and no incumbent advertises, and it is cheap for
this product to make true because the specification already requires it (XC-010, XC-013, INV-001).
And the assistant is only worth paying for if it is grounded in the loaded data (XC-013): an assistant
that confidently reports a number that is not in the file is worse than no assistant, and every
competitor is currently shipping the ungrounded version.

## Open questions this leaves

### OPEN-009 - Domestic-first or global self-serve
- decidedness: Open
- open: OPEN-009
- status: superseded
- superseded_by: XC-035
- question: the two motions need different products in their first year - one needs invoices,
  offline proof and a Japanese interface; the other needs a card checkout and English documentation.
  Which one is the first release for?
- affects: XC-071, XC-021

### OPEN-010 - Whether to incorporate before the first release
- decidedness: Open
- open: OPEN-010
- status: superseded
- superseded_by: XC-036
- question: an individual in Japan cannot obtain the cheapest code-signing route, and corporate buyers
  usually need an invoice from a company. Incorporation is a fixed annual cost against a revenue that
  does not exist yet
- affects: XC-051, XC-071
