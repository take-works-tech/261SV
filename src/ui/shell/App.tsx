/* The product shell (MOD-009). Composition follows mockup 1 (XC-256): topbar, work toolbar,
 * then the three-column workbench - navigator, centre column with work-area bar, canvas, shelf and
 * instruction bar, and the property rail. Settings and home are application pages: settings
 * composes its own navigation without workspace sidebars (XC-165); chat swaps the navigator for the
 * conversation list and owns its composer (XC-150); network hides the case tree because permission
 * is workspace-wide. */
import { useEffect, useState, type ReactNode } from "react";
import { session, useSession, type ScreenId } from "../state/session";
import { connectionFromEnvironment, engineState, useEngine } from "../state/engine";
import { shellApi } from "../client/shell";
import { EngineLost, EngineRefusal, EngineWarnings, OrphanNotice } from "../shared/EngineStatus";
import { EngineStarting } from "../shared/EngineStarting";
import { InstructionBar } from "../shared/InstructionBar";
import { SubjectBadge } from "../shared/SubjectBadge";
import { MaterialLibraryShelf, type ShelfAsset, type ShelfState } from "../shared/MaterialLibraryShelf";
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

/* Assets drawn as themselves (XC-215). The swatches are token gradients, not images: the shelf is
   chrome, and the one place a real colour map appears is the legend, which is data (XC-256). */
const SHELF_ASSETS: Partial<Record<ScreenId, ShelfAsset[]>> = {
  view: [
    { id: "a-steel", name: "鋼（つや消し）", source: "sample", swatch: "linear-gradient(135deg, var(--g-ink-faint), var(--g-active))" },
    { id: "a-neutral", name: "中間グレー", source: "sample", swatch: "var(--g-raise)" },
    { id: "a-glass", name: "半透明", source: "workspace", swatch: "linear-gradient(135deg, var(--g-active), var(--g-panel))" },
    { id: "a-result", name: "結果マテリアル", source: "sample", swatch: "var(--map-viridis)", newerSampleExists: true },
    { id: "a-studio", name: "スタジオ背景", source: "shared" },
  ],
  graph: [
    { id: "g-line", name: "折れ線（既定）", source: "sample", swatch: "var(--g-raise)" },
    { id: "g-mono", name: "単色スタイル", source: "workspace", swatch: "var(--map-greys)" },
  ],
  report: [
    { id: "r-journal", name: "論文体裁", source: "sample" },
    { id: "r-internal", name: "社内様式", source: "workspace" },
  ],
};

export function App() {
  const [dragging, setDragging] = useState(false);
  const s = useSession();
  const e = useEngine();

  // Inside the desktop shell, the engine's state is the shell's to report (XC-259): every change
  // arrives as a status, and "running" carries the connection the engine wrote. Outside it, a
  // development build may name a connection in its environment. There is no retry loop and no
  // polling in either case: a restart is a thing a person asks for, and a loop that quietly
  // reattaches hides an engine that keeps dying.
  useEffect(() => {
    const shell = shellApi();
    if (!shell) {
      const connection = connectionFromEnvironment();
      if (connection) void engineState.connect(connection);
      else engineState.disconnect();
      return;
    }
    let hadExited = false;
    const apply = (status: { state: string; reason: string | null; exitCode: number | null; signal: string | null; since?: unknown }) => {
      if (status.state === "running") {
        void shell.engine.connection().then((connection) => {
          if (!connection) return;
          // After an exit, what was saved is opened again; the first time, there is nothing to reopen.
          if (hadExited) void engineState.recover(connection);
          else void engineState.connect(connection);
        });
      } else if (status.state === "exited") {
        hadExited = true;
        engineState.engineExited(status);
      } else if (status.state === "starting") {
        engineState.engineStarting(status);
      }
    };
    const unsubscribe = shell.engine.onStatus(apply);
    void shell.engine.status().then(apply);
    // Quitting saves first (XC-259). The shell waits, bounded, for the answer.
    const unsubscribeQuit = shell.app.onWillQuit(() => {
      void engineState.save().finally(() => shell.app.quitReady());
    });
    return () => {
      unsubscribe();
      unsubscribeQuit();
    };
  }, []);

  const canvas = ((): ReactNode => {
    // Under the shell, no screen is shown until the engine answers: the page says the engine is
    // starting, for how long, and why if it failed (XC-304). A lost engine keeps its last screen,
    // labelled; a browser build with no engine keeps the design states it has always shown.
    if (shellApi() && e.reachability.kind !== "reachable" && e.reachability.kind !== "exited") return <EngineStarting />;
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
        <div className="centre-column" style={{ flex: 1, minHeight: 0 }}>
          <EngineRefusal refusal={e.refusal} onDismiss={() => engineState.clearRefusal()} />
          <EngineWarnings warnings={e.warnings} onDismiss={() => engineState.clearWarnings()} />
        <EngineLost lost={e.lost} onDismiss={() => engineState.dismissLost()} />
        <OrphanNotice />
          {canvas}
        </div>
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
    <section
      className="product-shell"
      onDragOver={(event) => {
        if (event.dataTransfer.types.includes("Files")) {
          event.preventDefault();
          if (!dragging) setDragging(true);
        }
      }}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        const shell = shellApi();
        const files = Array.from(event.dataTransfer.files);
        if (!shell) {
          // A browser hands the page a File and never its path, and the engine reads from disk.
          engineState.noteDropWithoutShell(files.map((one) => one.name));
          return;
        }
        void engineState.dropFiles(files.map((one) => shell.files.pathOf(one)));
      }}
    >
      {dragging ? (
        <div className="drop-hint" role="status" aria-live="polite">
          ここに落とすと読み込みます（ワークスペース .svw か、結果ファイル。複数の結果ファイルは、この文書が記録しているものだけをそれぞれのケースへ）。対応可否は読み込む前に形式ごとに示します
        </div>
      ) : null}
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
              {s.screen === "view" || s.screen === "graph" || s.screen === "report" ? <SubjectBadge area={s.screen} /> : null}
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

          <div className="canvas-wrap">
            <EngineRefusal refusal={e.refusal} onDismiss={() => engineState.clearRefusal()} />
            <EngineWarnings warnings={e.warnings} onDismiss={() => engineState.clearWarnings()} />
            <EngineLost lost={e.lost} onDismiss={() => engineState.dismissLost()} />
            {canvas}
          </div>

          {SHELF_SCREENS.includes(s.screen) ? (
            <MaterialLibraryShelf
              title="ライブラリ"
              categories={SHELF_CARDS[s.screen] ?? []}
              activeCategory={(SHELF_CARDS[s.screen] ?? [])[0]}
              assets={SHELF_ASSETS[s.screen] ?? []}
              // The six shelf states are catalogued view variants (mockup 1's library-*). The shelf
              // is shell furniture, so the shell reads the variant; the component owns the states.
              state={
                s.screen === "view" && s.variant.startsWith("library-")
                  ? (s.variant.replace("library-", "") as ShelfState)
                  : "one-row"
              }
              selectedId={(SHELF_ASSETS[s.screen] ?? [])[0]?.id ?? null}
              query={s.variant === "library-searching" ? "鋼" : ""}
              onSelect={(id) => submit({ operation: "library.list", parameters: { kind: "template", scope: "workspace" } })}
            />
          ) : null}

          {!isChat ? (
            <InstructionBar
              onSubmit={(text) =>
                submit({ operation: "script.run", parameters: { scriptText: text, authorisation: { allowDestructive: false } } })
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
