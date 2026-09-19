"""The notices generator's rules, without the closure (XC-025).

The generator itself needs a frozen engine and the VTK source release, which CI's package job has
and this suite does not. What can be checked here is the arithmetic it rests on: which library file
belongs to which module, and how a module description is read. A wrong answer to either is a file
attributed to the wrong component - or to none, which the generator refuses - so these are the
rules a person reading the notices is trusting.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging"))

from notices import REQUIRED_STATEMENTS, Component, _field, library_matches, soname  # noqa: E402


class TestALibraryFileBelongsToItsModule:
    def test_windows_and_linux_and_mac_spellings(self) -> None:
        assert library_matches("vtkCommonCore", "vtk.libs/vtkCommonCore-9.5.2.dll")
        assert library_matches("vtkCommonCore", "vtk.libs/libvtkCommonCore-9.5-abc123.so.9.5")
        assert library_matches("vtkCommonCore", "vtk.libs/libvtkCommonCore-9.5.dylib")

    def test_a_python_version_between_the_name_and_the_dash(self) -> None:
        """vtkWrappingPythonCore3.11-9.5.2.dll: found unattributed on the first run."""
        assert library_matches("vtkWrappingPythonCore", "vtk.libs/vtkWrappingPythonCore3.11-9.5.2.dll")

    def test_hdf5_s_high_level_library_belongs_to_hdf5(self) -> None:
        assert library_matches("vtkhdf5", "vtk.libs/vtkhdf5_hl-9.5.2.dll")
        assert library_matches("vtkhdf5", "vtk.libs/vtkhdf5-9.5.2.dll")

    def test_a_prefix_is_not_a_match(self) -> None:
        """vtkIO must not claim vtkIOXML, and vtkCommon must not claim vtkCommonCore: a file
        attributed twice is attributed to whichever module was asked first, silently."""
        assert not library_matches("vtkIO", "vtk.libs/vtkIOXML-9.5.2.dll")
        assert not library_matches("vtkCommon", "vtk.libs/vtkCommonCore-9.5.2.dll")
        assert not library_matches("vtkhdf5", "vtk.libs/vtkhdf5_hlx-9.5.2.dll")


class TestAModuleDescriptionIsReadAsVtkWritesIt:
    TEXT = (
        "NAME\n  VTK::CommonCore\n"
        "DEPENDS\n  VTK::kwiml\n  # a comment inside the block\n  VTK::vtksys\n"
        "PRIVATE_DEPENDS\n  VTK::fast_float\n"
        "TEST_DEPENDS\n  VTK::scn\n"
        "THIRD_PARTY\n"
    )

    def test_each_key_yields_its_own_indented_lines_without_comments(self) -> None:
        assert _field(self.TEXT, "NAME") == ["VTK::CommonCore"]
        assert _field(self.TEXT, "DEPENDS") == ["VTK::kwiml", "VTK::vtksys"]
        assert _field(self.TEXT, "PRIVATE_DEPENDS") == ["VTK::fast_float"]

    def test_test_dependencies_are_a_separate_key_and_not_shipped(self) -> None:
        """E-046 read scnlib as being on CommonCore's mandatory path; in 9.5.2 it is TEST_DEPENDS,
        which the closure walk does not follow, so no file of it ships and no notice attaches
        (E-207). The distinction is exactly one key name."""
        assert _field(self.TEXT, "TEST_DEPENDS") == ["VTK::scn"]
        assert "VTK::scn" not in _field(self.TEXT, "DEPENDS") + _field(self.TEXT, "PRIVATE_DEPENDS")

    def test_a_missing_key_is_empty_not_an_error(self) -> None:
        assert _field(self.TEXT, "LICENSE_FILES") == []


class TestTheStatementsSomeLicencesRequire:
    def test_the_four_e046_names_are_present_and_say_what_they_must(self) -> None:
        assert "FreeType Project" in REQUIRED_STATEMENTS["freetype"]
        assert "Independent JPEG Group" in REQUIRED_STATEMENTS["jpeg"]
        assert "MPL-2.0" in REQUIRED_STATEMENTS["eigen"] and "https://" in REQUIRED_STATEMENTS["eigen"]
        assert "modified" in REQUIRED_STATEMENTS["gl2ps"] and "https://" in REQUIRED_STATEMENTS["gl2ps"]


class TestASystemLibraryIsNamedAsItsPackageNamesIt:
    def test_the_hash_pyinstaller_or_auditwheel_added_is_removed_and_the_version_kept_to_the_major(self) -> None:
        assert soname("libXcursor-1a09904e.so.1.0.2") == "libXcursor.so.1"
        assert soname("libgfortran-040039e1-0352e75f.so.5.0.0") == "libgfortran.so.5"
        assert soname("libX11.so.6") == "libX11.so.6"
        assert soname("libreadline.so.8") == "libreadline.so.8"


class TestTheShapeTheScreenReadsIsTheShapeTheGeneratorWrites:
    def test_a_component_serialises_to_exactly_the_keys_the_interface_declares(self) -> None:
        """`NoticeComponent` in src/ui/client/shell.ts is the other half of this; the two sides cannot
        import from each other, so the keys are pinned here and named there."""
        one = Component(name="x", version="1", licence="MIT", files=["a"], texts=[("s", "t")], note="n")

        assert set(one.as_json()) == {"name", "version", "licence", "files", "texts", "note"}
        assert one.as_json()["texts"] == [{"source": "s", "text": "t"}]
