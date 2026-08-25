"""Which renderer runs here, and why a substitution is refused rather than made.

XC-004's reason is not politeness. A substituted backend can change shading, tessellation and colour
interpolation, so a user who believes they are looking at one path is measuring something they did not
choose - and the product's answer is to name what failed, say what it needs, and **offer** an
alternative that the user accepts.

AC-005 asks that switching paths report identical values. The tests here check the half that can be
checked with one backend: that the interface has no method a backend could return a value from. The
golden comparison across two live backends is named in the task entry as what remains.

Verifies: view/AC-005, AC-006, view/TASK-004, part of TASK-005, XC-004, XC-087, INV-002.
"""

from __future__ import annotations

import inspect

import pytest

from engine.visualization.backends import (
    FOR_ROLE,
    MARKED,
    REQUIRES,
    Availability,
    Backend,
    Renderer,
    RendererError,
    Role,
    choose,
    for_role,
    probe,
    unavailable,
)

EVERYTHING = {backend: True for backend in Backend}
NOTHING = {backend: False for backend in Backend}


class TestThePathsAreTheOnesTheDecisionNames:
    def test_there_are_four(self) -> None:
        """XC-087's three plus the optional one. Closed: a fifth is a decision, not a registration."""
        assert {backend.value for backend in Backend} == {
            "webgl2", "nativeOffscreen", "webgpu", "omniverse"
        }

    def test_each_job_has_a_path_written_down(self) -> None:
        """The two main paths are a division of labour, not alternatives - so which one draws a report
        image is answered in one place rather than decided at each call site."""
        assert FOR_ROLE[Role.INTERACTIVE] is Backend.WEB_GL2
        assert FOR_ROLE[Role.ABOVE_BUDGET] is Backend.NATIVE_OFFSCREEN
        assert FOR_ROLE[Role.REPORT_IMAGE] is Backend.NATIVE_OFFSCREEN

    def test_every_path_states_what_it_requires(self) -> None:
        """"Unavailable" without a requirement is a message nobody can act on."""
        assert set(REQUIRES) == set(Backend)
        assert all(REQUIRES[backend] for backend in Backend)

    def test_the_two_paths_a_user_is_warned_about_are_marked(self) -> None:
        assert set(MARKED) == {Backend.WEBGPU, Backend.OMNIVERSE}
        assert "実験的" in Availability(Backend.WEBGPU, True).describe()


class TestNothingProbesOnItsOwnAuthority:
    def test_the_answers_are_handed_in(self) -> None:
        """Whether a WebGL2 context exists is a question about a browser. A module that guessed would
        report a capability nobody tested."""
        found = probe({Backend.NATIVE_OFFSCREEN: True})

        assert next(one for one in found if one.backend is Backend.NATIVE_OFFSCREEN).available

    def test_a_path_nobody_answered_for_is_unavailable_and_says_why(self) -> None:
        """Rather than absent from the list: a path missing from a list reads as a path that does not
        exist."""
        found = probe({Backend.NATIVE_OFFSCREEN: True})

        webgpu = next(one for one in found if one.backend is Backend.WEBGPU)
        assert webgpu.available is False
        assert "確認していません" in (webgpu.detail or "")

    def test_every_path_appears_in_the_result(self) -> None:
        assert len(probe({})) == len(Backend)

    def test_the_unavailable_ones_can_be_shown_together(self) -> None:
        """One refusal at a time is how somebody discovers three problems over three attempts."""
        assert len(unavailable(probe(NOTHING))) == len(Backend)


class TestAnUnavailablePathIsNamedAndNeverSubstituted:
    def test_the_requested_path_runs_when_it_can(self) -> None:
        chosen = choose(Backend.WEB_GL2, probe(EVERYTHING))

        assert chosen.ran_as_asked
        assert chosen.selected is Backend.WEB_GL2

    def test_a_refusal_names_the_path_and_what_it_needs(self) -> None:
        """AC-006."""
        chosen = choose(
            Backend.WEBGPU, probe({**NOTHING, Backend.NATIVE_OFFSCREEN: True})
        )

        assert chosen.selected is None
        assert "webgpu" in chosen.describe()
        assert "WebGPU アダプタ" in (chosen.reason or "")

    def test_the_alternative_is_offered_rather_than_selected(self) -> None:
        """`selected` stays None. A field holding the alternative as though it were the answer is how a
        silent substitution gets written by accident."""
        chosen = choose(
            Backend.WEBGPU, probe({**NOTHING, Backend.NATIVE_OFFSCREEN: True})
        )

        assert chosen.offered is Backend.NATIVE_OFFSCREEN
        assert chosen.selected is None
        assert chosen.ran_as_asked is False

    def test_the_offer_says_why_it_is_not_automatic(self) -> None:
        """XC-004's reason: a substituted backend changes shading, tessellation and colour
        interpolation, so the user would be measuring something they did not choose."""
        chosen = choose(
            Backend.WEBGPU, probe({**NOTHING, Backend.NATIVE_OFFSCREEN: True})
        )

        assert "陰影・分割・色の補間が変わる" in chosen.describe()

    def test_nothing_available_at_all_says_that_rather_than_offering_nothing_quietly(self) -> None:
        chosen = choose(Backend.WEB_GL2, probe(NOTHING))

        assert chosen.offered is None
        assert "黙って使うことはしません" in chosen.describe()

    def test_the_offer_follows_the_division_of_labour(self) -> None:
        """The interactive path first, then the native one: what is offered is the ordinary path for the
        ordinary job rather than whichever happened to be checked first."""
        chosen = choose(Backend.OMNIVERSE, probe({**EVERYTHING, Backend.OMNIVERSE: False}))

        assert chosen.offered is Backend.WEB_GL2

    def test_a_path_that_was_never_probed_cannot_be_chosen_either_way(self) -> None:
        """Not "unavailable", which is an answer. Nobody looked."""
        with pytest.raises(RendererError):
            choose(Backend.WEB_GL2, [Availability(Backend.NATIVE_OFFSCREEN, True)])

    def test_a_job_asks_for_its_own_path(self) -> None:
        chosen = for_role(Role.REPORT_IMAGE, probe({**NOTHING, Backend.WEB_GL2: True}))

        assert chosen.wanted is Backend.NATIVE_OFFSCREEN
        assert chosen.offered is Backend.WEB_GL2


class TestABackendCannotReturnANumber:
    def test_the_interface_offers_pixels_and_capabilities_and_nothing_else(self) -> None:
        """INV-002 as a property of the shape rather than a rule somebody remembers. Reported values
        come from MOD-004 on canonical data (INV-001), and there is no method here that could return
        one."""
        methods = {
            name for name, _ in inspect.getmembers(Renderer, inspect.isfunction)
            if not name.startswith("_")
        }

        assert methods == {"capabilities", "draw"}

    def test_drawing_returns_bytes(self) -> None:
        signature = inspect.signature(Renderer.draw)

        assert signature.return_annotation == "bytes"

    def test_the_module_computes_nothing_from_a_dataset(self) -> None:
        """A backend module that imported the analysis layer would be a place where a number could be
        produced beside the one that produces them."""
        from pathlib import Path

        import engine.visualization.backends as backends

        source = Path(backends.__file__).read_text(encoding="utf-8")
        assert "engine.analysis" not in source
        assert "domain_core.dataset" not in source
