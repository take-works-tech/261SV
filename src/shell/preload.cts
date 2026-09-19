/* The bridge, renderer side (E-199 item 20).
 *
 * Exposes `window.solvia` with the shape `src/ui/client/shell.ts` declares - and only that. No raw
 * `ipcRenderer`, no channel names a page could invent, no Node. Each function forwards one named
 * request and returns what main answered; the status listener receives the status object and
 * nothing of the event it arrived in.
 *
 * A `.cts` file, so it compiles to CommonJS (`preload.cjs`): the renderer is sandboxed, and
 * "sandboxed preload scripts are run as plain JavaScript without an ESM context" (E-201).
 */
import { contextBridge, ipcRenderer, type IpcRendererEvent } from "electron";

import type { EngineProcessStatus, ShellApi } from "../ui/client/shell.js" with { "resolution-mode": "import" };

const api: ShellApi = {
  kind: "electron",
  notices: () => ipcRenderer.invoke("notices"),
  engine: {
    connection: () => ipcRenderer.invoke("engine:connection"),
    status: () => ipcRenderer.invoke("engine:status"),
    onStatus: (listener: (status: EngineProcessStatus) => void) => {
      const handler = (_event: IpcRendererEvent, status: EngineProcessStatus) => listener(status);
      ipcRenderer.on("engine:status", handler);
      return () => {
        ipcRenderer.removeListener("engine:status", handler);
      };
    },
    restart: () => ipcRenderer.invoke("engine:restart"),
  },
  app: {
    onWillQuit: (listener: () => void) => {
      const handler = () => listener();
      ipcRenderer.on("app:will-quit", handler);
      return () => {
        ipcRenderer.removeListener("app:will-quit", handler);
      };
    },
    quitReady: () => {
      ipcRenderer.send("app:quit-ready");
    },
  },
  dialog: {
    openWorkspace: () => ipcRenderer.invoke("dialog:openWorkspace"),
    openResult: () => ipcRenderer.invoke("dialog:openResult"),
    saveReport: (suggestedName: string) => ipcRenderer.invoke("dialog:saveReport", suggestedName),
  },
};

contextBridge.exposeInMainWorld("solvia", api);
