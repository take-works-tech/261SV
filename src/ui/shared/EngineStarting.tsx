/* The page while the engine starts (XC-304): what the interface is waiting for, for how long, and
 * why it can take a while - and, if the start failed, the reason and a way to start again. Shown in
 * place of every screen under the shell until the engine answers, so a design state is never on
 * screen beside a live engine, not even for the first second of a launch. */
import { useEffect, useState } from "react";

import { shellApi } from "../client/shell";
import { describeStartup } from "../logic/startup";
import { useEngine } from "../state/engine";

/** When this page's code loaded: the clock the wait is counted on, because the page cannot see the
 *  shell's own start and the shell's notes hold that number (spike/measure_launch.py). */
const LOADED_AT = Date.now();

export function EngineStarting() {
  const e = useEngine();
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const words = describeStartup(e.reachability, (now - LOADED_AT) / 1000);
  const shell = shellApi();
  return (
    <div className={`engine-starting${words.failed ? " failed" : ""}`} role="status" aria-live="polite">
      <h2>{words.title}</h2>
      <p>{words.detail}</p>
      {words.failed && shell ? (
        <button type="button" className="btn primary" onClick={() => void shell.engine.restart()}>
          再起動
        </button>
      ) : null}
    </div>
  );
}
