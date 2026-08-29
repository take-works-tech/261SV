/* Simulation area (design states).
 *
 * A saved @Simulation is one declarative flow grouping the run conditions of one or more external-
 * solver executions - not one row per solver process, and never the result Case (GL-043, XC-154).
 * Execution is a later release: this product never solves, and r1 never claims a result will exist
 * (XC-091). The four catalogued states:
 *   default     - a saved flow, node cards on a spine, resolution state per node
 *   empty       - nothing saved yet; the creation entry
 *   unavailable - the area's announcement: r1 runs no solver, pipeline import is the alternative
 *   unresolved  - undeclared variable and unconnected adapter named; run refused, definition kept
 *
 * CT-003 defines no simulation.* operation yet: the Simulation is owned by the Workspace (XC-154),
 * so design-state saves dispatch as workspace.save with the item named in the parameters.
 */
import type { ReactNode } from "react";
import { session } from "../../state/session";
import { submit } from "../../client/operations";
import { QuantityChip } from "../../shared/QuantityChip";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { MissingDataStyle } from "../../shared/MissingDataStyle";
import { UnresolvedList } from "../../shared/UnresolvedList";
import { disabledBecause, formatBytes } from "../../logic/format";
import "./SimulationScreen.css";

type NodeState = "resolved" | "unresolved" | "later";

const NODE_STATE_LABEL: Record<NodeState, string> = {
  resolved: "解決済み",
  unresolved: "未解決",
  later: "後続リリース",
};

function StateChip({ state }: { state: NodeState }) {
  const tone = state === "resolved" ? "si-chip good" : state === "unresolved" ? "si-chip error" : "si-chip";
  return <span className={tone}>{NODE_STATE_LABEL[state]}</span>;
}

function Row(props: { label: string; note?: string; children: ReactNode }) {
  return (
    <div className="si-row">
      <span className="si-row-label" title={props.label}>{props.label}</span>
      <span className="si-val">
        {props.children}
        {props.note ? <span className="si-note">{props.note}</span> : null}
      </span>
    </div>
  );
}

function NodeCard(props: { index: number; kind: string; name: string; state: NodeState; children: ReactNode }) {
  return (
    <li className={`si-node is-${props.state}`}>
      <span className="si-node-rail" aria-hidden>
        <span className="si-link pre" />
        <span className="si-node-index">{props.index}</span>
        <span className="si-link post" />
      </span>
      <section className="si-card" aria-label={`${props.name}（${NODE_STATE_LABEL[props.state]}）`}>
        <header>
          <span className="si-kind">{props.kind}</span>
          <b title={props.name}>{props.name}</b>
          <StateChip state={props.state} />
        </header>
        <div className="si-body">{props.children}</div>
      </section>
    </li>
  );
}

/* The two flow states share one composition (mockup 1's: notice, then the steps, then the trust
 * note); what differs is which nodes resolve and why the run button is disabled. */
