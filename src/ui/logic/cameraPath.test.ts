/* The camera path list the interface keeps: ordered, one keyframe per parameter, and honest about
 * whether it can be followed (XC-289). */
import { describe, expect, test } from "vitest";

import { canFollow, describePath, followReason, keyframeRow, suggestedParameter, withKeyframe, withoutKeyframe } from "./cameraPath";

const LOOK = { position_m: [4, 0, 0], focalPoint_m: [0, 0, 0], viewUp: [0, 0, 1], projection: "perspective" as const };
const OTHER = { ...LOOK, position_m: [0, 4, 0] };

describe("adding keyframes", () => {
  test("the first keyframe makes the path, and keyframes stay in parameter order", () => {
    const first = withKeyframe(null, 1, LOOK);
    if ("refused" in first) throw new Error(first.refused);
    expect(first.path.id).toBe("path:1");
    expect(canFollow(first.path)).toBe(false);
    expect(followReason(first.path)).toContain("1 件");

    const second = withKeyframe(first.path, 0, OTHER);
    if ("refused" in second) throw new Error(second.refused);
    expect(second.path.keyframes.map((one) => one.at)).toEqual([0, 1]);
    expect(canFollow(second.path)).toBe(true);
    expect(followReason(second.path)).toBeNull();
  });

  test("two keyframes at one parameter are refused, and one outside 0..1 too", () => {
    const first = withKeyframe(null, 0.5, LOOK);
    if ("refused" in first) throw new Error(first.refused);
    expect(withKeyframe(first.path, 0.5, OTHER)).toEqual({ refused: "媒介変数 0.5 には既にキーフレームがあります。別の値にするか、先に外してください" });
    expect(withKeyframe(first.path, 1.5, OTHER)).toEqual({ refused: "媒介変数 1.5 は 0〜1 の外です" });
  });

  test("removing a keyframe leaves the rest", () => {
    const first = withKeyframe(null, 0, LOOK);
    if ("refused" in first) throw new Error(first.refused);
    const second = withKeyframe(first.path, 1, OTHER);
    if ("refused" in second) throw new Error(second.refused);
    expect(withoutKeyframe(second.path, 0).keyframes.map((one) => one.at)).toEqual([1]);
  });
});

describe("what the panel says", () => {
  test("the suggested parameter walks 0, 1, then halfway between the last two", () => {
    expect(suggestedParameter(null)).toBe(0);
    const first = withKeyframe(null, 0, LOOK);
    if ("refused" in first) throw new Error(first.refused);
    expect(suggestedParameter(first.path)).toBe(1);
    const second = withKeyframe(first.path, 1, OTHER);
    if ("refused" in second) throw new Error(second.refused);
    expect(suggestedParameter(second.path)).toBe(0.5);
  });

  test("a keyframe row and the path's description carry the facts", () => {
    const first = withKeyframe(null, 0, LOOK);
    if ("refused" in first) throw new Error(first.refused);
    expect(keyframeRow(first.path.keyframes[0]!)).toBe("t = 0：位置 (4.000, 0.000, 0.000) m・perspective");
    expect(describePath({ ...first.path, interpolation: "smooth" })).toBe("カメラパス 1：キーフレーム 1 件・滑らか（Catmull-Rom 曲線がキーフレームを通る）");
    expect(followReason(null)).toContain("まだありません");
  });
});
