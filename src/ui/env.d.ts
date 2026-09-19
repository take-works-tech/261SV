/* What the build inlines into the bundle. Vite replaces `import.meta.env.VITE_*` by matching that
 * exact text, so the access has to be written plainly - a cast or a computed key is not replaced and
 * the value silently becomes undefined, which reads as "no engine" rather than as a mistake. */
interface ImportMetaEnv {
  /** The connection file's contents, as JSON. Absent means no engine, which is a mode (XC-257). */
  readonly VITE_ENGINE_CONNECTION?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
