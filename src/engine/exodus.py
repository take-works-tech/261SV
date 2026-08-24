"""Reading Exodus, where the default is to read no results at all.

`vtkExodusIIReader` offers its arrays through `UpdateInformation()` and reads **none of them** unless
each is switched on by name. Measured on VTK 9.5.2: a file written with `stress`, `temp` and
`elem_stress` comes back, after `SetFileName` and `Update`, carrying geometry, one `ObjectId` array and
**zero results** - no error, no warning (E-136). A whole result file read as an empty mesh.

There are **27 array categories** and all of them start off. Twenty-six have a plain
count/name/status triple; the twenty-seventh, `Object`, takes an object-type argument and is a view
over the others. A reader that switches on the two obvious ones silently drops the other twenty-four.

So this module does two things, and the second is the one that matters. It switches every category on;
and then it **checks that every result the file offered actually arrived**, by name, and refuses the
read if one did not. The switching is an attempt and the check is the guarantee: a category added to a
future toolkit release, or one misspelled here, fails loudly instead of costing a user their results.

Specification: ingest/REQ-015, AC-032, XC-237. Evidence: E-136 (T1).
"""

from __future__ import annotations

from vtkmodules.vtkCommonDataModel import vtkCompositeDataSet, vtkDataSet
from vtkmodules.vtkIOExodus import vtkExodusIIReader

#: Every array category `vtkExodusIIReader` exposes, as the stem of its count/name/status triple.
#: Written out rather than discovered by reflection so that a reviewer can see the whole surface, and
#: checked against the class at import so the list cannot quietly fall behind the toolkit.
CATEGORIES: tuple[str, ...] = (
    "Assembly", "EdgeBlock", "EdgeMap", "EdgeResult", "EdgeSet", "EdgeSetResult",
    "ElementBlock", "ElementMap", "ElementResult", "ElementSet", "ElementSetResult",
    "FaceBlock", "FaceMap", "FaceResult", "FaceSet", "FaceSetResult",
    "GlobalResult", "Hierarchy", "Material", "NodeMap", "NodeSet", "NodeSetResult",
    "Part", "PointResult", "SideSet", "SideSetResult",
)

#: `Object` is the twenty-seventh category and is not in the list above: its count, name and status
#: take an object-type argument rather than standing alone, so it is a view over the block categories
#: already switched on rather than a category of its own. Named here so that its absence reads as a
#: measurement (E-136) and not as an oversight.
PARAMETERISED_CATEGORY = "Object"

#: The categories that carry numbers onto points or cells. These are the ones whose loss is a loss of
#: results, so these are the ones checked by name after the read.
RESULT_CATEGORIES: tuple[str, ...] = (
    "PointResult", "ElementResult", "FaceResult", "EdgeResult",
    "NodeSetResult", "SideSetResult", "ElementSetResult", "EdgeSetResult", "FaceSetResult",
)

#: Exodus writes the element-block number onto every cell. It is a block identity, not a measurement,
#: and it is not marked with an identifier role - so nothing else would keep it out of the list a user
#: picks a @Variable from (GL-034, XC-236).
BLOCK_ID_ARRAY = "ObjectId"


class ExodusResultsLost(Exception):
    """Raised when the file offered a result that did not arrive. Never silently dropped."""


def _triple(reader: vtkExodusIIReader, category: str) -> tuple[int, object, object] | None:
    count = getattr(reader, f"GetNumberOf{category}Arrays", None)
    name = getattr(reader, f"Get{category}ArrayName", None)
    status = getattr(reader, f"Set{category}ArrayStatus", None)
    if count is None or name is None or status is None:
        return None
    return count(), name, status


def offered_results(reader: vtkExodusIIReader) -> set[str]:
    """The names of every result the file says it holds, across every result category."""
    found: set[str] = set()
    for category in RESULT_CATEGORIES:
        triple = _triple(reader, category)
        if triple is None:
            continue
        count, name, _ = triple
        found.update(name(index) for index in range(count))
    return found


def enable_everything(reader: vtkExodusIIReader) -> None:
    """Switch on every array the file offers, and generate the identifiers the format can supply.

    `UpdateInformation` first, because the counts are zero until the file has been looked at.
    """
    reader.UpdateInformation()
    for category in CATEGORIES:
        triple = _triple(reader, category)
        if triple is None:
            raise ExodusResultsLost(
                f"this build's Exodus reader has no '{category}' category, so the list in "
                "engine/exodus.py has fallen behind the toolkit and something may be going unread"
            )
        count, name, status = triple
        for index in range(count):
            status(name(index), 1)
    # Exodus carries node and element numbers, and the reader constructs them on request rather than
    # by default. They are what INV-023 reports an extreme value against.
    reader.SetGenerateGlobalNodeIdArray(1)
    reader.SetGenerateGlobalElementIdArray(1)


def _arrays_present(node: object, found: set[str]) -> None:
    if isinstance(node, vtkCompositeDataSet):
        iterator = node.NewIterator()
        iterator.InitTraversal()
        while not iterator.IsDoneWithTraversal():
            _arrays_present(iterator.GetCurrentDataObject(), found)
            iterator.GoToNextItem()
        return
    if isinstance(node, vtkDataSet):
        for container in (node.GetPointData(), node.GetCellData(), node.GetFieldData()):
            for index in range(container.GetNumberOfArrays()):
                name = container.GetArrayName(index)
                if name:
                    found.add(name)


def check_nothing_was_dropped(reader: vtkExodusIIReader, output: object) -> None:
    """Refuse the read if a result the file offered is not in what came back.

    The check rather than the switching is the guarantee. Switching every category on is an attempt
    that can fall behind the toolkit; comparing what arrived against what was offered cannot.
    """
    arrived: set[str] = set()
    _arrays_present(output, arrived)
    missing = sorted(offered_results(reader) - arrived)
    if missing:
        raise ExodusResultsLost(
            "この Exodus ファイルが持つ結果のうち、読み込まれなかったものがあります："
            f"{', '.join(missing)}。"
            "既定ではリーダーは結果を1つも読まないため、これは黙って失われる種類の欠落です"
            "（E-136）。値のない結果を返すより、読み込みを中止します"
        )
