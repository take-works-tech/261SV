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

### Added

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

### Changed

- **This repository is no longer local-only** (XC-186). It publishes to one named private repository;
  every other remote is refused by name, and history rewriting stays refused.
