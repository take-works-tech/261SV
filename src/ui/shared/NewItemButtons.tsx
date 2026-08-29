/* The creation row of 11_ui.md: ＋ 新規シミュレーション / ＋ 新規ビュー / ＋ 新規グラフ /
 * ＋ 新規レポート / ＋ 新規パイプライン - one row, one component, five labels.
 *
 * The spec lists them as a single component deliberately: five separately-written buttons drift,
 * and the drift shows up as five different words for "create" in five areas. The kinds are the
 * workflow tabs in their decided order, so the row cannot disagree with the toolbar.
 *
 * `check_commands.py` cannot match this by filename - the component's name in 11_ui.md is its five
 * labels, which no filename can carry. The gate now says so rather than passing in silence.
 */

export type ItemKind = "simulation" | "view" | "graph" | "report" | "pipeline";

const LABEL: Record<ItemKind, string> = {
  simulation: "＋ 新規シミュレーション",
  view: "＋ 新規ビュー",
  graph: "＋ 新規グラフ",
  report: "＋ 新規レポート",
  pipeline: "＋ 新規パイプライン",
};

/** The workflow order of 11_ui.md - Automation last, because it composes the others. */
export const ITEM_KINDS: readonly ItemKind[] = ["simulation", "view", "graph", "report", "pipeline"];

export function NewItemButtons(props: {
  kinds?: readonly ItemKind[];
  onCreate: (kind: ItemKind) => void;
  /** Per-kind reason. A creation that cannot happen says why, rather than looking broken. */
  disabled?: Partial<Record<ItemKind, string>>;
}) {
  const kinds = props.kinds ?? ITEM_KINDS;
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }} role="group" aria-label="新規作成">
      {kinds.map((kind) => {
        const because = props.disabled?.[kind];
        return (
          <button
            key={kind}
            className="btn"
            disabled={because !== undefined}
            title={because !== undefined ? `無効：${because}` : undefined}
            onClick={() => props.onCreate(kind)}
          >
            {LABEL[kind]}
          </button>
        );
      })}
    </div>
  );
}
