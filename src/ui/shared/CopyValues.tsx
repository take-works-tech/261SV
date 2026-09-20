/* Copying shown values as a spreadsheet takes them (XC-279): the rows the logic layer built, written
 * to the clipboard as tab-separated text, and what happened said beside the button. The rows carry
 * the value at its digits, the unit or the marker, the provenance, the location and the caveats -
 * a pasted number never travels alone (XC-003, INV-013). */
import { useState } from "react";
import { tsv } from "../logic/copy";

export function CopyValues(props: { rows: readonly (readonly string[])[]; label?: string; title?: string }) {
  const [said, setSaid] = useState<string | null>(null);
  const copy = async () => {
    const text = tsv(props.rows);
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      setSaid("この環境ではクリップボードに書けません");
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setSaid(`写しました（${Math.max(0, props.rows.length - 1)} 行・タブ区切り・見出し付き）`);
    } catch (failure) {
      setSaid(`写せませんでした：${failure instanceof Error ? failure.message : String(failure)}`);
    }
  };
  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center", minWidth: 0 }}>
      <button
        type="button"
        className="btn ghost"
        onClick={() => void copy()}
        title={props.title ?? "値・単位・有効桁・来歴・位置・注記をタブ区切りで写します。表計算にそのまま貼れます"}
      >
        {props.label ?? "値を写す"}
      </button>
      {said ? (
        <small className="type-caption" style={{ color: "var(--ink-muted)" }} role="status">
          {said}
        </small>
      ) : null}
    </span>
  );
}
