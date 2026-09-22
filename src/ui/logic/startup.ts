/* What the interface says while the engine starts (XC-304): that it is starting, for how long, and -
 * once it has taken longer than a warm start does - why that can be, in words that promise no
 * time. Never a design state: a page that shows invented cards while the real engine loads is a
 * page that lies for the first seconds of every launch. No React and no transport. */
import type { Reachability } from "../state/engine";
import { LAUNCH_BUDGET_SECONDS } from "./budgets";

/** After this many seconds a start is slow by this product's own measurement (E-222): a warm start
 *  reaches the engine well under a second on the development machine, and the first start after
 *  installing reads the bundled toolkit - hundreds of megabytes - from disk. */
export const SLOW_AFTER_SECONDS = 5;

export interface StartupWords {
  title: string;
  detail: string;
  /** Longer than a warm start: the detail says what can take the time. */
  slow: boolean;
  /** The start ended without an engine: the detail is the reason, and a restart is the way on. */
  failed: boolean;
  /** Past LIM-010: said, with the budget named, and never absorbed (XC-305). */
  overBudget: boolean;
}

/** The words for the page, from what the shell has said and how long the page has waited. */
export function describeStartup(reachability: Reachability, elapsedSeconds: number): StartupWords {
  const seconds = Math.max(0, Math.floor(elapsedSeconds));
  if (reachability.kind === "absent") {
    return { title: "エンジンに接続できませんでした", detail: reachability.because, slow: false, failed: true, overBudget: false };
  }
  if (reachability.kind === "exited") {
    return { title: "エンジンが起動中に終了しました", detail: reachability.because, slow: false, failed: true, overBudget: false };
  }
  const slow = seconds >= SLOW_AFTER_SECONDS;
  const overBudget = seconds >= LAUNCH_BUDGET_SECONDS;
  const budget = overBudget ? `起動の予算（${LAUNCH_BUDGET_SECONDS} 秒、LIM-010）を超えました。` : "";
  const detail = budget + (slow
    ? "通常より長くかかっています。初回の起動やインストール直後は、同梱の計算ライブラリ（数百 MB）の読み込みに数秒かかることがあります。応答がないままなら、シェルが待つのをやめて理由を示します"
    : "計算エンジンを別のプロセスとして起動し、その応答を待っています。この画面に出る数値は、すべてエンジンが答えたものです");
  return { title: `エンジンを起動しています（${seconds} 秒）`, detail, slow, failed: false, overBudget };
}
