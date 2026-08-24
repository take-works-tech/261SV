"""What indexes a @Case's results, read from the file and never guessed (GL-036, INV-023's neighbour).

Two separate questions, and the toolkit answers exactly one of them.

**The values** are available and universal. Every reader that has a sequence publishes it on the
pipeline as `vtkStreamingDemandDrivenPipeline::TIME_STEPS`, whatever the format - measured on CGNS,
whose `BaseIterativeData_t/TimeValues` came back as `[0.0, 0.5]` (E-138). So this module reads one key
rather than one method per reader.

**What the values are** is not available, and one reader will make it up. `vtkExodusIIReader` documents
its own default: *"whether the Exodus sequence number corresponds to time steps or mode shapes ...
HasModeShapes is false unless two time values in the Exodus file are identical, in which case it is
true"* (E-138). That is physics inferred from a coincidence - two equal values in a transient restart
would make a run modal - and it is the inference GL-036 exists to forbid. `SetModeShape(n)` is
documented as `SetTimeStep(n-1)`: the same index, relabelled by a guess.

So this product reads the values and reports the kind as **undeclared**. A CGNS file does say which -
`SimulationType_t` - and `vtkCGNSReader` exposes no accessor for it, exactly as it exposes none for the
units. Where the declaration becomes reachable, the kind is read; until then it is absent and says so,
because "0, 0.5" labelled seconds when they are mode indices is a number that is wrong about the physics
while looking entirely right.

Specification: GL-036, ingest/AC-041, AC-043, XC-240. Evidence: E-138 (T1).
"""

from __future__ import annotations

from vtkmodules.vtkCommonExecutionModel import vtkStreamingDemandDrivenPipeline as Pipeline

from domain_core.case_contents import AxisKind, ResultAxis


def declared_positions(reader: object) -> tuple[float, ...] | None:
    """The sequence values the file declared, or None where it declared none.

    Read from the pipeline key rather than from a reader method, so a format added later is covered by
    having a reader at all rather than by someone remembering to add a case here.
    """
    information = reader.GetExecutive().GetOutputInformation(0)
    if not information.Has(Pipeline.TIME_STEPS()):
        return None
    count = information.Length(Pipeline.TIME_STEPS())
    if count < 1:
        return None
    return tuple(float(information.Get(Pipeline.TIME_STEPS(), index)) for index in range(count))


#: A sequence of exactly this is the reader's placeholder, not the file's statement. Measured: a CGNS
#: file with no `BaseIterativeData_t` still publishes `TIME_STEPS = [0.0]`, while a plain `.vtu`
#: publishes the key not at all (E-138). Showing that 0.0 as a position would be putting a number in
#: front of a reader that the file never wrote, which is the one thing this product must not do.
#:
#: **What this gets wrong, stated rather than discovered.** A result that genuinely holds one step
#: declared at exactly 0 is indistinguishable from a steady one here, and is reported as steady. That
#: omits a position; the alternative fabricates one, far more often, and omitting is the safe direction.
PLACEHOLDER_SEQUENCE = (0.0,)


def axis_of(reader: object) -> ResultAxis:
    """The result axis of what this reader is about to hand over.

    The kind is `UNDECLARED` whenever there is a sequence, because no reader in this build surfaces a
    declaration of what the sequence means (E-138). It is `NONE` where there is no sequence, and where
    the only sequence is the reader's own placeholder.
    """
    positions = declared_positions(reader)
    if positions is None or positions == PLACEHOLDER_SEQUENCE:
        return ResultAxis(AxisKind.NONE)
    return ResultAxis(AxisKind.UNDECLARED, positions)
