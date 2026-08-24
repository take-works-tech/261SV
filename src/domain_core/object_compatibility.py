"""What this product does with each data object type it may be handed (CT-012).

**Generated from `specs/contracts/schema/CT-012.json` by `validate/check_object_compatibility.py --write`.**
Do not edit: `validate/check_object_compatibility.py` regenerates this file and fails if it differs, so
an edit here is a build failure rather than a divergence nobody notices. Change the contract instead.

A closed table with a default of refusal. A type absent from it is a type the product would meet without
a decision having been made about it, which is why the gate compares the keys against the toolkit's own
measured list (E-132) as well as against this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Disposition(str, Enum):
    """What happens to a data object of a given type."""

    READ = "read"              # accepted as it stands
    CONVERT = "convert"        # accepted after one named conversion, whose cost is stated
    DECOMPOSE = "decompose"    # taken apart into the parts of one @Case
    REFUSE = "refuse"          # named and refused; never approximated, never silently emptied


@dataclass(frozen=True, slots=True)
class Handling:
    """One row of CT-012's data-object table."""

    disposition: Disposition
    # `convert` only: the filter chain CT-012 names, and what running it costs.
    via: str | None = None
    costs: str | None = None
    # `refuse` only: why, in the words the user is shown.
    reason: str | None = None
    # `decompose` only: what it comes apart into.
    into: str | None = None

    @property
    def is_accepted(self) -> bool:
        return self.disposition is not Disposition.REFUSE


