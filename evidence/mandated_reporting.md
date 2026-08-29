---
status: draft
updated: 2026-08-30
---

# Where a report is mandatory, and who supplies the software

A survey taken on 2026-08-30 of fields where **the form of a report is fixed by law or by a
ministry specification**, and where the number in it must be defensible. This is a different question
from the one in `market_survey.md`: not "who visualises data" but "who is required to submit a
document in a prescribed form, and what do they use to make it".

The reason for asking it is the pain ranking the owner put: **being unable to submit** is a stronger
pain than a report taking a long time, and it exists only where a form is mandated.

## The three that recur

| | ICT as-built (出来形管理) | Workplace-environment measurement (作業環境測定) | Electronic delivery (電子納品) |
|---|---|---|---|
| Legal basis | MLIT 3D-measurement as-built management specification, **令和8年3月版** | **労働安全衛生法・作業環境測定法** | MLIT delivery specifications |
| Forms | by work type | **A / B / C / D / noise (N) / dioxin forms** | ~350 variants |
| Population | not measured here | **454 measurement institutions**, association members only | not measured here |
| Licence to practise | - | **作業環境測定士** (registered) | - |
| Precision written into the rule | **±50 mm (foundation), ±100 mm (retaining wall)** | concentration standards, significant figures per form | - |
| Existing software | KENTEM et al, **no published price** | 環境Office (秋田環境測定センター), **no published price** | KENTEM, ワイズ (JPY 14,980 perpetual) |

**All three publish no price, or a price only for the cheapest tier.** That is the same shape as the
report-shaped products in `market_survey.md`, and it is now visible in three unrelated fields.

## E-171 - The Japanese mechanical CAE market is not shrinking
- tier: T2
- url: https://www.nikkei.com/article/DGXZRSP688285_T10C25A3000000/
- verified: 2026-08-30
- says: Yano Research puts the domestic mechanical CAE market at **JPY 104.183 billion for 2024**
  (107.4% of the prior year), JPY 97.014 billion for 2023 (107.6%) and JPY 90.164 billion for 2022
  (106.5%), on a vendor-revenue basis
- justifies: XC-070, OPEN-036
- note: recorded at T2 - a newspaper report of a research firm's figure, not the firm's own
  publication, and the breakdown between solver licences, maintenance and visualisation is not
  published. **It corrects the impression left by E-043**: the standalone visualisation vendors total
  about USD 5 million, but the market they sit beside is JPY 100 billion in Japan alone and growing
  about 7 per cent a year. The category is thin; the field around it is not

## E-172 - A second mandated-form field with the same shape, and its population
- tier: T1
- url: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000046255_00002.html (register, xlsx) and
  https://www.jawe.or.jp/association/about/
- verified: 2026-08-30
- says: the ministry publishes a register of workplace-environment measurement institutions able to
  analyse concentration-standard substances; the 令和7年10月1日 sheet lists **47 institutions against
  119 substance columns**, and states these are institutions that **asked to be listed**. The
  association's own figures for 2025-03-31 give **872 members, of which 454 are measurement
  institutions**, 34 in-house measuring workplaces and 307 individual 作業環境測定士
- justifies: OPEN-036, OPEN-037
- note: **the first measured population of a mandated-form field in this survey.** 454 institutions
  is small in absolute terms and large relative to the standalone CAE visualisation category. Each is
  an organisation that must produce prescribed forms repeatedly, by law, with registered practitioners
  signing them

## E-173 - What the incumbent software in that field actually does
- tier: T1
- url: https://www.aksc.co.jp/office/software4/
- verified: 2026-08-30
- says: 環境Office 作業環境ソフト produces the A, B, C, D, noise (N) and dioxin forms and the new
  model form for personal sampling. Its stated features include **"計算方法・有効数字・小数点桁数の
  カスタマイズ"** and output against **multiple concentration bases (管理濃度・許容濃度・ACGIH)**,
  with Excel-linked drawing management. **No price is published**; the vendor is a single company
  (秋田環境測定センター株式会社)
- justifies: OPEN-037, XC-071
- note: **significant figures per form are a headline feature of a shipping product in this field.**
  That is INV-014's subject, arrived at independently by a vendor selling to registered
  practitioners - evidence that the discipline this product enforces is a requirement somebody
  already pays for, in a field this product has never considered

---

## What the three fields have in common

1. **A form fixed outside the vendor.** Nobody competes on layout; they compete on conforming.
2. **A practitioner who signs.** Registered measurers, site engineers, submitting contractors.
3. **A supplier who publishes no price**, and in each case a small domestic company.
4. **Significant figures, units and tolerance judgements are the product**, not a nicety.

Point 4 is the one that bears on this project: the discipline in `domain_core` - a declared unit,
provenance travelling with a value, digits the source supports, a stated absence - is not a CAE
concern that happens to be rigorous. **It is the working vocabulary of every field where a number is
submitted to somebody who may reject it.**

## What is still not settled

**Why none of them publishes a price.** Two readings, and they point in opposite directions:
(a) form coverage differs per customer so no list price is possible - which is a barrier to entry and
therefore an opportunity; or (b) the customer count is small enough that every sale is a conversation
- which is bad news about the size. This survey cannot separate them, and no amount of further
reading will. It needs one conversation with one vendor or one practitioner.

**And the population of the other two fields is unmeasured.** 454 is the only measured figure here.
