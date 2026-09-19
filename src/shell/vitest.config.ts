/* The shell's tests run under plain Node: `engine-process.ts` has no Electron in it, which is the
 * point - starting, crashing and stopping a real engine is checked without a window. */
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["*.test.ts"],
    exclude: ["node_modules/**", "dist/**", "dist-preload/**"],
    testTimeout: 60_000,
    hookTimeout: 120_000,
    fileParallelism: false,
  },
});
