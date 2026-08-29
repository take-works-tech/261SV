/* Conversation drawer (11_ui.md): the one conversation, opened over the canvas.
 *
 * XC-150: the instruction bar, this drawer and the Chat area are three forms of ONE conversation.
 * Opening the drawer moves the composer; it does not fork the thread, and it does not start a
 * second history. That is why the composer is absent from the shell while the drawer is open -
 * two composers on screen would be two conversations to the reader, whatever the model says.
 *
 * A turn shows what was mapped to commands, so the assistant is a caller like any other (INV-006)
 * and what it did is readable rather than inferred.
 */

export type Turn = {
  id: string;
  from: "person" | "assistant";
  text: string;
  /** The commands this turn produced, in the surface's own vocabulary. */
  commands?: string[];
  /** Present when the turn changed nothing, with the reason - never silence. */
  refusedBecause?: string;
};

export function ConversationDrawer(props: {
  turns: Turn[];
  draft: string;
  onDraft: (text: string) => void;
  onSend: () => void;
  onClose: () => void;
  busy?: string;
}) {
  return (
    <aside
      role="complementary"
      aria-label="会話"
      style={{
        position: "absolute",
        top: 0,
        right: 0,
        bottom: 0,
        zIndex: 20,
        width: "min(420px, 60%)",
        display: "flex",
        flexDirection: "column",
        borderLeft: "1px solid var(--line-strong)",
        background: "var(--surface-panel)",
        boxShadow: "var(--shadow-pop)",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 10px",
          borderBottom: "1px solid var(--line)",
        }}
      >
        <b className="type-emphasis" style={{ color: "var(--ink-strong)" }}>
          会話
        </b>
        <span className="type-caption" style={{ color: "var(--ink-faint)" }}>
          指示バー・チャットと同じ一つのスレッドです
        </span>
        <button className="icon-button" style={{ marginLeft: "auto" }} aria-label="閉じる" onClick={props.onClose}>
          ✕
        </button>
      </header>

      <div style={{ flex: 1, minHeight: 0, overflow: "auto", padding: 10, display: "grid", gap: 10 }}>
        {props.turns.length === 0 ? (
          <p className="prop-note" style={{ margin: 0 }}>
            まだやり取りはありません。例：「Run 12 の最大応力のビューを作って」
          </p>
        ) : (
          props.turns.map((turn) => (
            <article key={turn.id} style={{ display: "grid", gap: 4, minWidth: 0 }}>
              <b className="type-caption" style={{ color: "var(--ink-muted)" }}>
                {turn.from === "person" ? "あなた" : "アシスタント"}
              </b>
              <p style={{ margin: 0, fontSize: "var(--text-body)", wordBreak: "break-word" }}>{turn.text}</p>
              {turn.commands && turn.commands.length > 0 ? (
                <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 2 }}>
                  {turn.commands.map((command) => (
                    <li
                      key={command}
                      className="type-caption"
                      style={{
                        minWidth: 0,
                        overflowX: "auto",
                        fontFamily: "var(--family-mono)",
                        color: "var(--ink-muted)",
                        whiteSpace: "pre",
                      }}
                    >
                      {command}
                    </li>
                  ))}
                </ul>
              ) : null}
              {turn.refusedBecause ? (
                <div className="notice error">
                  <b>実行していません</b>
                  <span className="why">{turn.refusedBecause}</span>
                </div>
              ) : null}
            </article>
          ))
        )}
        {props.busy ? (
          <span className="run-chip">
            <span className="spinner" aria-hidden />
            {props.busy}
          </span>
        ) : null}
      </div>

      <form
        className="instruction-bar"
        onSubmit={(event) => {
          event.preventDefault();
          if (props.draft.trim() !== "") props.onSend();
        }}
      >
        <input
          value={props.draft}
          onChange={(event) => props.onDraft(event.target.value)}
          placeholder="言葉で指示"
          aria-label="アシスタントへの指示"
        />
        <button className="btn" type="submit" disabled={props.draft.trim() === ""}>
          送る
        </button>
      </form>
    </aside>
  );
}
