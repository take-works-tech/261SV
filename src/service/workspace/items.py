"""Working artefacts and reusable templates, kept apart on purpose.

XC-109 separated two things an earlier model collapsed into one. A **workspace item** is the concrete
view, graph or report a user opens and edits. A **template** is a reusable blueprint in the workspace or
shared library. Applying a template creates a new independent item; saving an item as a template copies
its current definition into a new revision. **Editing either side never silently changes the other.**

Three consequences the code has to enforce rather than describe.

**No item belongs to a @Case.** A case is an argument to an item, not its owner. That is why switching
case re-renders the same item: the alternative - a per-case copy - is how a user ends up editing the
wrong one of nine views called "断面" and finding out in a report.

**Applying a template records where it came from and copies the definition.** The identifier and the
revision travel with the item as provenance. A live link would mean a template edit changing somebody's
finished report, and XC-109 puts that outside r1: if it ever exists it is explicit and visible.

**Saving as a template makes a new revision and leaves the item alone.** The item stays independently
editable, which is the whole difference between copying a definition and adopting one.

Specification: XC-109, GL-019, workspace/AC-030, AC-031, AC-032, AC-061, CT-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from service.workspace.hierarchy import walk
from service.workspace.naming import NamingError, Registry, registry_of

#: The collections a workspace owns, and the Japanese labels XC-109 fixes for them. The labels are here
#: rather than in the interface layer because XC-109 decided them: `テンプレート` is reserved for the
#: reusable library, and a list of working artefacts that calls itself that is the collapse the decision
#: undid.
COLLECTIONS: dict[str, str] = {
    "views": "ビュー一覧",
    "graphs": "グラフ一覧",
    "reports": "レポート一覧",
    "simulations": "シミュレーション一覧",
}

#: Where a reusable blueprint may live (GL-019). `sample` ships with the product and is read-only.
SCOPES = ("workspace", "shared", "sample")


class ItemError(Exception):
    """Raised when an operation would put an item somewhere it does not belong."""


@dataclass(frozen=True, slots=True)
class SourceTemplate:
    """Where an item's definition came from, if it came from a template.

    Provenance, not a link. The revision is recorded so that "this came from 断面テンプレート v3" is
    answerable later, and so that nothing can mistake it for a subscription to v4.
    """

    template_id: str
    revision: int


def _collection(document: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    if kind not in COLLECTIONS:
        raise ItemError(f"'{kind}' はワークスペースが持つ一覧ではありません（{list(COLLECTIONS)}）")
    return document.setdefault("workspaceItems", {}).setdefault(kind, [])


def _templates(document: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    # The serialized field keeps the historical name `templates` for version-4 compatibility (CT-001).
    return document.setdefault("templates", {}).setdefault(kind, [])


def create(
    document: dict[str, Any],
    kind: str,
    item_id: str,
    name: str,
    definition: dict[str, Any],
    *,
    source: SourceTemplate | None = None,
) -> dict[str, Any]:
    """Add a concrete item to the workspace. Never to a @Case, and never as a template (AC-030)."""
    registry = registry_of(document)
    singular = kind[:-1] if kind.endswith("s") else kind
    try:
        registry.issue(singular, item_id, name)
    except NamingError as error:
        raise ItemError(str(error)) from None

    item: dict[str, Any] = {"id": item_id, "name": name, "definition": dict(definition)}
    if source is not None:
        item["sourceTemplate"] = {"id": source.template_id, "revision": source.revision}
    _collection(document, kind).append(item)
    return item


def find(document: dict[str, Any], kind: str, item_id: str) -> dict[str, Any]:
    for item in _collection(document, kind):
        if item.get("id") == item_id:
            return item
    raise ItemError(f"{COLLECTIONS[kind]}に '{item_id}' はありません")


def edit(document: dict[str, Any], kind: str, item_id: str, definition: dict[str, Any]) -> dict[str, Any]:
    """Change one item's definition, and nothing else (AC-031).

    Not its source template, not a sibling item, not a copy on a case - there is no copy on a case.
    """
    item = find(document, kind, item_id)
    item["definition"] = dict(definition)
    return item


def apply_template(
    document: dict[str, Any],
    kind: str,
    template_id: str,
    item_id: str,
    name: str,
) -> dict[str, Any]:
    """Create a new independent item from a template, carrying where it came from (AC-061).

    The definition is **copied**. A shared structure here would make a later template edit reach into a
    report somebody already sent.
    """
    for template in _templates(document, kind):
        if template.get("id") == template_id:
            revision = int(template.get("revision", 1))
            return create(
                document, kind, item_id, name,
                dict(template.get("definition", {})),
                source=SourceTemplate(template_id, revision),
            )
    raise ItemError(f"テンプレート '{template_id}' が {COLLECTIONS[kind]} にありません")


def save_as_template(
    document: dict[str, Any],
    kind: str,
    item_id: str,
    template_id: str,
    name: str,
    *,
    scope: str = "workspace",
) -> dict[str, Any]:
    """Copy an item's current definition into a new template revision (AC-032).

    The item stays independently editable - that is the whole difference between copying a definition
    and adopting one. Only workspace scope is written into the document; shared and sample entries live
    outside it (CT-001).
    """
    if scope not in SCOPES:
        raise ItemError(f"スコープ '{scope}' は {list(SCOPES)} のいずれかです")
    if scope != "workspace":
        raise ItemError(
            f"スコープ '{scope}' のテンプレートはワークスペース文書の外にあります。"
            "ここに書くとワークスペースを配っただけで共有ライブラリが増えます（CT-001）"
        )
    item = find(document, kind, item_id)
    existing = [t for t in _templates(document, kind) if t.get("id") == template_id]
    revision = max((int(t.get("revision", 1)) for t in existing), default=0) + 1
    template = {
        "id": template_id,
        "name": name,
        "revision": revision,
        "scope": scope,
        "definition": dict(item["definition"]),
    }
    _templates(document, kind).append(template)
    return template


def cases_owning_items(document: dict[str, Any]) -> tuple[str, ...]:
    """Any case holding a definition of its own - which none may (AC-030).

    A check rather than a comment: the model this replaced put artefacts on cases, and a document
    written by that model, or by hand, would put them back.
    """
    owning: list[str] = []
    for case, _ in walk(document.get("cases", [])):
        if any(key in case for key in ("views", "graphs", "reports", "simulations", "definition")):
            owning.append(str(case.get("id", "")))
    return tuple(owning)


def registry_including_templates(document: dict[str, Any]) -> Registry:
    """Names in use across items and templates, so a new one is checked against both."""
    registry = registry_of(document)
    for kind, entries in (document.get("templates") or {}).items():
        singular = (kind[:-1] if kind.endswith("s") else kind) + "-template"
        for entry in entries if isinstance(entries, list) else []:
            identifier = str(entry.get("id", ""))
            if identifier:
                registry.live.setdefault(singular, {})[identifier] = str(entry.get("name", ""))
                registry.retired.add(identifier)
    return registry
