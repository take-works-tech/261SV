/* The runs and the plan as the settings page shows them: newest first, every time saying where it
 * came from, and every file by name before anything goes (XC-141, AC-053, XC-268). */
import { describe, expect, test } from "vitest";

import { OSAKA } from "./fixtures";
import { describePlan, describeTotal, runLines, type OutputListing } from "./output";

const LISTING: OutputListing = {
  outputDirectory: "D:/studies/bracket/output",
  runs: [
    { id: "report-a/2026-09-01T00-00-00", started: { utc: "2026-09-01T00:00:00Z", offsetMinutes: OSAKA }, startedFrom: "record", artefactFiles: 2, artefactBytes: 500, hasRecord: true },
    { id: "report-a/2026-09-02T00-00-00", started: { utc: "2026-09-02T00:00:00Z", offsetMinutes: OSAKA }, startedFrom: "folder", artefactFiles: 1, artefactBytes: 2048, hasRecord: false },
  ],
  totalBytes: 2548,
  limitBytes: 21474836480,
  overLimit: false,
  suggestedRunIds: ["report-a/2026-09-01T00-00-00"],
};

describe("the runs as a table", () => {
  test("newest first, split into name and stamp, each time saying where it came from", () => {
    const lines = runLines(LISTING, OSAKA);

    expect(lines.map((one) => one.stamp)).toEqual(["2026-09-02T00-00-00", "2026-09-01T00-00-00"]);
    expect(lines[0]).toMatchObject({ name: "report-a", started: "2026-09-02 09:00", startedNote: "フォルダの更新時刻から（記録なし）", hasRecord: false, size: "2.0 KiB", suggested: false });
    expect(lines[1]).toMatchObject({ started: "2026-09-01 09:00", startedNote: "実行の記録から", files: 2, size: "500 B", suggested: true });
  });

  test("the total is an ask when over the limit, and a plain statement when not", () => {
    expect(describeTotal(LISTING)).toBe("出力は 2.5 KiB（2 実行分）。上限 20.0 GiB");
    expect(describeTotal({ ...LISTING, overLimit: true })).toContain("拒否ではなく、確認のお願いです");
  });
});

describe("the plan as the confirmation shows it", () => {
  test("every file by name, the total beside them, and what stays", () => {
    const shown = describePlan({
      runIds: ["report-a/2026-09-01T00-00-00"],
      files: ["report-a/2026-09-01T00-00-00/case-1/figure.png", "report-a/2026-09-01T00-00-00/case-1/table.csv"],
      freedBytes: 500,
      keptRecords: ["report-a/2026-09-01T00-00-00/run.json"],
    });

    expect(shown.files).toHaveLength(2);
    expect(shown.summary).toBe("1 実行分から 2 ファイル、500 B を削除します");
    expect(shown.kept).toContain("記録 1 件は残します");
  });
});
