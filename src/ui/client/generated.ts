/* GENERATED from specs/contracts/schema/CT-003.json by validate/check_client_types.py.
 * Do not edit by hand: the gate regenerates this file and compares, so an edit here fails
 * the build rather than changing anything (XC-252).
 *
 * What is generated is the shape of what crosses the wire - the operations, what each takes
 * and what each answers. What is NOT generated is behaviour: units, precision and the
 * invariants stay in Python and are reached by asking the service, never reimplemented here.
 */

export const PROTOCOL_VERSION = "3.10.0";

/* The wire's own names, from CT-003's $defs.transport (XC-258). The engine generates the
 * same values from the same place; neither side is derived from the other (XC-252). */
export const TOKEN_HEADER: string = "X-Solvia-Token";
export const COMMAND_PATH: string = "/command";
export const HANDLE_PATH: string = "/handle/";
export const HEALTH_PATH: string = "/health";
export const CONNECTION_FILE: string = "connection.json";

export type Operation =
  | "workspace.open"
  | "workspace.save"
  | "workspace.close"
  | "case.create"
  | "case.delete"
  | "case.move"
  | "case.tag"
  | "dataset.load"
  | "dataset.describe"
  | "field.declareUnit"
  | "field.statistics"
  | "variable.declare"
  | "variable.set"
  | "variable.detach"
  | "view.create"
  | "view.update"
  | "view.duplicate"
  | "view.rename"
  | "view.delete"
  | "view.render"
  | "graph.create"
  | "graph.update"
  | "graph.duplicate"
  | "graph.rename"
  | "graph.delete"
  | "graph.data"
  | "diff.create"
  | "report.create"
  | "report.update"
  | "report.duplicate"
  | "report.rename"
  | "report.delete"
  | "report.export"
  | "system.capabilities"
  | "system.protocols"
  | "history.undo"
  | "history.list"
  | "dataset.probe"
  | "dataset.parts"
  | "field.derive"
  | "field.setDisplayUnit"
  | "frame.declare"
  | "measurement.import"
  | "case.proposeTags"
  | "template.createFromItem"
  | "template.apply"
  | "template.promote"
  | "template.export"
  | "template.import"
  | "library.list"
  | "pipeline.create"
  | "pipeline.update"
  | "pipeline.dryRun"
  | "pipeline.run"
  | "pipeline.cancel"
  | "script.run"
  | "report.provenance"
  | "system.audit"
  | "system.supportBundle"
  | "workspace.pack"
  | "output.prune"
  | "view.pick"
  | "dataset.inspect"
  | "output.list"
  | "output.plan"
  | "view.get"
  | "report.get"
  | "system.operations"
  ;

export const OPERATIONS: readonly Operation[] = [
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
  "view.pick",
  "dataset.inspect",
  "output.list",
  "output.plan",
  "view.get",
  "report.get",
  "system.operations",
];

/** What each operation is, for a list a person reads (XC-277): whether it writes - from the
 *  catalogue table's class column - and its parameters and answer fields by name, from the
 *  schema. Behaviour is not here: what an operation does is the engine's to say. */
export interface OperationFacts {
  readonly writes: boolean;
  readonly required: readonly string[];
  readonly optional: readonly string[];
  readonly answers: readonly string[];
}

