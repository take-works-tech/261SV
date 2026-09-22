"""The composition root: production handlers on the command surface (XC-257, step 2).

Until 2026-09-18 `Surface.register` had no caller under `src/`. The vocabulary, the readers, the
reductions and the document writer all existed as tested library code, and every one of the 61
catalogue operations was answered 「カタログにありますが、このビルドに実装がありません」. This
module is what joins them: one `Session` holding what the engine has in memory, and `build_surface`,
which registers a handler for each operation this build can honestly perform.

Every operation on XC-257's path is registered here. Those it took a step to earn say so in their
handler: `view.render` arrived with step 3 and draws through the native offscreen path; `dataset.probe`
with step 4 and reads one value off the full dataset through the surface that was picked. What the
build still cannot do inside an operation is refused by name rather than approximated.

Every handler answers in the shape CT-003 states and is held to it by the surface (RESULT_FIELDS,
REPORTED_VALUES). A caller's mistake - a case that is not there, a file that cannot be read, a unit
this product does not know - comes back as a **refusal** with the reason; only a defect in this
module comes back as a failure, because that is the difference the two words mark (CT-002).
"""

from __future__ import annotations

import getpass
import os
import platform
import secrets
from dataclasses import dataclass, field as dataclass_field, replace
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from domain_core.association import Association
from domain_core.case_contents import AxisKind, PositionError, ResultAxis, ResultPosition, axis_word
from domain_core.locale_format import bytes_as_text
from domain_core.dataset import Dataset, Field
from domain_core.dimension import DIMENSIONLESS as NO_DIMENSION, parse_symbol
from domain_core.identifiers import location_of
from domain_core.parts import LoadedCase, Part
from domain_core.recorded_time import STORED_FORMAT, RecordedTime, from_stored, record as record_time, record_instant
from domain_core.reported_value import DIMENSIONLESS, Caveat, Provenance, ReportedValue
from domain_core.units import UndeclaredUnitError, unit as known_unit
from engine import reader, sample
from engine.code_page import active_code_page
from domain_core.os_paths import for_os, for_people
from engine.analysis import derived, nodal
from engine.completeness import FileIncomplete, ResultsLost
from engine.analysis import weights as field_weights
from engine.analysis.expression import Value
from engine.analysis.summary import Reduction, Summary, SummaryError, Weighting, summarise
from engine.graph import definition as graph_definition
from engine.graph import series as graph_series
from engine.limits import MachineClass
from engine.report import document as document_module, html
from engine.report.document import (
    Provenance as ReportProvenance,
    ReportError,
    SourceFile,
    ValueRow,
    build as build_document,
)
from engine.visualization import camera_path as camera_paths
from engine.visualization import pick
from engine.visualization import render as render_module
from engine.visualization.backends import REQUIRES, Backend, probe
from engine.visualization.render import Camera, Colouring, RenderError, probe_offscreen, render_view
from service.command.catalogue import PROTOCOL_VERSION
from service.command.surface import Effect, Handler, LogEntry, Permission, Result, Status, Surface
from service.egress import diagnostics
from service.egress.gate import Gate
from service.workspace import items, output, sources
from service.workspace import lock as workspace_lock
from service.workspace.lock import LockState, LockStatus
from service.workspace.document import FORMAT_VERSION, WorkspaceDocument, WorkspaceFileError, fresh as fresh_document, load as load_workspace
from service.workspace.document import WorkspaceVersionError, save as save_document
from service.workspace.hierarchy import capacity_warning as cases_capacity_warning, find as find_case, walk as walk_cases
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
    if value.missing_count:
        answer["missingCount"] = value.missing_count
    return answer


def as_reported(summary: Summary, *, digits: int, formula: str, caveats: frozenset[Caveat]) -> ReportedValue:
    """A `Summary` as a `ReportedValue`: digits and provenance attached, an absence kept as one.

    `Summary` carries the reduction, the weighting and the count; it does not carry digits or a
    provenance, because MOD-004 does not know what the field was stored as. This is the seam XC-257
    named as missing - until it existed, no reduction reached a document except by hand.
    """
    if summary.value is None:
        absent = ReportedValue.unavailable(
            summary.unavailable or "求められません",
            unit=summary.unit, digits=digits, provenance=Provenance.COMPUTED,
            caveats=caveats, formula=formula,
        )
        return replace(absent, missing_count=summary.skipped) if summary.skipped else absent
    if summary.unit is None:
        caveats = caveats | {Caveat.UNDECLARED_UNIT}
    # What the summary left out travels with the number (XC-303).
    return ReportedValue(
        value=summary.value, unit=summary.unit, digits=digits,
        provenance=Provenance.COMPUTED, caveats=caveats, formula=formula,
    ).with_missing(summary.skipped)


def bounds_m(datasets: list[Dataset]) -> dict[str, list[float]]:
    points = np.concatenate([dataset.points_m for dataset in datasets])
    return {
        "minM": [float(value) for value in points.min(axis=0)],
        "maxM": [float(value) for value in points.max(axis=0)],
    }


# -- what the engine holds ---------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Derivation:
    """One derived field's rule: what it was made from and how (XC-282). A rule, so that it is made
    again on every step of the case read after it (XC-283)."""

    source: str
    quantity: derived.Quantity
    component: str | None
    as_tensor: bool


@dataclass(slots=True)
class Loaded:
    """One loaded dataset: the case as read, where it came from, and what a person declared since.

    `case` is the file's first step, what `dataset.load` read. Another step is read from the file
    when a position asks for it (`at`), with this dataset's declared units and derived fields made
    again on it, and **the last step asked for is kept beside the first** - a timeline is scrubbed
    one step at a time, and keeping every step visited would grow without a bound LIM-001 sets
    (XC-283). A declaration or a derivation drops the kept step, so it is read again with the rule
    applied rather than patched.
    """

    case: LoadedCase
    path: Path
    case_id: str
    support_level: str
    gaps: tuple[str, ...]
    declared_units: dict[str, str] = dataclass_field(default_factory=dict)
    derivations: list[Derivation] = dataclass_field(default_factory=list)
    #: The file as it was when the first step was read - size and modification time of every file
    #: involved. Another step is read only from that same file; one that changed since is refused
    #: rather than mixed with what is in memory (ingest/AC-045, XC-284).
    fingerprint: reader.Fingerprint = dataclass_field(default_factory=dict)
    _other: tuple[int, LoadedCase] | None = None

    @property
    def axis(self) -> ResultAxis:
        return self.case.contents.axis

    def holders(self, field_name: str, case: LoadedCase | None = None) -> list[Part]:
        return [
            part for part in (case or self.case).present
            if part.dataset is not None and field_name in part.dataset.fields
        ]

    def datasets(self, case: LoadedCase | None = None) -> list[Dataset]:
        return [part.dataset for part in (case or self.case).present if part.dataset is not None]

    def at(self, position: ResultPosition) -> LoadedCase:
        """The case at `position`: the first step as loaded, or another read from the file now."""
        if position.step == 0:
            return self.case
        if self._other is not None and self._other[0] == position.step:
            return self._other[1]
        case = reader.read_case(self.path, step=position.step, expected=self.fingerprint or None)
        for name, symbol in self.declared_units.items():
            for part in self.holders(name, case):
                assert part.dataset is not None
                part.dataset.fields[name] = part.dataset.fields[name].declared(symbol)
        for rule in self.derivations:
            derive_into(self, case, rule)
        self._other = (position.step, case)
        return case

    def forget_other(self) -> None:
        self._other = None


def derive_into(loaded: Loaded, case: LoadedCase, rule: Derivation) -> list[derived.Derived]:
    """Make a derived field on every part of `case` that carries the source, at the source's
    precision and with its unit (XC-282). Raises `DerivedError` where the source is the wrong shape."""
    made: list[derived.Derived] = []
    for part in loaded.holders(rule.source, case):
        assert part.dataset is not None
        field = part.dataset.fields[rule.source]
        results = derived.derive(field, rule.quantity, component=rule.component, as_tensor=rule.as_tensor)
        precision = field.values.dtype if np.issubdtype(field.values.dtype, np.floating) else np.dtype(np.float64)
        for one in results:
            part.dataset.fields[one.name] = Field(
                name=one.name, association=field.association, values=one.values.astype(precision), unit=field.unit,
            )
            if field.unit is not None:
                loaded.declared_units[one.name] = field.unit
        made = list(results)
    return made


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
    """Whether the native toolkit can render offscreen here, found by rendering in a child process.

    Not by importing: an import proves the module is present, and on a machine with no display the
    toolkit segfaults in `Render()` rather than refusing (E-194). The child process is what keeps that
    from being the engine's segfault, and its answer is what `system.capabilities` reports and what
    `view.render` checks before it draws.
    """
    return probe_offscreen()


def _this_host() -> str:
    # The machine's own name, without a socket: nothing outside MOD-014 imports a network client.
    return os.environ.get("COMPUTERNAME") or platform.node()


def _this_user() -> str:
    for name in ("USERNAME", "USER"):
        if os.environ.get(name):
            return os.environ[name]
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return "unknown"


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
    #: The diagnostic log (XC-126, XC-263). Memory-only unless the transport was given a directory.
    log: diagnostics.Log = dataclass_field(default_factory=diagnostics.Log)
    workspace: WorkspaceDocument | None = None
    workspace_path: Path | None = None
    datasets: dict[str, Loaded] = dataclass_field(default_factory=dict)
    revisions: dict[str, int] = dataclass_field(default_factory=dict)
    handles: HandleStore = dataclass_field(default=None)  # type: ignore[assignment]
    #: The one door out (MOD-014, XC-106). This build injects no transport into it, so nothing can
    #: leave and every attempt is a refusal in the audit; `system.capabilities` says so and
    #: `system.audit` shows it, which is how a person checks it rather than believes it (#317).
    gate: Gate = dataclass_field(default=None)  # type: ignore[assignment]
    #: Who this session is for the workspace lock (XC-241, XC-269): the host and the user the lock
    #: names, so a second window can be told whose it is.
    host: str = dataclass_field(default_factory=_this_host)
    user: str = dataclass_field(default_factory=_this_user)
    #: The lock on the open document and the document it is for; None until one is open.
    lock: LockStatus | None = None
    lock_path: Path | None = None
    #: The support bundle's list as last shown in this session (AC-008, XC-302): a bundle is made
    #: from it, and from nothing that was not shown.
    support_manifest: diagnostics.Manifest | None = None

    _offscreen: tuple[bool, str] | None = None

    def __post_init__(self) -> None:
        if self.handles is None:
            self.handles = HandleStore(self.clock)
        if self.gate is None:
            self.gate = Gate(clock=self.clock, log=self.log)

    def offscreen(self) -> tuple[bool, str]:
        """The offscreen probe's answer, asked once per session: a child process is not free."""
        if self._offscreen is None:
            self._offscreen = self.native_offscreen()
        return self._offscreen

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

    def recorded_modified(self, one: Loaded) -> RecordedTime:
        """When a source changed, as the document recorded it when the file was read - the file the
        numbers came from, with the offset of whoever recorded it (XC-266). From the file itself,
        with this session's offset, only where the document holds no record of it."""
        if self.workspace is not None:
            found = find_case(self.workspace.cases, one.case_id)
            base = self.workspace_path.parent if self.workspace_path else one.path.parent
            entry = sources.find_source(found[0], one.path, relative_to=base) if found else None
            if entry is not None and isinstance(entry.get("modified"), Mapping):
                return from_stored(entry["modified"])
        return modified_time(one.path, self.clock())

    @property
    def read_only(self) -> bool:
        """Whether the open document may not be written back: somebody else holds its lock (XC-241)."""
        return self.lock is not None and not self.lock.may_edit

    def take_workspace(self, path: Path, *, take_over: bool = False) -> LockStatus:
        """Take the document's lock for this session, or learn who has it (XC-269).

        A lock this process already holds is ours - a second open of the same document in one session
        is one editor, not two. Any lock held on another document is released first. A stale or
        unreadable lock is taken over only when asked (`take_over`), and a live holder's never.
        """
        if self.lock_path is not None and self.lock_path != path:
            self.release_workspace()
        who = {"process_id": os.getpid(), "host": self.host, "user": self.user, "at": record_time(self.clock())}
        status = workspace_lock.take(path, **who)
        ours = (
            status.state is LockState.HELD
            and status.holder is not None
            and status.holder.process_id == os.getpid()
            and status.holder.host == self.host
        )
        if ours:
            status = LockStatus(LockState.FREE, holder=status.holder)
        elif take_over and status.state in (LockState.STALE, LockState.UNREADABLE):
            status = workspace_lock.take_over(path, **who)
        self.lock, self.lock_path = status, path
        return status

    def release_workspace(self) -> None:
        """Give the lock back if it was ours: when another document is opened, and when the engine
        stops. A crash leaves it, and the next open finds it stale and says so (XC-241)."""
        if self.lock_path is not None and self.lock is not None and self.lock.may_edit:
            workspace_lock.release(self.lock_path, process_id=os.getpid(), host=self.host)
        self.lock, self.lock_path = None, None

    def provenance_of(self, involved: list[Loaded]) -> ReportProvenance:
        """The trust content of a deliverable, from what this session knows first-hand."""
        workspace = self.workspace
        return ReportProvenance(
            workspace_id=workspace.identifier if workspace is not None else "",
            case_ids=tuple(dict.fromkeys(one.case_id for one in involved)),
            sources=tuple(
                SourceFile(path=str(one.path), modified=self.recorded_modified(one)) for one in involved
            ),
            declared_units={
                name: symbol for one in involved for name, symbol in one.declared_units.items()
            },
            product_version=product_version(),
            produced=record_time(self.clock()),
        )


