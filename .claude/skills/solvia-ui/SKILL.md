---
name: solvia-ui
description: The binding layer for ALL UI work in this repository - mockups, mockup 2, and the production interface. Load this BEFORE frontend-design, web-design-guidelines or any styling work. It constrains the generic design skills to this product's decided token system, component states and instrument-screen rules, and says which generic advice is rejected here and why.
---

# SOLVIA UI - what binds every screen in this repository

This product's claim is trustworthy numbers. A screen here is an **instrument**, not an editorial
page: the generic design skills in this directory push toward distinctiveness, and most of that push
is right for `home`, empty states and the download page, and wrong for any surface that shows a
measured value. This skill says where the line is. When it conflicts with a generic skill, **this
skill wins**; when it conflicts with the specs, **the specs win** - and say so rather than proceeding.

## Sources of truth (point, never copy)

One definition per value is a gate here (`check_constant_duplication.py`), and it applies to design
knowledge too. Do not restate these; read them:

- **Tokens**: `mockups/ui/app/globals.css` - two layers (XC-187): primitives (`--size-1..6`, raw
  colours) and semantic roles (`--text-body`, `--muted-ink`). A rule references the semantic name.
- **Components and layout**: `specs/11_ui.md` - 28 shared components, the shell grammar, required
  screen states, the keyboard scheme.
- **Areas, presets, transitions**: `specs/16_application_model.md` - the 20 editor kinds and what r1
  ships of each.
- **Design decisions already made**: `specs/08_decisions.md` - search the id before re-deciding
  anything (XC-187 tokens, XC-201 type, XC-191 table, XC-177 node editing, OPEN-021/OPEN-022 open).

## Hard rules (violations are defects, not style choices)

1. **No colour literal outside the token block.** Every `#hex` in a rule body is a defect being
   added to a measured pile (413 sites, OPEN-021). New colour = new token with a named role, in the
   token block, referenced by `var()`.
2. **No font-size outside the six-step scale.** The scale replaced twenty sizes, four of which sat
   within a pixel of each other (E-122). If a step is missing, that is a token-layer decision, not a
   local `px`.
3. **Numbers are `tabular-nums`, set once on the document.** Never per-table (it was forgotten at
   all but two sites when it was per-site - E-122).
4. **Every component ships seven states**: default, hover/focus-visible, disabled **with its reason**
   (an unexplained disabled control is indistinguishable from a bug), loading, empty (says what to do
   next), error (says what happened and how to fix it), truncated (with a way to read the full text).
   A component built with only its default state is not finished.
5. **Nothing may overflow silently.** Flex children get `min-width: 0` before text-overflow; grid
   columns that must shrink are `minmax(0, 1fr)`; wide content scrolls inside its own
   `overflow-x: auto` container. Buttons take no fixed width - the same label is 書き出し / Export /
   Exportieren als Bericht, and the third one decides.
6. **A missing value is a stated absence, never a blank cell** (XC-001). An undeclared unit shows the
   marker, never a guess (XC-003). Design the widths for those long strings first.
7. **UI text is Japanese**; identifiers, paths and spec ids keep their own form. No text is hardcoded
   in a way that blocks the message catalogue (XC-020) later.
8. **The deliverable preview uses `--family-deliverable`, never the UI face** (GL-013) - the
   recipient's document is not the tool's chrome, and blurring them makes the preview a lie.
9. **Mockups are design states, never evidence of implemented behaviour.** Whether a mockup may show
   a realistic number is OPEN-022 - still open; until it closes, numbers in mockups must be obviously
   illustrative and consistent with the invariants (units shown, provenance shown, no 13-digit
   float dumps).

## How to apply `frontend-design` here (the adopt/reject map)

The frontend-design skill is written for editorial surfaces. Split its advice:

| Its advice | Here |
|---|---|
| Distinctive typography, deliberate pairing | **Adopt** - in chrome, headings, `home`, empty states. Body/data faces stay `--family-ui`; digits stay tabular |
| Dominant colour + sharp accent | **Adopt** - as a token-layer redesign, never inline |
| Deliberate, few motions | **Adopt** - matches the existing 120ms menu animation; respect `prefers-reduced-motion` |
| Asymmetry, overlap, broken grids | **Reject for work areas** - a data-dense instrument reads on a grid; allowed only on `home` and marketing surfaces |
| Gradient meshes, noise textures | **Reject behind data** - nothing sits behind a viewport, a value table or a graph; permissible in `home` hero and empty-state illustrations |
| "The hero is a thesis" | **Reinterpret** - the product's thesis is a number with its unit, provenance and digits; show *that* confidently, not a marketing headline |
| Invented copy | **Reject** - UI text comes from the glossary's terms; a control says exactly what happens |

## Definition of done for any UI change

- `python validate/check_constant_duplication.py` passes (token uniqueness)
- `cd mockups/ui && npx tsc --noEmit && npx eslint .` pass
- The mockup catalogue (`lib/screen-catalog.json`) gains states for anything new, so
  `check_mockup_states.py` can sweep them
- No horizontal scroll on the page body at 100-200% zoom - check with the longest translation, not
  the shortest
- Dark theme: **do not invent one.** Its existence is an undecided question; raise it, don't ship it.
