/* Instruction bar (11_ui.md): the one conversation in its compact form (XC-150). What is typed here
 * and what is typed in the chat area are the same thread - the composer moves, the conversation
 * does not fork. Absent while the drawer owns the composer. */
import { useState } from "react";

export function InstructionBar(props: {
  placeholder?: string;
  onSubmit: (text: string) => void;
  disabled?: boolean;
  disabledReason?: string;
}) {
  const [draft, setDraft] = useState("");
  return (
    <form
      className="instruction-bar"
      onSubmit={(event) => {
        event.preventDefault();
        if (draft.trim() === "") return;
        props.onSubmit(draft.trim());
        setDraft("");
      }}
    >
      <input
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        placeholder={props.placeholder ?? "言葉で指示（例：最大応力のビューを作って）"}
        aria-label="アシスタントへの指示"
        disabled={props.disabled}
        title={props.disabled ? props.disabledReason : undefined}
      />
      <button className="btn" type="submit" disabled={props.disabled || draft.trim() === ""}>
        送る
      </button>
    </form>
  );
}
