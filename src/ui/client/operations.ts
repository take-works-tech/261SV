/* GENERATED from specs/contracts/schema/CT-003.json - do not edit by hand (XC-252).
 * Regenerate with: python tools not needed - see the PR that produced this file; the shape is
 * one union of the operation names. MOD-017 owns typed calls and the transport, nothing else. */

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
  | "output.prune";

export const OPERATIONS: readonly Operation[] = ["workspace.open", "workspace.save", "workspace.close", "case.create", "case.delete", "case.move", "case.tag", "dataset.load", "dataset.describe", "field.declareUnit", "field.statistics", "variable.declare", "variable.set", "variable.detach", "view.create", "view.update", "view.duplicate", "view.rename", "view.delete", "view.render", "graph.create", "graph.update", "graph.duplicate", "graph.rename", "graph.delete", "graph.data", "diff.create", "report.create", "report.update", "report.duplicate", "report.rename", "report.delete", "report.export", "system.capabilities", "system.protocols", "history.undo", "history.list", "dataset.probe", "dataset.parts", "field.derive", "field.setDisplayUnit", "frame.declare", "measurement.import", "case.proposeTags", "template.createFromItem", "template.apply", "template.promote", "template.export", "template.import", "library.list", "pipeline.create", "pipeline.update", "pipeline.dryRun", "pipeline.run", "pipeline.cancel", "script.run", "report.provenance", "system.audit", "system.supportBundle", "workspace.pack", "output.prune"] as const;

export type Submission = { operation: Operation; parameters: Record<string, unknown> };

/* Mockup 2 is design states: nothing is wired to an engine yet, and pretending otherwise would
 * make the mockup evidence of implemented behaviour, which it never is. The one submit path
 * exists so every screen already dispatches through it (INV-006) - the transport arrives later. */
export function submit(submission: Submission): { status: "design-state" } {
  console.info("command (design state, not executed):", submission.operation, submission.parameters);
  return { status: "design-state" };
}