def modified_time(path: Path, where: datetime) -> RecordedTime:
    """A file's modification time, recorded with the offset of whoever records it (XC-266): the
    file's own zone no filesystem keeps."""
    return record_instant(datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc), where=where)


# -- the handlers -------------------------------------------------------------------------------


def log_entry(session: Session, entry: LogEntry) -> None:
    """One command's outcome into the diagnostic log: the operation, who asked, how it went, and the
    reason if it was refused - names and outcomes, never a value (XC-126). A refusal is a warning and
    a failure an error, so a log read at WARNING is the list of what went wrong."""
    level = (
        diagnostics.Level.ERROR if entry.status is Status.FAILED
        else diagnostics.Level.WARNING if entry.status is Status.REFUSED
        else diagnostics.Level.INFO
    )
    session.log.record(
        level,
        "command",
        operation=entry.operation,
        origin=entry.origin.value,
        status=entry.status.value,
        reason=(entry.reason[:200] if entry.reason else None),
        undoId=entry.undo_id,
        dryRun=entry.dry_run,
    )
    # What the answer warned about is a notice a person may dismiss, and the log is where a
    # dismissed notice is found again (XC-286): one warning line each, the sentence as said.
    for warning in entry.warnings:
        session.log.record(
            diagnostics.Level.WARNING, "warning", operation=entry.operation, origin=entry.origin.value,
            text=warning[:200],
        )


def build_surface(session: Session, *, clock: Callable[[], datetime] | None = None) -> Surface:
    """A surface with every handler this build can honestly provide.

    Read it as the list of what works: an operation absent here is one `Surface.unimplemented()`
    reports, and the report is the truth rather than a placeholder.
    """
    surface = Surface(clock=clock or session.clock, on_entry=lambda entry: log_entry(session, entry))
    for handler in handlers(session):
        surface.register(handler)
    # The handlers that read the surface itself: what it recorded and what its caps dropped, and
    # which operations it registers at all (XC-277).
    surface.register(Handler("history.list", lambda p, t: history_list(session, surface, p)))
    surface.register(Handler("system.operations", lambda p, t: system_operations(surface)))
    return surface


def handlers(session: Session) -> tuple[Handler, ...]:
    return (
        Handler("workspace.open", lambda p, t: workspace_open(session, p)),
        Handler("workspace.create", lambda p, t: workspace_create(session, p)),
        Handler("workspace.sample", lambda p, t: workspace_sample(session, p)),
        Handler("workspace.save", lambda p, t: workspace_save(session, p)),
        Handler("dataset.inspect", lambda p, t: dataset_inspect(session, p)),
        Handler("dataset.load", lambda p, t: dataset_load(session, p)),
        Handler("dataset.describe", lambda p, t: dataset_describe(session, p)),
        Handler("dataset.parts", lambda p, t: dataset_parts(session, p)),
        Handler("field.declareUnit", lambda p, t: field_declare_unit(session, p)),
        Handler("field.statistics", lambda p, t: field_statistics(session, p)),
        Handler("field.derive", lambda p, t: field_derive(session, p)),
        Handler("view.create", lambda p, t: item_create(session, "views", p)),
        Handler("view.update", lambda p, t: item_update(session, "views", "viewId", p)),
        Handler("view.get", lambda p, t: item_get(session, "views", "viewId", p)),
        Handler("graph.create", lambda p, t: item_create(session, "graphs", p)),
        Handler("graph.update", lambda p, t: item_update(session, "graphs", "graphId", p)),
        Handler("graph.get", lambda p, t: item_get(session, "graphs", "graphId", p)),
        Handler("graph.data", lambda p, t: graph_data(session, p)),
        Handler("view.render", lambda p, t: view_render(session, p)),
        Handler("dataset.probe", lambda p, t: dataset_probe(session, p)),
        Handler("view.pick", lambda p, t: view_pick(session, p)),
        Handler("report.create", lambda p, t: item_create(session, "reports", p)),
        Handler("report.update", lambda p, t: item_update(session, "reports", "reportId", p)),
        Handler("report.get", lambda p, t: item_get(session, "reports", "reportId", p)),
        Handler("report.export", lambda p, t: report_export(session, p)),
        Handler("report.provenance", lambda p, t: report_provenance(session, p)),
        Handler("system.capabilities", lambda p, t: system_capabilities(session)),
        Handler("system.audit", lambda p, t: system_audit(session, p)),
        Handler("system.log", lambda p, t: system_log(session, p)),
        Handler("system.supportManifest", lambda p, t: system_support_manifest(session, p)),
        Handler("system.supportBundle", lambda p, t: system_support_bundle(session, p)),
        Handler("output.list", lambda p, t: output_list(session, p)),
        Handler("output.plan", lambda p, t: output_plan(session, p)),
        # Deleting files is destructive and needs the caller's say-so on the envelope (CT-002);
        # what it deletes is what `output.plan` showed, and nothing else (XC-268).
        Handler("output.prune", lambda p, t: output_prune(session, p), needs=frozenset({Permission.DESTRUCTIVE})),
        Handler("system.protocols", lambda p, t: Effect("対応する版です", value={"versions": [PROTOCOL_VERSION]})),
    )


