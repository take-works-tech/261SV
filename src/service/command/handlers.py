"""The composition root: production handlers on the command surface (XC-257, step 2).

Until 2026-09-18 `Surface.register` had no caller under `src/`. The vocabulary, the readers, the
reductions and the document writer all existed as tested library code, and every one of the 61
catalogue operations was answered 「カタログにありますが、このビルドに実装がありません」. This
module is what joins them: one `Session` holding what the engine has in memory, and `build_surface`,
which registers a handler for each operation this build can honestly perform.

What is deliberately **not** registered is as much the point as what is. `view.render` and
`dataset.probe` have no handler here - the renderer is step 3 of the path and the probe step 4 - so
the surface keeps answering "no implementation" for them, which is true, rather than a picture or a
number that is not.

Every handler answers in the shape CT-003 states and is held to it by the surface (RESULT_FIELDS,
REPORTED_VALUES). A caller's mistake - a case that is not there, a file that cannot be read, a unit
this product does not know - comes back as a **refusal** with the reason; only a defect in this
module comes back as a failure, because that is the difference the two words mark (CT-002).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from domain_core.association import Association
from domain_core.dataset import Dataset, Field
from domain_core.parts import LoadedCase, Part
from domain_core.recorded_time import RecordedTime, record as record_time
from domain_core.reported_value import Caveat, Provenance, ReportedValue
from domain_core.units import UndeclaredUnitError, unit as known_unit
from engine import reader
from engine.analysis import weights as field_weights
from engine.analysis.summary import Reduction, Summary, SummaryError, Weighting, summarise
from engine.limits import MachineClass
from engine.report import html
from engine.report.document import (
    Provenance as ReportProvenance,
    ReportError,
    SourceFile,
    ValueRow,
    build as build_document,
)
from engine.visualization.backends import REQUIRES, Backend, probe
from service.command.catalogue import PROTOCOL_VERSION
from service.command.surface import Effect, Handler, Result, Status, Surface
from service.workspace import items, sources
from service.workspace.document import WorkspaceDocument, WorkspaceFileError, load as load_workspace
from service.workspace.hierarchy import find as find_case, walk as walk_cases
from service.workspace.items import ItemError

#: The distribution this engine ships as. Read from the installed metadata rather than restated, so
#: the version a document names is the one that was installed and not the one somebody last typed.
DISTRIBUTION = "sim-viewer-engine"

#: CT-003's spelling of an association beside this product's own. `field` (global arrays) has no
#: counterpart here: the readers do not surface one, so it is never answered.
ASSOCIATION_WORD: dict[Association, str] = {
    Association.POINT: "point",
    Association.CELL: "cell",
    Association.INTEGRATION_POINT: "integrationPoint",
}

#: How long a handle's bytes are kept after they are issued (CT-003 "Large payloads"). Short, because
#: a handle is a way to fetch an answer that was just given, not a cache.
HANDLE_LIFETIME_SECONDS = 300


def product_version() -> str:
    """The installed version, or a statement that this is not an installed build."""
    try:
        return metadata.version(DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return "未配布ビルド（パッケージ情報なし）"


def refused(reason: str) -> Result:
    return Result(Status.REFUSED, reason=reason)


def identifier(kind: str) -> str:
    """A fresh identifier in the form the workspace registry requires: kind, colon, opaque tail."""
    return f"{kind}:{secrets.token_hex(4)}"


def reported(value: ReportedValue) -> dict[str, Any]:
    """A reported value in CT-003's shape. Only the keys that carry something are present."""
    answer: dict[str, Any] = {
        "value": value.value,
        "unit": value.unit,
        "digits": value.digits,
        "provenance": value.provenance.value,
    }
    if value.formula:
        answer["formula"] = value.formula
    if value.caveats:
        answer["caveats"] = sorted(one.value for one in value.caveats)
    if value.missing_because:
        answer["missingBecause"] = value.missing_because
    if value.location:
        answer["location"] = value.location
    return answer


