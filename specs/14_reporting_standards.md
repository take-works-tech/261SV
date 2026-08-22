---
status: draft
updated: 2026-08-20
---

# What a generated report may say

The product writes commentary with a language model, so the standard the commentary must meet is
written here rather than left to a prompt. A prompt is a request; this is the contract the output is
checked against, and a sentence that fails it does not get published (XC-104).

The rules below are not a house style. They are what an engineering audience rejects a report for, taken
from the places that had to write the rejection down: a journal that refuses papers without an accuracy
estimate (E-068), the standards that separate verification from validation (E-069), the metrology
guidance on stating a result with its uncertainty (E-070), and the enumeration of language that makes a
claim unverifiable (E-071).

## The four questions every statement must survive

1. **What is the number?** With its unit, or with the undeclared marker - never a bare quantity
   (XC-003).
2. **How precise is it?** To the significant digits its storage supports, never further (INV-014).
3. **What is known about its error?** Stated, or explicitly stated to be unquantified. Silence is a
   claim of exactness.
4. **Where did it come from?** Read from data, computed here with the expression shown, taken from
   reference material with the document named, or stated by the user (INV-013).

A sentence that cannot answer all four is either rewritten or omitted. **Omission is the correct
outcome**, and it is not a failure of the feature: a report that says less and is entirely checkable is
worth more than one that reads well and contains one sentence nobody can trace.

## Language that is not permitted

Enumerated by category, because a list of banned words is a list somebody works around (E-071).

| Category | Examples | Why |
|---|---|---|
| superlatives | best, worst, optimal, maximum performance | a claim over a set nobody enumerated |
| subjective language | good agreement, acceptable, satisfactory, excellent | states the author's comfort, not a measurement |
| ambiguous adverbs and adjectives | significant, considerable, minimal, slight, roughly | a quantity that refuses to be one |
| unquantified comparatives | better than, higher than, improved | improved by how much, against what, within what error |
| loopholes | if possible, as appropriate, where necessary | a statement that cannot be false |
| emotional or promotional register | impressive, dramatic, alarming, promising | a report is read to decide something, not to feel something |
| false precision | "exactly", or fifteen digits from a single-precision field | precision is a claim; see INV-014 |
| anthropomorphism of the solver | the model wants, tries, struggles to converge | hides what actually happened |

**"Significant" is the one to watch.** It is the most common word in draft engineering commentary and it
has a real statistical meaning that the sentence almost never intends. Either a difference is stated
with its magnitude and uncertainty, or it is not stated.

### The replacement is always the same shape

Not *"the pressure drop improved significantly"* but *"the pressure drop fell from 1.24 kPa to
0.98 kPa, a reduction of 0.26 kPa (21 percent); the discretisation uncertainty of these values has not
been quantified."* The second is longer, and it is the only one of the two a reviewer can disagree with,
which is what makes it worth writing.

## Comparisons

A comparison is a computed result and is subject to every rule above.

- state the **magnitude and the direction**, both as an absolute difference and, where a denominator is
  meaningful, as a relative one - a percentage alone hides whether the change matters
- state **what it is relative to**, by name: which case, which run, which reference value
- a difference smaller than the stated uncertainty, or than the comparison tolerance (INV-016), is
  reported as **not distinguishable at this tolerance**, never as "the same" and never as a change
- values from cases of different mesh, solver settings or precision are comparable only with that
  difference stated; the report says so rather than quietly placing them in one column

## Uncertainty and numerical error

The habit this product enforces, transferred from measurement reporting (E-070) and from the archetypal
journal policy (E-068):

- a result carries **the uncertainty that is known**, with the coverage factor or interval stated, and
  if the confidence level differs from the conventional one it is stated explicitly
- where discretisation error has **not** been quantified - a single mesh, no refinement study - the
  report says exactly that. It does not say the result is converged, grid-independent, accurate, or
  validated
- **err on the side of too much information rather than too little**: an uncertainty component that was
  considered and judged negligible is worth a line saying so
- uncertainty is never inflated to be safe; a padded number is a wrong number with better manners

## Verification, validation and the words around them

These words have specific meanings in this field and a model will use them loosely, because everyday
English does not distinguish them (E-069).

| Term | Means | May be written only when |
|---|---|---|
| verification | the equations were solved correctly - a statement about numerics | a numerical error estimate exists |
| validation | the right equations were solved - a comparison against measurement | measured data is present, with its own uncertainty |
| converged | an iterative or discretisation criterion was met | the criterion and its value are stated |
| grid-independent | the result stopped changing with refinement | at least three refinement levels are present |
| accurate | within a stated bound | the bound is stated in the same sentence |

Validation is **not pass/fail**: it quantifies model error (E-069). A report may therefore state the
observed difference between computation and measurement; it may not state that a model "passed
validation" as though a threshold had been crossed, unless the user defined that threshold, in which
case the report names it.

## What a generated passage is allowed to be built from

The generation rule that makes the rest enforceable:

- every number in commentary is **taken from a computed result**, never produced by the model. A model
  cannot do arithmetic on a study and must not appear to (XC-097)
- every citation is **selected from documents the product retrieved and holds**, never composed. A model
  is not permitted to emit a reference; it chooses one, and the product renders it from what it has
  (XC-105)
- every statement is one of four kinds, and the kind is recorded with it: **value**, **computed
  comparison**, **cited from reference material**, or **stated by the user**
- where reference material and the data disagree, the report carries the data value and states the
  disagreement (XC-013)

## Structure of an engineering report

The shape a technical reader expects, offered as templates rather than imposed:

1. **what was analysed** - geometry, cases, what distinguishes them
2. **how** - solver, settings, mesh, and what was assumed
3. **what came out** - values with units, precision and provenance
4. **what it means** - comparisons, against the criteria the user stated
5. **what is not known** - the limitations section, which is not optional in a defensible report

The last section is the one that is always dropped and the one that makes the rest credible. A report
generated by this product **always contains it**, even if its content is a single sentence saying that
discretisation error was not quantified and no measured data was available.

## Templates

Shipped samples cover the common shapes: **journal-paper format** (abstract, method, results,
discussion, references), technical memorandum, one-page result summary, design-review deck, and a
comparison report across cases. They are **generic**: no customer's branding, no organisation's house
format, nothing that assumes a particular solver. A user's own format is an original in the library
(GL-019), and the sample is what it starts from.

Every shipped sample - template, material, font, background, colour map - must be redistributable under
terms this product can ship (XC-085). A sample that cannot be shipped is not a sample.

## What this is not

Not a claim that the product produces publishable research. It produces a document whose every statement
is traceable, which is the precondition for that, and refuses to produce the rest. The engineer remains
the author.
