"""A template travelling: to the shared library, into a file, and back out somewhere else.

A template exists to cross studies, so the interesting cases are the ones where it does not fit. XC-090
settles them: **it applies as far as it resolves and names what it could not**, before anything is
drawn. Applying only on an exact match makes the rule trivial and defeats the purpose.

Four things this module refuses to do quietly.

**Promotion does not take the origin's workspace with it.** A shared template must be openable on a
machine that has never seen the workspace it came from, so what it needs is written down at promotion
(AC-037) rather than discovered by whoever applies it next year. Promotion is **not refused** when
something is resolvable only inside the origin - it is reported, because refusing turns a shareable
template into an unshareable one over a detail the user may be happy to accept.

**An asset whose licence forbids embedding is listed by name, not included.** A template that quietly
embeds a font somebody redistributed is a licence problem the user finds out about from someone else
(XC-025).

**An import records where it came from.** A template that arrives anonymous is one nobody can go back
to when its numbers are questioned.

**A contradicted arity is refused rather than guessed.** A template written for one @Case applied to a
set, or the reverse, is not a near miss - it is a different operation with a different answer.

Specification: XC-090, XC-025, GL-019, workspace/AC-036 to AC-040, AC-063.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from service.workspace.items import SCOPES, templates_of


class Arity(str, Enum):
    """How many @Case a template is written for (AC-040)."""

    ONE = "one"      # a single case
    MANY = "many"    # a set, compared or combined
    EITHER = "either"


class TemplateError(Exception):
    """Raised for a use a template's own statement rules out, or an export that cannot be honest."""


@dataclass(frozen=True, slots=True)
class Requirement:
    """One thing a template needs from wherever it is applied."""

    kind: str      # field, unit, variable, part, entry
    name: str
    #: True where this could be resolved only inside the workspace it was promoted from - the case
    #: AC-037 asks be reported rather than refused.
    origin_only: bool = False

    def describe(self) -> str:
        line = f"{self.kind} '{self.name}'"
        return line + "（元のワークスペース内でしか解決できません）" if self.origin_only else line


#: Where a requirement can be found in a definition. Written out rather than discovered by walking for
#: anything that looks like a name: a template's requirements are a promise to its user, and a promise
#: assembled by pattern-matching is one that changes when somebody renames a key.
REQUIREMENT_KEYS: dict[str, str] = {
    "field": "fields",
    "unit": "units",
    "variable": "variables",
    "part": "parts",
    "entry": "entries",
}


def requirements_of(
    definition: dict[str, Any], *, resolvable_in_origin_only: Iterable[str] = ()
) -> tuple[Requirement, ...]:
    """What a template needs from a target, collected for AC-037."""
    only = set(resolvable_in_origin_only)
    found: list[Requirement] = []
    for kind, key in REQUIREMENT_KEYS.items():
        for name in definition.get(key, []) or []:
            found.append(Requirement(kind, str(name), origin_only=str(name) in only))
    return tuple(sorted(found, key=lambda r: (r.kind, r.name)))


@dataclass(frozen=True, slots=True)
class Promotion:
    """The result of moving a template to a wider scope."""

    template_id: str
    scope: str
    requirements: tuple[Requirement, ...]

    @property
    def origin_only(self) -> tuple[Requirement, ...]:
        return tuple(item for item in self.requirements if item.origin_only)

    def describe(self) -> str:
        line = f"'{self.template_id}' を {self.scope} スコープに昇格しました"
        if not self.requirements:
            return line + "。必要なものはありません"
        line += f"。適用先に必要なもの {len(self.requirements)} 件"
        if self.origin_only:
            names = "、".join(item.name for item in self.origin_only)
            line += (
                f"。うち {len(self.origin_only)} 件は元のワークスペース内でしか解決できません"
                f"（{names}）— 昇格は妨げませんが、他所では未解決として一覧されます"
            )
        return line


def promote(
    document: dict[str, Any],
    kind: str,
    template_id: str,
    *,
    scope: str,
    resolvable_in_origin_only: Iterable[str] = (),
) -> Promotion:
    """Move a template to a wider scope, writing down what it needs from a target.

    The originating workspace still opens on its own (AC-036): promotion copies the definition outward
    and does not make the origin depend on the library.
    """
    if scope not in SCOPES or scope == "sample":
        raise TemplateError(
            f"昇格先のスコープは {[s for s in SCOPES if s != 'sample']} のいずれかです。"
            "sample は製品に同梱されるもので、その場で編集しません（GL-019）"
        )
    for template in templates_of(document, kind):
        if template.get("id") == template_id:
            requirements = requirements_of(
                template.get("definition", {}),
                resolvable_in_origin_only=resolvable_in_origin_only,
            )
            # Recorded on the template rather than returned only: whoever applies it next year reads
            # the template, not this call.
            template["requirements"] = [
                {"kind": r.kind, "name": r.name, "originOnly": r.origin_only} for r in requirements
            ]
            template["scope"] = scope
            return Promotion(template_id, scope, requirements)
    raise TemplateError(f"テンプレート '{template_id}' がありません")