def as_reported(summary: Summary, *, digits: int, formula: str, caveats: frozenset[Caveat]) -> ReportedValue:
    """A `Summary` as a `ReportedValue`: digits and provenance attached, an absence kept as one.

    `Summary` carries the reduction, the weighting and the count; it does not carry digits or a
    provenance, because MOD-004 does not know what the field was stored as. This is the seam XC-257
    named as missing - until it existed, no reduction reached a document except by hand.
    """
    if summary.value is None:
        return ReportedValue.unavailable(
            summary.unavailable or "求められません",
            unit=summary.unit, digits=digits, provenance=Provenance.COMPUTED,
            caveats=caveats, formula=formula,
        )
    if summary.unit is None:
        caveats = caveats | {Caveat.UNDECLARED_UNIT}
    return ReportedValue(
        value=summary.value, unit=summary.unit, digits=digits,
        provenance=Provenance.COMPUTED, caveats=caveats, formula=formula,
    )


def bounds_m(datasets: list[Dataset]) -> dict[str, list[float]]:
    points = np.concatenate([dataset.points_m for dataset in datasets])
    return {
        "minM": [float(value) for value in points.min(axis=0)],
        "maxM": [float(value) for value in points.max(axis=0)],
    }


# -- what the engine holds ---------------------------------------------------------------------


@dataclass(slots=True)
class Loaded:
    """One loaded dataset: the case as read, where it came from, and what a person declared since."""

    case: LoadedCase
    path: Path
    case_id: str
    support_level: str
    gaps: tuple[str, ...]
    declared_units: dict[str, str] = dataclass_field(default_factory=dict)

    def holders(self, field_name: str) -> list[Part]:
        return [
            part for part in self.case.present
            if part.dataset is not None and field_name in part.dataset.fields
        ]

    def datasets(self) -> list[Dataset]:
        return [part.dataset for part in self.case.present if part.dataset is not None]


class HandleExpired(Exception):
    """A handle used after its lifetime. A refusal, never a stale answer (CT-003)."""


@dataclass(slots=True)
class HandleStore:
    """Bytes an answer refers to by handle, kept for a stated lifetime.

    Geometry and images do not travel in a response body (CT-003 "Large payloads"): the answer names a
    handle, the bytes are fetched separately, and a handle names its own lifetime.
    """

    clock: Callable[[], datetime]
    lifetime_seconds: int = HANDLE_LIFETIME_SECONDS
    _held: dict[str, tuple[bytes, datetime]] = dataclass_field(default_factory=dict)

    def issue(self, data: bytes) -> dict[str, Any]:
        handle = identifier("handle")
        self._held[handle] = (data, self.clock())
        return {"id": handle, "bytes": len(data), "expiresAfterSeconds": self.lifetime_seconds}

    def fetch(self, handle: str) -> bytes:
        held = self._held.get(handle)
        if held is None:
            raise HandleExpired(f"ハンドル '{handle}' はありません。期限切れか、発行されていません")
        data, issued = held
        if (self.clock() - issued).total_seconds() > self.lifetime_seconds:
            del self._held[handle]
            raise HandleExpired(
                f"ハンドル '{handle}' は {self.lifetime_seconds} 秒の期限を過ぎました。"
                "古い答えを返すより、取り直しをお願いします"
            )
        return data


def native_offscreen_available() -> tuple[bool, str]:
    """Whether the native toolkit's OpenGL path can be loaded here - and no more than that.

    An import proves the module is present, not that a context can be created (E-191 measured that
    on one machine). Saying which of the two was checked is what keeps `system.capabilities` honest.
    """
    try:
        import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
    except ImportError as error:
        return False, f"読み込めません：{error}"
    return True, "モジュールは読み込めました（描画コンテキストの作成は未検証）"


