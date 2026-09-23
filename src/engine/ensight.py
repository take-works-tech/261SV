"""Reading EnSight Gold: every file the case names is checked against its own counts before the
toolkit's reader sees any of them, because that reader crashes, hangs or reads a cut file as a
whole one (E-227, XC-308).

Measured on VTK 9.5.2 with files the toolkit's own writer produced: a binary geometry file cut in
half takes the process down with a segmentation fault; cut at 90 or 99 per cent it reads as a whole
part with the cells silently gone; a cut variable file reads as a part with the variable silently
dropped; a case file cut in half makes the reader loop forever; and an ASCII geometry cut in half
reads as a whole part. None of those is a refusal, and two of them are not even a return. So this
module parses the case file itself (a malformed one is refused, never handed over), walks each
geometry and variable file by the counts the format writes into it - binary in either byte order,
ASCII by lines - and refuses, naming the file and the place, before the reader is asked for
anything. After the read, every variable the case file listed has to have arrived.

The reader takes its path through `SetCaseFileName` rather than `SetFileName`, which is why
`ReaderChoice` has `feed_path`. Parts are named by the geometry file's descriptions, which the
toolkit's own writer sets to "VTK Part" for every part; a fixture renames them where two would
collide. Variable names are the case file's, which that writer suffixes with `_n` or `_c`.

What is followed: unstructured parts with the standard element kinds (point, bar2, bar3, tria3,
tria6, quad4, quad8, tetra4, tetra10, pyramid5, pyramid13, penta6, penta15, hexa8, hexa20, and their
`g_` ghost forms), nsided and nfaced polyhedra, node and element ids given or not, scalars, vectors
and tensors per node and per element, one time set with numbered files. A structured `block`, an
`extents` line, a `coordinates partial` or `undef` variable, several time sets, a changing
geometry, or a keyword this module does not know is refused by name: the toolkit reads it, but
nothing here can say it is whole, and an unchecked geometry is a crash waiting (E-227).

Specification: ingest/AC-052, XC-308. Evidence: E-227 (T1), E-212 (T1).
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from domain_core.os_paths import for_os
from engine.completeness import FileIncomplete, ResultsLost, arrays_present

#: What has been exercised and what has not: the part of the support claim that is measured.
KNOWN_GAPS = (
    "verified against files the toolkit's own writer produced and hand-written ASCII: binary and "
    "ASCII Gold geometry with node and element ids, scalars, vectors and tensors per node and per "
    "element, parts and one time set of numbered files; every file the case names is checked "
    "against its own counts before the read, and a structured block, an extents line, a partial or "
    "undefined variable, several time sets or a changing geometry is refused rather than handed to a "
    "reader that crashes on a cut file (E-227); part names are the geometry file's descriptions, "
    "which a writer may repeat, and a file whose name holds a space cannot be named by a case file"
)

LINE = 80
#: Nodes per element, by the format's own keyword. A `g_` prefix is the ghost form of the same.
NODES_PER_ELEMENT = {
    "point": 1, "bar2": 2, "bar3": 3, "tria3": 3, "tria6": 6, "quad4": 4, "quad8": 8,
    "tetra4": 4, "tetra10": 10, "pyramid5": 5, "pyramid13": 13, "penta6": 6, "penta15": 15,
    "hexa8": 8, "hexa20": 20,
}
VARIABLE_COMPONENTS = {"scalar": 1, "vector": 3, "tensor symm": 6, "tensor asym": 9, "tensor": 6}


def _shown(line: str) -> str:
    """A line as a message quotes it: its first sixty characters where they are text, and a word
    where they are not - random bytes quoted back at a person are noise, not a place."""
    head = line[:60]
    return repr(head) if head.isprintable() else "テキストではないバイト列"


class EnSightError(FileIncomplete):
    """A case, geometry or variable file this module cannot follow to its end: not whole, not the
    shape the format writes, or not one this build reads - said by file and place, before any read."""


@dataclass(frozen=True)
class Variable:
    kind: str          # scalar, vector, tensor symm, tensor asym
    per: str           # node, element
    name: str
    filename: str      # as written, `*` wildcards included
    components: int


@dataclass(frozen=True)
class CaseFile:
    path: Path
    geometry: str
    variables: tuple[Variable, ...]
    #: The numbered files a `*` pattern stands for, in step order; one entry where there is no time.
    numbers: tuple[str, ...] = ("",)
    times: tuple[float, ...] = field(default_factory=tuple)

    def expand(self, pattern: str) -> list[str]:
        if "*" not in pattern:
            return [pattern]
        width = pattern.count("*")
        stem = pattern.replace("*" * width, "{}")
        return [stem.format(number.rjust(width, "0")[-width:] if number else "0" * width) for number in self.numbers]

    def geometry_files(self) -> list[Path]:
        return [self.path.parent / one for one in self.expand(self.geometry)]

    def variable_files(self, variable: Variable) -> list[Path]:
        return [self.path.parent / one for one in self.expand(variable.filename)]

    def every_file(self) -> list[Path]:
        found = self.geometry_files()
        for variable in self.variables:
            found += self.variable_files(variable)
        return found


# ---- the case file --------------------------------------------------------------------------------

def read_case_file(path: Path) -> CaseFile:
    """The case file, parsed strictly. Anything this parser cannot place is a refusal: the toolkit's
    reader, handed a case file cut in half, does not return (E-227)."""
    try:
        text = for_os(path).read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        raise EnSightError(f"{path.name} を読めません（{error.strerror or error}）") from error
    if not text.strip():
        raise EnSightError(f"{path.name} は空です。EnSight の case ファイルではありません")
    section = ""
    geometry: str | None = None
    variables: list[Variable] = []
    time: dict[str, str] = {}
    time_values: list[float] = []
    filename_numbers: list[str] = []
    reading_values = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        upper = line.upper()
        if upper in ("FORMAT", "GEOMETRY", "VARIABLE", "TIME", "FILE", "MATERIAL", "BLOCK_CONTINUED", "SCRIPTS"):
            section = upper
            reading_values = False
            continue
        if section == "FORMAT":
            if not line.lower().startswith("type:") or "ensight gold" not in line.lower():
                raise EnSightError(f"{path.name}：FORMAT が 'type: ensight gold' ではありません（{_shown(line)}）")
        elif section == "GEOMETRY":
            key, _, value = line.partition(":")
            if key.strip().lower() == "model":
                tokens = value.split()
                if not tokens:
                    raise EnSightError(f"{path.name}：model 行にファイル名がありません")
                # `model: [ts] [cs] filename [change_coords_only]` - a time-set index before the name
                # is allowed only for one time set, and a changing geometry is refused below.
                filename = next((one for one in tokens if not one.isdigit()), None)
                if filename is None:
                    raise EnSightError(f"{path.name}：model 行にファイル名がありません（{_shown(line)}）")
                if "change_coords_only" in tokens or len([one for one in tokens if one.isdigit()]) > 1:
                    raise EnSightError(f"{path.name}：形状が時刻で変わる case（{_shown(line)}）はこの版では読みません（E-227）")
                geometry = filename
            elif key.strip().lower() in ("measured", "match", "boundary", "rigid_body", "vector_glyphs"):
                raise EnSightError(f"{path.name}：GEOMETRY の '{key.strip()}' はこの版では読みません")
            else:
                raise EnSightError(f"{path.name}：GEOMETRY に知らない行があります（{_shown(line)}）")
        elif section == "VARIABLE":
            match = re.match(r"^(scalar|vector|tensor symm|tensor asym|tensor)\s+per\s+(node|element|measured node)\s*:\s*(.*)$", line, re.IGNORECASE)
            if not match:
                if re.match(r"^(constant|complex)", line, re.IGNORECASE):
                    raise EnSightError(f"{path.name}：VARIABLE の '{line.split(':')[0]}' はこの版では読みません")
                raise EnSightError(f"{path.name}：VARIABLE に知らない行があります（{_shown(line)}）")
            kind, per, rest = match.group(1).lower(), match.group(2).lower(), match.group(3).split()
            if per == "measured node":
                raise EnSightError(f"{path.name}：measured node の変数はこの版では読みません")
            # `[ts] [fs] description filename`: the description is the last-but-one token, the file
            # the last; leading integers are time and file set indices.
            if len(rest) < 2:
                raise EnSightError(f"{path.name}：変数行に説明とファイル名が要ります（{_shown(line)}）")
            name, filename = rest[-2], rest[-1]
            variables.append(Variable(kind, per, name, filename, VARIABLE_COMPONENTS[kind]))
        elif section == "TIME":
            if reading_values:
                try:
                    time_values += [float(one) for one in line.split()]
                    continue
                except ValueError:
                    reading_values = False
            key, _, value = line.partition(":")
            key = key.strip().lower()
            if key == "time set":
                if time.get("set") is not None:
                    raise EnSightError(f"{path.name}：時刻集合が二つ以上あります。この版は一つだけ読みます")
                time["set"] = value.strip()
            elif key == "number of steps":
                time["steps"] = value.strip()
            elif key == "filename start number":
                time["start"] = value.strip()
            elif key == "filename increment":
                time["increment"] = value.strip()
            elif key == "filename numbers":
                filename_numbers += value.split()
            elif key == "time values":
                reading_values = True
                time_values += [float(one) for one in value.split() if one]
            else:
                raise EnSightError(f"{path.name}：TIME に知らない行があります（{_shown(line)}）")
        elif section == "":
            raise EnSightError(f"{path.name}：節の外に行があります（{_shown(line)}）。case ファイルではないか、切り詰められています")
        else:
            raise EnSightError(f"{path.name}：'{section}' 節はこの版では読みません")
    if geometry is None:
        raise EnSightError(f"{path.name}：GEOMETRY の model 行がありません。case ファイルではないか、切り詰められています")
    numbers: tuple[str, ...] = ("",)
    times: tuple[float, ...] = ()
    if time:
        try:
            steps = int(time["steps"])
        except (KeyError, ValueError):
            raise EnSightError(f"{path.name}：TIME に number of steps がありません") from None
        if filename_numbers:
            found = filename_numbers
        elif "start" in time:
            start, increment = int(time["start"]), int(time.get("increment", "1"))
            found = [str(start + increment * step) for step in range(steps)]
        else:
            raise EnSightError(f"{path.name}：TIME に filename start number も filename numbers もありません")
        if len(found) != steps or len(time_values) != steps:
            raise EnSightError(
                f"{path.name}：TIME は {steps} ステップと言いますが、ファイル番号 {len(found)} 個、時刻 {len(time_values)} 個です。切り詰められた case ファイルです"
            )
        numbers, times = tuple(found), tuple(time_values)
    return CaseFile(path, geometry, tuple(variables), numbers, times)


# ---- the geometry ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class PartShape:
    number: int
    nodes: int
    #: Elements per block, in file order, with the block's keyword.
    blocks: tuple[tuple[str, int], ...]


class _Binary:
    """A cursor over a binary Gold file: lines of 80, ints and floats of 4, in one byte order."""

    def __init__(self, path: Path, data: bytes, order: str) -> None:
        self.path, self.data, self.order, self.at = path, data, order, 0

    def short(self, what: str) -> EnSightError:
        return EnSightError(
            f"{self.path.name} は {len(self.data)} バイトで、{self.at} バイト目で {what} を読み切れません。"
            "書き込み途中か、切り詰められたファイルです。ツールキットのリーダーはこの状態で落ちるか、"
            "読めた分を全体として返すので、読む前に拒みます（E-227）"
        )

    def line(self, what: str = "行") -> str:
        if self.at + LINE > len(self.data):
            raise self.short(what)
        raw = self.data[self.at:self.at + LINE]
        self.at += LINE
        return raw.split(b"\0")[0].decode("latin-1").strip()

    def int(self, what: str = "整数") -> int:
        if self.at + 4 > len(self.data):
            raise self.short(what)
        value = struct.unpack(self.order + "i", self.data[self.at:self.at + 4])[0]
        self.at += 4
        return value

    def skip(self, count: int, what: str) -> None:
        if count < 0 or self.at + 4 * count > len(self.data):
            raise self.short(f"{what}（{count} 個）")
        self.at += 4 * count

    def ints(self, count: int, what: str) -> list[int]:
        if count < 0 or self.at + 4 * count > len(self.data):
            raise self.short(f"{what}（{count} 個）")
        values = list(struct.unpack(f"{self.order}{count}i", self.data[self.at:self.at + 4 * count]))
        self.at += 4 * count
        return values

    @property
    def done(self) -> bool:
        return self.at >= len(self.data)


def _element_kind(keyword: str) -> str | None:
    base = keyword[2:] if keyword.startswith("g_") else keyword
    return base if base in NODES_PER_ELEMENT or base in ("nsided", "nfaced") else None


def _walk_binary_geometry(cursor: _Binary) -> list[PartShape]:
    for expected in ("説明 1", "説明 2"):
        cursor.line(expected)
    node_ids = cursor.line("node id").lower()
    element_ids = cursor.line("element id").lower()
    if not node_ids.startswith("node id") or not element_ids.startswith("element id"):
        raise EnSightError(f"{cursor.path.name}：ヘッダに 'node id' と 'element id' の行がありません。EnSight Gold の形状ファイルではないか、別のバイト順です")
    nodes_given = node_ids.split()[-1] in ("given", "ignore")
    elements_given = element_ids.split()[-1] in ("given", "ignore")
    parts: list[PartShape] = []
    while not cursor.done:
        keyword = cursor.line("part")
        if keyword == "extents":
            raise EnSightError(f"{cursor.path.name}：extents 行はこの版では読みません（E-227）")
        if keyword != "part":
            raise EnSightError(f"{cursor.path.name}：{cursor.at - LINE} バイト目に 'part' ではなく {keyword[:30]!r} があります")
        number = cursor.int("パート番号")
        cursor.line("パートの説明")
        layout = cursor.line("coordinates")
        if layout != "coordinates":
            raise EnSightError(f"{cursor.path.name}：パート {number} は '{layout[:30]}' で始まります。この版は非構造格子（coordinates）だけを読みます")
        nodes = cursor.int("節点数")
        if nodes < 0:
            raise EnSightError(f"{cursor.path.name}：パート {number} の節点数が負です（{nodes}）。別のバイト順か、形状ファイルではありません")
        if nodes_given:
            cursor.skip(nodes, "節点 id")
        cursor.skip(3 * nodes, "座標")
        blocks: list[tuple[str, int]] = []
        while not cursor.done:
            probe = cursor.at
            keyword = cursor.line("要素種別")
            if keyword == "part":
                cursor.at = probe
                break
            kind = _element_kind(keyword)
            if kind is None:
                raise EnSightError(f"{cursor.path.name}：要素種別 {keyword[:30]!r} はこの版では読みません")
            count = cursor.int("要素数")
            if count < 0:
                raise EnSightError(f"{cursor.path.name}：{keyword} の要素数が負です（{count}）")
            if elements_given:
                cursor.skip(count, f"{keyword} の要素 id")
            if kind == "nsided":
                per_element = cursor.ints(count, "多角形の頂点数")
                cursor.skip(sum(per_element), "多角形の接続")
            elif kind == "nfaced":
                faces = cursor.ints(count, "多面体の面数")
                per_face = cursor.ints(sum(faces), "面の頂点数")
                cursor.skip(sum(per_face), "多面体の接続")
            else:
                cursor.skip(count * NODES_PER_ELEMENT[kind], f"{keyword} の接続")
            blocks.append((keyword, count))
        parts.append(PartShape(number, nodes, tuple(blocks)))
    if not parts:
        raise EnSightError(f"{cursor.path.name}：パートがありません")
    return parts


def _walk_ascii_geometry(path: Path, lines: list[str]) -> list[PartShape]:
    cursor = _Lines(path, lines)
    cursor.take("説明 1")
    cursor.take("説明 2")
    node_ids = cursor.take("node id").lower()
    element_ids = cursor.take("element id").lower()
    if not node_ids.startswith("node id") or not element_ids.startswith("element id"):
        raise EnSightError(f"{path.name}：ヘッダに 'node id' と 'element id' の行がありません。EnSight Gold の形状ファイルではありません")
    nodes_given = node_ids.split()[-1] in ("given", "ignore")
    elements_given = element_ids.split()[-1] in ("given", "ignore")
    parts: list[PartShape] = []
    while not cursor.done:
        keyword = cursor.take("part")
        if keyword == "extents":
            raise EnSightError(f"{path.name}：extents 行はこの版では読みません（E-227）")
        if keyword != "part":
            raise EnSightError(f"{path.name}：{cursor.at} 行目に 'part' ではなく {keyword[:30]!r} があります")
        number = cursor.int("パート番号")
        cursor.take("パートの説明")
        layout = cursor.take("coordinates")
        if layout != "coordinates":
            raise EnSightError(f"{path.name}：パート {number} は '{layout[:30]}' で始まります。この版は非構造格子（coordinates）だけを読みます")
        nodes = cursor.int("節点数")
        if nodes_given:
            cursor.skip(nodes, "節点 id")
        cursor.skip(3 * nodes, "座標")
        blocks: list[tuple[str, int]] = []
        while not cursor.done:
            probe = cursor.at
            keyword = cursor.take("要素種別")
            if keyword == "part":
                cursor.at = probe
                break
            kind = _element_kind(keyword)
            if kind is None:
                raise EnSightError(f"{path.name}：要素種別 {keyword[:30]!r} はこの版では読みません")
            count = cursor.int("要素数")
            if elements_given:
                cursor.skip(count, f"{keyword} の要素 id")
            if kind == "nsided":
                per_element = [cursor.int("多角形の頂点数") for _ in range(count)]
                cursor.skip(len(per_element), "多角形の接続")
            elif kind == "nfaced":
                faces = [cursor.int("多面体の面数") for _ in range(count)]
                per_face = [cursor.int("面の頂点数") for _ in range(sum(faces))]
                cursor.skip(len(per_face), "多面体の接続")
            else:
                cursor.skip(count, f"{keyword} の接続")
            blocks.append((keyword, count))
        parts.append(PartShape(number, nodes, tuple(blocks)))
    if not parts:
        raise EnSightError(f"{path.name}：パートがありません")
    return parts


class _Lines:
    """A cursor over an ASCII Gold file, line by line."""

    def __init__(self, path: Path, lines: list[str]) -> None:
        self.path, self.lines, self.at = path, lines, 0

    def short(self, what: str) -> EnSightError:
        return EnSightError(
            f"{self.path.name} は {len(self.lines)} 行で、{self.at + 1} 行目で {what} を読み切れません。"
            "書き込み途中か、切り詰められたファイルです。ツールキットのリーダーは読めた分を全体として返すので、読む前に拒みます（E-227）"
        )

    def take(self, what: str) -> str:
        if self.at >= len(self.lines):
            raise self.short(what)
        line = self.lines[self.at].strip()
        self.at += 1
        return line

    def int(self, what: str) -> int:
        line = self.take(what)
        try:
            value = int(line.split()[0])
        except (ValueError, IndexError):
            raise EnSightError(f"{self.path.name}：{self.at} 行目に {what} を期待しましたが {line[:30]!r} でした") from None
        if value < 0:
            raise EnSightError(f"{self.path.name}：{what} が負です（{value}）")
        return value

    def skip(self, count: int, what: str) -> None:
        if self.at + count > len(self.lines):
            self.at = len(self.lines)
            raise self.short(f"{what}（{count} 行）")
        self.at += count

    @property
    def done(self) -> bool:
        return self.at >= len(self.lines)


def _is_binary(head: bytes) -> bool:
    return head[:LINE].split(b"\0")[0].decode("latin-1").strip().lower().endswith("binary")


def geometry_shapes(path: Path) -> list[PartShape]:
    """Every part of a geometry file with its node count and element blocks, from the file's own
    counts - or a refusal naming where the file ends short or leaves what this module follows."""
    location = for_os(path)
    try:
        data = location.read_bytes()
    except OSError as error:
        raise EnSightError(f"{path.name} を読めません（{error.strerror or error}）") from error
    if not data:
        raise EnSightError(f"{path.name} は空です")
    if _is_binary(data):
        if data[:LINE].split(b"\0")[0].decode("latin-1").strip().lower().startswith("fortran"):
            raise EnSightError(f"{path.name}：Fortran binary はこの版では読みません")
        failures: list[str] = []
        for order in ("<", ">"):
            cursor = _Binary(path, data, order)
            cursor.line("C Binary")
            try:
                return _walk_binary_geometry(cursor)
            except EnSightError as error:
                failures.append(str(error))
        raise EnSightError(failures[0] + "（逆のバイト順でも同じ）")
    lines = data.decode("latin-1").splitlines()
    return _walk_ascii_geometry(path, lines)


# ---- the variables --------------------------------------------------------------------------------

def check_variable(path: Path, variable: Variable, shapes: list[PartShape]) -> None:
    """A variable file walked by the part sizes the geometry gave: one value per component per node
    or per element, block by block. Short, partial or undefined is refused by name."""
    location = for_os(path)
    try:
        data = location.read_bytes()
    except OSError as error:
        raise EnSightError(f"{path.name} を読めません（{error.strerror or error}）") from error
    if not data:
        raise EnSightError(f"{path.name} は空です")
    by_number = {shape.number: shape for shape in shapes}
    if _is_binary(data[:LINE]) or not data[:LINE].split(b"\0")[0].isascii() or b"\0" in data[:LINE]:
        failures: list[str] = []
        for order in ("<", ">"):
            try:
                _walk_binary_variable(_Binary(path, data, order), variable, by_number)
                return
            except EnSightError as error:
                failures.append(str(error))
        raise EnSightError(failures[0] + "（逆のバイト順でも同じ）")
    _walk_ascii_variable(_Lines(path, data.decode("latin-1").splitlines()), variable, by_number)


def _walk_binary_variable(cursor: _Binary, variable: Variable, by_number: dict[int, PartShape]) -> None:
    cursor.line("説明")
    seen = 0
    while not cursor.done:
        keyword = cursor.line("part")
        if keyword != "part":
            raise EnSightError(f"{cursor.path.name}：{cursor.at - LINE} バイト目に 'part' ではなく {keyword[:30]!r} があります")
        number = cursor.int("パート番号")
        shape = by_number.get(number)
        if shape is None:
            raise EnSightError(f"{cursor.path.name}：パート {number} は形状ファイルにありません")
        if variable.per == "node":
            layout = cursor.line("coordinates")
            if layout != "coordinates":
                raise EnSightError(f"{cursor.path.name}：'{layout[:30]}' はこの版では読みません（partial や undef の変数）")
            cursor.skip(variable.components * shape.nodes, f"{variable.name} の値")
        else:
            for keyword_expected, count in shape.blocks:
                keyword = cursor.line("要素種別")
                if keyword != keyword_expected:
                    raise EnSightError(f"{cursor.path.name}：パート {number} で {keyword_expected} を期待しましたが {keyword[:30]!r} でした")
                cursor.skip(variable.components * count, f"{variable.name} の値")
        seen += 1
    if seen == 0:
        raise EnSightError(f"{cursor.path.name}：パートがありません")


def _walk_ascii_variable(cursor: _Lines, variable: Variable, by_number: dict[int, PartShape]) -> None:
    cursor.take("説明")
    seen = 0
    while not cursor.done:
        keyword = cursor.take("part")
        if keyword != "part":
            raise EnSightError(f"{cursor.path.name}：{cursor.at} 行目に 'part' ではなく {keyword[:30]!r} があります")
        number = cursor.int("パート番号")
        shape = by_number.get(number)
        if shape is None:
            raise EnSightError(f"{cursor.path.name}：パート {number} は形状ファイルにありません")
        if variable.per == "node":
            layout = cursor.take("coordinates")
            if layout != "coordinates":
                raise EnSightError(f"{cursor.path.name}：'{layout[:30]}' はこの版では読みません（partial や undef の変数）")
            cursor.skip(variable.components * shape.nodes, f"{variable.name} の値")
        else:
            for keyword_expected, count in shape.blocks:
                keyword = cursor.take("要素種別")
                if keyword != keyword_expected:
                    raise EnSightError(f"{cursor.path.name}：パート {number} で {keyword_expected} を期待しましたが {keyword[:30]!r} でした")
                cursor.skip(variable.components * count, f"{variable.name} の値")
        seen += 1
    if seen == 0:
        raise EnSightError(f"{cursor.path.name}：パートがありません")


# ---- what the reader is given, and what it must return ---------------------------------------------

def companions(case_path: Path) -> list[Path]:
    """Every file the case names, for the fingerprint (XC-284). A case file that cannot be parsed
    is refused here, by name, rather than handed to a reader that would not return."""
    return read_case_file(for_os(case_path)).every_file()


def check_before_read(case_path: Path) -> CaseFile:
    """The case parsed and every file it names walked to its end (E-227)."""
    case = read_case_file(for_os(case_path))
    for geometry in case.geometry_files():
        if not geometry.exists():
            raise EnSightError(f"{case.path.name} が名指す形状ファイル {geometry.name} がありません")
    # A refusal names the file that was opened as well as the file that is short: the person dropped
    # the case, and the geometry or variable file it names is one they may never have seen.
    shapes_per_step: list[list[PartShape]] = []
    for geometry in case.geometry_files():
        try:
            shapes_per_step.append(geometry_shapes(geometry))
        except EnSightError as error:
            raise EnSightError(f"{case.path.name} が名指す形状ファイル {error}") from None
    for variable in case.variables:
        files = case.variable_files(variable)
        for index, one in enumerate(files):
            if not one.exists():
                raise EnSightError(f"{case.path.name} が名指す変数ファイル {one.name}（{variable.name}）がありません")
            shapes = shapes_per_step[index if len(shapes_per_step) > 1 else 0]
            try:
                check_variable(one, variable, shapes)
            except EnSightError as error:
                raise EnSightError(f"{case.path.name} が名指す変数ファイル（{variable.name}） {error}") from None
    return case


def feed_path(reader: object, path: str) -> None:
    reader.SetCaseFileName(path)  # type: ignore[attr-defined]


def case_path_of(reader: object) -> Path:
    """The case file's full path, put back together: the reader splits what `SetCaseFileName` was
    given into a directory and a name, and `GetCaseFileName` returns the name alone (measured)."""
    name = Path(reader.GetCaseFileName())  # type: ignore[attr-defined]
    if name.is_absolute():
        return name
    return Path(reader.GetFilePath() or "") / name  # type: ignore[attr-defined]


def prepare(reader: object) -> None:
    """Every file checked before the toolkit's reader is asked for anything, then every variable
    switched on: the reader reads none unless told to."""
    check_before_read(case_path_of(reader))
    reader.ReadAllVariablesOn()  # type: ignore[attr-defined]


def verify(reader: object, output: object) -> None:
    """Every variable the case file listed arrived as an array: a variable file the reader dropped
    silently (measured on a cut one, E-227) is a result lost, not a dataset."""
    case = read_case_file(case_path_of(reader))
    offered = {variable.name for variable in case.variables}
    if not offered:
        return
    present = arrays_present(output)
    missing = sorted(offered - present)
    if missing:
        raise ResultsLost(
            f"{case.path.name} が名指す変数 {', '.join(missing)} が読み込みに現れませんでした。"
            "ツールキットのリーダーが黙って落とした結果は、結果ではありません（E-227）"
        )


def iter_variables(case_path: Path) -> Iterator[Variable]:
    yield from read_case_file(for_os(case_path)).variables
