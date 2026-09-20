/* The command list a person reads in the settings (16_application_model §7.13, XC-277): every
 * operation of CT-003 from the generated catalogue, with its class, its parameters, what it answers,
 * and - from the engine - whether this build answers it. Nothing here is written by hand and nothing
 * here decides what an operation does. No React and no transport. */
import { OPERATIONS, OPERATION_FACTS, type Operation } from "../client/generated";

/** What `system.operations` answered, or null where no engine has been asked. */
export type Answering = { readonly registered: readonly string[]; readonly unimplemented: readonly string[] } | null;

export type CommandStatus = "answers" | "unimplemented" | "unknown";

export interface CommandRow {
  operation: Operation;
  namespace: string;
  writes: boolean;
  /** The parameters by name, required first and the optional ones marked, or なし. */
  parameters: string;
  /** The answer's members by name, or — where the answer is a bare acknowledgement. */
  answers: string;
  status: CommandStatus;
}

export interface CommandGroup {
  namespace: string;
  rows: CommandRow[];
}

/** No operation has a key in this build: the keymap is a design state (XC-277). Said once, here. */
export const NO_KEY = "キーなし";

export const STATUS_LABEL: Record<CommandStatus, string> = {
  answers: "この版が答える",
  unimplemented: "実装なし（拒否される）",
  unknown: "接続時に分かる",
};

function statusOf(answering: Answering, operation: Operation): CommandStatus {
  if (!answering) return "unknown";
  if (answering.registered.includes(operation)) return "answers";
  if (answering.unimplemented.includes(operation)) return "unimplemented";
  return "unknown";
}

function describeParameters(required: readonly string[], optional: readonly string[]): string {
  const parts = [...required, ...optional.map((name) => `${name}?`)];
  return parts.length > 0 ? parts.join("、") : "なし";
}

/** Every operation as a row, grouped by its namespace in catalogue order, filtered by a query that
 *  matches the operation's name or one of its parameters. */
export function commandGroups(answering: Answering, query: string): CommandGroup[] {
  const needle = query.trim().toLowerCase();
  const groups = new Map<string, CommandRow[]>();
  for (const operation of OPERATIONS) {
    const facts = OPERATION_FACTS[operation];
    const namespace = operation.split(".")[0] ?? operation;
    const matches =
      needle === "" ||
      operation.toLowerCase().includes(needle) ||
      [...facts.required, ...facts.optional].some((name) => name.toLowerCase().includes(needle));
    if (!matches) continue;
    const rows = groups.get(namespace) ?? [];
    rows.push({
      operation,
      namespace,
      writes: facts.writes,
      parameters: describeParameters(facts.required, facts.optional),
      answers: facts.answers.length > 0 ? facts.answers.join("、") : "—",
      status: statusOf(answering, operation),
    });
    groups.set(namespace, rows);
  }
  return [...groups.entries()].map(([namespace, rows]) => ({ namespace, rows }));
}

/** One sentence on how much of the catalogue this build answers, or that it is not yet known. */
export function describeAnswering(answering: Answering): string {
  if (!answering) return `契約は ${OPERATIONS.length} 操作を挙げます。この版がどれに答えるかは、エンジンに接続すると分かります`;
  return `契約の ${OPERATIONS.length} 操作のうち、この版は ${answering.registered.length} 操作に答え、${answering.unimplemented.length} 操作は実装がなく拒否されます`;
}
