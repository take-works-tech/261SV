/* The engine's reachability as the shell reports it (XC-259, XC-304): starting is a state of its
 * own, distinct from never having had an engine and from having lost one. Plain Node: nothing here
 * talks to an engine. */
import { describe, expect, test } from "vitest";

import { engineState, snapshot } from "./engine";

describe("the engine's reachability", () => {
  test("starting carries when the shell began, a failed connection says why, and a lost engine is told apart", () => {
    const since = { utc: "2026-09-22T00:00:00Z", offsetMinutes: 540 };
    engineState.engineStarting({ since });
    expect(snapshot().reachability).toEqual({ kind: "starting", since });
    expect(snapshot().busy).toBe(false);

    engineState.engineStarting({});
    expect(snapshot().reachability).toEqual({ kind: "starting", since: null });

    engineState.disconnect();
    expect(snapshot().reachability.kind).toBe("absent");

    engineState.engineExited({ reason: "終了コード 3", exitCode: 3, signal: null });
    expect(snapshot().reachability).toMatchObject({ kind: "exited", because: "終了コード 3", exitCode: 3 });
  });
});