export const OPERATION_FACTS: Readonly<Record<Operation, OperationFacts>> = {
  "workspace.open": { writes: true, required: ["path"], optional: ["takeOverStaleLock"], answers: ["workspaceId", "formatVersion", "unresolvedCases", "items", "readOnly", "lock"] },
  "workspace.save": { writes: true, required: ["workspaceId"], optional: ["path"], answers: ["path", "previousKept"] },
  "workspace.close": { writes: true, required: ["workspaceId"], optional: [], answers: [] },
  "case.create": { writes: true, required: ["name", "workspaceId"], optional: ["parentCaseId"], answers: ["id"] },
  "case.delete": { writes: true, required: ["caseId"], optional: [], answers: ["affectedDescendantIds"] },
  "case.move": { writes: true, required: ["caseId", "newParentId"], optional: [], answers: [] },
  "case.tag": { writes: true, required: ["caseId", "tags"], optional: [], answers: [] },
  "dataset.load": { writes: true, required: ["caseId", "filePaths"], optional: [], answers: ["datasetId", "fields", "supportLevel", "gaps"] },
  "dataset.describe": { writes: false, required: ["datasetId"], optional: [], answers: ["pointCount", "cellCount", "boundsM", "partial", "resultAxis"] },
  "field.declareUnit": { writes: true, required: ["datasetId", "fieldName", "unitSymbol"], optional: [], answers: [] },
  "field.statistics": { writes: false, required: ["datasetId", "fieldName"], optional: ["region", "resultPosition"], answers: ["minimum", "maximum", "mean", "missingCount", "association", "reduction", "weighting", "scope", "averaging", "averaged", "averagingRefused", "resultPosition"] },
  "variable.declare": { writes: true, required: ["name", "value"], optional: ["workspaceId", "caseId", "unit"], answers: ["id"] },
  "variable.set": { writes: true, required: ["value", "variableId"], optional: [], answers: ["changedIds"] },
  "variable.detach": { writes: true, required: ["caseId", "variableId"], optional: [], answers: ["keptValue"] },
  "view.create": { writes: true, required: ["definition", "workspaceId"], optional: ["sourceTemplateId", "sourceTemplateRevision"], answers: ["id", "revision"] },
  "view.update": { writes: true, required: ["definition", "viewId"], optional: [], answers: ["id", "revision"] },
  "view.duplicate": { writes: true, required: ["newName", "viewId"], optional: [], answers: ["id"] },
  "view.rename": { writes: true, required: ["newName", "viewId"], optional: [], answers: ["id", "revision"] },
  "view.delete": { writes: true, required: ["viewId"], optional: [], answers: ["deletedId", "unresolvedUnitIds"] },
  "view.render": { writes: false, required: ["format", "height", "viewId", "width"], optional: ["legend", "camera"], answers: ["handle", "reduced", "resultPosition"] },
  "graph.create": { writes: true, required: ["definition", "workspaceId"], optional: ["sourceTemplateId", "sourceTemplateRevision"], answers: ["id", "revision"] },
  "graph.update": { writes: true, required: ["definition", "graphId"], optional: [], answers: ["id", "revision"] },
  "graph.duplicate": { writes: true, required: ["graphId", "newName"], optional: [], answers: ["id"] },
  "graph.rename": { writes: true, required: ["graphId", "newName"], optional: [], answers: ["id", "revision"] },
  "graph.delete": { writes: true, required: ["graphId"], optional: [], answers: ["deletedId", "unresolvedUnitIds"] },
  "graph.data": { writes: false, required: ["graphId"], optional: [], answers: ["series", "resultAxisNote"] },
  "diff.create": { writes: true, required: ["basisCaseId", "caseIdA", "caseIdB"], optional: [], answers: ["diffId", "outsideCount", "outsideFraction", "roundTripError", "disclosure"] },
  "report.create": { writes: true, required: ["definition", "workspaceId"], optional: ["sourceTemplateId", "sourceTemplateRevision"], answers: ["id", "revision"] },
  "report.update": { writes: true, required: ["definition", "reportId"], optional: [], answers: ["id", "revision"] },
  "report.duplicate": { writes: true, required: ["newName", "reportId"], optional: [], answers: ["id"] },
  "report.rename": { writes: true, required: ["newName", "reportId"], optional: [], answers: ["id", "revision"] },
  "report.delete": { writes: true, required: ["reportId"], optional: [], answers: ["deletedId", "unresolvedUnitIds"] },
  "report.export": { writes: true, required: ["path", "reportId"], optional: [], answers: ["path", "bytes", "reductions", "omitted"] },
  "system.capabilities": { writes: false, required: [], optional: [], answers: ["machineClass", "renderers", "formats", "diagnostics", "egress"] },
  "system.protocols": { writes: false, required: [], optional: [], answers: ["versions"] },
  "history.undo": { writes: true, required: ["undoId"], optional: [], answers: ["restoredIds"] },
  "history.list": { writes: false, required: ["workspaceId"], optional: [], answers: ["entries", "undoLimit", "undoDropped", "historyLimit", "omitted"] },
  "dataset.probe": { writes: false, required: ["datasetId", "fieldName", "pointM", "resultPosition"], optional: [], answers: ["value", "association", "resultPosition"] },
  "dataset.parts": { writes: false, required: ["datasetId"], optional: [], answers: ["parts"] },
  "field.derive": { writes: false, required: ["datasetId", "fieldName", "quantity"], optional: ["frameId", "component", "asTensor"], answers: ["fieldName", "formula", "conventions", "frameId", "fieldNames", "association", "unit"] },
  "field.setDisplayUnit": { writes: true, required: ["quantity", "unitSymbol", "workspaceId"], optional: [], answers: [] },
  "frame.declare": { writes: true, required: ["axis", "kind", "name", "origin", "workspaceId"], optional: [], answers: ["id"] },
  "measurement.import": { writes: true, required: ["caseId", "source", "values"], optional: [], answers: ["importedIds", "undeclared"] },
  "case.proposeTags": { writes: false, required: ["caseIds"], optional: [], answers: ["proposals"] },
  "template.createFromItem": { writes: true, required: ["name", "targetScope", "workspaceItemId", "workspaceItemRevision"], optional: [], answers: ["id", "revision"] },
  "template.apply": { writes: true, required: ["targetSelection", "templateId", "templateRevision", "workspaceId"], optional: [], answers: ["resolved", "unresolved", "itemId"] },
  "template.promote": { writes: true, required: ["targetScope", "templateId"], optional: [], answers: ["templateId", "requirements"] },
  "template.export": { writes: true, required: ["path", "templateId"], optional: [], answers: ["path", "assetsEmbedded", "assetsListed"] },
  "template.import": { writes: true, required: ["path", "targetScope"], optional: [], answers: ["templateId", "origin", "unresolvedReferences"] },
  "library.list": { writes: false, required: [], optional: ["scope", "kind"], answers: ["entries"] },
  "pipeline.create": { writes: true, required: ["definition", "workspaceId"], optional: [], answers: ["id", "revision"] },
  "pipeline.update": { writes: true, required: ["definition", "pipelineId"], optional: [], answers: ["id", "revision"] },
  "pipeline.dryRun": { writes: false, required: ["pipelineId"], optional: ["startingCases"], answers: ["steps"] },
  "pipeline.run": { writes: true, required: ["pipelineId"], optional: ["startingCases", "destructiveAuthorisation"], answers: ["runId", "resolvedCases", "results", "written", "failedCases", "stoppedAt", "started", "finished"] },
  "pipeline.cancel": { writes: true, required: ["runId"], optional: [], answers: ["stoppedAt", "written"] },
  "script.run": { writes: true, required: ["authorisation"], optional: ["scriptText", "path"], answers: ["undoId", "commandCount"] },
  "report.provenance": { writes: false, required: [], optional: ["exportedPath", "reportId"], answers: ["workspaceId", "caseIds", "sources", "declaredUnits", "productVersion", "produced"] },
  "system.audit": { writes: false, required: [], optional: ["since"], answers: ["entries"] },
  "system.supportBundle": { writes: true, required: ["consent", "path"], optional: [], answers: ["path", "contents"] },
  "workspace.pack": { writes: true, required: ["includeData", "path", "workspaceId"], optional: [], answers: ["path", "bytes", "omitted"] },
  "output.prune": { writes: true, required: ["runsToRemove", "workspaceId"], optional: ["expectedFiles"], answers: ["removedRunIds", "freedBytes", "deletedFiles"] },
  "view.pick": { writes: false, required: ["viewId", "width", "height", "x", "y"], optional: ["camera"], answers: ["value", "association", "part", "resultPosition"] },
  "dataset.inspect": { writes: false, required: ["path"], optional: [], answers: ["format", "supportLevel", "gaps", "sizeBytes", "modified", "exists"] },
  "output.list": { writes: false, required: ["workspaceId"], optional: [], answers: ["outputDirectory", "runs", "totalBytes", "limitBytes", "overLimit", "suggestedRunIds"] },
  "output.plan": { writes: false, required: ["workspaceId", "runsToRemove"], optional: [], answers: ["runIds", "files", "freedBytes", "keptRecords"] },
  "view.get": { writes: false, required: ["viewId"], optional: [], answers: ["id", "revision", "definition"] },
  "report.get": { writes: false, required: ["reportId"], optional: [], answers: ["id", "revision", "definition"] },
  "system.operations": { writes: false, required: [], optional: [], answers: ["registered", "unimplemented"] },
};