HANDLING: dict[str, Handling] = {
    "vtkPolyData": Handling(
        Disposition.READ,
    ),
    "vtkUnstructuredGrid": Handling(
        Disposition.READ,
    ),
    "vtkPointSet": Handling(
        Disposition.REFUSE, reason="points with no cells, and no reader in this build produces one: a point cloud arrives as a vtkPolyData of vertex cells, which is read. Marking it read as well would be a second path with nothing behind it, and the check that found this said so",
    ),
    "vtkStructuredGrid": Handling(
        Disposition.CONVERT, via="vtkAppendFilter", costs="connectivity becomes explicit, so memory grows by the connectivity array the file did not store; no value changes and no cell is added",
    ),
    "vtkRectilinearGrid": Handling(
        Disposition.CONVERT, via="vtkRectilinearGridToPointSet then vtkAppendFilter", costs="the three coordinate vectors become one explicit point array; memory grows from O(nx+ny+nz) to O(nx*ny*nz) and no value changes",
    ),
    "vtkImageData": Handling(
        Disposition.CONVERT, via="vtkImageDataToPointSet then vtkAppendFilter", costs="origin and spacing are implicit in the file and explicit afterwards; both are recorded on the @Dataset because after the conversion nothing can recover them, and a spacing is the one number in a voxel result that carries a length unit",
    ),
    "vtkStructuredPoints": Handling(
        Disposition.CONVERT, via="as vtkImageData, of which it is the older name", costs="origin and spacing are implicit in the file and explicit afterwards; both are recorded on the @Dataset because after the conversion nothing can recover them, and a spacing is the one number in a voxel result that carries a length unit（vtkImageData と同じ）",
    ),
    "vtkUniformGrid": Handling(
        Disposition.CONVERT, via="as vtkImageData", costs="origin and spacing are implicit in the file and explicit afterwards; both are recorded on the @Dataset because after the conversion nothing can recover them, and a spacing is the one number in a voxel result that carries a length unit（vtkImageData と同じ）, and its blanking becomes HIDDENCELL in the ghost array rather than being dropped - a blanked cell is a cell the file said to ignore, not a cell that is absent",
    ),
    "vtkExplicitStructuredGrid": Handling(
        Disposition.CONVERT, via="vtkExplicitStructuredGridToUnstructuredGrid", costs="the i,j,k address of each cell is lost unless it is kept as a cell field; a reservoir result is usually reported by that address",
    ),
    "vtkHyperTreeGrid": Handling(
        Disposition.CONVERT, via="vtkHyperTreeGridToUnstructuredGrid", costs="the tree is the compression; expanding it produces one cell per leaf and the memory is what the format existed to avoid. The cost is stated against LIM-002 before the conversion runs, never after",
    ),
    "vtkUniformHyperTreeGrid": Handling(
        Disposition.CONVERT, via="as vtkHyperTreeGrid", costs="the tree is the compression; expanding it produces one cell per leaf and the memory is what the format existed to avoid. The cost is stated against LIM-002 before the conversion runs, never after（vtkHyperTreeGrid と同じ）",
    ),
    "vtkCellGrid": Handling(
        Disposition.CONVERT, via="vtkCellGridToUnstructuredGrid", costs="the discontinuous-Galerkin basis does not survive: the conversion writes linear sub-cells. INV-009 therefore forbids reporting a number from the converted form, and the conversion is offered for display while the numbers wait for a path that reads the basis",
    ),
    "vtkTable": Handling(
        Disposition.READ,
    ),
    "vtkPartitionedDataSet": Handling(
        Disposition.DECOMPOSE, into="the partitions of one part",
    ),
    "vtkMultiPieceDataSet": Handling(
        Disposition.DECOMPOSE, into="the partitions of one part",
    ),
    "vtkPartitionedDataSetCollection": Handling(
        Disposition.DECOMPOSE, into="one part per dataset, each with its own partitions",
    ),
    "vtkMultiBlockDataSet": Handling(
        Disposition.DECOMPOSE, into="one part per leaf block, keeping the block names as the part hierarchy",
    ),
    "vtkOverlappingAMR": Handling(
        Disposition.REFUSE, reason="the levels overlap by construction: a refined region is present at every level above it, so a sum over the leaves counts it once per level. Until the level masking is read and applied, every aggregate over one is wrong by an amount that looks plausible - INV-010 one level up",
    ),
    "vtkNonOverlappingAMR": Handling(
        Disposition.REFUSE, reason="no reader in this build produces one, and accepting a type nothing can deliver would be an untested path pretending to be support",
    ),
    "vtkUniformGridAMR": Handling(
        Disposition.REFUSE, reason="the levels overlap by construction: a refined region is present at every level above it, so a sum over the leaves counts it once per level. Until the level masking is read and applied, every aggregate over one is wrong by an amount that looks plausible - INV-010 one level up（vtkOverlappingAMR と同じ）, of which it is the base",
    ),
    "vtkHierarchicalBoxDataSet": Handling(
        Disposition.REFUSE, reason="deprecated in the toolkit and superseded by vtkOverlappingAMR",
    ),
    "vtkPath": Handling(
        Disposition.REFUSE, reason="a two-dimensional drawing path used by the text renderer, not result geometry, although it is a vtkDataSet",
    ),
    "vtkMolecule": Handling(
        Disposition.REFUSE, reason="atoms and bonds are a different domain with their own units and their own conventions; reading one as a mesh of vertices would show it and mean nothing",
    ),
    "vtkGraph": Handling(
        Disposition.REFUSE, reason="a topology with no geometry this product can report on",
    ),
    "vtkDirectedGraph": Handling(
        Disposition.REFUSE, reason="a topology with no geometry this product can report on（vtkGraph と同じ）",
    ),
    "vtkUndirectedGraph": Handling(
        Disposition.REFUSE, reason="a topology with no geometry this product can report on（vtkGraph と同じ）",
    ),
    "vtkDirectedAcyclicGraph": Handling(
        Disposition.REFUSE, reason="a topology with no geometry this product can report on（vtkGraph と同じ）",
    ),
    "vtkReebGraph": Handling(
        Disposition.REFUSE, reason="a topology with no geometry this product can report on（vtkGraph と同じ）",
    ),
    "vtkTree": Handling(
        Disposition.REFUSE, reason="a topology with no geometry this product can report on（vtkGraph と同じ）",
    ),
    "vtkSelection": Handling(
        Disposition.REFUSE, reason="a description of a subset, not data; it is an argument to an operation and never a @Case",
    ),
    "vtkAnnotation": Handling(
        Disposition.REFUSE, reason="a selection with a label; annotations here are CT-004 state, not read data",
    ),
    "vtkAnnotationLayers": Handling(
        Disposition.REFUSE, reason="a selection with a label; annotations here are CT-004 state, not read data（vtkAnnotation と同じ）",
    ),
    "vtkArrayData": Handling(
        Disposition.REFUSE, reason="n-dimensional arrays with no association to points or cells, so INV-003 has nothing to hold",
    ),
    "vtkBSPCuts": Handling(
        Disposition.REFUSE, reason="a spatial partitioning tree used by parallel filters, not a result",
    ),
    "vtkPiecewiseFunction": Handling(
        Disposition.REFUSE, reason="a transfer function - appearance, and already CT-004 state",
    ),
    "vtkDataObject": Handling(
        Disposition.REFUSE, reason="the base class. A reader returning one has told us nothing about what it read, which is a reason to stop rather than to guess",
    ),
    "vtkGenericDataSet": Handling(
        Disposition.REFUSE, reason="an adaptor interface with no storage of its own",
    ),
    "vtkImageStencilData": Handling(
        Disposition.REFUSE, reason="a mask for image operations",
    ),
    "vtkAbstractElectronicData": Handling(
        Disposition.REFUSE, reason="atoms and bonds are a different domain with their own units and their own conventions; reading one as a mesh of vertices would show it and mean nothing（vtkMolecule と同じ）",
    ),
    "vtkOpenQubeElectronicData": Handling(
        Disposition.REFUSE, reason="atoms and bonds are a different domain with their own units and their own conventions; reading one as a mesh of vertices would show it and mean nothing（vtkMolecule と同じ）",
    ),
    "vtkGeoJSONFeature": Handling(
        Disposition.REFUSE, reason="geographic features carry their own coordinate reference systems, which this product does not model",
    ),
    "vtkAMRDataObject": Handling(
        Disposition.REFUSE, reason="the levels overlap by construction: a refined region is present at every level above it, so a sum over the leaves counts it once per level. Until the level masking is read and applied, every aggregate over one is wrong by an amount that looks plausible - INV-010 one level up（vtkOverlappingAMR と同じ）",
    ),
    "vtkCartesianGrid": Handling(
        Disposition.REFUSE, reason="present in the toolkit's type table and produced by no reader in this build",
    ),
    "vtkStatisticalModel": Handling(
        Disposition.REFUSE, reason="a fitted model, not measured data",
    ),
    "vtkCompositeDataSet": Handling(
        Disposition.REFUSE, reason="the composite base class; as vtkDataObject",
    ),
    "vtkDataObjectTree": Handling(
        Disposition.REFUSE, reason="the composite tree base class; as vtkDataObject",
    ),
    "vtkDataSet": Handling(
        Disposition.REFUSE, reason="the dataset base class; as vtkDataObject",
    ),
    "vtkUnstructuredGridBase": Handling(
        Disposition.REFUSE, reason="an abstract base with no storage",
    ),
    "vtkMultiGroupDataSet": Handling(
        Disposition.REFUSE, reason="obsolete in the toolkit",
    ),
    "vtkHierarchicalDataSet": Handling(
        Disposition.REFUSE, reason="obsolete in the toolkit",
    ),
    "vtkHyperOctree": Handling(
        Disposition.REFUSE, reason="obsolete in the toolkit",
    ),
    "vtkTemporalDataSet": Handling(
        Disposition.REFUSE, reason="obsolete in the toolkit; time is a @Case axis here, not a data object",
    ),
    "vtkPistonDataObject": Handling(
        Disposition.REFUSE, reason="obsolete in the toolkit",
    ),
}


def handling(class_name: str) -> Handling:
    """CT-012's row for a class, or a refusal that says the table has a hole rather than guessing."""
    found = HANDLING.get(class_name)
    if found is None:
        raise KeyError(
            f"{class_name} is not in CT-012's table. The table is meant to be total, so this is a "
            "defect in the contract and not a permission: add a disposition for it"
        )
    return found
