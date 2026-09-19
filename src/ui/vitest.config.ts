/* The interface's tests run under Node, not a browser: the store is the interface's model of the
 * engine and computes nothing, so what it holds after each step is what a screen would render. The
 * timeouts are long because one test starts a real engine (a VTK import on a cold runner) and walks
 * the whole prototype thread against it. */
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["**/*.test.ts"],
    exclude: ["node_modules/**", "dist/**"],
    testTimeout: 60_000,
    hookTimeout: 120_000,
    // One engine per run: the connected test owns a process and a port, and two of it at once would
    // be two engines answering for one store.
    fileParallelism: false,
  },
});
