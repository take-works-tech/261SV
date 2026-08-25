"""The log this product writes about itself, and the bundle somebody may choose to send.

XC-126's reason is one measurement away from ordinary: automatic crash reporting produces better
diagnostics and sends a customer's part names to a third party without anybody deciding to. Every rule
tested here is a refusal to do that by accident.

The float rule is the interesting one. Names are strings, counts are integers (INV-015), and a value
measured from a dataset is a float - so refusing floats catches the shape a field value arrives in. It
does not catch a float somebody formatted into a string first, and the test says so rather than letting
the check look stronger than it is.

Verifies: operations/AC-007, AC-008, operations/TASK-011, TASK-012, XC-126, INV-015.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from service.egress.diagnostics import (
    ALLOWED_CONTEXT,
    DiagnosticsError,
    Item,
    Level,
    Log,
    Manifest,
    contents_for_egress,
    create,
    manifest_for,
)
from service.egress.gate import Gate, Outcome, Permission

WHEN = lambda: datetime(2026, 8, 25, 9, tzinfo=timezone(timedelta(hours=9)))  # noqa: E731


def a_log() -> Log:
    log = Log(clock=WHEN)
    log.record(Level.INFO, "dataset.load", case="Run 12", points=1127844, partial=False)
    return log


class TestALogLineCarriesNoFieldValue:
    def test_a_float_is_refused(self) -> None:
        """AC-007. A measured value is a float; names are strings and counts are integers."""
        log = Log(clock=WHEN)

        with pytest.raises(DiagnosticsError) as refusal:
            log.record(Level.INFO, "field.statistics", maximum=241.7)

        assert "XC-126" in str(refusal.value)

    def test_the_refusal_says_what_a_log_may_hold_instead(self) -> None:
        log = Log(clock=WHEN)

        with pytest.raises(DiagnosticsError) as refusal:
            log.record(Level.INFO, "field.statistics", maximum=241.7)

        assert "件数は整数" in str(refusal.value)

    def test_names_and_counts_are_allowed(self) -> None:
        line = a_log().lines()[0]

        assert line.context["case"] == "Run 12"
        assert line.context["points"] == 1127844

    def test_an_array_is_refused_too(self) -> None:
        """The other shape a field arrives in."""
        log = Log(clock=WHEN)

        with pytest.raises(DiagnosticsError):
            log.record(Level.INFO, "field.statistics", values=[1.0, 2.0])

    def test_what_may_be_in_a_line_is_written_down(self) -> None:
        assert float not in ALLOWED_CONTEXT
        assert str in ALLOWED_CONTEXT and int in ALLOWED_CONTEXT

    def test_a_float_formatted_into_a_string_is_not_caught_and_that_is_stated(self) -> None:
        """The check makes the accident hard and does not make the deliberate act impossible. Asserted
        so the limit is visible rather than discovered by somebody relying on it."""
        log = Log(clock=WHEN)

        log.record(Level.INFO, "field.statistics", maximum="241.7")

        assert "241.7" in log.as_text()

    def test_no_line_of_this_log_contains_a_value(self) -> None:
        """TASK-011's own condition, over the whole log rather than one line."""
        text = a_log().as_text()

        assert all(not part.replace(".", "").isdigit() or "." not in part
                   for part in text.split("=") if part)


class TestTheLogStaysLocal:
    def test_the_module_reaches_no_network(self) -> None:
        """XC-126: never sent anywhere on its own. Structural, because a module that imported a client
        could send it whatever it currently does."""
        from pathlib import Path

        import service.egress.diagnostics as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for client in ("requests", "httpx", "urllib", "socket"):
            assert client not in source

    def test_it_is_readable_as_text(self) -> None:
        assert "dataset.load" in a_log().as_text()

    def test_each_line_carries_when(self) -> None:
        assert "2026-08-25T00:00:00Z" in a_log().as_text()


