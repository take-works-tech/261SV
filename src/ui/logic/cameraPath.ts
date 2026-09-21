/* A camera path as the interface edits it (XC-289, CT-004 3.3.0): keyframes of the live look at a
 * parameter from 0 to 1, and the rule between them. Nothing is interpolated here - the engine does that
 * and answers the pose with the rule - so this layer only keeps the list honest: ordered, no two
 * keyframes at one parameter, and a path of one keyframe named as one that cannot be followed. No React
 * and no transport. */
import type { CameraDefinition } from "../client/generated";

export type Interpolation = "linear" | "smooth";

export interface Keyframe {
  readonly at: number;
  readonly camera: CameraDefinition;
}

export interface CameraPathDefinition {
  readonly id: string;
  readonly name: string;
  readonly interpolation: Interpolation;
  readonly keyframes: readonly Keyframe[];
}

export const RULE_LABEL: Record<Interpolation, string> = {
  linear: "直線（キーフレームの間をまっすぐ）",
  smooth: "滑らか（Catmull-Rom 曲線がキーフレームを通る）",
};

/** The one path the interface edits in r1, made when the first keyframe is added. */
export const FIRST_PATH = { id: "path:1", name: "カメラパス 1" } as const;

/** A path with `camera` added at `at`, kept in parameter order - or the reason it cannot be. */
export function withKeyframe(path: CameraPathDefinition | null, at: number, camera: CameraDefinition): { path: CameraPathDefinition } | { refused: string } {
  if (!Number.isFinite(at) || at < 0 || at > 1) return { refused: `媒介変数 ${at} は 0〜1 の外です` };
  const base: CameraPathDefinition = path ?? { ...FIRST_PATH, interpolation: "linear", keyframes: [] };
  if (base.keyframes.some((one) => one.at === at)) return { refused: `媒介変数 ${at} には既にキーフレームがあります。別の値にするか、先に外してください` };
  const keyframes = [...base.keyframes, { at, camera }].sort((a, b) => a.at - b.at);
  return { path: { ...base, keyframes } };
}

/** The path without the keyframe at `at`. */
export function withoutKeyframe(path: CameraPathDefinition, at: number): CameraPathDefinition {
  return { ...path, keyframes: path.keyframes.filter((one) => one.at !== at) };
}

/** Whether the engine can follow the path: two keyframes at least (a path of one is refused by name). */
export function canFollow(path: CameraPathDefinition | null): path is CameraPathDefinition {
  return path !== null && path.keyframes.length >= 2;
}

/** Why the path cannot be followed, or null. */
export function followReason(path: CameraPathDefinition | null): string | null {
  if (!path || path.keyframes.length === 0) return "キーフレームがまだありません。今の向きを 1 つ目として追加してください";
  if (path.keyframes.length === 1) return "キーフレームが 1 件です。経路には 2 件以上が要ります";
  return null;
}

/** Where a new keyframe would go by default: 0 for the first, 1 for the second, then halfway
 *  between the last two so the list stays in order without a person typing a number. */
export function suggestedParameter(path: CameraPathDefinition | null): number {
  if (!path || path.keyframes.length === 0) return 0;
  if (path.keyframes.length === 1) return path.keyframes[0]?.at === 1 ? 0 : 1;
  const last = path.keyframes[path.keyframes.length - 1]?.at ?? 1;
  const before = path.keyframes[path.keyframes.length - 2]?.at ?? 0;
  return Number(((last + before) / 2).toFixed(3));
}

/** One keyframe as a row: the parameter and where the camera stands, at the digits a look needs. */
export function keyframeRow(keyframe: Keyframe): string {
  const position = keyframe.camera.position_m?.map((one) => one.toFixed(3)).join(", ") ?? "位置なし";
  return `t = ${keyframe.at}：位置 (${position}) m・${keyframe.camera.projection}`;
}

export function describePath(path: CameraPathDefinition): string {
  return `${path.name}：キーフレーム ${path.keyframes.length} 件・${RULE_LABEL[path.interpolation]}`;
}
