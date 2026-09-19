/* MOD-017: typed calls to the engine, the transport under them, and the failure of the transport
 * itself. Nothing else - no retry policy, no caching, no interpretation of a result. Each of those
 * is a decision some layer above should be making visibly.
 *
 * The wire is CT-003's envelope over HTTP on loopback with a per-session token (XC-258). No module
 * above `client` knows that: the desktop build reaches a local process and the hosted build reaches
 * a remote one, and the moment a screen knows which, the two products start to diverge.
 *
 * Two failures are kept apart, because a caller does different things about them:
 *   - the **engine answered** - applied, answered, refused or failed. A refusal is an answer. It
 *     arrives as a `Response` and carries its reason.
 *   - the **transport failed** - nothing is listening, the token is wrong, the machine said no.
 *     That throws `TransportFailure`, because there is no answer to read.
 */

import { OPERATIONS, PROTOCOL_VERSION } from "./generated";
import type { Operation, Parameters, Results } from "./generated";

export { OPERATIONS, PROTOCOL_VERSION };
export type { Operation, Parameters, Results };

import type { Connection } from "./shell";

export type { Connection };

/** CT-003's four statuses. `answered` is what a read returns: it applied nothing. */
export type Status = "applied" | "answered" | "refused" | "failed";

/** A refusal's reason on the wire: a stable identifier a caller matches on, and a message for a
 *  person. The identifier is what a support conversation quotes (CT-003, XC-020). */
export interface Reason {
  readonly id: string;
  readonly message: string;
  readonly operation: string;
}

export interface Response<O extends Operation> {
  readonly status: Status;
  readonly changed?: readonly string[];
  readonly effectSummary?: string;
  readonly reason?: string | Reason;
  readonly undoId?: string;
  readonly result?: Results[O];
  readonly warnings?: readonly string[];
}

export interface Authorisation {
  readonly allowDestructive?: boolean;
  readonly allowOverwrite?: boolean;
  readonly allowNetwork?: boolean;
}

export interface Options {
  readonly targets?: readonly string[];
  readonly groupId?: string;
  readonly authorisation?: Authorisation;
  readonly dryRun?: boolean;
  readonly signal?: AbortSignal;
}

/** The transport itself failed: nothing answered, so there is nothing to read. Distinct from a
 *  refusal, which is an answer and arrives as a `Response`. */
export class TransportFailure extends Error {
  constructor(
    message: string,
    override readonly cause?: unknown,
  ) {
    super(message);
    this.name = "TransportFailure";
  }
}

const TOKEN_HEADER = "X-Solvia-Token";

export class Engine {
  constructor(private readonly connection: Connection) {}

  get baseUrl(): string {
    return `http://${this.connection.host}:${this.connection.port}`;
  }

  /** Submit one command and return what the engine answered.
   *
   * Typed both ways: the parameters are the contract's for that operation, and the result is the
   * contract's for that operation. A screen cannot call `dataset.probe` without a `fieldName`,
   * because the contract says it takes one and this signature is generated from the contract.
   */
  async submit<O extends Operation>(
    operation: O,
    parameters: Parameters[O],
    options: Options = {},
  ): Promise<Response<O>> {
    const body: Record<string, unknown> = {
      protocol: PROTOCOL_VERSION,
      operation,
      parameters,
    };
    if (options.targets?.length) body.targets = options.targets;
    if (options.groupId) body.groupId = options.groupId;
    if (options.authorisation) body.authorisation = options.authorisation;
    if (options.dryRun) body.dryRun = true;

    let answer: globalThis.Response;
    try {
      answer = await fetch(`${this.baseUrl}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json", [TOKEN_HEADER]: this.connection.token },
        body: JSON.stringify(body),
        signal: options.signal,
      });
    } catch (cause) {
      throw new TransportFailure(
        `エンジンに届きませんでした（${this.baseUrl}）。起動しているか確認してください`,
        cause,
      );
    }
    let payload: unknown;
    try {
      payload = await answer.json();
    } catch (cause) {
      throw new TransportFailure(
        `エンジンの応答を読めません（HTTP ${answer.status}）`,
        cause,
      );
    }
    if (!isResponse(payload)) {
      throw new TransportFailure(`エンジンの応答が CT-003 の形ではありません（HTTP ${answer.status}）`);
    }
    return payload as Response<O>;
  }

  /** Fetch the bytes an answer named. Geometry and images never travel in a response body
   *  (CT-003 "Large payloads"), so a handle is how a picture reaches the screen. */
  async handle(id: string, options: { signal?: AbortSignal } = {}): Promise<Blob> {
    let answer: globalThis.Response;
    try {
      answer = await fetch(`${this.baseUrl}/handle/${encodeURIComponent(id)}`, {
        headers: { [TOKEN_HEADER]: this.connection.token },
        signal: options.signal,
      });
    } catch (cause) {
      throw new TransportFailure(`ハンドル '${id}' を取りに行けませんでした`, cause);
    }
    if (!answer.ok) {
      // An expired handle is a refusal, never a stale answer (CT-003). It is a transport-level
      // failure here because there is no command result to carry it in.
      throw new TransportFailure(`ハンドル '${id}' は取得できません（HTTP ${answer.status}）`);
    }
    return answer.blob();
  }

  /** Whether the engine is up and speaks a version this build knows. The one call that needs no
   *  token: a shell that cannot yet prove who it is still has to be able to ask. */
  async health(options: { signal?: AbortSignal } = {}): Promise<{ protocols: string[] }> {
    try {
      const answer = await fetch(`${this.baseUrl}/health`, { signal: options.signal });
      return (await answer.json()) as { protocols: string[] };
    } catch (cause) {
      throw new TransportFailure(`エンジンが応答しません（${this.baseUrl}）`, cause);
    }
  }
}

function isResponse(payload: unknown): payload is Response<Operation> {
  if (typeof payload !== "object" || payload === null) return false;
  const status = (payload as { status?: unknown }).status;
  return status === "applied" || status === "answered" || status === "refused" || status === "failed";
}

/** The reason as a sentence, whichever shape it arrived in. A refusal from the surface is a string;
 *  one from the transport is CT-003's object. Both are read by the same person. */
export function reasonText(reason: string | Reason | undefined): string {
  if (reason === undefined) return "";
  return typeof reason === "string" ? reason : reason.message;
}
