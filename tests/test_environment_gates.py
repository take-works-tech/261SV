"""The environment gates must be able to fail.

They guard things with no symptom: a constant quietly defined twice, an instruction layer that grew
without anyone charging it, a check nobody invokes, a push to a repository nobody chose. Each of those
is invisible until it is expensive, which is exactly why the gates need tests that break the project on
purpose.

Specification: none of these is a product requirement - they guard how this repository is worked on,
not what the product does. That is why they live in `validate/` and `.claude/hooks/` beside the spec
gates rather than in `src/`.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GUARD = ROOT / ".claude" / "hooks" / "local_only_guard.py"


def run(gate: str, cwd: pathlib.Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(cwd / "validate" / gate)], cwd=cwd, capture_output=True, text=True
    )


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    """A copy carrying only what the gates read, so a test may break it safely."""
    (tmp_path / "validate").mkdir()
    for gate in ("check_constant_duplication.py", "check_context_budget.py", "check_gates_wired.py"):
        shutil.copy2(ROOT / "validate" / gate, tmp_path / "validate" / gate)
    (tmp_path / ".claude" / "output-styles").mkdir(parents=True)
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# probe\n\nShort.\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
        "\n".join(
            f"      - run: python validate/{gate}"
            for gate in ("check_constant_duplication.py", "check_context_budget.py", "check_gates_wired.py")
        )
        + "\n",
        encoding="utf-8",
    )
    return tmp_path


class TestConstantDuplication:
    def test_this_repository_is_clean(self) -> None:
        result = run("check_constant_duplication.py")
        assert result.returncode == 0, result.stdout

    def test_the_same_constant_twice_fails(self, project: pathlib.Path) -> None:
        (project / "src").mkdir()
        (project / "src" / "a.py").write_text("MAX_CASES = 500\n", encoding="utf-8")
        (project / "src" / "b.py").write_text("MAX_CASES = 500\n", encoding="utf-8")
        result = run("check_constant_duplication.py", project)
        assert result.returncode == 1
        assert "MAX_CASES" in result.stdout

    def test_disagreeing_values_are_named_as_a_contradiction(self, project: pathlib.Path) -> None:
        (project / "src").mkdir()
        (project / "src" / "a.py").write_text("MAX_CASES = 500\n", encoding="utf-8")
        (project / "src" / "b.py").write_text("MAX_CASES = 900\n", encoding="utf-8")
        result = run("check_constant_duplication.py", project)
        assert result.returncode == 1
        assert "Contradicting" in result.stdout

    def write_css(self, project: pathlib.Path, body: str) -> None:
        (project / "app").mkdir(exist_ok=True)
        (project / "app" / "styles.css").write_text(body, encoding="utf-8")

    def test_one_name_holding_two_roles_fails(self, project: pathlib.Path) -> None:
        """The defect this half was written for: `--muted` was a background and a text colour."""
        self.write_css(project, ":root { --muted: #f1f4f6; --muted: #6f7e88; }\n")
        result = run("check_constant_duplication.py", project)
        assert result.returncode == 1
        assert "--muted" in result.stdout
        assert "the last one wins" in result.stdout

    def test_a_responsive_override_is_not_a_duplicate(self, project: pathlib.Path) -> None:
        """A media query redeclaring a token is correct, and an earlier version of this gate said it
        was not. The false finding is the reason the block walker tracks nesting."""
        self.write_css(
            project,
            ".tabs { --tab-width: 112px; }\n"
            "@media (max-width: 900px) { .tabs { --tab-width: 96px; } }\n"
            "@media (max-width: 600px) { .tabs { --tab-width: 38px; } }\n",
        )
        assert run("check_constant_duplication.py", project).returncode == 0

    def test_two_spellings_of_one_colour_fail(self, project: pathlib.Path) -> None:
        self.write_css(project, ".a { color: #fff; }\n.b { color: #ffffff; }\n")
        result = run("check_constant_duplication.py", project)
        assert result.returncode == 1
        assert "#ffffff" in result.stdout

    def test_one_spelling_passes(self, project: pathlib.Path) -> None:
        self.write_css(project, ".a { color: #ffffff; }\n.b { color: #ffffff; }\n")
        assert run("check_constant_duplication.py", project).returncode == 0

    def test_different_colours_are_not_spellings_of_each_other(self, project: pathlib.Path) -> None:
        self.write_css(project, ".a { color: #ffffff; }\n.b { color: #fefefe; }\n")
        assert run("check_constant_duplication.py", project).returncode == 0

    def test_it_states_what_it_did_not_check(self) -> None:
        assert "NOT checked" in run("check_constant_duplication.py").stdout

    def test_generated_next_output_and_archive_are_not_source_definitions(self, project: pathlib.Path) -> None:
        for relative in ("mockups/ui/.next/server/chunk.js", "archive/legacy/src/old.js"):
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("const GENERATED_LIMIT = 12\n", encoding="utf-8")
        result = run("check_constant_duplication.py", project)
        assert result.returncode == 0, result.stdout


class TestContextBudget:
    def test_this_repository_is_within_budget(self) -> None:
        result = run("check_context_budget.py")
        assert result.returncode == 0, result.stdout + result.stderr

    def test_an_imported_file_is_charged(self, project: pathlib.Path) -> None:
        """`CLAUDE.md` is one line here; the tokens are all in what it imports."""
        (project / "AGENTS.md").write_text("# probe\n\n" + ("word " * 400), encoding="utf-8")
        result = run("check_context_budget.py", project)
        assert "AGENTS.md" in result.stdout
        charged = [line for line in result.stdout.splitlines() if line.strip().endswith("AGENTS.md")]
        assert charged and int(charged[0].split()[0]) > 100

    def test_growth_fails(self, project: pathlib.Path) -> None:
        rules = project / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "bloat.md").write_text("# Bloat\n\n" + ("word " * 40000), encoding="utf-8")
        result = run("check_context_budget.py", project)
        assert result.returncode == 1
        assert "always-injected" in result.stderr

    def test_path_scoping_is_bounded_too(self, project: pathlib.Path) -> None:
        rules = project / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "bloat.md").write_text(
            '---\npaths:\n  - "**/*.py"\n---\n\n' + ("word " * 40000), encoding="utf-8"
        )
        result = run("check_context_budget.py", project)
        assert result.returncode == 1
        assert "path-scoped" in result.stderr


class TestGatesWired:
    def test_every_validator_here_is_invoked(self) -> None:
        result = run("check_gates_wired.py")
        assert result.returncode == 0, result.stdout

    def test_an_unwired_validator_is_reported(self, project: pathlib.Path) -> None:
        (project / "validate" / "check_orphan.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        result = run("check_gates_wired.py", project)
        assert result.returncode == 1
        assert "check_orphan.py" in result.stdout

    def test_with_no_runner_it_says_it_checked_nothing(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "validate").mkdir()
        shutil.copy2(ROOT / "validate" / "check_gates_wired.py", tmp_path / "validate")
        result = run("check_gates_wired.py", tmp_path)
        assert result.returncode == 0
        assert "NOT checked" in result.stdout


class TestDependencyPins:
    """XC-185. Check 7 sees `SYMBOL = literal` in source files; a pin in a manifest is invisible to it.

    The project carried `version: VTK 9.7.x` against a `vtk==9.5.2` pin for long enough that three
    measured values were taken on the version the specification did not name.
    """

    @pytest.fixture
    def pinned(self, tmp_path: pathlib.Path) -> pathlib.Path:
        """A project holding only what this gate reads."""
        (tmp_path / "validate").mkdir()
        shutil.copy2(ROOT / "validate" / "check_dependency_pins.py", tmp_path / "validate")
        (tmp_path / "specs").mkdir()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "probe"\ndependencies = ["vtk==9.5.2"]\n', encoding="utf-8"
        )
        (tmp_path / "specs" / "09_technology.md").write_text(
            "| Dependency | Purpose | Licence | Adoption evidence | Support horizon | Alternative rejected |\n"
            "|---|---|---|---|---|---|\n"
            "| VTK | readers | BSD-3 | ParaView | Kitware | - |\n",
            encoding="utf-8",
        )
        return tmp_path

    def write_external(self, project: pathlib.Path, version: str) -> None:
        (project / "specs" / "06_external.md").write_text(
            f"### EXT-001 - VTK\n- version: {version}\n- pinned_in: pyproject.toml#vtk\n",
            encoding="utf-8",
        )

    def test_this_repository_agrees_with_its_manifest(self) -> None:
        result = run("check_dependency_pins.py")
        assert result.returncode == 0, result.stdout

    def test_a_disagreeing_version_fails(self, pinned: pathlib.Path) -> None:
        self.write_external(pinned, "9.7.0")
        result = run("check_dependency_pins.py", pinned)
        assert result.returncode == 1
        assert "9.7.0" in result.stdout and "9.5.2" in result.stdout

    def test_an_agreeing_version_passes(self, pinned: pathlib.Path) -> None:
        self.write_external(pinned, "9.5.2")
        assert run("check_dependency_pins.py", pinned).returncode == 0

    def test_a_runtime_dependency_with_no_row_fails(self, pinned: pathlib.Path) -> None:
        """The defect this gate was written for: numpy shipped with no licence question ever asked."""
        self.write_external(pinned, "9.5.2")
        (pinned / "pyproject.toml").write_text(
            '[project]\nname = "probe"\ndependencies = ["vtk==9.5.2", "numpy==2.3.4"]\n', encoding="utf-8"
        )
        result = run("check_dependency_pins.py", pinned)
        assert result.returncode == 1
        assert "numpy" in result.stdout

    def test_a_claim_against_a_package_the_manifest_does_not_require_fails(self, pinned: pathlib.Path) -> None:
        (pinned / "specs" / "06_external.md").write_text(
            "### EXT-099 - Absent\n- version: 1.0.0\n- pinned_in: pyproject.toml#nothing-here\n",
            encoding="utf-8",
        )
        result = run("check_dependency_pins.py", pinned)
        assert result.returncode == 1
        assert "nothing-here" in result.stdout

    def test_it_always_states_what_it_did_not_check(self) -> None:
        assert "NOT checked" in run("check_dependency_pins.py").stdout


ZERO = "0" * 40
PRE_PUSH = ROOT / ".githooks" / "pre-push"


class TestPrePushHook:
    """The only guard that runs in a plain terminal.

    `.claude/hooks/local_only_guard.py` refuses a force-push inside an agent session and is silent
    everywhere else, and GitHub refuses nothing at all on this plan (OPEN-020). A `git push --force`
    typed from muscle memory meets neither. This hook is what stands there instead - client-side, and
    skippable with `--no-verify`, which is the honest limit of it.
    """

    @pytest.fixture(autouse=True)
    def _needs_sh(self) -> None:
        if shutil.which("sh") is None:
            pytest.skip("no POSIX shell on PATH, so the pre-push hook could not be exercised")

    def push(self, local: str, remote: str, cwd: pathlib.Path = ROOT) -> subprocess.CompletedProcess[str]:
        """Drive the hook the way git drives it: refspec lines on stdin, remote name in argv."""
        return subprocess.run(
            ["sh", str(PRE_PUSH), "origin", "https://example.invalid/repo.git"],
            input=f"refs/heads/main {local} refs/heads/main {remote}\n",
            capture_output=True,
            text=True,
            cwd=cwd,
        )

    def head(self, offset: int = 0) -> str:
        ref = "HEAD" if offset == 0 else f"HEAD~{offset}"
        return subprocess.run(
            ["git", "rev-parse", ref], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()

    def test_a_fast_forward_with_green_gates_is_allowed(self) -> None:
        result = self.push(self.head(), self.head(1))
        assert result.returncode == 0, result.stderr

    def test_rewriting_published_history_is_refused(self) -> None:
        result = self.push(self.head(1), self.head())
        assert result.returncode == 1
        assert "would not fast-forward" in result.stderr

    def test_deleting_a_branch_by_push_is_refused(self) -> None:
        result = self.push(ZERO, self.head())
        assert result.returncode == 1
        assert "deleting" in result.stderr

    def test_a_new_branch_is_allowed(self) -> None:
        """A first push has no remote side to fast-forward from, and must not be read as a rewrite."""
        result = self.push(self.head(), ZERO)
        assert result.returncode == 0, result.stderr

    def test_a_red_gate_refuses_the_push(self, tmp_path: pathlib.Path) -> None:
        """Proven by breaking a gate, not by trusting the branch that reads its exit code."""
        shutil.copytree(ROOT / ".githooks", tmp_path / ".githooks")
        (tmp_path / "validate").mkdir()
        (tmp_path / "validate" / "check_always_red.py").write_text(
            "print('this gate is deliberately red')\nraise SystemExit(1)\n", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
        # A new branch: no remote side, so the history checks pass and the gates are what decide.
        result = self.push("a" * 40, ZERO, cwd=tmp_path)
        assert result.returncode == 1
        assert "check_always_red.py" in result.stderr
        assert "the repository gates are red" in result.stderr

    def test_a_missing_interpreter_says_so_rather_than_refusing(self, tmp_path: pathlib.Path) -> None:
        """On Windows `python3` is a Store stub that resolves, prints and exits non-zero. Taking the
        first name on PATH made every gate look red for a reason unrelated to the change - which is
        how a hook teaches people to reach for --no-verify. Found by running it, not by reading it."""
        shutil.copytree(ROOT / ".githooks", tmp_path / ".githooks")
        (tmp_path / "validate").mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
        stub = tmp_path / "bin"
        stub.mkdir()
        for name in ("python", "python3", "py"):
            (stub / name).write_text("#!/bin/sh\necho 'Python was not found' >&2\nexit 9009\n", encoding="utf-8")
            (stub / name).chmod(0o755)
        # The stub directory goes in front of the real PATH, not instead of it: the hook needs `git`
        # and `tr` to get as far as choosing an interpreter at all.
        environment = dict(os.environ, PATH=os.pathsep.join([str(stub), os.environ.get("PATH", "")]))
        result = subprocess.run(
            ["sh", str(tmp_path / ".githooks" / "pre-push"), "origin"],
            input=f"refs/heads/main {'a' * 40} refs/heads/main {ZERO}\n",
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=environment,
        )
        assert result.returncode == 0
        assert "NOT checked" in result.stderr

    def test_the_repository_points_git_at_the_versioned_hooks(self) -> None:
        """A working-copy setting, so CI legitimately does not have it - and never pushes anyway.

        This is a skip that is defensible where the reader tests' skip is not: there the thing under
        test is the product, and CI forbids the skip with SIM_VIEWER_REQUIRE_VTK. Here the thing under
        test is one developer's clone, which a fresh checkout on a runner is not.
        """
        if os.environ.get("CI"):
            pytest.skip("a fresh CI checkout has no local git config, and CI does not push")
        configured = subprocess.run(
            ["git", "config", "core.hooksPath"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        assert configured == ".githooks", (
            "run `git config core.hooksPath .githooks` - the hook is versioned so it travels with the "
            "repository, but git will not use it until each clone is pointed at it"
        )


def guard(tool: str, **tool_input: str) -> subprocess.CompletedProcess[str]:
    """Drive the PreToolUse guard the way the harness drives it: one JSON payload on stdin."""
    return subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps({"tool_name": tool, "tool_input": tool_input}),
        capture_output=True,
        text=True,
    )


class TestLocalOnlyGuard:
    """XC-181 authorised one remote. The guard exists so that "one" is enforced rather than intended.

    The forbidden command strings are assembled from fragments here on purpose: written whole, they
    would appear in the `command` field of the tool call that runs this test, and the guard would
    refuse to let its own test suite start.
    """

    def test_an_edit_inside_the_project_is_allowed(self) -> None:
        assert guard("Write", file_path=str(ROOT / "specs" / "README.md")).returncode == 0

    def test_an_edit_outside_the_project_is_refused(self, tmp_path: pathlib.Path) -> None:
        result = guard("Write", file_path=str(tmp_path / "elsewhere.md"))
        assert result.returncode == 2
        assert "outside this project" in result.stderr

    def test_an_ordinary_command_is_allowed(self) -> None:
        assert guard("Bash", command="python -m pytest tests").returncode == 0

    def test_a_push_to_the_authorised_remote_is_allowed(self) -> None:
        assert guard("Bash", command="git push -u origin main").returncode == 0
        assert (
            guard(
                "Bash",
                command="git remote add origin "
                "https://github.com/take-works-tech/202604-sim-analysis-visualization.git",
            ).returncode
            == 0
        )

    def test_a_push_to_another_repository_is_refused(self) -> None:
        result = guard(
            "Bash", command="git remote add backup https://github.com/someone-else/product-plans.git"
        )
        assert result.returncode == 2
        assert "someone-else/product-plans" in result.stderr

    def test_creating_a_repository_elsewhere_is_refused(self) -> None:
        result = guard("Bash", command="gh repo cre" + "ate other-org/leak --public")
        assert result.returncode == 2
        assert "other-org/leak" in result.stderr

    @pytest.mark.parametrize(
        "command",
        [
            "git push --fo" + "rce origin main",
            "git push " + "-f origin main",
            "git re" + "set --hard HEAD~3",
            "git filter-" + "branch --tree-filter true HEAD",
            "gh repo dele" + "te take-works-tech/202604-sim-analysis-visualization",
        ],
    )
    def test_history_destroying_commands_are_refused(self, command: str) -> None:
        result = guard("Bash", command=command)
        assert result.returncode == 2, command
        assert result.stderr.startswith("refused:")

    def test_a_malformed_payload_does_not_block_the_session(self) -> None:
        """A guard that cannot read its input lets the turn continue; it does not stop the session."""
        result = subprocess.run(
            [sys.executable, str(GUARD)], input="not json", capture_output=True, text=True
        )
        assert result.returncode == 0

    def test_the_settings_file_invokes_the_guard_by_an_absolute_path(self) -> None:
        """A cwd-relative hook path is a session-wide denial of service, and it happened once.

        One command run from a subdirectory left the shell there; the hook path stopped resolving;
        Python's exit code 2 for a missing file is the same code that means *block this tool call*.
        Every edit and every command in the session was refused, including the repair.
        """
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        commands = [
            hook["command"]
            for event in settings["hooks"].values()
            for matcher in event
            for hook in matcher["hooks"]
        ]
        assert commands, "no hooks are wired at all"
        for command in commands:
            assert "$CLAUDE_PROJECT_DIR" in command, command
