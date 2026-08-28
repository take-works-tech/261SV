# Skills in this repository, and where each came from

Vendored rather than referenced, so the environment is reproducible and a skill cannot change under
us between two screens of one product (the same reasoning as XC-024). Licences were read first-hand
on the date shown; upstream commit ids make a later diff cheap.

| Skill | Source | Commit | Licence | Verified |
|---|---|---|---|---|
| `frontend-design` | github.com/anthropics/skills `skills/frontend-design` | 3b3fad9 | Apache-2.0 (its own LICENSE.txt, read in full) | 2026-08-29 |
| `web-design-guidelines` | github.com/vercel-labs/agent-skills `skills/web-design-guidelines` | 063bee9 | MIT (repository README declaration) | 2026-08-29 |
| `react-best-practices` | github.com/vercel-labs/agent-skills `skills/react-best-practices` | 063bee9 | MIT (repository README + its own frontmatter) | 2026-08-29 |
| `composition-patterns` | github.com/vercel-labs/agent-skills `skills/composition-patterns` | 063bee9 | MIT (repository README declaration) | 2026-08-29 |
| `solvia-ui` | written here | - | project's | - |
| `spec-authoring` | written here | - | project's | - |

Update by re-cloning upstream and diffing against the commit above - never by editing the vendored
copy in place, which would be a fork nobody records.

## Order of authority

`solvia-ui` binds the generic skills to this product: tokens only, seven states, instrument-screen
rules, and an explicit adopt/reject map for `frontend-design`'s editorial advice. On any UI work,
load `solvia-ui` first. Where skills disagree, solvia-ui wins; where solvia-ui and the specs
disagree, the specs win - and say which, rather than proceeding (AGENTS.md).

These are development-time tools. Nothing here ships in the product, so XC-025's attribution file
does not list them; this README is their licence record instead.
