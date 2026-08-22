# Changelog

Notable changes to the specification set, the gates and the environment. The product has not shipped a
release; entries before the first one describe what the repository can prove about itself.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project does not yet version
itself — `pyproject.toml` reads 0.0.1 and will until there is something to install.

## [Unreleased]

### Fixed

- **The declared VTK version disagreed with the pinned one.** `specs/06_external.md` declared
  `VTK 9.7.x` as a Fixed value while `pyproject.toml` pinned `vtk==9.5.2`, and every first-hand
  measurement behind LIM-002, LIM-004 and XC-049 was taken on 9.5.2. EXT-001 now declares the version
  the evidence describes; moving to 9.7.x is tracked as OPEN-019, because it is a re-measurement rather
  than a version bump.
- **LIM-004 compared two releases as though they were one artefact.** Its rationale set a 393.8 MB
  install measured on 9.5.2 beside an 80.4 MB download figure recorded for 9.7.0.
- **OPEN-008 described LIM-002 as unmeasured after E-063 measured it**, including the frame-distinctness
  problem it named as outstanding. Its `affects` list also omitted LIM-009 and LIM-012, both of which
  declare `open: OPEN-008`.
- **`05_limits.md` opened by claiming all limits are Fixed by definition**, contradicted by six of its
  thirteen entries. Replaced with what each of the three labels means for a limit.
- **`LIM-009`'s `unit:` slot held a paragraph of rationale** rather than a unit.
- **`numpy` shipped as a runtime dependency with no row in the dependency table**, so its licence, its
  adoption evidence and its support horizon had never been recorded. Its published wheel declares
  `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` (E-118).
- **`python -m pytest tests` did not run.** `tests/test_reader.py` imported `vtkmodules` at module
  scope, so on a machine without the engine environment the suite failed at collection and none of the
  other tests ran either — while `AGENTS.md` documented the command.
- **The mockup catalogue routed Settings to a `SettingsPropertyEditor` that was never defined**, which
  fails `tsc --noEmit` with `TS2304` and contradicts XC-165. The XC-003 statement that units are never
  inferred from a file was also missing from the Settings units category.
- **Both hooks were wired with paths relative to the shell's working directory.** One command run from
  a subdirectory left the shell there, the hook path stopped resolving, and Python's exit code 2 for a
  missing file is the same code that means *block this tool call* — so every edit and every command in
  the session was refused, including the repair. Anchored to `$CLAUDE_PROJECT_DIR`, with a test.

- **`--muted` named two roles at once.** Declared twice in one `:root` block — `#f1f4f6` for the
  shadcn light-background role, then `#6f7e88` for this project's grey body text. The second won, so
  every `bg-muted` rendered dark grey and nothing reported it. Split into `--muted` (background) and
  `--muted-ink` (text); the 106 existing uses resolve to the same pixels as before, and the one broken
  `bg-muted` is fixed. White was also written both `#fff` (95×) and `#ffffff` (5×); now one notation.

### Added

- Style tokens are now inside the single-source gate. `check_constant_duplication.py` reads CSS as
  well as source files, and its block walker tracks at-rule nesting — an earlier version reported a
  media-query override of `--area-tab-width` as a duplicate, which is correct CSS and a false finding.
  It states what it cannot judge: whether a literal *should* have been a token is a question about
  meaning (XC-187, OPEN-021).
- `validate/check_dependency_pins.py` — compares declared versions against the manifests that pin them,
  in both directions. Check 7 looks for `SYMBOL = literal` in source files, so a pin written
  `"vtk==9.5.2"` inside a TOML array was invisible to every gate here (XC-185).
- `.github/workflows/ci.yml` — replaces `specs.yml`, which ran the seven validators and **never ran the
  test suite**. Now runs the gates, the tests with skipping forbidden, and the mockup typecheck.
- `tests/conftest.py` — a skip on a laptop, a failure in CI, and the interpreter written into the report.
- `LICENSE.md` — FSL-1.1-MIT, decided in XC-082 on 2026-08-19 and until now not present in the
  repository at all.
- GitHub wiring: automated Claude review with a silent-success guard, `@claude` interaction, CODEOWNERS,
  pull-request and issue templates, Dependabot.
- `.claude/agents/code-reviewer-ci.md` — the defects this repository has actually shipped, by name.

- `.github/ruleset-main.json` — the branch ruleset, written and rejected by the plan rather than by a
  decision (OPEN-020). Applying it is one command on the day the account permits it.
- `.gitattributes` — LF everywhere, in the repository and the working tree. Several gates here compare
  literals, and a working tree that is CRLF on one machine makes those comparisons machine-dependent.

### Changed

- **This repository is no longer local-only** (XC-186). It publishes to one named private repository;
  every other remote is refused by name, and history rewriting stays refused.

### Known gaps

- **Branch protection is not in force** (OPEN-020). Measured 2026-08-22: both the rulesets API and the
  classic branch-protection API return HTTP 403 — "Upgrade to GitHub Pro or make this repository
  public" — for a private repository on a free personal account. CI runs on every push and pull request
  and reports honestly; it cannot block a merge. The pre-tool-use hook runs only inside an agent session
  on this machine and is silent in a plain terminal.
- **A pull request is judged by CI alone** (XC-188). `CLAUDE_CODE_OAUTH_TOKEN` is deferred, so the
  Claude review and `@claude` workflows no longer trigger on a pull request — they keep their prompts
  and guards and run only by hand. They were not given a skip-when-absent branch: that reports success
  for a review nobody received. Merging still depends on a person, because branch protection is
  unavailable (OPEN-020); what changed is that the three CI checks are now the only ones shown, and a
  red check again means something about the change.
