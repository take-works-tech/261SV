/* The top bar (MOD-009): brand, the six menus, the workspace/list switch, and the global actions.
 * Composition follows mockup 1 (XC-256). A destructive command shows キーなし and its confirmation
 * path rather than gaining a single key (XC-193). */
import { useEffect, useRef, useState } from "react";
import { session, useSession } from "../state/session";
import { NotificationHistory, type Notice } from "../shared/NotificationHistory";
import { ScriptView, type ScriptLine } from "../shared/ScriptView";

type MenuItem = { label: string; key?: string; noKeyBecause?: string; disabled?: string };

const MENUS: { name: string; items: MenuItem[] }[] = [
  { name: "ファイル", items: [
    { label: "結果ファイルを読み込む…", key: "Ctrl+O" },
    { label: "ワークスペースを保存", key: "Ctrl+S" },
    { label: "ワークスペースを閉じる", noKeyBecause: "破壊的になり得る操作は単一キーを持ちません" },
  ]},
  { name: "編集", items: [
    { label: "取り消し", key: "Ctrl+Z" },
    { label: "やり直し", key: "Ctrl+Y" },
    { label: "削除", noKeyBecause: "確認を通る操作です" },
  ]},
  { name: "表示", items: [
    { label: "左パネル", key: "Ctrl+B" },
    { label: "右パネル", key: "Ctrl+Alt+B" },
    { label: "画面プリセットへ戻す", key: "Ctrl+0" },
  ]},
  { name: "フィルタ", items: [
    { label: "条件選択（find）…", key: "Ctrl+F" },
    { label: "しきい値…" },
  ]},
  { name: "ツール", items: [
    { label: "パイプラインをドライラン", key: "Ctrl+R" },
    { label: "診断情報を作成…", noKeyBecause: "内容の一覧を見てから作る操作です" },
  ]},
  { name: "ヘルプ", items: [
    { label: "操作一覧", key: "F1" },
    { label: "このビルドについて" },
  ]},
];

const NOTICES: Notice[] = [
  { id: "n1", at: "10:24", severity: "refusal", title: "ネットワーク要求を拒否", detail: "host: api.example.test — 許可がないため送信していません（XC-106）" },
  { id: "n2", at: "10:12", severity: "warning", title: "単位が未宣言", detail: "フィールド stress — 変換は行っていません（XC-003）" },
  { id: "n3", at: "09:58", severity: "info", title: "読み込み完了", detail: "Run 12 — 1,127,844 点" },
];

/* XC-046: every interface action has a written form, and it is the same command surface a script
   would use. These are the last few, as they would read after opening Run 12 and probing it. */
const RECENT: ScriptLine[] = [
  { at: "10:24", operation: "workspace.open", parameters: '"D:/studies/bracket.svw"', outcome: "applied" },
  { at: "10:24", operation: "dataset.load", parameters: '"Run 12"', outcome: "applied" },
  { at: "10:25", operation: "field.declareUnit", parameters: '"stress", "MPa"', outcome: "applied" },
  { at: "10:26", operation: "dataset.probe", parameters: '"stress", node="GlobalNodeId 1003"', outcome: "answered" },
  {
    at: "10:31",
    operation: "report.export",
    parameters: '"強度確認", format="html"',
    outcome: "refused",
    reason: "せん断の単位が未宣言のため（XC-003）",
  },
];

export function Topbar() {
  const s = useSession();
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [showNotices, setShowNotices] = useState(false);
  const [showScript, setShowScript] = useState(false);
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDown = (event: MouseEvent) => {
      if (!barRef.current?.contains(event.target as Node)) {
        setOpenMenu(null);
        setShowNotices(false);
        setShowScript(false);
      }
    };
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, []);

  return (
    <div className="topbar" ref={barRef}>
      <button className="brand" onClick={() => session.navigate("home")} aria-label="ワークスペース一覧へ">
        <span className="brand-mark" aria-hidden>SV</span>
        <b>SOLVIA</b>
        <small>設計状態</small>
      </button>

      <nav className="main-menu" aria-label="メインメニュー">
        {MENUS.map((menu) => (
          <span key={menu.name} style={{ position: "relative" }}>
            <button
              className="menu-trigger"
              aria-expanded={openMenu === menu.name}
              aria-haspopup="menu"
              onClick={() => setOpenMenu(openMenu === menu.name ? null : menu.name)}
            >
              {menu.name}
            </button>
            {openMenu === menu.name ? (
              <div className="menu-pop" role="menu">
                {menu.items.map((item) => (
                  <button
                    key={item.label}
                    className="menu-item"
                    role="menuitem"
                    disabled={item.disabled !== undefined}
                    title={item.disabled}
                    onClick={() => setOpenMenu(null)}
                  >
                    <span>{item.label}</span>
                    {item.key ? <kbd>{item.key}</kbd> : <span className="no-key" title={item.noKeyBecause}>キーなし</span>}
                  </button>
                ))}
              </div>
            ) : null}
          </span>
        ))}
      </nav>

      <div className="top-actions">
        <div className="view-switcher" role="group" aria-label="表示の切り替え">
          <button aria-pressed={s.screen !== "home"} onClick={() => (s.workspaceOpen ? session.navigate("view") : session.openWorkspace())}>
            ワークスペース
          </button>
          <button aria-pressed={s.screen === "home"} onClick={() => session.navigate("home")}>
            一覧
          </button>
        </div>
        <span className="offline-chip" title="ネットワークには何も送っていません（INV-007）。詳細は network 画面">
          <span className="dot" aria-hidden />
          オフライン
        </span>
        <span style={{ position: "relative" }}>
          <button
            className="icon-button"
            aria-pressed={showNotices}
            aria-label="通知履歴"
            title="通知履歴（閉じても記録は残ります）"
            onClick={() => setShowNotices(!showNotices)}
          >
            ◷
          </button>
          {showNotices ? (
            <div className="popover" style={{ right: 0, top: "calc(100% + 6px)" }}>
              <header>通知履歴</header>
              <div className="body">
                <NotificationHistory notices={NOTICES} />
              </div>
            </div>
          ) : null}
        </span>
        <span style={{ position: "relative" }}>
          <button
            className="icon-button"
            aria-pressed={showScript}
            aria-label="操作の記録"
            title="いま行った操作を、同じことをするコマンドとして読む（XC-046）"
            onClick={() => setShowScript(!showScript)}
          >
            {"{ }"}
          </button>
          {showScript ? (
            <div className="popover" style={{ right: 0, top: "calc(100% + 6px)" }}>
              <header>操作の記録</header>
              <div className="body">
                <ScriptView
                  lines={RECENT}
                  onCopy={(text) => void navigator.clipboard?.writeText(text)}
                />
              </div>
            </div>
          ) : null}
        </span>
        <button className="icon-button" aria-label="設定" title="設定" onClick={() => session.navigate("settings")}>
          ⚙
        </button>
      </div>
    </div>
  );
}