def workspace_open(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    # In the operating system's form from here on (XC-294): what is derived from it - the lock, the
    # output folder, the sources' relative paths - reaches the file system the same way.
    location = for_os(str(parameters["path"]))
    try:
        loaded = load_workspace(location)
    except WorkspaceFileError as error:
        return refused(str(error))
    # A `.writing` beside the document is a save that did not finish (XC-055 writes there and moves
    # into place). It is never a document, so it is removed - and said, because an interrupted save
    # is a thing the person may want to know happened (#313).
    interrupted = location.with_name(location.name + ".writing")
    warnings: tuple[str, ...] = ()
    if interrupted.exists():
        try:
            interrupted.unlink()
            warnings = (f"{interrupted.name} がありました：前回の保存は途中で終わっています。開いたのは最後に完了した保存です",)
        except OSError as error:
            warnings = (f"{interrupted.name} を消せませんでした：{error}",)

    # A document holding more items than LIM-016 allows is opened whole and said, not refused: it is
    # the person's work, and the limit is on what this build adds to it (XC-265).
    over = items.capacity_warning(loaded.raw)
    if over is not None:
        warnings += (over,)
    # The same for cases (LIM-005): opened whole and said, never refused (XC-306).
    crowded = cases_capacity_warning(loaded.cases)
    if crowded is not None:
        warnings += (crowded,)

    # A version-4 document was lifted to this build's shape on the way in (CT-001 5.0.0, XC-266).
    # Said, because the next save writes it as 5.0.0, and a file that changes version is a thing a
    # person shares with somebody on the version before.
    if loaded.migrated_from:
        warnings += (
            f"{location.name} は版 {loaded.migrated_from} の文書です。この版の形 {FORMAT_VERSION} に読み替えました："
            "記録時のゾーンを持たない時刻は不明として保持し、次に保存すると "
            f"{FORMAT_VERSION} で書かれます（CT-001）",
        )

    # The document's lock, taken for this session (XC-241, XC-269). Held by somebody else, the document
    # opens read-only: the window works in memory and saving is refused naming the holder. A stale or
    # unreadable lock is taken over only when the caller says so, and a live holder's never.
    take_over = bool(parameters.get("takeOverStaleLock"))
    status = session.take_workspace(location, take_over=take_over)
    if not status.may_edit:
        warnings += (status.describe(),)
        if take_over and status.state is LockState.HELD:
            warnings += (
                "ロックを引き継ぎませんでした：持ち主のプロセスは生きている可能性があります。生きているものは決して壊しません（XC-241）",
            )

    # A dataset belongs to a case of a workspace; the one that was open is no longer, so neither are
    # they. They are **not** kept for undo: an undo closure holding every dataset of every workspace
    # a session has opened is the memory #315 is about (LIM-001 per case, times the history). The
    # undo puts the previous document back and says that its datasets need reading again.
    before = (session.workspace, session.workspace_path, dict(session.revisions))
    dropped_datasets = len(session.datasets)
    session.workspace, session.workspace_path = loaded, location
    session.datasets = {}
    session.revisions = {}

    resolutions = {
        str(case.get("id", "")): sources.resolve_case(case, relative_to=location.parent)
        for case, _ in walk_cases(loaded.cases)
    }
    unresolved = [case_id for case_id, resolution in resolutions.items() if not resolution.is_resolved]
    base = for_people(location.parent)

    def sources_of(case_id: str) -> list[dict[str, Any]]:
        # Where each recorded file is now and whether it is there, so a caller can load a case's
        # file without a second question (XC-298). The path is the plain one (XC-294).
        resolution = resolutions.get(case_id)
        if resolution is None:
            return []
        return [
            {"name": Path(one.path_relative).name, "path": str(base / one.path_relative), "present": one.is_resolved}
            for one in resolution.sources
        ]

    def undo() -> None:
        session.workspace, session.workspace_path, session.revisions = before
        session.datasets = {}
        # The previous document's lock goes with it: retaken, or found held and said.
        if session.workspace_path is not None:
            session.take_workspace(session.workspace_path)
        else:
            session.release_workspace()

    if dropped_datasets:
        warnings += (
            f"読み込んでいた {dropped_datasets} 件のデータセットは閉じました。取り消しても文書が戻るだけで、データセットは読み直しが要ります（LIM-014）",
        )
    return Effect(
        f"{location.name} を開きました",
        changed=(loaded.identifier,),
        value={
            "workspaceId": loaded.identifier,
            "formatVersion": loaded.format_version,
            "unresolvedCases": unresolved,
            "items": items_of(loaded),
            # The document's own name, or its file's where it has none, and the tags of its cases as
            # one set: what a list of workspaces shows and narrows by (XC-297).
            "name": str(loaded.raw.get("name") or location.stem),
            "tags": sorted({str(tag) for case, _ in walk_cases(loaded.cases) for tag in (case.get("tags") or [])}),
            # The cases the document holds, flattened with their parents, so a file dropped on the
            # window knows where it may go without the interface guessing a case id (XC-291).
            "cases": [
                {
                    "id": str(case.get("id", "")), "name": str(case.get("name", case.get("id", ""))),
                    **({"parentId": ancestors[-1]} if ancestors else {}),
                    "sources": sources_of(str(case.get("id", ""))),
                }
                for case, ancestors in walk_cases(loaded.cases)
            ],
            "readOnly": not status.may_edit,
            "lock": status.as_stored(workspace_lock.lock_for(location)),
        },
        warnings=warnings,
        undo=undo,
    )


def workspace_create(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """A new document at a path of the person's choosing, then opened (XC-297).

    Refused where a file is already there - this build overwrites nothing on a person's disk
    without being asked - and where the folder is not, naming which. One case, named by the caller
    or `ケース 1`, because a workspace with no case has nowhere to load a file into (XC-291). What
    comes back is the open's answer, so the caller knows the document as it would any other.
    """
    location = for_os(str(parameters["path"]))
    if location.exists():
        return refused(f"{for_people(location)} はすでにあります。上書きはしません — 別の名前か場所を選んでください")
    if not location.parent.exists():
        return refused(f"{for_people(location.parent)} というフォルダがありません。あるフォルダを選んでください")
    name = str(parameters.get("name") or location.stem)
    document = fresh_document(
        session.issue("ws"), name, created_by=product_version(),
        cases=[{"id": session.issue("case"), "name": str(parameters.get("caseName") or "ケース 1"), "children": [], "sources": []}],
    )
    try:
        save_document(document, location)
    except OSError as error:
        return refused(f"{location.name} を書けません：{error.strerror or error}")
    opened = workspace_open(session, {"path": str(parameters["path"])})
    if isinstance(opened, Result):
        return opened
    return replace(opened, summary=f"{location.name} を作って開きました")


#: What the sample's author declares about its fields (XC-003): the sample workspace is the
#: author's document, and the units are its author's declaration, made once, here.
SAMPLE_UNITS = {"stress": "Pa", "element_stress": "Pa", "displacement": "m"}
SAMPLE_NAME = "片持ち梁（サンプル）"
#: The two cases: the beam under a tip load, and under half as much again.
SAMPLE_CASES = (("荷重 100 N", ("静荷重",), 100.0), ("荷重 150 N", ("静荷重", "1.5 倍"), 150.0))


def workspace_sample(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """The shipped sample, generated where the person chose, then opened (XC-129, XC-298).

    A cantilever beam under two loads, written by this build from beam theory (engine/sample.py):
    the data folder beside the document, one file per case, the units declared by the sample's
    author. Refused where the document or its data folder already exists, because a sample a person
    changed is theirs (XC-130); a newer build writes a newer sample under another name.
    """
    location = for_os(str(parameters["path"]))
    data = location.with_name(location.stem + ".data")
    for taken in (location, data):
        if taken.exists():
            return refused(f"{for_people(taken)} はすでにあります。上書きはしません — 別の名前か場所を選んでください")
    if not location.parent.exists():
        return refused(f"{for_people(location.parent)} というフォルダがありません。あるフォルダを選んでください")
    try:
        data.mkdir()
        cases: list[dict[str, Any]] = []
        for case_name, tags, force in SAMPLE_CASES:
            file = data / f"cantilever_{int(force)}N.vtu"
            sample.write_cantilever(file, force_newton=force)
            entry = sources.record(file, relative_to=location.parent, where=session.clock())
            entry["pathAbsolute"] = str(for_people(for_os(file).resolve()))
            entry["declaredUnits"] = dict(SAMPLE_UNITS)
            cases.append({"id": session.issue("case"), "name": case_name, "tags": list(tags), "children": [], "sources": [entry]})
        save_document(fresh_document(session.issue("ws"), SAMPLE_NAME, cases=cases, created_by=product_version()), location)
    except OSError as error:
        return refused(f"サンプルを書けません：{error.strerror or error}")
    opened = workspace_open(session, {"path": str(parameters["path"])})
    if isinstance(opened, Result):
        return opened
    return replace(opened, summary=f"サンプル {location.name} を作って開きました")


def items_of(workspace: WorkspaceDocument) -> dict[str, list[dict[str, str]]]:
    """The views, graphs and reports a document holds, by id and name - what a caller needs to
    update one rather than create a second under a name the document refuses (AC-030)."""
    held = workspace.raw.get("workspaceItems") or {}
    answer: dict[str, list[dict[str, str]]] = {}
    for kind in ("views", "graphs", "reports"):
        entries = []
        for entry in held.get(kind) or []:
            if not isinstance(entry, dict):
                continue
            one = {"id": str(entry.get("id", "")), "name": str(entry.get("name", ""))}
            definition = entry.get("definition") or {}
            if kind == "views" and isinstance(definition, dict) and definition.get("datasetId"):
                one["datasetId"] = str(definition["datasetId"])
            entries.append(one)
        answer[kind] = entries
    return answer


def history_list(session: Session, surface: Surface, parameters: Mapping[str, Any]) -> Effect | Result:
    """The command history (XC-023), with what memory no longer holds said in numbers (LIM-014,
    LIM-015, #315): each entry says whether it can still be undone, and the answer says how many undo
    groups the cap dropped and how many entries fell out of the list."""
    workspace = session.open_workspace(str(parameters["workspaceId"]))
    if isinstance(workspace, Result):
        return workspace
    report = surface.history_report()
    entries = []
    for entry in report["entries"]:
        one: dict[str, Any] = {
            "operation": entry.operation,
            "origin": entry.origin.value,
            "at": entry.at.as_stored(),
            "outcome": entry.status.value,
            "undoable": bool(entry.undo_id and entry.undo_id in report["undoable"]),
        }
        if entry.undo_id:
            one["undoId"] = entry.undo_id
        entries.append(one)
    return Effect(
        f"履歴 {len(entries)} 件",
        value={
            "entries": entries,
            "undoLimit": report["undoLimit"],
            "undoDropped": report["undoDropped"],
            "historyLimit": report["historyLimit"],
            "omitted": report["omitted"],
        },
    )


def workspace_save(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """Write the open document back, keeping the previous version beside it (CT-003, XC-055).

    What this makes true is the sentence XC-259 rests on: what was saved is intact after a crash.
    Until this existed nothing was ever saved after `workspace.open`, so every declaration, view and
    report of a session was lost when the process ended - by a crash or by quitting.
    """
    workspace = session.open_workspace(str(parameters["workspaceId"]))
    if isinstance(workspace, Result):
        return workspace
    if session.read_only and session.lock is not None:
        return refused(
            f"読み取り専用で開いています：{session.lock.describe()}。保存しません。"
            "編集するには、もう一方の窓を閉じるか、そのプロセスが終了していれば takeOverStaleLock を付けて開き直してください（XC-241、XC-269）"
        )
    target = for_os(str(parameters["path"])) if parameters.get("path") else session.workspace_path
    if target is None:
        return refused("保存先がありません：path を指定してください")
    previous = target.with_name(target.name + ".previous")
    # The version before the last one is kept as a file beside the target during this save, so the
    # undo can put it back from disk rather than from bytes held in memory for as long as the undo
    # lives (#315): a document is small, and fifty of them held for nothing is the habit to avoid.
    older = target.with_name(target.name + ".previous.older")
    if previous.exists():
        os.replace(previous, older)
    try:
        kept = save_document(workspace, target)
    except (OSError, WorkspaceVersionError) as error:
        if older.exists():
            os.replace(older, previous)
        return refused(f"保存できません：{error}")
    session.workspace_path = target

    def undo() -> None:
        # The document as it was on disk before this save comes back; what this save wrote goes.
        if kept != target and kept.exists():
            os.replace(kept, target)
            if older.exists():
                os.replace(older, previous)
        elif target.exists():
            target.unlink()

    if older.exists() and kept != target:
        # Two versions back is more than XC-055 promises; once the undo of this save is no longer
        # the newest possible one, the older file is not needed. It is removed on the next save
        # rather than tracked, because a file is what it is and a tracker is a second truth.
        pass
    return Effect(
        f"{target.name} を保存しました" + ("（直前の版を残しました）" if kept != target else ""),
        changed=(workspace.identifier,),
        value={"path": str(for_people(target)), "previousKept": str(for_people(kept)) if kept != target else None},
        undo=undo,
    )


def dataset_inspect(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """What can be said about a file before it is read (ingest/AC-032, XC-049).

    The support level is a promise this build makes about a format, and a promise is stated before
    it is relied on; so is the reader's list of what it does not read. Neither needs the file open,
    and this does not open it - a file that turns out unreadable says so at `dataset.load`.
    """
    path = for_os(str(parameters["path"]))
    level, gaps = reader.support_level(path)
    exists = path.exists()
    stat = path.stat() if exists else None
    value: dict[str, Any] = {
        "format": path.suffix.lower().lstrip("."),
        "supportLevel": level,
        "gaps": [gap for gap in gaps.split("; ") if gap],
        "sizeBytes": int(stat.st_size) if stat else 0,
        "exists": exists,
    }
    if stat is not None:
        # The file's time with this session's offset beside it (XC-266); absent rather than empty
        # where there is no file, because "" is not a time (XC-001).
        value["modified"] = modified_time(path, session.clock()).as_stored()
    # A load this build would refuse before reading - a path the format's library cannot take -
    # is said here, so a drop is refused before any load (XC-291, XC-293).
    refusal = reader.load_refusal(path)
    if refusal:
        value["refusal"] = refusal
    return Effect(f"{path.name}：{level}", value=value)


def dataset_load(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    case_id = str(parameters["caseId"])
    found_case = find_case(workspace.cases, case_id)
    if found_case is None:
        return refused(f"ケース '{case_id}' はこのワークスペースにありません")
    case_entry = found_case[0]
    paths = [for_os(str(one)) for one in parameters["filePaths"]]
    if len(paths) != 1:
        # Stated rather than silently taking the first: a case of several files is a real thing
        # (an Exodus run split by step) and this build does not yet read one as one dataset.
        return refused(
            f"この版は 1 回の読み込みで 1 ファイルを扱います（{len(paths)} 件が指定されました）。"
            "複数ファイルのケースは後の段で扱います"
        )
    path = paths[0]
    # The file's own problems - a format nothing reads, a file cut short or still being written, a
    # result the reader dropped - are refusals with the reason, never failures of this build and
    # never a dataset of part of the file (ingest/AC-022, AC-045, XC-284).
    try:
        fingerprint = reader.snapshot(path)
        case = reader.read_case(path, expected=fingerprint)
    except (reader.UnsupportedFormatError, reader.UnreadableFileError, ResultsLost, FileIncomplete) as error:
        return refused(str(error))
    level, gaps = reader.support_level(path)
    dataset_id = session.issue("dataset")
    loaded = Loaded(
        case=case, path=path, case_id=case_id, support_level=level,
        gaps=tuple(gap for gap in gaps.split("; ") if gap), fingerprint=fingerprint,
    )
    session.datasets[dataset_id] = loaded

    # The document's own record of this file, and what a person declared about it in an earlier
    # session. A unit declared before and saved is a unit found now (XC-003, XC-259); one never
    # saved is not here, and the field is as undeclared as the file left it.
    workspace_directory = (session.workspace_path.parent if session.workspace_path else path.parent)
    source_entry, source_created = sources.ensure_source(
        case_entry, path, relative_to=workspace_directory, where=session.clock(),
    )
    applied_units: dict[str, str] = {}
    for name, symbol in sources.declared_units(source_entry).items():
        for part in loaded.holders(name):
            assert part.dataset is not None
            part.dataset.fields[name] = part.dataset.fields[name].declared(symbol)
        if loaded.holders(name):
            loaded.declared_units[name] = symbol
            applied_units[name] = symbol

    seen: dict[str, Field] = {}
    for dataset in loaded.datasets():
        for name, field in dataset.fields.items():
            seen.setdefault(name, field)
    fields = [
        {
            "name": name, "association": ASSOCIATION_WORD[field.association], "unit": field.unit,
            # How many numbers each entry is: a vector or a tensor is coloured, probed and summarised
            # only through a derived quantity, and the interface has to know which fields those are.
            "components": field.components,
            # How many entries the file has no value for, so the information area can say it before
            # anyone reads a number (XC-303).
            "missingCount": field.missing_count,
        }
        for name, field in seen.items()
    ]

    def undo() -> None:
        session.datasets.pop(dataset_id, None)
        if source_created:
            case_entry.get("sources", []).remove(source_entry)

    warnings: tuple[str, ...] = ()
    if case.is_partial:
        warnings = (f"ケースは不完全です：{case.describe()}",)
    if applied_units:
        warnings += (
            "保存済みの宣言を適用しました：" + "、".join(f"{name} = {symbol}" for name, symbol in applied_units.items()),
        )
    return Effect(
        f"{path.name} を読み込みました（{len(case.present)} パート）",
        changed=(dataset_id, workspace.identifier) if source_created else (dataset_id,),
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
    """Every part the file named, present or absent, with the path the file gave it (INV-019).

    The path is the file's own hierarchy, root first; `parentId` is the same path without its last
    step, so an interface nests rows without splitting a string on a separator it did not choose.
    An absent part is listed with nothing counted for it and the reader's reason (AC-027, XC-272).
    """
    loaded = session.loaded(str(parameters["datasetId"]))
    if isinstance(loaded, Result):
        return loaded
    parts: list[dict[str, Any]] = []
    for part in loaded.case.parts:
        row: dict[str, Any] = {
            "name": part.label,
            "type": "part" if part.dataset is not None else "absent",
            "path": list(part.path),
            "pointCount": part.dataset.point_count if part.dataset is not None else 0,
            "cellCount": part.dataset.cell_count if part.dataset is not None else 0,
        }
        if part.parent_label is not None:
            row["parentId"] = part.parent_label
        if part.dataset is not None:
            row["boundsM"] = bounds_m([part.dataset])
        elif part.reason:
            row["reason"] = part.reason
        parts.append(row)
    return Effect("パートの一覧です", value={"parts": parts})


def parts_shown(loaded: Loaded, definition: Mapping[str, Any], case: LoadedCase | None = None) -> list[Part] | Result:
    """The present parts a view shows, after its `partVisibility` (CT-004, INV-019, XC-274).

    A name the dataset does not have is refused rather than skipped: a visibility written for a
    part that is not there is a definition saying something about nothing, and a picture drawn
    past it would look right. Every part hidden is refused too - an empty frame with a legend is
    a picture of nothing presented as a picture of something (XC-001).
    """
    case = case or loaded.case
    stated = definition.get("partVisibility") or {}
    if not isinstance(stated, Mapping):
        return refused(f"partVisibility はパート名から真偽値への対応です（{type(stated).__name__} が書かれています）")
    known = {part.label for part in case.parts}
    unknown = sorted(str(name) for name in stated if str(name) not in known)
    if unknown:
        return refused(
            f"partVisibility が名指したパートはこのデータセットにありません：{unknown}。"
            f"あるのは {sorted(known)} です"
        )
    shown = [part for part in case.present if stated.get(part.label, True) is not False]
    if not shown:
        return refused("すべてのパートが非表示です：描くものがありません。何も描かない絵を返す代わりに拒みます")
    return shown


#: The definition members that say what a sequence *is*, and the axis kind each one presumes.
KIND_MEMBERS = {"timeStep": AxisKind.TIME, "modeNumber": AxisKind.MODE, "frequencyHz": AxisKind.FREQUENCY}


def position_of(loaded: Loaded, definition: Mapping[str, Any]) -> ResultPosition | Result:
    """The step a view definition's `resultPosition` names on this dataset's axis (CT-004, XC-283).

    `step` is the ordinal along the declared sequence, from 0, and the one member an axis of
    undeclared kind can take. `timeStep`, `modeNumber` and `frequencyHz` each say what the
    sequence **is**, and are accepted only where the file said so - which no reader in this build
    surfaces (XC-240) - because a definition that calls the second of "0, 0.5" a time step has
    labelled a value the file did not label. A definition naming no position is at the first step.
    """
    stated = definition.get("resultPosition") or {}
    if not isinstance(stated, Mapping):
        return refused(f"resultPosition はオブジェクトです（{type(stated).__name__} が書かれています）")
    axis = loaded.axis
    step = int(stated["step"]) if "step" in stated else 0
    for member, presumed in KIND_MEMBERS.items():
        if member not in stated:
            continue
        if axis.kind is not presumed:
            return refused(
                f"resultPosition.{member} は結果軸の種類が「{axis_word(presumed)}」であると言うことになりますが、"
                f"このデータセットの軸の種類は「{axis_word(axis.kind)}」です。"
                "ステップ番号（step）で位置を指定してください（XC-240, XC-283）"
            )
        if member == "frequencyHz":
            return refused("この版に周波数軸の結果を読む読み手がありません（XC-240）")
        step = int(stated[member]) - (1 if member == "modeNumber" else 0)
    if "phaseDegrees" in stated or "sweeping" in stated:
        return refused("この版に周波数軸の結果を読む読み手がなく、位相は指定できません（XC-240）")
    try:
        return axis.at(step)
    except PositionError as error:
        return refused(str(error))


def stated_position(position: ResultPosition) -> dict[str, Any]:
    """CT-003's `resultPosition` answer: which step a value came from (view/AC-032). The unit is
    null because the file does not say what its positions are (XC-003, XC-240)."""
    return {
        "step": position.step, "count": position.count, "kind": position.kind.value,
        "value": position.value, "unit": None, "stated": position.describe(),
    }


def case_at(loaded: Loaded, position: ResultPosition) -> LoadedCase | Result:
    """The dataset at a position, or the refusal that says why it could not be read there."""
    try:
        return loaded.at(position)
    except (PositionError, reader.UnreadableFileError, ResultsLost, FileIncomplete, derived.DerivedError) as error:
        return refused(str(error))


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
    loaded.forget_other()

    # Into the document, so that the declaration survives the session once the document is saved
    # (CT-001 `declaredUnits`, #306). In memory alone it was lost on every exit.
    workspace = session.open_workspace()
    recorded_previous: str | None = None
    source_entry = None
    if not isinstance(workspace, Result):
        found_case = find_case(workspace.cases, loaded.case_id)
        if found_case is not None:
            workspace_directory = (session.workspace_path.parent if session.workspace_path else loaded.path.parent)
            source_entry, _ = sources.ensure_source(
                found_case[0], loaded.path, relative_to=workspace_directory, where=session.clock(),
            )
            recorded_previous = sources.record_unit(source_entry, name, symbol)

    def undo() -> None:
        for part in holders:
            assert part.dataset is not None
            part.dataset.fields[name] = before[id(part)]
        if previous is None:
            loaded.declared_units.pop(name, None)
        else:
            loaded.declared_units[name] = previous
        loaded.forget_other()
        if source_entry is not None:
            sources.forget_unit(source_entry, name, recorded_previous)

    changed = (dataset_id, workspace.identifier) if not isinstance(workspace, Result) else (dataset_id,)
    return Effect(
        f"'{name}' の単位を {symbol} と宣言しました", changed=changed, value={}, undo=undo,
    )


def field_derive(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """A catalogue quantity of a field, added to the loaded dataset as a scalar field (INV-020, XC-282).

    A read on the catalogue's side: the derived field lives in this session's memory beside its
    source, is made again from the file next time, and is not a document change. The answer
    carries the formula and every convention the value depended on, so a reviewer checks rather
    than trusts; the values are kept at the source's precision, because the source supports no
    more digits than it has (INV-014).
    """
    loaded = session.loaded(str(parameters["datasetId"]))
    if isinstance(loaded, Result):
        return loaded
    name = str(parameters["fieldName"])
    frame_id = parameters.get("frameId")
    if frame_id:
        return refused(
            f"フレーム '{frame_id}' はこの文書にありません。この版が報告できるのは {derived.GLOBAL_CARTESIAN} だけで、"
            "名前付きフレームはまだ作れません（INV-021, XC-122）"
        )
    stated = str(parameters["quantity"])
    try:
        quantity = derived.Quantity(stated)
    except ValueError:
        if stated in derived.NOT_BUILT:
            return refused(f"'{stated}' はカタログにありますが、この版は導出しません：{derived.NOT_BUILT[stated]}")
        return refused(
            f"'{stated}' は 15_derived_quantities のカタログにありません。"
            f"この版が導出するのは {[one.value for one in derived.Quantity]} です"
        )
    holders = loaded.holders(name)
    if not holders:
        return refused(f"'{name}' というフィールドはこのデータセットにありません")
    component = parameters.get("component")
    rule = Derivation(name, quantity, str(component) if component is not None else None, bool(parameters.get("asTensor", False)))
    try:
        made = derive_into(loaded, loaded.case, rule)
    except derived.DerivedError as error:
        return refused(str(error))
    # A derivation is a rule of this dataset: made again on every step read from now on, and the
    # step kept beside the first is dropped so it is read with the rule applied (XC-283).
    loaded.derivations.append(rule)
    loaded.forget_other()
    source = holders[0].dataset.fields[name] if holders[0].dataset is not None else None
    first = made[0]
    return Effect(
        f"'{first.name}' を導出しました（{first.formula}）",
        value={
            "fieldName": first.name,
            "fieldNames": [one.name for one in made],
            "formula": first.formula,
            "conventions": list(first.conventions),
            "association": ASSOCIATION_WORD[source.association] if source is not None else "point",
            "unit": source.unit if source is not None else None,
        },
    )


def field_statistics(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """A field's minimum, maximum and mean over the case, or over one named part (INV-017).

    `region` is a part's name as `dataset.parts` lists it (GL-029, INV-019). The scope is written
    into the answer either way, so a number never travels without saying what it covered
    (view/AC-035); a part the file named and the reader could not fill has no numbers and says so.
    """
    loaded = session.loaded(str(parameters["datasetId"]))
    if isinstance(loaded, Result):
        return loaded
    name = str(parameters["fieldName"])
    # Which step the numbers are of: the one asked for, or the first, and the answer says which
    # either way (view/AC-032). A step the case does not have is refused, not rounded (AC-033).
    try:
        position = loaded.axis.at(int(parameters.get("resultPosition", 0)))
    except PositionError as error:
        return refused(str(error))
    case = case_at(loaded, position)
    if isinstance(case, Result):
        return case
    region = parameters.get("region")
    if region:
        try:
            part = case.part(str(region))
        except KeyError:
            return refused(
                f"'{region}' というパートはこのデータセットにありません。"
                f"あるのは {[one.label for one in case.parts]} です（dataset.parts の名前で指定します）"
            )
        if part.dataset is None:
            return refused(f"パート '{part.label}' は読めていません（{part.reason or '理由不明'}）。数はありません")
        if name not in part.dataset.fields:
            return refused(f"'{name}' というフィールドはパート '{part.label}' にありません")
        holders = [part]
    else:
        holders = loaded.holders(name, case)
    if not holders:
        return refused(f"'{name}' というフィールドはこのデータセットにありません")
    fields = [part.dataset.fields[name] for part in holders if part.dataset is not None]
    association = fields[0].association
    if fields[0].components != 1:
        return refused(
            f"'{name}' は {fields[0].components} 成分の場です。統計は一つの数の場に対して求めます — "
            "大きさや成分などの導出量を作ってください（field.derive, XC-282）"
        )
    if association is Association.INTEGRATION_POINT:
        return refused(
            f"'{name}' は積分点の値です。平均や合計には求積則の重みが要り、ファイルにはありません（XC-123）"
        )
    unit = fields[0].unit
    digits = min(field.significant_digits for field in fields)
    values = np.concatenate([field.values for field in fields])
    caveats: frozenset[Caveat] = frozenset()
    if case.is_partial:
        caveats = caveats | {Caveat.PARTIAL_DATASET}
    scope = f"パート {holders[0].label}" if region else f"ケース全体（{len(holders)} パート）"
    if position.count > 1:
        scope += f"・{position.describe()}"

    if region:
        # One part's own extremum, located in that part's words and named for it (INV-019).
        maximum = holders[0].dataset.maximum(name) if holders[0].dataset is not None else case.maximum(name)
        if maximum.location:
            maximum = replace(maximum, location=f"{holders[0].label}：{maximum.location}")
        if caveats:
            maximum = maximum.with_caveat(Caveat.PARTIAL_DATASET)
    else:
        maximum = case.maximum(name)
    minimum = as_reported(
        summarise(
            values, reduction=Reduction.MIN, association=association, scope=scope,
            weighting=Weighting.NONE, unit=unit,
        ),
        digits=digits, formula=f"min({name})", caveats=caveats,
    )
    mean, weighting = weighted_mean(holders, name, values, association, scope, unit, digits, caveats)

    answer: dict[str, Any] = {
        "minimum": reported(minimum),
        "maximum": reported(maximum),
        "mean": reported(mean),
        "missingCount": int(np.count_nonzero(np.isnan(values))),
        "association": ASSOCIATION_WORD[association],
        "reduction": "min / max / mean",
        "weighting": weighting.value,
        "scope": scope,
        "resultPosition": stated_position(position),
    }
    if association is Association.CELL:
        # A value at a shared node is several values: the numbers above are the element values,
        # said so, and the averaged ones travel beside them with the spread (INV-032, XC-247).
        answer["averaging"] = "unaveraged"
        try:
            both = averaged_extrema(holders, name, unit=unit, digits=digits, caveats=caveats)
        except nodal.NodalError as error:
            answer["averagingRefused"] = str(error)
        else:
            answer["averaged"] = {
                "maximum": reported(both.maximum),
                "minimum": reported(both.minimum),
                "spreadAtMaximum": reported(both.spread),
                "spreadFraction": reported(both.fraction),
                # The two figures compared only where both exist: a zero standing in for either
                # would be the substituted value XC-001 forbids, in a sentence rather than a cell.
                "disagreement": (
                    nodal.disagreement(
                        nodal.Extremum(float(maximum.value), nodal.Averaging.UNAVERAGED, 0, unit),
                        nodal.Extremum(float(both.maximum.value), nodal.Averaging.AVERAGED, 0, unit),
                    )
                    if maximum.value is not None and both.maximum.value is not None
                    else "比較できません：どちらかの最大が値なしです"
                ),
            }
    return Effect(f"'{name}' の統計です", value=answer)


@dataclass(frozen=True, slots=True)
class AveragedExtrema:
    """The nodal-averaged maximum and minimum of a cell field over the parts, each located, and the
    spread at the maximum's node - the three numbers INV-032 says travel together."""

    maximum: ReportedValue
    minimum: ReportedValue
    spread: ReportedValue
    #: The spread over the absolute average at the same node: dimensionless, unit 1, and a stated
    #: absence where the average is zero (a fraction of nothing is not perfect agreement).
    fraction: ReportedValue


def averaged_extrema(
    holders: list[Part], name: str, *, unit: str | None, digits: int, caveats: frozenset[Caveat],
) -> AveragedExtrema:
    """Average a cell field onto the nodes **part by part** and take the extrema across the parts.

    Never across parts: two parts sharing a face keep their own values at the shared nodes
    (INV-022). The location names the part and then the node in the source's own words
    (INV-023), and every value carries the averaged caveat so the label travels with the number.
    """
    found: list[tuple[Part, nodal.Extremum, nodal.Extremum]] = []
    for part in holders:
        if part.dataset is None:
            continue
        field = part.dataset.fields[name]
        found.append((
            part,
            nodal.extremum(part.dataset, field, averaging=nodal.Averaging.AVERAGED, largest=True),
            nodal.extremum(part.dataset, field, averaging=nodal.Averaging.AVERAGED, largest=False),
        ))
    if not found:
        raise nodal.NodalError(f"'{name}' を持つパートがありません")
    top_part, top, _ = max(found, key=lambda one: one[1].value)
    bottom_part, _, bottom = min(found, key=lambda one: one[2].value)
    marked = caveats | {Caveat.AVERAGED} | (frozenset({Caveat.UNDECLARED_UNIT}) if unit is None else frozenset())
    # The cells the averaging left out because they had no value (INV-011): counted on every one of
    # the four numbers, because each is computed without them (XC-303).
    left_out = sum(
        int(np.count_nonzero(np.isnan(part.dataset.fields[name].values)))
        for part in holders if part.dataset is not None and name in part.dataset.fields
    )

    def where(part: Part, at: int) -> str:
        assert part.dataset is not None
        return f"{part.label}：{location_of(part.dataset.identifiers.get(Association.POINT), at, Association.POINT)}"

    ratio_formula = f"spread / |nodal-average({name})| at the node of max(nodal-average({name}))"
    fraction = (
        ReportedValue(
            value=float(top.fraction), unit=DIMENSIONLESS, digits=digits, provenance=Provenance.COMPUTED,
            caveats=caveats, formula=ratio_formula, location=where(top_part, top.at),
        )
        if top.fraction is not None and np.isfinite(top.fraction)
        else ReportedValue.unavailable(
            "平均が 0 の節点では、ばらつきの比は定まりません", unit=DIMENSIONLESS, digits=digits,
            provenance=Provenance.COMPUTED, caveats=caveats, formula=ratio_formula,
        )
    )
    return AveragedExtrema(
        maximum=ReportedValue(
            value=top.value, unit=unit, digits=digits, provenance=Provenance.COMPUTED, caveats=marked,
            formula=f"max(nodal-average({name}))", location=where(top_part, top.at),
        ).with_missing(left_out),
        minimum=ReportedValue(
            value=bottom.value, unit=unit, digits=digits, provenance=Provenance.COMPUTED, caveats=marked,
            formula=f"min(nodal-average({name}))", location=where(bottom_part, bottom.at),
        ).with_missing(left_out),
        spread=ReportedValue(
            value=top.spread, unit=unit, digits=digits, provenance=Provenance.COMPUTED,
            caveats=caveats | (frozenset({Caveat.UNDECLARED_UNIT}) if unit is None else frozenset()),
            formula=f"max(contributing {name}) - min(contributing {name}) at the node of max(nodal-average({name}))",
            location=where(top_part, top.at),
        ).with_missing(left_out),
        fraction=fraction.with_missing(left_out),
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


def item_get(session: Session, kind: str, key: str, parameters: Mapping[str, Any]) -> Effect | Result:
    """One item's definition as the document holds it now, with its revision (CT-003 3.5.0).

    What an interface reads before it writes: a definition rebuilt from what a window remembers
    replaces what the document kept - the camera a person saved last session went that way on the
    first redraw of the next, until this existed (XC-274).
    """
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    item_id = str(parameters[key])
    try:
        item = items.find(workspace.raw, kind, item_id)
    except ItemError as error:
        return refused(str(error))
    return Effect(
        f"'{item_id}' の定義です",
        value={"id": item_id, "revision": session.revisions.get(item_id, 1), "definition": dict(item["definition"])},
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


#: The picture formats this build writes. CT-003 also names jpeg and webp; each is refused by name
#: until it exists, because a png handed back under another name is a lie about the bytes.
IMAGE_FORMATS = ("png",)


def colouring_of(stated: Mapping[str, Any]) -> Colouring | Result:
    """CT-004's `colouring` as the renderer's, or the refusal that says which part it cannot take."""
    association = {"point": Association.POINT, "cell": Association.CELL}.get(str(stated.get("association", "")))
    if association is None:
        return refused(f"colouring.association は point か cell です（'{stated.get('association')}' が渡されました）")
    stated_range = stated.get("range") or {}
    try:
        return Colouring(
            field_name=str(stated.get("fieldName", "")),
            association=association,
            colour_map=str(stated.get("colourMap") or Colouring.__dataclass_fields__["colour_map"].default),
            range_mode=str(stated_range.get("mode") or "dataRange"),
            minimum=stated_range.get("min"),
            maximum=stated_range.get("max"),
            out_of_range=str(stated.get("outOfRange") or "clamp"),
        )
    except RenderError as error:
        return refused(str(error))


def camera_of(stated: Mapping[str, Any] | None) -> Camera | Result:
    if not stated:
        return Camera()
    try:
        return Camera(
            position_m=tuple(stated["position_m"]) if stated.get("position_m") else None,
            focal_point_m=tuple(stated["focalPoint_m"]) if stated.get("focalPoint_m") else None,
            view_up=tuple(stated["viewUp"]) if stated.get("viewUp") else None,
            parallel_scale_m=stated.get("parallelScale_m"),
            projection=str(stated.get("projection") or "perspective"),
        )
    except (RenderError, TypeError, ValueError) as error:
        return refused(f"camera が読めません：{error}")


def camera_for(definition: Mapping[str, Any], parameters: Mapping[str, Any]) -> tuple[Camera, dict[str, Any] | None] | Result:
    """The camera a picture is drawn or picked with, and - where it came from a path - the statement
    of which path, where on it, by what rule, and the pose that gave (XC-289).

    Three sources, in this order: `cameraPath` in the parameters (a path of the definition and a
    parameter on it), `camera` in the parameters (a look, interface state, XC-270), the definition's
    own camera. Two of the first two together are refused: two answers to "from where".
    """
    stated_path = parameters.get("cameraPath")
    stated_camera = parameters.get("camera")
    if stated_path and stated_camera:
        return refused("camera と cameraPath は同時に指定できません：どこから描くかの答えが二つになります")
    if not stated_path:
        camera = camera_of(stated_camera or definition.get("camera"))
        return camera if isinstance(camera, Result) else (camera, None)
    if not isinstance(stated_path, Mapping):
        return refused(f"cameraPath はオブジェクトです（{type(stated_path).__name__} が渡されました）")
    wanted = str(stated_path.get("id", ""))
    found = next((one for one in (definition.get("cameraPaths") or []) if isinstance(one, Mapping) and str(one.get("id")) == wanted), None)
    if found is None:
        known = [str(one.get("id")) for one in (definition.get("cameraPaths") or []) if isinstance(one, Mapping)]
        return refused(f"カメラパス '{wanted}' はこのビューにありません。あるのは {known} です")

    def parse(stated: Mapping[str, Any] | None) -> Camera:
        camera = camera_of(stated)
        if isinstance(camera, Result):
            raise camera_paths.CameraPathError(camera.reason or "camera が読めません")
        return camera

    try:
        path = camera_paths.from_definition(found, parse)
        camera = path.at(float(stated_path.get("at", float("nan"))))
    except (camera_paths.CameraPathError, TypeError, ValueError) as error:
        return refused(str(error))
    return camera, {
        "id": path.id,
        "at": float(stated_path["at"]),
        "interpolation": path.interpolation,
        "rule": path.rule,
        "camera": camera_definition(camera),
    }


def camera_definition(camera: Camera) -> dict[str, Any]:
    """A camera in CT-004's shape, so a pose the engine computed can be handed back and used again."""
    stated: dict[str, Any] = {"projection": camera.projection}
    if camera.position_m is not None:
        stated["position_m"] = list(camera.position_m)
    if camera.focal_point_m is not None:
        stated["focalPoint_m"] = list(camera.focal_point_m)
    if camera.view_up is not None:
        stated["viewUp"] = list(camera.view_up)
    if camera.parallel_scale_m is not None:
        stated["parallelScale_m"] = camera.parallel_scale_m
    return stated


#: The ground a picture is drawn on when the view does not say. White, because the deliverable is the
#: harder case: a document printed on paper wants a white ground, and a screen can ask for its own.
DEFAULT_BACKGROUND = (1.0, 1.0, 1.0)


def background_of(stated: Any) -> tuple[float, float, float] | Result:
    """CT-004's `background` as three channels, or the refusal that says what is wrong with it.

    A screen wants the dark ground its chrome is built on (XC-256) and a page wants white. Neither is
    guessed from context: the view says which, and a view that says nothing gets the document's.
    """
    if not stated:
        return DEFAULT_BACKGROUND
    if not isinstance(stated, Mapping):
        return refused(f"background はオブジェクトです（{type(stated).__name__} が渡されました）")
    channels = stated.get("rgb")
    if channels is None:
        return DEFAULT_BACKGROUND
    if not isinstance(channels, (list, tuple)) or len(channels) != 3:
        return refused("background.rgb は 0..1 の 3 つの値です")
    try:
        values = tuple(float(one) for one in channels)
    except (TypeError, ValueError):
        return refused("background.rgb の値が数値ではありません")
    if any(one < 0.0 or one > 1.0 for one in values):
        return refused(f"background.rgb は 0..1 の範囲です（{list(values)} が渡されました）")
    return values  # type: ignore[return-value]


def view_render(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    image_format = str(parameters["format"])
    if image_format not in IMAGE_FORMATS:
        return refused(f"この版が書ける画像は {list(IMAGE_FORMATS)} です（'{image_format}' が求められました）")
    try:
        item = items.find(workspace.raw, "views", str(parameters["viewId"]))
    except ItemError as error:
        return refused(str(error))
    definition = item["definition"]
    if str(definition.get("representation", "surface")) != "surface":
        return refused(
            f"表現 '{definition.get('representation')}' はこの版では描けません（surface のみ）。"
            "描けない表現を surface で描いて返すことはしません"
        )
    loaded = session.loaded(str(definition.get("datasetId", "")))
    if isinstance(loaded, Result):
        return loaded
    stated = definition.get("colouring")
    if not isinstance(stated, Mapping):
        return refused("着色（colouring）のないビューはこの版では描きません：何で色付けするかを定義に書いてください")
    colouring = colouring_of(stated)
    if isinstance(colouring, Result):
        return colouring
    # The step the definition is at (CT-004 `resultPosition`, XC-283): the picture is of that step,
    # and the answer says which (view/AC-032).
    position = position_of(loaded, definition)
    if isinstance(position, Result):
        return position
    case = case_at(loaded, position)
    if isinstance(case, Result):
        return case
    shown = parts_shown(loaded, definition, case)
    if isinstance(shown, Result):
        return shown
    # A camera given draws the picture from there and leaves the definition's camera as it is: a
    # camera move is interface state, not a document change (XC-270, 16_application_model §6). A
    # position on one of the definition's camera paths is a computed pose, answered with its rule.
    looked = camera_for(definition, parameters)
    if isinstance(looked, Result):
        return looked
    camera, from_path = looked
    available, detail = session.offscreen()
    if not available:
        # Asked before drawing, because drawing without a context does not fail - it takes the
        # process down (E-194). A refusal that names the requirement is what the caller can act on.
        return refused(f"描画できません：{detail}")
    ground = background_of(definition.get("background"))
    if isinstance(ground, Result):
        return ground
    try:
        rendered = render_view(
            [part.dataset for part in shown if part.dataset is not None], colouring,
            width=int(parameters["width"]), height=int(parameters["height"]), camera=camera,
            background=ground, legend=bool(parameters.get("legend", True)),
        )
    except RenderError as error:
        return refused(str(error))
    handle = session.handles.issue(rendered.png)
    answer: dict[str, Any] = {"handle": handle["id"], "reduced": rendered.reduced, "resultPosition": stated_position(position)}
    if from_path is not None:
        answer["cameraPath"] = from_path
    return Effect(
        f"{rendered.width}x{rendered.height} の画像を描きました（{handle['bytes']} バイト）",
        value=answer,
    )


def dataset_probe(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """One value at a point, from the nearest part (view/AC-027 to AC-029).

    A case may hold several parts; the pick is tried on each and the part whose surface the point is
    nearest to answers, its label in front of the location so a node number in an assembly says which
    part's numbering it belongs to. A point on no part's surface is a stated absence, not a refusal:
    the question was well formed and the answer is "nothing is there".
    """
    loaded = session.loaded(str(parameters["datasetId"]))
    if isinstance(loaded, Result):
        return loaded
    try:
        position = loaded.axis.at(int(parameters["resultPosition"]))
    except PositionError as error:
        return refused(str(error))
    case = case_at(loaded, position)
    if isinstance(case, Result):
        return case
    name = str(parameters["fieldName"])
    holders = loaded.holders(name, case)
    if not holders:
        return refused(f"'{name}' というフィールドはこのデータセットにありません")
    if any(part.dataset is not None and part.dataset.fields[name].components != 1 for part in holders):
        return refused(
            f"'{name}' は成分の複数ある場で、一点の値としては読めません。導出量を作ってから読んでください（field.derive, XC-282）"
        )
    point = parameters["pointM"]
    picks: list[tuple[Part, pick.Pick]] = []
    for part in holders:
        assert part.dataset is not None
        try:
            picks.append((part, pick.probe(part.dataset, name, point)))
        except pick.PickError as error:
            return refused(str(error))
    part, found = min(picks, key=lambda pair: pair[1].distance_m)
    value = found.value
    if value.location and len(holders) > 1:
        value = replace(value, location=f"{part.label}：{value.location}")
    if case.is_partial:
        value = value.with_caveat(Caveat.PARTIAL_DATASET)
    return Effect(
        f"'{name}' の値を読みました" if not value.is_missing else f"'{name}' の値はそこにありません",
        value={
            "value": reported(value), "association": ASSOCIATION_WORD[found.association],
            "resultPosition": stated_position(position),
        },
    )


def view_pick(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """The value under one pixel of a frame drawn at a stated size (view/AC-027 to AC-029).

    `dataset.probe` is the same answer from a point in metres, which is what a script has. This is
    what an **interface** has: a pixel. The camera the picture was drawn with is the engine's, so
    the unprojection is the engine's - an interface computing it would be computing with a camera it
    never saw.
    """
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    try:
        item = items.find(workspace.raw, "views", str(parameters["viewId"]))
    except ItemError as error:
        return refused(str(error))
    definition = item["definition"]
    loaded = session.loaded(str(definition.get("datasetId", "")))
    if isinstance(loaded, Result):
        return loaded
    stated = definition.get("colouring")
    if not isinstance(stated, Mapping):
        return refused("着色のないビューは、どのフィールドの値を読むかを言えません")
    colouring = colouring_of(stated)
    if isinstance(colouring, Result):
        return colouring
    # The camera the picture was drawn with, where the caller gave one (XC-270) - or the pose on a
    # path the picture was drawn from, so the pixel is read off the same picture (XC-289).
    looked = camera_for(definition, parameters)
    if isinstance(looked, Result):
        return looked
    camera, from_path = looked
    available, detail = session.offscreen()
    if not available:
        # The unprojection needs the same scene the picture was drawn in, and that needs the toolkit
        # to be able to set one up at all (E-194).
        return refused(f"画素から座標を求められません：{detail}")

    # The step the picture is of, then the parts it shows: a hidden part is not in the frame, so a
    # value read from it would be a value from a picture nobody is looking at (XC-274, XC-283).
    position = position_of(loaded, definition)
    if isinstance(position, Result):
        return position
    case = case_at(loaded, position)
    if isinstance(case, Result):
        return case
    shown = parts_shown(loaded, definition, case)
    if isinstance(shown, Result):
        return shown
    width, height = int(parameters["width"]), int(parameters["height"])
    pixel = (int(parameters["x"]), int(parameters["y"]))
    datasets = [part.dataset for part in shown if part.dataset is not None]
    if any(colouring.field_name in one.fields and one.fields[colouring.field_name].components != 1 for one in datasets):
        return refused(
            f"'{colouring.field_name}' は成分の複数ある場で、一点の値としては読めません。導出量を作ってから読んでください（field.derive, XC-282）"
        )
    try:
        ray = render_module.ray_through(datasets, pixel, width=width, height=height, camera=camera)
    except RenderError as error:
        return refused(str(error))

    # A case may hold several parts and the ray meets the nearest. Each is asked and the one that
    # answers with a value wins - a part the ray missed says so rather than being silently skipped.
    found: list[tuple[Part, pick.Pick]] = []
    for part in shown:
        if part.dataset is None or colouring.field_name not in part.dataset.fields:
            continue
        try:
            found.append((part, pick.along_ray(part.dataset, colouring.field_name, ray.near_m, ray.far_m)))
        except pick.PickError as error:
            return refused(str(error))
    if not found:
        return refused(f"'{colouring.field_name}' を持つパートがありません")
    hit = [pair for pair in found if not pair[1].value.is_missing]
    part, answer = hit[0] if hit else found[0]
    value = answer.value
    if value.location and len(found) > 1:
        value = replace(value, location=f"{part.label}：{value.location}")
    if case.is_partial:
        value = value.with_caveat(Caveat.PARTIAL_DATASET)
    answered: dict[str, Any] = {
        "value": reported(value), "association": ASSOCIATION_WORD[answer.association],
        "resultPosition": stated_position(position),
    }
    if hit:
        # Which part answered, so the outliner's selection can follow the viewport's (view/AC-055).
        # Nothing hit names no part: a name there would be the part the ray happened to be asked last.
        answered["part"] = part.label
    if from_path is not None:
        answered["cameraPath"] = from_path
    return Effect(
        f"画素 {pixel} の値を読みました" if not value.is_missing else f"画素 {pixel} の先には何もありません",
        value=answered,
    )


# ---- graphs: the definition's series as numbers, computed by MOD-004 and arranged by MOD-005 ---------


@dataclass(frozen=True, slots=True)
class Reduced:
    """One number of a field over a case or a step, with what a graph must say about it."""

    value: ReportedValue
    scope: str
    weighting: str | None


def reduce_field(loaded: Loaded, case: LoadedCase, name: str, reduction: str) -> Reduced:
    """A field's maximum, minimum or weighted mean over the whole case, as `field.statistics` would
    answer it - the same arithmetic, so a graph and a table cannot disagree (INV-017, XC-290)."""
    holders = loaded.holders(name, case)
    scope = f"ケース全体（{len(holders)} パート）"
    fields = [part.dataset.fields[name] for part in holders if part.dataset is not None]
    if not fields:
        return Reduced(ReportedValue.unavailable(f"'{name}' というフィールドはこのデータセットにありません", unit=None, digits=1,
                                                 provenance=Provenance.COMPUTED, formula=f"{reduction}({name})"), scope, None)
    unit = fields[0].unit
    digits = min(field.significant_digits for field in fields)
    if fields[0].components != 1:
        return Reduced(ReportedValue.unavailable(
            f"'{name}' は {fields[0].components} 成分の場です。一つの数は導出量から求めてください（field.derive, XC-282）",
            unit=unit, digits=digits, provenance=Provenance.COMPUTED, formula=f"{reduction}({name})"), scope, None)
    association = fields[0].association
    caveats: frozenset[Caveat] = frozenset({Caveat.PARTIAL_DATASET}) if case.is_partial else frozenset()
    if reduction == "max":
        return Reduced(case.maximum(name), scope, "none")
    values = np.concatenate([field.values for field in fields])
    if reduction == "min":
        try:
            summary = summarise(values, reduction=Reduction.MIN, association=association, scope=scope, weighting=Weighting.NONE, unit=unit)
        except SummaryError as error:
            return Reduced(ReportedValue.unavailable(str(error), unit=unit, digits=digits, provenance=Provenance.COMPUTED,
                                                     formula=f"min({name})", caveats=caveats), scope, "none")
        return Reduced(as_reported(summary, digits=digits, formula=f"min({name})", caveats=caveats), scope, "none")
    mean, weighting = weighted_mean(holders, name, values, association, scope, unit, digits, caveats)
    return Reduced(mean, scope, weighting.value)


class CaseQuantities(Mapping[str, "Value | graph_series.Absent"]):
    """The quantities of one case (or one step of it) as the graph module reads them: `field.max`,
    `field.min` and `field.mean` for every field, each computed when first asked for. A number the
    field cannot give is an `Absent` with the reason, so the point says why (graph/AC-013)."""

    def __init__(self, loaded: Loaded, case: LoadedCase) -> None:
        self._loaded = loaded
        self._case = case
        names: list[str] = []
        for dataset in loaded.datasets(case):
            for name in dataset.fields:
                if name not in names:
                    names.append(name)
        self._keys = [f"{name}.{reduction}" for name in names for reduction in graph_definition.REDUCTIONS]
        self._reduced: dict[str, Reduced] = {}

    def reduced(self, key: str) -> Reduced:
        if key not in self._reduced:
            name, _, reduction = key.rpartition(".")
            self._reduced[key] = reduce_field(self._loaded, self._case, name, reduction)
        return self._reduced[key]

    def __getitem__(self, key: str) -> Value | graph_series.Absent:
        if key not in self._keys:
            raise KeyError(key)
        reduced = self.reduced(key)
        if reduced.value.value is None:
            return graph_series.Absent(reduced.value.missing_because or "値なし")
        if reduced.value.unit is None:
            return Value(float(reduced.value.value), NO_DIMENSION, None)
        composed = parse_symbol(reduced.value.unit)
        # In the internal unit of the quantity, as the axis is labelled (CT-005): MPa and kPa on one
        # axis are plotted as Pa. The declared symbol travels beside it.
        return Value(float(reduced.value.value) * composed.to_internal, composed.dimension, reduced.value.unit)

    def __iter__(self):
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)

    def touched(self) -> list[Reduced]:
        """Every reduction computed so far: after a series is plotted over this case, exactly the
        numbers its value came from, so a point can carry their caveats (XC-303)."""
        return list(self._reduced.values())


def point_caveats(value: float | None, touched: list[Reduced]) -> dict[str, Any]:
    """What a plotted point must say beside its number (XC-303): the union of the caveats of every
    reduction its value came from, and the missing entries they left out, added up. A point with no
    value already says why in its reason."""
    if value is None or not touched:
        return {}
    answer: dict[str, Any] = {}
    # The undeclared unit is the series' fact, said once by its `unit`; a point carries what varies
    # from point to point - a partial dataset, an average, a reduced geometry, missing entries.
    caveats = sorted({
        one.value for reduced in touched for one in reduced.value.caveats if one is not Caveat.UNDECLARED_UNIT
    })
    if caveats:
        answer["caveats"] = caveats
    left_out = sum(reduced.value.missing_count for reduced in touched)
    if left_out:
        answer["missingCount"] = left_out
    return answer


def graph_data(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """The graph's series as numbers (graph/AC-001, AC-002, AC-008, AC-013, INV-017, XC-290).

    One point per loaded case, or - for a graph `overTime` - one per step of the result axis of the
    one loaded case, each step read through the same door the view uses (XC-283). A point that
    cannot be made is drawn as no data with the reason, and stays in the legend. Two series whose
    units cannot share an axis are refused naming both (AC-003); a series over a field is refused
    without its reduction, because which number of a field to plot is not this product's to choose.
    """
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    try:
        item = items.find(workspace.raw, "graphs", str(parameters["graphId"]))
    except ItemError as error:
        return refused(str(error))
    definition = item["definition"]
    try:
        stored_series = graph_definition.read_series(definition)
    except graph_definition.GraphError as error:
        return refused(str(error))
    if not stored_series:
        return refused("この グラフ に系列がありません（CT-005 series）")
    for one in stored_series:
        if one.source is graph_definition.SourceKind.FIELD and not one.expression and one.reduction is None:
            return refused(
                f"系列 '{one.label}' は場 '{one.field_name}' を描きますが、どの一つの数か（reduction: {list(graph_definition.REDUCTIONS)}）が"
                "ありません。場は多くの数で、点は一つです：どれを描くかはこちらでは選びません（INV-017, XC-290）"
            )
    if not session.datasets:
        return refused("データセットが読み込まれていません。グラフの点は読み込まれたケースから作ります")

    # Which cases: the definition's own, else the context the asking area gave - the tree's
    # selection or the case it is pinned to (XC-292) - else every loaded one; and the answer says
    # which (AC-008, AC-009). A definition that names its cases is the authority: the tree cannot
    # override it by clicking (11_ui.md), so the context is ignored rather than merged in.
    selection = definition.get("caseSelection") or {}
    given = [str(one) for one in (selection.get("caseIds") or [])] if isinstance(selection, Mapping) else []
    context = [str(one) for one in (parameters.get("contextCaseIds") or [])]
    by_case: dict[str, Loaded] = {}
    for loaded in session.datasets.values():
        by_case[loaded.case_id] = loaded
    cases = given or context or list(by_case)
    chosen = "given" if given else "context" if context else "loaded"

    # The series with the units the fields carry **now**: a definition written before a declaration
    # would otherwise label the axis with a unit the numbers are no longer in (XC-003).
    live_series: list[graph_definition.Series] = []
    for one in stored_series:
        unit = one.unit
        if one.source is graph_definition.SourceKind.FIELD and one.field_name and not one.expression:
            found = next((loaded for loaded in by_case.values() if loaded.holders(one.field_name)), None)
            unit = found.holders(one.field_name)[0].dataset.fields[one.field_name].unit if found else None  # type: ignore[union-attr]
        try:
            live_series.append(replace(one, unit=unit))
        except graph_definition.GraphError as error:
            return refused(str(error))
    refusal = graph_definition.refusal_for(live_series)
    if refusal:
        return refused(refusal)

    over_time = str(definition.get("kind")) == "overTime"
    answered: list[dict[str, Any]] = []
    missing: list[str] = []
    axes = []
    for one in live_series:
        points: list[dict[str, Any]] = []
        reduced_seen: Reduced | None = None
        key = f"{one.field_name}.{one.reduction}" if one.reduction else None
        if over_time:
            if len(cases) != 1 or cases[0] not in by_case:
                return refused(
                    f"結果軸に沿ったグラフ（overTime）は読み込まれた一つのケースの上に描きます（対象 {cases}）"
                )
            loaded = by_case[cases[0]]
            axes.append(loaded.axis)
            for step in range(loaded.axis.count):
                position = loaded.axis.at(step)
                case = case_at(loaded, position)
                if isinstance(case, Result):
                    points.append({"caseId": loaded.case_id, "x": position.value, "value": None, "reason": case.reason or "読めません", "resultPosition": stated_position(position)})
                    continue
                quantities = CaseQuantities(loaded, case)
                plotted = graph_series.plot(one, [loaded.case_id], lambda _case, q=quantities: q)
                point = plotted.points[0]
                if key and key in quantities:
                    reduced_seen = quantities.reduced(key)
                entry: dict[str, Any] = {"caseId": loaded.case_id, "x": position.value if position.value is not None else float(step), "value": point.value, "resultPosition": stated_position(position)}
                if point.reason:
                    entry["reason"] = point.reason
                entry.update(point_caveats(point.value, quantities.touched()))
                points.append(entry)
        else:
            for case_id in cases:
                loaded = by_case.get(case_id)
                if loaded is None:
                    points.append({"caseId": case_id, "x": None, "value": None, "reason": f"ケース '{case_id}' は読み込まれていません"})
                    continue
                axes.append(loaded.axis)
                quantities = CaseQuantities(loaded, loaded.case)
                plotted = graph_series.plot(one, [case_id], lambda _case, q=quantities: q)
                point = plotted.points[0]
                if key and key in quantities:
                    reduced_seen = quantities.reduced(key)
                entry = {"caseId": case_id, "x": None, "value": point.value}
                if point.reason:
                    entry["reason"] = point.reason
                entry.update(point_caveats(point.value, quantities.touched()))
                points.append(entry)
        series_answer: dict[str, Any] = {
            "label": one.label,
            "points": points,
            "unit": parse_symbol(one.unit).canonical if one.unit else None,
            "declaredUnit": one.unit,
            "provenance": one.provenance.value,
        }
        if one.expression:
            series_answer["expression"] = one.expression
        if one.reduction:
            series_answer["reduction"] = one.reduction
        if reduced_seen is not None:
            series_answer["scope"] = reduced_seen.scope
            if reduced_seen.weighting:
                series_answer["weighting"] = reduced_seen.weighting
            series_answer["digits"] = reduced_seen.value.digits
        answered.append(series_answer)
        for point in points:
            if point["value"] is None:
                missing.append(f"{one.label} / {point['caseId']}：{point.get('reason', '理由不明')}")
    value: dict[str, Any] = {
        "series": answered,
        "axisLabel": graph_definition.axis_label(live_series),
        "cases": cases,
        "selection": chosen,
        "missing": missing,
    }
    note = graph_definition.note_result_axes(dict(definition), axes)
    if note:
        value["resultAxisNote"] = note
    return Effect(f"グラフの系列 {len(answered)} 本（対象 {len(cases)} ケース）", value=value)


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
        # The step the block's view is at, where it names one: the table beside a picture states
        # the numbers of the step the picture shows, and each row says which (view/AC-032).
        position = position_for_block(session, loaded, block)
        if isinstance(position, Result):
            raise ReportError(f"{key} 番目の値の表：{position.reason or '結果位置を決められません'}")
        case = case_at(loaded, position)
        if isinstance(case, Result):
            raise ReportError(f"{key} 番目の値の表：{case.reason or '結果位置のデータを読めません'}")
        rows[key] = [row for name in names for row in value_rows(loaded, name, case, position)]
    return rows, involved


def position_for_block(session: Session, loaded: Loaded, block: Mapping[str, Any]) -> ResultPosition | Result:
    """The position a report block's numbers are of: its view's, or the first step where it names
    no view. A view the document does not hold is refused by name rather than read as the first step."""
    view_id = block.get("viewId")
    if not view_id or session.workspace is None:
        return loaded.axis.at(0)
    try:
        item = items.find(session.workspace.raw, "views", str(view_id))
    except ItemError as error:
        return refused(str(error))
    return position_of(loaded, item["definition"])


def value_rows(loaded: Loaded, name: str, case: LoadedCase, position: ResultPosition) -> list[ValueRow]:
    """A field's maximum as a document states it - and for a cell field, both numbers with the spread.

    A report that gives one without saying which has answered neither (INV-032): the element value
    is labelled as such, the averaged one carries its caveat, and the spread at its node follows.
    Where the case has more than one step, every label says which step the number is of (AC-032).
    """
    at = f"・{position.describe()}" if position.count > 1 else ""
    maximum = case.maximum(name)
    holders = loaded.holders(name, case)
    cell = bool(holders) and all(
        part.dataset is not None and part.dataset.fields[name].association is Association.CELL for part in holders
    )
    if not cell:
        return [ValueRow(label=f"{name} の最大{at}", value=maximum)]
    rows = [ValueRow(label=f"{name} の最大（要素値・平均なし）{at}", value=maximum)]
    unit = maximum.unit
    digits = maximum.digits
    caveats = frozenset({Caveat.PARTIAL_DATASET}) if case.is_partial else frozenset()
    try:
        both = averaged_extrema(holders, name, unit=unit, digits=digits, caveats=caveats)
    except nodal.NodalError as error:
        rows.append(ValueRow(
            label=f"{name} の最大（節点平均）{at}",
            value=ReportedValue.unavailable(str(error), unit=unit, digits=digits, provenance=Provenance.COMPUTED,
                                            caveats=caveats, formula=f"max(nodal-average({name}))"),
        ))
        return rows
    rows.append(ValueRow(label=f"{name} の最大（節点平均）{at}", value=both.maximum))
    rows.append(ValueRow(label=f"{name} の節点平均の最大でのばらつき（メッシュ細分の目安）{at}", value=both.spread))
    return rows


#: How large a still is drawn for a deliverable, and how far it is cut down when the document would
#: exceed LIM-006. Two retries, halving each time: a picture a quarter of the edge is a quarter of the
#: page and still a picture, and a third halving would be a thumbnail nobody can read a contour from.
FIGURE_SIZES = ((1200, 900), (800, 600), (560, 420))


def figures_for_report(
    session: Session, definition: Mapping[str, Any], size: tuple[int, int],
) -> tuple[dict[str, document_module.Figure], list[Loaded]]:
    """Draw a still for each view block that asked for one, at `size`.

    A block asking for an interactive view or a video gets no figure and no substitute: the writer
    names what it could not carry, which is the honest answer to a request this build cannot meet.
    """
    workspace = session.workspace
    figures: dict[str, document_module.Figure] = {}
    involved: list[Loaded] = []
    if workspace is None:
        return figures, involved
    for index, block in enumerate(definition.get("blocks", []) or []):
        if block.get("kind") != "view" or block.get("form") != "still":
            continue
        view_id = str(block.get("viewId") or "")
        key = view_id or str(index)
        try:
            item = items.find(workspace.raw, "views", view_id)
        except ItemError as error:
            raise ReportError(f"{key} 番目の view ブロック：{error}") from None
        view = item["definition"]
        loaded = session.datasets.get(str(view.get("datasetId", "")))
        if loaded is None:
            raise ReportError(f"ビュー '{view_id}' のデータセットが読み込まれていません")
        stated = view.get("colouring")
        if not isinstance(stated, Mapping):
            raise ReportError(f"ビュー '{view_id}' に着色（colouring）がありません")
        colouring = colouring_of(stated)
        if isinstance(colouring, Result):
            raise ReportError(colouring.reason or "着色を読めません")
        camera = camera_of(view.get("camera"))
        if isinstance(camera, Result):
            raise ReportError(camera.reason or "カメラを読めません")
        # The step the view is at, and the parts it shows, and no more: a part hidden on screen
        # and drawn in the deliverable would be two pictures under one name (XC-274, XC-283).
        position = position_of(loaded, view)
        if isinstance(position, Result):
            raise ReportError(f"ビュー '{view_id}'：{position.reason or '結果位置を決められません'}")
        case = case_at(loaded, position)
        if isinstance(case, Result):
            raise ReportError(f"ビュー '{view_id}'：{case.reason or '結果位置のデータを読めません'}")
        shown = parts_shown(loaded, view, case)
        if isinstance(shown, Result):
            raise ReportError(f"ビュー '{view_id}'：{shown.reason or '表示するパートを決められません'}")
        available, detail = session.offscreen()
        if not available:
            raise ReportError(f"図を描けません：{detail}")
        try:
            rendered = render_view(
                [part.dataset for part in shown if part.dataset is not None], colouring,
                width=size[0], height=size[1], camera=camera,
            )
        except RenderError as error:
            raise ReportError(f"ビュー '{view_id}' を描けません：{error}") from None
        if loaded not in involved:
            involved.append(loaded)
        figures[key] = document_module.Figure(
            png=rendered.png,
            width=rendered.width,
            height=rendered.height,
            legend=document_module.Legend(
                field_name=rendered.legend.field_name,
                unit=rendered.legend.unit,
                minimum=rendered.legend.minimum,
                maximum=rendered.legend.maximum,
                digits=rendered.legend.digits,
                colour_map=rendered.legend.colour_map,
                uniform=rendered.legend.uniform,
            ),
            # The step the picture is of, in the figure's own words (view/AC-032).
            description=str(item.get("name") or view_id) + (f"（{position.describe()}）" if position.count > 1 else ""),
        )
    return figures, involved


def report_export(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    workspace = session.open_workspace()
    if isinstance(workspace, Result):
        return workspace
    report_id = str(parameters["reportId"])
    path = for_os(str(parameters["path"]))
    if path.exists():
        return refused(f"{for_people(path)} はすでにあります。この版は上書きしません — 別の場所を指定してください")
    try:
        item = items.find(workspace.raw, "reports", report_id)
    except ItemError as error:
        return refused(str(error))
    definition = item["definition"]
    # No font ships yet (OPEN-032): every Japanese label is unrepresentable and the document says so
    # itself, which is XC-254's rule and XC-257's stated state of the prototype.
    capability = html.Capability()
    reductions: list[str] = []
    export = None
    for attempt, size in enumerate(FIGURE_SIZES):
        try:
            rows, involved = rows_for_report(session, definition)
            figures, drawn = figures_for_report(session, definition, size)
            for one in drawn:
                if one not in involved:
                    involved.append(one)
            document = build_document(
                definition, rows_for=rows, figures_for=figures,
                provenance=session.provenance_of(involved),
            )
            export = html.write(document, path, capability=capability, accepted=True)
        except ReportError as error:
            # LIM-006's on_exceed: reduce the picture and say by how much, rather than writing a file
            # a mail system will bounce or dropping the picture without a word. Only a size refusal
            # is retried; anything else is the caller's answer.
            if "LIM-006" in str(error) and attempt + 1 < len(FIGURE_SIZES):
                nxt = FIGURE_SIZES[attempt + 1]
                reductions.append(
                    f"図を {size[0]}x{size[1]} から {nxt[0]}x{nxt[1]} に縮小しました"
                    f"（成果物の上限 {html.MAX_REPORT_BYTES:,} バイト・LIM-006）"
                )
                continue
            return refused(str(error))
        break
    if export is None:  # pragma: no cover - the loop returns or breaks
        return refused("成果物を書き出せませんでした")

    def undo() -> None:
        if path.exists():
            path.unlink()

    return Effect(
        export.describe(),
        changed=(report_id,),
        value={
            "path": str(for_people(export.path)),
            "bytes": export.bytes,
            "reductions": reductions,
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
                {"path": source.path, "modified": source.modified.as_stored()} for source in provenance.sources
            ],
            "declaredUnits": dict(provenance.declared_units),
            "productVersion": provenance.product_version,
            "produced": provenance.produced.as_stored() if provenance.produced else None,
        },
    )


# -- output: what the runs left behind, and pruning it by name (XC-141, XC-268, #314) -------------


def _output_root(session: Session, parameters: Mapping[str, Any]) -> tuple[WorkspaceDocument, Path, Path] | Result:
    """The open workspace, its folder, and its output folder under it (XC-113)."""
    workspace = session.open_workspace(str(parameters["workspaceId"]))
    if isinstance(workspace, Result):
        return workspace
    if session.workspace_path is None:
        return refused("保存先のないワークスペースには出力フォルダがありません（XC-113）")
    base = session.workspace_path.parent
    return workspace, base, base / output.OUTPUT_DIRECTORY


def output_list(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """What the output folder holds, run by run, against LIM-012 (workspace/AC-052): each run's size
    and time - and where the time came from - the total, and which runs pruning oldest-first would
    take to get under the limit. An ask, never a refusal (XC-141)."""
    found = _output_root(session, parameters)
    if isinstance(found, Result):
        return found
    _, _, root = found
    runs = output.runs_of(root, where=session.clock())
    size = output.size_of(runs)
    suggested = output.plan_pruning(runs)
    return Effect(
        size.describe(),
        value={
            "outputDirectory": str(root),
            "runs": [run.as_stored() for run in runs],
            "totalBytes": size.total_bytes,
            "limitBytes": size.limit_bytes,
            "overLimit": size.over_limit,
            "suggestedRunIds": [run.identifier for run in suggested.runs],
        },
    )


def _recorded_inputs(workspace: WorkspaceDocument, base: Path) -> list[Path]:
    """Every file a case records as a source. Never this product's to delete, whatever folder it is in."""
    inputs: list[Path] = []
    for case, _ in walk_cases(workspace.cases):
        for source in case.get("sources") or []:
            if not isinstance(source, dict):
                continue
            if source.get("pathAbsolute"):
                inputs.append(Path(str(source["pathAbsolute"])))
            if source.get("pathRelative"):
                inputs.append(base / str(source["pathRelative"]))
    return inputs


def _planned(session: Session, parameters: Mapping[str, Any]) -> tuple[Path, output.PrunePlan] | Result:
    found = _output_root(session, parameters)
    if isinstance(found, Result):
        return found
    workspace, base, root = found
    chosen = parameters.get("runsToRemove")
    if not isinstance(chosen, list):
        return refused("runsToRemove は実行の識別子の一覧です")
    runs = output.runs_of(root, where=session.clock())
    try:
        plan = output.plan_for(runs, chosen, protected=_recorded_inputs(workspace, base))
    except output.OutputError as error:
        return refused(str(error))
    return root, plan


def output_plan(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """What pruning the chosen runs would delete, file by file, and the records it would keep - shown
    before anything goes (workspace/AC-053)."""
    made = _planned(session, parameters)
    if isinstance(made, Result):
        return made
    root, plan = made
    return Effect(plan.describe(), value=plan.as_stored(root))


def output_prune(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """Delete exactly what the plan showed (AC-053, XC-268). The caller names the files it expects to
    go; a folder that changed since the plan is refused with nothing deleted, because a list a person
    confirmed is the only list this may act on. No undo: a deleted artefact is regenerated from its
    record (XC-046), not brought back from memory."""
    if session.read_only and session.lock is not None:
        return refused(
            f"読み取り専用で開いています：{session.lock.describe()}。"
            "もう一方の窓が使っているかもしれない成果物は消しません（XC-241）"
        )
    made = _planned(session, parameters)
    if isinstance(made, Result):
        return made
    root, plan = made
    stored = plan.as_stored(root)
    expected = parameters.get("expectedFiles")
    if expected is not None and sorted(str(one) for one in expected) != sorted(stored["files"]):
        return refused(
            "計画を見せたあとに出力フォルダが変わっています。何も消していません。"
            "一覧を読み直して、もう一度確認してください（XC-268）"
        )
    removed = output.prune(plan)
    return Effect(
        f"{len(plan.runs)} 実行分から {removed} ファイル、{bytes_as_text(plan.freed_bytes)} を消しました。"
        f"実行の記録 {len(plan.kept_records)} 件は残しています",
        changed=tuple(run.identifier for run in plan.runs),
        value={"removedRunIds": stored["runIds"], "freedBytes": plan.freed_bytes, "deletedFiles": stored["files"]},
        warnings=("この操作は取り消せません。消した成果物は実行の記録から作り直します（XC-046、XC-061）",),
    )


def system_audit(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """What has left this machine, as the gate recorded it (XC-106, assistant/AC-021): every
    request, sent or refused, with its time as the pair. Empty is an answer - "nothing" said by the
    record, not by a sentence about the policy (#317)."""
    since = parameters.get("since")
    floor: str | None = None
    if since is not None:
        try:
            floor = RecordedTime(str(since), None).utc
        except ValueError:
            return refused(f"since は UTC の時刻（{STORED_FORMAT}）で指定してください：{since!r}")
    recorded = session.gate.audit()
    entries = [one.as_stored() for one in recorded if floor is None or one.at.utc >= floor]
    return Effect(
        "外部に出た要求はありません" if not recorded else f"外部要求の記録 {len(entries)} 件",
        value={"entries": entries},
    )


def system_log(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """The diagnostic log read back (XC-286): commands with their outcomes and reasons, the warnings
    beside answers, and the egress decisions - from the files where there are files, which is how a
    person reads what happened after the window that showed it has closed. Never a field value: the
    log refused one at every write (XC-126)."""
    stated = str(parameters.get("level", diagnostics.Level.WARNING.value))
    try:
        level = diagnostics.Level(stated)
    except ValueError:
        return refused(f"level は {[one.value for one in diagnostics.Level]} のどれかです：{stated!r}")
    since = parameters.get("since")
    floor: str | None = None
    if since is not None:
        try:
            floor = RecordedTime(str(since), None).utc
        except ValueError:
            return refused(f"since は UTC の時刻（{STORED_FORMAT}）で指定してください：{since!r}")
    limit = int(parameters.get("limit", LOG_READ_LIMIT))
    if limit < 1 or limit > LOG_READ_LIMIT:
        return refused(f"limit は 1〜{LOG_READ_LIMIT} です（{limit} が求められました）")
    reading = session.log.read(level=level, since=floor, limit=limit)
    location = session.log.describe_location()
    return Effect(
        f"診断ログ {len(reading.lines)} 件" + (f"（さらに {reading.omitted} 件は上限で省略）" if reading.omitted else ""),
        value={
            "entries": [
                {"at": one.at.as_stored(), "level": one.level.value, "event": one.event, "context": dict(one.context)}
                for one in reading.lines
            ],
            "source": session.log.source,
            "logDirectory": location["logDirectory"],
            "files": location["files"],
            "retainDays": location["retainDays"],
            "omitted": reading.omitted,
            "unreadable": reading.unreadable,
        },
    )


#: The most lines one read of the log answers. A day of a busy session is a few thousand; a person
#: reads the newest, and `since` narrows the rest.
LOG_READ_LIMIT = 2000


def system_operations(surface: Surface) -> Effect:
    """Which catalogue operations this build answers, and which it does not (XC-277, INV-006).

    Read from the surface's own registry, so the list can never say more than the registry does:
    an interface that listed the catalogue would list forty operations nothing answers.
    """
    return Effect(
        "この版が答える操作です",
        value={"registered": list(surface.registered()), "unimplemented": list(surface.unimplemented())},
    )


def _include_from(parameters: Mapping[str, Any]) -> diagnostics.Include | Result:
    raw = parameters.get("include") or {}
    if not isinstance(raw, Mapping):
        return refused("include は caseNames と filePaths を持つオブジェクトです")
    return diagnostics.Include(case_names=bool(raw.get("caseNames", False)), file_paths=bool(raw.get("filePaths", False)))


def _environment(session: Session) -> dict[str, Any]:
    """The facts a support case needs about where the engine ran - never a path, never a user name."""
    try:
        from vtkmodules.vtkCommonCore import vtkVersion

        vtk_version: str | None = str(vtkVersion.GetVTKVersion())
    except ImportError:
        vtk_version = None
    offscreen, _ = session.offscreen()
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "vtk": vtk_version,
        "machineClass": session.machine_class.value,
        "offscreen": offscreen,
        "codePage": active_code_page(),
    }


def _support_manifest(session: Session, include: diagnostics.Include) -> diagnostics.Manifest:
    """What a bundle would contain now, for the person to read before it exists (AC-008, XC-302):
    the case names and the recorded paths only where they chose them."""
    workspace = session.workspace
    case_names: list[str] = []
    paths: list[str] = []
    if workspace is not None and session.workspace_path is not None:
        base = for_people(session.workspace_path.parent)
        for case, _ in walk_cases(workspace.cases):
            if include.case_names:
                case_names.append(str(case.get("name") or case.get("id", "")))
            if include.file_paths:
                resolution = sources.resolve_case(case, relative_to=session.workspace_path.parent)
                paths += [str(base / one.path_relative) for one in resolution.sources]
    shell_lines: int | None = None
    if include.free_text and session.log.directory is not None:
        shell = session.log.directory / diagnostics.SHELL_LOG_FILE
        if shell.exists():
            with shell.open(encoding="utf-8", errors="replace") as handle:
                shell_lines = sum(1 for _ in handle)
    return diagnostics.manifest_for(
        session.log,
        workspace_id=workspace.identifier if workspace is not None else None,
        case_names=case_names,
        paths=paths,
        clock=session.clock,
        include=include,
        product_version=product_version(),
        environment=_environment(session),
        shell_lines=shell_lines,
    )


def system_support_manifest(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """Everything a support bundle would contain, listed before it exists (operations/AC-008, XC-302).
    The list is kept as the one shown, and the bundle is made from it and from nothing else."""
    include = _include_from(parameters)
    if isinstance(include, Result):
        return include
    manifest = _support_manifest(session, include)
    session.support_manifest = manifest
    return Effect(f"診断情報の一覧 {len(manifest.items)} 件", value=manifest.as_answer())


def system_support_bundle(session: Session, parameters: Mapping[str, Any]) -> Effect | Result:
    """The archive, from the list that was shown and consented to (XC-126, AC-008, XC-302): written
    whole or not at all, never over a file that is there, and recorded in the log. Nothing here
    sends it anywhere - leaving the machine is the gate's, with a consent of its own (AC-009)."""
    if parameters.get("consent") is not True:
        return refused("同意がありません。診断情報は、何が入るかの一覧に同意してから作ります（XC-126、operations/AC-008）")
    include = _include_from(parameters)
    if isinstance(include, Result):
        return include
    shown = session.support_manifest
    if shown is None or shown.include != include:
        return refused(
            "一覧をまだ見ていません。system.supportManifest で同じ選択の一覧を見てから作ります（operations/AC-008）"
        )
    current = _support_manifest(session, include)
    if current.fixed_items != shown.fixed_items:
        session.support_manifest = current
        return refused("一覧を見てから、開いている文書やケースが変わりました。一覧を見直してから作ってください（operations/AC-008）")
    path = for_os(Path(str(parameters["path"])))
    if path.exists():
        return refused(f"{for_people(path)} はすでにあります。この版は上書きしません — 別の場所を指定してください")
    if not path.parent.is_dir():
        return refused(f"{for_people(path.parent)} というフォルダがありません")
    workspace = session.workspace
    cases: list[dict[str, Any]] = []
    recorded: list[dict[str, Any]] = []
    if workspace is not None and session.workspace_path is not None:
        base = for_people(session.workspace_path.parent)
        for case, _ in walk_cases(workspace.cases):
            cases.append({"id": str(case.get("id", "")), "name": str(case.get("name") or "")})
            resolution = sources.resolve_case(case, relative_to=session.workspace_path.parent)
            recorded += [
                {"caseId": resolution.case_id, "path": str(base / one.path_relative), "present": one.is_resolved}
                for one in resolution.sources
            ]
    bundle = diagnostics.create(shown, accepted=True)
    try:
        written = diagnostics.write_bundle(
            bundle,
            path=path,
            log=session.log,
            product_version=product_version(),
            environment=_environment(session),
            cases=cases,
            sources=recorded,
            shell_log=(session.log.directory / diagnostics.SHELL_LOG_FILE) if session.log.directory is not None else None,
        )
    except diagnostics.DiagnosticsError as error:
        return refused(str(error))
    except OSError as error:
        return refused(f"診断情報を書けませんでした：{error}")
    session.log.record(
        diagnostics.Level.INFO, "supportBundle",
        items=len(shown.items), customerItems=len(shown.case_names) + len(shown.paths),
        freeText=shown.free_text_kept, bytes=written.bytes, entries=len(written.entries),
    )

    def undo() -> None:
        if path.exists():
            path.unlink()

    return Effect(
        f"診断情報を作成しました（{len(written.entries)} ファイル、{written.bytes} バイト）",
        value={
            "path": str(for_people(path)),
            "contents": list(bundle.contents),
            "bytes": written.bytes,
            "entries": list(written.entries),
        },
        undo=undo,
    )


def system_capabilities(session: Session) -> Effect:
    native, detail = session.offscreen()
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
            "diagnostics": session.log.describe_location(),
            "egress": session.gate.describe_policy(session.workspace.identifier if session.workspace else None),
            "machineClass": session.machine_class.value,
            "renderers": [
                {"backend": one.backend.value, "available": one.available, "requires": REQUIRES[one.backend]}
                for one in availability
            ],
            "formats": formats,
        },
    )
