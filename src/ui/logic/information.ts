/* What the loaded dataset holds, as the information area shows it (MOD-015, XC-273): read from the
 * engine's own answers - dataset.load, dataset.describe, dataset.parts - and nothing inferred. Where
 * the contract does not carry a fact the area's design lists, the fact is named as not answered, never
 * filled with a plausible value (XC-001). No React and no transport here. */
import type { EngineState, FieldSummary } from "../state/engine";
import { currentStep } from "./resultPosition";

export interface FileFacts {
  name: string;
  path: string | null;
  /** The file's extension, which is all the engine says about the format's name. */
  format: string;
  supportLevel: string | null;
  supportLabel: string;
  supportNote: string;
  gaps: readonly string[];
}

export interface StructureFacts {
  points: number;
  cells: number;
  bounds: { axis: "X" | "Y" | "Z"; min: number; max: number }[] | null;
  partial: boolean;
}

export interface PartFacts {
  name: string;
  present: boolean;
  /** Why the part is absent, in the reader's words, or null (XC-272). */
  reason: string | null;
  points: number;
  cells: number;
}

export interface FieldFacts {
  name: string;
  association: FieldSummary["association"];
  associationLabel: string;
  unit: string | null;
}

export interface AxisFacts {
  kind: string;
  label: string;
  positions: number | null;
  first: number | null;
  last: number | null;
  unit: string | null;
  /** The step the view is at, as a sentence, where the case has more than one (view/AC-032). */
  current: string | null;
}

export interface NotAnswered {
  what: string;
  because: string;
}

export interface InformationView {
  file: FileFacts;
  structure: StructureFacts | null;
  parts: PartFacts[];
  fields: FieldFacts[];
  axis: AxisFacts | null;
  notAnswered: NotAnswered[];
}

const ASSOCIATION_LABEL: Record<string, string> = {
  point: "点",
  cell: "要素",
  integrationPoint: "積分点",
  field: "場（値の集合）",
};

const AXIS_LABEL: Record<string, string> = {
  time: "時刻",
  mode: "モード",
  frequency: "周波数",
  undeclared: "軸の種類は宣言されていません",
  none: "結果軸なし",
};

const LEVEL_LABEL: Record<string, { label: string; note: string }> = {
  verified: { label: "検証済み", note: "この製品の回帰テストが実ファイルを開き、値を検証しています（XC-049）" },
  offered: { label: "提供（offered）", note: "ツールキットのリーダーで開きます。リーダー既知の欠落は取込時に名指しされます（XC-049）" },
  absent: { label: "未対応", note: "この版にこの形式のリーダーはありません" },
};

/** What the area's design lists and CT-003 does not carry. Named, so the screen says it rather than
 *  showing a fixture's value where a fact should be. */
export const NOT_ANSWERED: readonly NotAnswered[] = [
  { what: "リーダーとその版", because: "CT-003 は読み手の名前と版を運びません。対応レベル（XC-049）だけを答えます" },
  { what: "要素種別の内訳", because: "dataset.describe は要素の総数を答え、種別ごとの数は運びません" },
  { what: "元ファイルのチェックサム", because: "契約にありません。文書は元ファイルの大きさと更新時刻を記録します（CT-001）" },
  { what: "座標系の宣言と解決", because: "読み手は正準フレームへ変換しますが、その記録は CT-003 の答えに載っていません" },
  { what: "取込時刻", because: "操作の記録（history.list）が持ち、ここには運びません" },
  { what: "フィールドの成分数・実測範囲・欠損値数", because: "field.statistics が場ごとに答えます。ここでは宣言単位と関連だけを示します" },
];

/** The information view of what is loaded, or null where nothing is. */
export function informationOf(state: EngineState): InformationView | null {
  if (!state.datasetId || !state.sourceName) return null;
  const extension = state.sourceName.includes(".") ? `.${state.sourceName.split(".").pop() ?? ""}` : "";
  const level = state.supportLevel ? LEVEL_LABEL[state.supportLevel] : undefined;
  const described = state.described;
  const axis = described?.resultAxis ?? null;
  const positions = axis?.positions ?? null;
  return {
    file: {
      name: state.sourceName,
      path: state.caseId ? (state.loaded[state.caseId]?.filePath ?? null) : null,
      format: extension,
      supportLevel: state.supportLevel,
      supportLabel: level?.label ?? state.supportLevel ?? "不明",
      supportNote: level?.note ?? "対応レベルはエンジンの答えにありませんでした",
      gaps: state.gaps,
    },
    structure: described
      ? {
          points: described.pointCount,
          cells: described.cellCount,
          bounds:
            described.boundsM && described.boundsM.minM.length >= 3 && described.boundsM.maxM.length >= 3
              ? (["X", "Y", "Z"] as const).map((axisName, index) => ({
                  axis: axisName,
                  min: described.boundsM.minM[index] ?? Number.NaN,
                  max: described.boundsM.maxM[index] ?? Number.NaN,
                }))
              : null,
          partial: described.partial,
        }
      : null,
    parts: (state.parts ?? []).map((part) => ({
      name: part.name,
      present: part.type !== "absent",
      reason: part.reason ?? null,
      points: part.pointCount,
      cells: part.cellCount,
    })),
    fields: state.fields.map((field) => ({
      name: field.name,
      association: field.association,
      associationLabel: ASSOCIATION_LABEL[field.association] ?? field.association,
      unit: field.unit,
    })),
    axis: axis
      ? {
          kind: axis.kind,
          label: AXIS_LABEL[axis.kind] ?? axis.kind,
          positions: axis.count ?? positions?.length ?? null,
          first: positions && positions.length > 0 ? positions[0] ?? null : null,
          last: positions && positions.length > 0 ? positions[positions.length - 1] ?? null : null,
          unit: axis.unit ?? null,
          current: currentStep(state),
        }
      : null,
    notAnswered: [...NOT_ANSWERED],
  };
}
