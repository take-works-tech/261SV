---
status: draft
updated: 2026-08-19
---

# Product principles

Ordered. When two conflict, the earlier one wins. This is what a Bounded item is judged by: an
implementer choosing between two reasonable options resolves it here, not by preference.

### XC-010 - A correct number, before a picture of it
- statement: when numerical fidelity and visual quality conflict, fidelity wins, and the picture says
  what it is showing
- applies_when: interpolating cell values to points for smooth shading; tessellating high-order
  elements; decimating a mesh for interactive display; choosing a colour map that flatters a result
- decidedness: Fixed
- basis: E-001 (T1)

The product's whole claim is that an engineer can put its output in front of a customer. A visual
that quietly averages away a stress peak destroys that claim in a way no feature recovers.

### XC-011 - Failing loudly, before showing something plausible
- statement: when a value cannot be computed or a unit is unknown, the product says so; it never
  substitutes a default that looks like a measurement
- applies_when: missing fields, unreadable time steps, unit not declared, a diff between incompatible
  meshes, a renderer that cannot run on this machine
- decidedness: Fixed
- basis: E-001 (T1)

### XC-012 - Reproducibility, before convenience
- statement: anything the user sees must be reconstructible from the saved @Workspace, and a change
  that cannot be saved is not offered
- applies_when: camera positions, colour scales, graph data selection, report layout, art style
- decidedness: Fixed
- basis: E-001 (T1)

A screenshot nobody can regenerate six months later is the state this product exists to replace.

### XC-013 - Measured data, before documents
- statement: values read from a @Dataset always outrank values found in @Reference material, and any
  number the assistant states carries where it came from
- applies_when: commentary written with language-model assistance; retrieval over user documents;
  answers in chat
- decidedness: Fixed
- basis: E-001 (T1)

The reference document may describe a different run. Treating it as authoritative is how a wrong
number reaches a customer with a citation attached, which is worse than no citation at all.

### XC-014 - Working offline, before working everywhere
- statement: the desktop product completes its core work with no network at all; anything requiring a
  network is optional, visible, and refusable
- applies_when: language-model features, updates, telemetry, licence checks, asset downloads
- decidedness: Fixed
- basis: E-001 (T1)

The buyers who care most about this product are the ones who cannot send geometry outside their
network. A feature that silently phones home disqualifies the product in that room.

### XC-015 - One implementation of a concept, before speed of adding the next one
- statement: a concept that exists in two work areas has one implementation and one definition
- applies_when: colour maps shared between view and graph; art style across report and image export;
  the case tree in every area; unit formatting everywhere
- decidedness: Fixed
- basis: E-001 (T1)

**Order matters and is deliberate.** Correctness outranks honesty about failure only because a correct
number needs no apology; honesty outranks reproducibility because a reproducible wrong answer is still
wrong; and all of them outrank speed of delivery, which is not on this list at all.
