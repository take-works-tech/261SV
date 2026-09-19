"""The notices file, generated from the build closure and nothing else (XC-025, XC-041).

    python packaging/notices.py                      # from build/engine/solvia-engine, to build/notices/
    python packaging/notices.py --app <unpacked dir> # also the shell and the interface's bundle
    python packaging/notices.py --verify             # fail unless every shipped file is attributed

XC-025 says the list is generated from the **actual build closure**, not by hand and not from a
dependency's own install tree, because a hand-maintained list is wrong within one release and an
upstream list is incomplete: VTK's wheel ships no third-party notices at all (E-047). So this reads
the frozen engine directory file by file and attributes each file to the component it belongs to,
and refuses to finish while any file is unattributed. The texts come from where each component keeps
them:

  - **VTK**: the 9.5.2 source release (pinned by SHA-256, fetched into build/ when absent). Every
    `vtk.module` declares its licence, its copyright and, where the licence is a variant, the file
    that carries the variant's text (E-207). A module is *in the closure* when its library file is,
    and the modules that are pull in what they declare they depend on - which is how the header-only
    third parties (Eigen, scnlib) are reached, since no file of theirs ships (E-046).
  - **NumPy** and **VTK's own copyright**: the wheels' metadata and licence files, carried into the
    frozen directory by PyInstaller's --copy-metadata.
  - **Python**: the interpreter that froze the engine, whose version the closure names by its
    library file; the text is its own LICENSE.txt.
  - **The Microsoft runtime**, **the OpenXR loader**: bundled into the VTK wheel by delvewheel; a
    statement of terms for the one (E-205), a vendored dual-licence notice for the other (E-206).
  - **Electron and Chromium**: the files electron-builder already places next to the executable.
  - **The interface's bundle**: React and what it brings, from the interface's own lockfile.

What this does NOT do: judge whether a licence's conditions are met. It reproduces what each
component says its terms are, and says where in the closure the component is. Reading the
conditions is a person's work, and the file is laid out to make it possible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tarfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
ENGINE_DEFAULT = BUILD / "engine" / "solvia-engine"
OUT_DEFAULT = BUILD / "notices"
VENDORED = ROOT / "packaging" / "notices"

VTK_VERSION = "9.5.2"
VTK_SOURCE_URL = f"https://vtk.org/files/release/9.5/VTK-{VTK_VERSION}.tar.gz"
VTK_SOURCE_SHA256 = "cee64b98d270ff7302daf1ef13458dff5d5ac1ecb45d47723835f7f7d562c989"
VTK_SOURCE_DIR = BUILD / "vtk-source"

LICENCE_FILE_NAME = re.compile(r"^(LICENSE|LICENCE|COPYING|COPYRIGHT|NOTICE)", re.IGNORECASE)

#: Statements a licence requires beyond its own text (E-046), attached to the component's entry.
REQUIRED_STATEMENTS = {
    "freetype": (
        "Required credit (FreeType License): Portions of this software are copyright (c) The FreeType "
        "Project (www.freetype.org). All rights reserved."
    ),
    "jpeg": (
        "Statement (libjpeg-turbo, IJG terms): this software is based in part on the work of the "
        "Independent JPEG Group."
    ),
    "eigen": (
        "Eigen is MPL-2.0: its source, as VTK bundles it, is ThirdParty/eigen/vtkeigen in the VTK "
        f"{VTK_VERSION} source release at {VTK_SOURCE_URL}"
    ),
    "gl2ps": (
        "VTK ships a modified GL2PS; the modified source is published as ThirdParty/gl2ps/vtkgl2ps in the "
        f"VTK {VTK_VERSION} source release at {VTK_SOURCE_URL} (XC-041)"
    ),
}


# ---- what a component is -----------------------------------------------------------------------


@dataclass
class Component:
    name: str
    version: str
    licence: str
    """SPDX where a source declares one; otherwise the words the source uses."""
    files: list[str] = field(default_factory=list)
    """Paths inside the closure, relative to its root, that belong to this component."""
    texts: list[tuple[str, str]] = field(default_factory=list)
    """(where the text came from, the text) - reproduced verbatim."""
    note: str = ""
    """One sentence a person needs: a dual licence exercised, a text found elsewhere, a statement."""

    def as_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "licence": self.licence,
            "files": sorted(self.files),
            "texts": [{"source": source, "text": text} for source, text in self.texts],
            "note": self.note,
        }


class NoticesError(Exception):
    pass


# ---- the VTK source release: what its module descriptions declare ------------------------------


@dataclass
class VtkModule:
    name: str
    library: str
    spdx: str
    copyright: str
    custom_licence_file: str | None
    custom_licence_name: str | None
    licence_files: list[str]
    depends: list[str]
    third_party: bool
    directory: str
    """Inside the tarball, e.g. VTK-9.5.2/Common/Core."""


def _field(text: str, key: str) -> list[str]:
    match = re.search(rf"^{key}\n((?:  .*\n?)+)", text, re.M)
    if not match:
        return []
    return [line.strip() for line in match.group(1).splitlines() if line.strip() and not line.strip().startswith("#")]


def fetch_vtk_source() -> Path:
    VTK_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    tarball = VTK_SOURCE_DIR / f"VTK-{VTK_VERSION}.tar.gz"
    if not tarball.exists():
        print(f"fetching {VTK_SOURCE_URL}", file=sys.stderr)
        with urllib.request.urlopen(VTK_SOURCE_URL, timeout=600) as answer, tarball.open("wb") as out:
            while chunk := answer.read(1 << 20):
                out.write(chunk)
    digest = hashlib.sha256(tarball.read_bytes()).hexdigest()
    if digest != VTK_SOURCE_SHA256:
        raise NoticesError(f"VTK source tarball hash is {digest}, expected {VTK_SOURCE_SHA256}")
    return tarball


def read_vtk_modules(tarball: Path) -> tuple[dict[str, VtkModule], dict[str, str]]:
    """Every vtk.module in the release, and every licence text they name or the third parties hold."""
    modules: dict[str, VtkModule] = {}
    texts: dict[str, str] = {}
    wanted_texts: set[str] = set()
    with tarfile.open(tarball, "r:gz") as archive:
        members = {member.name: member for member in archive.getmembers() if member.isfile()}
        for name, member in members.items():
            if not name.endswith("/vtk.module"):
                continue
            raw = archive.extractfile(member)
            assert raw is not None
            text = raw.read().decode("utf-8", errors="replace")
            directory = name[: -len("/vtk.module")]
            module_name = (_field(text, "NAME") or [directory.rsplit("/", 1)[-1]])[0]
            # VTK's default library name is the module name without its namespace, prefixed with
            # `vtk` unless it already is: VTK::CommonCore -> vtkCommonCore, VTK::vtksys -> vtksys.
            bare = module_name.replace("VTK::", "")
            library = (_field(text, "LIBRARY_NAME") or [bare if bare.startswith("vtk") else "vtk" + bare])[0]
            custom_file = (_field(text, "SPDX_CUSTOM_LICENSE_FILE") or [None])[0]
            licence_files = _field(text, "LICENSE_FILES")
            module = VtkModule(
                name=module_name,
                library=library,
                spdx=" ".join(_field(text, "SPDX_LICENSE_IDENTIFIER")),
                copyright="\n".join(_field(text, "SPDX_COPYRIGHT_TEXT")),
                custom_licence_file=custom_file,
                custom_licence_name=(_field(text, "SPDX_CUSTOM_LICENSE_NAME") or [None])[0],
                licence_files=licence_files,
                depends=_field(text, "DEPENDS") + _field(text, "PRIVATE_DEPENDS"),
                third_party="\nTHIRD_PARTY" in text or text.startswith("THIRD_PARTY"),
                directory=directory,
            )
            modules[module_name] = module
            for named in [custom_file, *licence_files]:
                if named:
                    wanted_texts.add(f"{directory}/{named}")
            if module.third_party:
                # ThirdParty/<x>/vtk<x>/<licence-like file>, one or two levels down.
                prefix = f"{directory}/{library}/"
                found = False
                for candidate in members:
                    if candidate.startswith(prefix):
                        rest = candidate[len(prefix):]
                        parts = rest.split("/")
                        if len(parts) <= 2 and LICENCE_FILE_NAME.match(parts[-1]):
                            wanted_texts.add(candidate)
                            found = True
                if not found:
                    # A library whose authors put their terms in the header itself - SQLite disclaims
                    # copyright in sqlite3.h and ships no licence file. The header's leading comment
                    # is the statement, and is taken as such.
                    short = library[3:] if library.startswith("vtk") else library
                    for candidate in members:
                        if candidate.startswith(prefix):
                            base = candidate[len(prefix):]
                            if base.count("/") <= 1 and base.rsplit("/", 1)[-1] in (f"{short}.h", f"{short}3.h", f"{short}.hpp"):
                                wanted_texts.add(candidate)
        wanted_texts.add(f"VTK-{VTK_VERSION}/Copyright.txt")
        for name in sorted(wanted_texts):
            member = members.get(name)
            if member is None:
                continue
            raw = archive.extractfile(member)
            assert raw is not None
            content = raw.read().decode("utf-8", errors="replace")
            if name.endswith((".h", ".hpp")):
                # Only the leading comment block: the statement, not the interface.
                end = content.find("*/")
                content = content[: end + 2] if end != -1 else content[:2000]
            texts[name] = content
    return modules, texts


# ---- the closure: what is actually there --------------------------------------------------------


def closure_files(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)).replace(os.sep, "/") for path in root.rglob("*") if path.is_file())


def library_matches(library: str, filename: str) -> bool:
    """Whether a file in vtk.libs is this module's library: `vtkX-9.5.2.dll` on Windows,
    `libvtkX-9.5-<hash>.so.9.5.2` after auditwheel on Linux, `libvtkX-9.5.dylib` on macOS."""
    base = filename.rsplit("/", 1)[-1]
    # `vtkWrappingPythonCore3.11-9.5.2.dll` carries the Python version between the name and the
    # dash; `vtkhdf5_hl-9.5.2.dll` is HDF5's high-level library beside `vtkhdf5`.
    pattern = re.compile(r"^(lib)?" + re.escape(library) + r"(\d+\.\d+|_hl)?[-.]")
    return pattern.match(base) is not None


def attribute_vtk(
    files: list[str], modules: dict[str, VtkModule], texts: dict[str, str], engine: Path, claimed: dict[str, str]
) -> list[Component]:
    """VTK's own copyright, its licence variants among the modules present, and each third party
    the present modules depend on - with the files each one accounts for."""
    library_files = [f for f in files if "/vtk.libs/" in f or f.startswith("vtk.libs/") or "/vtkmodules/" in f]
    present: dict[str, list[str]] = {}
    for module in modules.values():
        mine = [f for f in library_files if library_matches(module.library, f)]
        if mine:
            present[module.name] = mine
    # viskores names its libraries without the vtk prefix.
    viskores = [f for f in library_files if f.rsplit("/", 1)[-1].startswith("viskores")]
    if viskores and "VTK::vtkviskores" in modules:
        present.setdefault("VTK::vtkviskores", []).extend(viskores)

    # The dependency walk: what a present module declares it needs is in the closure whether or not
    # a file of its own is - Eigen and scnlib are headers compiled into other libraries (E-046).
    reached: set[str] = set(present)
    frontier = list(present)
    while frontier:
        name = frontier.pop()
        for dependency in modules.get(name, VtkModule("", "", "", "", None, None, [], [], False, "")).depends:
            if dependency in modules and dependency not in reached:
                reached.add(dependency)
                frontier.append(dependency)

    components: list[Component] = []

    # 1. VTK itself: the wheel's own copyright file, and the python modules and bindings.
    dist_info = next((f for f in files if re.match(r"^vtk-[^/]+\.dist-info/LICENSE$", f)), None)
    own_files = [f for f in files if f.startswith("vtkmodules/") or f.startswith("vtk-") and ".dist-info/" in f]
    own_files += [f for name in present if not modules[name].third_party for f in present[name]]
    vtk = Component(
        name="VTK (Visualization Toolkit)",
        version=VTK_VERSION,
        licence="BSD-3-Clause",
        files=sorted(set(own_files)),
        note=(
            "The wheel's own LICENSE. Modules under a variant of the BSD licence are listed below with "
            "the variant's text, because those variants require the notice on all copies (E-045)."
        ),
    )
    if dist_info:
        vtk.texts.append((f"{engine.name}/_internal/{dist_info}", (engine / "_internal" / dist_info).read_text(encoding="utf-8", errors="replace")))
    elif f"VTK-{VTK_VERSION}/Copyright.txt" in texts:
        # The Linux wheel's metadata carries no licence file (only `License: BSD` in METADATA); the
        # text is the release's own Copyright.txt, which is what the Windows wheel's LICENSE is a copy of.
        metadata_files = sorted(f for f in files if re.match(r"^vtk-[^/]+\.dist-info/", f))
        vtk.texts.append((f"VTK-{VTK_VERSION} source: Copyright.txt (the wheel's dist-info holds {', '.join(f.rsplit('/', 1)[-1] for f in metadata_files) or 'nothing'})", texts[f"VTK-{VTK_VERSION}/Copyright.txt"]))
    else:
        raise NoticesError("VTK's copyright text is in neither the wheel's dist-info nor the source release")
    components.append(vtk)
    for f in vtk.files:
        claimed.setdefault(f, vtk.name)

    # 2. Licence variants among the present own modules: one component per distinct text.
    variants: dict[str, tuple[str, list[str], str]] = {}
    for name in sorted(present):
        module = modules[name]
        if module.third_party or not module.custom_licence_file:
            continue
        key = f"{module.directory}/{module.custom_licence_file}"
        text = texts.get(key)
        if text is None:
            raise NoticesError(f"{name} declares licence file {key}, which the release does not contain")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        label, carriers, _ = variants.get(digest, (module.custom_licence_name or module.spdx, [], text))
        carriers.append(f"{name} ({module.library})")
        variants[digest] = (label, carriers, text)
    seen_labels: dict[str, int] = {}
    for digest, (label, carriers, text) in sorted(variants.items(), key=lambda item: item[1][0]):
        seen_labels[label] = seen_labels.get(label, 0) + 1
        title = f"VTK modules under {label}" + (f" (text {seen_labels[label]})" if seen_labels[label] > 1 else "")
        components.append(Component(
            name=title,
            version=VTK_VERSION,
            licence=label,
            files=[],
            texts=[(f"VTK-{VTK_VERSION} source: {label}", text)],
            note="Carried by: " + ", ".join(carriers),
        ))

    # 3. Third parties reached.
    for name in sorted(reached):
        module = modules[name]
        if not module.third_party:
            continue
        mine = present.get(name, [])
        prefix = f"{module.directory}/{module.library}/"
        licence_texts = [(key, texts[key]) for key in sorted(texts) if key.startswith(prefix)]
        if not licence_texts and module.custom_licence_file:
            key = f"{module.directory}/{module.custom_licence_file}"
            if key in texts:
                licence_texts = [(key, texts[key])]
        if not licence_texts and not module.spdx and not module.copyright:
            # vtkm is an empty directory in 9.5 (superseded by viskores); an empty entry is honest.
            if name == "VTK::vtkm":
                continue
            raise NoticesError(f"third party {name} is in the closure and carries no licence text in the release")
        short = module.library[3:] if module.library.startswith("vtk") else module.library
        required = REQUIRED_STATEMENTS.get(short, "")
        component = Component(
            name=f"{short} (bundled by VTK as {module.library})",
            version=VTK_VERSION + " bundle",
            licence=module.spdx or "see the text",
            files=mine,
            texts=[(f"VTK-{VTK_VERSION} source: {key}", text) for key, text in licence_texts],
            note=(
                "Present as " + ", ".join(sorted(f.rsplit("/", 1)[-1] for f in mine))
                if mine
                else "No separate library file: header-only or linked into the libraries of the modules that depend on it"
            )
            + (f". Declared copyright: {module.copyright}" if module.copyright else "")
            + (f". {required}" if required else ""),
        )
        components.append(component)
        for f in mine:
            claimed.setdefault(f, component.name)

    # What the release carries and the closure does not reach, said rather than left to be inferred:
    # a reader comparing this list with VTK's ThirdParty tree would otherwise wonder.
    absent = sorted(
        m.library[3:] if m.library.startswith("vtk") else m.library
        for name, m in modules.items() if m.third_party and name not in reached
    )
    if absent:
        components.append(Component(
            name="VTK third parties in the release but not in this closure",
            version=VTK_VERSION,
            licence="not shipped",
            files=[],
            texts=[],
            note=(
                "Present in the VTK source release and reached by no module in this closure, so no file of "
                "theirs ships and no notice attaches: " + ", ".join(absent)
                + ". scnlib is a test dependency of CommonCore in 9.5.2 (E-207)."
            ),
        ))
    return components


# ---- the rest of the engine's closure ---------------------------------------------------------


def attribute_python(files: list[str], engine: Path, claimed: dict[str, str]) -> Component:
    library = next((f for f in files if re.match(r"^(python3\d+\.dll|libpython3\.\d+\.so.*|libpython3\.\d+\.dylib)$", f.rsplit("/", 1)[-1]) and "/" not in f), None)
    if library is None:
        raise NoticesError("no Python runtime library found at the top of _internal")
    match = re.search(r"python3\.?(\d+)", library)
    minor = int(match.group(1)) if match else -1
    running = f"{sys.version_info.major}.{sys.version_info.minor}"
    if minor != sys.version_info.minor:
        raise NoticesError(f"the closure carries Python 3.{minor} ({library}) but this generator runs on {running}; run it with the interpreter that froze the engine")
    base = Path(sys.base_prefix)
    candidates = [base / "LICENSE.txt", base / "LICENSE", base / "lib" / f"python{running}" / "LICENSE.txt"]
    licence = next((c for c in candidates if c.exists()), None)
    if licence is None:
        raise NoticesError(f"the interpreter's LICENSE.txt was not found under {base}")
    mine = [f for f in files if (
        "/" not in f and (f == library or f.endswith(".pyd") or f.endswith(".so") or f == "base_library.zip")
        or f.startswith("lib-dynload/")
        or f.startswith("lib/")
        or re.match(r"^(libffi|libcrypto|libssl|sqlite3|libsqlite3|libz|zlib1|libbz2|liblzma|libexpat|libmpdec|libgcc|libstdc)", f.rsplit("/", 1)[-1]) is not None and "/" not in f
    )]
    component = Component(
        name=f"Python {running} (interpreter and standard library)",
        version=platform_python_version(),
        licence="PSF-2.0 (see the text: it also carries the notices of what the interpreter itself bundles)",
        files=mine,
        texts=[(str(licence), licence.read_text(encoding="utf-8", errors="replace"))],
        note="Frozen by PyInstaller, whose own licence page says the bundle needs no notice for PyInstaller itself (E-204)",
    )
    for f in mine:
        claimed.setdefault(f, component.name)
    return component


def platform_python_version() -> str:
    return sys.version.split()[0]


def attribute_dist_info(files: list[str], engine: Path, claimed: dict[str, str], name: str, code_prefixes: tuple[str, ...]) -> Component:
    info = next((f for f in files if re.match(rf"^{name}-[^/]+\.dist-info/METADATA$", f)), None)
    if info is None:
        raise NoticesError(f"{name}'s metadata is not in the closure (was --copy-metadata {name} given?)")
    metadata = (engine / "_internal" / info).read_text(encoding="utf-8", errors="replace")
    version = re.search(r"^Version:\s*(\S+)", metadata, re.M)
    expression = re.search(r"^License-Expression:\s*(.+)$", metadata, re.M)
    plain = re.search(r"^License:\s*(.+)$", metadata, re.M)
    directory = info.rsplit("/", 1)[0]
    texts = [
        (f"{engine.name}/_internal/{f}", (engine / "_internal" / f).read_text(encoding="utf-8", errors="replace"))
        for f in files
        if f.startswith(directory + "/") and LICENCE_FILE_NAME.match(f.rsplit("/", 1)[-1])
    ]
    if not texts:
        raise NoticesError(f"{name}'s dist-info carries no licence file")
    mine = [f for f in files if f.startswith(directory + "/") or any(f.startswith(p) for p in code_prefixes)]
    component = Component(
        name=name,
        version=version.group(1) if version else "?",
        licence=(
            expression.group(1).strip() if expression
            else plain.group(1).strip() if plain and len(plain.group(1).strip()) <= 80 and not plain.group(1).strip().startswith("Copyright")
            else "see the text"
        ),
        files=mine,
        texts=texts,
    )
    for f in mine:
        claimed.setdefault(f, component.name)
    return component


def attribute_bundled_runtime(files: list[str], claimed: dict[str, str]) -> list[Component]:
    components: list[Component] = []
    microsoft = [f for f in files if re.match(r"^(VCRUNTIME|vcruntime|msvcp|MSVCP|api-ms-win-|ucrtbase|concrt|vcomp)", f.rsplit("/", 1)[-1])]
    if microsoft:
        component = Component(
            name="Microsoft Visual C++ Runtime",
            version="14.x (Visual Studio 2015-2022 binary-compatible runtime)",
            licence="Microsoft Software License Terms (Visual Studio), redistributable files",
            files=microsoft,
            texts=[],
            note=(
                "Microsoft's redistribution page: distribution of the runtime's individual binaries is "
                "subject to the Microsoft Software License Terms, and app-local deployment next to the "
                "executable is permitted though not recommended for servicing (E-205). The files came "
                "inside the VTK wheel, placed there by delvewheel."
            ),
        )
        components.append(component)
        for f in microsoft:
            claimed.setdefault(f, component.name)
    openxr = [f for f in files if f.rsplit("/", 1)[-1].startswith("openxr_loader")]
    if openxr:
        text = (VENDORED / "openxr-loader.txt").read_text(encoding="utf-8")
        component = Component(
            name="OpenXR loader (Khronos)",
            version="bundled with VTK " + VTK_VERSION,
            licence="Apache-2.0 OR MIT (MIT exercised)",
            files=openxr,
            texts=[(str(VENDORED / "openxr-loader.txt"), text)],
            note="Placed inside the VTK wheel by delvewheel; not part of VTK's ThirdParty tree (E-206)",
        )
        components.append(component)
        for f in openxr:
            claimed.setdefault(f, component.name)
    return components


def attribute_product(files: list[str], claimed: dict[str, str]) -> Component:
    mine = [f for f in files if f not in claimed]
    # What is left at this point is the product's own frozen code and PyInstaller's bookkeeping.
    own = [f for f in mine if f.startswith(("service/", "engine/", "domain_core/")) or f.endswith((".pyz", ".toc", ".manifest")) or f in ("struct.pyd",)]
    own += [f for f in files if f.startswith(("THIRD-PARTY-NOTICES", "notices.json"))]
    component = Component(
        name="SOLVIA (this product)",
        version=(ROOT / "src" / "shell" / "package.json").exists() and json.loads((ROOT / "src" / "shell" / "package.json").read_text(encoding="utf-8")).get("version", "?") or "?",
        licence="FSL-1.1-MIT",
        files=own,
        texts=[("LICENSE.md", (ROOT / "LICENSE.md").read_text(encoding="utf-8", errors="replace"))],
    )
    for f in own:
        claimed.setdefault(f, component.name)
    return component


# ---- the shell and the interface ------------------------------------------------------------------


def attribute_app(app: Path, claimed_app: dict[str, str], claimed_engine: dict[str, str]) -> list[Component]:
    files = closure_files(app)
    components: list[Component] = []
    electron_licence = next((f for f in files if f.startswith("LICENSE.electron")), None)
    chromium = next((f for f in files if f.startswith("LICENSES.chromium")), None)
    if not electron_licence or not chromium:
        raise NoticesError("the unpacked application lacks LICENSE.electron.txt or LICENSES.chromium.html")
    shell_package = json.loads((ROOT / "src" / "shell" / "package.json").read_text(encoding="utf-8"))
    electron_version = shell_package["devDependencies"]["electron"]
    electron_files = [f for f in files if not f.startswith("resources/") or f in ("resources/app.asar",) and False]
    electron = Component(
        name="Electron (with Chromium, Node.js and V8)",
        version=electron_version,
        licence="MIT (Electron); Chromium and its third parties as listed in LICENSES.chromium.html next to the executable",
        files=electron_files,
        texts=[(electron_licence, (app / electron_licence).read_text(encoding="utf-8", errors="replace"))],
        note=f"{chromium} next to the executable is Chromium's own generated list and is part of these notices by reference",
    )
    components.append(electron)
    for f in electron_files:
        claimed_app.setdefault(f, electron.name)

    lock = json.loads((ROOT / "src" / "ui" / "package-lock.json").read_text(encoding="utf-8"))
    ui_package = json.loads((ROOT / "src" / "ui" / "package.json").read_text(encoding="utf-8"))
    runtime = set(ui_package.get("dependencies", {}))
    # Transitive runtime dependencies from the lockfile.
    packages = lock.get("packages", {})
    frontier = list(runtime)
    while frontier:
        name = frontier.pop()
        entry = packages.get(f"node_modules/{name}", {})
        for dependency in entry.get("dependencies", {}):
            if dependency not in runtime:
                runtime.add(dependency)
                frontier.append(dependency)
    ui_files = [f for f in files if f.startswith("resources/ui/")]
    for name in sorted(runtime):
        entry = packages.get(f"node_modules/{name}", {})
        licence_file = next((p for p in (ROOT / "src" / "ui" / "node_modules" / name).glob("LICENSE*")), None)
        if licence_file is None:
            raise NoticesError(f"{name} ships no LICENSE file in node_modules")
        component = Component(
            name=name,
            version=entry.get("version", "?"),
            licence=entry.get("license", "see the text"),
            files=[],
            texts=[(str(licence_file.relative_to(ROOT)), licence_file.read_text(encoding="utf-8", errors="replace"))],
            note="Bundled into the interface's assets by Vite; the bundle is resources/ui/assets/",
        )
        components.append(component)
    product_files = [
        f for f in files
        if f.startswith(("resources/app.asar", "resources/ui/", "resources/notices", "THIRD-PARTY-NOTICES"))
    ]
    for f in product_files:
        claimed_app.setdefault(f, "SOLVIA (this product)")
    for f in ui_files:
        claimed_app.setdefault(f, "SOLVIA (this product)")
    # The engine inside the application is the same closure the engine pass attributed, file for
    # file; its claims carry over by path rather than being computed a second time.
    for f in files:
        if f.startswith("resources/engine/_internal/"):
            inner = f[len("resources/engine/_internal/"):]
            if inner in claimed_engine:
                claimed_app.setdefault(f, claimed_engine[inner])
        elif f.startswith("resources/engine/"):
            claimed_app.setdefault(f, "SOLVIA (this product)")
    return components


# ---- writing ----------------------------------------------------------------------------------------


def render(components: list[Component], engine: Path, app: Path | None) -> str:
    lines = [
        "THIRD-PARTY NOTICES",
        "",
        "This file lists every component shipped with SOLVIA, the terms each one states for itself, and",
        "where in the installation the component is. It is generated from the files actually shipped,",
        "not from a list kept by hand (XC-025). Sections reproduce each component's own licence text",
        "verbatim; a note above a text says where it was taken from.",
        "",
        f"Engine closure: {engine.name}/" + (f"   Application: {app.name}/" if app else ""),
        "",
    ]
    for index, component in enumerate(components, 1):
        lines.append("=" * 100)
        lines.append(f"{index}. {component.name}  -  version {component.version}")
        lines.append(f"   licence: {component.licence}")
        if component.note:
            lines.append(f"   {component.note}")
        if component.files:
            shown = sorted(component.files)
            head = shown[:12]
            lines.append(f"   files ({len(shown)}): " + ", ".join(f.rsplit('/', 1)[-1] for f in head) + (" ..." if len(shown) > 12 else ""))
        lines.append("")
        for source, text in component.texts:
            lines.append(f"--- {source} ---")
            lines.append(text.rstrip("\n"))
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", type=Path, default=ENGINE_DEFAULT, help="the frozen engine directory")
    parser.add_argument("--app", type=Path, default=None, help="the unpacked application directory, if built")
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--verify", action="store_true", help="fail unless every shipped file is attributed")
    arguments = parser.parse_args(argv)

    engine: Path = arguments.engine
    internal = engine / "_internal"
    if not internal.is_dir():
        raise NoticesError(f"{internal} is not a frozen engine directory")
    files = closure_files(internal)
    executable = [f.name for f in engine.iterdir() if f.is_file()]

    claimed: dict[str, str] = {}
    components: list[Component] = []
    tarball = fetch_vtk_source()
    modules, texts = read_vtk_modules(tarball)
    components += attribute_vtk(files, modules, texts, engine, claimed)
    # numpy.libs/ holds the OpenBLAS the wheel bundles; its terms are in NumPy's LICENSE.txt, which
    # appends the notices of everything the wheel carries.
    components.append(attribute_dist_info(files, engine, claimed, "numpy", ("numpy/", "numpy.libs/")))
    components += attribute_bundled_runtime(files, claimed)
    components.append(attribute_python(files, engine, claimed))
    components.append(attribute_product(files, claimed))
    product = next(c for c in components if c.name == "SOLVIA (this product)")
    for name in executable:
        claimed.setdefault(name, product.name)
        product.files.append(name)

    app: Path | None = arguments.app
    claimed_app: dict[str, str] = {}
    if app is not None:
        components += attribute_app(app, claimed_app, claimed)

    unattributed = [f for f in files if f not in claimed]
    unattributed_app = [f for f in (closure_files(app) if app else []) if f not in claimed_app]

    arguments.out.mkdir(parents=True, exist_ok=True)
    (arguments.out / "THIRD-PARTY-NOTICES.txt").write_text(render(components, engine, app), encoding="utf-8", newline="\n")
    (arguments.out / "notices.json").write_text(
        json.dumps({"components": [c.as_json() for c in components], "unattributed": unattributed + unattributed_app}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n",
    )
    summary = {
        "components": len(components),
        "engine_files": len(files) + len(executable),
        "app_files": len(closure_files(app)) if app else 0,
        "unattributed": unattributed[:20] + unattributed_app[:20],
        "unattributed_count": len(unattributed) + len(unattributed_app),
        "out": str(arguments.out),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if arguments.verify and summary["unattributed_count"]:
        print("notices incomplete: files above are shipped and attributed to nothing", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except NoticesError as error:
        print(f"notices: {error}", file=sys.stderr)
        raise SystemExit(2)
