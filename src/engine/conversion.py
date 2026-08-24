"""Performing the conversions CT-012 names, at the cost CT-012 states, before it is paid.

Nine data object types are accepted after one named conversion. This module runs exactly the chain the
contract names for each - not a chain that happens to work - so that what the specification says and
what the code does cannot be two answers.

**The cost is computed from the unconverted object.** A structured, rectilinear or image grid knows its
cell count from its dimensions and a hyper-tree grid knows its leaf count, so the size of the result is
knowable before anything expands (E-132). That is what makes ingest/AC-032 possible as written: the cost
is stated *before* the conversion, not discovered once the memory has been spent.

Specification: CT-012, LIM-002, ingest/AC-032, ingest/TASK-029.
"""

from __future__ import annotations

from vtkmodules.vtkCommonDataModel import (
    vtkDataObject,
    vtkExplicitStructuredGrid,
    vtkHyperTreeGrid,
    vtkImageData,
    vtkRectilinearGrid,
    vtkStructuredGrid,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkFiltersCore import vtkAppendFilter, vtkExplicitStructuredGridToUnstructuredGrid
from vtkmodules.vtkFiltersGeneral import vtkImageDataToPointSet, vtkRectilinearGridToPointSet
from vtkmodules.vtkFiltersHyperTree import vtkHyperTreeGridToUnstructuredGrid

from domain_core.conversion import ConversionRecord, ConversionTooLarge
from domain_core.object_compatibility import Disposition, handling
from engine.limits import MAX_INTERACTIVE_TRIANGLES

TARGET = "vtkUnstructuredGrid"


def cost_in_cells(data: vtkDataObject) -> int:
    """How many cells the conversion will produce, read before it runs.

    A hyper-tree grid reports 0 cells until it is expanded, so its leaves are counted instead - that is
    the number the expansion produces and the number the format exists to avoid materialising.
    """
    if isinstance(data, vtkHyperTreeGrid):
        return int(data.GetNumberOfLeaves())
    return int(data.GetNumberOfCells())


def _preserved(data: vtkDataObject) -> dict[str, tuple[float, ...]]:
    """Facts that are implicit in the source and absent from the result.

    An image grid's spacing is the one number in a voxel result that carries a length. Once the points
    are explicit nothing remembers it, so it is captured here or it is lost.
    """
    if isinstance(data, vtkImageData):
        return {
            "spacing": tuple(float(v) for v in data.GetSpacing()),
            "origin": tuple(float(v) for v in data.GetOrigin()),
            "dimensions": tuple(float(v) for v in data.GetDimensions()),
        }
    if isinstance(data, vtkRectilinearGrid):
        return {"dimensions": tuple(float(v) for v in data.GetDimensions())}
    if isinstance(data, (vtkStructuredGrid, vtkExplicitStructuredGrid)):
        # `GetDimensions` on these takes an out-parameter in the Python wrapping, so the extent - the
        # same information, and the form the file stores - is read instead.
        return {"extent": tuple(float(v) for v in data.GetExtent())}
    return {}


def _to_point_set(data: vtkDataObject) -> vtkDataObject:
    """The first half of the chains that have two, exactly as CT-012 names them."""
    if isinstance(data, vtkImageData):
        step = vtkImageDataToPointSet()
    elif isinstance(data, vtkRectilinearGrid):
        step = vtkRectilinearGridToPointSet()
    else:
        return data
    step.SetInputData(data)
    step.Update()
    return step.GetOutput()


def to_unstructured(
    data: vtkDataObject, *, budget: int = MAX_INTERACTIVE_TRIANGLES, accepted: bool = False
) -> tuple[vtkUnstructuredGrid, ConversionRecord]:
    """Convert one accepted-after-conversion object, or refuse the cost before paying it.

    `accepted` is the user having been shown the cost and said yes. Without it a conversion whose
    result exceeds the budget raises `ConversionTooLarge` rather than running - the count came from the
    source, so refusing costs nothing and the choice is still the user's.
    """
    name = data.GetClassName()
    row = handling(name)
    if row.disposition is not Disposition.CONVERT:
        raise ValueError(
            f"CT-012 says {name} is '{row.disposition.value}', not a conversion; running one anyway "
            "would make the code and the contract two answers"
        )

    cells = cost_in_cells(data)
    if not accepted and cells > budget:
        raise ConversionTooLarge(name, cells, budget, row.costs or "")

    preserved = _preserved(data)
    intermediate = _to_point_set(data)

    if isinstance(intermediate, vtkHyperTreeGrid):
        step = vtkHyperTreeGridToUnstructuredGrid()
        step.SetInputData(intermediate)
        step.Update()
        result = step.GetOutput()
    elif isinstance(intermediate, vtkExplicitStructuredGrid):
        step = vtkExplicitStructuredGridToUnstructuredGrid()
        step.SetInputData(intermediate)
        step.Update()
        result = step.GetOutput()
    else:
        append = vtkAppendFilter()
        append.SetInputData(intermediate)
        append.Update()
        result = append.GetOutput()

    return result, ConversionRecord(
        source_type=name,
        target_type=TARGET,
        via=row.via or "",
        costs=row.costs or "",
        cells=int(result.GetNumberOfCells()),
        preserved=preserved,
    )
