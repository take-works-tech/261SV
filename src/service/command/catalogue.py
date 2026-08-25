"""The operation catalogue of CT-003, as code.

**Generated from `specs/contracts/CT-003_engine_api.md` by
`validate/check_commands.py --write`.** Do not edit by hand: the gate compares this file
against the contract on every run, so an edit here fails the build rather than changing
anything.

The set is closed. An operation not in it is refused rather than attempted, which is what
CT-002 promises happens to an unknown command - and the refusal is what stops a caller
believing it disabled something when it merely misspelled it.
"""

from __future__ import annotations

#: Operations that change state. Each enters the undo history and may need authorisation.
WRITES = frozenset({
    "workspace.open",
    "workspace.save",
    "workspace.close",
    "case.create",
    "case.delete",
    "case.move",
    "case.tag",
    "dataset.load",
    "field.declareUnit",
    "variable.declare",
    "variable.set",
    "variable.detach",
    "view.create",
    "view.update",
    "view.duplicate",
    "view.rename",
    "view.delete",
    "graph.create",
    "graph.update",
    "graph.duplicate",
    "graph.rename",
    "graph.delete",
    "diff.create",
    "report.create",
    "report.update",
    "report.duplicate",
    "report.rename",
    "report.delete",
    "report.export",
    "history.undo",
    "field.setDisplayUnit",
    "frame.declare",
    "measurement.import",
    "template.createFromItem",
    "template.apply",
    "template.promote",
    "template.export",
    "template.import",
    "pipeline.create",
    "pipeline.update",
    "pipeline.run",
    "pipeline.cancel",
    "script.run",
    "system.supportBundle",
    "workspace.pack",
    "output.prune",
})

#: Operations that only answer. A read never needs confirmation and never enters undo.
READS = frozenset({
    "dataset.describe",
    "field.statistics",
    "view.render",
    "graph.data",
    "system.capabilities",
    "system.protocols",
    "history.list",
    "dataset.probe",
    "dataset.parts",
    "field.derive",
    "case.proposeTags",
    "library.list",
    "pipeline.dryRun",
    "report.provenance",
    "system.audit",
})

#: Every operation this build knows the name of, in the order the contract lists them.
OPERATIONS = (
    "workspace.open",
    "workspace.save",
    "workspace.close",
    "case.create",
    "case.delete",
    "case.move",
    "case.tag",
    "dataset.load",
    "dataset.describe",
    "field.declareUnit",
    "field.statistics",
    "variable.declare",
    "variable.set",
    "variable.detach",
    "view.create",
    "view.update",
    "view.duplicate",
    "view.rename",
    "view.delete",
    "view.render",
    "graph.create",
    "graph.update",
    "graph.duplicate",
    "graph.rename",
    "graph.delete",
    "graph.data",
    "diff.create",
    "report.create",
    "report.update",
    "report.duplicate",
    "report.rename",
    "report.delete",
    "report.export",
    "system.capabilities",
    "system.protocols",
    "history.undo",
    "history.list",
    "dataset.probe",
    "dataset.parts",
    "field.derive",
    "field.setDisplayUnit",
    "frame.declare",
    "measurement.import",
    "case.proposeTags",
    "template.createFromItem",
    "template.apply",
    "template.promote",
    "template.export",
    "template.import",
    "library.list",
    "pipeline.create",
    "pipeline.update",
    "pipeline.dryRun",
    "pipeline.run",
    "pipeline.cancel",
    "script.run",
    "report.provenance",
    "system.audit",
    "system.supportBundle",
    "workspace.pack",
    "output.prune",
)


def writes(operation: str) -> bool:
    """Whether an operation changes state. Unknown operations raise rather than defaulting.

    Defaulting either way is wrong in a way that is hard to see: defaulting to read lets a
    write escape the undo history, and defaulting to write puts a question in front of an
    answer somebody just asked for.
    """
    if operation in WRITES:
        return True
    if operation in READS:
        return False
    raise KeyError(operation)
