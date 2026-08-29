---
status: draft
updated: 2026-08-30
---

# The products that already exist, and where the holes are

A survey of what a customer can buy today in and around this product's space, taken on 2026-08-30
against three hole patterns the product owner named: **(1)** a price band incumbents vacated by moving
upmarket, **(3)** a geography, language or standard a global product does not fit, **(4)** a live
market served by a product that stopped moving.

Every price below is quoted from the vendor's own page or price list, with the URL. Where a vendor
publishes no price, that is recorded as a finding rather than estimated - **a category where nobody
publishes a price is a category with no self-serve motion, and that is itself the shape of hole (1).**

## What the survey does not cover

Unit sales, customer counts and revenue: none of these vendors disclose them, and no primary source
gives them. Every judgement here about "the market is alive" rests on the product still being sold and
maintained, not on a measured customer count. Where a product's maintenance stopped, that is stated.

---

## The price map, as measured

| Product | Form | Published price | Source |
|---|---|---|---|
| ParaView, PyVista, VTK | desktop / library | **free** | open source |
| **Origin** (OriginLab) | desktop | **from USD 495**, annual or perpetual, first year of maintenance included | originlab.com/ordering |
| **CALS Manager 14** (ワイズ) | Windows desktop | **JPY 14,980 per licence, perpetual**; free edition = the same features for one year | wise.co.jp/quickproject/cm/ |
| **蔵衛門クラウド** | SaaS + mobile | **JPY 1,200 per person per month**, no setup fee, up to two months free | kuraemon.com/plan/ |
| **Tecplot Focus** | desktop | **USD 1,670/yr** or **USD 4,030 perpetual**; maintenance USD 920/yr | cts.com.au price list |
| **Tecplot 360** | desktop | **USD 3,330/yr** or **USD 7,860 perpetual**; maintenance USD 1,820/yr | same |
| POSTFLOW (ソフトフロー) | Windows desktop | **not published** - Lite edition free, capped at 5 slides and watermarked | softflow.jp/postflow/ |
| VCollab | desktop + browser viewer | **not published** - enquiry only | vcollab.com |
| 電子納品支援システム (KENTEM) | Windows desktop | **not published** - enquiry only | kentem.jp |
| LabDAMS (日立ハイテク), OpreX LIMS (横河) | on-premise system | **not published** - enquiry only | vendor pages |
| JCSS calibration certificates | **a service, not software** | per-instrument service pricing | mitutoyo.co.jp, nite.go.jp |

**The band between JPY 15,000 perpetual and USD 3,330 a year is where almost nothing is published.**
Origin at USD 495 is the only vendor in this survey selling a technical-analysis desktop product in the
middle with a price on the page.

---

## E-160 - The vacated price band in analysis post-processing and reporting
- tier: T1
- url: https://www.cts.com.au/Tecplot%20Prices.pdf and https://www.originlab.com/ordering
- verified: 2026-08-30
- says: Tecplot's own international price list gives Focus at USD 1,670 a year / USD 4,030 perpetual
  and 360 at USD 3,330 a year / USD 7,860 perpetual, with maintenance renewals of USD 920 and
  USD 1,820. OriginLab publishes commercial licences "as low as $495". Below that, the alternatives in
  this category are free (ParaView, PyVista). **No vendor found in this survey publishes a price
  between USD 495 and USD 1,670 for analysis post-processing**, and the vendors of the report-shaped
  products (VCollab, POSTFLOW, KENTEM, the LIMS vendors) publish no price at all
- justifies: XC-070, XC-071, OPEN-036
- note: absence of a published price is evidence about the sales motion, not about the price. It means
  a buyer cannot self-serve, which is the friction the product owner's own constraints name

## E-161 - A Japanese standard with roughly 350 variants, served only by enquiry-priced desktop software
- tier: T1
- url: https://www.kentem.jp/product-service/dns/ and https://www.wise.co.jp/quickproject/cm/
- verified: 2026-08-30
- says: KENTEM's 電子納品支援システム states it covers "国土交通省ほか全国約350種類の電子納品要領（案）"
  - roughly 350 separate delivery specifications issued by the ministry and local authorities - and
  publishes no price. ワイズ's CALS Manager 14 is a Windows desktop application at JPY 14,980 per
  perpetual licence, with a free edition offering the same features for one year