@dataclass(slots=True)
class Session:
    """What one engine process holds between commands. The authority is the workspace (MOD-007);
    this is what the handlers reach it through."""

    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc).astimezone()
    issue: Callable[[str], str] = identifier
    #: The class this build is budgeted for. Defaults to the integrated class because that is the
    #: safe direction: handing an integrated machine the workstation's budget is twice what LIM-001
    #: allows (XC-086), while the reverse merely renders less than it could.
    machine_class: MachineClass = MachineClass.INTEGRATED
    native_offscreen: Callable[[], tuple[bool, str]] = native_offscreen_available
    workspace: WorkspaceDocument | None = None
    workspace_path: Path | None = None
    datasets: dict[str, Loaded] = dataclass_field(default_factory=dict)
    revisions: dict[str, int] = dataclass_field(default_factory=dict)
    handles: HandleStore = dataclass_field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.handles is None:
            self.handles = HandleStore(self.clock)

    def loaded(self, dataset_id: str) -> Loaded | Result:
        found = self.datasets.get(dataset_id)
        if found is None:
            return refused(f"データセット '{dataset_id}' は読み込まれていません")
        return found

    def open_workspace(self, workspace_id: str | None = None) -> WorkspaceDocument | Result:
        if self.workspace is None:
            return refused("ワークスペースが開いていません。先に workspace.open が要ります")
        if workspace_id is not None and workspace_id != self.workspace.identifier:
            return refused(
                f"ワークスペース '{workspace_id}' は開いていません（開いているのは '{self.workspace.identifier}'）"
            )
        return self.workspace

    def provenance_of(self, involved: list[Loaded]) -> ReportProvenance:
        """The trust content of a deliverable, from what this session knows first-hand."""
        workspace = self.workspace
        return ReportProvenance(
            workspace_id=workspace.identifier if workspace is not None else "",
            case_ids=tuple(dict.fromkeys(one.case_id for one in involved)),
            sources=tuple(
                SourceFile(path=str(one.path), modified=modified_time(one.path)) for one in involved
            ),
            declared_units={
                name: symbol for one in involved for name, symbol in one.declared_units.items()
            },
            product_version=product_version(),
            produced=record_time(self.clock()),
        )


def modified_time(path: Path) -> RecordedTime:
    return record_time(datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc))


# -- the handlers -------------------------------------------------------------------------------


def build_surface(session: Session, *, clock: Callable[[], datetime] | None = None) -> Surface:
    """A surface with every handler this build can honestly provide.

    Read it as the list of what works: an operation absent here is one `Surface.unimplemented()`
    reports, and the report is the truth rather than a placeholder.
    """
    surface = Surface(clock=clock or session.clock)
    for handler in handlers(session):
        surface.register(handler)
    return surface


def handlers(session: Session) -> tuple[Handler, ...]:
    return (
        Handler("workspace.open", lambda p, t: workspace_open(session, p)),
        Handler("dataset.load", lambda p, t: dataset_load(session, p)),
        Handler("dataset.describe", lambda p, t: dataset_describe(session, p)),
        Handler("dataset.parts", lambda p, t: dataset_parts(session, p)),
        Handler("field.declareUnit", lambda p, t: field_declare_unit(session, p)),
        Handler("field.statistics", lambda p, t: field_statistics(session, p)),
        Handler("view.create", lambda p, t: item_create(session, "views", p)),
        Handler("view.update", lambda p, t: item_update(session, "views", "viewId", p)),
        Handler("report.create", lambda p, t: item_create(session, "reports", p)),
        Handler("report.export", lambda p, t: report_export(session, p)),
        Handler("report.provenance", lambda p, t: report_provenance(session, p)),
        Handler("system.capabilities", lambda p, t: system_capabilities(session)),
        Handler("system.protocols", lambda p, t: Effect("対応する版です", value={"versions": [PROTOCOL_VERSION]})),
    )


