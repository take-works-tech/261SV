import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The production interface builds to static files an Electron shell (or a dev server) hosts.
// No network is reached at runtime: fonts and assets ship with the build (INV-007).
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "dist", target: "es2022" },
});
