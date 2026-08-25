"""The object model a script reaches, and the one rule underneath it.

**A script issues commands; it does not reach past them** (13_scripting.md). There is no path from here
into a module's internals, no direct write to the workspace document, and no way to produce a @View the
command log does not contain. The reason is not tidiness: undo, the run record, reproducibility and the
dry run are all built on the log, and an action that skipped it would be invisible to all four at once.

So this module builds documents and issues commands, and holds no behaviour of its own. `sv.data` reads
and needs no command - a script that only reads produces no log entries and no undo steps. `sv.ops`
writes, and everything it does goes through MOD-012.

**One script is one undo step** (XC-061, XC-102), which is where this deliberately differs from the
reference application: there, operators called from Python bypass the undo stack by default so that a
script does not push a step per operator (E-064). That trade suits a tool whose scripts mostly run
before anyone is watching. Here the customer asks an agent to build forty reports and must be able to
take it back.

**Lookup by name resolves to exactly one object, or raises** (XC-103). The two reference products
diverge here and the divergence is instructive: one appends a numeric suffix, so `Cube` silently becomes
`Cube.002` and a script written against the name it asked for gets something else (E-064); the other
allows duplicates and returns every match, so the documented idiom is to take the first and hope
(E-067). Refusing is the only one of the three that never quietly points a reference at the wrong
object - and in a product whose output is numbers attached to names, the wrong object is a wrong answer
with a plausible label.

Specification: 13_scripting.md, XC-102, XC-103, XC-061, pipeline/AC-035, AC-036.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any, Iterable, Mapping

from service.command.catalogue import OPERATIONS, writes
from service.command.surface import Command, Origin, Permission, Result, Surface
from service.pipeline.document import (
    DefinitionRef,
    Kind,
    Source,
    add,
    add_cases_unit,
    artefact_unit,
    condition_unit,
    formula_unit,
    loop_unit,
    variable_unit,
)


class ScriptError(Exception):
    """Raised for a lookup that cannot resolve to one object, or a call the model does not offer."""


@dataclass(frozen=True, slots=True)
class Named:
    """One object a script can reach: its stable identifier and the name people use.

    Stored references use the **identifier** (XC-103), so renaming rewires nothing - nothing stored ever
    pointed at the name.
    """

    identifier: str
    name: str
    revision: int = 1


class Collection:
    """Objects of one kind, reached by name.

    Never returns a list to be indexed. A collection that answered a lookup with several matches would
    make "take the first" the documented idiom, and the first is whichever one happened to be created
    earlier.
    """

    def __init__(self, kind: str, items: Iterable[Named] = ()) -> None:
        self.kind = kind
        self._items: list[Named] = list(items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self._items)

    def __getitem__(self, name: str) -> Named:
        found = [item for item in self._items if item.name == name]
        if not found:
            known = "、".join(sorted(self.names())) or "（ひとつもありません）"
            raise ScriptError(f"{self.kind} に '{name}' はありません。あるのは：{known}")
        if len(found) > 1:
            raise ScriptError(
                f"{self.kind} の '{name}' が {len(found)} 件あります。"
                "どれか一つを返すことはしません — 名前で引いた参照が別のものを指すのは、"
                "もっともらしいラベルのついた誤答です（XC-103）"
            )
        return found[0]

    def by_id(self, identifier: str) -> Named:
        for item in self._items:
            if item.identifier == identifier:
                return item
        raise ScriptError(f"{self.kind} に識別子 '{identifier}' はありません")

    def add(self, item: Named) -> Named:
        """Refuses a name already in use, naming what holds it (XC-103).

        Not a suffix. `Cube` becoming `Cube.002` is the behaviour that hands a script something other
        than what it asked for, without saying so.
        """
        if item.name in self.names():
            holder = self[item.name]
            raise ScriptError(
                f"{self.kind} の名前 '{item.name}' は '{holder.identifier}' が使っています。"
                "連番を付けて別名にすることはしません"
            )
        self._items.append(item)
        return item


class PipelineScript:
    """`sv.pipeline` - building a CT-009 document.

    Every edit goes through MOD-011's own functions, so a pipeline a script builds is refused by exactly
    the rules that refuse one built by hand. A builder that assembled the dictionary itself would be a
    second implementation of the edit-time rules, and the copy would be the one that stopped refusing.
    """

    def __init__(self, identifier: str, name: str) -> None:
        self.document: dict[str, Any] = {"id": identifier, "name": name, "units": []}

    def add_cases(self, unit_id: str, case_ids: Iterable[str], **kwargs: Any) -> PipelineScript:
        add(self.document, add_cases_unit(unit_id, case_ids, **kwargs))
        return self

    def view(self, unit_id: str, reference: DefinitionRef, **kwargs: Any) -> PipelineScript:
        add(self.document, artefact_unit(unit_id, Kind.VIEW, reference, **kwargs))
        return self

    def graph(self, unit_id: str, reference: DefinitionRef, **kwargs: Any) -> PipelineScript:
        add(self.document, artefact_unit(unit_id, Kind.GRAPH, reference, **kwargs))
        return self

    def report(self, unit_id: str, reference: DefinitionRef, **kwargs: Any) -> PipelineScript:
        add(self.document, artefact_unit(unit_id, Kind.REPORT, reference, **kwargs))
        return self

    def variable(self, unit_id: str, name: str, **kwargs: Any) -> PipelineScript:
        add(self.document, variable_unit(unit_id, name, **kwargs))
        return self

    def formula(
        self,
        unit_id: str,
        name: str,
        expression: str,
        *,
        inside: str | None = None,
        outside: Iterable[str] = (),
    ) -> PipelineScript:
        # `outside` is what the workspace supplies - a formula may name a recorded quantity of a case,
        # which no unit above it binds. Passed through rather than defaulted to nothing, or the edit-time
        # check would refuse every expression that reads the data the pipeline exists to read.
        add(self.document, formula_unit(unit_id, name, expression), inside=inside, outside=outside)
        return self

    def loop(self, unit_id: str, **kwargs: Any) -> PipelineScript:
        add(self.document, loop_unit(unit_id, **kwargs))
        return self

    def condition(
        self,
        unit_id: str,
        expression: str,
        *,
        inside: str | None = None,
        outside: Iterable[str] = (),
    ) -> PipelineScript:
        add(self.document, condition_unit(unit_id, expression), inside=inside, outside=outside)
        return self

    def inside(self, container_id: str, unit: dict[str, Any], **kwargs: Any) -> PipelineScript:
        add(self.document, unit, inside=container_id, **kwargs)
        return self


class Operations:
    """`sv.ops` - the command surface, with every call carrying the script's identity and group.

    A script's commands are ordinary commands: refused by the same rules, logged the same way, and
    undone as one step. There is no privileged form.
    """

    def __init__(self, surface: Surface, group_id: str) -> None:
        self._surface = surface
        self._group_id = group_id
        self._issued: list[Result] = []

    def call(
        self,
        operation: str,
        parameters: Mapping[str, Any] | None = None,
        *,
        targets: Iterable[str] = (),
        allowed: Iterable[Permission] = (),
        dry_run: bool = False,
    ) -> Result:
        if operation not in OPERATIONS:
            raise ScriptError(
                f"'{operation}' はこの製品の操作ではありません。"
                "存在しない操作の呼び出しは、実行時ではなくここで止めます"
            )
        result = self._surface.submit(
            Command(
                operation,
                dict(parameters or {}),
                Origin.SCRIPT,
                tuple(targets),
                self._group_id,
                frozenset(allowed),
                dry_run,
            )
        )
        self._issued.append(result)
        return result

    @property
    def issued(self) -> tuple[Result, ...]:
        return tuple(self._issued)

    def undo_all(self) -> Result:
        """One script, one undo step (XC-061)."""
        return self._surface.undo(self._group_id)


@dataclass(slots=True)
class Session:
    """`sv` - the root a script is handed.

    `data` is readable and `ops` is writable, and the split is not cosmetic: reading needs no command,
    so a script that only reads produces no log entries and no undo steps.
    """

    surface: Surface
    group_id: str = "script:001"
    cases: Collection = dataclass_field(default_factory=lambda: Collection("ケース"))
    views: Collection = dataclass_field(default_factory=lambda: Collection("ビュー"))
    graphs: Collection = dataclass_field(default_factory=lambda: Collection("グラフ"))
    reports: Collection = dataclass_field(default_factory=lambda: Collection("レポート"))
    variables: Collection = dataclass_field(default_factory=lambda: Collection("変数"))

    @property
    def ops(self) -> Operations:
        return Operations(self.surface, self.group_id)

    def pipeline(self, identifier: str, name: str) -> PipelineScript:
        return PipelineScript(identifier, name)

    def reference(self, item: Named, *, source: Source = Source.WORKSPACE_ITEM) -> DefinitionRef:
        """A pinned reference to a workspace item, with the revision it has now.

        Pinned here rather than resolved at run time, because a reference that quietly becomes the
        newest revision is a pipeline whose output changed when somebody else edited a definition.
        """
        return DefinitionRef(source, item.identifier, item.revision)

    def reads_only(self, operations: Iterable[str]) -> bool:
        return all(not writes(operation) for operation in operations)
