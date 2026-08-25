"""Which renderer runs here, what it needs, and why none of them may return a number.

XC-087 gives the product four rendering paths with separate jobs rather than four alternatives: the
scientific web renderer for the interactive view, the native toolkit offscreen for datasets above the
interactive budget and for report images, WebGPU as an experimental selection, and Omniverse as an
optional path.

**A renderer that cannot run is named, with what it requires, and an alternative is offered** (XC-004,
AC-006). It is never substituted silently, and the distinction is not politeness: a substituted backend
can change shading, tessellation and colour interpolation, so a user who believes they are looking at
one path is measuring something they did not choose.

**No backend produces a number** (INV-002, AC-005). That is enforced by the shape of the interface
rather than by discipline: a backend is handed a scene and returns an image and its capabilities, and
there is no method on it that could return a field value. Reported values come from MOD-004 on canonical
data (INV-001), which is what makes "the same view reports the same numbers on every renderer" a
property of the architecture instead of a promise.

Nothing here probes anything itself. Whether a WebGL2 context exists is a question about a browser and
whether the native toolkit is importable is a question about an installation; both are answered by
whoever can answer them and handed in. A module that guessed would report a capability nobody tested.

Specification: XC-004, XC-087, INV-001, INV-002, view/AC-005, AC-006, LIM-002.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Protocol


class Backend(str, Enum):
    """XC-087's four paths. Closed: a fifth is a decision, not a registration."""

    WEB_GL2 = "webgl2"
    NATIVE_OFFSCREEN = "nativeOffscreen"
    WEBGPU = "webgpu"
    OMNIVERSE = "omniverse"


class Role(str, Enum):
    """What a path is **for** (XC-087). The two main ones are a division of labour, not a choice."""

    INTERACTIVE = "interactive"
    ABOVE_BUDGET = "aboveBudget"     # datasets over LIM-002
    REPORT_IMAGE = "reportImage"


#: Which backend does which job, from XC-087. Held as a table so "which renderer draws a report image"
#: is answered in one place rather than decided at each call site.
FOR_ROLE: dict[Role, Backend] = {
    Role.INTERACTIVE: Backend.WEB_GL2,
    Role.ABOVE_BUDGET: Backend.NATIVE_OFFSCREEN,
    Role.REPORT_IMAGE: Backend.NATIVE_OFFSCREEN,
}

#: What each path needs before it can run, in the words a user is told when it cannot. Written out
#: because "unavailable" without a requirement is a message nobody can act on.
REQUIRES: dict[Backend, str] = {
    Backend.WEB_GL2: "ブラウザの WebGL2 コンテキスト",
    Backend.NATIVE_OFFSCREEN: "エンジン側のネイティブツールキット（オフスクリーン描画）",
    Backend.WEBGPU: "WebGPU アダプタ（実験的な選択肢です）",
    Backend.OMNIVERSE: "Omniverse への接続（任意の経路です）",
}

#: Paths a user is warned about before choosing them, and the words used.
MARKED: dict[Backend, str] = {
    Backend.WEBGPU: "実験的",
    Backend.OMNIVERSE: "任意",
}


class RendererError(Exception):
    """Raised where a rendering path cannot be chosen honestly."""


@dataclass(frozen=True, slots=True)
class Availability:
    """Whether one path can run here, and what is missing where it cannot."""

    backend: Backend
    available: bool
    detail: str | None = None

    def describe(self) -> str:
        mark = f"（{MARKED[self.backend]}）" if self.backend in MARKED else ""
        if self.available:
            return f"{self.backend.value}{mark}：使えます"
        because = f"：{self.detail}" if self.detail else ""
        return f"{self.backend.value}{mark}：使えません（{REQUIRES[self.backend]} が必要）{because}"


@dataclass(frozen=True, slots=True)
class Choice:
    """The outcome of asking for a renderer.

    A refusal carries an **offer**, not a substitution. `selected` is None when the requested path
    cannot run, and the caller has to accept `offered` deliberately - a field holding the alternative
    as though it were the answer is how a silent substitution gets written by accident.
    """

    wanted: Backend
    selected: Backend | None = None
    offered: Backend | None = None
    reason: str | None = None

    @property
    def ran_as_asked(self) -> bool:
        return self.selected is not None and self.selected is self.wanted

    def describe(self) -> str:
        if self.ran_as_asked:
            return f"{self.wanted.value} で描画します"
        if self.offered is None:
            return (
                f"{self.wanted.value} は使えません（{self.reason}）。"
                "代わりに使える描画経路がこの環境にはありません — "
                "別の経路を黙って使うことはしません（XC-004）"
            )
        return (
            f"{self.wanted.value} は使えません（{self.reason}）。"
            f"{self.offered.value} なら実行できます。"
            "陰影・分割・色の補間が変わるため、置き換えは選んでいただいてからにします（XC-004）"
        )


class Renderer(Protocol):
    """What a rendering backend offers.

    Deliberately two methods and neither returns a value from the data. A backend draws and says what it
    can do; asking it for a number is not a thing the interface permits, which is what makes INV-002 a
    property of the shape rather than a rule somebody has to remember.
    """

    def capabilities(self) -> frozenset[str]:
        """What this path can draw - volume rendering, order-independent transparency, and so on."""
        ...

    def draw(self, scene: object, width: int, height: int) -> bytes:
        """Pixels. Not values."""
        ...


def probe(answers: Mapping[Backend, bool], *, details: Mapping[Backend, str] | None = None) -> tuple[Availability, ...]:
    """Turn answers about this machine into the availability list (AC-006).

    The answers are handed in. Whether a WebGL2 context exists is a question about a browser and whether
    the toolkit is importable is a question about an installation; a module that guessed either would
    report a capability nobody tested.

    A path nobody answered for is **unavailable with the reason that it was not probed**, rather than
    absent from the list: a path missing from a list reads as a path that does not exist.
    """
    stated = details or {}
    return tuple(
        Availability(
            backend,
            bool(answers.get(backend, False)),
            stated.get(backend) or (None if backend in answers else "この環境では確認していません"),
        )
        for backend in Backend
    )


def choose(wanted: Backend, availability: Iterable[Availability]) -> Choice:
    """Ask for a path, and get it or a refusal that names an alternative (XC-004, AC-006).

    The order of the offer is XC-087's division of labour rather than a preference: the interactive path
    first, then the native one, then the marked paths, so what is offered is the ordinary path for the
    ordinary job.
    """
    by_backend = {one.backend: one for one in availability}
    if wanted not in by_backend:
        raise RendererError(
            f"{wanted.value} の可用性が渡されていません。"
            "確認していない経路を「使える」とも「使えない」とも言いません"
        )
    if by_backend[wanted].available:
        return Choice(wanted, selected=wanted)

    order = [Backend.WEB_GL2, Backend.NATIVE_OFFSCREEN, Backend.WEBGPU, Backend.OMNIVERSE]
    offered = next(
        (one for one in order if one is not wanted and by_backend.get(one, Availability(one, False)).available),
        None,
    )
    detail = by_backend[wanted].detail
    reason = f"{REQUIRES[wanted]} がありません" + (f"：{detail}" if detail else "")
    return Choice(wanted, selected=None, offered=offered, reason=reason)


def for_role(role: Role, availability: Iterable[Availability]) -> Choice:
    """The path that does this job, or the refusal for it (XC-087)."""
    return choose(FOR_ROLE[role], availability)


def unavailable(availability: Iterable[Availability]) -> tuple[Availability, ...]:
    """Everything that cannot run here, for showing all of it at once rather than one refusal at a time."""
    return tuple(one for one in availability if not one.available)
