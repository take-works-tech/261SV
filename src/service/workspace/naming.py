"""Identifiers that never change and names that never collide, so a rename breaks nothing.

XC-103's rule in one line: **references are stored by identifier, names are for people.** A stored
reference containing a name is a reference that breaks when somebody fixes a typo, and it breaks quietly
- the view still opens, the expression still parses, and the number it shows is from something else or
from nothing.

Three consequences, each of which is a refusal rather than a convenience.

**A colliding name is refused and the holder is named** (AC-023), rather than a suffix being appended.
"baseline (2)" beside "baseline" is a pair of objects nobody can tell apart in a report, created by a
product that decided not to bother the user.

**A lookup by name returns one object or fails saying what it found** (AC-024), never a list. Returning
a list moves the choice to a caller that has less information than this layer does, and every caller
that takes the first element is a bug nobody will find.

**An identifier is never reused.** Not after a delete, not after an undo. A reference held by something
outside this workspace - a pipeline, an exported report, a script - resolves to the object it meant or
to nothing, and never to whatever took its place.

Specification: XC-103, workspace/AC-022 to AC-025, CT-001.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dataclass_field
from typing import Any, Iterable

#: An identifier is a kind, a colon and an opaque suffix. The kind is in it so that a reference read out
#: of a file says what it refers to even when the object is gone - "case:7f3a" is a case somebody
#: deleted, and "7f3a" is nothing anybody can act on.
IDENTIFIER = re.compile(r"^[a-z][a-z-]*:[0-9a-z][0-9a-z-]*$")


class NamingError(Exception):
    """Raised for a collision, a reused identifier, or a lookup that cannot answer with one object."""


@dataclass
class Registry:
    """Every object of every kind in a workspace, by identifier, with the names taken.

    `retired` is the point of the class. An identifier that has been used is remembered after the object
    is gone, so nothing can hand it out again.
    """

    #: kind -> identifier -> name
    live: dict[str, dict[str, str]] = dataclass_field(default_factory=dict)
    #: every identifier ever issued, including those whose object was deleted
    retired: set[str] = dataclass_field(default_factory=set)

    def _of_kind(self, kind: str) -> dict[str, str]:
        return self.live.setdefault(kind, {})

    def issue(self, kind: str, identifier: str, name: str) -> str:
        """Record a new object. Refuses a reused identifier and a colliding name."""
        if not IDENTIFIER.match(identifier):
            raise NamingError(
                f"識別子 '{identifier}' の形が違います。"
                "種別・コロン・不透明な後半（例 'case:7f3a'）にしてください — "
                "ファイルから読み出した参照が、対象が消えていても何を指していたか言えるようにするためです"
            )
        if not identifier.startswith(f"{kind}:"):
            raise NamingError(f"識別子 '{identifier}' は種別 '{kind}' で始まっていません")
        if identifier in self.retired or identifier in self._of_kind(kind):
            raise NamingError(
                f"識別子 '{identifier}' はすでに使われています。識別子は再利用しません — "
                "外部に残った参照が、意図した対象ではなく後から入ったものに解決してしまいます（XC-103）"
            )
        holder = self.holder_of(kind, name)
        if holder is not None:
            raise NamingError(_collision(kind, name, holder))
        self._of_kind(kind)[identifier] = name
        self.retired.add(identifier)
        return identifier

    def rename(self, kind: str, identifier: str, name: str) -> None:
        """Change what an object is called. Every stored reference keeps working, because none holds
        the name."""
        names = self._of_kind(kind)
        if identifier not in names:
            raise NamingError(f"'{identifier}' は種別 '{kind}' にありません")
        holder = self.holder_of(kind, name)
        if holder is not None and holder != identifier:
            raise NamingError(_collision(kind, name, holder))
        names[identifier] = name

    def retire(self, kind: str, identifier: str) -> None:
        """Remove an object. Its identifier stays retired and is never issued again."""
        self._of_kind(kind).pop(identifier, None)

    def holder_of(self, kind: str, name: str) -> str | None:
        """The identifier already using this name for this kind, or None."""
        for identifier, held in self._of_kind(kind).items():
            if held == name:
                return identifier
        return None

    def name_of(self, kind: str, identifier: str) -> str | None:
        return self._of_kind(kind).get(identifier)

    def resolve(self, kind: str, name: str) -> str:
        """One identifier for a name, or a failure saying what was searched (AC-024).

        Never a list. Returning one moves the choice to a caller with less information than this layer
        has, and every caller that takes the first element is a bug nobody will find.
        """
        matches = [
            identifier for identifier, held in self._of_kind(kind).items() if held == name
        ]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            known = sorted(self._of_kind(kind).values())
            raise NamingError(
                f"種別 '{kind}' に '{name}' という名前のものはありません。"
                f"あるのは {known or '（ひとつもありません）'} です"
            )
        raise NamingError(
            f"種別 '{kind}' に '{name}' が {len(matches)} 件あります：{sorted(matches)}。"
            "名前の重複は作成時に拒否されるはずのもので、この文書は外部で編集されています"
        )


def _collision(kind: str, name: str, holder: str) -> str:
    return (
        f"種別 '{kind}' に '{name}' はすでにあります（{holder}）。"
        "接尾辞を付けて回避することはしません — "
        "'baseline (2)' と 'baseline' は、レポートの中で誰にも区別できない一対になります（AC-023）"
    )


def registry_of(document: dict[str, Any]) -> Registry:
    """Build a registry from a document as it stands, so a collision is checked against reality.

    Reads the cases, the variables and the workspace items. A kind absent from the document contributes
    nothing rather than an empty promise.
    """
    from service.workspace.hierarchy import walk  # imported here to keep the module graph acyclic

    registry = Registry()
    for case, _ in walk(document.get("cases", [])):
        _adopt(registry, "case", case)
    for variable in document.get("variables", []):
        _adopt(registry, "variable", variable)
    for kind, entries in (document.get("workspaceItems") or {}).items():
        singular = kind[:-1] if kind.endswith("s") else kind
        for entry in entries if isinstance(entries, list) else []:
            _adopt(registry, singular, entry)
    return registry


def _adopt(registry: Registry, kind: str, entry: dict[str, Any]) -> None:
    """Take an object that already exists into the registry, without the checks a new one gets.

    A document written by another version, or edited outside this product, may hold identifiers this
    build would not issue and names this build would not have allowed. Refusing to load them would lose
    the user's work over a rule about how they were made; the collision check applies to what happens
    **next**.
    """
    identifier = str(entry.get("id", ""))
    if not identifier:
        return
    registry.live.setdefault(kind, {})[identifier] = str(entry.get("name", ""))
    registry.retired.add(identifier)


def references_in(value: Any) -> Iterable[str]:
    """Every identifier-shaped string anywhere inside a structure.

    Used to check that a stored reference is an identifier and not a name (AC-022) - which is a thing a
    test can assert about a whole document rather than one field at a time.
    """
    if isinstance(value, str):
        if IDENTIFIER.match(value):
            yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from references_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from references_in(item)