class TestTheManifestExistsBeforeTheBundle:
    def test_it_lists_case_names_and_paths_individually(self) -> None:
        """AC-008. "3 files" is a number somebody accepts without reading; a customer's part name in the
        list is the thing they would have objected to, and they can only object to what they can see."""
        manifest = manifest_for(
            a_log(), workspace_id="workspace:001",
            case_names=["Run 12", "Run 13"], paths=["D:/studies/run12.vtu"], clock=WHEN,
        )

        assert manifest.case_names == ("Run 12", "Run 13")
        assert manifest.paths == ("D:/studies/run12.vtu",)
        assert "Run 12" in manifest.describe()
        assert "D:/studies/run12.vtu" in manifest.describe()

    def test_it_says_which_of_them_are_the_customers(self) -> None:
        manifest = manifest_for(a_log(), case_names=["Run 12"], clock=WHEN)

        assert "お客さまの情報です" in manifest.describe()

    def test_a_bundle_cannot_be_created_without_the_list_being_accepted(self) -> None:
        """`create` takes the manifest rather than the ingredients, so a bundle cannot exist without a
        list having been shown - one that reported its contents afterwards is one somebody found out
        about."""
        manifest = manifest_for(a_log(), clock=WHEN)

        with pytest.raises(DiagnosticsError) as refusal:
            create(manifest, accepted=False)

        assert "見たうえで作ります" in str(refusal.value)

    def test_accepting_it_creates_the_bundle(self) -> None:
        manifest = manifest_for(a_log(), workspace_id="workspace:001", clock=WHEN)

        bundle = create(manifest, accepted=True)

        assert bundle.manifest is manifest
        assert len(bundle.contents) == 2

    def test_an_empty_bundle_is_refused(self) -> None:
        with pytest.raises(DiagnosticsError):
            create(Manifest(()), accepted=True)

    def test_the_log_is_always_in_it_with_its_size(self) -> None:
        manifest = manifest_for(a_log(), clock=WHEN)

        assert manifest.items[0].kind == "log"
        assert "1 行" in manifest.items[0].describe()


class TestItLeavesOnlyThroughTheGate:
    def test_what_is_audited_is_what_the_user_accepted(self) -> None:
        """Two descriptions of one bundle is one description too many."""
        manifest = manifest_for(a_log(), case_names=["Run 12"], clock=WHEN)
        bundle = create(manifest, accepted=True)

        gate = Gate(clock=WHEN, send=lambda purpose, host, sent: None)
        gate.permit("workspace:001", Permission(hosts=frozenset({"support.example.test"})))

        found = gate.send_support_bundle(
            workspace_id="workspace:001", host="support.example.test",
            contents=contents_for_egress(bundle), consented=True,
        )

        assert found.outcome is Outcome.SENT
        assert "Run 12" in found.record.sent

    def test_without_consent_at_the_gate_it_still_does_not_go(self) -> None:
        """Two separate acceptances, and both are needed: one for what goes in the bundle, one for
        sending it. Accepting the manifest is not agreeing to send it anywhere."""
        bundle = create(manifest_for(a_log(), clock=WHEN), accepted=True)
        gate = Gate(clock=WHEN, send=lambda purpose, host, sent: None)

        found = gate.send_support_bundle(
            workspace_id="workspace:001", host="support.example.test",
            contents=contents_for_egress(bundle), consented=False,
        )

        assert found.outcome is Outcome.REFUSED

    def test_the_bundle_module_does_not_send_anything_itself(self) -> None:
        import service.egress.diagnostics as module

        assert not hasattr(module, "send")
        assert not any(name.startswith("send_") for name in dir(module))


class TestTheItemsAreReadable:
    def test_an_item_says_what_kind_of_thing_it_is(self) -> None:
        assert Item("case", "Run 12").describe() == "case：Run 12"

    def test_a_detail_appears_where_there_is_one(self) -> None:
        assert "12 行" in Item("log", "診断ログ", "12 行").describe()

    def test_an_empty_manifest_says_so_rather_than_being_blank(self) -> None:
        assert "何も含まれません" in Manifest(()).describe()
