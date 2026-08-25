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

#: What each operation accepts, and which of those it requires. From CT-003's per-operation
#: schemas, so a handler is checked against the **contract** rather than against its own
#: declaration - which is what CT-002 promises when it says an unknown parameter is rejected.
PARAMETERS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "workspace.open": (frozenset(['path']), frozenset(['path'])),
    "workspace.save": (frozenset(['path', 'workspaceId']), frozenset(['workspaceId'])),
    "workspace.close": (frozenset(['workspaceId']), frozenset(['workspaceId'])),
    "case.create": (frozenset(['name', 'parentCaseId', 'workspaceId']), frozenset(['name', 'workspaceId'])),
    "case.delete": (frozenset(['caseId']), frozenset(['caseId'])),
    "case.move": (frozenset(['caseId', 'newParentId']), frozenset(['caseId', 'newParentId'])),
    "case.tag": (frozenset(['caseId', 'tags']), frozenset(['caseId', 'tags'])),
    "dataset.load": (frozenset(['caseId', 'filePaths']), frozenset(['caseId', 'filePaths'])),
    "dataset.describe": (frozenset(['datasetId']), frozenset(['datasetId'])),
    "field.declareUnit": (frozenset(['datasetId', 'fieldName', 'unitSymbol']), frozenset(['datasetId', 'fieldName', 'unitSymbol'])),
    "field.statistics": (frozenset(['datasetId', 'fieldName', 'region']), frozenset(['datasetId', 'fieldName'])),
    "variable.declare": (frozenset(['caseId', 'name', 'unit', 'value', 'workspaceId']), frozenset(['name', 'value'])),
    "variable.set": (frozenset(['value', 'variableId']), frozenset(['value', 'variableId'])),
    "variable.detach": (frozenset(['caseId', 'variableId']), frozenset(['caseId', 'variableId'])),
    "view.create": (frozenset(['definition', 'sourceTemplateId', 'sourceTemplateRevision', 'workspaceId']), frozenset(['definition', 'workspaceId'])),
    "view.update": (frozenset(['definition', 'viewId']), frozenset(['definition', 'viewId'])),
    "view.duplicate": (frozenset(['newName', 'viewId']), frozenset(['newName', 'viewId'])),
    "view.rename": (frozenset(['newName', 'viewId']), frozenset(['newName', 'viewId'])),
    "view.delete": (frozenset(['viewId']), frozenset(['viewId'])),
    "view.render": (frozenset(['format', 'height', 'viewId', 'width']), frozenset(['format', 'height', 'viewId', 'width'])),
    "graph.create": (frozenset(['definition', 'sourceTemplateId', 'sourceTemplateRevision', 'workspaceId']), frozenset(['definition', 'workspaceId'])),
    "graph.update": (frozenset(['definition', 'graphId']), frozenset(['definition', 'graphId'])),
    "graph.duplicate": (frozenset(['graphId', 'newName']), frozenset(['graphId', 'newName'])),
    "graph.rename": (frozenset(['graphId', 'newName']), frozenset(['graphId', 'newName'])),
    "graph.delete": (frozenset(['graphId']), frozenset(['graphId'])),
    "graph.data": (frozenset(['graphId']), frozenset(['graphId'])),
    "diff.create": (frozenset(['basisCaseId', 'caseIdA', 'caseIdB']), frozenset(['basisCaseId', 'caseIdA', 'caseIdB'])),
    "report.create": (frozenset(['definition', 'sourceTemplateId', 'sourceTemplateRevision', 'workspaceId']), frozenset(['definition', 'workspaceId'])),
    "report.update": (frozenset(['definition', 'reportId']), frozenset(['definition', 'reportId'])),
    "report.duplicate": (frozenset(['newName', 'reportId']), frozenset(['newName', 'reportId'])),
    "report.rename": (frozenset(['newName', 'reportId']), frozenset(['newName', 'reportId'])),
    "report.delete": (frozenset(['reportId']), frozenset(['reportId'])),
    "report.export": (frozenset(['path', 'reportId']), frozenset(['path', 'reportId'])),
    "system.capabilities": (frozenset([]), frozenset([])),
    "system.protocols": (frozenset([]), frozenset([])),
    "history.undo": (frozenset(['undoId']), frozenset(['undoId'])),
    "history.list": (frozenset(['workspaceId']), frozenset(['workspaceId'])),
    "dataset.probe": (frozenset(['datasetId', 'pointM', 'resultPosition']), frozenset(['datasetId', 'pointM', 'resultPosition'])),
    "dataset.parts": (frozenset(['datasetId']), frozenset(['datasetId'])),
    "field.derive": (frozenset(['datasetId', 'fieldName', 'frameId', 'quantity']), frozenset(['datasetId', 'fieldName', 'quantity'])),
    "field.setDisplayUnit": (frozenset(['quantity', 'unitSymbol', 'workspaceId']), frozenset(['quantity', 'unitSymbol', 'workspaceId'])),
    "frame.declare": (frozenset(['axis', 'kind', 'name', 'origin', 'workspaceId']), frozenset(['axis', 'kind', 'name', 'origin', 'workspaceId'])),
    "measurement.import": (frozenset(['caseId', 'source', 'values']), frozenset(['caseId', 'source', 'values'])),
    "case.proposeTags": (frozenset(['caseIds']), frozenset(['caseIds'])),
    "template.createFromItem": (frozenset(['name', 'targetScope', 'workspaceItemId', 'workspaceItemRevision']), frozenset(['name', 'targetScope', 'workspaceItemId', 'workspaceItemRevision'])),
    "template.apply": (frozenset(['targetSelection', 'templateId', 'templateRevision', 'workspaceId']), frozenset(['targetSelection', 'templateId', 'templateRevision', 'workspaceId'])),
    "template.promote": (frozenset(['targetScope', 'templateId']), frozenset(['targetScope', 'templateId'])),
    "template.export": (frozenset(['path', 'templateId']), frozenset(['path', 'templateId'])),
    "template.import": (frozenset(['path', 'targetScope']), frozenset(['path', 'targetScope'])),
    "library.list": (frozenset(['kind', 'scope']), frozenset([])),
    "pipeline.create": (frozenset(['definition', 'workspaceId']), frozenset(['definition', 'workspaceId'])),
    "pipeline.update": (frozenset(['definition', 'pipelineId']), frozenset(['definition', 'pipelineId'])),
    "pipeline.dryRun": (frozenset(['pipelineId', 'startingCases']), frozenset(['pipelineId'])),
    "pipeline.run": (frozenset(['destructiveAuthorisation', 'pipelineId', 'startingCases']), frozenset(['pipelineId'])),
    "pipeline.cancel": (frozenset(['runId']), frozenset(['runId'])),
    "script.run": (frozenset(['authorisation', 'path', 'scriptText']), frozenset(['authorisation'])),
    "report.provenance": (frozenset(['exportedPath', 'reportId']), frozenset([])),
    "system.audit": (frozenset(['since']), frozenset([])),
    "system.supportBundle": (frozenset(['consent', 'path']), frozenset(['consent', 'path'])),
    "workspace.pack": (frozenset(['includeData', 'path', 'workspaceId']), frozenset(['includeData', 'path', 'workspaceId'])),
    "output.prune": (frozenset(['runsToRemove', 'workspaceId']), frozenset(['runsToRemove', 'workspaceId'])),
}


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