function FlowCanvas({ unresolved }: { unresolved: boolean }) {
  const solverExe = "C:\\solvers\\CalculiX\\ccx_2.21.exe";
  const runDisabled = unresolved
    ? disabledBecause("未解決が2件（変数「設計許容応力」・ソルバーアダプター）残っています")
    : disabledBecause("r1では外部ソルバーを実行しません（XC-091）");

  return (
    <div className="si-canvas">
      <div className="si-column">
        <div className="si-flow-head">
          <h2 title="基準シミュレーション">基準シミュレーション</h2>
          <span className="si-flow-meta">改訂 3・保存 2026-08-27 18:42</span>
          <span className="si-flow-actions">
            <button
              className="btn"
              onClick={() => submit({ operation: "workspace.save", parameters: { item: "simulation", name: "基準シミュレーション", revision: 3 } })}
            >
              定義を保存
            </button>
            <button className="btn primary" {...runDisabled}>実行</button>
          </span>
        </div>

        {unresolved ? (
          <>
            <div className="notice error" role="alert">
              <b>実行条件を解決できません — 実行を拒否しました</b>
              <span className="why">
                条件が揃うまで実行は始まりません。保存済みの定義は変更されず、代替値や前回値で補うことはありません（XC-001）。
              </span>
            </div>
            <UnresolvedList
              title="未解決の項目（2件）"
              items={[
                { what: "材料条件 → 変数「設計許容応力」", missing: "変数が未宣言。左の変数一覧で宣言するまで束縛できません" },
                { what: "ソルバー呼び出し → アダプター", missing: "未接続。右のソルバタブで実行ファイルとバージョンを宣言します" },
              ]}
            />
          </>
        ) : (
          <div className="notice">
            <b>定義は保存できます — 実行は後続リリース</b>
            <span className="why">
              この保存フローは実行条件をまとめたものです。r1では外部ソルバーを呼び出さず、結果ケースを作成しません（XC-091）。
            </span>
          </div>
        )}

        <ol className="si-nodes">
          <NodeCard index={1} kind="入力" name="メッシュ入力" state="resolved">
            <Row label="参照" note="参照は利用者の選択です。ケースを削除すると未解決になります">
              <span className="si-text">ケース「Run 12（基準）」</span>
              <ProvenanceBadge origin="declared" />
            </Row>
            <Row label="解決先">
              <span className="si-text si-mono" title="run12_mesh.inp">run12_mesh.inp</span>
              <span className="si-text">{formatBytes(2634752)}</span>
              <ProvenanceBadge origin="dataset" />
            </Row>
            <Row label="規模">
              <span className="si-text">節点 214,036・要素 198,552</span>
              <ProvenanceBadge origin="dataset" />
            </Row>
          </NodeCard>

          <NodeCard index={2} kind="条件" name="材料条件" state={unresolved ? "unresolved" : "resolved"}>
            {unresolved ? (
              <Row label="設計許容応力" note="代替値・前回値は使いません。宣言されるまでこの行は値なしのままです（XC-001）">
                <MissingDataStyle because="変数「設計許容応力」が未宣言" />
              </Row>
            ) : (
              <Row label="設計許容応力" note="変数「設計許容応力」から束縛">
                <QuantityChip value="235" unit="MPa" />
                <ProvenanceBadge origin="declared" />
              </Row>
            )}
            <Row label="ヤング率">
              <QuantityChip value="206" unit="GPa" />
              <ProvenanceBadge origin="declared" />
            </Row>
            <Row label="ポアソン比">
              <QuantityChip value="0.30" unit="無次元" />
              <ProvenanceBadge origin="declared" />
            </Row>
          </NodeCard>

          <NodeCard index={3} kind="条件" name="境界条件" state="resolved">
            <Row label="固定面">
              <span className="si-text">パート「取付フランジ」・完全拘束</span>
              <ProvenanceBadge origin="declared" />
            </Row>
            <Row label="荷重面">
              <span className="si-text">パート「荷重リブ」</span>
              <ProvenanceBadge origin="declared" />
            </Row>
            <Row label="荷重" note="面法線方向・等分布">
              <QuantityChip value="12.5" unit="kN" />
              <ProvenanceBadge origin="declared" />
            </Row>
          </NodeCard>

          <NodeCard index={4} kind="実行" name="ソルバー呼び出し" state={unresolved ? "unresolved" : "later"}>
            {unresolved ? (
              <Row label="アダプター" note="右のソルバタブで宣言します。接続されるまでフロー全体が実行を解決しません">
                <MissingDataStyle because="アダプター未接続" />
              </Row>
            ) : (
              <>
                <Row label="アダプター">
                  <span className="si-text">CalculiX（ccx）</span>
                  <ProvenanceBadge origin="declared" />
                </Row>
                <Row label="実行ファイル">
                  <span className="si-text si-mono" title={solverExe}>{solverExe}</span>
                  <ProvenanceBadge origin="declared" />
                </Row>
                <Row label="呼び出し" note="定義のみを保存します。実行と結果ケースの作成は後続リリースです">
                  <span className="si-text">r1では実行しません（XC-091）</span>
                </Row>
              </>
            )}
          </NodeCard>
        </ol>

        <p className="si-trust">
          <span aria-hidden>※</span>
          このフローは1回以上の外部ソルバー実行の条件をまとめた1件の保存対象です。ソルバープロセス1件につき1行ではありません（XC-154）。
        </p>
      </div>
    </div>
  );
}

export function SimulationScreen(props: { variant: string }) {
  if (props.variant === "empty") {
    return (
      <div className="empty-state">
        <h2>保存されたシミュレーションがありません</h2>
        <p>
          シミュレーションは、1回以上の外部ソルバー実行の条件をまとめて保存するフローです。
          r1では定義の保存と編集までを行い、実行と結果ケースの作成は行いません（XC-091）。
        </p>
        <div className="actions">
          <button
            className="btn primary"
            onClick={() => submit({ operation: "workspace.save", parameters: { item: "simulation", action: "create" } })}
          >
            ＋ 新規シミュレーション
          </button>
          <button className="btn ghost" onClick={() => session.navigate("pipeline")}>
            パイプライン取込を開く
          </button>
        </div>
      </div>
    );
  }

  if (props.variant === "unavailable") {
    return (
      <div className="empty-state">
        <span className="si-eyebrow">後続リリース</span>
        <h2>シミュレーション実行はr1に含まれません</h2>
        <p>
          この製品自体は解を計算せず、後続リリースで外部ソルバーを駆動します（XC-091）。
          既存ソルバーの結果はパイプライン取込で読み込み、ビュー・グラフ・レポートを作成できます。
          定義の保存と編集は現在も可能です。
        </p>
        <div className="actions">
          <button className="btn primary" onClick={() => session.navigate("pipeline")}>
            パイプライン取込を開く
          </button>
          <button className="btn ghost" onClick={() => session.navigate("simulation")}>
            定義を編集
          </button>
        </div>
      </div>
    );
  }

  // The baseline (XC-207): an unknown variant lands on the saved flow.
  return <FlowCanvas unresolved={props.variant === "unresolved"} />;
}

