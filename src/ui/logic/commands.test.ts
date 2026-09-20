/* The command list from the generated catalogue and the engine's registry (XC-277). */
import { describe, expect, test } from "vitest";

import { OPERATIONS } from "../client/generated";
import { commandGroups, describeAnswering, NO_KEY, STATUS_LABEL } from "./commands";

const ANSWERING = { registered: ["workspace.open", "dataset.load", "system.operations"], unimplemented: ["graph.data"] };

describe("the rows", () => {
  test("every operation of the contract is a row, once, under its namespace, in the catalogue's order within it", () => {
    const groups = commandGroups(null, "");
    const flat = groups.flatMap((group) => group.rows.map((row) => row.operation));

    expect([...flat].sort()).toEqual([...OPERATIONS].sort());
    expect(new Set(flat).size).toBe(OPERATIONS.length);
    expect(groups[0]?.namespace).toBe("workspace");
    for (const group of groups) {
      expect(group.rows.every((row) => row.namespace === group.namespace)).toBe(true);
      // The catalogue lists a namespace's operations in more than one run (dataset.probe comes after
      // the view operations); within a group the rows keep the catalogue's order.
      const positions = group.rows.map((row) => OPERATIONS.indexOf(row.operation));
      expect([...positions].sort((a, b) => a - b)).toEqual(positions);
    }
  });

  test("a row says its class, its parameters by name with the optional ones marked, and what it answers", () => {
    const load = commandGroups(null, "").flatMap((group) => group.rows).find((row) => row.operation === "dataset.load");
    const protocols = commandGroups(null, "").flatMap((group) => group.rows).find((row) => row.operation === "system.protocols");

    expect(load).toMatchObject({ writes: true, parameters: "caseId、filePaths", status: "unknown" });
    expect(load?.answers).toContain("datasetId");
    expect(protocols).toMatchObject({ writes: false, parameters: "なし", answers: "versions" });
  });

  test("with the engine's answer each row says whether this build answers it", () => {
    const rows = commandGroups(ANSWERING, "").flatMap((group) => group.rows);
    const status = Object.fromEntries(rows.map((row) => [row.operation, row.status]));

    expect(status["workspace.open"]).toBe("answers");
    expect(status["graph.data"]).toBe("unimplemented");
    // An operation the answer names in neither half is not guessed either way.
    expect(status["view.render"]).toBe("unknown");
    expect(STATUS_LABEL.unimplemented).toContain("拒否");
  });

  test("the query matches an operation's name or one of its parameters, and nothing else", () => {
    const byName = commandGroups(null, "pick").flatMap((group) => group.rows).map((row) => row.operation);
    const byParameter = commandGroups(null, "takeOverStaleLock").flatMap((group) => group.rows).map((row) => row.operation);

    expect(byName).toEqual(["view.pick"]);
    expect(byParameter).toEqual(["workspace.open"]);
    expect(commandGroups(null, "no such thing")).toEqual([]);
  });
});

describe("the sentence above the list", () => {
  test("says how much of the catalogue this build answers, or that it is not yet known", () => {
    expect(describeAnswering(null)).toContain(`${OPERATIONS.length} 操作`);
    expect(describeAnswering(null)).toContain("接続すると分かります");
    expect(describeAnswering(ANSWERING)).toContain("3 操作に答え");
    expect(describeAnswering(ANSWERING)).toContain("1 操作は実装がなく");
    expect(NO_KEY).toBe("キーなし");
  });
});
