## What changed, and why

<!-- One paragraph. Lead with the outcome. -->

## Specification

<!-- A spec change and the code it describes ship together, in one pull request (spec model 6.5).
     Delete the line that does not apply; do not delete both. -->

- Specification items touched: <!-- e.g. LIM-002, INV-011, view/REQ-013 -->
- No specification change: this touches no Fixed value, no contract and no acceptance criterion.

## Evidence

<!-- A number without a source is not a finding. For every figure this PR introduces or changes,
     say where it came from and when it was checked. Mark each as measured, estimated or assumed -
     all three are legitimate, presenting one as another is not. -->

| Value | Measured / estimated / assumed | Source | Date checked |
|---|---|---|---|
|  |  |  |  |

## Checks

- [ ] `python validate/check_specs.py` — 0 findings
- [ ] `python -m pytest tests` — passing, and no test skipped that CI will require
- [ ] every gate in `validate/` green (`.github/workflows/ci.yml` runs them all)
- [ ] `updated:` refreshed on every spec file touched
- [ ] a reversed decision is recorded in `specs/08_decisions.md` with the old one marked superseded,
      not deleted

## What this change does not do

<!-- What a reviewer might reasonably expect to be here and is not, and why. An empty section is a
     considered answer only if you write "nothing" in it. -->
