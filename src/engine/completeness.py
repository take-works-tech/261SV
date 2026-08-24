"""Reading everything a file offers, and proving nothing was dropped.

Two of the toolkit's readers for formats this product's users actually work in **read no results at
all** unless each array is switched on by name, and neither says so:

* `vtkExodusIIReader` - 27 array categories, every status 0 (E-136);
* `vtkCGNSReader` - three `vtkDataArraySelection` objects, every array off (E-137).

Two formats with two unrelated APIs and the same defect is a pattern rather than a quirk, so the answer
lives here rather than being written a third time for the third format. What a reader must supply is
small: how to list what the file offers, and how to switch it all on. What this module supplies is the
part that matters - **the check that what was offered arrived**.

The distinction is the whole point. Switching everything on is an *attempt*: it can fall behind a
toolkit release, misspell a category, or miss an API that did not exist when it was written. Comparing
what came back against what the file said it held cannot. A result that is missing stops the read,
because it is not an absent value - XC-001 governs a value the file does not have, and this is a value
the file does have and the reader did not fetch.

Specification: ingest/REQ-015, AC-032, XC-237. Evidence: E-136 (T1), E-137 (T1).
"""

from __future__ import annotations

from vtkmodules.vtkCommonDataModel import vtkCompositeDataSet, vtkDataSet


class ResultsLost(Exception):
    """Raised when a file offered a result that did not arrive. Never silently dropped."""


def enable_selections(*selections: object) -> None:
    """Switch on every array of each `vtkDataArraySelection` given."""
    for selection in selections:
        selection.EnableAllArrays()


def names_in_selections(*selections: object) -> set[str]:
    """Every array name the given selections offer."""
    found: set[str] = set()
    for selection in selections:
        found.update(
            selection.GetArrayName(index) for index in range(selection.GetNumberOfArrays())
        )
    return {name for name in found if name}


def arrays_present(node: object, found: set[str] | None = None) -> set[str]:
    """Every array name anywhere in a data object, walking composites to their leaves."""
    found = set() if found is None else found
    if isinstance(node, vtkCompositeDataSet):
        iterator = node.NewIterator()
        iterator.InitTraversal()
        while not iterator.IsDoneWithTraversal():
            arrays_present(iterator.GetCurrentDataObject(), found)
            iterator.GoToNextItem()
        return found
    if isinstance(node, vtkDataSet):
        for container in (node.GetPointData(), node.GetCellData(), node.GetFieldData()):
            for index in range(container.GetNumberOfArrays()):
                name = container.GetArrayName(index)
                if name:
                    found.add(name)
    return found


def check_nothing_was_dropped(offered: set[str], output: object, *, evidence: str) -> None:
    """Refuse the read if a result the file offered is not in what came back.

    `evidence` names the measurement behind the refusal, because a user meeting this message is being
    told something surprising about their file's reader and is entitled to know it was measured.
    """
    missing = sorted(offered - arrays_present(output))
    if missing:
        raise ResultsLost(
            "このファイルが持つ結果のうち、読み込まれなかったものがあります："
            f"{', '.join(missing)}。"
            "このリーダーは既定では結果を読まないため、これは黙って失われる種類の欠落です"
            f"（{evidence}）。値のない結果を返すより、読み込みを中止します"
        )
