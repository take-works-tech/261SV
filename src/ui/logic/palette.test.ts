/* The palette's rows: what this screen can run now, with its parameters from the context, and why
 * the rest cannot (XC-278). */
import { describe, expect, test } from "vitest";

import { OPERATIONS } from "../client/generated";
import { describeParameters, paletteRows, type Context } from "./palette";

const EMPTY: Context = { workspaceId: null, caseId: null, datasetId: null, viewId: null, reportId: null, fieldName: null };
const LOADED: Context = { workspaceId: "ws:1", caseId: "case:1", datasetId: "dataset:0001", viewId: "view:0001", reportId: null, fieldName: "temperature" };
const ANSWERING = {
  registered: ["workspace.open", "workspace.save", "dataset.describe", "field.statistics", "view.render", "report.get", "output.prune", "system.protocols"],
  unimplemented: ["graph.data"],
};

describe("what can run now", () => {
  test("an operation runs when the engine answers it and the context holds every required parameter", () => {
    const rows = paletteRows(ANSWERING, LOADED, "");
    const byName = Object.fromEntries(rows.map((row) => [row.operation, row]));

    expect(byName["dataset.describe"]).toMatchObject({ runnable: true, parameters: { datasetId: "dataset:0001" }, writes: false });
    expect(byName["field.statistics"]).toMatchObject({ runnable: true, parameters: { datasetId: "dataset:0001", fieldName: "temperature" } });
    expect(byName["system.protocols"]).toMatchObject({ runnable: true, parameters: {} });
    expect(byName["workspace.save"]).toMatchObject({ runnable: true, writes: true, parameters: { workspaceId: "ws:1" } });
  });

  test("a parameter the context does not hold stops the run and is named", () => {
    const rows = paletteRows(ANSWERING, LOADED, "");
    const byName = Object.fromEntries(rows.map((row) => [row.operation, row]));

    expect(byName["view.render"]?.runnable).toBe(false);
    expect(byName["view.render"]?.because).toContain("width");
    expect(byName["view.render"]?.parameters).toEqual({ viewId: "view:0001" });
    expect(byName["report.get"]?.because).toContain("reportId");
    expect(byName["workspace.open"]?.because).toContain("path");
  });

  test("an unimplemented operation, one the engine did not name, and the destructive one never run", () => {
    const rows = paletteRows(ANSWERING, LOADED, "");
    const byName = Object.fromEntries(rows.map((row) => [row.operation, row]));

    expect(byName["graph.data"]?.because).toContain("実装なし");
    expect(byName["view.pick"]?.because).toContain("接続時");
    expect(byName["output.prune"]).toMatchObject({ runnable: false });
    expect(byName["output.prune"]?.because).toContain("確認");
  });

  test("without an engine nothing runs, and every row says so", () => {
    const rows = paletteRows(null, LOADED, "");
    expect(rows).toHaveLength(OPERATIONS.length);
    expect(rows.every((row) => !row.runnable)).toBe(true);
    // The destructive one keeps its own reason whatever the connection: it never runs from here.
    expect(rows.filter((row) => row.operation !== "output.prune").every((row) => row.because === "エンジンに接続していません")).toBe(true);
    expect(rows.find((row) => row.operation === "output.prune")?.because).toContain("確認");
  });

  test("the query narrows by the operation's name, and the parameters read as one line", () => {
    const rows = paletteRows(ANSWERING, LOADED, "statistics");
    expect(rows.map((row) => row.operation)).toEqual(["field.statistics"]);
    expect(describeParameters(rows[0] as NonNullable<(typeof rows)[0]>)).toBe("datasetId = dataset:0001、fieldName = temperature");
    expect(describeParameters(paletteRows(ANSWERING, EMPTY, "protocols")[0] as NonNullable<(typeof rows)[0]>)).toBe("引数なし");
  });
});
