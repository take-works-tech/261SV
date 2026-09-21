/* The camera path with an engine (XC-289): keyframes taken from the live look, the rule between them,
 * and a scrub that draws the frame the engine interpolates - answered with the pose and the rule, which
 * the panel shows rather than restates. The design states keep their own presets; this panel appears
 * only where there is a picture to take a look from. */
import { useState } from "react";
import { engineState, useEngine } from "../state/engine";
import { canFollow, describePath, followReason, keyframeRow, RULE_LABEL, suggestedParameter, type Interpolation } from "../logic/cameraPath";
import { disabledBecause } from "../logic/format";

export function CameraPathPanel() {
  const e = useEngine();
  const [open, setOpen] = useState(false);
  const [at, setAt] = useState<number | null>(null);
  const [preview, setPreview] = useState(0);
  const path = e.cameraPaths[0] ?? null;
  const reason = followReason(path);
  const nextAt = at ?? suggestedParameter(path);

  if (!open) {
    return (
      <button className="btn ghost" style={{ position: "absolute", right: 10, bottom: 54, zIndex: 3 }} onClick={() => setOpen(true)} title="カメラパス：今の向きをキーフレームにして、経路上の姿勢を描く（XC-289）">
        カメラパス{path ? `（${path.keyframes.length}）` : ""}
      </button>
    );
  }
  return (
    <section className="vi-panel" style={{ right: 10, bottom: 54, width: "min(420px, calc(100vw - 24px))" }} aria-label="カメラパス">
      <header>
        <b>{path ? describePath(path) : "カメラパス"}</b>
        <button className="icon-button" aria-label="閉じる" onClick={() => setOpen(false)}>×</button>
      </header>
      <div className="body" style={{ display: "grid", gap: 6 }}>
        <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
          <label className="type-caption">
            媒介変数 t
            <input type="number" className="field-input" min={0} max={1} step={0.05} value={nextAt} style={{ width: 72, marginLeft: 4 }} onChange={(event) => setAt(Number(event.target.value))} />
          </label>
          <button className="btn primary" onClick={() => void engineState.addPathKeyframe(nextAt).then(() => setAt(null))} title="今の向き（回して見ている姿勢）をこの t のキーフレームにする">
            今の向きを追加
          </button>
        </div>
        {path ? (
          <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 3 }}>
            {path.keyframes.map((keyframe) => (
              <li key={keyframe.at} className="vi-row" style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <span style={{ fontVariantNumeric: "tabular-nums", flex: 1, minWidth: 0 }}>{keyframeRow(keyframe)}</span>
                <button className="btn ghost" onClick={() => void engineState.removePathKeyframe(keyframe.at)} title="このキーフレームを外す">外す</button>
              </li>
            ))}
          </ol>
        ) : null}
        <div role="radiogroup" aria-label="補間" style={{ display: "flex", gap: 4 }}>
          {(Object.keys(RULE_LABEL) as Interpolation[]).map((rule) => (
            <button key={rule} role="radio" aria-checked={path?.interpolation === rule} className={path?.interpolation === rule ? "btn" : "btn ghost"} title={RULE_LABEL[rule]} {...(path ? {} : disabledBecause("キーフレームがまだありません"))} onClick={() => void engineState.setPathInterpolation(rule)}>
              {rule === "linear" ? "直線" : "滑らか"}
            </button>
          ))}
        </div>
        <label className="type-caption" style={{ display: "grid", gap: 2 }}>
          経路上の位置 t = {preview.toFixed(2)}
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={preview}
            {...(canFollow(path) ? {} : disabledBecause(reason ?? "経路を辿れません"))}
            onChange={(event) => {
              const value = Number(event.target.value);
              setPreview(value);
              void engineState.previewPath(value);
            }}
          />
        </label>
        {e.pathPreview ? (
          <p className="type-caption" style={{ margin: 0, color: "var(--ink-muted)" }}>
            描画した姿勢：位置 ({e.pathPreview.camera.position_m?.map((one) => one.toFixed(3)).join(", ")}) m・{e.pathPreview.rule}
          </p>
        ) : reason ? (
          <p className="type-caption" style={{ margin: 0, color: "var(--ink-muted)" }}>{reason}</p>
        ) : null}
        {e.pathPreview ? (
          <button className="btn ghost" style={{ justifySelf: "start" }} onClick={() => void engineState.clearPathPreview()} title="経路の姿勢をやめ、回して見ていた向きに戻す">
            回していた向きに戻す
          </button>
        ) : null}
      </div>
      <footer>キーフレームはビュー定義に保存されます（CT-004）。動画の書き出しはエンコーダの判断（#276）待ちです。</footer>
    </section>
  );
}