/* The rail's one tab: ソルバ. Every value here is a declaration by the user - the product never
 * inspects, probes or runs the executable, so nothing on this panel is detected (the same
 * discipline as units: declared or absent, never inferred, XC-003). */
export function SimulationRail(props: { tab: string; variant: string }) {
  if (props.variant === "empty") {
    return (
      <div className="prop-section">
        <h3>ソルバ</h3>
        <p className="prop-note">
          シミュレーションが未作成です。フローを作成すると、ソルバーアダプターの宣言がここに表示されます。
        </p>
      </div>
    );
  }

  if (props.variant === "unavailable") {
    return (
      <div className="prop-section">
        <h3>ソルバ</h3>
        <p className="prop-note">
          r1では外部ソルバーを実行しません（XC-091）。宣言済みの定義は保持され、後続リリースでそのまま使えます。
        </p>
        <p className="prop-note">
          既存ソルバーの結果を読み込むにはパイプライン取込を使います。
        </p>
        <div className="prop-row" style={{ marginTop: 8 }}>
          <label htmlFor="si-rail-to-pipeline">代替</label>
          <button id="si-rail-to-pipeline" className="btn" onClick={() => session.navigate("pipeline")}>
            パイプライン取込へ
          </button>
        </div>
      </div>
    );
  }

  const unresolved = props.variant === "unresolved";
  const declare = (field: string) =>
    submit({ operation: "workspace.save", parameters: { item: "simulation", field } });
  // The badge travels with a value (INV-013): an undeclared field carries no origin to show.
  const declaredBadge = unresolved ? null : <ProvenanceBadge origin="declared" />;

  // 単一タブの画面: RightSidebar は "solver" を渡す。未知のタブ名でも同じ内容が正しい内容になる。
  // key: 変種を切り替えたら宣言欄を初期値へ戻す（defaultValue はマウント時のみ読まれるため）。
  return (
    <div key={props.variant} data-rail-tab={props.tab}>
      <div className="prop-section">
        <h3>ソルバーアダプター</h3>
        <div className="prop-row">
          <label htmlFor="si-adapter">アダプター</label>
          <span className="si-rail-field">
            <select
              id="si-adapter"
              className="field-input"
              defaultValue={unresolved ? "none" : "ccx"}
              onChange={() => declare("adapter")}
            >
              <option value="none">未接続</option>
              <option value="ccx">CalculiX（ccx）</option>
            </select>
            {declaredBadge}
          </span>
        </div>
        <div className="prop-row">
          <label htmlFor="si-exe">実行ファイル</label>
          <span className="si-rail-field">
            <input
              id="si-exe"
              className="field-input si-mono"
              defaultValue={unresolved ? "" : "C:\\solvers\\CalculiX\\ccx_2.21.exe"}
              placeholder="未宣言"
              title={unresolved ? "未宣言" : "C:\\solvers\\CalculiX\\ccx_2.21.exe"}
              onBlur={() => declare("executable")}
            />
            {declaredBadge}
          </span>
        </div>
        <div className="prop-row">
          <label htmlFor="si-version">バージョン</label>
          <span className="si-rail-field">
            <input
              id="si-version"
              className="field-input"
              defaultValue={unresolved ? "" : "2.21"}
              placeholder="未宣言"
              onBlur={() => declare("version")}
            />
            {declaredBadge}
          </span>
        </div>
        {unresolved ? (
          <p className="prop-note">
            <MissingDataStyle because="アダプター未接続" />
            {" "}実行ファイルとバージョンが未宣言のため、このフローは実行を解決できません。
          </p>
        ) : (
          <p className="prop-note">
            値はいずれも利用者の宣言であり、検出ではありません。本製品は実行ファイルの存在やバージョンを確認していません。
          </p>
        )}
      </div>

      <div className="prop-section">
        <h3>ライセンス</h3>
        <div className="prop-row">
          <label htmlFor="si-license">形態</label>
          <span className="si-rail-field">
            <input
              id="si-license"
              className="field-input"
              defaultValue={unresolved ? "" : "サイトライセンス（5席）"}
              placeholder="未宣言"
              onBlur={() => declare("license")}
            />
            {declaredBadge}
          </span>
        </div>
        <div className="prop-row">
          <label htmlFor="si-license-date">確認日</label>
          <span className="si-rail-field">
            <input
              id="si-license-date"
              className="field-input"
              defaultValue={unresolved ? "" : "2026-08-12"}
              placeholder="未宣言"
              onBlur={() => declare("licenseChecked")}
            />
            {declaredBadge}
          </span>
        </div>
        <p className="prop-note">
          ライセンスは照会・検証しません。宣言の記録として定義と一緒に保存されます。
        </p>
      </div>

      <div className="prop-section">
        <h3>検証</h3>
        <button className="btn" {...disabledBecause("r1では外部ソルバーを検査・実行しません（XC-091）")}>
          接続確認
        </button>
        <p className="prop-note">無効：r1では外部ソルバーを検査・実行しません（XC-091）。</p>
      </div>
    </div>
  );
}
