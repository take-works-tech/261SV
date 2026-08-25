"""Running without a person, and what a run leaves on the disk.

E-065 is the argument for the default: the application this rule is modelled on shipped the permissive
one first and had to retrofit the preference. A permissive default cannot be made stricter without
breaking somebody's automation, so it is never actually changed - which makes getting it right the first
time the whole of the work.

AC-041's reason is one sentence: undo restores the workspace and not the disk. A run that wrote forty
reports and was then undone leaves forty reports, and the user's undo was for the workspace.

Verifies: pipeline/AC-038, AC-041, pipeline/TASK-038, TASK-041, XC-102, XC-061, E-065.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from service.scripting.authorisation import (
    Artefact,
    AuthorisationError,
    Unattended,
    Written,
    may_run,
    written_from,
)


class TestUnattendedIsOffByDefault:
    def test_a_fresh_workspace_refuses(self) -> None:
        """AC-038. The default value of the field is the refusal, not a convention applied elsewhere."""
        refusal = may_run(None, a_person_is_authorising=False)

        assert refusal is not None
        assert "既定は無効" in refusal

    def test_the_default_of_the_setting_itself_is_off(self) -> None:
        """A setting whose permissive value is what you get by forgetting is a permissive setting."""
        assert Unattended().enabled is False

    def test_a_person_pressing_run_needs_no_setting(self) -> None:
        """The setting is about running **without** a person, not about running at all."""
        assert may_run(None, a_person_is_authorising=True) is None

    def test_enabling_it_lets_a_script_run_unattended(self) -> None:
        setting = Unattended(enabled=True, granted_by="品質保証部 田中")

        assert may_run(setting, a_person_is_authorising=False) is None

    def test_enabling_it_without_saying_who_is_refused(self) -> None:
        """A permission with no record of being granted is one nobody can be asked about."""
        with pytest.raises(AuthorisationError) as refusal:
            Unattended(enabled=True)

        assert "誰が許可したか" in str(refusal.value)

    def test_the_refusal_says_both_ways_out(self) -> None:
        """A refusal that names no way forward is one somebody works around."""
        refusal = may_run(None, a_person_is_authorising=False) or ""

        assert "人が実行を指示する" in refusal
        assert "ワークスペースごとの設定" in refusal


class TestARunOffersToDeleteWhatItWrote:
    def test_it_names_the_files(self, tmp_path: Path) -> None:
        """AC-041: naming them, because a count is something somebody accepts without reading."""
        written = Written()
        written.note(Artefact(tmp_path / "report-001.html", "unit:report", "case:001"))

        assert "report-001.html" in written.describe()
        assert "unit:report / case:001" in written.describe()

    def test_it_says_why_the_offer_exists(self, tmp_path: Path) -> None:
        written = Written()
        written.note(Artefact(tmp_path / "report-001.html", "unit:report"))

        assert "ディスクは戻しません" in written.describe()

    def test_a_run_that_wrote_nothing_says_so(self) -> None:
        assert "書き出していません" in Written().describe()

    def test_deleting_removes_them(self, tmp_path: Path) -> None:
        path = tmp_path / "report-001.html"
        path.write_text("x", encoding="utf-8")
        written = Written()
        written.note(Artefact(path, "unit:report"))

        removed = written.delete(accepted=True)

        assert removed == (path,)
        assert not path.exists()

    def test_nothing_is_deleted_without_the_list_being_accepted(self, tmp_path: Path) -> None:
        path = tmp_path / "report-001.html"
        path.write_text("x", encoding="utf-8")
        written = Written()
        written.note(Artefact(path, "unit:report"))

        with pytest.raises(AuthorisationError):
            written.delete(accepted=False)

        assert path.exists()

    def test_it_deletes_only_what_this_run_wrote(self, tmp_path: Path) -> None:
        """A file that was there before is not this run's to remove, and a deletion routine that took a
        path on trust is one that eventually takes the wrong one."""
        mine = tmp_path / "report-001.html"
        mine.write_text("x", encoding="utf-8")
        somebody_elses = tmp_path / "notes.docx"
        somebody_elses.write_text("x", encoding="utf-8")
        written = Written()
        written.note(Artefact(mine, "unit:report"))

        with pytest.raises(AuthorisationError) as refusal:
            written.delete(accepted=True, only=[somebody_elses])

        assert "notes.docx" in str(refusal.value)
        assert somebody_elses.exists()

    def test_deleting_a_subset_leaves_the_rest_offered(self, tmp_path: Path) -> None:
        first, second = tmp_path / "a.html", tmp_path / "b.html"
        for path in (first, second):
            path.write_text("x", encoding="utf-8")
        written = Written()
        written.note(Artefact(first, "unit:report"))
        written.note(Artefact(second, "unit:report"))

        written.delete(accepted=True, only=[first])

        assert [one.path for one in written.artefacts] == [second]

    def test_a_file_already_gone_is_reported_as_removed(self, tmp_path: Path) -> None:
        """The outcome the user asked for is that it is not there, and it is not there."""
        path = tmp_path / "report-001.html"
        written = Written()
        written.note(Artefact(path, "unit:report"))

        assert written.delete(accepted=True) == (path,)


class TestTheListComesFromTheRunRecord:
    def test_it_is_what_the_run_said_it_wrote(self) -> None:
        """Rather than a second list assembled afterwards, which might include a file somebody else
        made."""
        from service.pipeline.document import (
            DefinitionRef,
            Kind,
            Source,
            add,
            add_cases_unit,
            artefact_unit,
        )
        from service.pipeline.run import run

        document = {"id": "pipeline:001", "units": []}
        add(document, add_cases_unit("unit:cases", ["case:001", "case:002"]))
        add(
            document,
            artefact_unit("unit:view", Kind.VIEW, DefinitionRef(Source.WORKSPACE_ITEM, "v", 1)),
        )
        record = run(document, cases=["case:001", "case:002"])

        written = written_from(record)

        assert [one.path.name for one in written.artefacts] == ["case:001", "case:002"]
        assert all(one.unit_id == "unit:view" for one in written.artefacts)

    def test_a_run_that_wrote_nothing_offers_nothing(self) -> None:
        class Empty:
            written: list[str] = []

        assert written_from(Empty()).artefacts == []