/** What each operation takes. From CT-003's $defs.operationParameters. */
export interface Parameters {
  "workspace.open": {
    path: string;
    takeOverStaleLock?: boolean;
  };
  "workspace.save": {
    workspaceId: string;
    path?: string;
  };
  "workspace.close": {
    workspaceId: string;
  };
  "case.create": {
    workspaceId: string;
    name: string;
    parentCaseId?: string;
  };
  "case.delete": {
    caseId: string;
  };
  "case.move": {
    caseId: string;
    newParentId: string;
  };
  "case.tag": {
    caseId: string;
    tags: readonly (string)[];
  };
  "dataset.load": {
    caseId: string;
    filePaths: readonly (string)[];
  };
  "dataset.describe": {
    datasetId: string;
  };
  "field.declareUnit": {
    datasetId: string;
    fieldName: string;
    unitSymbol: string;
  };
  "field.statistics": {
    datasetId: string;
    fieldName: string;
    region?: string;
    resultPosition?: number;
  };
  "variable.declare": {
    name: string;
    value: unknown;
    workspaceId?: string;
    caseId?: string;
    unit?: string;
  };
  "variable.set": {
    variableId: string;
    value: unknown;
  };
  "variable.detach": {
    caseId: string;
    variableId: string;
  };
  "view.create": {
    workspaceId: string;
    definition: Record<string, unknown>;
    sourceTemplateId?: string;
    sourceTemplateRevision?: number;
  };
  "view.update": {
    viewId: string;
    definition: Record<string, unknown>;
  };
  "view.duplicate": {
    viewId: string;
    newName: string;
  };
  "view.rename": {
    viewId: string;
    newName: string;
  };
  "view.delete": {
    viewId: string;
  };
  "view.render": {
    viewId: string;
    width: number;
    height: number;
    format: "png" | "jpeg" | "webp";
    legend?: boolean;
    camera?: CameraDefinition;
  };
  "graph.create": {
    workspaceId: string;
    definition: Record<string, unknown>;
    sourceTemplateId?: string;
    sourceTemplateRevision?: number;
  };
  "graph.update": {
    graphId: string;
    definition: Record<string, unknown>;
  };
  "graph.duplicate": {
    graphId: string;
    newName: string;
  };
  "graph.rename": {
    graphId: string;
    newName: string;
  };
  "graph.delete": {
    graphId: string;
  };
  "graph.data": {
    graphId: string;
  };
  "diff.create": {
    caseIdA: string;
    caseIdB: string;
    basisCaseId: string;
  };
  "report.create": {
    workspaceId: string;
    definition: Record<string, unknown>;
    sourceTemplateId?: string;
    sourceTemplateRevision?: number;
  };
  "report.update": {
    reportId: string;
    definition: Record<string, unknown>;
  };
  "report.duplicate": {
    reportId: string;
    newName: string;
  };
  "report.rename": {
    reportId: string;
    newName: string;
  };
  "report.delete": {
    reportId: string;
  };
  "report.export": {
    reportId: string;
    path: string;
  };
  "system.capabilities": Record<string, unknown>;
  "system.protocols": Record<string, unknown>;
  "history.undo": {
    undoId: string;
  };
  "history.list": {
    workspaceId: string;
  };
  "dataset.probe": {
    datasetId: string;
    fieldName: string;
    pointM: readonly (number)[];
    resultPosition: number;
  };
  "dataset.parts": {
    datasetId: string;
  };
  "field.derive": {
    datasetId: string;
    fieldName: string;
    quantity: string;
    frameId?: string;
    component?: string;
    asTensor?: boolean;
  };
  "field.setDisplayUnit": {
    workspaceId: string;
    quantity: string;
    unitSymbol: string;
  };
  "frame.declare": {
    workspaceId: string;
    name: string;
    kind: "cartesian" | "cylindrical" | "spherical";
    origin: readonly (number)[];
    axis: readonly (number)[];
  };
  "measurement.import": {
    caseId: string;
    values: readonly (Record<string, unknown>)[];
    source: string;
  };
  "case.proposeTags": {
    caseIds: readonly (string)[];
  };
  "template.createFromItem": {
    workspaceItemId: string;
    workspaceItemRevision: number;
    targetScope: "workspace" | "shared";
    name: string;
  };
  "template.apply": {
    templateId: string;
    templateRevision: number;
    workspaceId: string;
    targetSelection: Record<string, unknown>;
  };
  "template.promote": {
    templateId: string;
    targetScope: "workspace" | "shared";
  };
  "template.export": {
    templateId: string;
    path: string;
  };
  "template.import": {
    path: string;
    targetScope: "workspace" | "shared";
  };
  "library.list": {
    scope?: "sample" | "workspace" | "shared";
    kind?: "view" | "graph" | "report" | "material" | "asset";
  };
  "pipeline.create": {
    workspaceId: string;
    definition: Record<string, unknown>;
  };
  "pipeline.update": {
    pipelineId: string;
    definition: Record<string, unknown>;
  };
  "pipeline.dryRun": {
    pipelineId: string;
    startingCases?: readonly (string)[];
  };
  "pipeline.run": {
    pipelineId: string;
    startingCases?: readonly (string)[];
    destructiveAuthorisation?: readonly ({
      unitId: string;
      caseCount: number;
    })[];
  };
  "pipeline.cancel": {
    runId: string;
  };
  "script.run": {
    authorisation: {
      byPerson?: boolean;
      unattended?: boolean;
    };
    scriptText?: string;
    path?: string;
  };
  "report.provenance": {
    exportedPath?: string;
    reportId?: string;
  };
  "system.audit": {
    since?: string;
  };
  "system.supportBundle": {
    path: string;
    consent: boolean;
  };
  "workspace.pack": {
    workspaceId: string;
    path: string;
    includeData: boolean;
  };
  "output.prune": {
    workspaceId: string;
    runsToRemove: readonly (string)[];
    expectedFiles?: readonly (string)[];
  };
  "view.pick": {
    viewId: string;
    width: number;
    height: number;
    x: number;
    y: number;
    camera?: CameraDefinition;
  };
  "dataset.inspect": {
    path: string;
  };
  "output.list": {
    workspaceId: string;
  };
  "output.plan": {
    workspaceId: string;
    runsToRemove: readonly (string)[];
  };
  "view.get": {
    viewId: string;
  };
  "report.get": {
    reportId: string;
  };
  "system.operations": Record<string, unknown>;
}

