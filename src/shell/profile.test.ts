/* The profile's layout (XC-300): the recent list is beside the engine's root and the logs and
 * inside neither, so nothing the engine is told about contains a customer's paths. */
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";

import { isInside, layoutUnder } from "./profile";

describe("the profile layout", () => {
  const root = join(tmpdir(), "solvia-プロファイル (試験)");
  const layout = layoutUnder(root);

  test("the engine root and the log directory are under the profile, beside each other", () => {
    expect(isInside(layout.engineRoot, root)).toBe(true);
    expect(isInside(layout.logDirectory, root)).toBe(true);
    expect(isInside(layout.logDirectory, layout.engineRoot)).toBe(false);
    expect(isInside(layout.engineRoot, layout.logDirectory)).toBe(false);
  });

  test("the recent list is under the profile and inside neither directory the engine is told about", () => {
    expect(isInside(layout.recentFile, root)).toBe(true);
    expect(isInside(layout.recentFile, layout.engineRoot)).toBe(false);
    expect(isInside(layout.recentFile, layout.logDirectory)).toBe(false);
  });

  test("isInside is path arithmetic: a session file is inside the engine root; a sibling, the root itself and a parent are not", () => {
    expect(isInside(join(layout.engineRoot, "sessions", "1234", "connection.json"), layout.engineRoot)).toBe(true);
    expect(isInside(join(root, "engine-notes.txt"), layout.engineRoot)).toBe(false);
    expect(isInside(layout.engineRoot, layout.engineRoot)).toBe(false);
    expect(isInside(join(root, "..", "elsewhere.json"), root)).toBe(false);
  });
});
