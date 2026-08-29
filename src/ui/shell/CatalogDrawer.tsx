/* The design-state catalogue drawer. Not a product surface: mockup 2 is a catalogue of design
 * states, and this drawer is how a reviewer walks all of them. It lists every scenario grouped by
 * screen and deep-links as #/screen/variant, the same contract mockup 1 enforces by test. */
import { useMemo, useState } from "react";
import { session, useSession } from "../state/session";
import { SCENARIOS } from "./catalog";

export function CatalogDrawer() {
  const s = useSession();
  const [open, setOpen] = useState(false);
  const groups = useMemo(() => {
    const byScreen = new Map<string, typeof SCENARIOS[number][]>();
    for (const scenario of SCENARIOS) {
      const list = byScreen.get(scenario.screen) ?? [];
      list.push(scenario);
      byScreen.set(scenario.screen, list);
    }
    return [...byScreen.entries()];
  }, []);

  return (
    <>
      <button className="catalog-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
        設計状態 {SCENARIOS.length} 件 {open ? "▾" : "▴"}
      </button>
      {open ? (
        <div className="catalog-drawer" role="dialog" aria-label="設計状態の一覧">
          <header>
            設計状態のカタログ — 実装の証拠ではありません。#/画面/状態 で直接開けます
          </header>
          <div className="body">
            {groups.map(([screen, scenarios]) => (
              <div key={screen} className="catalog-group">
                <b>{screen}（{scenarios.length}）</b>
                {scenarios.map((scenario) => (
                  <button
                    key={scenario.id}
                    className="catalog-item"
                    aria-current={s.screen === scenario.screen && s.variant === scenario.variant}
                    title={scenario.intent}
                    onClick={() => session.navigate(scenario.screen, scenario.variant)}
                  >
                    <span className="id">{scenario.variant}</span>
                    <span>{scenario.label}</span>
                    <span className="intent">{scenario.intent}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}