@dataclass(frozen=True, slots=True)
class Export:
    """One self-contained file, and what could not go into it."""

    path: Path
    embedded: tuple[str, ...]
    listed_only: tuple[str, ...] = dataclass_field(default_factory=tuple)

    def describe(self) -> str:
        line = f"{self.path.name} に定義と {len(self.embedded)} 件の素材を埋め込みました"
        if self.listed_only:
            line += (
                f"。ライセンス上埋め込めない {len(self.listed_only)} 件は名前で記載しています"
                f"（{'、'.join(self.listed_only)}）— 同梱すると、受け取った側が第三者から"
                "知らされる種類の問題になります（XC-025）"
            )
        return line


def export(
    template: dict[str, Any],
    path: str | Path,
    *,
    assets: dict[str, bytes] | None = None,
    embeddable: Iterable[str] = (),
) -> Export:
    """Write one self-contained file (AC-038).

    An asset absent from `embeddable` is **listed by name and not included**, whatever its size. The
    rule is about the licence, not about convenience, so it is expressed as an allowance rather than a
    denial: an asset nobody has cleared is not embedded.
    """
    assets = assets or {}
    allowed = set(embeddable)
    embedded = {name: data.hex() for name, data in assets.items() if name in allowed}
    listed = tuple(sorted(name for name in assets if name not in allowed))

    body = {
        "kind": "solvia-template",
        "template": template,
        "embeddedAssets": embedded,
        "listedAssets": list(listed),
        "origin": template.get("origin") or template.get("id"),
    }
    location = Path(path)
    location.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return Export(location, tuple(sorted(embedded)), listed)


@dataclass(frozen=True, slots=True)
class Import:
    """A template that arrived from elsewhere, and what it still needs."""

    template: dict[str, Any]
    scope: str
    origin: str
    unresolved: tuple[Requirement, ...]

    def describe(self) -> str:
        line = f"'{self.template.get('name', self.template.get('id'))}' を {self.scope} に取り込みました"
        line += f"（出所 {self.origin}）"
        if self.unresolved:
            names = "、".join(item.name for item in self.unresolved)
            line += (
                f"。未解決 {len(self.unresolved)} 件：{names}。"
                "解決した分は適用でき、残りは名前で一覧されます（XC-090）"
            )
        return line


def import_template(
    document: dict[str, Any],
    kind: str,
    path: str | Path,
    *,
    scope: str = "workspace",
    available: Iterable[str] = (),
) -> Import:
    """Read an exported template into a scope, recording where it came from (AC-039).

    What resolves against `available` is usable; what does not is listed rather than making the import
    fail. A template exists to cross studies, and refusing one that does not fit exactly defeats it.
    """
    if scope not in SCOPES or scope == "sample":
        raise TemplateError(f"取り込み先のスコープは {[s for s in SCOPES if s != 'sample']} です")
    location = Path(path)
    try:
        body = json.loads(location.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TemplateError(f"{location.name} を読めません：{error}") from None
    if body.get("kind") != "solvia-template":
        raise TemplateError(
            f"{location.name} はテンプレートのエクスポートではありません（kind={body.get('kind')!r}）"
        )

    template = dict(body.get("template", {}))
    template["scope"] = scope
    # Recorded on the template. One that arrives anonymous is one nobody can go back to when its
    # numbers are questioned.
    template["origin"] = str(body.get("origin", location.name))

    have = set(available)
    stated = template.get("requirements") or [
        {"kind": r.kind, "name": r.name, "originOnly": r.origin_only}
        for r in requirements_of(template.get("definition", {}))
    ]
    unresolved = tuple(
        Requirement(str(item["kind"]), str(item["name"]), bool(item.get("originOnly", False)))
        for item in stated
        if str(item["name"]) not in have
    )
    templates_of(document, kind).append(template)
    return Import(template, scope, template["origin"], unresolved)


def check_arity(template: dict[str, Any], case_count: int) -> None:
    """Refuse a use the template's own statement rules out (AC-040).

    Not a near miss: a template written for one case applied to a set is a different operation with a
    different answer, and guessing which the user meant produces the answer nobody asked for.
    """
    stated = str(template.get("arity", Arity.EITHER.value))
    try:
        arity = Arity(stated)
    except ValueError:
        raise TemplateError(
            f"テンプレートの arity が '{stated}' です。{[a.value for a in Arity]} のいずれかです"
        ) from None
    if arity is Arity.ONE and case_count != 1:
        raise TemplateError(
            f"このテンプレートは 1 ケース用（arity=one）ですが、{case_count} ケースに適用しようと"
            "しています。どちらのつもりかを推測はしません — 別の操作で、別の答えになります"
        )
    if arity is Arity.MANY and case_count < 2:
        raise TemplateError(
            f"このテンプレートは複数ケース用（arity=many）ですが、{case_count} ケースに適用しようと"
            "しています"
        )
