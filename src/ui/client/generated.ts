/* GENERATED from specs/contracts/schema/CT-003.json by validate/check_client_types.py.
 * Do not edit by hand: the gate regenerates this file and compares, so an edit here fails
 * the build rather than changing anything (XC-252).
 *
 * What is generated is the shape of what crosses the wire - the operations, what each takes
 * and what each answers. What is NOT generated is behaviour: units, precision and the
 * invariants stay in Python and are reached by asking the service, never reimplemented here.
 */

export const PROTOCOL_VERSION = "2.5.0";

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
];

/** What each operation takes. From CT-003's $defs.operationParameters. */
export interface Parameters {
  "workspace.open": {
    path: string;
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
  };
  "view.pick": {
    viewId: string;
    width: number;
    height: number;
    x: number;
    y: number;
  };
}

/** What each operation answers. From CT-003's $defs.operationResults. */
export interface Results {
  "workspace.open": {
    workspaceId: string;
    formatVersion: string;
    unresolvedCases: readonly (string)[];
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
      atUtc: string;
      outcome: string;
      undoId?: string;
    })[];
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
  };
  "dataset.parts": {
    parts: readonly ({
      name: string;
      type: string;
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
    startedUtc?: string;
    finishedUtc?: string;
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
      modifiedUtc: string;
    })[];
    declaredUnits: Record<string, unknown>;
    productVersion: string;
  };
  "system.audit": {
    entries: readonly ({
      atUtc: string;
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
