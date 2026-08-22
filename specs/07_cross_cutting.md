---
status: draft
updated: 2026-08-20
---

# Cross-cutting requirements

Nobody's feature, and therefore forgotten. Each is a requirement with acceptance criteria like any
other. For a product sold on trust, several of these are the product.

### XC-020 - Message and error catalogue
- statement: every user-visible message has a stable identifier that never changes once shipped, and
  the text is looked up by that identifier
- rationale: a support conversation quotes the identifier, not a translated sentence; and a message
  whose text is scattered through the code cannot be reviewed for the honesty this product depends on
- note: a message that reports a **failure or a refusal** additionally takes the shape of CT-010 - a
  reason code, what it happened to, what was missing, and whether anything changed. The identifier here
  is what the sentence is looked up by; the reason code is what a caller branches on, and they are not
  the same thing: one may be reworded in a translation, the other may never change meaning
- decidedness: Fixed
- basis: E-001 (T1)

### XC-021 - Localisation
- statement: the product is built for any locale from the first release - every user-visible string is
  looked up by the stable identifier of XC-020, and **adding a language is a data change, never a code
  change**. The catalogue shipped in the first release is Japanese and English; Simplified Chinese
  follows, then Traditional Chinese and Korean. An untranslated string falls back to English, visibly
  marked in development builds and never silently in released ones
- note: @Art style and report content carry the user's language, independent of the interface language
- decidedness: Fixed
- basis: E-001 (T1)

**Multi-language is a rendering problem before it is a translation problem**, and this product has two
places where that bites. Text drawn into the 3D view goes through the embedded toolkit's own text
rendering, which needs a font containing the glyphs - a Latin-only font silently produces blank boxes
for Chinese, Japanese and Korean. And an exported report is opened on a machine whose fonts are
unknown, so the glyphs have to travel with the document.

### XC-021b - Fonts travel with the deliverable
- statement: exported documents embed a subset of the font covering exactly the characters they
  contain, under a licence that permits embedding and redistribution; nothing relies on the recipient
  having a CJK font installed
- rationale: a report that renders as empty boxes on the recipient's machine fails at the only moment
  that matters. Subsetting keeps the cost proportional - a full CJK face is tens of megabytes, which
  would dominate the report budget of LIM-006
- note: the font licence is part of the notices file (XC-025), and the subset must not strip the
  licence obligation with the unused glyphs
- decidedness: Bounded

### XC-022 - Accessibility
- statement: keyboard operation for every command - to the scheme in [11_ui.md](11_ui.md), which is
  checked rather than asserted (XC-127) - focus order that follows reading order, and contrast that
  stays legible when a colour map is on screen
- note: colour maps are the accessibility problem in this domain - a result read by hue alone is
  unreadable to a large minority of engineers. Every colour-coded value is also available as a number
- note: what is **not** committed is stated in XC-114 rather than left to be inferred: screen-reader
  support is not claimed, because a 3D scene and a continuous field have no meaningful reading and a
  partial implementation would claim an accessibility the product does not have
- decidedness: Bounded

### XC-021c - Units a reader works in
- statement: interface language decides how a number is **formatted** (XC-110) and the @Display unit
  decides what unit it is **shown in** (XC-134); neither reaches storage, computation, or a
  machine-readable export, which states the unit it wrote
- rationale: these are three different things that all look like "units and numbers" and get conflated
  into one setting, at which point an export written in one locale means something else in another
- decidedness: Fixed
- basis: E-001 (T1)

### XC-023 - Audit log
- statement: every state change records what changed, by which command, from which origin (interface,
  assistant, external caller) and when; the log is local, readable by the user, and never leaves the
  machine on its own
- rationale: @Headless agent mode means changes can happen with nobody watching. A product that cannot
  say what an agent did to a workspace is not one an engineer can defend to a reviewer
- note: this is the **state-change** log. What leaves the machine is audited separately and to a
  stricter rule (XC-106, XC-126), because the question there is not what changed but what was sent
- decidedness: Fixed
- basis: E-001 (T1)

### XC-024 - Update and rollback
- statement: updates are user-initiated by default, state what changed, and can be declined
  indefinitely; the previous version stays installable
- rationale: an engineer mid-project does not want a silent update changing a rendering path between
  two figures in one report
- decidedness: Fixed
- basis: E-001 (T1)

### XC-025 - Third-party licence attribution
- statement: the product ships a complete list of its dependencies with their licences and required
  notices, viewable in the application and present as a file next to the executable
- note: the list is generated from the **actual build closure**, not by hand and not from a
  dependency's own install tree. A hand-maintained list is wrong within one release, and an
  upstream-provided one can be incomplete: VTK's install tree omits the MPL-2.0 text for a library it
  vendors, and its published wheel carries no third-party notices at all
- decidedness: Fixed
- basis: E-001 (T1), E-046 (T1), E-047 (T1)

### XC-026 - Security and data protection
- statement: no @Dataset, @Workspace or @Reference material content leaves the machine unless the user
  enables a network feature for that workspace and confirms what would be sent
- default: deny - every permission check returns false unless a rule grants access
- rationale: this is the reason the desktop build exists (XC-014). It is also the first question a
  corporate buyer asks, and the one they verify rather than believe
- decidedness: Fixed
- basis: E-001 (T1)

### XC-027 - Telemetry
- statement: there is no telemetry unless the user turns it on; when on, the product states what is
  collected and lets the user see the payload before it is sent
- decidedness: Fixed
- basis: E-001 (T1)

A product whose selling point is that data stays inside can afford no exception here. One background
request to a vendor endpoint, found by a customer's network team, ends the sale and the reference.

### XC-028 - Licence enforcement of our own product
- statement: a signed licence file verified locally, with an update-until date and no run expiry, a
  fingerprint recorded but not enforced, and a clock rollback that warns rather than blocks. **No
  licence check may block, discard or alter a computed result** (XC-039)
- rationale: an offline product cannot revoke anything, so enforcement buys little and costs the one
  thing that must not break - the customer's work on the day they change a machine
- decidedness: Fixed
- basis: E-057 (T1)

### XC-029 - Vulnerability response
- statement: dependencies are inventoried (XC-025), known vulnerabilities are checked on each release,
  and a contact route exists for reporting one
- note: a single-person vendor cannot promise a response time it cannot meet; what it can promise is
  an inventory, a check, and a route
- decidedness: Bounded
