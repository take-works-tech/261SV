/* The product shell (MOD-009). Composition follows mockup 1 (XC-256): topbar, work toolbar,
 * then the three-column workbench - navigator, centre column with work-area bar, canvas, shelf and
 * instruction bar, and the property rail. Settings and home are application pages: settings
 * composes its own navigation without workspace sidebars (XC-165); chat swaps the navigator for the
 * conversation list and owns its composer (XC-150); network hides the case tree because permission
 * is workspace-wide. */
import type { ReactNode } from "react";
import { session, useSession, type ScreenId } from "../state/session";
import { InstructionBar } from "../shared/InstructionBar";
import { Topbar } from "./Topbar";
import { WorkToolbar } from "./WorkToolbar";
import { LeftSidebar } from "./LeftSidebar";
import { RightSidebar } from "./RightSidebar";
import { CatalogDrawer } from "./CatalogDrawer";
import { submit } from "../client/operations";

import { HomeScreen } from "./screens/HomeScreen";
import { ViewScreen, ViewRail } from "./screens/ViewScreen";
import { GraphScreen, GraphRail } from "./screens/GraphScreen";
import { ReportScreen, ReportRail } from "./screens/ReportScreen";
import { PipelineScreen, PipelineRail } from "./screens/PipelineScreen";
import { SimulationScreen, SimulationRail } from "./screens/SimulationScreen";
import { ChatScreen } from "./screens/ChatScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { NetworkScreen, NetworkRail } from "./screens/NetworkScreen";
import { InformationScreen, InformationRail } from "./screens/InformationScreen";
import { FindScreen, FindRail } from "./screens/FindScreen";
import { DiffScreen, DiffRail } from "./screens/DiffScreen";

const TITLES: Record<ScreenId, string> = {
  home: "ワークスペース一覧",
  simulation: "実行条件フロー",
  view: "ビュー：全体外観",
  graph: "グラフ：ケース横断 最大応力",
  report: "レポート：Run 12 強度確認",
  pipeline: "パイプライン：全ケース書き出し",
  chat: "会話",
  settings: "設定",
  network: "ネットワークと監査",
  information: "データの中身：Run 12",
  find: "条件選択",
  diff: "差分：Run 12 − Run 11",
};

const SHELF_SCREENS: ScreenId[] = ["view", "graph", "report"];

const SHELF_CARDS: Partial<Record<ScreenId, string[]>> = {
  view: ["テンプレート", "マテリアル", "背景", "ガイド", "フォント"],
  graph: ["テンプレート", "スタイル", "フォント"],
  report: ["テンプレート", "レイアウト", "スタイル", "フォント"],
};

