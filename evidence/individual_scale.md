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

## E-187 - The population obliged to supply an SDS, measured

- tier: T1
- url: https://www.meti.go.jp/statistics/tyo/kkj/pdf/seizo_gaikyo2024.pdf (2024 年経済構造実態調査
  二次集計結果、製造業事業所調査、第 1 表) and
  https://www.stat.go.jp/data/e-census/2021/kekka/pdf/oroshikouri_outline.pdf (令和 3 年経済
  センサス-活動調査、卸売業、第 1 表)
- verified: 2026-08-30
- says: establishments, quoted from the tables themselves.
  Manufacturing, 2024 (survey date 1 June, **individual proprietorships excluded** by the table's own
  note): **16 化学工業 5,641** (5,664 in 2023, -0.4 %), **17 石油製品・石炭製品製造業 1,291**,
  **18 プラスチック製品製造業 13,745**, **19 ゴム製品製造業 2,380**; all manufacturing 222,200.
  Wholesale, as of 2021-06-01: **532 化学製品卸売業 17,852 establishments and 190,880 employees**
  (5.1 % and 4.9 % of wholesale), **533 石油・鉱物卸売業 5,804**; all wholesale 348,889
- justifies: OPEN-036
- note: **this settles the population question and it settles it in favour of the candidate.** The
  parties who manufacture or resell chemicals - all of whom owe an SDS on transfer under 安衛法
  57 条の 2 - number roughly **46,700 establishments** (5,641 + 1,291 + 13,745 + 2,380 + 17,852 +
  5,804). That is one to two orders of magnitude above every other measured population in this
  survey: 454 measurement institutions (E-172), 9,210 3D printers a year (E-179).
  Two qualifications, both material. **The chemical wholesalers average 10.7 employees per
  establishment** (190,880 / 17,852) - the individual-scale test is passed on the measured average,
  not assumed. And **the manufacturing counts exclude 個人経営 by construction**, so the smallest
  operators - precisely the ones the owner's constraint names - are outside the only number
  available. The figure is a floor, and it cannot be turned into a ceiling from published statistics

## E-188 - What the substance count actually rests on

- tier: T1
- url: https://anzeninfo.mhlw.go.jp/anzen/gmsds/gmsds640.html
- verified: 2026-08-30
- says: the ministry's own 職場のあんぜんサイト publishes the list of ラベル表示・SDS 交付義務対象
  物質 as an Excel file, currently at **2025-04-01**, and keeps the prior **2024-04-01 list of 896
  substances** beside it for reference
- justifies: OPEN-036
- note: **a correction to the tier E-186 claimed, not to its content.** 896 substances at 2024-04-01
  is confirmed at T1, from the ministry rather than from a vendor page. **The expansion to roughly
  2,900 by April 2026 is not.** The 政令改正 (令和 5 年政令第 265 号) and the 令和 8 年 4 月 1 日
  addition list exist and are cited by the ministry, but neither the ministry's Q&A page nor its
  意見聴取 page states a total in the text that could be read here; the 2,900 figure remains a
  T2 vendor and agency claim. It is the strongest single driver of the thesis and it is the one
  number in it still unverified at primary level

## E-189 - What it costs to enter this field, measured barrier by barrier

- tier: T1
- url: https://www.chem-info.nite.go.jp/chem/ghs/ghs_download.html (NITE, 政府による GHS 分類結果);
  https://www.mhlw.go.jp/stf/newpage_11237.html (厚生労働省, 化学物質対策 Q&A, Q9-2 and Q15-2);
  https://webdesk.jsa.or.jp/books/W11M0090/index/?bunsyo_id=JIS+Z+7253:2019 (日本規格協会)
- verified: 2026-09-02
- says: **the data.** NITE publishes the government GHS classifications as Excel, last updated
  **2026.07**, with the stated condition "本分類結果は、GHS に基づくラベルや SDS を作成する際に
  **自由に引用又は複写していただけます**" - and immediately after it, "引用又は複写により作成された
  ラベルや SDS に対する**責任は、ラベルや SDS の作成者にあります**". The same page states the
  classification is 参考 and that a supplier is free to record something different.
  **The obligation.** The ministry's Q&A states "ラベル表示及び SDS 交付の義務は、**化学品の譲渡・
  提供者にあります**" (Q9-2), and that since **2024-04-01 every 事業場 that manufactures, handles or
  supplies a リスクアセスメント対象物 must appoint a 化学物質管理者** whose duties include creating
  labels and SDS (Q15-2). **No qualification is stated anywhere for the author of an SDS.**
  **The standard.** JIS Z 7253:2019 is 100 pages at **JPY 5,720 including tax**
- justifies: OPEN-036, OPEN-037
- note: **every structural barrier to entry that could have existed here is absent, and each absence
  is quoted rather than inferred.** No licence to practise, unlike the 作業環境測定士 of E-172. The
  reference data is free and explicitly copyable. The statutory duty sits with the customer, not with
  whoever supplied the tool - which bounds the vendor's exposure to contract and reputation, and does
  not remove it. The specification costs less than a day's work. And the 2024 appointment rule means
  each of E-187's establishments now contains **a named person whose job this is** - a buyer that
  exists by law rather than by inference

## E-190 - An individual is already doing this work, at a price that changes the argument

