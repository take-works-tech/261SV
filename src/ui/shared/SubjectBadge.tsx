/* The subject badge of an artefact area's header (11_ui.md "Which cases an area is showing",
 * 16_application_model §3 `header`, XC-292): which case the area shows, in the document's own words,
 * and why - the item's own binding, a pin, or the tree - with the one control that pins the area to
 * that case or lets it follow the tree again. With an engine the store answers; without one the design
 * states show the fixture tree's selection, and the topbar says which mode this is. */
import { engineState, useEngine } from "../state/engine";
import { session, useSession } from "../state/session";
import { areaSubject, AREA_LABEL, type Area, type AreaSubject } from "../logic/subject";
import { FIXTURE_CASES } from "./fixtureCases";

export function SubjectBadge({ area }: { area: Area }) {
  const s = useSession();
  const e = useEngine();
  const live = e.reachability.kind === "reachable" && e.workspaceId !== null;
  const subject: AreaSubject = live ? engineState.subjectOf(area) : areaSubject(s.subjects[area], s.selectedCaseId, null, FIXTURE_CASES);
  const bound = subject.source === "item";
  const pinned = subject.source === "pinned";
  const pinTitle = bound
    ? subject.because
    : subject.caseId
      ? "この領域をいまのケースに固定します。ツリーで別のケースを選んでも、この領域は変わりません"
      : "固定するケースがありません";
  return (
    <span className="subject-badge" role="group" aria-label={`${AREA_LABEL[area]}の対象ケース`}>
      <span className="subject-badge-case" title={`${subject.label}・${subject.because}`}>
        <b>{subject.label}</b>
        <span>・{subject.because}</span>
      </span>
      {pinned ? (
        <button type="button" className="btn ghost" onClick={() => session.followArea(area)} title="固定を外し、ツリーの選択に追従します">
          追従に戻す
        </button>
      ) : (
        <button
          type="button"
          className="btn ghost"
          disabled={bound || subject.caseId === null}
          title={pinTitle}
          onClick={() => (subject.caseId ? session.pinArea(area, subject.caseId) : undefined)}
        >
          固定
        </button>
      )}
    </span>
  );
}