export function App() {
  const s = useSession();

  const canvas = ((): ReactNode => {
    switch (s.screen) {
      case "home": return <HomeScreen variant={s.variant} />;
      case "view": return <ViewScreen variant={s.variant} />;
      case "graph": return <GraphScreen variant={s.variant} />;
      case "report": return <ReportScreen variant={s.variant} />;
      case "pipeline": return <PipelineScreen variant={s.variant} />;
      case "simulation": return <SimulationScreen variant={s.variant} />;
      case "chat": return <ChatScreen variant={s.variant} />;
      case "settings": return <SettingsScreen variant={s.variant} />;
      case "network": return <NetworkScreen variant={s.variant} />;
      case "information": return <InformationScreen variant={s.variant} />;
      case "find": return <FindScreen variant={s.variant} />;
      case "diff": return <DiffScreen variant={s.variant} />;
    }
  })();

  const rail = (tab: string): ReactNode => {
    switch (s.screen) {
      case "view": return <ViewRail tab={tab} variant={s.variant} />;
      case "graph": return <GraphRail tab={tab} variant={s.variant} />;
      case "report": return <ReportRail tab={tab} variant={s.variant} />;
      case "pipeline": return <PipelineRail tab={tab} variant={s.variant} />;
      case "simulation": return <SimulationRail tab={tab} variant={s.variant} />;
      case "network": return <NetworkRail tab={tab} variant={s.variant} />;
      case "information": return <InformationRail tab={tab} variant={s.variant} />;
      case "find": return <FindRail tab={tab} variant={s.variant} />;
      case "diff": return <DiffRail tab={tab} variant={s.variant} />;
      default: return null;
    }
  };

  // Application pages own the whole body (XC-165).
  if (s.screen === "home" || s.screen === "settings") {
    return (
      <section className="product-shell">
        <header className="app-header">
          <Topbar />
        </header>
        <div className="centre-column" style={{ flex: 1, minHeight: 0 }}>{canvas}</div>
        <CatalogDrawer />
      </section>
    );
  }

  const isChat = s.screen === "chat";
  const hasRail = !isChat;
  const workbenchClass = [
    "workbench",
    s.leftOpen ? "" : "left-closed",
    s.rightOpen && hasRail ? "" : "right-closed",
  ].filter(Boolean).join(" ");

  return (
    <section className="product-shell">
      <header className="app-header">
        <Topbar />
        <WorkToolbar />
      </header>
      <div
        className={workbenchClass}
        style={{
          ["--left-w" as string]: `${s.leftWidth}px`,
          ["--right-w" as string]: `${s.rightWidth}px`,
        }}
      >
        {s.leftOpen ? <LeftSidebar /> : null}
        <div className="centre-column">
          {!isChat ? (
            <div className="work-area-bar">
              <span className="title">{TITLES[s.screen]}</span>
              {s.screen === "view" ? (
                <span className="cluster" role="group" aria-label="分割">
                  {([1, 2, 3, 4] as const).map((count) => (
                    <button
                      key={count}
                      className="icon-button"
                      style={{ width: 24, height: 24 }}
                      aria-pressed={s.paneCount === count}
                      aria-label={`${count} 画面`}
                      onClick={() => session.setPaneCount(count)}
                    >
                      {count}
                    </button>
                  ))}
                  <button
                    className="icon-button"
                    style={{ width: "auto", padding: "0 8px" }}
                    aria-pressed={s.cameraSync}
                    title="カメラ同期（分割は出力されません — XC-210）"
                    onClick={session.toggleCameraSync}
                  >
                    同期
                  </button>
                </span>
              ) : null}
              <span className="spacer" />
            </div>
          ) : null}

          <div className="canvas-wrap">{canvas}</div>

          {SHELF_SCREENS.includes(s.screen) ? (() => {
            // The material-library shelf's six states are catalogued view variants (mockup 1's
            // library-*); the shelf itself is shell furniture, so the states live here.
            const shelfState = s.screen === "view" && s.variant.startsWith("library-")
              ? s.variant.replace("library-", "")
              : "one-row";
            const cards = SHELF_CARDS[s.screen] ?? [];
            const searching = shelfState === "searching";
            const rows = shelfState === "expanded" ? [cards, cards] : [cards];
            return (
              <div className="shelf">
                <header>
                  <b>ライブラリ</b>
                  <span className="type-caption" style={{ color: "var(--ink-faint)" }}>
                    サンプル／ワークスペース
                  </span>
                  {searching ? (
                    <span className="side-search" style={{ margin: 0, height: 24 }}>
                      <input defaultValue="鋼" aria-label="ライブラリを検索" />
                    </span>
                  ) : null}
                  {shelfState === "narrow" ? (
                    <span className="type-caption" style={{ color: "var(--ink-muted)", marginLeft: "auto" }}>
                      幅が足りないため下段ドロワーで開きます
                    </span>
                  ) : null}
                </header>
                {shelfState !== "collapsed" && shelfState !== "narrow"
                  ? rows.map((row, index) => (
                      <div key={index} className="shelf-row">
                        {row
                          .filter((name) => !searching || name.includes("マテリアル") || name.includes("テンプレート"))
                          .map((name) => (
                            <button
                              key={`${index}:${name}`}
                              className="shelf-card"
                              aria-pressed={shelfState === "selected" && name === cards[0]}
                              title={shelfState === "selected" ? "選択中 — 適用はドラッグか適用ボタンで" : undefined}
                            >
                              <span className="thumb">{name}</span>
                              <span className="name">{name}</span>
                            </button>
                          ))}
                      </div>
                    ))
                  : null}
              </div>
            );
          })() : null}

          {!isChat ? (
            <InstructionBar
              onSubmit={(text) =>
                submit({ operation: "script.run", parameters: { instruction: text } })
              }
            />
          ) : null}
        </div>
        {hasRail && s.rightOpen ? <RightSidebar render={rail} /> : null}
      </div>
      <CatalogDrawer />
    </section>
  );
}
