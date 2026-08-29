# The screen contract (mockup 2)

Every file here implements ONE screen of the design-state catalogue and honours this contract.
The binding rules are `.claude/skills/solvia-ui/SKILL.md` (read it first); this file adds only the
mechanical interface.

## Exports

`<Short>Screen(props: { variant: string })` - the canvas content for every variant of the screen.
`<Short>Rail(props: { tab: string; variant: string })` - the right-rail property content, where the
screen has a rail (home / chat / settings do not).

## Variants

The full variant list, with labels and intents, is `src/ui/shell/catalog.ts` (generated from
mockup 1's own catalogue - do not edit it). Implement every variant of your screen: a variant is a
design state a reviewer deep-links as `#/screen/variant`. Group related variants in the code
(comparison-*, object-*, library-*, split-*) rather than writing 45 disjoint branches.

## What you may touch

Your screen file, plus optionally ONE `<name>.css` beside it (imported from the file, every class
prefixed with your screen's short prefix, colours and sizes ONLY via `var(--token)` from
`src/ui/shared/tokens.css`). Nothing else - no new dependencies, no edits to shared/, state/,
client/, App.tsx, or another screen.

## The shared vocabulary (import, never re-implement)

From `../../shared/...`:
- `QuantityChip {value, unit(null=未宣言), title?}` / `UnitLabel {unit}` / `NumberCell {value|null, missingBecause?}`(a `<td>`)
- `ProvenanceBadge {origin: "declared"|"dataset"|"computed"|"measured"|"reference"}`
- `MissingDataStyle {because}` - the one way absence looks (XC-001)
- `CaseTree`, `VariableRow`, `FieldSelector {fields, value, onChange, disabled?, disabledReason?}`
- `ColourMapControl {value, onChange}` (ids: viridis|plasma|greys)
- `UnresolvedList {items: {what, missing}[], title?}` (XC-090)
- `RunOutcomeTable {units, cases, outcome(unit,case)->{kind,note?}}`
- `ScopeConfirmation {operation, affected, onAccept, onCancel}` (XC-094)
- `ProbeReadout {field, value, unit, origin, location, onHold?}` (INV-023 - location in source words)
- `SplitLayout {panes}` / `ViewportPlaceholder {caseName, fieldLabel?, map?, legendTicks?, reducedNote?, children?}`
- `Outliner {roots, selectedId, onSelect, onToggleVisible?, emptyText?}`
- `NotificationHistory {notices}` / `InstructionBar {onSubmit, ...}` / `ProgressAndCancel {label, detail?, fraction?, onCancel?, cancelNote?}`
- `WorkspaceItemList {kindLabel, items, openId, onOpen, onCreate?}`

From `../../state/session`: `useSession()` (screen, variant, selectedCaseId, resultPosition,
paneCount, cameraSync...), `session.selectCase/moveResultPosition/setPaneCount/navigate`.
From `../../client/operations`: `submit({operation, parameters})` - every action dispatches through
it (INV-006); it logs and returns `{status:"design-state"}`.
From `../../logic/format`: `formatValue(value, digits)`, `formatBytes(bytes)`, `disabledBecause(reason)`.

Shell CSS classes already available (see `src/ui/shared/app.css`): `.prop-section`, `.prop-row`,
`.prop-note`, `.field-input`, `.btn`(+`.primary`/`.ghost`), `.notice`(+`.error`/`.warn`/`.good`),
`.value-table`+`.table-scroll`, `.empty-state`, `.dialog-scrim`/`.dialog`, `.popover`,
`.viewport-pane`, `.playback-overlay`, `.pane-badge`, `.legend`, `.tree-row`, `.shelf-card`.

## Hard rules (from solvia-ui - the ones screens break most)

- Numbers are illustrative but honest: value + unit (or 単位未宣言) + provenance, digits per
  INV-014 (241.7, never 241.6999969482422). Missing is stated absence, never blank or zero.
- Japanese UI text. Disabled controls carry their reason (title or inline note). Every surface has
  its empty / error / loading form where the variant calls for it.
- Strict TS: `noUncheckedIndexedAccess` is on - index access yields `T | undefined`; handle it.
  No unused imports or variables. Do NOT run tsc (siblings are being written concurrently);
  integration typechecks afterwards.
- TS 7 (native strip-types era): keep types simple - unions, literal objects, `as const`. No
  namespaces, no decorators, no enums (use union types).
