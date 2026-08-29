/* The second toolbar (MOD-009): panel toggles at the OUTER ends (XC-144 - a sidebar never repeats
 * its toggle in its own header), work tools, then the workflow tabs in the decided order
 * Simulation, View, Graph, Report, Automation - Chat is a work area but not an ordered tab, and
 * the three specified-but-new areas ride behind a 分析 cluster. */
import { session, useSession, type ScreenId } from "../state/session";

const WORKFLOW_TABS: { id: ScreenId; label: string }[] = [
  { id: "simulation", label: "シミュレーション" },
  { id: "view", label: "ビュー" },
  { id: "graph", label: "グラフ" },
  { id: "report", label: "レポート" },
  { id: "pipeline", label: "自動化" },
];

const ANALYSIS_TABS: { id: ScreenId; label: string; title: string }[] = [
  { id: "information", label: "情報", title: "読み込んだデータが実際に何を含むか" },
  { id: "find", label: "選択", title: "条件による点・セルの選択" },
  { id: "diff", label: "差分", title: "二ケースの差、三点開示つき" },
];

export function WorkToolbar() {
  const s = useSession();
  const running = s.screen === "pipeline" && s.variant === "running";

  return (
    <div className="work-toolbar">
      <div className="cluster">
        <button
          className="icon-button"
          aria-pressed={s.leftOpen}
          aria-label={s.leftOpen ? "左パネルを閉じる" : "左パネルを開く"}
          title="左パネル（Ctrl+B）"
          onClick={session.toggleLeft}
        >
          ⧉
        </button>
      </div>
      <div className="tool-divider" />
      <div className="cluster">
        <button className="icon-button" aria-label="読み込み" title="結果ファイルを読み込む（Ctrl+O）">⤓</button>
        <button className="icon-button" aria-label="保存" title="ワークスペースを保存（Ctrl+S）">⤒</button>
        <button className="icon-button" aria-label="取り消し" title="取り消し（Ctrl+Z）">↶</button>
        <button className="icon-button" aria-label="やり直し" title="やり直し（Ctrl+Y）">↷</button>
      </div>

      <nav className="area-tabs" role="tablist" aria-label="作業領域">
        {WORKFLOW_TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={s.screen === tab.id}
            onClick={() => session.navigate(tab.id)}
          >
            {tab.label}
          </button>
        ))}
        <span className="tool-divider" aria-hidden />
        {ANALYSIS_TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={s.screen === tab.id}
            title={tab.title}
            onClick={() => session.navigate(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {running ? (
        <span className="run-chip" role="status">
          <span className="spinner" aria-hidden />
          実行中 — 編集はロック、中断はユニット境界で
        </span>
      ) : null}

      <div className="cluster" style={{ marginLeft: "auto" }}>
        <button
          className="icon-button"
          aria-pressed={s.screen === "chat"}
          aria-label="チャット"
          title="一つの会話の全高表示（XC-150）"
          onClick={() => session.navigate("chat")}
        >
          ✉
        </button>
        <button
          className="icon-button"
          aria-pressed={s.rightOpen}
          aria-label={s.rightOpen ? "右パネルを閉じる" : "右パネルを開く"}
          title="右パネル（Ctrl+Alt+B）"
          onClick={session.toggleRight}
        >
          ⧉
        </button>
      </div>
    </div>
  );
}