- tier: T1
- url: https://coconala.com/services/1402824 and neighbouring listings in the same category
- verified: 2026-09-02
- says: on ココナラ, a consumer skills marketplace, the seller りすま offers
  「GHS/JIS 準拠の SDS を丁寧に作成・修正します」 at **JPY 15,000**, with **304 sales on this
  listing, 335 in total, a rating of 5.0 from 269 reviews**, platinum seller rank, identity verified,
  and **インボイス発行事業者 未登録** - the registration status of an operator below the consumption
  tax threshold. Turnaround is stated as **about 4 days (measured)** and first reply within 4 hours.
  Options are priced: foreign-language SDS +JPY 5,000, HS code +JPY 2,000, label specimen
  +JPY 5,000. Two further individuals sell the same service in the same category at **JPY 10,000**
  (Rino, メーカー研究職) and **JPY 15,000** (Chan25). A buyer's review reads
  「**個人事業者で知識がない中**、とても丁寧に説明や質問の回答をいただき」
- justifies: OPEN-036, OPEN-037
- correction: 2026-09-02. **This corrects the price floor E-186 recorded.** E-186 gave outsourced
  preparation as JPY 39,800 / 45,000 / 82,500 per sheet, from three agency pages, and reasoned from
  it that "a business preparing two or three sheets a year has no software option at all - only the
  agency". The agency prices are real and are not withdrawn. **But they are not the floor.** The
  floor is JPY 10,000-15,000, charged by individuals on a consumer marketplace, and the gap E-186
  described is between the JPY 75,000-a-month tool and JPY 15,000 a sheet rather than JPY 40,000 -
  a factor of five narrower than recorded, and in the direction that weakens the case for a tool.
- note: two readings, and both are load-bearing. **The entry question is answered by observation, not
  by argument**: one person, no licence, no employer, has sold 304 safety data sheets at JPY 15,000
  and holds a 5.0 rating - roughly JPY 4.5 million gross from a single listing. Individual entry into
  this field is not a hypothesis here; it is a measured fact, and the platform that carries it is
  reachable by anyone.
  **And the same fact is the strongest argument against building a tool for the smallest buyer.** A
  business preparing two or three sheets a year can pay JPY 30,000-45,000 to a human who needs no
  chemistry from them, carries the work, and delivers in four days. No subscription undercuts that,
  and no tool removes the buyer's need to understand what they are declaring. **The very segment the
  owner's constraint names is already served - by individuals, at a price a tool cannot beat.** What
  remains unserved is the buyer with tens to hundreds of sheets to write and re-write as the
  substance list expands, which is where per-sheet human work stops scaling and the JPY 75,000 tool
  begins - and that buyer is no longer individual scale

---

## What the three have in common, and what separates them from everything earlier

All three satisfy the constraint the owner set, and no earlier candidate did:

| | Buyer | Form fixed by | Price the buyer already pays |
|---|---|---|---|
| Patent drawings | **an individual inventor or micro-firm** | the patent office | **JPY 5,000 per figure** |
| Journal figures | **an individual researcher** | the journal | **USD 12-30 / month** for tools, weeks of delay otherwise |
| (as-built management) | a construction firm | MLIT | not published |
| (workplace measurement) | one of 454 institutions | the labour ministry | not published |
| (CAE reporting) | a company | nobody | not published |
| **Safety data sheets** | **~46,700 establishments, 10.7 employees average** | **JIS Z 7253** | **JPY 15,000 per sheet to an individual (E-190), JPY 39,800-82,500 to an agency; JPY 75,000/month for the cheapest tool** |

These are **the only measured cases in this whole survey where a form is fixed outside the buyer AND
the buyer is one person or close to it AND a price is published**. Of the three, only the safety data
sheet has all four of a legal obligation, a measured population, a published gap between what the
buyer pays and what the cheapest tool costs, and a form whose content is numbers requiring a source.
Patent drawings fail on the fourth; journal figures fail on the third (E-185).

## What is not settled

**Whether either of the first two needs this product's discipline.** A patent drawing needs correct
line work, not correct units. A journal figure needs correct axes, units and error bars - which is
this product's subject - but the tools selling into that space are illustration generators, and the
band is occupied anyway (E-185).

**What an SDS candidate would cost this project.** The fit is asymmetric and should be said plainly:
`domain_core`'s discipline - a declared unit, provenance travelling with a value, digits the source
supports, a stated absence rather than a substituted default - is the working vocabulary of an SDS,
and the deliverable writer already refuses to emit a document it cannot account for. **Everything
built for geometry would be discarded**: the reader, the decimation, the tessellation, the viewer,
and the visualisation half of the interface. The owner has said sunk cost is not a consideration;
this records what the cost is, not whether to pay it.

**Whether an individual can enter is no longer a question.** E-189 measures the barriers and finds
none of the structural ones present: no licence, free and explicitly copyable reference data, the
statutory duty resting on the customer, a JPY 5,720 standard, and a buyer named by law inside every
obliged establishment. E-190 then observes the thing directly - one person, 304 sheets sold at
JPY 15,000, rated 5.0. **The field is enterable and someone has already entered it.**

**What that same observation costs the software case** is recorded in E-190 and should not be read
past: it is the service that is enterable at individual scale, not the tool, and the smallest buyers
are already served by people at a price no subscription undercuts. The unserved buyer is the one
with tens or hundreds of sheets - which is a larger customer than the constraint allows.

**And the hard part of an SDS is not the document.** It is classifying a mixture under JIS Z 7252
from its components, which needs a hazard database and cut-off rules, not a specification read
carefully. NITE publishes government GHS classifications openly, which makes the data question
answerable; the expertise question is not answered here. A wrong SDS is a wrong legal document, and
that is the same failure this project's whole discipline exists to prevent - stated as the reason the
fit is interesting, not as evidence the risk is small.