- justifies: OPEN-037
- note: **this is the shape of hole (3) in its purest form.** No global product fits ~350 Japanese
  delivery specifications, and none will: the specification set is the barrier, and it is also the moat

## E-162 - A product in this exact category died with its vendor, and the market did not
- tier: T1
- url: https://www.appliedopt.com/nouhin/
- verified: 2026-08-30
- says: the page for 「かんたん電子納品５」 now carries only a notice that the company has been
  dissolved and support has ended following the death of its representative. The product itself is
  gone; the ministry's delivery requirement is not
- justifies: OPEN-036
- note: a one-person software business in this space is a real precedent in both directions - it
  existed and sold, and it ended when its single person did

## E-163 - The Japanese CAE reporting product a competitor already built, and what it depends on
- tier: T1
- url: https://www.softflow.jp/postflow/
- verified: 2026-08-30
- says: POSTFLOW is a Windows report-authoring tool for CAE/CFD engineers - animation, graph output and
  automatic placement into a report. Its stated visualisation dependency is **ParaView 5.6** (ParaView
  is at 6.x). Editions are Lite (five slides, vendor watermark, no support) and full (unlimited slides,
  original templates, support, unlimited concurrent launches). Latest update recorded on the page:
  2024-12-06, version 2.1.0 to 2.2.0. No price is published
- justifies: XC-070, XC-072
- note: **the closest existing product to this one, in the same country, with the same buyer.** It is
  evidence that the need is real enough for somebody to have built for it, and its watermark-and-cap
  free edition is the same gating shape recorded in XC-255

## E-164 - The price a Japanese construction site actually pays, per person per month
- tier: T1
- url: https://www.kuraemon.com/plan/
- verified: 2026-08-30
- says: 蔵衛門クラウド is JPY 1,200 per person per month with no setup fee, no per-feature charges and
  up to two months free. Licences are sold in three-seat packs
- justifies: XC-071, OPEN-035
- note: recorded because it is the only price in this survey for a **self-serve, per-seat, monthly**
  product bought by the same kind of Japanese site organisation XC-035 targets. It is roughly
  JPY 14,400 per seat per year - two orders of magnitude below Tecplot and one below Origin, and it
  is what "an individual can adopt without procurement" costs in this market

---

## The three holes, as the evidence supports them

### Hole (1) - the vacated band

**Free ... then nothing published ... then USD 1,670–3,330 a year.** The category's incumbents price
where a department budget lives; the alternative is free and unusable by the intended user. Origin's
USD 495 shows the middle can carry a published price and a self-serve purchase - in a neighbouring
category, by a vendor who did not leave.

What sits in that gap is not a cheaper Tecplot. It is the buyer who cannot use ParaView and cannot
justify Tecplot, and today buys neither.

### Hole (3) - the specification set as the barrier

Roughly 350 Japanese delivery specifications (E-161), calibration and measurement rules under the
metrology law, and JIS-shaped quality records. **No global product fits these and none is trying.**
The vendors who do fit them sell enquiry-priced Windows desktop software, and one of them dissolved
(E-162).

This is the hole this product is structurally best placed for, because it is the one where the work is
"read the specification correctly and prove you did", which is the discipline the spec set already
enforces.

### Hole (4) - the market moved, the product did not

- POSTFLOW depends on **ParaView 5.6** while ParaView is at 6.x (E-163)
- CALS Manager is a **Windows desktop** application in a market whose sites work from phones
- The LIMS vendors sell on-premise systems by enquiry to buyers who now expect a price and a trial
- Tecplot's own list still leads with **perpetual licences and maintenance renewals**, a shape most
  software left a decade ago

None of these vendors has stopped selling. The market is alive; the product form is old.

---

## What this survey cannot settle

Which hole to enter. That needs one number this survey does not contain - **how many organisations are
in each** - and no primary source gives it (OPEN-036). The next step is not more desk research; it is
asking five of the people in one of these holes whether the pain is real, which is what XC-255's
reversal trigger already asks for.