def workspace_open(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    location = Path(str(parameters["path"]))
    try:
        loaded = load_workspace(location)
    except WorkspaceFileError as error:
        return refused(str(error))

    before = (session.workspace, session.workspace_path, dict(session.datasets), dict(session.revisions))
    session.workspace, session.workspace_path = loaded, location
    # A dataset belongs to a case of a workspace; the one that was open is no longer, so neither are
    # they. Kept for undo, which puts the previous workspace and its datasets back together.
    session.datasets = {}
    session.revisions = {}

    unresolved = [
        resolution.case_id
        for case, _ in walk_cases(loaded.cases)
        for resolution in (sources.resolve_case(case, relative_to=location.parent),)
        if not resolution.is_resolved
    ]

    def undo() -> None:
        session.workspace, session.workspace_path, session.datasets, session.revisions = before

    return Effect(
        f"{location.name} を開きました",
        changed=(loaded.identifier,),
        value={
            "workspaceId": loaded.identifier,
            "formatVersion": loaded.format_version,
            "unresolvedCases": unresolved,
        },
        undo=undo,
    )


def dataset_load(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    case_id = str(parameters["caseId"])
    if find_case(workspace.cases, case_id) is None:
        return refused(f"ケース '{case_id}' はこのワークスペースにありません")
    paths = [Path(str(one)) for one in parameters["filePaths"]]
    if len(paths) != 1:
        # Stated rather than silently taking the first: a case of several files is a real thing
        # (an Exodus run split by step) and this build does not yet read one as one dataset.
        return refused(
            f"この版は 1 回の読み込みで 1 ファイルを扱います（{len(paths)} 件が指定されました）。"
            "複数ファイルのケースは後の段で扱います"
        )
    path = paths[0]
    try:
        case = reader.read_case(path)
    except (reader.UnsupportedFormatError, reader.UnreadableFileError) as error:
        return refused(str(error))
    level, gaps = reader.support_level(path)
    dataset_id = session.issue("dataset")
    loaded = Loaded(
        case=case, path=path, case_id=case_id, support_level=level,
        gaps=tuple(gap for gap in gaps.split("; ") if gap),
    )
    session.datasets[dataset_id] = loaded

    seen: dict[str, Field] = {}
    for dataset in loaded.datasets():
        for name, field in dataset.fields.items():
            seen.setdefault(name, field)
    fields = [
        {"name": name, "association": ASSOCIATION_WORD[field.association], "unit": field.unit}
        for name, field in seen.items()
    ]

    def undo() -> None:
        session.datasets.pop(dataset_id, None)

    warnings: tuple[str, ...] = ()
    if case.is_partial:
        warnings = (f"ケースは不完全です：{case.describe()}",)
    return Effect(
        f"{path.name} を読み込みました（{len(case.present)} パート）",
        changed=(dataset_id,),
        value={
            "datasetId": dataset_id,
            "fields": fields,
            "supportLevel": level.lower(),
            "gaps": list(loaded.gaps),
        },
        warnings=warnings,
        undo=undo,
    )


def dataset_describe(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    loaded = session.loaded(str(parameters["datasetId"]))
    if isinstance(loaded, Result):
        return loaded
    datasets = loaded.datasets()
    axis = loaded.case.contents.axis
    result_axis: dict[str, Any] = {"kind": axis.kind.value, "unit": None}
    if axis.positions is not None:
        result_axis["positions"] = [float(position) for position in axis.positions]
        result_axis["count"] = len(axis.positions)
    return Effect(
        "データセットの概要です",
        value={
            "pointCount": sum(dataset.point_count for dataset in datasets),
            "cellCount": sum(dataset.cell_count for dataset in datasets),
            "boundsM": bounds_m(datasets),
            "partial": loaded.case.is_partial,
            "resultAxis": result_axis,
        },
    )


def dataset_parts(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    loaded = session.loaded(str(parameters["datasetId"]))
    if isinstance(loaded, Result):
        return loaded
    parts: list[dict[str, Any]] = []
    for part in loaded.case.parts:
        if part.dataset is None:
            # An absent part is listed as absent, with nothing counted for it (ingest/AC-027).
            parts.append({"name": part.label, "type": "absent", "pointCount": 0, "cellCount": 0})
            continue
        parts.append({
            "name": part.label,
            "type": "part",
            "pointCount": part.dataset.point_count,
            "cellCount": part.dataset.cell_count,
            "boundsM": bounds_m([part.dataset]),
        })
    return Effect("パートの一覧です", value={"parts": parts})


def field_declare_unit(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    dataset_id = str(parameters["datasetId"])
    loaded = session.loaded(dataset_id)
    if isinstance(loaded, Result):
        return loaded
    name = str(parameters["fieldName"])
    symbol = str(parameters["unitSymbol"])
    try:
        known_unit(symbol)
    except UndeclaredUnitError as error:
        return refused(str(error))
    holders = loaded.holders(name)
    if not holders:
        return refused(f"'{name}' というフィールドはこのデータセットにありません")

    before = {id(part): part.dataset.fields[name] for part in holders if part.dataset is not None}
    previous = loaded.declared_units.get(name)
    for part in holders:
        assert part.dataset is not None
        part.dataset.fields[name] = part.dataset.fields[name].declared(symbol)
    loaded.declared_units[name] = symbol

    def undo() -> None:
        for part in holders:
            assert part.dataset is not None
            part.dataset.fields[name] = before[id(part)]
        if previous is None:
            loaded.declared_units.pop(name, None)
        else:
            loaded.declared_units[name] = previous

    return Effect(
        f"'{name}' の単位を {symbol} と宣言しました", changed=(dataset_id,), value={}, undo=undo,
    )


def field_statistics(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    loaded = session.loaded(str(parameters["datasetId"]))
    if isinstance(loaded, Result):
        return loaded
    name = str(parameters["fieldName"])
    if parameters.get("region"):
        return refused("領域を限った統計はこの版では扱いません。ケース全体で求めます")
    holders = loaded.holders(name)
    if not holders:
        return refused(f"'{name}' というフィールドはこのデータセットにありません")
    fields = [part.dataset.fields[name] for part in holders if part.dataset is not None]
    association = fields[0].association
    if association is Association.INTEGRATION_POINT:
        return refused(
            f"'{name}' は積分点の値です。平均や合計には求積則の重みが要り、ファイルにはありません（XC-123）"
        )
    unit = fields[0].unit
    digits = min(field.significant_digits for field in fields)
    values = np.concatenate([field.values for field in fields])
    caveats: frozenset[Caveat] = frozenset()
    if loaded.case.is_partial:
        caveats = caveats | {Caveat.PARTIAL_DATASET}
    scope = f"ケース全体（{len(holders)} パート）"

    maximum = loaded.case.maximum(name)
    minimum = as_reported(
        summarise(
            values, reduction=Reduction.MIN, association=association, scope=scope,
            weighting=Weighting.NONE, unit=unit,
        ),
        digits=digits, formula=f"min({name})", caveats=caveats,
    )
    mean, weighting = weighted_mean(holders, name, values, association, scope, unit, digits, caveats)

    return Effect(
        f"'{name}' の統計です",
        value={
            "minimum": reported(minimum),
            "maximum": reported(maximum),
            "mean": reported(mean),
            "missingCount": int(np.count_nonzero(np.isnan(values))),
            "association": ASSOCIATION_WORD[association],
            "reduction": "min / max / mean",
            "weighting": weighting.value,
            "scope": scope,
        },
    )


def weighted_mean(
    holders: list[Part], name: str, values: np.ndarray, association: Association,
    scope: str, unit: str | None, digits: int, caveats: frozenset[Caveat],
) -> tuple[ReportedValue, Weighting]:
    """The mean weighted as INV-017 asks, or a stated absence - never an arithmetic mean under the
    weighted label, and never the weighted label over an arithmetic mean."""
    weighting = Weighting.VOLUME if association is Association.CELL else Weighting.DUAL_VOLUME
    formula = f"mean({name})"
    try:
        weights = np.concatenate([
            field_weights.cell_volumes(part.dataset) if association is Association.CELL
            else field_weights.point_weights(part.dataset)
            for part in holders if part.dataset is not None
        ])
    except Exception as error:  # noqa: BLE001 - the toolkit may be absent or the mesh degenerate
        return (
            ReportedValue.unavailable(
                f"重みを求められません：{str(error)[:200]}。重みなしの平均を加重平均の名で出すことはしません（INV-017）",
                unit=unit, digits=digits, provenance=Provenance.COMPUTED, caveats=caveats, formula=formula,
            ),
            weighting,
        )
    if not np.isfinite(weights).all() or float(weights.sum()) <= 0.0:
        return (
            ReportedValue.unavailable(
                "重みの合計が 0 です：体積を持たないメッシュ（面メッシュ）には面積加重が要り、"
                "この版はまだ扱いません。重みなしの平均を代わりに出すことはしません（INV-017）",
                unit=unit, digits=digits, provenance=Provenance.COMPUTED, caveats=caveats, formula=formula,
            ),
            weighting,
        )
    try:
        summary = summarise(
            values, reduction=Reduction.MEAN, association=association, scope=scope,
            weights=weights, weighting=weighting, unit=unit,
        )
    except SummaryError as error:
        return (
            ReportedValue.unavailable(
                str(error), unit=unit, digits=digits, provenance=Provenance.COMPUTED,
                caveats=caveats, formula=formula,
            ),
            weighting,
        )
    return as_reported(summary, digits=digits, formula=formula, caveats=caveats), weighting


def item_create(session: Session, kind: str, parameters: Mapping[str, Any]) -> Effect | Result:
    workspace = session.open_workspace(str(parameters["workspaceId"]))
    if isinstance(workspace, Result):
        return workspace
    if parameters.get("sourceTemplateId") is not None:
        # Accepting the parameter and ignoring it would create an item that claims no template when
        # the caller named one. Refused until templates are built (XC-257 sets them aside).
        return refused("テンプレートからの作成はこの版では扱いません。definition だけで作ってください")
    stated = parameters["definition"]
    if not isinstance(stated, Mapping):
        return refused(f"definition はオブジェクトです（{type(stated).__name__} が渡されました）")
    definition = dict(stated)
    singular = kind[:-1]
    item_id = session.issue(singular)
    definition.setdefault("id", item_id)
    name = str(definition.get("name") or item_id)
    try:
        items.create(workspace.raw, kind, item_id, name, definition)
    except ItemError as error:
        return refused(str(error))
    session.revisions[item_id] = 1

    def undo() -> None:
        collection = workspace.raw.setdefault("workspaceItems", {}).get(kind, [])
        collection[:] = [one for one in collection if one.get("id") != item_id]
        session.revisions.pop(item_id, None)

    return Effect(
        f"{items.COLLECTIONS[kind]}に '{name}' を作りました",
        changed=(item_id,),
        value={"id": item_id, "revision": 1},
        undo=undo,
    )


def item_update(session: Session, kind: str, key: str, parameters: Mapping[str, Any]) -> Effect | Result:
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    item_id = str(parameters[key])
    stated = parameters["definition"]
    if not isinstance(stated, Mapping):
        return refused(f"definition はオブジェクトです（{type(stated).__name__} が渡されました）")
    try:
        item = items.find(workspace.raw, kind, item_id)
    except ItemError as error:
        return refused(str(error))
    before = dict(item["definition"])
    previous = session.revisions.get(item_id, 1)
    items.edit(workspace.raw, kind, item_id, dict(stated))
    session.revisions[item_id] = previous + 1

    def undo() -> None:
        items.edit(workspace.raw, kind, item_id, before)
        session.revisions[item_id] = previous

    return Effect(
        f"'{item_id}' を更新しました",
        changed=(item_id,),
        value={"id": item_id, "revision": previous + 1},
        undo=undo,
    )


def rows_for_report(session: Session, definition: Mapping[str, Any]) -> tuple[dict[str, list[ValueRow]], list[Loaded]]:
    """The values each block shows, computed by MOD-004 and arranged here (INV-001).

    A value table names fields; each field's maximum across the case is a row. The dataset is the
    one loaded for the case the block's view belongs to, or - while a report has no way to name a
    case (CT-006 names workspaces) - the one dataset loaded in this session. More than one loaded
    and no way to choose is refused rather than guessed.
    """
    involved: list[Loaded] = []
    rows: dict[str, list[ValueRow]] = {}
    for index, block in enumerate(definition.get("blocks", []) or []):
        if block.get("kind") != "valueTable":
            continue
        names = [str(name) for name in block.get("fields", []) or []]
        if not names:
            continue
        candidates = list(session.datasets.values())
        if len(candidates) != 1:
            raise ReportError(
                f"値の表はデータセットを一つ要りますが、{len(candidates)} 件が読み込まれています。"
                "どれを使うかを推測はしません"
            )
        loaded = candidates[0]
        if loaded not in involved:
            involved.append(loaded)
        key = str(block.get("viewId") or block.get("graphId") or index)
        rows[key] = [
            ValueRow(label=f"{name} の最大", value=loaded.case.maximum(name)) for name in names
        ]
    return rows, involved


def report_export(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    report_id = str(parameters["reportId"])
    path = Path(str(parameters["path"]))
    if path.exists():
        return refused(f"{path} はすでにあります。この版は上書きしません — 別の場所を指定してください")
    try:
        item = items.find(workspace.raw, "reports", report_id)
    except ItemError as error:
        return refused(str(error))
    definition = item["definition"]
    try:
        rows, involved = rows_for_report(session, definition)
        document = build_document(definition, rows_for=rows, provenance=session.provenance_of(involved))
    except ReportError as error:
        return refused(str(error))
    # No font ships yet (OPEN-032): every Japanese label is unrepresentable and the document says so
    # itself, which is XC-254's rule and XC-257's stated state of the prototype.
    capability = html.Capability()
    try:
        export = html.write(document, path, capability=capability, accepted=True)
    except ReportError as error:
        return refused(str(error))

    def undo() -> None:
        if path.exists():
            path.unlink()

    return Effect(
        export.describe(),
        changed=(report_id,),
        value={
            "path": str(export.path),
            "bytes": export.bytes,
            "reductions": [],
            "omitted": list(export.stated),
        },
        undo=undo,
    )


def report_provenance(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    if parameters.get("exportedPath"):
        return refused("書き出し済みファイルから来歴を読み戻すことは、この版では扱いません。reportId を指定してください")
    report_id = parameters.get("reportId")
    if not report_id:
        return refused("reportId か exportedPath のどちらかが要ります")
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    try:
        item = items.find(workspace.raw, "reports", str(report_id))
    except ItemError as error:
        return refused(str(error))
    try:
        _, involved = rows_for_report(session, item["definition"])
    except ReportError as error:
        return refused(str(error))
    provenance = session.provenance_of(involved)
    return Effect(
        "来歴です",
        value={
            "workspaceId": provenance.workspace_id,
            "caseIds": list(provenance.case_ids),
            "sources": [
                {"path": source.path, "modifiedUtc": source.modified.utc} for source in provenance.sources
            ],
            "declaredUnits": dict(provenance.declared_units),
            "productVersion": provenance.product_version,
        },
    )


def system_capabilities(session: Session) -> Effect:
    native, detail = session.native_offscreen()
    availability = probe(
        {
            Backend.NATIVE_OFFSCREEN: native,
            Backend.WEB_GL2: False,
            Backend.WEBGPU: False,
            Backend.OMNIVERSE: False,
        },
        details={
            Backend.NATIVE_OFFSCREEN: detail,
            Backend.WEB_GL2: "ブラウザ側で判定します（エンジンからは分かりません）",
            Backend.WEBGPU: "ブラウザ側で判定します（エンジンからは分かりません）",
            Backend.OMNIVERSE: "同梱していません（XC-250）",
        },
    )
    formats = []
    for suffix in reader.supported_suffixes():
        level, _ = reader.support_level(f"probe{suffix}")
        formats.append({"format": suffix.lstrip("."), "level": level.lower()})
    return Effect(
        "この機械でできることです",
        value={
            "machineClass": session.machine_class.value,
            "renderers": [
                {"backend": one.backend.value, "available": one.available, "requires": REQUIRES[one.backend]}
                for one in availability
            ],
            "formats": formats,
        },
    )