/** What each operation answers. From CT-003's $defs.operationResults. */
export interface Results {
  "workspace.open": {
    workspaceId: string;
    formatVersion: string;
    unresolvedCases: readonly (string)[];
    items?: {
      views?: readonly ({
        id: string;
        name: string;
        datasetId?: string;
      })[];
      graphs?: readonly ({
        id: string;
        name: string;
        datasetId?: string;
      })[];
      reports?: readonly ({
        id: string;
        name: string;
        datasetId?: string;
      })[];
    };
    readOnly: boolean;
    lock: {
      state: "free" | "held" | "stale" | "unreadable";
      lockFile: string;
      holder?: {
        processId: number;
        host: string;
        user: string;
        takenAt: RecordedTime;
      };
      detail?: string;
    };
  };
  "workspace.save": {
    path: string;
    previousKept?: boolean;
  };
  "workspace.close": Record<string, unknown>;
  "case.create": {
    id: string;
  };
  "case.delete": {
    affectedDescendantIds: readonly (string)[];
  };
  "case.move": Record<string, unknown>;
  "case.tag": Record<string, unknown>;
  "dataset.load": {
    datasetId: string;
    fields: readonly ({
      name: string;
      association: "point" | "cell" | "integrationPoint" | "field";
      unit?: string | null;
      components?: number;
    })[];
    supportLevel: "verified" | "offered";
    gaps: readonly (string)[];
  };
  "dataset.describe": {
    pointCount: number;
    cellCount: number;
    boundsM: {
      minM: readonly (number)[];
      maxM: readonly (number)[];
    };
    partial: boolean;
    resultAxis?: {
      kind: "time" | "mode" | "frequency" | "undeclared" | "none";
      positions?: readonly (number)[];
      count?: number;
      unit?: string | null;
    };
  };
  "field.declareUnit": Record<string, unknown>;
  "field.statistics": {
    minimum: {
      value: number | null;
      unit: string | null;
      digits: number;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      formula?: string;
      caveats?: readonly (string)[];
      missingBecause?: string;
      location?: string;
    };
    maximum: {
      value: number | null;
      unit: string | null;
      digits: number;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      formula?: string;
      caveats?: readonly (string)[];
      missingBecause?: string;
      location?: string;
    };
    mean: {
      value: number | null;
      unit: string | null;
      digits: number;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      formula?: string;
      caveats?: readonly (string)[];
      missingBecause?: string;
      location?: string;
    };
    missingCount: number;
    association: "point" | "cell";
    reduction: string;
    weighting: "volume" | "dualVolume" | "area" | "none";
    scope: string;
    averaging?: "unaveraged";
    averaged?: {
      maximum: ReportedValue;
      minimum: ReportedValue;
      spreadAtMaximum: ReportedValue;
      spreadFraction: ReportedValue;
      disagreement: string;
    };
    averagingRefused?: string;
    resultPosition: {
      step: number;
      count: number;
      kind: "time" | "mode" | "frequency" | "undeclared" | "none";
      value: number | null;
      unit: string | null;
      stated: string;
    };
  };
  "variable.declare": {
    id: string;
  };
  "variable.set": {
    changedIds: readonly (string)[];
  };
  "variable.detach": {
    keptValue: {
      value: number | null;
      unit: string | null;
      digits: number;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      formula?: string;
      caveats?: readonly (string)[];
      missingBecause?: string;
      location?: string;
    };
  };
  "view.create": {
    id: string;
    revision: number;
  };
  "view.update": {
    id: string;
    revision: number;
  };
  "view.duplicate": {
    id: string;
  };
  "view.rename": {
    id: string;
    revision: number;
  };
  "view.delete": {
    deletedId: string;
    unresolvedUnitIds: readonly (string)[];
  };
  "view.render": {
    handle: string;
    reduced?: string;
    resultPosition: {
      step: number;
      count: number;
      kind: "time" | "mode" | "frequency" | "undeclared" | "none";
      value: number | null;
      unit: string | null;
      stated: string;
    };
  };
  "graph.create": {
    id: string;
    revision: number;
  };
  "graph.update": {
    id: string;
    revision: number;
  };
  "graph.duplicate": {
    id: string;
  };
  "graph.rename": {
    id: string;
    revision: number;
  };
  "graph.delete": {
    deletedId: string;
    unresolvedUnitIds: readonly (string)[];
  };
  "graph.data": {
    series: readonly ({
      label: string;
      points: readonly ({
        caseId: string;
        value?: number | null;
        reason?: string;
      })[];
      unit: string | null;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      expression?: string;
    })[];
    resultAxisNote?: string;
  };
  "diff.create": {
    diffId: string;
    outsideCount: number;
    outsideFraction: number;
    roundTripError: {
      value: number | null;
      unit: string | null;
      digits: number;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      formula?: string;
      caveats?: readonly (string)[];
      missingBecause?: string;
      location?: string;
    };
    disclosure: string;
  };
  "report.create": {
    id: string;
    revision: number;
  };
  "report.update": {
    id: string;
    revision: number;
  };
  "report.duplicate": {
    id: string;
  };
  "report.rename": {
    id: string;
    revision: number;
  };
  "report.delete": {
    deletedId: string;
    unresolvedUnitIds: readonly (string)[];
  };
  "report.export": {
    path: string;
    bytes: number;
    reductions: readonly (string)[];
    omitted: readonly (string)[];
  };
  "system.capabilities": {
    machineClass: "integrated-graphics" | "workstation";
    renderers: readonly ({
      backend: string;
      available: boolean;
      requires?: string;
    })[];
    formats: readonly ({
      format: string;
      level: "verified" | "offered" | "absent";
    })[];
    diagnostics?: {
      logDirectory: string | null;
      level: "debug" | "info" | "warning" | "error";
      maxBytes: number;
      keepFiles: number;
      retainDays: number;
      files: number;
      bytes: number;
    };
    egress?: {
      transportConfigured: boolean;
      offline: boolean;
      workspaceId: string | null;
      search: boolean;
      languageModel: boolean;
      updateCheck: boolean;
      hosts: readonly (string)[];
      withoutAsking: boolean;
      workspaceContent: boolean;
      auditEntries: number;
      sentEntries: number;
    };
  };
  "system.protocols": {
    versions: readonly (string)[];
  };
  "history.undo": {
    restoredIds: readonly (string)[];
  };
  "history.list": {
    entries: readonly ({
      operation: string;
      origin: "interface" | "assistant" | "script" | "pipeline";
      at: RecordedTime;
      outcome: string;
      undoId?: string;
      undoable?: boolean;
    })[];
    undoLimit?: number;
    undoDropped?: number;
    historyLimit?: number;
    omitted?: number;
  };
  "dataset.probe": {
    value: {
      value: number | null;
      unit: string | null;
      digits: number;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      formula?: string;
      caveats?: readonly (string)[];
      missingBecause?: string;
      location?: string;
    };
    association?: string;
    resultPosition: {
      step: number;
      count: number;
      kind: "time" | "mode" | "frequency" | "undeclared" | "none";
      value: number | null;
      unit: string | null;
      stated: string;
    };
  };
  "dataset.parts": {
    parts: readonly ({
      name: string;
      type: string;
      path: readonly (string)[];
      reason?: string;
      pointCount: number;
      cellCount: number;
      parentId?: string;
      boundsM?: {
        minM: readonly (number)[];
        maxM: readonly (number)[];
      };
    })[];
  };
  "field.derive": {
    fieldName: string;
    formula: string;
    conventions: readonly (string)[];
    frameId?: string;
    fieldNames?: readonly (string)[];
    association: "point" | "cell" | "integrationPoint" | "field";
    unit: string | null;
  };
  "field.setDisplayUnit": Record<string, unknown>;
  "frame.declare": {
    id: string;
  };
  "measurement.import": {
    importedIds: readonly (string)[];
    undeclared?: readonly (string)[];
  };
  "case.proposeTags": {
    proposals: readonly ({
      caseId: string;
      tag: string;
      signal: string;
    })[];
  };
  "template.createFromItem": {
    id: string;
    revision: number;
  };
  "template.apply": {
    resolved: readonly (string)[];
    unresolved: readonly ({
      what: string;
      missing: string;
    })[];
    itemId?: string;
  };
  "template.promote": {
    templateId: string;
    requirements: readonly ({
      kind: string;
      name: string;
      originOnly?: boolean;
    })[];
  };
  "template.export": {
    path: string;
    assetsEmbedded: readonly (string)[];
    assetsListed: readonly (string)[];
  };
  "template.import": {
    templateId: string;
    origin: string;
    unresolvedReferences?: readonly (string)[];
  };
  "library.list": {
    entries: readonly ({
      id: string;
      kind: string;
      scope: "sample" | "workspace" | "shared";
      origin: string;
      newerSampleExists?: boolean;
    })[];
  };
  "pipeline.create": {
    id: string;
    revision: number;
  };
  "pipeline.update": {
    id: string;
    revision: number;
  };
  "pipeline.dryRun": {
    steps: readonly ({
      unitId: string;
      kind: string;
      caseCount: number;
      iterations?: number | null;
      countSource?: string | null;
      conditionValue?: boolean | null;
      destructive?: boolean;
      unresolved?: string | null;
    })[];
  };
  "pipeline.run": {
    runId: string;
    resolvedCases: readonly (string)[];
    results: readonly ({
      unitId: string;
      caseId: string | null;
      outcome: "done" | "skipped-empty" | "skipped-after" | "skipped-unauthorised" | "skipped-condition" | "failed" | "cancelled";
      targetSize: number;
      detail?: string;
    })[];
    written: readonly (string)[];
    failedCases: readonly (string)[];
    stoppedAt?: string | null;
    started?: RecordedTime;
    finished?: RecordedTime;
  };
  "pipeline.cancel": {
    stoppedAt: string;
    written: readonly (string)[];
  };
  "script.run": {
    undoId: string;
    commandCount: number;
  };
  "report.provenance": {
    workspaceId: string;
    caseIds: readonly (string)[];
    sources: readonly ({
      path: string;
      modified: RecordedTime;
    })[];
    declaredUnits: Record<string, unknown>;
    productVersion: string;
    produced: RecordedTime;
  };
  "system.audit": {
    entries: readonly ({
      at: RecordedTime;
      purpose: string;
      host: string;
      outcome: "sent" | "refused" | "awaitingConfirmation";
      sent?: string;
      reason?: string;
      withheld?: readonly (string)[];
    })[];
  };
  "system.supportBundle": {
    path: string;
    contents: readonly (string)[];
  };
  "workspace.pack": {
    path: string;
    bytes: number;
    omitted?: readonly (string)[];
  };
  "output.prune": {
    removedRunIds: readonly (string)[];
    freedBytes: number;
    deletedFiles: readonly (string)[];
  };
  "view.pick": {
    value: {
      value: number | null;
      unit: string | null;
      digits: number;
      provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
      formula?: string;
      caveats?: readonly (string)[];
      missingBecause?: string;
      location?: string;
    };
    association?: string;
    part?: string;
    resultPosition: {
      step: number;
      count: number;
      kind: "time" | "mode" | "frequency" | "undeclared" | "none";
      value: number | null;
      unit: string | null;
      stated: string;
    };
  };
  "dataset.inspect": {
    format: string;
    supportLevel: string;
    gaps: readonly (string)[];
    sizeBytes: number;
    modified?: RecordedTime;
    exists: boolean;
  };
  "output.list": {
    outputDirectory: string;
    runs: readonly ({
      id: string;
      started: RecordedTime;
      startedFrom: "record" | "folder";
      artefactFiles: number;
      artefactBytes: number;
      hasRecord: boolean;
    })[];
    totalBytes: number;
    limitBytes: number;
    overLimit: boolean;
    suggestedRunIds: readonly (string)[];
  };
  "output.plan": {
    runIds: readonly (string)[];
    files: readonly (string)[];
    freedBytes: number;
    keptRecords: readonly (string)[];
  };
  "view.get": {
    id: string;
    revision: number;
    definition: Record<string, unknown>;
  };
  "report.get": {
    id: string;
    revision: number;
    definition: Record<string, unknown>;
  };
  "system.operations": {
    registered: readonly (string)[];
    unimplemented: readonly (string)[];
  };
}

/** A number this product reports: its unit, the digits it honestly carries, and where it
  * came from. Never a bare number - one without its unit is a number in whatever unit the
  * reader assumed (XC-003, XC-253). */
export type ReportedValue = {
  value: number | null;
  unit: string | null;
  digits: number;
  provenance: "declared" | "dataset" | "computed" | "measured" | "reference";
  formula?: string;
  caveats?: readonly (string)[];
  missingBecause?: string;
  location?: string;
};

/** A time this product recorded: the UTC instant, and the offset of the zone it was recorded
  * in - or null where a record written before the offset was kept has none (XC-142, XC-266).
  * Defined once, in CT-001's $defs.recordedTime, and referenced by every contract. */
export type RecordedTime = {
  utc: string;
  offsetMinutes: number | null;
};

/** Where a picture is looked at from: CT-004's camera, referenced by view.render and view.pick
  * so a camera move can be drawn without becoming a change to the view's definition (XC-270). */
export type CameraDefinition = {
  position_m?: readonly (number)[];
  focalPoint_m?: readonly (number)[];
  viewUp?: readonly (number)[];
  parallelScale_m?: number;
  projection?: "perspective" | "orthographic";
};
