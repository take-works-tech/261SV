# UI mockup guidance

- This is a Next.js 16, React 19, TypeScript, Tailwind CSS, React Three Fiber, and Three.js application.
- This is a design catalogue, not evidence that product behaviour is implemented.
- `../../specs/11_ui.md` owns the screen structure; `lib/screen-catalog.json` owns the mockup scenario list.
- Every scenario must remain deep-linkable as `?screen=<screen>&variant=<variant>` and covered by `tests/test_ui_mockup_catalog.py`.
- Never invent analysis values, units, provenance, file metadata, or solver outcomes. Use explicit placeholders and label mock geometry.
- Preserve the existing workspace-list and engineering-view visual language unless the user explicitly requests a redesign.
- Keep 3D overlays readable and non-overlapping across supported viewport sizes.
- Run `npm.cmd run lint`, `npm.cmd run typecheck`, and `npm.cmd run build` after relevant changes.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
