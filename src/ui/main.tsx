import { createRoot } from "react-dom/client";
import { App } from "./shell/App";
import "./shared/tokens.css";
import "./shared/app.css";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(<App />);
}
