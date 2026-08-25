"""Whether a script may run without a person, and what a run leaves on the disk afterwards.

**Unattended execution is off by default and is enabled per workspace** (XC-102, AC-038). The
application this rule is modelled on shipped the permissive default first and had to retrofit the
preference (E-065), which is the cheapest possible argument for getting the default right the first
time: a permissive default cannot be made stricter without breaking somebody's automation, so it is
never actually changed.

**A run offers to delete what it wrote** (AC-041). Undo restores the @Workspace and not the disk
(XC-061) - a run that wrote forty reports and was then undone leaves forty reports, and the user's undo
was for the workspace. So the run record lists its artefacts by name and can remove them, and it removes
**only what that run wrote**: a file that was there before is not this run's to delete.

Specification: XC-102, XC-061, pipeline/AC-038, AC-041, E-065.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Iterable


class AuthorisationError(Exception):
    """Raised where a script would run with nobody having said it may."""


@dataclass(frozen=True, slots=True)
class Unattended:
    """Whether this @Workspace lets a script run with nobody watching.

    `False` is the default value of the field, not a convention applied elsewhere. A setting whose
    permissive value is what you get by forgetting is a setting that is permissive.
    """

    enabled: bool = False
    #: Who turned it on and when, in their own words. A permission with no record of being granted is
    #: one nobody can be asked about.
    granted_by: str | None = None

    def __post_init__(self) -> None:
        if self.enabled and not self.granted_by:
            raise AuthorisationError(
                "無人実行を有効にするには、誰が許可したかが要ります。"
                "誰が与えたか分からない権限は、誰にも問えない権限です"
            )


def may_run(
    setting: Unattended | None, *, a_person_is_authorising: bool
) -> str | None:
    """Why this script may not run, or None (AC-038).

    `a_person_is_authorising` is somebody pressing run. With that, a script runs whatever the setting
    says - the setting is about running **without** a person, not about running at all.
    """
    if a_person_is_authorising:
        return None
    held = setting or Unattended()
    if not held.enabled:
        return (
            "このワークスペースでは無人でのスクリプト実行が有効になっていません（既定は無効です）。"
            "人が実行を指示するか、ワークスペースごとの設定で有効にしてください（XC-102）"
        )
    return None


@dataclass(frozen=True, slots=True)
class Artefact:
    """One thing a run wrote, named as the user would recognise it."""

    path: Path
    unit_id: str
    case_id: str | None = None

    def describe(self) -> str:
        where = f"{self.unit_id}" + (f" / {self.case_id}" if self.case_id else "")
        return f"{self.path.name}（{where}）"


@dataclass(slots=True)
class Written:
    """What one run put on the disk, and the offer to remove it (AC-041).

    Undo restores the workspace and not the disk. A run that wrote forty reports and was then undone
    leaves forty reports, and the user's undo was for the workspace - so this is a separate offer, made
    in the same breath rather than left for them to discover.
    """

    artefacts: list[Artefact] = dataclass_field(default_factory=list)

    def note(self, artefact: Artefact) -> None:
        self.artefacts.append(artefact)

    def describe(self) -> str:
        if not self.artefacts:
            return "この実行はファイルを書き出していません"
        named = "、".join(one.describe() for one in self.artefacts)
        return (
            f"この実行は {len(self.artefacts)} 件のファイルを書き出しました：{named}。"
            "取り消しはワークスペースを戻しますが、ディスクは戻しません（XC-061）— "
            "これらを削除するかどうかは別に決めてください"
        )

    def delete(self, *, accepted: bool, only: Iterable[Path] | None = None) -> tuple[Path, ...]:
        """Remove what this run wrote, once somebody has accepted the list.

        `only` narrows it, and anything in it that this run did **not** write is refused rather than
        deleted: a file that was there before is not this run's to remove, and a deletion routine that
        took a path on trust is one that eventually takes the wrong one.
        """
        if not accepted:
            raise AuthorisationError(
                "削除の一覧が承諾されていません。何を消すかを見てから決めてください（AC-041）"
            )
        mine = {one.path for one in self.artefacts}
        wanted = set(only) if only is not None else mine
        outside = sorted(str(path) for path in wanted - mine)
        if outside:
            raise AuthorisationError(
                f"この実行が書き出していないファイルは削除しません：{'、'.join(outside)}"
            )
        removed: list[Path] = []
        for path in sorted(wanted):
            if path.exists():
                path.unlink()
            # A file already gone is reported as removed rather than as an error: the outcome the user
            # asked for is that it is not there, and it is not there.
            removed.append(path)
        self.artefacts = [one for one in self.artefacts if one.path not in wanted]
        return tuple(removed)


def written_from(record: object) -> Written:
    """The artefacts of a finished run, read from its record.

    Takes the record rather than a list of paths, so what can be deleted is what the run said it wrote -
    the same list, not a second one assembled afterwards that might include a file somebody else made.
    """
    written = Written()
    for entry in getattr(record, "written", ()) or ():
        unit, _, case = str(entry).partition("/")
        written.note(Artefact(Path(str(entry)), unit, case or None))
    return written
