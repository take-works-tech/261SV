'use client'

import { Fragment, Suspense, useState } from 'react'
import Image from 'next/image'
import { useRouter, useSearchParams } from 'next/navigation'
import { Viewport } from '@/components/workspace/viewport'
import { MaterialPreview } from '@/components/workspace/material-preview'
import { VisualOptions, OptionSample } from '@/components/workspace/option-samples'
import { MaterialSphereIcon } from '@/components/icons/material-sphere-icon'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogFooter, DialogOverlay } from '@/components/ui/dialog'
import { Popover, PopoverContent } from '@/components/ui/popover'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  ArrowUpRight,
  ArrowUpDown,
  BarChart3,
  Bookmark,
  Boxes,
  Camera,
  ChartNoAxesCombined,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ChevronUp,
  CircleDashed,
  Clock3,
  Columns3,
  Copy,
  Cpu,
  Crosshair,
  FileOutput,
  FileText,
  Film,
  FolderOpen,
  FolderPlus,
  Gauge,
  Globe2,
  Grid2X2,
  HardDrive,
  GripVertical,
  Grid3x3,
  PenLine,
  HelpCircle,
  Eye,
  EyeOff,
  Image as ImageIcon,
  Database,
  Globe,
  IdCard,
  ListChecks,
  Layers3,
  LayoutTemplate,
  LayoutGrid,
  List,
  MessageSquareText,
  MoreHorizontal,
  Network,
  MonitorCog,
  Paintbrush,
  PanelLeft,
  PanelRight,
  Pencil,
  Play,
  Plus,
  RefreshCw,
  Redo2,
  Ruler,
  Save,
  Search,
  ScrollText,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Square,
  Shapes,
  Tag,
  Target,
  Telescope,
  Trash2,
  Type,
  Upload,
  Undo2,
  Variable,
  Waypoints,
  Workflow,
  X,
} from 'lucide-react'
import catalogData from '@/lib/screen-catalog.json'

type ScreenId =
  | 'home'
  | 'simulation'
  | 'pipeline'
  | 'view'
  | 'graph'
  | 'report'
  | 'chat'
  | 'settings'
  | 'network'

type Scenario = {
  id: string
  screen: ScreenId
  variant: string
  label: string
  intent: string
  href: string
}

const scenarios = catalogData.scenarios as Scenario[]
const screenOrder: ScreenId[] = [
  'home',
  'simulation',
  'view',
  'graph',
  'report',
  'pipeline',
  'chat',
  'settings',
  'network',
]

const screenNames: Record<ScreenId, string> = {
  home: 'ワークスペース一覧',
  simulation: 'シミュレーション',
  pipeline: '自動化',
  view: 'ビュー',
  graph: 'グラフ',
  report: 'レポート',
  chat: 'チャット',
  settings: '設定',
  network: 'ネットワークと監査',
}

const areaTabs: { id: ScreenId; label: string; icon: typeof Boxes }[] = [
  { id: 'simulation', label: 'シミュレーション', icon: Gauge },
  { id: 'view', label: 'ビュー', icon: Boxes },
  { id: 'graph', label: 'グラフ', icon: BarChart3 },
  { id: 'report', label: 'レポート', icon: FileText },
  { id: 'pipeline', label: '自動化', icon: Workflow },
]

type SidebarTab = {
  id: string
  label: string
  description: string
  icon: typeof Boxes
  scope?: 'view' | 'selection'
}

type ViewObjectKind =
  | 'analysis-mesh'
  | 'reference-mesh'
  | 'scalar-field'
  | 'vector-field'
  | 'trajectory'
  | 'point-cloud'
  | 'annotation'
  | 'effect'

type MeshRepresentation = 'surface' | 'surface-edges' | 'wireframe'

const viewObjectKinds: Record<ViewObjectKind, { label: string; name: string; materialSurface: boolean; textProperties: boolean }> = {
  'analysis-mesh': { label: '解析メッシュ', name: '解析メッシュ（仮）', materialSurface: true, textProperties: false },
  'reference-mesh': { label: '参照メッシュ', name: '参照メッシュ（仮）', materialSurface: true, textProperties: false },
  'scalar-field': { label: 'スカラー場', name: 'スカラー場（未接続）', materialSurface: true, textProperties: false },
  'vector-field': { label: 'ベクトル場', name: 'ベクトル場（未接続）', materialSurface: false, textProperties: false },
  trajectory: { label: '流線・軌跡', name: '流線・軌跡（未接続）', materialSurface: false, textProperties: false },
  'point-cloud': { label: '点群', name: '点群（未接続）', materialSurface: false, textProperties: false },
  annotation: { label: 'テキスト・注釈', name: 'テキスト注釈（仮）', materialSurface: false, textProperties: true },
  effect: { label: 'エフェクト', name: '強調表示（仮）', materialSurface: false, textProperties: false },
}

// view/AC-068: selection in the viewport or the @Outliner decides which View object the Object,
// Materials and contextual Text sections edit. The rail used to read the scenario variant alone, so
// clicking another element left every property form describing the previous one.
const outlinerObjectKinds: Record<string, ViewObjectKind | 'container'> = {
  '［元ファイルのルート名］': 'container',
  '［元ファイルのアセンブリ名］': 'container',
  '［元ファイルの部品名 01］': 'analysis-mesh',
  '［元ファイルの部品名 02］': 'reference-mesh',
  '［元ファイルの領域名］': 'point-cloud',
}

const viewObjectKindByVariant: Partial<Record<string, ViewObjectKind>> = {
  'object-analysis-mesh': 'analysis-mesh',
  'object-reference-mesh': 'reference-mesh',
  'object-scalar-field': 'scalar-field',
  'object-vector-field': 'vector-field',
  'object-trajectory': 'trajectory',
  'object-point-cloud': 'point-cloud',
  'object-annotation': 'annotation',
  'object-effect': 'effect',
  'material-composition': 'analysis-mesh',
}

type ActiveViewObject = { name: string; kind: ViewObjectKind | 'container' }

function activeViewObject(variant: string, selectedViewObjects: string[]): ActiveViewObject {
  // The most recently selected object is the active one; the rest stay selected without producing an
  // aggregate form (view/AC-068).
  const name = selectedViewObjects.at(-1)
  const selectedKind = name ? outlinerObjectKinds[name] : undefined
  if (name && selectedKind) return { name, kind: selectedKind }
  const kind = viewObjectKindByVariant[variant] ?? 'analysis-mesh'
  return { name: name ?? viewObjectKinds[kind].name, kind }
}

const rightSidebarTabs: Record<ScreenId, SidebarTab[]> = {
  home: [],
  simulation: [
    { id: 'solver', label: 'ソルバー', description: 'ソルバー連携と実行条件を確認します。', icon: Cpu },
  ],
  pipeline: [
    { id: 'unit', label: 'ユニット', description: 'パイプラインに追加する処理単位を選択します。', icon: Layers3 },
    { id: 'settings', label: '設定', description: '選択中のユニットとパイプラインの条件を編集します。', icon: SlidersHorizontal },
    { id: 'history', label: '履歴', description: '実行結果と再現可能な処理履歴を確認します。', icon: Clock3 },
  ],
  view: [
    { id: 'overall', label: 'ビュー', description: '開いている項目そのもの（名前・定義）と、キャンバスに重ねるガイドを設定します。', icon: IdCard, scope: 'view' },
    { id: 'camera', label: 'カメラ', description: 'このビューが持つカメラを追加し、ポーズとレンズ、被写界深度を設定します。', icon: Camera, scope: 'view' },
    { id: 'rendering', label: '描画', description: 'レンダラー、照明、現像を設定します。', icon: MonitorCog, scope: 'view' },
    { id: 'background', label: '背景', description: 'ビューの背景と周辺環境を設定します。', icon: Globe, scope: 'view' },
    { id: 'output', label: '出力', description: '画像と動画の作成条件を設定します。', icon: FileOutput, scope: 'view' },
    { id: 'objects', label: 'オブジェクト', description: '選択中の表示オブジェクトを設定します。', icon: Shapes, scope: 'selection' },
    { id: 'text', label: 'テキスト', description: '選択中のテキスト・注釈の内容と文字表現を設定します。', icon: Type, scope: 'selection' },
    { id: 'materials', label: 'マテリアル', description: '選択中の形状と結果表示に使う外観を設定します。', icon: MaterialSphereIcon, scope: 'selection' },
  ],
  graph: [
    { id: 'overall', label: 'グラフ', description: '開いているグラフそのもの（名前・種類・凡例）と、描く対象のケースを設定します。', icon: IdCard },
    { id: 'series', label: '系列', description: '系列ごとに、何を描くかと、どう見えるかを1か所で設定します。', icon: Database },
    { id: 'axes', label: '軸', description: '軸を1本選び、その表題・範囲・目盛・グリッドを設定します。', icon: Grid3x3 },
    { id: 'style', label: 'スタイル', description: 'グラフ全体の配色・既定の線とマーカー・書体を設定します。', icon: Paintbrush },
    { id: 'output', label: '出力', description: '画像、ベクター形式、表データの出力条件を設定します。', icon: FileOutput },
  ],
  report: [
    { id: 'overall', label: 'レポート', description: '開いているレポートそのもの（名前・タイトル・必須情報）を設定します。', icon: IdCard },
    { id: 'contents', label: '内容', description: '参照するケースの範囲と、収録するブロックを設定します。', icon: ListChecks },
    { id: 'drafting', label: '執筆', description: '本文の書き方を決め、下書きを作って、確認したものだけを取り込みます。', icon: PenLine },
    { id: 'style', label: 'スタイル', description: 'ページ・配色・書体を、文書全体のテーマとしてまとめて設定します。', icon: Paintbrush },
    { id: 'output', label: '出力', description: '文書形式と出力条件を設定します。', icon: FileOutput },
  ],
  chat: [],
  settings: [
  ],
  network: [
    { id: 'permissions', label: '権限', description: 'ネットワーク利用の許可範囲を確認します。', icon: ShieldCheck },
    { id: 'audit', label: '監査', description: '外部通信と許可判断の記録を確認します。', icon: ScrollText },
  ],
}

const libraryCategories: Partial<Record<ScreenId, string[]>> = {
  view: ['template', 'objects', 'materials', 'background', 'fonts'],
  graph: ['template', 'style', 'fonts'],
  report: ['template', 'layout', 'style', 'fonts'],
}

const libraryCategoryMeta: Record<string, { label: string; icon: typeof Boxes }> = {
  template: { label: 'テンプレート', icon: LayoutTemplate },
  objects: { label: 'オブジェクト', icon: Shapes },
  materials: { label: 'マテリアル', icon: MaterialSphereIcon },
  background: { label: '背景', icon: ImageIcon },
  fonts: { label: 'テキスト', icon: Type },
  style: { label: 'スタイル', icon: Paintbrush },
  layout: { label: 'レイアウト', icon: LayoutGrid },
}

// The keyboard scheme of 11_ui.md, shown where the commands are. "Every command is reachable from the
// keyboard" was once a promise with nothing behind it; a scheme nobody can find is the same promise.
// The exact key is a platform decision - what this table fixes is what has a shortcut and what may
// never have one. `specGroup` names the row of the specification's keyboard table this group answers,
// so a row added there fails the build until a group here carries it.
const shortcutGroups: { group: string; specGroup: string; note: string; commands: { name: string; key: string | null; reason?: string }[] }[] = [
  { group: 'ワークスペース', specGroup: 'workspace', note: 'プラットフォーム標準の修飾キーに従います', commands: [
    { name: '新規', key: 'Ctrl + N' }, { name: '開く', key: 'Ctrl + O' }, { name: '保存', key: 'Ctrl + S' }, { name: '名前を付けて保存', key: 'Ctrl + Shift + S' },
  ] },
  { group: '取り消しとやり直し', specGroup: 'undo and redo', note: '1つの指示は1ステップ。スクリプト全体でも同じです（XC-061）', commands: [
    { name: '取り消し', key: 'Ctrl + Z' }, { name: 'やり直し', key: 'Ctrl + Y' },
  ] },
  { group: '作業モード', specGroup: 'areas', note: '6モードに6キー。対象は変わりません', commands: [
    { name: 'シミュレーション', key: 'Ctrl + 1' }, { name: 'ビュー', key: 'Ctrl + 2' }, { name: 'グラフ', key: 'Ctrl + 3' },
    { name: 'レポート', key: 'Ctrl + 4' }, { name: '自動化', key: 'Ctrl + 5' }, { name: 'チャット', key: 'Ctrl + 6' },
  ] },
  { group: 'ケースツリー', specGroup: 'case tree', note: '検索は常設の入力欄で、ダイアログではありません', commands: [
    { name: 'ケースを上下に移動', key: '↑ / ↓' }, { name: 'ケースを折りたたむ・展開する', key: '← / →' }, { name: 'ケースを文字入力で検索', key: '文字キー' },
  ] },
  { group: 'アウトライナー', specGroup: 'outliner', note: 'アクティブなビューにのみ作用し、元データの階層は編集しません', commands: [
    { name: '構成要素を上下に移動', key: '↑ / ↓' }, { name: '構成要素を折りたたむ・展開する', key: '← / →' },
    { name: '構成要素を文字入力で検索', key: '文字キー' }, { name: '表示・非表示を切り替え', key: 'H' }, { name: '分岐だけを表示', key: 'Shift + H' },
  ] },
  { group: '結果軸', specGroup: 'result axis', note: '軸が時刻・モード・周波数のいずれでも同じキーです（XC-131）', commands: [
    { name: '再生／一時停止', key: 'Space' }, { name: '前へ', key: '←' }, { name: '次へ', key: '→' },
    { name: '先頭', key: 'Home' }, { name: '末尾', key: 'End' },
  ] },
  { group: 'ビュー', specGroup: 'view', note: '変形の切り替えがあるからこそ、倍率は常に描き込まれます（INV-024）', commands: [
    { name: '全体を表示', key: 'F' }, { name: '正投影方向', key: 'Numpad 1 / 3 / 7' }, { name: '変形倍率を1.0と設定値で切替', key: 'D' },
  ] },
  { group: '選択とプローブ', specGroup: 'selection and probe', note: '保持は常に明示操作で、自動では行いません', commands: [
    { name: 'カーソル位置をプローブ', key: 'P' }, { name: 'プローブ値を変数として保持', key: 'Ctrl + P' },
  ] },
  { group: '指示バー', specGroup: 'instruction bar', note: 'エージェント支援の利用者がいちばん多く通る経路です', commands: [
    { name: '指示バーへフォーカス', key: 'Ctrl + K' }, { name: 'フォーカスを元の位置へ戻す', key: 'Esc' },
  ] },
  { group: 'パネル', specGroup: 'panels', note: '表示状態だけを変え、解析内容や項目の定義は変えません', commands: [
    { name: '左サイドバーの表示切替', key: 'Ctrl + B' }, { name: '右サイドバーの表示切替', key: 'Ctrl + Shift + B' },
    { name: '分割レイアウトへ入る・出る', key: 'Ctrl + Alt + S' },
  ] },
  { group: '破壊的な操作', specGroup: 'destructive', note: 'いずれも単一キーを持ちません。確認を経由してのみ到達します（XC-062、XC-094）', commands: [
    { name: 'ケースを削除', key: null, reason: '影響するケース数を示す確認から実行' },
    { name: '対象集合をクリア', key: null, reason: '対象範囲を示す確認から実行' },
    { name: '破壊的パイプラインユニットを実行', key: null, reason: '影響範囲の確認から実行' },
  ] },
]

// One definition per key. The menus below and the instruction bar read from this table instead of
// printing a second copy of `Ctrl + K` that nothing keeps in step (P7, XC-187).
const commandByName = new Map(shortcutGroups.flatMap((group) => group.commands.map((command) => [command.name, command] as const)))

function shortcutFor(name: string) {
  return commandByName.get(name) ?? null
}

// The File/Edit/View/Filter/Tools/Help menus. They used to hold two generated placeholders per menu -
// `ファイルを開く` and `ファイルの設定` - which named no command and taught no key. 11_ui.md requires a
// shortcut to be discoverable from the thing it operates on: beside the action in the menu, and in the
// command list. Both now read the one command table above.
type TopMenuItem = { command: string; action?: TopMenuAction }
type TopMenuAction = 'import' | 'settings' | 'shortcuts' | 'script' | 'notifications' | 'left-panel' | 'right-panel' | 'assistant' | 'network' | 'home'

const topMenuCommands: { menu: string; items: TopMenuItem[] }[] = [
  { menu: 'ファイル', items: [
    { command: '新規', action: 'home' },
    { command: '開く', action: 'home' },
    { command: '保存' },
    { command: '名前を付けて保存' },
    { command: '結果ファイルを取り込む', action: 'import' },
  ] },
  { menu: '編集', items: [
    { command: '取り消し' },
    { command: 'やり直し' },
    { command: 'ケースを削除' },
    { command: '対象集合をクリア' },
  ] },
  { menu: '表示', items: [
    { command: '左サイドバーの表示切替', action: 'left-panel' },
    { command: '右サイドバーの表示切替', action: 'right-panel' },
    { command: '分割レイアウトへ入る・出る' },
    { command: '全体を表示' },
    { command: '変形倍率を1.0と設定値で切替' },
  ] },
  { menu: 'フィルタ', items: [
    { command: 'ケースを文字入力で検索' },
    { command: '構成要素を文字入力で検索' },
    { command: '分岐だけを表示' },
  ] },
  { menu: 'ツール', items: [
    { command: 'カーソル位置をプローブ' },
    { command: 'プローブ値を変数として保持' },
    { command: '指示バーへフォーカス', action: 'assistant' },
    { command: '操作のスクリプトを表示', action: 'script' },
  ] },
  { menu: 'ヘルプ', items: [
    { command: 'コマンドとキーの一覧', action: 'shortcuts' },
    { command: '通知履歴', action: 'notifications' },
    { command: 'ネットワークと監査', action: 'network' },
  ] },
]

function TopMenu({ menu, items, onAction }: { menu: string; items: TopMenuItem[]; onAction: (action: TopMenuAction) => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild><button type="button">{menu}</button></DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="top-menu-content command-menu">
        {items.map((item) => {
          const command = shortcutFor(item.command)
          return (
            <DropdownMenuItem key={item.command} onSelect={() => item.action && onAction(item.action)}>
              <span>{item.command}</span>
              {command && command.key === null
                ? <em className="command-menu-no-key" title={command.reason}>キーなし</em>
                : <kbd>{command?.key ?? '—'}</kbd>}
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}


// XC-207: entering an area lands on that area's declared baseline, never on whichever of its states
// sorts first. The catalogue is ordered for reading, so "first" put the assistant drawer over the 3D
// view the moment the View area was opened - a demonstration state presented as the product's resting
// state.
function scenarioFor(screen: ScreenId, variant?: string) {
  return (
    scenarios.find((scenario) => scenario.screen === screen && scenario.variant === variant) ??
    scenarios.find((scenario) => scenario.screen === screen && scenario.variant === 'default') ??
    scenarios.find((scenario) => scenario.screen === screen) ??
    scenarios[0]
  )
}

export default function Page() {
  return (
    <Suspense fallback={<div className="loading-shell">UIモックアップ一覧を読み込んでいます…</div>}>
      <MockupCatalog />
    </Suspense>
  )
}

function MockupCatalog() {
  const router = useRouter()
  const params = useSearchParams()
  const [sharedDraft, setSharedDraft] = useState('')
  const [conversationSettings, setConversationSettings] = useState<ConversationSettings>({ model: 'local', effort: 'standard', search: 'off' })
  const screen = (params.get('screen') as ScreenId | null) ?? 'home'
  const variant = params.get('variant') ?? 'default'
  const selected = scenarioFor(screenNames[screen] ? screen : 'home', variant)
  const navigate = (scenario: Scenario) => router.replace(scenario.href, { scroll: false })
  const navigateScreen = (nextScreen: ScreenId) => navigate(scenarioFor(nextScreen))

  return (
    <main className="mockup-root">
      <ProductShell key={selected.id} scenario={selected} onScreen={navigateScreen} draft={sharedDraft} onDraftChange={setSharedDraft} settings={conversationSettings} onSettingsChange={setConversationSettings} />
      <ScenarioCatalog selected={selected} onSelect={navigate} />
    </main>
  )
}

function startHorizontalPanelResize(
  event: React.PointerEvent<HTMLButtonElement>,
  side: 'left' | 'right',
  currentWidth: number,
  setWidth: React.Dispatch<React.SetStateAction<number>>,
) {
  event.preventDefault()
  const handle = event.currentTarget
  const pointerId = event.pointerId
  const startX = event.clientX
  const previousCursor = document.body.style.cursor
  const previousSelection = document.body.style.userSelect
  handle.setPointerCapture(pointerId)
  document.body.style.cursor = 'ew-resize'
  document.body.style.userSelect = 'none'
  const centreWidth = handle.closest('.workbench')?.querySelector<HTMLElement>('.centre-column')?.clientWidth ?? 320
  const availableGrowth = Math.max(0, centreWidth - 320)
  const hardMaximum = side === 'left' ? 360 : 460
  const maximum = Math.min(hardMaximum, currentWidth + availableGrowth)

  const move = (moveEvent: PointerEvent) => {
    const delta = moveEvent.clientX - startX
    const next = side === 'left' ? currentWidth + delta : currentWidth - delta
    const minimum = side === 'left' ? 160 : 210
    setWidth(Math.min(maximum, Math.max(minimum, next)))
  }
  const finish = () => {
    document.body.style.cursor = previousCursor
    document.body.style.userSelect = previousSelection
    handle.removeEventListener('pointermove', move)
    handle.removeEventListener('pointerup', finish)
    handle.removeEventListener('pointercancel', finish)
  }
  handle.addEventListener('pointermove', move)
  handle.addEventListener('pointerup', finish)
  handle.addEventListener('pointercancel', finish)
}

function resizeHorizontalPanelFromKey(
  event: React.KeyboardEvent<HTMLButtonElement>,
  side: 'left' | 'right',
  setWidth: React.Dispatch<React.SetStateAction<number>>,
) {
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
  event.preventDefault()
  const centreWidth = event.currentTarget.closest('.workbench')?.querySelector<HTMLElement>('.centre-column')?.clientWidth ?? 320
  const grows = side === 'left' ? event.key === 'ArrowRight' : event.key === 'ArrowLeft'
  const direction = grows ? 12 : -12
  const minimum = side === 'left' ? 160 : 210
  const hardMaximum = side === 'left' ? 360 : 460
  setWidth((current) => {
    const maximum = Math.min(hardMaximum, current + Math.max(0, centreWidth - 320))
    return Math.min(maximum, Math.max(minimum, current + direction))
  })
}

function getLibraryMaximumHeight(shelf: HTMLElement) {
  const centreColumn = shelf.closest<HTMLElement>('.centre-column')
  if (!centreColumn) throw new Error('Material library shelf is detached from its centre column')
  const reservedHeight = Array.from(centreColumn.children)
    .filter((child) => child !== shelf && !child.classList.contains('canvas-wrap'))
    .reduce((height, child) => height + (child as HTMLElement).getBoundingClientRect().height, 0)
  return Math.min(560, Math.max(169, centreColumn.clientHeight - reservedHeight))
}

function startLibraryResize(
  event: React.PointerEvent<HTMLButtonElement>,
  setHeight: React.Dispatch<React.SetStateAction<number>>,
  setMaximum: React.Dispatch<React.SetStateAction<number>>,
  onExpand: () => void,
) {
  event.preventDefault()
  const handle = event.currentTarget
  const shelf = handle.closest<HTMLElement>('.asset-library-shelf')
  if (!shelf) throw new Error('Material library splitter is detached from its shelf')
  const pointerId = event.pointerId
  const startY = event.clientY
  const startHeight = shelf.getBoundingClientRect().height
  const maximum = getLibraryMaximumHeight(shelf)
  const baselineHeight = Math.min(maximum, Math.max(169, startHeight))
  const previousCursor = document.body.style.cursor
  const previousSelection = document.body.style.userSelect
  handle.setPointerCapture(pointerId)
  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
  setMaximum(maximum)
  setHeight(baselineHeight)
  onExpand()

  const move = (moveEvent: PointerEvent) => {
    const next = baselineHeight - (moveEvent.clientY - startY)
    setHeight(Math.min(maximum, Math.max(169, next)))
  }
  const finish = () => {
    document.body.style.cursor = previousCursor
    document.body.style.userSelect = previousSelection
    handle.removeEventListener('pointermove', move)
    handle.removeEventListener('pointerup', finish)
    handle.removeEventListener('pointercancel', finish)
  }
  handle.addEventListener('pointermove', move)
  handle.addEventListener('pointerup', finish)
  handle.addEventListener('pointercancel', finish)
}

function ProductShell({ scenario, onScreen, draft, onDraftChange, settings, onSettingsChange }: { scenario: Scenario; onScreen: (screen: ScreenId) => void; draft: string; onDraftChange: (draft: string) => void; settings: ConversationSettings; onSettingsChange: (settings: ConversationSettings) => void }) {
  const isHome = scenario.screen === 'home'
  const isChat = scenario.screen === 'chat'
  const isSettings = scenario.screen === 'settings'
  // 11_ui.md's layout table grants the left column to Simulation, View, Graph, Report and Automation,
  // and the chat history to Chat. Network and audit is in neither list: a case tree beside a
  // workspace-wide permission implies the permission belongs to the selected case (the reasoning of
  // XC-165, one screen over).
  const showsCaseSidebar = scenario.screen !== 'network'
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)
  const [assistantOpen, setAssistantOpen] = useState(scenario.variant === 'assistant-drawer')
  const [importOpen, setImportOpen] = useState(scenario.variant === 'import-review')
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [scriptOpen, setScriptOpen] = useState(false)
  const [itemListOpen, setItemListOpen] = useState(false)
  const [itemListQuery, setItemListQuery] = useState('')
  const [itemListLayout, setItemListLayout] = useState<'grid' | 'list'>('grid')
  const [itemListScope, setItemListScope] = useState('すべて')
  const [selectedCase, setSelectedCase] = useState(scenario.variant === 'steady-result' ? '静荷重ケース' : workspaceCases[0].name)
  // Which item is open in each area, and - for the View area - therefore which kind it is (XC-202).
  const [openItems, setOpenItems] = useState<Partial<Record<ScreenId, string>>>(
    scenario.screen === 'view' && scenario.variant.startsWith('comparison') ? { view: 'ケース比較' } : {},
  )
  const openViewItem = workItemHeaderByScreen.view?.items.find((item) => item.name === (openItems.view ?? workItemHeaderByScreen.view?.items[0].name)) ?? null
  const isComparisonItem = openViewItem?.kind === 'comparison'
  const [comparison, setComparison] = useState<ComparisonModel>({
    axis: scenario.variant === 'comparison-range' || scenario.variant === 'comparison-columns' || scenario.variant === 'comparison-output' ? 'resultPosition' : 'case',
    members: workspaceCases.map((item) => item.name),
    memberMode: scenario.variant === 'comparison-range' || scenario.variant === 'comparison-columns' ? 'range' : 'enumerate',
    rangeCount: scenario.variant === 'comparison-columns' ? 6 : 4,
    arrangement: scenario.variant === 'comparison-overlay' ? 'overlay' : 'grid',
    columns: scenario.variant === 'comparison-columns' ? 3 : 'auto',
    sharedColourMap: true,
  })
  // Session state, held by the shell rather than the canvas: the control that sets it is in the work
  // area bar, and a value edited from the bar cannot live inside the thing the bar sits above (XC-204).
  const [splitPanes, setSplitPanes] = useState(scenario.variant === 'split-two' || scenario.variant === 'split-output' ? 2 : scenario.variant === 'split-three' ? 3 : scenario.variant === 'split-four' ? 4 : 1)
  const [cameraSync, setCameraSync] = useState(true)
  const [splitPromoteOpen, setSplitPromoteOpen] = useState(false)
  const layoutControl: { kind: 'split' } | { kind: 'comparison'; members: number } | null = scenario.screen !== 'view'
    ? null
    : isComparisonItem
      ? (comparison.arrangement === 'grid' ? { kind: 'comparison', members: comparisonMemberLabels(comparison).length } : null)
      : { kind: 'split' }
  const [viewItem, setViewItem] = useState<ViewItemState>(initialViewItem)
  const [pipelineUnits, setPipelineUnits] = useState<PipelineUnitModel[]>(scenario.screen === 'pipeline' && scenario.variant === 'empty' ? [] : defaultPipelineUnits)
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>('unit-graph')
  const [leftSidebarWidth, setLeftSidebarWidth] = useState(220)
  const [rightSidebarWidth, setRightSidebarWidth] = useState(286)
  // A taxonomy variant seeds its own object; every other View state starts on a source element the
  // Outliner actually lists, so the highlighted row and the Object panel name the same thing.
  const [selectedViewObjects, setSelectedViewObjects] = useState([
    viewObjectKindByVariant[scenario.variant]
      ? viewObjectKinds[viewObjectKindByVariant[scenario.variant] as ViewObjectKind].name
      : '［元ファイルの部品名 01］',
  ])

  const selectViewObject = (name: string, additive = false) => {
    setSelectedViewObjects((current) => additive ? [...current.filter((item) => item !== name), name] : [name])
  }

  const runTopMenuAction = (action: TopMenuAction) => {
    if (action === 'import') setImportOpen(true)
    if (action === 'settings' || action === 'shortcuts') onScreen('settings')
    if (action === 'script') setScriptOpen(true)
    if (action === 'notifications') setNotificationsOpen(true)
    if (action === 'left-panel') setLeftOpen((open) => !open)
    if (action === 'right-panel') setRightOpen((open) => !open)
    if (action === 'assistant') setAssistantOpen(true)
    if (action === 'network') onScreen('network')
    if (action === 'home') onScreen('home')
  }

  return (
    <section className="product-shell">
      <header className="app-header">
        <div className="topbar">
          <button className="brand" onClick={() => onScreen('home')} aria-label="ワークスペース一覧を開く">
            <span><Waypoints size={17} /></span>
            <b>SOLVIA</b>
            <small>UIモック</small>
          </button>
          <nav className="main-menu" aria-label="メインメニュー">
            {topMenuCommands.map(({ menu, items }) => <TopMenu key={menu} menu={menu} items={items} onAction={runTopMenuAction} />)}
          </nav>
          <div className="top-actions">
            <div className="view-switcher" aria-label="表示切替">
              <button className={!isHome && !isSettings ? 'active' : ''} onClick={() => onScreen('view')}>ワークスペース</button>
              <button className={isHome ? 'active' : ''} onClick={() => onScreen('home')}>ワークスペース一覧</button>
            </div>
            <button type="button" className="offline-chip" onClick={() => onScreen('network')} aria-label="ネットワークと監査を開く"><ShieldCheck size={13} /> オフライン</button>
            <div className="notification-anchor">
              <button aria-label="通知履歴" aria-expanded={notificationsOpen} onClick={() => setNotificationsOpen((open) => !open)}><Clock3 size={16} /></button>
              {notificationsOpen && <NotificationHistory onClose={() => setNotificationsOpen(false)} />}
            </div>
            {/* Script view: what was just done, as script text, copyable. Reachable from every area
                because reproducibility is a property of the recorded command log, not of the area the
                command happened to be issued from (XC-046, 13_scripting.md). */}
            <div className="notification-anchor">
              <button aria-label="操作のスクリプトを表示" aria-expanded={scriptOpen} onClick={() => setScriptOpen((open) => !open)}><ScrollText size={16} /></button>
              {scriptOpen && <ScriptView onClose={() => setScriptOpen(false)} />}
            </div>
            <button aria-label="設定" onClick={() => onScreen('settings')}><Settings size={16} /></button>
            <button aria-label="ヘルプ"><HelpCircle size={16} /></button>
          </div>
        </div>
        {!isHome && !isSettings && <div className="work-toolbar">
          {showsCaseSidebar && <Button variant="ghost" size="icon" className="panel-toggle panel-toggle-left" aria-label={leftOpen ? '左サイドバーを閉じる' : '左サイドバーを開く'} onClick={() => setLeftOpen((open) => !open)}><PanelLeft size={15} /></Button>}
          <span className="tool-divider" />
          <button className="toolbar-button" aria-label="ファイルを取り込む" onClick={() => setImportOpen(true)}><Upload size={14} /></button>
          <button className="toolbar-button" aria-label="ワークスペースを保存"><Save size={14} /></button>
          <button className="toolbar-button" aria-label="元に戻す"><Undo2 size={14} /></button>
          <button className="toolbar-button" aria-label="やり直す"><Redo2 size={14} /></button>
          <span className="tool-divider" />
          <nav className="area-tabs" aria-label="作業領域">
            {areaTabs.map(({ id, label, icon: Icon }) => (
              <button key={id} className={scenario.screen === id ? 'active' : ''} onClick={() => onScreen(id)}>
                <Icon size={14} /> {label}
              </button>
            ))}
          </nav>
          {scenario.variant === 'running' && <span className="run-chip"><CircleDashed size={13} /> パイプライン実行中</span>}
          <div className="work-toolbar-utilities">
            <Button variant="ghost" size="sm" className={isChat ? 'chat-global-button active' : 'chat-global-button'} aria-label="チャットを開く" aria-pressed={isChat} onClick={() => onScreen('chat')}><MessageSquareText size={14} /><span>チャット</span></Button>
            {!isChat && !itemListOpen && <Button variant="ghost" size="icon" className="panel-toggle panel-toggle-right" aria-label={rightOpen ? '右サイドバーを閉じる' : '右サイドバーを開く'} onClick={() => setRightOpen((open) => !open)}><PanelRight size={15} /></Button>}
          </div>
        </div>}
      </header>

      {isHome ? (
        <WorkspaceHome variant={scenario.variant} onOpenView={() => onScreen('view')} onImport={() => setImportOpen(true)} />
      ) : isSettings ? (
        <div className="settings-page">
          <SettingsScreen variant={scenario.variant} />
        </div>
      ) : (
        <div
          className={`workbench ${isChat ? 'chat-workbench' : ''} ${!leftOpen || !showsCaseSidebar ? 'left-closed' : ''} ${!rightOpen || itemListOpen ? 'right-closed' : ''}`}
          style={{ '--left-sidebar-width': `${leftSidebarWidth}px`, '--right-sidebar-width': `${rightSidebarWidth}px` } as React.CSSProperties}
        >
          {leftOpen && showsCaseSidebar && <LeftSidebar screen={scenario.screen} width={leftSidebarWidth} setWidth={setLeftSidebarWidth} selectedCase={selectedCase} onSelectCase={setSelectedCase} />}
          <section className="centre-column">
            {scenario.screen !== 'chat' && <WorkAreaBar screen={scenario.screen} itemListOpen={itemListOpen} onItemListOpenChange={setItemListOpen} itemListQuery={itemListQuery} onItemListQueryChange={setItemListQuery} itemListLayout={itemListLayout} onItemListLayoutChange={setItemListLayout} itemListScope={itemListScope} onItemListScopeChange={setItemListScope} openItems={openItems} onOpenItemChange={(screen, item) => setOpenItems((current) => ({ ...current, [screen]: item }))} splitPanes={splitPanes} onSplitPanesChange={setSplitPanes} cameraSync={cameraSync} onCameraSyncChange={setCameraSync} onPromoteSplit={() => setSplitPromoteOpen(true)} layoutControl={layoutControl} comparisonColumns={comparison.columns} onComparisonColumnsChange={(columns) => setComparison({ ...comparison, columns })} />}
            <div className={`canvas-wrap ${scenario.screen === 'chat' ? 'chat-canvas-wrap' : ''} ${scenario.screen === 'view' && !itemListOpen ? 'view-canvas-wrap' : ''} ${itemListOpen ? 'work-item-list-wrap' : ''}`}>
              {itemListOpen && scenario.screen !== 'chat' ? <WorkItemLibrary screen={scenario.screen} query={itemListQuery} layout={itemListLayout} scope={itemListScope} onSelect={() => setItemListOpen(false)} /> : <ScreenCanvas scenario={scenario} draft={draft} onDraftChange={onDraftChange} onViewObjectSelect={selectViewObject} onScreen={onScreen} settings={settings} onSettingsChange={onSettingsChange} pipelineUnits={pipelineUnits} onPipelineUnitsChange={setPipelineUnits} selectedUnitId={selectedUnitId} onSelectUnit={setSelectedUnitId} selectedCase={selectedCase} viewItem={viewItem} onViewItemChange={setViewItem} isComparisonItem={isComparisonItem} comparison={comparison} baseViewName={openViewItem?.baseViewName ?? '標準ビュー'} splitPanes={splitPanes} promoteOpen={splitPromoteOpen} onPromoteOpenChange={setSplitPromoteOpen} />}
              {!isChat && assistantOpen && <AssistantDrawer draft={draft} onDraftChange={onDraftChange} onClose={() => setAssistantOpen(false)} onOpenChat={() => onScreen('chat')} settings={settings} onSettingsChange={onSettingsChange} />}
            </div>
            {scenario.screen !== 'chat' && !itemListOpen && <AssetLibraryShelf screen={scenario.screen} variant={scenario.variant} />}
            {scenario.screen !== 'chat' && (assistantOpen ? null : <InstructionBar draft={draft} onDraftChange={onDraftChange} onOpen={() => setAssistantOpen(true)} />)}
          </section>
          {!isChat && rightOpen && !itemListOpen && <RightSidebar screen={scenario.screen} variant={scenario.variant} width={rightSidebarWidth} setWidth={setRightSidebarWidth} selectedViewObjects={selectedViewObjects} onViewObjectSelect={selectViewObject} pipelineUnits={pipelineUnits} onPipelineUnitsChange={setPipelineUnits} selectedUnitId={selectedUnitId} onSelectUnit={setSelectedUnitId} viewItem={viewItem} onViewItemChange={setViewItem} selectedCase={selectedCase} isComparisonItem={isComparisonItem} baseViewName={openViewItem?.baseViewName ?? '標準ビュー'} comparison={comparison} onComparisonChange={setComparison} splitPanes={splitPanes} />}
        </div>
      )}
      <ImportFlowDialog open={importOpen} onOpenChange={setImportOpen} initialStep={scenario.variant === 'import-review' ? 'review' : 'choose'} />
    </section>
  )
}

// The script for what was just done. It is the reproducible artefact - not the model, not the
// screenshot - so it is copyable and reachable from wherever the operation was performed (XC-046).
function ScriptView({ onClose }: { onClose: () => void }) {
  const [copied, setCopied] = useState(false)
  const script = [
    "workspace = solvia.open_workspace()",
    "case = workspace.cases['基準ケース']",
    "view = workspace.views['標準ビュー']",
    "view.deformation_scale = 50.0            # 表示のみ・報告値は未変形形状から計算",
    "probe = view.probe(node_id=12345)        # 単位・有効数字・由来つき",
    "workspace.variables.keep(probe, name='プローブ応力')",
  ].join("\n")
  return (
    <section className="script-view" aria-label="操作のスクリプト">
      <header>
        <span><b>スクリプト</b><small>いま行った操作。これが再現可能な成果物です</small></span>
        <button type="button" aria-label="スクリプトを閉じる" onClick={onClose}><X size={13} /></button>
      </header>
      <pre>{script}</pre>
      <footer>
        <button type="button" className="primary-button" onClick={() => setCopied(true)}><Copy size={12} />{copied ? 'コピーしました' : 'コピー'}</button>
        <small>言語モデルはコマンドを生成し、結果は生成しません。再現性はこのログの性質です。</small>
      </footer>
    </section>
  )
}

function NotificationHistory({ onClose }: { onClose: () => void }) {
  return <section className="notification-history" aria-label="通知履歴">
    <header><span><b>通知履歴</b><small>完了・失敗・拒否をローカルに保持</small></span><button type="button" aria-label="通知履歴を閉じる" onClick={onClose}><X size={14} /></button></header>
    <div className="notification-history-list">
      <article><ShieldCheck size={14} /><span><b>ワークスペースを開きました</b><small>ローカル操作・外部通信なし</small></span></article>
      <article className="warning"><AlertTriangle size={14} /><span><b>未宣言の単位があります</b><small>変換は行わず、数量を未宣言として維持しています</small></span></article>
      {/* A failure is shown where it happened *and* kept here, so a failure during a long run is not
          lost by looking away. Neither surface replaces the other. */}
      <article className="error"><AlertTriangle size={14} /><span><b>パイプライン：板厚変更ケースが失敗しました</b><small>グラフユニットで失敗・後続ユニットはこのケースだけスキップ</small></span></article>
    </div>
    <footer><button type="button">すべての通知を表示</button></footer>
  </section>
}

const importTagProposals = [
  { tag: 'ソルバー：［書き出し元］', basis: '根拠：ファイルヘッダーの書き出し元' },
  { tag: '要素数：［メッシュ規模］', basis: '根拠：読み取ったメッシュ規模の区分' },
  { tag: '差分：板厚', basis: '根拠：兄弟ケースと異なる変数' },
  { tag: '取込日：［日付］', basis: '根拠：ファイルの更新日時' },
]

function ImportFlowDialog({ open, onOpenChange, initialStep = 'choose' }: { open: boolean; onOpenChange: (open: boolean) => void; initialStep?: 'choose' | 'review' }) {
  const [step, setStep] = useState<'choose' | 'review' | 'importing'>(initialStep)
  const [groupingAccepted, setGroupingAccepted] = useState<boolean | null>(null)
  const [acceptedTags, setAcceptedTags] = useState<string[]>([])
  const [rejectedTags, setRejectedTags] = useState<string[]>([])
  const close = () => { setStep('choose'); onOpenChange(false) }
  return <Dialog open={open} onOpenChange={(nextOpen) => nextOpen ? onOpenChange(true) : close()}>
    <DialogOverlay className="modal-backdrop" />
    <DialogContent className="workflow-dialog import-flow-dialog">
      <header><span><small>データセット取込</small><b>{step === 'choose' ? '結果ファイルを選択' : step === 'review' ? '取込内容を確認' : '検証して読み込み中'}</b></span><button type="button" aria-label="取込を閉じる" onClick={close}><X size={15} /></button></header>
      {step === 'choose' && <>
        <button type="button" className="import-drop-target" onClick={() => setStep('review')}><Upload size={24} /><b>ここへファイルをドロップ</b><span>またはファイルを選択</span><small>対応可否は読込前に形式ごとに表示します</small></button>
        <p className="workflow-trust-note"><ShieldCheck size={13} />元ファイルは変更せず、単位・座標系・階層をファイル名から推測しません。</p>
      </>}
      {step === 'review' && <>
        <section className="import-review-list">
          <article><FileText size={16} /><span><b>［選択したファイル］</b><small>形式：検証待ち</small></span><em>読込前</em></article>
        </section>
        <section className="workflow-check-list" aria-label="取込時に確認する内容">
          <p><CheckCircle2 size={13} /><span><b>形式サポート</b><small>Verified / Limited / Unsupported と不足機能を表示</small></span></p>
          <p><CheckCircle2 size={13} /><span><b>フィールド</b><small>点・セル・積分点の関連を元のまま表示</small></span></p>
          <p><AlertTriangle size={13} /><span><b>単位</b><small>取込直後は未宣言。利用者が宣言するまで変換不可</small></span></p>
          <p><AlertTriangle size={13} /><span><b>座標フレーム</b><small>解決できないフレームや尺度なら取込を拒否</small></span></p>
        </section>
        {/* XC-120: grouping and tags are *proposals*. Nothing is applied until accepted, in one action
            for the whole import, and a rejected proposal is not offered again in this session. The
            review step listed only the format checks, so the state the specification names - proposed
            grouping and tags, nothing applied - had nowhere to appear. */}
        <section className="import-proposals" aria-label="提案された分類とタグ">
          <header><b>提案された分類とタグ</b><small>読み取れた内容からの提案です。受け入れるまで何も適用しません</small></header>
          <div className="import-proposal-group">
            <span className="import-proposal-kind">分類</span>
            <p>［選択したファイル群］を1つの設計スタディとしてまとめる（根拠：同一フォルダー・連続する更新日時）</p>
            <div>
              <button type="button" className={groupingAccepted === true ? 'active' : ''} aria-pressed={groupingAccepted === true} onClick={() => setGroupingAccepted(true)}>受け入れる</button>
              <button type="button" className={groupingAccepted === false ? 'active' : ''} aria-pressed={groupingAccepted === false} onClick={() => setGroupingAccepted(false)}>今回は使わない</button>
            </div>
          </div>
          <ul className="import-proposal-tags">
            {importTagProposals.filter((proposal) => !rejectedTags.includes(proposal.tag)).map((proposal) => (
              <li key={proposal.tag}>
                <label><input type="checkbox" checked={acceptedTags.includes(proposal.tag)} onChange={(event) => setAcceptedTags((current) => event.target.checked ? [...current, proposal.tag] : current.filter((tag) => tag !== proposal.tag))} /><b>{proposal.tag}</b><small>{proposal.basis}</small></label>
                <button type="button" aria-label={`${proposal.tag}の提案を今回は出さない`} onClick={() => { setRejectedTags((current) => [...current, proposal.tag]); setAcceptedTags((current) => current.filter((tag) => tag !== proposal.tag)) }}><X size={11} /></button>
              </li>
            ))}
            {importTagProposals.every((proposal) => rejectedTags.includes(proposal.tag)) && <li className="import-proposal-empty">提案はすべて却下しました。このセッションでは再提案しません。</li>}
          </ul>
          <footer>
            <button type="button" onClick={() => setAcceptedTags(importTagProposals.filter((proposal) => !rejectedTags.includes(proposal.tag)).map((proposal) => proposal.tag))}>すべて受け入れる</button>
            <small>{acceptedTags.length}件のタグを取込時に付与します。却下した提案はこのセッションでは再提案しません。</small>
          </footer>
        </section>
      </>}
      {step === 'importing' && <section className="workflow-progress" aria-live="polite"><CircleDashed size={22} /><span><b>構造と完全性を検証しています</b><small>キャンセルしても部分ケースを残しません</small></span><i><span /></i></section>}
      <footer>
        <button type="button" onClick={close}>キャンセル</button>
        {step === 'choose' && <button type="button" className="primary-button" onClick={() => setStep('review')}>ファイルを選択</button>}
        {step === 'review' && <button type="button" className="primary-button" onClick={() => setStep('importing')}>{acceptedTags.length > 0 || groupingAccepted ? '提案を受け入れて取込' : '提案を適用せず取込'}</button>}
      </footer>
    </DialogContent>
  </Dialog>
}

function WorkspaceHome({ variant, onOpenView, onImport }: { variant: string; onOpenView: () => void; onImport: () => void }) {
  const [homeQuery, setHomeQuery] = useState('')
  const [homeFilter, setHomeFilter] = useState('すべて')
  const [homeLayout, setHomeLayout] = useState<'grid' | 'list'>('grid')
  const [homeTags, setHomeTags] = useState<string[]>([])
  const [filterOpen, setFilterOpen] = useState(false)
  const workspaceItems = [['冷却ブラケット検討', '構造', 'ケース、テンプレート、パイプラインをまとめた設計検討', 'ローカル', '/thumbnails/bracket-1.png'], ['マニホールド流量検証', '流体', '複数条件を整理した流量検証ワークスペース', 'ローカル', '/thumbnails/manifold-1.png'], ['筐体熱解析', '熱', '熱解析結果とレポート構成を管理するワークスペース', 'ローカル', '/thumbnails/housing.png'], ['翼型空力検討', '流体', '翼型まわりの解析構成とレポートを整理するワークスペース', 'ローカル', '/thumbnails/wing.png']]
  const availableHomeTags = Array.from(new Set(workspaceItems.map(([, tag]) => tag)))
  const visibleWorkspaces = workspaceItems
    .filter(([name, tag, description]) => `${name} ${tag} ${description}`.includes(homeQuery.trim()))
    .filter(([, , , scope]) => homeFilter === 'すべて' || homeFilter === scope)
    .filter(([, tag]) => homeTags.length === 0 || homeTags.includes(tag))
  if (variant === 'first-run') {
    return (
      <div className="home-state">
        <span className="eyebrow">初回起動</span>
        <h1>最初のワークスペースを開く</h1>
        <p>サンプルで画面を確認するか、空のワークスペースへ解析結果をドロップします。</p>
        <div className="first-run-grid">
          <button className="choice-card featured" onClick={onOpenView}><Sparkles /><b>サンプルを開く</b><span>製品の操作だけを確認する一般化されたデータ</span></button>
          <button className="choice-card" onClick={onImport}><Upload /><b>空のワークスペース</b><span>結果ファイルをここへドロップ</span></button>
        </div>
        <small className="mock-note">モックアップ — 数値・解析結果は表示していません</small>
      </div>
    )
  }

  if (variant === 'importing') {
    return (
      <div className="home-state compact-state">
        <StatePanel tone="progress" title="データセットを読み込み中" detail="元ファイルは変更しません。読み込みはキャンセルできます。" />
        <div className="progress-card"><div><HardDrive /><span><b>bracket_result.vtu</b><small>形式と構造を検証中</small></span><button>キャンセル</button></div><i><span /></i></div>
      </div>
    )
  }

  if (variant === 'unreadable-file') {
    return (
      <div className="home-state compact-state">
        <StatePanel tone="error" title="ファイルを開けませんでした" detail="bracket_result.vtu — ヘッダーが途中で終了しています。ケースは作成されず、元ファイルも変更されていません。" />
        <button className="primary-button" onClick={onImport}>別のファイルを選ぶ</button>
      </div>
    )
  }

  return (
    <div className="home-page">
      <div className="workspace-list-toolbar"><div><h1>ワークスペース一覧</h1><p>解析プロジェクトを整理・検索して開きます。</p></div><div className="home-tools"><label><Search size={15} /><input value={homeQuery} onChange={(event) => setHomeQuery(event.target.value)} placeholder="名前・説明・タグで検索" /></label>
        <button type="button" className={homeTags.length > 0 ? 'active' : ''} aria-label="絞り込み" aria-expanded={filterOpen} aria-haspopup="listbox" onClick={() => setFilterOpen((open) => !open)}><SlidersHorizontal size={14} /></button>
        <Popover open={filterOpen} onOpenChange={setFilterOpen}>
          <PopoverContent className="template-tag-popover home-filter-popover">
            {/* The tags offered are the ones the listed workspaces actually carry; the picker never
                proposes a tag no card has. */}
            <header><b>タグで絞り込み</b>{homeTags.length > 0 && <Button variant="ghost" size="sm" type="button" onClick={() => setHomeTags([])}>すべて解除</Button>}</header>
            <ul role="listbox" aria-label="ワークスペースのタグ" aria-multiselectable="true">
              {availableHomeTags.map((tag) => (
                <li key={tag} role="option" aria-selected={homeTags.includes(tag)}>
                  <button type="button" onClick={() => setHomeTags((current) => current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag])}><span>{tag}</span>{homeTags.includes(tag) && <span aria-hidden="true">✓</span>}</button>
                </li>
              ))}
            </ul>
          </PopoverContent>
        </Popover>
        <div className="layout-switch"><button className={homeLayout === 'grid' ? 'active' : ''} aria-label="グリッド表示" aria-pressed={homeLayout === 'grid'} onClick={() => setHomeLayout('grid')}><LayoutGrid size={14} /></button><button className={homeLayout === 'list' ? 'active' : ''} aria-label="リスト表示" aria-pressed={homeLayout === 'list'} onClick={() => setHomeLayout('list')}><List size={14} /></button></div><button className="primary-button" onClick={onOpenView}><Plus size={15} /> 新規ワークスペース</button></div></div>
      {/* The chips name the scope each card actually carries. A `最近使用` chip stood here while every
          card reported `最終利用：—`, so it silently returned the whole list - a filter that quietly
          does nothing is the same defect as a value quietly substituted. */}
      <div className="workspace-filters">{(['すべて', 'ローカル', '共有'] as const).map((item) => <button className={homeFilter === item ? 'active' : ''} onClick={() => setHomeFilter(item)} key={item}>{item}</button>)}
        {homeTags.map((tag) => <button className="workspace-filter-chip" key={tag} onClick={() => setHomeTags((current) => current.filter((item) => item !== tag))} aria-label={`${tag}を解除`}>{tag}<X size={10} /></button>)}
      </div>
      <div className={`workspace-grid ${homeLayout === 'list' ? 'workspace-list-layout' : ''}`}>
        {visibleWorkspaces.map(([name, tag, description, scope, preview]) => (
          <button className="workspace-card" key={name} onClick={onOpenView}>
            <div className="workspace-visual"><Image src={preview} alt={`${name}の参照プレビュー`} fill sizes="(max-width: 640px) 100vw, 320px" /><span>参照モック画像・解析値未連携</span></div>
            <div><div className="workspace-card-heading"><span><small>ワークスペース</small><h2>{name}</h2></span><ArrowUpRight size={15} /></div><p>{description}</p><div className="workspace-tags"><span>{tag}</span><span>{scope}</span></div><footer><span>ケース数：—</span><span>最終利用：—</span></footer></div>
          </button>
        ))}
      </div>
      {visibleWorkspaces.length === 0 && <div className="centred-state"><Search size={24} /><h2>一致するワークスペースはありません</h2><p>{homeFilter === '共有' ? '共有スコープのワークスペースはこのモックアップにありません。' : '検索語または絞り込みを変更してください。'}</p></div>}
    </div>
  )
}

function LeftSidebar({ screen, width, setWidth, selectedCase, onSelectCase }: { screen: ScreenId; width: number; setWidth: React.Dispatch<React.SetStateAction<number>>; selectedCase: string; onSelectCase: (name: string) => void }) {
  const [caseQuery, setCaseQuery] = useState('')
  const chat = screen === 'chat'
  const [conversationQuery, setConversationQuery] = useState('')
  const conversations = ['結果の確認', 'レポート構成', '新しいチャット']
  const visibleConversations = conversations.filter((conversation) => conversation.includes(conversationQuery.trim()))
  return (
    <aside className="left-sidebar" id="left-sidebar">
      <div className="sidebar-scroll-content">
        {chat ? (
          <div className="conversation-list">
            <button className="conversation-new-button" type="button"><Plus size={14} /> 新しいチャット</button>
            <label className="conversation-search"><Search size={13} /><input value={conversationQuery} onChange={(event) => setConversationQuery(event.target.value)} placeholder="チャットを検索" /></label>
            {visibleConversations.map((conversation, index) => <button className={index === 0 ? 'active' : ''} key={conversation} type="button"><MessageSquareText size={14} /><span><b>{conversation}</b><small>{index === 0 ? 'たった今' : 'ローカル'}</small></span></button>)}
          </div>
        ) : (
          <>
            <WorkspaceSourceSections selectedCase={selectedCase} onSelectCase={onSelectCase} query={caseQuery} onQueryChange={setCaseQuery} />
          </>
        )}
      </div>
      <button
        className="dock-splitter sidebar-splitter-left"
        type="button"
        role="separator"
        aria-orientation="vertical"
        aria-controls="left-sidebar"
        aria-valuemin={160}
        aria-valuemax={360}
        aria-valuenow={width}
        aria-label="左サイドバーの幅を変更"
        onPointerDown={(event) => startHorizontalPanelResize(event, 'left', width, setWidth)}
        onKeyDown={(event) => resizeHorizontalPanelFromKey(event, 'left', setWidth)}
      />
    </aside>
  )
}

// The four origins a quantity may have (GL-016). Provenance travels with the value from the moment it
// exists, so it is a property of the row rather than a label applied at display time (INV-013).
type Provenance = 'declared' | 'dataset' | 'computed' | 'reference'

const provenanceLabels: Record<Provenance, { short: string; full: string }> = {
  declared: { short: '宣言', full: '人が宣言した値' },
  dataset: { short: 'データ', full: 'データセットから読み取った値' },
  computed: { short: '計算', full: '式で計算した値' },
  reference: { short: '資料', full: '参考資料から取得した値' },
}

function ProvenanceBadge({ kind }: { kind: Provenance }) {
  const label = provenanceLabels[kind]
  return <em className={`provenance-badge provenance-${kind}`} title={label.full} aria-label={label.full}>{label.short}</em>
}

// INV-014: a value is shown to the significant digits its stored precision supports, never padded.
// INV-013: it carries its provenance. XC-003: an undeclared unit is a marker, never a guessed unit.
function NumberCell({ value, unit, digits, provenance, expression }: { value: number | null; unit: string | null; digits: number; provenance: Provenance; expression?: string }) {
  const shown = value === null ? '—' : value.toPrecision(digits)
  return (
    <span className={`number-cell${value === null ? ' number-cell-missing' : ''}`} title={expression}>
      <b>{shown}</b>
      <small className={unit === null ? 'unit-undeclared' : undefined}>{unit === null ? '単位未宣言' : unit}</small>
      <ProvenanceBadge kind={provenance} />
      {value === null && <small className="missing-reason">欠損・置換なし</small>}
    </span>
  )
}

// A reference to a variable, embeddable in any input that accepts a quantity. Dragging it is how a
// quantity reaches a graph axis, a report table or an expression without retyping a value.
function QuantityChip({ name, provenance, unit }: { name: string; provenance: Provenance; unit: string | null }) {
  return (
    <span className="quantity-chip" draggable role="button" tabIndex={0} aria-label={`${name}（${provenanceLabels[provenance].full}）をドラッグして入力へ挿入`}>
      <Variable size={10} />
      <b>{name}</b>
      <small className={unit === null ? 'unit-undeclared' : undefined}>{unit ?? '単位未宣言'}</small>
      <ProvenanceBadge kind={provenance} />
    </span>
  )
}

// XC-104: every generated statement carries which of four kinds it is. This is a different taxonomy
// from a quantity's provenance (GL-016, above): that one says where a *number* came from, this one
// says what kind of *claim* a sentence is. The shared components table names both, and the mockup
// carried only the first - so Report and Chat showed generated prose with nothing attached.
type StatementKind = 'value' | 'comparison' | 'citation' | 'user'

const statementKindLabels: Record<StatementKind, { short: string; full: string }> = {
  value: { short: '値', full: 'データセットから読んだ値の記述' },
  comparison: { short: '比較', full: '計算による比較' },
  citation: { short: '引用', full: '参考資料からの引用' },
  user: { short: '記述', full: '利用者が述べた内容' },
}

function StatementKindBadge({ kind, source }: { kind: StatementKind; source: string }) {
  const label = statementKindLabels[kind]
  return <em className={`statement-kind-badge statement-kind-${kind}`} title={`${label.full}：${source}`} aria-label={`${label.full}：${source}`}>{label.short}<small>{source}</small></em>
}

const workspaceCases: { name: string; tags: string[]; resultAxis: 'time' | 'steady'; references: string[] }[] = [
  { name: '基準ケース', tags: ['基準'], resultAxis: 'time', references: ['ビュー「標準ビュー」', 'グラフ「ケース比較グラフ」', 'パイプライン「レポート生成フロー」の対象セット'] },
  { name: '板厚変更', tags: ['板厚', '要確認'], resultAxis: 'time', references: ['グラフ「ケース比較グラフ」', 'パイプライン「レポート生成フロー」の対象セット'] },
  { name: '荷重変更', tags: ['荷重'], resultAxis: 'time', references: ['パイプライン「レポート生成フロー」の対象セット'] },
  { name: '静荷重ケース', tags: ['定常'], resultAxis: 'steady', references: [] },
]

// XC-131: a steady @Case has no @Result axis at all. XC-160 already requires the playback overlay to be
// absent rather than disabled there, and the same follows for anything that offers motion.
const caseHasResultAxis = (name: string) => workspaceCases.find((item) => item.name === name)?.resultAxis !== 'steady'

const workspaceVariables: { name: string; value: number | null; unit: string | null; digits: number; provenance: Provenance; expression?: string }[] = [
  { name: '荷重', value: 1200, unit: null, digits: 4, provenance: 'declared' },
  { name: '応力場', value: null, unit: null, digits: 7, provenance: 'dataset' },
  { name: '安全率', value: 1.83, unit: '—', digits: 3, provenance: 'computed', expression: '= 降伏応力 / 最大応力' },
  { name: '設計許容応力', value: 235, unit: 'MPa', digits: 3, provenance: 'reference', expression: '出典：設計ノート・数値根拠には使用しない' },
  { name: '最大応力', value: null, unit: 'MPa', digits: 4, provenance: 'dataset' },
]

// The shared @Expression editor named in 11_ui.md: the names in scope, unit checking, and the error at
// the position it occurred. Graph, computed quantities and Pipeline each wrote a bare text input, so an
// expression could name a variable that does not exist and nothing said where.
type UnitSignature = Record<string, number>
type ExpressionToken = { kind: 'name' | 'number' | 'op'; text: string; index: number }
type ExpressionCheck = { status: 'ok' | 'error' | 'undeclared'; message: string; position: number; length: number }

function tokeniseExpression(text: string): ExpressionToken[] {
  const tokens: ExpressionToken[] = []
  const pattern = /([+\-*/()]|<=|>=|==|<|>)|([0-9]+(?:\.[0-9]+)?)|([^\s+\-*/()<>=]+)/g
  let match: RegExpExecArray | null
  while ((match = pattern.exec(text)) !== null) {
    if (match[1]) tokens.push({ kind: 'op', text: match[1], index: match.index })
    else if (match[2]) tokens.push({ kind: 'number', text: match[2], index: match.index })
    else tokens.push({ kind: 'name', text: match[3], index: match.index })
  }
  return tokens
}

function multiplySignature(left: UnitSignature, right: UnitSignature, sign: 1 | -1): UnitSignature {
  const result: UnitSignature = { ...left }
  for (const [unit, power] of Object.entries(right)) {
    const next = (result[unit] ?? 0) + sign * power
    if (next === 0) delete result[unit]
    else result[unit] = next
  }
  return result
}

function describeSignature(signature: UnitSignature) {
  const entries = Object.entries(signature)
  if (entries.length === 0) return '無次元'
  return entries.map(([unit, power]) => (power === 1 ? unit : `${unit}^${power}`)).join('·')
}

function sameSignature(left: UnitSignature, right: UnitSignature) {
  const keys = new Set([...Object.keys(left), ...Object.keys(right)])
  return Array.from(keys).every((key) => (left[key] ?? 0) === (right[key] ?? 0))
}

// XC-003 decides the hard case: an undeclared unit is not treated as dimensionless, because that would
// let `荷重 + 応力場` pass. The check stops and names which quantity has no declared unit.
function checkExpression(text: string): ExpressionCheck {
  const declared = new Map(workspaceVariables.map((variable) => [variable.name, variable.unit]))
  const tokens = tokeniseExpression(text)
  if (tokens.length === 0) return { status: 'error', message: '式が空です。', position: 0, length: 0 }
  const unknown = tokens.find((token) => token.kind === 'name' && !declared.has(token.text))
  if (unknown) return { status: 'error', message: `名前「${unknown.text}」はスコープにありません。`, position: unknown.index, length: unknown.text.length }
  const undeclared = tokens.find((token) => token.kind === 'name' && declared.get(token.text) === null)
  if (undeclared) return { status: 'undeclared', message: `「${undeclared.text}」の単位が未宣言のため、次元を検査できません。`, position: undeclared.index, length: undeclared.text.length }

  let term: UnitSignature = {}
  let pending: '*' | '/' | null = null
  let started = false
  let comparison: UnitSignature | null = null
  for (const token of tokens) {
    if (token.kind === 'op') {
      if (token.text === '*' || token.text === '/') { pending = token.text; continue }
      if (token.text === '(' || token.text === ')' || token.text === '+' || token.text === '-') { pending = null; continue }
      comparison = term
      term = {}
      started = false
      pending = null
      continue
    }
    const unit = token.kind === 'number' ? null : declared.get(token.text) ?? null
    const signature: UnitSignature = unit && unit !== '—' ? { [unit]: 1 } : {}
    if (!started) { term = signature; started = true; continue }
    term = multiplySignature(term, signature, pending === '/' ? -1 : 1)
    pending = null
  }
  if (comparison && !sameSignature(comparison, term)) {
    return { status: 'error', message: `比較の左右で次元が違います（${describeSignature(comparison)} と ${describeSignature(term)}）。`, position: 0, length: text.length }
  }
  return { status: 'ok', message: `次元を検査しました：${describeSignature(comparison ?? term)}`, position: 0, length: 0 }
}

function ExpressionEditor({ id, label, initial }: { id: string; label: string; initial: string }) {
  const [text, setText] = useState(initial)
  const check = checkExpression(text)
  const caret = check.status === 'ok' ? '' : `${' '.repeat(check.position)}${'^'.repeat(Math.max(1, check.length))}`
  return (
    <section className="expression-editor" aria-label={`${label}の式`}>
      <label htmlFor={`expression-${id}`}>{label}</label>
      <input id={`expression-${id}`} className="expression-input" value={text} spellCheck={false} aria-invalid={check.status !== 'ok'} aria-describedby={`expression-status-${id}`} onChange={(event) => setText(event.target.value)} />
      {check.status !== 'ok' && caret && <pre className="expression-caret" aria-hidden="true">{caret}</pre>}
      <p id={`expression-status-${id}`} className={`expression-status expression-status-${check.status}`} role="status">
        {check.status === 'ok' ? <ShieldCheck size={11} /> : <AlertTriangle size={11} />}
        <span>{check.status !== 'ok' && check.length > 0 ? `${check.position + 1}文字目：${check.message}` : check.message}</span>
      </p>
      <div className="expression-scope" aria-label="スコープにある名前">
        {workspaceVariables.map((variable) => (
          <button type="button" key={variable.name} onClick={() => setText((current) => `${current}${current && !current.endsWith(' ') ? ' ' : ''}${variable.name}`)}>
            <QuantityChip name={variable.name} provenance={variable.provenance} unit={variable.unit} />
          </button>
        ))}
      </div>
    </section>
  )
}

function WorkspaceSourceSections({ selectedCase, onSelectCase, query, onQueryChange }: { selectedCase: string; onSelectCase: (name: string) => void; query: string; onQueryChange: (query: string) => void }) {
  const [tagFilter, setTagFilter] = useState<string | null>(null)
  const [deleteCase, setDeleteCase] = useState<string | null>(null)
  const [notice, setNotice] = useState('')
  const tags = Array.from(new Set(workspaceCases.flatMap((item) => item.tags)))
  const needle = query.trim()
  const visibleCases = workspaceCases
    .filter((item) => !tagFilter || item.tags.includes(tagFilter))
    .filter((item) => !needle || item.name.includes(needle) || item.tags.some((tag) => tag.includes(needle)) || item.name === selectedCase)
  const references = workspaceCases.find((item) => item.name === deleteCase)?.references ?? []
  return (
    <>
      <SidebarSection title="ケース" icon={<FolderOpen size={13} />}>
        {/* XC-217: the field filters cases, so it lives inside the case section. Above the heading it
            sat over 変数 and 参考資料 as well, claiming a scope it does not have. */}
        <div className="permanent-search"><Search size={13} /><input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="ケースを検索・タグ絞込" aria-label="ケースを検索" /></div>
        {/* Tag filtering is a permanent control at this scale, not a dialogue (LIM-005). */}
        <div className="case-tag-filter" role="group" aria-label="タグで絞り込む">
          <Tag size={10} />
          {tags.map((tag) => <button className={tagFilter === tag ? 'active' : ''} key={tag} type="button" aria-pressed={tagFilter === tag} onClick={() => setTagFilter((current) => (current === tag ? null : tag))}>{tag}</button>)}
        </div>
        <button className="tree-row" type="button"><ChevronDown size={12} /><span><b>設計スタディ</b><small>{visibleCases.length}／{workspaceCases.length}ケース</small></span></button>
        {visibleCases.map((item) => (
          <div className={`tree-row nested case-row ${selectedCase === item.name ? 'active' : ''}`} key={item.name}>
            <button type="button" className="case-row-select" aria-pressed={selectedCase === item.name} onClick={() => onSelectCase(item.name)}>
              <Square size={10} />
              <span><b>{item.name}</b><small>{item.tags.join('・')}</small></span>
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild><button type="button" className="case-row-more" aria-label={`${item.name}の操作`}><MoreHorizontal size={13} /></button></DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onSelect={() => setNotice(`${item.name}の名前編集を開始しました`)}><Pencil size={12} />名前を変更</DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setNotice(`${item.name}にタグを付与しました`)}><Tag size={12} />タグを付与</DropdownMenuItem>
                {/* XC-062: deleting a @Case is confirmed by naming what changes and how many places. */}
                <DropdownMenuItem onSelect={() => setDeleteCase(item.name)}><Trash2 size={12} />削除</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        ))}
        {visibleCases.length === 0 && <p className="filter-note">「{needle}」に一致するケースはありません。<button type="button" className="filter-note-action" onClick={() => onQueryChange('')}>検索を解除</button></p>}
        {tagFilter && <p className="filter-note">タグ「{tagFilter}」で絞り込み中。選択中のケースは範囲外でも表示されます。</p>}
        {notice && <p className="filter-note" role="status">{notice}</p>}
      </SidebarSection>
      <SidebarSection title="変数" icon={<Variable size={13} />}>
        {/* One list holding declared values, fields read from data, computed quantities and values
            taken from reference material - each showing which it is (XC-088, INV-013). */}
        {workspaceVariables.map((variable) => (
          <div className="variable-row" key={variable.name} draggable aria-label={`${variable.name} をドラッグして入力へ挿入`}>
            {/* XC-207: a row that can be dragged looks like an object that can be picked up. Without a
                frame and a grip it read as text, and nothing on screen said the drag existed. */}
            <GripVertical size={11} className="variable-grip" aria-hidden="true" />
            <span>{variable.name}</span>
            <NumberCell value={variable.value} unit={variable.unit} digits={variable.digits} provenance={variable.provenance} expression={variable.expression} />
          </div>
        ))}
        <p className="filter-note">行はそのまま入力へドラッグできます。値の由来は表示のたびに付け直すのではなく、値と一緒に運ばれます。</p>
      </SidebarSection>
      <SidebarSection title="参考資料" icon={<FileText size={13} />}><button className="tree-row"><FileText size={11} /><span><b>設計ノート</b><small>数値根拠には使用しない</small></span></button></SidebarSection>
      <Dialog open={deleteCase !== null} onOpenChange={(open) => { if (!open) setDeleteCase(null) }}>
        <DialogOverlay className="modal-backdrop" />
        <DialogContent className="workflow-dialog compact-workflow-dialog">
          <header><span><small>削除の確認</small><b>{deleteCase}</b></span><button type="button" aria-label="ケース削除の確認を閉じる" onClick={() => setDeleteCase(null)}><X size={15} /></button></header>
          <p>このケースを参照している箇所は{references.length}件です。削除するとその参照は未解決になり、代替値では埋めません。</p>
          <ul className="confirmation-reference-list">{references.map((reference) => <li key={reference}>{reference}</li>)}</ul>
          <p className="workflow-trust-note"><ShieldCheck size={13} />ワークスペースの変更としてUndoできます。書き出し済みファイルは削除しません。</p>
          <footer><button type="button" onClick={() => setDeleteCase(null)}>キャンセル</button><button type="button" className="danger-button" onClick={() => { setNotice(`${deleteCase}を削除しました。参照${references.length}件は未解決として残ります`); setDeleteCase(null) }}>{references.length}件の参照ごと削除</button></footer>
        </DialogContent>
      </Dialog>
    </>
  )
}

function SidebarSection({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return <section className="sidebar-section"><h3>{icon}{title}<ChevronDown size={11} /></h3>{children}</section>
}

// XC-202: the View area holds two kinds of item. A comparison is not a second work area and not a
// mode of every View - it is an item that names a base View and varies one axis.
type WorkItemKind = 'single' | 'comparison'
type WorkItem = { name: string; tags: string[]; scope: 'ローカル' | '共有'; kind?: WorkItemKind; baseViewName?: string; usedBy?: string[] }

type WorkItemHeader = {
  title: string
  itemLabel: string
  detail: string
  createLabel: string
  items: WorkItem[]
}

const workItemHeaderByScreen: Partial<Record<ScreenId, WorkItemHeader>> = {
  simulation: { title: 'シミュレーション', itemLabel: 'シミュレーション', detail: '外部ソルバー実行定義・後続リリース', createLabel: '新規シミュレーション', items: [{ name: '基準シミュレーション', tags: ['基準'], scope: 'ローカル' }, { name: '材料条件スタディ', tags: ['材料'], scope: 'ローカル' }] },
  view: { title: 'ビュー', itemLabel: 'ビュー', detail: 'ワークスペース内のビューを編集中', createLabel: '新規ビュー', items: [
    { name: '標準ビュー', tags: ['標準'], scope: 'ローカル', kind: 'single', usedBy: ['比較「ケース比較」', '比較「時刻比較」', 'レポート「設計レビューレポート」'] },
    { name: 'ケース比較', tags: ['比較'], scope: 'ローカル', kind: 'comparison', baseViewName: '標準ビュー' },
    { name: '時刻比較', tags: ['比較'], scope: '共有', kind: 'comparison', baseViewName: '標準ビュー' },
  ] },
  graph: { title: 'グラフ', itemLabel: 'グラフ', detail: 'ワークスペース内のグラフを編集中', createLabel: '新規グラフ', items: [{ name: 'ケース比較グラフ', tags: ['比較'], scope: 'ローカル' }, { name: '結果推移グラフ', tags: ['推移'], scope: 'ローカル' }] },
  report: { title: 'レポート', itemLabel: 'レポート', detail: 'ワークスペース内のレポートを編集中', createLabel: '新規レポート', items: [{ name: '設計レビューレポート', tags: ['レビュー'], scope: 'ローカル' }, { name: '要約レポート', tags: ['要約'], scope: '共有' }] },
  pipeline: { title: '自動化', itemLabel: 'パイプライン', detail: '結果処理と成果物生成を自動化', createLabel: '新規パイプライン', items: [{ name: 'レポート生成フロー', tags: ['レポート'], scope: 'ローカル' }, { name: 'ケース比較フロー', tags: ['比較'], scope: 'ローカル' }] },
}

function WorkAreaBar({ screen, itemListOpen, onItemListOpenChange, itemListQuery, onItemListQueryChange, itemListLayout, onItemListLayoutChange, itemListScope, onItemListScopeChange, openItems, onOpenItemChange, splitPanes, onSplitPanesChange, cameraSync, onCameraSyncChange, onPromoteSplit, layoutControl, comparisonColumns, onComparisonColumnsChange }: { screen: ScreenId; itemListOpen: boolean; onItemListOpenChange: (open: boolean) => void; itemListQuery: string; onItemListQueryChange: (query: string) => void; itemListLayout: 'grid' | 'list'; onItemListLayoutChange: (layout: 'grid' | 'list') => void; itemListScope: string; onItemListScopeChange: (scope: string) => void; openItems: Partial<Record<ScreenId, string>>; onOpenItemChange: (screen: ScreenId, item: string) => void; splitPanes: number; onSplitPanesChange: (panes: number) => void; cameraSync: boolean; onCameraSyncChange: (sync: boolean) => void; onPromoteSplit: () => void; layoutControl: { kind: 'split' } | { kind: 'comparison'; members: number } | null; comparisonColumns: 'auto' | number; onComparisonColumnsChange: (columns: 'auto' | number) => void }) {
  const itemHeader = workItemHeaderByScreen[screen]
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [previewIndex, setPreviewIndex] = useState<number | null>(null)
  const [previewTop, setPreviewTop] = useState<number | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [createKind, setCreateKind] = useState<WorkItemKind>('single')
  const [deleteItem, setDeleteItem] = useState<string | null>(null)
  const [templateItem, setTemplateItem] = useState<string | null>(null)
  const [templateScope, setTemplateScope] = useState<'workspace' | 'shared'>('workspace')
  const [itemNotice, setItemNotice] = useState('')

  if (!itemHeader) {
    // Network and audit has no saved workspace item to switch between. This bar printed the screen
    // name twice - once as the eyebrow and once as the title - which said nothing the second time.
    return <div className="work-area-bar"><div className="work-area-static"><span className="eyebrow">ワークスペース権限</span><b>{screenNames[screen]}</b><small>このワークスペースから外部へ出せる内容と、実際に出た記録</small></div></div>
  }
  const selectedItem = openItems[screen] ?? itemHeader.items[0].name
  const selectedWorkItem = itemHeader.items.find((item) => item.name === selectedItem) ?? itemHeader.items[0]
  const visibleItems = itemHeader.items.filter((item) => item.name.includes(query.trim()))
  const deleteItemReferences = itemHeader.items.find((item) => item.name === deleteItem)?.usedBy ?? []

  const selectItem = (item: string) => {
    onOpenItemChange(screen, item)
    setOpen(false)
    setQuery('')
    setPreviewIndex(null)
    setPreviewTop(null)
  }

  const showPreview = (event: React.SyntheticEvent<HTMLDivElement>, index: number) => {
    const option = event.currentTarget
    const popover = option.closest<HTMLElement>('.work-item-popover')
    if (!popover) return
    const optionRect = option.getBoundingClientRect()
    const popoverRect = popover.getBoundingClientRect()
    setPreviewIndex(index)
    setPreviewTop(optionRect.top + optionRect.height / 2 - popoverRect.top)
  }

  return (
    <div className={`work-area-bar ${itemListOpen ? 'work-area-list-mode' : ''}`}>
      <div className="work-area-mode-switch" role="tablist" aria-label={`${itemHeader.itemLabel}の表示モード`}>
        <Button variant="ghost" size="sm" role="tab" aria-selected={!itemListOpen} className={!itemListOpen ? 'active' : ''} onClick={() => onItemListOpenChange(false)}><Pencil size={12} aria-hidden="true" /> 編集</Button>
        <Button variant="ghost" size="sm" role="tab" aria-selected={itemListOpen} className={itemListOpen ? 'active' : ''} onClick={() => onItemListOpenChange(true)}><List size={12} aria-hidden="true" /> 一覧</Button>
      </div>
      {!itemListOpen && <div className="work-item-switcher">
        <button
          className="work-item-selector"
          type="button"
          aria-label={`${itemHeader.itemLabel}を選択`}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={`work-item-list-${screen}`}
          onClick={() => setOpen((current) => !current)}
        >
          <span className="work-item-selector-copy"><small className="work-item-selector-kind">{selectedWorkItem.kind === 'comparison' ? '比較' : itemHeader.itemLabel}</small><b>{selectedItem}</b>{selectedWorkItem.kind === 'comparison' && <em className="work-item-base">基準：{selectedWorkItem.baseViewName}</em>}</span>
          <ChevronDown size={14} aria-hidden="true" />
        </button>
        {open && (
          <section className="work-item-popover" aria-label={`${itemHeader.itemLabel}一覧`}>
            <label><Search size={13} aria-hidden="true" /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`${itemHeader.itemLabel}を検索`} /></label>
            <div id={`work-item-list-${screen}`} role="listbox" aria-label={`${itemHeader.itemLabel}一覧`} onMouseLeave={() => { setPreviewIndex(null); setPreviewTop(null) }}>
              {visibleItems.map((entry, index) => {
                const item = entry.name
                return (
                <div className={`work-item-option ${selectedItem === item ? 'active' : ''}`} key={item} onMouseEnter={(event) => showPreview(event, index)} onFocus={(event) => showPreview(event, index)}>
                  <button type="button" role="option" aria-selected={selectedItem === item} onClick={() => selectItem(item)}><span>{item}{entry.kind === 'comparison' && <em className="work-item-kind-badge"><Columns3 size={9} />比較</em>}</span><small>{entry.kind === 'comparison' ? `基準ビュー：${entry.baseViewName}` : selectedItem === item ? '編集中' : 'ワークスペース項目'}</small></button>
                  <DropdownMenu><DropdownMenuTrigger asChild><button type="button" className="work-item-more" aria-label={`${item}の操作`}><MoreHorizontal size={14} /></button></DropdownMenuTrigger><DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => setItemNotice(`${item}の名前編集を開始しました`)}><Pencil size={12} />名前を変更</DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => setItemNotice(`${item}を独立した複製として作成しました`)}><Copy size={12} />複製</DropdownMenuItem>
                    {/* A secondary item command, never permanent header chrome (XC-148). Saving as a
                        template copies the definition into a chosen scope; it creates no live link,
                        so editing the template later never changes this item (XC-109). */}
                    {screen !== 'simulation' && screen !== 'pipeline' && <DropdownMenuItem onSelect={() => setTemplateItem(item)}><LayoutTemplate size={12} />テンプレートとして保存</DropdownMenuItem>}
                    <DropdownMenuItem onSelect={() => setDeleteItem(item)}><Trash2 size={12} />削除</DropdownMenuItem>
                  </DropdownMenuContent></DropdownMenu>
                </div>
                )
              })}
              {visibleItems.length === 0 && <p>一致する{itemHeader.itemLabel}はありません。</p>}
            </div>
            {open && previewIndex !== null && (screen === 'view' || screen === 'graph' || screen === 'report') && <div className="work-item-popover-preview" style={{ top: `${previewTop ?? 48}px` }}><WorkItemPreview screen={screen} index={previewIndex} /></div>}
          </section>
        )}
      </div>}
      {itemListOpen && <div className="work-area-list-tools">
        <div className="work-area-list-search"><Search size={14} aria-hidden="true" /><Input value={itemListQuery} onChange={(event) => onItemListQueryChange(event.target.value)} className="work-area-list-search-input" placeholder={`${itemHeader.itemLabel}・説明・タグで検索`} aria-label={`${itemHeader.itemLabel}を検索`} /></div>
        <div className="work-area-list-scope" role="group" aria-label={`${itemHeader.itemLabel}の保存範囲`}>
          {['すべて', 'ローカル', '共有'].map((value) => <button type="button" key={value} className={itemListScope === value ? 'active' : ''} aria-pressed={itemListScope === value} onClick={() => onItemListScopeChange(value)}>{value}</button>)}
        </div>
        <div className="layout-switch"><Button variant="ghost" size="icon" className={itemListLayout === 'grid' ? 'active' : ''} aria-pressed={itemListLayout === 'grid'} aria-label="グリッド表示" onClick={() => onItemListLayoutChange('grid')}><LayoutGrid size={14} /></Button><Button variant="ghost" size="icon" className={itemListLayout === 'list' ? 'active' : ''} aria-pressed={itemListLayout === 'list'} aria-label="リスト表示" onClick={() => onItemListLayoutChange('list')}><List size={14} /></Button></div>
      </div>}
      {/* XC-206: one control, in the area bar, for one question - how this canvas is laid out. It never
          disappears between the two kinds of item; what it sets is what each kind has. For a @View that
          is the session split; for a @Comparison the panes are its members, so it is the column count
          the members wrap at. The 3D canvas carries neither (XC-204). */}
      {layoutControl && !itemListOpen && <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={`work-area-split ${layoutControl.kind === 'split' ? (splitPanes > 1 ? 'active' : '') : 'active'}`} aria-label="画面レイアウト" aria-haspopup="menu"><Columns3 size={14} />{layoutControl.kind === 'split'
            ? splitPanes > 1 && <span>{splitPanes}画面</span>
            : <span>{comparisonColumns === 'auto' ? '自動' : `${comparisonColumns} 列`}</span>}</button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {layoutControl.kind === 'split' ? <>
            {[1, 2, 3, 4].map((count) => (
              <DropdownMenuItem key={count} onSelect={() => onSplitPanesChange(count)}>{splitPanes === count ? <Check size={12} /> : <span className="menu-check-space" />}{count}画面</DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem disabled={splitPanes === 1} onSelect={() => onCameraSyncChange(!cameraSync)}>{cameraSync ? <Check size={12} /> : <span className="menu-check-space" />}カメラ同期</DropdownMenuItem>
            {/* XC-209: the split's two facts that are not repeated anywhere else - that it is thrown
                away, and the one action that turns it into something that is not. */}
            {splitPanes > 1 && <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={onPromoteSplit}><Save size={12} />この比較を保存</DropdownMenuItem>
              <div className="menu-note">この分割は見ながら比べるための一時的な状態です。保存も書き出しもされません。並べた図を成果物にする場合は「この比較を保存」から比較項目を作ります。</div>
            </>}
          </> : <>
            <div className="menu-note">ペイン数はメンバー数（{layoutControl.members}件）です。列数だけを選び、行数はそこから決まります。</div>
            {(['auto', 1, 2, 3, 4] as const).map((value) => (
              <DropdownMenuItem key={String(value)} onSelect={() => onComparisonColumnsChange(value)}>{comparisonColumns === value ? <Check size={12} /> : <span className="menu-check-space" />}{value === 'auto' ? `自動（${comparisonGridColumns(layoutControl.members, 'auto')} 列）` : `${value} 列`}</DropdownMenuItem>
            ))}
          </>}
        </DropdownMenuContent>
      </DropdownMenu>}
      <Button className="primary-button" aria-label={`${itemHeader.createLabel}を作成`} onClick={() => setCreateOpen(true)}><Plus size={14} /> {itemHeader.createLabel}</Button>
      {itemNotice && <span className="work-item-notice" role="status">{itemNotice}</span>}
      <Dialog open={templateItem !== null} onOpenChange={(open) => { if (!open) setTemplateItem(null) }}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog"><header><span><small>{itemHeader.itemLabel}</small><b>テンプレートとして保存</b></span><button type="button" aria-label="テンプレート保存を閉じる" onClick={() => setTemplateItem(null)}><X size={15} /></button></header><div className="settings-fields"><label><span>名前</span><input defaultValue={`${templateItem ?? ''}のテンプレート`} /></label><label><span>保存先スコープ</span><Select value={templateScope} onValueChange={(value) => setTemplateScope(value as 'workspace' | 'shared')}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="workspace">このワークスペース</SelectItem><SelectItem value="shared">共有</SelectItem></SelectContent></Select></label></div><p className="workflow-trust-note"><ShieldCheck size={13} />定義を新しいテンプレート版として複写します。生きたリンクは作られないため、後からテンプレートを編集しても「{templateItem}」は変わりません。</p><footer><button type="button" onClick={() => setTemplateItem(null)}>戻る</button><button type="button" className="primary-button" onClick={() => { setItemNotice(`${templateItem}を${templateScope === 'shared' ? '共有' : 'このワークスペース'}のテンプレートとして保存しました`); setTemplateItem(null) }}>保存</button></footer></DialogContent></Dialog>
      <Dialog open={createOpen} onOpenChange={setCreateOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog">
        <header><span><small>{itemHeader.itemLabel}</small><b>{itemHeader.createLabel}</b></span><button type="button" aria-label="新規作成を閉じる" onClick={() => setCreateOpen(false)}><X size={15} /></button></header>
        {/* XC-202: the View area holds two kinds. Choosing here is what makes a comparison an item
            rather than a mode every View has to carry. */}
        {screen === 'view' && <div className="creation-kind" role="radiogroup" aria-label="作成する種別">
          {([['single', '単一ビュー', '1ケース・1カメラ・1結果位置の絵'], ['comparison', '比較', '基準ビューを1本の軸で振って並べる']] as const).map(([kind, label, detail]) => (
            <label key={kind} className={createKind === kind ? 'active' : ''}>
              <input type="radio" name="create-kind" checked={createKind === kind} onChange={() => setCreateKind(kind)} />
              <span><b>{label}</b><small>{detail}</small></span>
            </label>
          ))}
        </div>}
        {screen === 'view' && createKind === 'comparison'
          ? <>
              <div className="settings-fields">
                <label><span>基準ビュー</span><Select defaultValue="standard"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{itemHeader.items.filter((item) => item.kind !== 'comparison').map((item) => <SelectItem value="standard" key={item.name}>{item.name}</SelectItem>)}</SelectContent></Select></label>
                <label><span>変える軸</span><Select defaultValue="case"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{(Object.keys(comparisonAxisLabels) as ComparisonAxis[]).map((axis) => <SelectItem value={axis} key={axis}>{comparisonAxisLabels[axis]}</SelectItem>)}</SelectContent></Select></label>
              </div>
              <p className="workflow-trust-note"><ShieldCheck size={13} />比較は自前のマテリアル・照明・背景を持ちません。基準ビューへの生きた参照なので、基準ビューを直すと全ペインが変わります。</p>
              <footer><button type="button" onClick={() => setCreateOpen(false)}>キャンセル</button><button type="button" className="primary-button" onClick={() => { setItemNotice('比較を作成しました。基準ビューを参照します'); setCreateOpen(false) }}>比較を作成</button></footer>
            </>
          : <>
              <div className="creation-options">
                <button type="button" onClick={() => { setItemNotice(`空の${itemHeader.itemLabel}を作成しました`); setCreateOpen(false) }}><Plus size={18} /><span><b>空から作成</b><small>独立したワークスペース項目</small></span></button>
                {screen !== 'simulation' && <button type="button" onClick={() => { setItemNotice('テンプレートの解決確認へ進みます'); setCreateOpen(false) }}><LayoutTemplate size={18} /><span><b>テンプレートから作成</b><small>解決結果を確認してから作成</small></span></button>}
              </div>
              {screen === 'simulation' && <p className="workflow-trust-note"><AlertTriangle size={13} />定義は保存できますが、r1では外部ソルバーを実行しません。</p>}
            </>}
      </DialogContent></Dialog>
      <Dialog open={Boolean(deleteItem)} onOpenChange={(open) => !open && setDeleteItem(null)}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog"><header><span><small>削除の確認</small><b>{deleteItem}</b></span><button type="button" aria-label="削除確認を閉じる" onClick={() => setDeleteItem(null)}><X size={15} /></button></header><p>この{itemHeader.itemLabel}だけを削除します。テンプレートや出力済みファイルは削除しません。</p>{deleteItemReferences.length > 0 && <><p className="workflow-trust-note blocked"><AlertTriangle size={13} />この{itemHeader.itemLabel}を参照している項目が{deleteItemReferences.length}件あります。削除すると未解決になり、別の{itemHeader.itemLabel}へ付け替えることはしません。</p><ul className="confirmation-reference-list">{deleteItemReferences.map((reference) => <li key={reference}>{reference}</li>)}</ul></>}<footer><button type="button" onClick={() => setDeleteItem(null)}>キャンセル</button><button type="button" className="danger-button" onClick={() => { setItemNotice(`${deleteItem}を削除しました`); setDeleteItem(null) }}>削除</button></footer></DialogContent></Dialog>
    </div>
  )
}

// The `一覧` catalogue. The shared title bar owns search, tag filtering and the grid/list switch
// (XC-149); this surface owned a *second* grid/list switch while the title-bar pair was decorative,
// so the visible control and the working control were different buttons.
function WorkItemLibrary({ screen, query, layout, scope, onSelect }: { screen: ScreenId; query: string; layout: 'grid' | 'list'; scope: string; onSelect: () => void }) {
  const itemHeader = workItemHeaderByScreen[screen]
  if (!itemHeader) return null
  const visibleItems = itemHeader.items
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => item.name.includes(query.trim()))
    .filter(({ item }) => scope === 'すべて' || item.scope === scope)
  return <section className="home-page work-item-library" aria-label={`${itemHeader.itemLabel}一覧`}>
    <div className={`workspace-grid ${layout === 'list' ? 'workspace-list-layout' : ''}`}>{visibleItems.map(({ item, index }) => <button type="button" className="workspace-card" key={item.name} onClick={onSelect}><WorkItemCatalogPreview screen={screen} index={index} label={itemHeader.itemLabel} /><div><div className="workspace-card-heading"><span><small>{item.kind === 'comparison' ? '比較' : itemHeader.itemLabel}</small><h2>{item.name}</h2></span><ArrowUpRight size={15} /></div><p>{item.kind === 'comparison' ? `基準ビュー「${item.baseViewName}」を1本の軸で振って並べます。表示設定は基準ビューから借ります。` : `ワークスペースに保存された${itemHeader.itemLabel}の設定と表示内容。`}</p><div className="workspace-tags">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}<span>{item.scope}</span></div><footer><span>{index === 0 ? '現在使用中' : '保存済み'}</span><span>最終利用：—</span></footer></div></button>)}</div>
    {visibleItems.length === 0 && <div className="centred-state"><Search size={24} /><h2>一致する{itemHeader.itemLabel}はありません</h2><p>検索語または絞り込みを変更してください。</p></div>}
  </section>
}

function WorkItemCatalogPreview({ screen, index, label }: { screen: ScreenId; index: number; label: string }) {
  if (screen === 'view') {
    const image = index % 2 === 0 ? '/thumbnails/bracket-1.png' : '/thumbnails/manifold-1.png'
    return <div className="workspace-visual"><Image src={image} alt={`${label}のプレビュー`} fill sizes="(max-width: 640px) 100vw, 320px" /><span>表示モック・解析値なし</span></div>
  }
  if (screen === 'graph') return <div className="workspace-visual catalog-graph-preview"><svg viewBox="0 0 320 150" aria-hidden="true"><path d="M24 124H300M24 124V18" /><polyline points={index % 2 === 0 ? '28,112 92,88 148,98 208,48 292,64' : '28,102 86,110 146,68 208,78 292,34'} /><circle cx="208" cy={index % 2 === 0 ? '48' : '78'} r="5" /></svg><span>グラフ・静止プレビュー</span></div>
  if (screen === 'report') return <div className="workspace-visual catalog-report-preview" aria-hidden="true"><div className="catalog-report-page"><i /><b /><span /><span /><div><em /><em /></div></div><span>レポート・レイアウトプレビュー</span></div>
  return <div className={`workspace-visual catalog-flow-preview catalog-${screen}`} aria-hidden="true"><div><i /><i /><i /></div><span>{label}・保存済み</span></div>
}

function WorkItemPreview({ screen, index }: { screen: ScreenId; index: number }) {
  if (screen !== 'view' && screen !== 'graph' && screen !== 'report') return null
  if (screen === 'view') {
    const image = index % 2 === 0 ? '/thumbnails/bracket-1.png' : '/thumbnails/manifold-1.png'
    return <div className="work-item-preview-content work-item-preview-image" aria-hidden="true"><Image src={image} alt="" fill sizes="160px" /></div>
  }
  if (screen === 'graph') return <div className="work-item-preview-content work-item-preview-chart" aria-hidden="true"><svg viewBox="0 0 160 72"><path d="M8 58H152M8 58V10" /><polyline points={index % 2 === 0 ? '10,52 42,41 72,46 103,22 150,29' : '10,45 40,48 72,29 104,34 150,14'} /><circle cx="103" cy={index % 2 === 0 ? "22" : "34"} r="3" /></svg></div>
  return <div className="work-item-preview-content work-item-preview-report" aria-hidden="true"><div className="report-preview-heading" /><div className="report-preview-lines"><i /><i /><i /><i /></div><div className="report-preview-columns"><span /><span /></div></div>
}

type LibrarySource = 'sample' | 'original'
type LibrarySort = 'default' | 'name-asc' | 'name-desc'
type LibraryShelfMode = 'collapsed' | 'one-row' | 'expanded'
type LibraryItem = { id: string; name: string; detail: string; tags: string[]; tone: string; thumbnail?: string; thumbnailMissing?: boolean; scope?: LibraryScope }

const librarySamples: Record<string, LibraryItem[]> = {
  template: [
    { id: 'technical-review', name: '技術レビュー', detail: '標準構成', tags: ['レビュー', '標準'], tone: 'blue' },
    { id: 'comparison', name: 'ケース比較', detail: '比較構成', tags: ['比較', '標準'], tone: 'cyan' },
    { id: 'presentation', name: 'プレゼンテーション', detail: '説明用構成', tags: ['発表', '注釈'], tone: 'violet' },
    { id: 'minimal', name: 'ミニマル', detail: '簡潔な構成', tags: ['簡潔'], tone: 'neutral' },
    { id: 'print', name: '印刷向け', detail: '明背景構成', tags: ['印刷', '明背景'], tone: 'warm' },
  ],
  objects: [
    { id: 'annotation', name: '注釈セット', detail: 'オブジェクトアセット', tags: ['注釈', '標準'], tone: 'blue' },
    { id: 'dimensions', name: '寸法セット', detail: 'オブジェクトアセット', tags: ['寸法', 'レビュー'], tone: 'cyan' },
    { id: 'section-guide', name: '断面ガイド', detail: 'オブジェクトアセット', tags: ['断面'], tone: 'violet' },
    { id: 'vector-guide', name: 'ベクトルガイド', detail: 'オブジェクトアセット', tags: ['ベクトル'], tone: 'warm' },
  ],
  materials: [
    { id: 'brushed-steel', name: 'ブラッシュドスチール', detail: '表面表現', tags: ['金属', '標準'], tone: 'neutral', thumbnail: '/materials/brushed-steel.png' },
    { id: 'stress-steel', name: 'スチール＋応力コンター', detail: '解析データ依存・サンプルデータ', tags: ['応力', 'MaterialX'], tone: 'blue', thumbnail: '/materials/result-sample.png' },
    { id: 'technical-blue', name: 'テクニカルブルー', detail: '表面表現', tags: ['寒色', '標準'], tone: 'blue', thumbnail: '/materials/technical-blue.png' },
    { id: 'neutral-gray', name: 'ニュートラルグレー', detail: '表面表現', tags: ['中立', 'レビュー'], tone: 'neutral', thumbnail: '/materials/neutral-gray.png' },
    { id: 'inspection-orange', name: 'インスペクション', detail: '表面表現', tags: ['暖色', '強調'], tone: 'warm', thumbnail: '/materials/inspection-orange.png' },
    { id: 'transparent', name: '半透明', detail: '表面表現', tags: ['透過', '内部確認'], tone: 'cyan', thumbnail: '/materials/translucent-cyan.png' },
  ],
  background: [
    { id: 'studio-light', name: 'スタジオライト', detail: '明背景', tags: ['明背景', '標準'], tone: 'neutral' },
    { id: 'studio-dark', name: 'スタジオダーク', detail: '暗背景', tags: ['暗背景', '高コントラスト'], tone: 'blue' },
    { id: 'presentation-bg', name: 'プレゼンテーション', detail: '説明用背景', tags: ['発表'], tone: 'violet' },
  ],
  fonts: [
    { id: 'technical-sans', name: 'テクニカル Sans', detail: '日本語対応', tags: ['日本語', '標準'], tone: 'blue' },
    { id: 'compact-sans', name: 'コンパクト Sans', detail: '省スペース', tags: ['日本語', '簡潔'], tone: 'neutral' },
    { id: 'report-serif', name: 'レポート Serif', detail: '本文向け', tags: ['文書', '印刷'], tone: 'warm' },
  ],
  style: [
    { id: 'engineering-blue', name: 'エンジニアリング', detail: '標準配色', tags: ['標準', '寒色'], tone: 'blue' },
    { id: 'high-contrast', name: '高コントラスト', detail: '識別性重視', tags: ['高コントラスト'], tone: 'violet' },
    { id: 'monochrome', name: 'モノクローム', detail: '印刷向け', tags: ['印刷', '中立'], tone: 'neutral' },
  ],
  layout: [
    { id: 'single-column', name: '1カラム', detail: '本文中心', tags: ['標準', '文書'], tone: 'neutral' },
    { id: 'two-column', name: '2カラム', detail: '比較向け', tags: ['比較', '文書'], tone: 'blue' },
    { id: 'summary-page', name: '要約ページ', detail: '1ページ構成', tags: ['簡潔', 'レビュー'], tone: 'warm' },
  ],
}

// `オリジナル` was an empty branch: the source tab switched and the shelf showed the empty state for
// every category, so the scope labelling 11_ui.md requires - `このワークスペース` or `共有`, kept out
// of the サンプル/オリジナル choice - had nothing to label. GL-019: dragging between the two copies.
type LibraryScope = 'workspace' | 'shared'
const libraryScopeLabels: Record<LibraryScope, string> = { workspace: 'このワークスペース', shared: '共有' }

const libraryOriginals: Record<string, LibraryItem[]> = {
  template: [
    { id: 'own-review', name: '社内レビュー', detail: '保存済みビュー構成', tags: ['レビュー'], tone: 'blue', scope: 'workspace' },
    { id: 'own-shared-review', name: '部門標準', detail: '共有ライブラリの構成', tags: ['標準'], tone: 'violet', scope: 'shared' },
  ],
  objects: [
    { id: 'own-callouts', name: '注釈セット・改', detail: 'オブジェクトアセット', tags: ['注釈'], tone: 'cyan', scope: 'workspace' },
  ],
  materials: [
    { id: 'own-steel', name: '社内スチール', detail: '表面表現', tags: ['金属'], tone: 'neutral', scope: 'workspace', thumbnail: '/materials/brushed-steel.png' },
    // AC-076: a thumbnail that does not exist is named as missing. It never borrows another Asset's
    // sphere, and never falls back to a plausible generic material.
    { id: 'own-unrendered', name: '試作マテリアル', detail: '表面表現', tags: ['試作'], tone: 'neutral', scope: 'workspace', thumbnailMissing: true },
  ],
  background: [
    { id: 'own-室内', name: '社内スタジオ', detail: '明背景', tags: ['明背景'], tone: 'neutral', scope: 'shared' },
  ],
  fonts: [
    { id: 'own-font', name: '社内書体設定', detail: '日本語対応', tags: ['日本語'], tone: 'blue', scope: 'shared' },
  ],
  style: [
    { id: 'own-style', name: '部門配色', detail: '標準配色', tags: ['標準'], tone: 'violet', scope: 'shared' },
  ],
  layout: [
    { id: 'own-layout', name: '報告書レイアウト', detail: '2カラム', tags: ['文書'], tone: 'blue', scope: 'workspace' },
  ],
}

const librarySortLabels: Record<LibrarySort, string> = {
  default: '既定順',
  'name-asc': '名前：昇順',
  'name-desc': '名前：降順',
}

function AssetLibraryShelf({ screen, variant }: { screen: ScreenId; variant: string }) {
  const categories = libraryCategories[screen]
  const initialMode: LibraryShelfMode = variant === 'library-expanded' ? 'expanded' : variant === 'library-collapsed' || !variant.startsWith('library-') ? 'collapsed' : 'one-row'
  const [mode, setMode] = useState<LibraryShelfMode>(initialMode)
  const [shelfHeight, setShelfHeight] = useState(340)
  const [shelfMaximum, setShelfMaximum] = useState(560)
  const [category, setCategory] = useState(categories?.[0] ?? 'template')
  const [source, setSource] = useState<LibrarySource>('sample')
  const [query, setQuery] = useState(variant === 'library-searching' ? '技術' : '')
  const [tagQuery, setTagQuery] = useState('')
  const [tagPanelOpen, setTagPanelOpen] = useState(false)
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [sortPanelOpen, setSortPanelOpen] = useState(false)
  const [scopeFilter, setScopeFilter] = useState<LibraryScope | 'all'>('all')
  const [sort, setSort] = useState<LibrarySort>('default')
  const [selectedItem, setSelectedItem] = useState<string | null>(variant === 'library-selected' ? 'technical-review' : null)
  const [applyOpen, setApplyOpen] = useState(false)
  const [applyComplete, setApplyComplete] = useState(false)
  const [materialTarget, setMaterialTarget] = useState<'object' | 'part' | 'elements'>('object')
  if (!categories) return null

  const meta = libraryCategoryMeta[category]
  const label = meta.label
  const Icon = meta.icon
  const samples = librarySamples[category] ?? []
  const originals = libraryOriginals[category] ?? []
  const sourceItems = source === 'sample' ? samples : originals
  const libraryTagSuggestions = Array.from(new Set(sourceItems.flatMap((item) => item.tags))).sort((a, b) => a.localeCompare(b, 'ja'))
  const sourceLabel = source === 'sample' ? 'サンプル' : 'オリジナル'
  const hasFilter = query.trim().length > 0 || selectedTags.length > 0 || (source === 'original' && scopeFilter !== 'all')
  const visibleTags = libraryTagSuggestions.filter((tag) => tag.toLocaleLowerCase('ja').includes(tagQuery.trim().toLocaleLowerCase('ja')))
  const normalizedQuery = query.trim().toLocaleLowerCase('ja')
  const visibleItems = sourceItems
    .filter((item) => source === 'sample' || scopeFilter === 'all' || item.scope === scopeFilter)
    .filter((item) => !normalizedQuery || `${item.name} ${item.detail} ${item.tags.join(' ')}`.toLocaleLowerCase('ja').includes(normalizedQuery))
    .filter((item) => selectedTags.every((tag) => item.tags.includes(tag)))
    .sort((left, right) => sort === 'name-asc' ? left.name.localeCompare(right.name, 'ja') : sort === 'name-desc' ? right.name.localeCompare(left.name, 'ja') : 0)

  const toggleTag = (tag: string) => {
    setSelectedTags((current) => current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag])
  }

  return (
    <section className={`asset-library-shelf library-shelf-${mode} ${selectedItem ? 'library-has-selection' : ''} ${variant === 'library-narrow' ? 'library-shelf-narrow' : ''}`} id="asset-library-shelf" aria-label="素材ライブラリ" style={mode === 'expanded' ? { height: `${shelfHeight}px` } : undefined}>
      <button
        className="dock-splitter library-splitter"
        type="button"
        role="separator"
        aria-orientation="horizontal"
        aria-controls="asset-library-shelf"
        aria-valuemin={169}
        aria-valuemax={shelfMaximum}
        aria-valuenow={mode === 'expanded' ? shelfHeight : 169}
        aria-label="素材ライブラリの高さを変更"
        onPointerDown={(event) => startLibraryResize(event, setShelfHeight, setShelfMaximum, () => setMode('expanded'))}
        onKeyDown={(event) => {
          if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return
          event.preventDefault()
          const shelf = event.currentTarget.closest<HTMLElement>('.asset-library-shelf')
          if (!shelf) throw new Error('Material library splitter is detached from its shelf')
          const maximum = getLibraryMaximumHeight(shelf)
          setShelfMaximum(maximum)
          setMode('expanded')
          setShelfHeight((current) => {
            const base = mode === 'expanded' ? current : 169
            return Math.min(maximum, Math.max(169, base + (event.key === 'ArrowUp' ? 12 : -12)))
          })
        }}
      />
      {mode === 'collapsed' ? (
        <button className="library-collapsed-trigger" type="button" onClick={() => setMode('one-row')} aria-label="素材ライブラリを開く"><Grid2X2 size={14} aria-hidden="true" /><b>素材ライブラリ</b><span className="library-toggle-indicator"><ChevronUp size={14} aria-hidden="true" /></span></button>
      ) : (
        <header className="library-shelf-header">
          <button className="library-open-collapse-trigger" type="button" onClick={() => setMode('collapsed')} aria-label="素材ライブラリを閉じる" />
          <div className="library-shelf-title"><Grid2X2 size={14} aria-hidden="true" /><b>素材ライブラリ</b><span className="library-toggle-indicator"><ChevronDown size={14} aria-hidden="true" /></span></div>
          <nav className="library-category-rail" aria-label="素材の種類">
            {categories.map((id) => {
              const categoryMeta = libraryCategoryMeta[id]
              const CategoryIcon = categoryMeta.icon
              return <button type="button" className={category === id ? 'active' : ''} aria-pressed={category === id} onClick={() => { setCategory(id); setSelectedItem(null); setQuery(''); setSelectedTags([]) }} key={id}><CategoryIcon size={15} /><span>{categoryMeta.label}</span></button>
            })}
          </nav>
        </header>
      )}
      {mode !== 'collapsed' && <div className="library-shelf-body">
        <div className="template-library">
          <div className="library-filter-bar">
            <Tabs value={source} onValueChange={(value) => { setSource(value as LibrarySource); setSelectedItem(null); setSelectedTags([]) }} className="contents">
              <TabsList className="template-source-tabs" aria-label={`${label}の種類`}>
                <TabsTrigger value="sample" className={source === 'sample' ? 'active' : ''}>サンプル</TabsTrigger>
                <TabsTrigger value="original" className={source === 'original' ? 'active' : ''}>オリジナル</TabsTrigger>
              </TabsList>
            </Tabs>
            <div className="template-library-search" role="search" aria-label={`${label}を検索・絞り込み`}>
              <div className="template-search-row">
                <label className="template-text-search"><Search size={13} aria-hidden="true" /><Input className="h-auto border-0 bg-transparent p-0 type-body shadow-none focus-visible:ring-0" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`${label}を検索`} aria-label={`${label}を検索`} /></label>
                <Button
                  variant="outline"
                  size="sm"
                  type="button"
                  className={`template-tag-trigger ${selectedTags.length > 0 ? 'active' : ''}`}
                  aria-haspopup="listbox"
                  aria-expanded={tagPanelOpen}
                  aria-controls="template-tag-options"
                  onClick={() => {
                    setSortPanelOpen(false)
                    setTagPanelOpen((open) => !open)
                  }}
                >
                  <Tag size={13} aria-hidden="true" /><span>タグ{selectedTags.length > 0 ? ` ${selectedTags.length}` : ''}</span><ChevronDown size={11} aria-hidden="true" />
                </Button>
                <Popover open={tagPanelOpen} onOpenChange={setTagPanelOpen}>
                  <PopoverContent className="template-tag-popover">
                    <header><b>タグで絞り込み</b>{selectedTags.length > 0 && <Button variant="ghost" size="sm" type="button" onClick={() => setSelectedTags([])}>すべて解除</Button>}</header>
                    <label className="template-tag-search"><Search size={12} aria-hidden="true" /><Input className="h-auto border-0 bg-transparent p-0 type-body shadow-none focus-visible:ring-0" value={tagQuery} onChange={(event) => setTagQuery(event.target.value)} placeholder="タグを絞り込み" role="combobox" aria-autocomplete="list" aria-expanded="true" aria-controls="template-tag-options" /></label>
                    <ul id="template-tag-options" role="listbox" aria-label={`${label}のタグ候補`} aria-multiselectable="true">
                      {visibleTags.length > 0 ? visibleTags.map((tag) => (
                        <li key={tag} role="option" aria-selected={selectedTags.includes(tag)}><button type="button" onClick={() => toggleTag(tag)}><span>{tag}</span>{selectedTags.includes(tag) && <span aria-hidden="true">✓</span>}</button></li>
                      )) : <li className="template-tag-empty">登録済みタグはありません。</li>}
                    </ul>
                  </PopoverContent>
                </Popover>
                <Button
                  variant="outline"
                  size="icon"
                  type="button"
                  className={`template-sort-trigger ${sort !== 'default' ? 'active' : ''}`}
                  aria-label={`${label}の並び順：${librarySortLabels[sort]}`}
                  aria-haspopup="menu"
                  aria-expanded={sortPanelOpen}
                  aria-controls="template-sort-options"
                  onClick={() => {
                    setTagPanelOpen(false)
                    setSortPanelOpen((open) => !open)
                  }}
                >
                  <ArrowUpDown size={13} aria-hidden="true" />
                </Button>
                <Popover open={sortPanelOpen} onOpenChange={setSortPanelOpen}>
                  <PopoverContent className="template-sort-popover">
                    <header><b>並び順</b></header>
                    <div id="template-sort-options" role="menu" aria-label={`${label}の並び順`}>
                      {(Object.entries(librarySortLabels) as [LibrarySort, string][]).map(([value, sortLabel]) => (
                        <button type="button" role="menuitemradio" aria-checked={sort === value} className={sort === value ? 'active' : ''} onClick={() => { setSort(value); setSortPanelOpen(false) }} key={value}>
                          <span>{sortLabel}</span><span aria-hidden="true">{sort === value ? '✓' : ''}</span>
                        </button>
                      ))}
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
              {source === 'original' && <div className="library-scope-filter" role="group" aria-label="オリジナルの保存範囲">
                {([['all', 'すべて'], ['workspace', libraryScopeLabels.workspace], ['shared', libraryScopeLabels.shared]] as const).map(([value, text]) => (
                  <button type="button" key={value} className={scopeFilter === value ? 'active' : ''} aria-pressed={scopeFilter === value} onClick={() => setScopeFilter(value)}>{text}</button>
                ))}
                <small>ドラッグでの移動は複写です。ワークスペースは単独で開けます。</small>
              </div>}
              {selectedTags.length > 0 && <div className="template-tag-chips" aria-label="選択中のタグ">{selectedTags.map((tag) => <button type="button" className="template-tag-chip" aria-label={`${tag}を解除`} onClick={() => toggleTag(tag)} key={tag}><span>{tag}</span><X size={10} aria-hidden="true" /></button>)}</div>}
            </div>
          </div>
          {visibleItems.length > 0 ? (
            <div className="library-card-grid" role="list" aria-label={`${sourceLabel}の${label}`}>
              {visibleItems.map((item) => <div role="listitem" key={item.id}><button type="button" draggable className={`library-card ${selectedItem === item.id ? 'selected' : ''}`} aria-pressed={selectedItem === item.id} onClick={() => setSelectedItem(item.id)} onDragStart={(event) => event.dataTransfer.setData('text/plain', item.id)}>
                <span className={`library-card-preview ${item.thumbnailMissing ? 'library-card-preview-missing' : item.thumbnail ? 'material-sphere-thumbnail' : `tone-${item.tone}`}`}>{item.thumbnailMissing ? <span className="library-thumbnail-missing"><AlertTriangle size={13} aria-hidden="true" />サムネイル未生成</span> : item.thumbnail ? <Image src={item.thumbnail} alt="" width={54} height={54} sizes="54px" aria-hidden="true" /> : <Icon size={20} strokeWidth={1.45} />}</span>
                <span className="library-card-copy"><b>{item.name}</b><small>{item.detail}</small>{item.scope && <em className="library-card-scope">{libraryScopeLabels[item.scope]}</em>}</span>
                {selectedItem === item.id && <span className="library-card-check" aria-hidden="true">✓</span>}
              </button></div>)}
            </div>
          ) : (
            <section className="template-empty-state" aria-live="polite">
              <span className="template-empty-icon"><Icon size={20} strokeWidth={1.6} aria-hidden="true" /></span>
              <b>{label}</b>
              <small>{hasFilter ? `検索条件に一致する${label}はありません。` : `${sourceLabel}の${label}は空です。`}</small>
            </section>
          )}
          {selectedItem && <footer className="library-selection-bar"><span><small>{applyComplete ? '適用済み' : '選択中'}</small><b>{sourceItems.find((item) => item.id === selectedItem)?.name}</b></span><span>{applyComplete ? 'ワークスペースの変更としてUndo可能' : 'ドラッグして対象へ適用'}</span><button type="button" className="primary-button" onClick={() => { setApplyComplete(false); setApplyOpen(true) }}>適用</button></footer>}
        </div>
      </div>
      }
      <Dialog open={applyOpen} onOpenChange={setApplyOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog library-apply-dialog"><header><span><small>{label}を適用</small><b>{sourceItems.find((item) => item.id === selectedItem)?.name}</b></span><button type="button" aria-label="適用確認を閉じる" onClick={() => setApplyOpen(false)}><X size={15} /></button></header>
        {category === 'template' && <section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>解決済み</b><small>レイアウトと表示設定</small></span></p><p><AlertTriangle size={13} /><span><b>確認が必要</b><small>数量・ケース・参照アセットは新しい項目で明示的に結び付けます</small></span></p><p><FolderPlus size={13} /><span><b>作成方法</b><small>開いている項目を置換せず、独立した新規項目を作成</small></span></p></section>}
        {category === 'materials' && <section><p className="workflow-trust-note"><MaterialSphereIcon size={13} />アクティブオブジェクトの新しいマテリアルスロットとして追加します。</p><div className="material-target-options" role="radiogroup" aria-label="マテリアルの割り当て先">{([['object','オブジェクト全体'],['part','部品'],['elements','要素セット']] as const).map(([id,text]) => <label key={id}><input type="radio" name="material-target" checked={materialTarget === id} onChange={() => setMaterialTarget(id)} /><span>{text}</span></label>)}</div>{materialTarget !== 'object' && <p className="workflow-selection-mode"><Shapes size={13} /><span><b>適用後に選択モードを開始</b><small>ビューポートまたはアウトライナーで重複しない対象を選択します</small></span></p>}</section>}
        {category === 'objects' && <section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>独立オブジェクトを作成</b><small>元アセットの識別子とリビジョンを来歴として記録</small></span></p><p><AlertTriangle size={13} /><span><b>参照解決</b><small>必要なフィールドや座標がなければ作成せず理由を表示</small></span></p></section>}
        {!['template','materials','objects'].includes(category) && <p className="workflow-trust-note"><ShieldCheck size={13} />表示表現だけを変更し、解析値・単位・来歴は変更しません。</p>}
        <footer><button type="button" onClick={() => setApplyOpen(false)}>キャンセル</button><button type="button" className="primary-button" onClick={() => { setApplyComplete(true); setApplyOpen(false) }}>{category === 'template' ? '確認して新規作成' : materialTarget !== 'object' && category === 'materials' ? '選択モードへ' : '適用'}</button></footer>
      </DialogContent></Dialog>
    </section>
  )
}

function RightSidebar({ screen, variant, width, setWidth, selectedViewObjects, onViewObjectSelect, pipelineUnits, onPipelineUnitsChange, selectedUnitId, onSelectUnit, viewItem, onViewItemChange, selectedCase, isComparisonItem, baseViewName, comparison, onComparisonChange, splitPanes }: { screen: ScreenId; variant: string; width: number; setWidth: React.Dispatch<React.SetStateAction<number>>; selectedViewObjects: string[]; onViewObjectSelect: (name: string, additive?: boolean) => void; pipelineUnits: PipelineUnitModel[]; onPipelineUnitsChange: (units: PipelineUnitModel[]) => void; selectedUnitId: string | null; onSelectUnit: (id: string) => void; viewItem: ViewItemState; onViewItemChange: (next: ViewItemState) => void; selectedCase: string; isComparisonItem: boolean; baseViewName: string; comparison: ComparisonModel; onComparisonChange: (next: ComparisonModel) => void; splitPanes: number }) {
  const active = activeViewObject(variant, selectedViewObjects)
  const tabs = rightSidebarTabs[screen].filter((tab) => screen !== 'view' || tab.id !== 'text' || (active.kind !== 'container' && viewObjectKinds[active.kind].textProperties))
  // XC-202: a comparison owns 全体 and 出力. The others stay in the rail - removing them leaves "where
  // did the material go" unanswered - but they are marked, so nobody opens six tabs to find the two.
  const borrowedTabIds = ['camera', 'rendering', 'background', 'objects', 'text', 'materials']
  const isBorrowed = (tabId: string) => screen === 'view' && isComparisonItem && borrowedTabIds.includes(tabId)
  const [selectedByScreen, setSelectedByScreen] = useState<Partial<Record<ScreenId, string>>>({})
  const variantTab = variant.startsWith('object-') ? 'objects' : variant.startsWith('material-') ? 'materials' : variant === 'steady-result' ? 'output' : variant === 'comparison-borrowed' ? 'materials' : variant === 'cameras' || variant.startsWith('camera-') ? 'camera' : variant === 'unit-reference' ? 'settings' : variant === 'commentary-review' || variant === 'drafting' ? 'drafting' : variant === 'axes' ? 'axes' : variant === 'style' || variant === 'theme' ? 'style' : variant === 'background' ? 'background' : variant === 'output-motion' || variant === 'split-output' || variant === 'comparison-output' ? 'output' : variant === 'develop-grade' ? 'rendering' : variant.includes('output-preflight') ? 'output' : variant === 'series-unresolved' || variant === 'series' ? 'series' : undefined
  const selectedTab = tabs.find((tab) => tab.id === (selectedByScreen[screen] ?? variantTab)) ?? tabs[0]

  if (!selectedTab) return null
  const SelectedTabIcon = selectedTab.icon

  const selectTab = (tab: SidebarTab) => {
    setSelectedByScreen((current) => ({ ...current, [screen]: tab.id }))
  }

  const moveTabFocus = (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
    let nextIndex: number | undefined
    if (event.key === 'ArrowDown') nextIndex = (index + 1) % tabs.length
    if (event.key === 'ArrowUp') nextIndex = (index - 1 + tabs.length) % tabs.length
    if (event.key === 'Home') nextIndex = 0
    if (event.key === 'End') nextIndex = tabs.length - 1
    if (nextIndex === undefined) return
    event.preventDefault()
    const nextTab = tabs[nextIndex]
    selectTab(nextTab)
    document.getElementById(`sidebar-tab-${screen}-${nextTab.id}`)?.focus()
  }

  return (
    <aside className="right-sidebar" id="right-sidebar">
      {screen === 'view' && <OutlinerPanel variant={variant} selectedNames={selectedViewObjects} onSelect={onViewObjectSelect} borrowedFrom={isComparisonItem ? baseViewName : null} />}
      <div className="sidebar-editor">
        <nav className="sidebar-tab-rail" role="tablist" aria-label={`${screenNames[screen]}の設定`} aria-orientation="vertical">
          {tabs.map((tab, index) => {
            const Icon = tab.icon
            // XC-207: this tab edits the open item itself, so it is named after that item rather than
            // called 全体 - every other view-scoped tab is "the whole view" too, which is what made the
            // old name say nothing.
            const label = tab.id === 'overall' && screen === 'view' && isComparisonItem ? '比較' : tab.label
            const active = tab.id === selectedTab.id
            const startsSelectionGroup = tab.scope === 'selection' && tabs[index - 1]?.scope !== 'selection'
            const scopeLabel = tab.scope === 'selection' ? '選択中のオブジェクト' : tab.scope === 'view' ? 'ビュー全体' : undefined
            return (
              <Fragment key={tab.id}>
                {startsSelectionGroup && <span className="sidebar-tab-scope-separator" aria-hidden="true" />}
                <button
                  id={`sidebar-tab-${screen}-${tab.id}`}
                  className={`sidebar-tab-button ${active ? 'active' : ''} ${isBorrowed(tab.id) ? 'borrowed' : ''}`}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  aria-controls={`sidebar-panel-${screen}`}
                  aria-label={isBorrowed(tab.id) ? `${label}（基準ビューの設定）` : scopeLabel ? `${scopeLabel}：${label}` : label}
                  data-tooltip={isBorrowed(tab.id) ? `${label}・基準ビューの設定` : label}
                  tabIndex={active ? 0 : -1}
                  onClick={() => selectTab(tab)}
                  onKeyDown={(event) => moveTabFocus(event, index)}
                >
                  <Icon size={17} strokeWidth={1.75} aria-hidden="true" />
                </button>
              </Fragment>
            )
          })}
        </nav>
        <section
          className="sidebar-tab-panel"
          id={`sidebar-panel-${screen}`}
          role="tabpanel"
          aria-labelledby={`sidebar-tab-${screen}-${selectedTab.id}`}
        >
          <header className="sidebar-tab-panel-title">
            <span className="sidebar-tab-panel-icon"><SelectedTabIcon size={16} strokeWidth={1.8} aria-hidden="true" /></span>
            <span><b>{selectedTab.id === 'overall' && screen === 'view' && isComparisonItem ? '比較' : selectedTab.label}</b></span>
            {isBorrowed(selectedTab.id) && <em className="sidebar-tab-borrowed-mark">基準ビューの設定</em>}
          </header>
          <p className="sidebar-tab-summary">{selectedTab.description}</p>
          <PropertyEditor key={`${screen}-${selectedTab.id}`} screen={screen} tab={selectedTab} variant={variant} activeObject={active} pipelineUnits={pipelineUnits} onPipelineUnitsChange={onPipelineUnitsChange} selectedUnitId={selectedUnitId} onSelectUnit={onSelectUnit} viewItem={viewItem} onViewItemChange={onViewItemChange} selectedCase={selectedCase} isComparisonItem={isComparisonItem} baseViewName={baseViewName} comparison={comparison} onComparisonChange={onComparisonChange} splitPanes={splitPanes} />
        </section>
      </div>
      <button
        className="dock-splitter sidebar-splitter-right"
        type="button"
        role="separator"
        aria-orientation="vertical"
        aria-controls="right-sidebar"
        aria-valuemin={210}
        aria-valuemax={460}
        aria-valuenow={width}
        aria-label="右サイドバーの幅を変更"
        onPointerDown={(event) => startHorizontalPanelResize(event, 'right', width, setWidth)}
        onKeyDown={(event) => resizeHorizontalPanelFromKey(event, 'right', setWidth)}
      />
    </aside>
  )
}

function PropertyEditor({ screen, tab, variant, activeObject, pipelineUnits, onPipelineUnitsChange, selectedUnitId, onSelectUnit, viewItem, onViewItemChange, selectedCase, isComparisonItem, baseViewName, comparison, onComparisonChange, splitPanes }: { screen: ScreenId; tab: SidebarTab; variant: string; activeObject: ActiveViewObject; pipelineUnits: PipelineUnitModel[]; onPipelineUnitsChange: (units: PipelineUnitModel[]) => void; selectedUnitId: string | null; onSelectUnit: (id: string) => void; viewItem: ViewItemState; onViewItemChange: (next: ViewItemState) => void; selectedCase: string; isComparisonItem: boolean; baseViewName: string; comparison: ComparisonModel; onComparisonChange: (next: ComparisonModel) => void; splitPanes: number }) {
  if (screen === 'pipeline') return <AutomationPropertyEditor tab={tab} variant={variant} units={pipelineUnits} onUnitsChange={onPipelineUnitsChange} selectedUnitId={selectedUnitId} onSelectUnit={onSelectUnit} />
  // XC-202: a comparison owns 全体 and 出力 only. Every other tab belongs to its base View, and is
  // named as borrowed rather than shown as an editable copy - a copy would let a user change one pane's
  //材料 and destroy the one guarantee a comparison makes (XC-182 names the state instead).
  if (screen === 'view' && isComparisonItem && ['camera', 'rendering', 'background', 'objects', 'text', 'materials'].includes(tab.id)) {
    return <BorrowedSettingPanel tabLabel={tab.label} tabId={tab.id} baseViewName={baseViewName} />
  }
  if (screen === 'view' && tab.id === 'objects') return <ViewObjectPropertyEditor activeObject={activeObject} />
  if (screen === 'view' && tab.id === 'materials') return <ViewMaterialPropertyEditor variant={variant} activeObject={activeObject} />
  if (screen === 'view' && tab.id === 'text') return <ViewTextPropertyEditor activeObject={activeObject} />
  if (screen === 'view') return <ViewPropertyEditor tab={tab} variant={variant} viewItem={viewItem} onViewItemChange={onViewItemChange} selectedCase={selectedCase} isComparisonItem={isComparisonItem} baseViewName={baseViewName} comparison={comparison} onComparisonChange={onComparisonChange} splitPanes={splitPanes} />
  if (screen === 'graph') return <GraphPropertyEditor tab={tab} variant={variant} />
  if (screen === 'report') return <ReportPropertyEditor tab={tab} variant={variant} />
  if (screen === 'simulation') return <SimulationPropertyEditor />
  // Settings has no branch here on purpose (XC-165): it is a full-width page whose own category
  // navigation owns 全般 / 単位 / 成分座標系 / レンダラー, and it never renders the workspace right
  // sidebar. A branch for it stood here returning a SettingsPropertyEditor that was never defined
  // anywhere in this file - unreachable, untypecheckable, and contradicting the decision at once.
  if (screen === 'network') return <NetworkPropertyEditor tab={tab} variant={variant} />
  return null
}

function BorrowedSettingPanel({ tabLabel, tabId, baseViewName }: { tabLabel: string; tabId: string; baseViewName: string }) {
  return <div className="property-editor">
    <div className="sidebar-context-state borrowed-setting">
      <Columns3 size={22} />
      <b>この設定は基準ビューが持っています</b>
      <small>比較は自前の{tabLabel}を持ちません。基準ビュー「{baseViewName}」の設定をそのまま全メンバーへ適用します。ここで直せてしまうと、ペインの差の原因を特定できなくなります。</small>
      <button type="button" className="primary-button"><ArrowUpRight size={12} />基準ビュー「{baseViewName}」を編集</button>
    </div>
    {tabId === 'camera' && <p className="property-editor-note"><ShieldCheck size={12} />カメラそのものを比べたいときは、「全体」の比較グループで変える軸に「カメラ」を選びます。</p>}
  </div>
}

function PropertyGroup({ title, children, open = true }: { title: string; children: React.ReactNode; open?: boolean }) {
  return <details className="property-group" open={open}><summary><ChevronRight size={12} /><b>{title}</b></summary><div className="property-fields">{children}</div></details>
}

type PreflightCheck = { label: string; detail: string; status: 'pass' | 'warning' | 'blocked' }

function OutputPreflightDialog({ open, onOpenChange, title, checks, onStart }: { open: boolean; onOpenChange: (open: boolean) => void; title: string; checks: PreflightCheck[]; onStart: () => void }) {
  const blocked = checks.some((check) => check.status === 'blocked')
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog preflight-dialog"><header><span><small>出力前チェック</small><b>{title}</b></span><button type="button" aria-label="出力前チェックを閉じる" onClick={() => onOpenChange(false)}><X size={15} /></button></header><section className="preflight-checks">{checks.map((check) => <article className={check.status} key={check.label}>{check.status === 'pass' ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}<span><b>{check.label}</b><small>{check.detail}</small></span><em>{check.status === 'pass' ? '合格' : check.status === 'warning' ? '要記載' : '出力不可'}</em></article>)}</section><p className={blocked ? 'workflow-trust-note blocked' : 'workflow-trust-note'}>{blocked ? <AlertTriangle size={13} /> : <ShieldCheck size={13} />}{blocked ? '不足項目を解決するまで通常出力は開始しません。既存成果物は変更されません。' : '新しい実行フォルダーへ保存し、既存成果物を上書きしません。'}</p><footer><button type="button" onClick={() => onOpenChange(false)}>戻る</button><button type="button" className="primary-button" disabled={blocked} onClick={onStart}>出力を開始</button></footer></DialogContent></Dialog>
}

// XC-197, on the @Result axis. A bookmark holds a rule, resolves per case, lands on a position that
// exists, and says when it snapped. `12.0 s` typed into four panes is the thing this replaces.
type ResultBookmarkModel = {
  id: string
  name: string
  rule:
    | { kind: 'explicit'; position: number }
    | { kind: 'extremum'; quantity: string; statistic: '最大' | '最小' }
    | { kind: 'crossing'; quantity: string; threshold: string; direction: '上昇' | '下降' }
    | { kind: 'relative'; of: '先頭' | '末尾' }
}

const seedResultBookmarks: ResultBookmarkModel[] = [
  { id: 'hold', name: '保持時間', rule: { kind: 'explicit', position: 12 } },
  { id: 'peak', name: '最大応力時', rule: { kind: 'extremum', quantity: '最大応力', statistic: '最大' } },
  { id: 'yield', name: '許容応力を超えた時刻', rule: { kind: 'crossing', quantity: '最大応力', threshold: '235 MPa', direction: '上昇' } },
  { id: 'last', name: '最終ステップ', rule: { kind: 'relative', of: '末尾' } },
]

function describeBookmarkRule(bookmark: ResultBookmarkModel) {
  const rule = bookmark.rule
  if (rule.kind === 'explicit') return '固定した位置'
  if (rule.kind === 'extremum') return `規則：${rule.quantity}が${rule.statistic}`
  if (rule.kind === 'crossing') return `規則：${rule.quantity}が${rule.threshold}を${rule.direction}方向に横切る`
  return `規則：軸の${rule.of}`
}

// Resolution is recomputed for the case in scope, so the same bookmark puts each pane at its own
// position. It never lands between stored positions: it snaps and says so (view/AC-033, XC-160).
function resolveBookmark(bookmark: ResultBookmarkModel, axis: ResultAxisKind, caseName: string, unresolved: boolean) {
  const definition = resultAxes[axis]
  const rule = bookmark.rule
  if (rule.kind === 'explicit') return { state: 'resolved' as const, position: rule.position, snapped: false, at: null as string | null }
  if (rule.kind === 'relative') return { state: 'resolved' as const, position: rule.of === '先頭' ? definition.minimum : definition.maximum, snapped: false, at: null }
  if (unresolved) return { state: 'unresolved' as const, position: definition.minimum, snapped: false, at: `${rule.quantity}がケース「${caseName}」にありません` }
  // The mockup varies the resolved step per case so that the per-case behaviour is visible; it states
  // the value as a placeholder rather than inventing an analysis number (OPEN-022).
  const offset = caseName.length % 5
  const step = definition.storedStep
  const raw = definition.minimum + (rule.kind === 'crossing' ? 6 + offset : 17 + offset) * step
  const snappedPosition = Math.round((raw - definition.minimum) / step) * step + definition.minimum
  return { state: 'resolved' as const, position: Math.min(definition.maximum, snappedPosition), snapped: rule.kind === 'extremum', at: '［値・単位未宣言］' }
}

// The shared unresolved list: what a template could not apply and why, with the template it came from.
// XC-063 keeps the source identifier and revision reachable from the item, so prose in a banner is not
// enough - the reader needs the list and the identity that produced it.
function UnresolvedList({ title, source, revision, resolved, unresolved }: { title: string; source: string; revision: string; resolved: string[]; unresolved: { item: string; reason: string }[] }) {
  return (
    <section className="unresolved-list" aria-label={title}>
      <header><AlertTriangle size={15} /><span><b>{title}</b><small>{source}・{revision}</small></span></header>
      <div>
        <ul className="unresolved-list-resolved" aria-label="解決済み">{resolved.map((item) => <li key={item}><CheckCircle2 size={11} />{item}</li>)}</ul>
        <ul className="unresolved-list-unresolved" aria-label="未解決">{unresolved.map((entry) => <li key={entry.item}><AlertTriangle size={11} /><span><b>{entry.item}</b><small>{entry.reason}</small></span></li>)}</ul>
      </div>
      <footer><ShieldCheck size={12} />未解決の項目は既定値で埋めません。この一覧と参照元テンプレートの識別子・リビジョンは、作成された項目からいつでも参照できます。</footer>
    </section>
  )
}

// The probe readout: a value at a point with its unit, digits, provenance and result position.
// Keeping it as a @Variable is deliberate and never automatic (11_ui.md, keyboard scheme).
function ProbeReadout() {
  const [kept, setKept] = useState(false)
  const [open, setOpen] = useState(true)
  if (!open) return null
  return (
    <section className="probe-readout" aria-label="プローブ結果">
      <header>
        <span><b>プローブ</b><small>節点 12345・未変形座標</small></span>
        <button type="button" aria-label="プローブを閉じる" onClick={() => setOpen(false)}><X size={13} /></button>
      </header>
      <dl>
        <div><dt>応力</dt><dd><NumberCell value={182.4} unit="MPa" digits={4} provenance="dataset" /></dd></div>
        <div><dt>変位</dt><dd><NumberCell value={0.00317} unit="m" digits={3} provenance="dataset" /></dd></div>
        <div><dt>温度</dt><dd><NumberCell value={null} unit={null} digits={4} provenance="dataset" /></dd></div>
      </dl>
      <p className="probe-position">結果位置：時刻 12.0 s／点データ・セル平均なし</p>
      <footer>
        {kept ? (
          <>
            <QuantityChip name="プローブ応力" provenance="dataset" unit="MPa" />
            <small>変数リストへ追加しました。以降はどの入力にもドラッグできます。</small>
          </>
        ) : (
          <button className="primary-button" type="button" onClick={() => setKept(true)}>変数として保持</button>
        )}
      </footer>
    </section>
  )
}

// XC-199: a @View holds several named cameras and several named timelines. A camera is one object -
// its pose and its lens together - because a saved pose without a lens is half a camera, and keeping
// the two apart means changing the lens for one saved position changes it for all of them.
type CameraFocus =
  | { kind: 'object'; label: string }
  | { kind: 'selection'; label: string }
  | { kind: 'position'; label: string }
  | { kind: 'extremum'; quantity: string; statistic: '最大' | '最小' | '絶対値最大' }

type CameraModel = {
  id: string
  name: string
  pose: 'explicit' | 'framed'
  focus: CameraFocus | null
  projection: 'perspective' | 'orthographic'
  focalLengthMm: number
  depthOfField: boolean
}

// XC-200: a @Timeline answers *when* and holds six values. It carried camera work twice - keyframes,
// then shots - and both blocked the thing comparison needs: replaying the same motion from a different
// camera. A video output names one timeline and one camera.
type TimelineModel = {
  id: string
  name: string
  fromBookmarkId: string
  toBookmarkId: string
  stride: number
  speed: number
  frameRate: number
  loop: boolean
}

function cameraRule(camera: CameraModel) {
  if (camera.pose === 'explicit') return '固定した位置・注視点・上方向'
  if (!camera.focus) return '対象未設定'
  if (camera.focus.kind === 'extremum') return `規則：${camera.focus.quantity}の${camera.focus.statistic}へ寄せる`
  return `規則：${camera.focus.label}を画面に収める`
}

// Derived for the case in scope and never written back, so four panes show four positions.
function resolveCamera(camera: CameraModel, unresolved: boolean) {
  if (camera.pose === 'explicit') return { state: 'resolved' as const, detail: '保存した位置を再現' }
  if (camera.focus?.kind === 'extremum' && unresolved) {
    return { state: 'unresolved' as const, detail: `${camera.focus.quantity}がこのケースにありません。カメラは動かしていません` }
  }
  if (camera.focus?.kind === 'extremum') {
    return { state: 'resolved' as const, detail: `解決先：［${camera.focus.quantity}の位置］・値 ［未接続・単位未宣言］` }
  }
  return { state: 'resolved' as const, detail: '対象の境界に合わせて画角を決定' }
}

// XC-198: grading is a group inside 描画, and its default applies no grade at all. A picture cited as
// evidence is produced with 計測, so the value-to-colour mapping in two screenshots cannot disagree.
type GradePreset = 'measurement' | 'standard' | 'technicalDocument' | 'presentation' | 'photoreal'

const gradePresets: Record<GradePreset, { label: string; detail: string; tone: string; exposure: string; treatments: string }> = {
  measurement: { label: '計測', detail: '無補正・既定', tone: 'なし', exposure: '0.0 EV', treatments: '色を変える処理はすべてオフ' },
  standard: { label: '標準', detail: '穏やかな階調', tone: 'Neutral', exposure: '0.0 EV', treatments: 'アンチエイリアスのみ' },
  technicalDocument: { label: '技術文書', detail: '明背景の印刷向け', tone: 'Neutral', exposure: '+0.3 EV', treatments: '高コントラスト・環境遮蔽あり' },
  presentation: { label: 'プレゼン', detail: '説明用', tone: 'Filmic', exposure: '+0.5 EV', treatments: '環境遮蔽・影・軽いブルーム' },
  photoreal: { label: 'フォトリアル', detail: '対応レンダラーのみ', tone: 'ACES', exposure: '+0.5 EV', treatments: 'レイトレース影・被写界深度・デノイズ' },
}

const seedCameras: CameraModel[] = [
  { id: 'cam-front', name: '正面', pose: 'explicit', focus: null, projection: 'orthographic', focalLengthMm: 50, depthOfField: false },
  { id: 'cam-iso', name: '等角', pose: 'explicit', focus: null, projection: 'perspective', focalLengthMm: 50, depthOfField: false },
  { id: 'cam-peak', name: '最大応力へ寄せる', pose: 'framed', focus: { kind: 'extremum', quantity: '最大応力', statistic: '最大' }, projection: 'perspective', focalLengthMm: 85, depthOfField: true },
  { id: 'cam-fixture', name: '固定部の拡大', pose: 'framed', focus: { kind: 'object', label: '［元ファイルの部品名 02］' }, projection: 'perspective', focalLengthMm: 100, depthOfField: false },
]

const seedTimelines: TimelineModel[] = [
  { id: 'tl-full', name: '全体再生', fromBookmarkId: 'first', toBookmarkId: 'last', stride: 1, speed: 1, frameRate: 30, loop: false },
  { id: 'tl-ramp', name: '立ち上がりをゆっくり', fromBookmarkId: 'first', toBookmarkId: 'hold', stride: 1, speed: 0.5, frameRate: 60, loop: true },
  { id: 'tl-peak', name: '臨界時刻まで', fromBookmarkId: 'first', toBookmarkId: 'peak', stride: 2, speed: 1, frameRate: 30, loop: false },
]

// XC-202: the second kind of item in the View area. It names a base @View and varies one axis; it owns
// no objects, materials, lighting, background or guides of its own.
type ComparisonAxis = 'case' | 'resultPosition' | 'camera' | 'quantity' | 'deformation' | 'representation'

type ComparisonModel = {
  axis: ComparisonAxis
  members: string[]
  // An ordered axis may be divided instead of enumerated: a contact sheet over time should not require
  // naming every position as a bookmark first (XC-202, E-123's UpdateWholeRange).
  memberMode: 'enumerate' | 'range'
  rangeCount: number
  arrangement: 'grid' | 'overlay'
  // The columns only. Rows are always derived from the member count, so no setting can produce a grid
  // that omits a member - which is what a free rows-and-columns pair does (XC-205).
  columns: 'auto' | number
  sharedColourMap: boolean
}

const orderedAxes: ComparisonAxis[] = ['resultPosition', 'deformation']

// What a comparison actually draws, derived in one place: the panel's figures, the area bar's menu and
// the canvas all read this, so none of the three can state a grid another one does not draw.
const comparisonMemberLabels = (comparison: ComparisonModel) =>
  comparison.memberMode === 'range' && orderedAxes.includes(comparison.axis)
    ? rangeMembers(comparison.rangeCount).map((member) => member.label)
    : comparison.members

// A comparison varies one ordered axis, so `auto` keeps the members on one line and wraps only when
// they no longer fit - reading order is the axis. A chosen column count never exceeds the member count,
// and the rows follow from it, so every member has a pane (XC-205).
const comparisonGridColumns = (members: number, columns: 'auto' | number) =>
  Math.max(1, Math.min(columns === 'auto' ? 4 : columns, Math.max(1, members)))

// Generated members land on positions that exist, and say when they snapped (view/AC-033). Two that
// snap to the same stored position are reported rather than drawn as two identical panes.
function rangeMembers(count: number) {
  const axis = resultAxes.time
  const span = axis.maximum - axis.minimum
  const raw = Array.from({ length: count }, (_, index) => axis.minimum + (span * index) / Math.max(1, count - 1))
  const snapped = raw.map((value) => Math.round((value - axis.minimum) / axis.storedStep) * axis.storedStep + axis.minimum)
  return snapped.map((value, index) => ({
    label: axis.format(value),
    snapped: Math.abs(value - raw[index]) > 1e-9,
    duplicate: snapped.indexOf(value) !== index,
  }))
}

// Three of these are sets of subjects or of the View's own named objects; the last three are published
// properties of the base View itself. Sweeping a property is what lets stress be compared with
// temperature, or a surface with a section, without two Views differing in five other ways (XC-202).
// XC-215: a font choice is shown in the font. The stacks are the mockup's samples, not a shipped list.
const fontStacks: Record<string, string> = {
  workspace: 'var(--family-ui)',
  'noto-sans': "'Noto Sans JP', var(--family-ui)",
  'source-serif': "'Source Serif 4', Georgia, serif",
  mono: 'var(--family-mono)',
}
const fontLabels: Record<string, string> = {
  workspace: 'ワークスペース設定',
  'noto-sans': 'Noto Sans',
  'source-serif': 'Source Serif',
  mono: '等幅',
}

const comparisonAxisLabels: Record<ComparisonAxis, string> = {
  case: 'ケース',
  resultPosition: '結果位置（時刻・モード・周波数）',
  camera: 'カメラ',
  quantity: '基準ビューのプロパティ：色を付ける数量',
  deformation: '基準ビューのプロパティ：変形倍率',
  representation: '基準ビューのプロパティ：表示形式',
}

const comparisonPropertyAxes: ComparisonAxis[] = ['quantity', 'deformation', 'representation']

// Everything the axis is not is shared, so changing the axis replaces the member list rather than
// adding a second dimension to it (XC-202).
function comparisonMembersFor(axis: ComparisonAxis, viewItem: ViewItemState) {
  if (axis === 'case') return workspaceCases.map((item) => item.name)
  if (axis === 'camera') return viewItem.cameras.map((item) => item.name)
  if (axis === 'resultPosition') return viewItem.bookmarks.map((entry) => entry.name)
  if (axis === 'quantity') return ['最大応力', '変位', '温度']
  if (axis === 'deformation') return ['×1.0', '×10', '×50']
  return ['サーフェス', 'サーフェス＋エッジ', 'ワイヤーフレーム']
}

type ViewItemState = {
  cameras: CameraModel[]
  activeCameraId: string
  timelines: TimelineModel[]
  activeTimelineId: string
  bookmarks: ResultBookmarkModel[]
}

const initialViewItem: ViewItemState = {
  cameras: seedCameras,
  activeCameraId: 'cam-peak',
  timelines: seedTimelines,
  activeTimelineId: 'tl-peak',
  bookmarks: seedResultBookmarks,
}

function ViewPropertyEditor({ tab, variant, viewItem, onViewItemChange, selectedCase, isComparisonItem, baseViewName, comparison, onComparisonChange, splitPanes }: { tab: SidebarTab; variant: string; viewItem: ViewItemState; onViewItemChange: (next: ViewItemState) => void; selectedCase: string; isComparisonItem: boolean; baseViewName: string; comparison: ComparisonModel; onComparisonChange: (next: ComparisonModel) => void; splitPanes: number }) {
  const cameraUnresolved = variant === 'camera-unresolved'
  const [selectedCameraId, setSelectedCameraId] = useState(viewItem.activeCameraId)
  const [selectedTimelineId, setSelectedTimelineId] = useState(viewItem.activeTimelineId)
  const [cameraDialogOpen, setCameraDialogOpen] = useState(false)
  const [newCameraName, setNewCameraName] = useState('')
  const [newCameraKind, setNewCameraKind] = useState<'explicit' | 'object' | 'selection' | 'extremum'>('extremum')
  const [grade, setGrade] = useState<GradePreset>('measurement')
  const hasResultAxis = caseHasResultAxis(selectedCase)
  // XC-212: a comparison over the result axis pins every pane to its own position, so there is nothing
  // left to play. Over any other axis the panes advance together along the shared position, which is
  // the multi-pane video a deliverable actually needs.
  const axisPinsEveryPane = isComparisonItem && comparison.axis === 'resultPosition'
  const canWriteVideo = hasResultAxis && !axisPinsEveryPane
  const isComparison = isComparisonItem
  const setComparison = onComparisonChange
  const effectiveMembers = comparisonMemberLabels(comparison)
  const comparisonColumns = comparisonGridColumns(effectiveMembers.length, comparison.columns)
  const comparisonRows = Math.max(1, Math.ceil(effectiveMembers.length / Math.max(1, comparisonColumns)))
  const [backgroundMode, setBackgroundMode] = useState<'solid' | 'gradient' | 'image' | 'environment'>('gradient')
  const [outputMode, setOutputMode] = useState<'image' | 'video'>('image')
  const [renderer, setRenderer] = useState<'vtk' | 'omniverse'>('vtk')
  const [lightingSource, setLightingSource] = useState<'studio' | 'background-environment' | 'unlit'>('studio')
  const [preflightOpen, setPreflightOpen] = useState(variant === 'output-preflight')
  const [outputStarted, setOutputStarted] = useState(false)

  const camera = viewItem.cameras.find((item) => item.id === selectedCameraId) ?? viewItem.cameras[0] ?? null
  const timeline = viewItem.timelines.find((item) => item.id === selectedTimelineId) ?? viewItem.timelines[0] ?? null
  const bookmarkName = (id: string) => id === 'first' ? '軸の先頭' : id === 'last' ? '軸の末尾' : viewItem.bookmarks.find((entry) => entry.id === id)?.name ?? '未解決の位置'
  // A span whose ends are rules can resolve backwards in one case and forwards in another.
  const timelineReversed = timeline !== null && bookmarkAxisPosition(timeline.toBookmarkId, 'time', selectedCase, viewItem.bookmarks) <= bookmarkAxisPosition(timeline.fromBookmarkId, 'time', selectedCase, viewItem.bookmarks)

  const updateCamera = (patch: Partial<CameraModel>) => {
    if (!camera) return
    onViewItemChange({ ...viewItem, cameras: viewItem.cameras.map((item) => item.id === camera.id ? { ...item, ...patch } : item) })
  }
  const updateTimeline = (patch: Partial<TimelineModel>) => {
    if (!timeline) return
    onViewItemChange({ ...viewItem, timelines: viewItem.timelines.map((item) => item.id === timeline.id ? { ...item, ...patch } : item) })
  }
  const addCamera = () => {
    const focus: CameraFocus | null = newCameraKind === 'explicit' ? null
      : newCameraKind === 'extremum' ? { kind: 'extremum', quantity: '最大応力', statistic: '最大' }
      : newCameraKind === 'object' ? { kind: 'object', label: '［選択したオブジェクト］' }
      : { kind: 'selection', label: '［保存した選択］' }
    const next: CameraModel = { id: `cam-${viewItem.cameras.length + 1}`, name: newCameraName.trim(), pose: newCameraKind === 'explicit' ? 'explicit' : 'framed', focus, projection: 'perspective', focalLengthMm: 50, depthOfField: false }
    onViewItemChange({ ...viewItem, cameras: [...viewItem.cameras, next] })
    setSelectedCameraId(next.id)
    setNewCameraName('')
    setCameraDialogOpen(false)
  }
  const duplicateCamera = () => {
    if (!camera) return
    const next: CameraModel = { ...camera, id: `${camera.id}-copy`, name: `${camera.name}のコピー` }
    onViewItemChange({ ...viewItem, cameras: [...viewItem.cameras, next] })
    setSelectedCameraId(next.id)
  }
  const removeCamera = () => {
    if (!camera || viewItem.cameras.length <= 1) return
    const remaining = viewItem.cameras.filter((item) => item.id !== camera.id)
    onViewItemChange({
      ...viewItem,
      cameras: remaining,
      activeCameraId: viewItem.activeCameraId === camera.id ? remaining[0].id : viewItem.activeCameraId,
    })
    setSelectedCameraId(remaining[0].id)
  }
  const addTimeline = () => {
    const next: TimelineModel = { id: `tl-${viewItem.timelines.length + 1}`, name: `再生プリセット ${viewItem.timelines.length + 1}`, fromBookmarkId: 'first', toBookmarkId: 'last', stride: 1, speed: 1, frameRate: 30, loop: false }
    onViewItemChange({ ...viewItem, timelines: [...viewItem.timelines, next] })
    setSelectedTimelineId(next.id)
  }
  const removeTimeline = () => {
    if (!timeline || viewItem.timelines.length <= 1) return
    const remaining = viewItem.timelines.filter((item) => item.id !== timeline.id)
    onViewItemChange({ ...viewItem, timelines: remaining, activeTimelineId: viewItem.activeTimelineId === timeline.id ? remaining[0].id : viewItem.activeTimelineId })
    setSelectedTimelineId(remaining[0].id)
  }
  if (tab.id === 'overall') return <div className="property-editor">
    {/* 全体 owns the item and the canvas as a whole. Projection and camera moved to the カメラ tab
        (XC-196): a section that also holds the lens is a section with no nameable responsibility. */}
    <PropertyGroup title="ビュー">
      <label><span>名前</span><input defaultValue="変形＋応力" /></label>
      <label><span>説明</span><input placeholder="このビューが示す内容" /></label>
    </PropertyGroup>
    {isComparison && <PropertyGroup title="比較">
      {/* XC-202: a comparison names a base @View and varies exactly one axis. It owns no objects,
          materials, lighting, background or guides - all of them come from the base View, so a
          comparison is edited by editing that View. Six controls, one group, no new rail tab. */}
      <label><span>基準ビュー</span><select defaultValue="standard"><option value="standard">標準ビュー</option><option value="compare">ケース比較ビュー</option></select></label>
      {/* Live, unlike a @Template: editing the View changes every pane, which is why the comparison
          holds nothing of its own (XC-202, against XC-109). */}
      <label><span>参照の性質</span><input value={`生きた参照・「${baseViewName}」の編集が全ペインに反映`} readOnly /></label>
      <label><span>変える軸</span><select value={comparison.axis} onChange={(event) => setComparison({ ...comparison, axis: event.target.value as ComparisonAxis, members: comparisonMembersFor(event.target.value as ComparisonAxis, viewItem) })}>{(Object.keys(comparisonAxisLabels) as ComparisonAxis[]).map((axis) => <option value={axis} key={axis}>{comparisonAxisLabels[axis]}</option>)}</select></label>
      {comparisonPropertyAxes.includes(comparison.axis) && <p className="property-editor-note"><ShieldCheck size={12} />基準ビュー自身のプロパティを振ります。他はすべて共有されるので、差の原因はこのプロパティに限定されます。</p>}
      {orderedAxes.includes(comparison.axis) && <label><span>メンバーの決め方</span><select value={comparison.memberMode} onChange={(event) => setComparison({ ...comparison, memberMode: event.target.value as ComparisonModel['memberMode'] })}><option value="enumerate">保存した位置から選ぶ</option><option value="range">範囲を等分する</option></select></label>}
      {comparison.memberMode === 'range' && orderedAxes.includes(comparison.axis) ? <>
        <label><span>開始</span><select defaultValue="first"><option value="first">軸の先頭</option>{viewItem.bookmarks.map((entry) => <option value={entry.id} key={entry.id}>{entry.name}</option>)}</select></label>
        <label><span>終了</span><select defaultValue="last"><option value="last">軸の末尾</option>{viewItem.bookmarks.map((entry) => <option value={entry.id} key={entry.id}>{entry.name}</option>)}</select></label>
        <label><span>分割数</span><input type="number" min={2} max={12} value={comparison.rangeCount} onChange={(event) => setComparison({ ...comparison, rangeCount: Math.max(2, Math.min(12, Number(event.target.value))) })} /></label>
        <div className="comparison-members" role="group" aria-label="生成されたメンバー">
          {rangeMembers(comparison.rangeCount).map((member, index) => (
            <div className={`comparison-member ${member.duplicate ? 'duplicate' : ''}`} key={index}>
              <span className="comparison-member-index">{index + 1}</span>
              <b>{member.label}</b>
              {member.duplicate ? <em className="comparison-member-note">前と同じ保存位置</em> : member.snapped ? <em className="comparison-member-note">保存位置へ丸め</em> : null}
            </div>
          ))}
        </div>
        {rangeMembers(comparison.rangeCount).some((member) => member.duplicate)
          ? <div className="property-unresolved"><AlertTriangle size={13} /><span><b>同じ位置に解決するメンバーがあります</b><small>軸の保存位置より細かく分割しています。分割数を減らすまで、同じ絵が並ぶ図を出力しません。</small></span></div>
          : <p className="property-editor-note"><ShieldCheck size={12} />生成した位置は軸上に実在する保存位置へ丸め、丸めた事実をメンバーごとに示します。</p>}
      </> : <div className="comparison-members" role="group" aria-label="比較するメンバー">
        {comparison.members.map((member, index) => (
          <div className="comparison-member" key={member}>
            <span className="comparison-member-index">{index + 1}</span>
            <b>{member}</b>
            <button type="button" aria-label={`${member}を外す`} disabled={comparison.members.length <= 2} onClick={() => setComparison({ ...comparison, members: comparison.members.filter((item) => item !== member) })}><X size={10} /></button>
          </div>
        ))}
      </div>}
      {/* "Everything else is shared" is only checkable when the shared values are written down. */}
      <div className="comparison-shared" aria-label="共有する設定">
        {comparison.axis !== 'case' && <label><span>共有ケース</span><select defaultValue={workspaceCases[0].name}>{workspaceCases.map((item) => <option value={item.name} key={item.name}>{item.name}</option>)}</select></label>}
        {comparison.axis !== 'camera' && <label><span>共有カメラ</span><select defaultValue={viewItem.cameras[0]?.id}>{viewItem.cameras.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>}
        {comparison.axis !== 'resultPosition' && <label><span>共有結果位置</span><select defaultValue="first"><option value="first">軸の先頭</option>{viewItem.bookmarks.map((entry) => <option value={entry.id} key={entry.id}>{entry.name}</option>)}</select></label>}
      </div>
      <label><span>配置</span><select value={comparison.arrangement} onChange={(event) => setComparison({ ...comparison, arrangement: event.target.value as ComparisonModel['arrangement'] })}><option value="grid">グリッド</option><option value="overlay">重ね合わせ</option></select></label>
      {comparison.arrangement === 'grid'
        ? <><label><span>行×列</span><div className="property-pair"><input value={`${comparisonRows} 行`} readOnly aria-label="行数" /><input value={comparison.columns === 'auto' ? `自動・${comparisonColumns} 列` : `${comparisonColumns} 列`} readOnly aria-label="列数" /></div></label>
            <p className="property-editor-note"><ShieldCheck size={12} />列数は画面上部の「画面レイアウト」で選びます（XC-206）。行数はメンバー数（{effectiveMembers.length}件）から決まるため、どの列数でも絵に出ないメンバーは生まれません。</p></>
        : <div className="property-unresolved"><AlertTriangle size={13} /><span><b>結果色を持てるのは1メンバーだけです</b><small>「{comparison.members[0]}」に結果色を割り当て、残りは参照形状として描きます。2つのコンターを重ねた画は値を符号化しません。</small></span></div>}
      <label className="property-toggle"><span>ラベル</span><input type="checkbox" checked disabled readOnly /></label>
      <label className="property-toggle"><span>カラーマップを共有</span><input type="checkbox" checked={comparison.sharedColourMap} onChange={(event) => setComparison({ ...comparison, sharedColourMap: event.target.checked })} /></label>
      {comparison.sharedColourMap
        ? <p className="property-editor-note"><ShieldCheck size={12} />全メンバーが同じカラーマップと同じ範囲で描かれます。隣り合うペインを目で比べられるのは、これが保証されているときだけです。</p>
        : <p className="property-editor-note warning"><AlertTriangle size={12} />ペインごとに範囲が変わります。同じ色が別の値を意味するため、図とその書き出しの両方にその旨を明記します。</p>}
    </PropertyGroup>}
    <PropertyGroup title="ガイド">
      <label className="property-toggle"><span>座標軸</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>グリッド</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>方位ギズモ</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>スケールバー</span><input type="checkbox" /></label>
      <label className="property-toggle"><span>凡例</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>選択輪郭</span><input type="checkbox" defaultChecked /></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />ガイドは表示状態です。解析値と正規データは変更しません。</p>
  </div>

  if (tab.id === 'camera') return <div className="property-editor">
    {/* XC-199: the @View holds several cameras. The list is the object list; the groups below edit the
        selected one. A pane names the camera it looks through, so four panes can look from four places. */}
    <PropertyGroup title="カメラ">
      <div className="named-object-list" role="listbox" aria-label="このビューのカメラ">
        {viewItem.cameras.map((item) => {
          const resolution = resolveCamera(item, cameraUnresolved)
          return (
            <div className={`named-object-row ${selectedCameraId === item.id ? 'selected' : ''} ${resolution.state}`} key={item.id}>
              <button type="button" role="option" aria-selected={selectedCameraId === item.id} onClick={() => setSelectedCameraId(item.id)}>
                <span className="named-object-kind">{item.pose === 'explicit' ? <Crosshair size={12} /> : <Target size={12} />}</span>
                <span><b>{item.name}</b><small>{cameraRule(item)}</small><em>{resolution.detail}</em></span>
              </button>
              <button type="button" className={`named-object-active ${viewItem.activeCameraId === item.id ? 'on' : ''}`} aria-label={`${item.name}を表示中のカメラにする`} aria-pressed={viewItem.activeCameraId === item.id} onClick={() => onViewItemChange({ ...viewItem, activeCameraId: item.id })}><Eye size={12} /></button>
            </div>
          )
        })}
      </div>
      <div className="named-object-actions">
        <button type="button" onClick={() => setCameraDialogOpen(true)}><Plus size={12} />追加</button>
        <button type="button" disabled={!camera} onClick={duplicateCamera}><Copy size={12} />複製</button>
        <button type="button" disabled={!camera || viewItem.cameras.length <= 1} onClick={removeCamera}><Trash2 size={12} />削除</button>
      </div>
      <p className="property-editor-note"><ShieldCheck size={12} />規則で位置を決めるカメラは座標を保存しません。ケースごとに解決し、解決できないときはカメラを動かしません。</p>
    </PropertyGroup>
    {camera ? <>
      <PropertyGroup title="ポーズ">
        <label><span>名前</span><input value={camera.name} onChange={(event) => updateCamera({ name: event.target.value })} /></label>
        <label><span>決め方</span><select value={camera.pose} onChange={(event) => updateCamera({ pose: event.target.value as CameraModel['pose'], focus: event.target.value === 'explicit' ? null : camera.focus ?? { kind: 'extremum', quantity: '最大応力', statistic: '最大' } })}><option value="explicit">現在の位置を固定</option><option value="framed">対象を画面に収める</option></select></label>
        {camera.pose === 'framed' && <>
          <label><span>対象</span><select value={camera.focus?.kind ?? 'extremum'} onChange={(event) => updateCamera({ focus: event.target.value === 'extremum' ? { kind: 'extremum', quantity: '最大応力', statistic: '最大' } : event.target.value === 'object' ? { kind: 'object', label: '［選択したオブジェクト］' } : event.target.value === 'selection' ? { kind: 'selection', label: '［保存した選択］' } : { kind: 'position', label: '［座標］' } })}><option value="extremum">数量の極値</option><option value="object">オブジェクト</option><option value="selection">保存した選択</option><option value="position">座標</option></select></label>
          {camera.focus?.kind === 'extremum' && <>
            <label><span>数量</span><select value={camera.focus.quantity} onChange={(event) => updateCamera({ focus: { kind: 'extremum', quantity: event.target.value, statistic: camera.focus?.kind === 'extremum' ? camera.focus.statistic : '最大' } })}><option value="最大応力">最大応力</option><option value="変位">変位</option></select></label>
            <label><span>統計</span><select value={camera.focus.statistic} onChange={(event) => updateCamera({ focus: { kind: 'extremum', quantity: camera.focus?.kind === 'extremum' ? camera.focus.quantity : '最大応力', statistic: event.target.value as '最大' | '最小' | '絶対値最大' } })}><option value="最大">最大</option><option value="最小">最小</option><option value="絶対値最大">絶対値最大</option></select></label>
          </>}
          <label><span>余白</span><div className="property-range"><input type="range" min="0" max="50" defaultValue="12" /><output>12%</output></div></label>
        </>}
      </PropertyGroup>
      <PropertyGroup title="レンズ">
        <label><span>投影</span><select value={camera.projection} onChange={(event) => updateCamera({ projection: event.target.value as CameraModel['projection'] })}><option value="perspective">透視投影</option><option value="orthographic">平行投影</option></select></label>
        {camera.projection === 'perspective'
          ? <><label><span>焦点距離</span><div className="property-range"><input type="range" min="14" max="200" value={camera.focalLengthMm} onChange={(event) => updateCamera({ focalLengthMm: Number(event.target.value) })} /><output>{camera.focalLengthMm} mm</output></div></label>
              <label><span>センサー幅</span><input defaultValue="36 mm" /></label></>
          : <label><span>表示範囲</span><input defaultValue="［形状に合わせる］" /></label>}
        <label><span>クリップ</span><div className="property-pair"><input defaultValue="手前 0.01" aria-label="クリップ手前" /><input defaultValue="奥 1000" aria-label="クリップ奥" /></div></label>
        <label><span>シフト</span><div className="property-pair"><input defaultValue="X 0.00" aria-label="シフトX" /><input defaultValue="Y 0.00" aria-label="シフトY" /></div></label>
      </PropertyGroup>
      <PropertyGroup title="被写界深度" open={false}>
        <label className="property-toggle"><span>使用する</span><input type="checkbox" checked={camera.depthOfField} onChange={(event) => updateCamera({ depthOfField: event.target.checked })} /></label>
        {camera.depthOfField && <>
          <label><span>合焦先</span><select defaultValue="focus"><option value="focus">このカメラのフォーカス対象</option><option value="distance">距離を指定</option></select></label>
          <label><span>F値</span><div className="property-range"><input type="range" min="12" max="220" defaultValue="28" /><output>f/2.8</output></div></label>
          <label><span>絞り羽根</span><select defaultValue="0"><option value="0">円形</option><option value="6">6枚</option><option value="8">8枚</option></select></label>
        </>}
      </PropertyGroup>
      <PropertyGroup title="操作" open={false}>
        <label><span>回転中心</span><select defaultValue="selection"><option value="selection">選択中のオブジェクト</option><option value="bounds">形状の中心</option><option value="cursor">注視点</option></select></label>
        <label className="property-toggle"><span>カーソル方向へズーム</span><input type="checkbox" defaultChecked /></label>
      </PropertyGroup>
    </> : <div className="sidebar-context-state"><Camera size={22} /><b>カメラがありません</b><small>追加すると、画面への割り当てとカメラパスで使えます。</small></div>}
    <Dialog open={cameraDialogOpen} onOpenChange={setCameraDialogOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog">
      <header><span><small>カメラ</small><b>カメラを追加</b></span><button type="button" aria-label="カメラ追加を閉じる" onClick={() => setCameraDialogOpen(false)}><X size={15} /></button></header>
      <div className="settings-fields">
        <label><span>名前</span><input value={newCameraName} onChange={(event) => setNewCameraName(event.target.value)} placeholder="例：最大応力へ寄せる" /></label>
        <label><span>ポーズの決め方</span><Select value={newCameraKind} onValueChange={(value) => setNewCameraKind(value as typeof newCameraKind)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>
          <SelectItem value="explicit">現在のカメラを固定する</SelectItem>
          <SelectItem value="object">オブジェクトを画面に収める</SelectItem>
          <SelectItem value="selection">選択範囲を画面に収める</SelectItem>
          <SelectItem value="extremum">数量の極値へ寄せる</SelectItem>
        </SelectContent></Select></label>
      </div>
      <p className="workflow-trust-note"><ShieldCheck size={13} />規則を選んだ場合は条件だけを保存します。座標は保存せず、ケースごとに解決し直します。</p>
      <footer><button type="button" onClick={() => setCameraDialogOpen(false)}>キャンセル</button><button type="button" className="primary-button" disabled={!newCameraName.trim()} onClick={addCamera}>追加</button></footer>
    </DialogContent></Dialog>
  </div>

  if (tab.id === 'rendering') return <div className="property-editor">
    <PropertyGroup title="レンダラー">
      <label><span>方式</span><select value={renderer} onChange={(event) => setRenderer(event.target.value as 'vtk' | 'omniverse')}><option value="vtk">リアルタイム・VTK</option><option value="omniverse" disabled>フォトリアル・Omniverse（未接続）</option></select></label>
      <label><span>状態</span><input value={renderer === 'vtk' ? '利用可能・オフライン' : '利用不可・接続が必要'} readOnly /></label>
      <label><span>品質</span><select defaultValue="interactive"><option value="interactive">操作優先</option><option value="balanced">標準</option><option value="quality">品質優先</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="照明">
      <label><span>光源</span><select value={lightingSource} onChange={(event) => setLightingSource(event.target.value as typeof lightingSource)}><option value="studio">スタジオ</option><option value="background-environment">背景の環境</option><option value="unlit">照明なし</option></select></label>
      {lightingSource === 'background-environment' && <label><span>参照</span><input value="背景タブの環境アセットと回転" readOnly /></label>}
      {lightingSource !== 'unlit' && <>
        <label><span>照明強度</span><div className="property-range"><input type="range" min="0" max="200" defaultValue="100" /><output>100%</output></div></label>
        {lightingSource === 'studio' && <label><span>主光源</span><div className="property-range"><input type="range" min="0" max="100" defaultValue="70" /><output>70%</output></div></label>}
        <label className="property-toggle"><span>影</span><input type="checkbox" defaultChecked /></label>
        <label className="property-toggle"><span>環境遮蔽</span><input type="checkbox" defaultChecked /></label>
      </>}
    </PropertyGroup>
    {/* 現像 is the second group of 描画, after 照明 (XC-198). Its default applies no grade, and the
        note below is the rule the reference implementations do not have: a graded picture must not
        leave the legend saying a different value. */}
    <PropertyGroup title="現像">
      <VisualOptions label="プリセット" kind="grade" columns={3} value={grade} onChange={(value) => setGrade(value as GradePreset)}
        options={(Object.keys(gradePresets) as GradePreset[]).map((key) => ({ value: key, label: gradePresets[key].label, detail: `${gradePresets[key].label}・${gradePresets[key].tone}` }))} />
      <label><span>露光</span><input value={gradePresets[grade].exposure} readOnly={grade === 'measurement'} /></label>
      <label><span>トーンマップ</span><input value={gradePresets[grade].tone} readOnly={grade === 'measurement'} /></label>
      <label><span>画像処理</span><input value={gradePresets[grade].treatments} readOnly /></label>
      {grade !== 'measurement' && <>
        <label><span>コントラスト</span><div className="property-range"><input type="range" min="0" max="200" defaultValue="100" /><output>1.00</output></div></label>
        <label><span>色温度</span><div className="property-range"><input type="range" min="3000" max="9000" defaultValue="6500" /><output>6500 K</output></div></label>
        <label><span>凡例の扱い</span><select defaultValue="graded"><option value="graded">凡例も同じ補正を通す</option><option value="recorded">補正名とパラメータを出力に記載</option></select></label>
      </>}
      {grade === 'photoreal' && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>このレンダラーでは利用できません</b><small>フォトリアル経路は未接続です。VTK経路では影とレイトレースのサンプル数を適用しません。</small></span></div>}
    </PropertyGroup>
    <PropertyGroup title="画質" open={false}>
      <label><span>アンチエイリアス</span><select defaultValue="taa"><option value="none">なし</option><option value="fxaa">FXAA</option><option value="taa">TAA</option></select></label>
      <label><span>サンプル数</span><select defaultValue="8"><option value="1">1</option><option value="8">8</option><option value="64">64</option></select></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />未対応レンダラーへ黙って切り替えず、利用できない理由を表示します。</p>
    {grade === 'measurement'
      ? <p className="property-editor-note"><ShieldCheck size={12} />計測プリセットは無補正です。根拠として引用する画像はこの状態で出力します。</p>
      : <p className="property-editor-note warning"><AlertTriangle size={12} />補正を掛けた画像は、凡例も同じ補正を通すか、補正名とパラメータを成果物に記載します。値と色の対応が2枚の画像でずれないようにするためです。</p>}
  </div>

  if (tab.id === 'background') return <div className="property-editor">
    <PropertyGroup title="背景">
      <VisualOptions label="種類" kind="background" columns={4} value={backgroundMode} onChange={(value) => setBackgroundMode(value as typeof backgroundMode)}
        options={[{ value: 'solid', label: '単色' }, { value: 'gradient', label: 'グラデーション' }, { value: 'image', label: '画像' }, { value: 'environment', label: '環境' }]} />
      {backgroundMode === 'solid' && <label><span>カラー</span><input type="color" defaultValue="#1a2228" aria-label="背景色" /></label>}
      {backgroundMode === 'gradient' && <><label><span>上</span><input type="color" defaultValue="#182128" aria-label="背景グラデーション上端" /></label><label><span>下</span><input type="color" defaultValue="#2d3940" aria-label="背景グラデーション下端" /></label></>}
      {backgroundMode === 'image' && <><label><span>画像</span><select defaultValue="unresolved"><option value="unresolved">未選択</option></select></label><label><span>配置</span><select defaultValue="cover"><option value="cover">全体を覆う</option><option value="contain">全体を表示</option><option value="stretch">引き伸ばす</option></select></label></>}
      {backgroundMode === 'environment' && <><label><span>環境</span><select defaultValue="studio"><option value="studio">スタジオ・サンプル</option><option value="unresolved">未選択</option></select></label><label><span>回転</span><div className="property-range"><input type="range" min="-180" max="180" defaultValue="0" /><output>0°</output></div></label></>}
      <label><span>表示強度</span><div className="property-range"><input type="range" min="0" max="200" defaultValue="100" /><output>100%</output></div></label>
      <label className="property-toggle"><span>カメラに表示</span><input type="checkbox" defaultChecked /></label>
    </PropertyGroup>
    <p className="property-editor-note"><ImageIcon size={12} />再利用する背景は素材ライブラリから適用し、このタブでは現在のビューへの配置を調整します。</p>
  </div>

  return <div className="property-editor">
    <PropertyGroup title="成果物">
      {/* XC-210: a split is not an export path. Saying so here is the point - this is the tab a user
          opens expecting the side-by-side they are looking at. */}
      {splitPanes > 1 && !isComparisonItem && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>画面分割は書き出しに含まれません</b><small>いま{splitPanes}画面に分けていますが、出力は下で選ぶカメラ1つの絵です。並べた図が必要な場合は、画面上部の「画面レイアウト」から「この比較を保存」で比較項目にします。</small></span></div>}
      <label><span>種類</span><select value={outputMode} onChange={(event) => setOutputMode(event.target.value as typeof outputMode)}><option value="image">画像</option><option value="video" disabled={!canWriteVideo}>動画{hasResultAxis ? '' : '・この結果には軸がありません'}</option></select></label>
      {axisPinsEveryPane && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>この比較は結果位置を軸にしています</b><small>各ペインが別々の位置に固定されるため、再生する余地がありません。動画にする場合は、軸をケース・カメラなどに変え、結果位置を共有にします。</small></span></div>}
      {!hasResultAxis && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>ケース「{selectedCase}」は定常結果です</b><small>再生する軸がないため、動画とその再生プリセットは選べません。画像とインタラクティブは通常どおり出力できます。</small></span></div>}
      {outputMode === 'image' ? <>
        <label><span>形式</span><select defaultValue="png"><option value="png">PNG</option><option value="jpeg">JPEG</option><option value="tiff">TIFF</option></select></label>
        <label><span>サイズ</span><select defaultValue="1920x1080"><option value="1920x1080">1920 × 1080</option><option value="3840x2160">3840 × 2160</option><option value="viewport">現在の表示領域</option></select></label>
        <label className="property-toggle"><span>背景を透過</span><input type="checkbox" /></label>
        {/* XC-212: a @Comparison already fixes both of these - one as the axis it varies, the other as
            the shared binding in the 比較 tab. Asking again here would be a second control for one
            value, and the two could disagree in the file that gets sent to someone. */}
        {isComparisonItem ? <>
          <label><span>カメラ</span><input value={comparison.axis === 'camera' ? '比較の軸・メンバーごと' : '比較で共有・比較タブで設定'} readOnly /></label>
          <label><span>結果位置</span><input value={comparison.axis === 'resultPosition' ? '比較の軸・メンバーごと' : '比較で共有・比較タブで設定'} readOnly /></label>
        </> : <>
          <label><span>カメラ</span><select defaultValue={viewItem.activeCameraId}>{viewItem.cameras.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
          <label><span>結果位置</span><select defaultValue="current"><option value="current">現在の位置</option>{viewItem.bookmarks.map((entry) => <option value={entry.id} key={entry.id}>ブックマーク：{entry.name}</option>)}</select></label>
        </>}
      </> : <>
        <label><span>形式</span><select defaultValue="mp4"><option value="mp4">MP4</option><option value="webm">WebM</option><option value="frames">PNG連番</option></select></label>
        {/* Motion belongs to the timeline, not to the file it is written into (XC-196 correction). */}
        <label><span>タイムライン</span><select value={selectedTimelineId} onChange={(event) => { setSelectedTimelineId(event.target.value); onViewItemChange({ ...viewItem, activeTimelineId: event.target.value }) }}>{viewItem.timelines.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
      </>}
    </PropertyGroup>
    {outputMode === 'video' && canWriteVideo && <PropertyGroup title="再生プリセット">
      {/* XC-200: a timeline is six values and carries no camera. The video above names one timeline and
          one camera, which is what lets the same motion be replayed from somewhere else. */}
      <div className="named-object-list" role="listbox" aria-label="このビューの再生プリセット">
        {viewItem.timelines.map((item) => (
          <div className={`named-object-row ${selectedTimelineId === item.id ? 'selected' : ''}`} key={item.id}>
            <button type="button" role="option" aria-selected={selectedTimelineId === item.id} onClick={() => setSelectedTimelineId(item.id)}>
              <span className="named-object-kind"><Film size={12} /></span>
              <span><b>{item.name}</b><small>{bookmarkName(item.fromBookmarkId)} → {bookmarkName(item.toBookmarkId)}</small><em>{item.speed}×・{item.frameRate} fps{item.loop ? '・繰り返し' : ''}</em></span>
            </button>
          </div>
        ))}
      </div>
      <div className="named-object-actions">
        <button type="button" onClick={addTimeline}><Plus size={12} />追加</button>
        <button type="button" disabled={!timeline || viewItem.timelines.length <= 1} onClick={removeTimeline}><Trash2 size={12} />削除</button>
      </div>
      {timeline && <>
        <label><span>名前</span><input value={timeline.name} onChange={(event) => updateTimeline({ name: event.target.value })} /></label>
        {timelineReversed && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>終了が開始より手前に解決します</b><small>ケース「{selectedCase}」では終了位置が開始位置より前になります。位置を入れ替えるまで出力を拒否します。</small></span></div>}
        <label><span>開始</span><select value={timeline.fromBookmarkId} onChange={(event) => updateTimeline({ fromBookmarkId: event.target.value })}><option value="first">軸の先頭</option>{viewItem.bookmarks.map((entry) => <option value={entry.id} key={entry.id}>{entry.name}</option>)}</select></label>
        <label><span>終了</span><select value={timeline.toBookmarkId} onChange={(event) => updateTimeline({ toBookmarkId: event.target.value })}><option value="last">軸の末尾</option>{viewItem.bookmarks.map((entry) => <option value={entry.id} key={entry.id}>{entry.name}</option>)}</select></label>
        <label><span>間引き</span><select value={timeline.stride} onChange={(event) => updateTimeline({ stride: Number(event.target.value) })}><option value={1}>保存位置をすべて</option><option value={2}>2つおき</option><option value={5}>5つおき</option></select></label>
        <label><span>速度</span><select value={timeline.speed} onChange={(event) => updateTimeline({ speed: Number(event.target.value) })}><option value={0.25}>0.25×</option><option value={0.5}>0.5×</option><option value={1}>1.0×</option><option value={2}>2.0×</option><option value={4}>4.0×</option></select></label>
        <label><span>フレームレート</span><select value={timeline.frameRate} onChange={(event) => updateTimeline({ frameRate: Number(event.target.value) })}><option value={24}>24 fps</option><option value={30}>30 fps</option><option value={60}>60 fps</option></select></label>
        <label className="property-toggle"><span>繰り返し</span><input type="checkbox" checked={timeline.loop} onChange={(event) => updateTimeline({ loop: event.target.checked })} /></label>
        <label><span>解決結果</span><input value={cameraUnresolved ? '未解決・規則が参照する数量がありません' : '［開始位置］〜［終了位置］・ケースごとに解決'} readOnly /></label>
      </>}
      <p className="property-editor-note"><ShieldCheck size={12} />プリセットは「いつ」だけを持ちます。「どこから」は上のカメラで選ぶため、同じプリセットを別のカメラで再生できます。</p>
    </PropertyGroup>}
    <PropertyGroup title="保存先">
      <label><span>パターン</span><input value="output/view/<run>/<case>/" readOnly /></label>
      <label><span>既存出力</span><input value="上書きしない" readOnly /></label>
    </PropertyGroup>
    <div className="property-panel-action"><button type="button" className="primary-button" onClick={() => setPreflightOpen(true)}><ShieldCheck size={12} />出力前チェック</button></div>
    {outputStarted && <p className="property-editor-note" role="status"><CircleDashed size={12} />出力を開始しました。通知履歴から進行状況を確認できます。</p>}
    <OutputPreflightDialog open={preflightOpen} onOpenChange={setPreflightOpen} title={outputMode === 'image' ? 'ビュー画像' : 'ビュー動画'} checks={outputMode === 'image' ? [{ label: 'レンダラー', detail: 'VTK経路を利用可能', status: 'pass' }, { label: '保存先', detail: '新規実行フォルダー・衝突なし', status: 'pass' }] : [{ label: 'カメラパス', detail: '名前付きカメラパスが選択されていません', status: 'blocked' }, { label: '時間対応', detail: '結果軸と壁時計時間の対応を出力に記載', status: 'warning' }]} onStart={() => { setOutputStarted(true); setPreflightOpen(false) }} />
  </div>
}

function GraphPropertyEditor({ tab, variant }: { tab: SidebarTab; variant: string }) {
  const [dimension, setDimension] = useState<'2d' | '3d'>('2d')
  const [chartKind, setChartKind] = useState('line')
  const [palette, setPalette] = useState('accessible')
  const [chartBackground, setChartBackground] = useState('light')
  const [defaultMarker, setDefaultMarker] = useState('circle')
  const [defaultWidth, setDefaultWidth] = useState('2')
  const [seriesLine, setSeriesLine] = useState('solid')
  const [seriesMarker, setSeriesMarker] = useState('theme')
  const [seriesWidth, setSeriesWidth] = useState('theme')
  const [outputKind, setOutputKind] = useState<'image' | 'vector' | 'data' | 'animation'>('image')
  const [preflightOpen, setPreflightOpen] = useState(variant === 'output-preflight')
  const [outputStarted, setOutputStarted] = useState(false)
  const [caseSelectionMode, setCaseSelectionMode] = useState<'selected' | 'saved' | 'tag' | 'code'>('selected')
  const [graphSeries, setGraphSeries] = useState([{ id: 'series-1', label: '系列 1', quantity: 'unresolved', source: 'dataset' }])
  const [activeSeriesId, setActiveSeriesId] = useState('series-1')
  const activeSeries = graphSeries.find((series) => series.id === activeSeriesId) ?? graphSeries[0]
  const unresolvedSeries = graphSeries.filter((series) => series.quantity === 'unresolved')
  // XC-213: the measured reference carries 25 properties per axis and repeats them for four axes -
  // 100 of its 115 chart properties, in 20 of its 23 panel groups (E-124). One axis is chosen here and
  // the same fields serve all of them, which is the same information in one twentieth of the panel.
  const [axis, setAxis] = useState<'x' | 'y' | 'y2'>('x')
  const [axisAuto, setAxisAuto] = useState(true)
  const axisNames: Record<'x' | 'y' | 'y2', string> = { x: 'X（横）', y: 'Y（左）', y2: '第2Y（右）' }

  if (tab.id === 'overall') return <div className="property-editor">
    <PropertyGroup title="グラフ">
      <label><span>名前</span><input defaultValue="ケース比較" /></label>
      <label><span>タイトル</span><input defaultValue="最大変位の比較" /></label>
      <label><span>副題</span><input placeholder="任意" /></label>
      <label><span>説明</span><textarea rows={3} placeholder="図が示す内容を記載" /></label>
    </PropertyGroup>
    {/* XC-213: the chart kind is two fields and the first thing chosen; a tab of its own was a click
        to reach a pair of selects. The measured reference spends its panel on axes instead (E-124). */}

    <PropertyGroup title="次元">
      <label><span>次元</span><select value={dimension} onChange={(event) => setDimension(event.target.value as typeof dimension)}><option value="2d">2D</option><option value="3d">3D</option></select></label>
      {/* XC-215: the shape of a chart is the thing being chosen, so it is drawn. */}
      <VisualOptions label="種類" kind="chart" columns={3} value={chartKind} onChange={setChartKind}
        options={dimension === '2d'
          ? [{ value: 'line', label: '折れ線' }, { value: 'scatter', label: '散布図' }, { value: 'bar', label: '棒' }, { value: 'distribution', label: '分布' }, { value: 'heatmap', label: 'ヒートマップ' }]
          : [{ value: 'surface', label: 'サーフェス' }, { value: 'scatter3d', label: '3D散布図' }, { value: 'contour3d', label: '2変数コンター' }]} />
    </PropertyGroup>
    {dimension === '3d' && <PropertyGroup title="投影">
      <label><span>投影</span><select defaultValue="perspective"><option value="perspective">透視投影</option><option value="orthographic">平行投影</option></select></label>
      <label><span>視線</span><select defaultValue="saved"><option value="saved">保存済み</option><option value="isometric">等角</option><option value="front">正面</option><option value="top">上</option></select></label>
    </PropertyGroup>}
    <p className="property-editor-note"><ChartNoAxesCombined size={12} />種類を変えても数量の参照と単位互換性の検証は維持されます。</p>
    <PropertyGroup title="構成">
      <label className="property-toggle"><span>タイトルを表示</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>凡例を表示</span><input type="checkbox" defaultChecked /></label>
      <label><span>凡例位置</span><select defaultValue="right"><option value="right">右</option><option value="bottom">下</option><option value="inside">プロット内</option></select></label>
    </PropertyGroup>
    {/* XC-221: which cases the graph covers is a property of the graph, not of one series - a series
        spans every selected case. These sat in the series tab only because it used to be called データ
        and collected everything data-shaped. */}
    <PropertyGroup title="ケース選択">
      <label><span>対象</span><select value={caseSelectionMode} onChange={(event) => setCaseSelectionMode(event.target.value as typeof caseSelectionMode)}><option value="selected">選択中のケース</option><option value="saved">保存済み選択</option><option value="tag">宣言的な条件</option><option value="code">Python選択</option></select></label>
      {caseSelectionMode === 'saved' && <label><span>選択</span><select defaultValue="unresolved"><option value="unresolved">選択を指定</option></select></label>}
      {caseSelectionMode === 'tag' && <label><span>条件</span><input placeholder="タグ・状態・変数の条件" /></label>}
      {caseSelectionMode === 'code' && <><label><span>スクリプト</span><textarea rows={3} defaultValue={'def select(cases):\n    return []'} /></label><p className="property-editor-note"><ShieldCheck size={12} />メタデータだけを受け取り、ファイル・データセット・ネットワークへアクセスしません。失敗は空選択ではなく拒否として報告します。</p></>}
      <label><span>選択結果</span><input value={caseSelectionMode === 'selected' ? '選択中のケース・1件' : '条件の解決待ち'} readOnly /></label>
      <label><span>反復</span><select defaultValue="separate"><option value="separate">反復ごとに表示</option><option value="combined">反復を集約</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="集約" open={false}>
      <label><span>方法</span><select defaultValue="none"><option value="none">集約しない</option><option value="weighted">関連量で重み付け</option><option value="unweighted">単純平均・重みなし</option></select></label>
      <label><span>範囲</span><select defaultValue="whole"><option value="whole">全体</option><option value="selection">選択範囲</option></select></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />グラフは値のコピーではなく、数量・単位・来歴を参照する定義として保存します。</p>
  </div>

  if (tab.id === 'series') return <div className="property-editor">
    <PropertyGroup title="系列">
      <div className="compact-definition-list"><div role="listbox" aria-label="グラフ系列">{graphSeries.map((series) => <button type="button" role="option" aria-selected={activeSeriesId === series.id} className={activeSeriesId === series.id ? 'selected' : ''} onClick={() => setActiveSeriesId(series.id)} key={series.id}><span><b>{series.label}</b><small>{series.quantity === 'unresolved' ? '数量未選択' : series.quantity === 'expression' ? '式による計算・解析モジュール' : '数量参照・単位未宣言'}</small></span>{series.quantity === 'unresolved' && <AlertTriangle size={12} />}</button>)}</div><aside><button type="button" aria-label="系列を追加" onClick={() => { const id = `series-${graphSeries.length + 1}`; setGraphSeries((current) => [...current, { id, label: `系列 ${current.length + 1}`, quantity: 'unresolved', source: 'dataset' }]); setActiveSeriesId(id) }}><Plus size={12} /></button><button type="button" aria-label="選択中の系列を削除" disabled={graphSeries.length === 1} onClick={() => { const next = graphSeries.filter((series) => series.id !== activeSeriesId); setGraphSeries(next); setActiveSeriesId(next[0]?.id ?? '') }}><X size={12} /></button></aside></div>
      {activeSeries && <><label><span>X</span><select defaultValue="parameter"><option value="parameter">パラメーターを選択</option><option value="result-axis">結果軸</option></select></label>
        <label><span>Y</span><select value={activeSeries.quantity} onChange={(event) => setGraphSeries((current) => current.map((series) => series.id === activeSeries.id ? { ...series, quantity: event.target.value } : series))}><option value="unresolved">数量を選択</option><option value="dataset">データセットの数量</option><option value="computed">計算済み数量</option><option value="measurement">測定値</option><option value="reference">参考ファイルの値</option><option value="expression">式</option></select></label>
        {activeSeries.quantity === 'expression' && <ExpressionEditor id={`graph-${activeSeries.id}`} label="系列の式" initial="設計許容応力 / 最大応力" />}
        <label><span>単位</span><input value={activeSeries.quantity === 'unresolved' ? '数量の選択後に表示' : '未宣言'} readOnly /></label>
        {/* XC-213: colour, line and marker belong to the series, not to the chart - the measured
            reference keys all three to the series (E-124), and splitting them across two tabs meant
            changing one series' look and its quantity in two places. */}
        <label><span>色</span><div className="property-pair"><select defaultValue="palette"><option value="palette">パレット順</option><option value="custom">指定色</option></select><input type="color" defaultValue="#2f6df6" aria-label={`${activeSeries.label}の色`} /></div></label>
        <label><span>パレット</span><span className="palette-readout"><OptionSample kind="palette" value={palette} /><small>この系列は{['1番目','2番目','3番目','4番目','5番目'][graphSeries.indexOf(activeSeries) % 5]}の色を使います</small></span></label>
        {/* XC-221: the first option is the theme's, drawn as the theme currently resolves it, so the
            relationship between the two tabs is on screen instead of being two identical pickers. */}
        <VisualOptions label="線" kind="line" columns={4} value={seriesLine} onChange={setSeriesLine}
          options={[{ value: 'solid', label: '実線' }, { value: 'dashed', label: '破線' }, { value: 'dotted', label: '点線' }, { value: 'none', label: 'なし' }]} />
        <label><span>線幅</span><select value={seriesWidth} onChange={(event) => setSeriesWidth(event.target.value)}><option value="theme">テーマに従う（{defaultWidth} px）</option>{['1', '2', '3', '4', '5', '6'].map((w) => <option value={w} key={w}>{w} px</option>)}</select></label>
        <VisualOptions label="マーカー" kind="marker" columns={5} value={seriesMarker} onChange={setSeriesMarker}
          options={[{ value: 'theme', label: 'テーマ', sample: defaultMarker, detail: `テーマに従う（${{ circle: '円', square: '四角', triangle: '三角', none: 'なし' }[defaultMarker] ?? defaultMarker}）` }, { value: 'circle', label: '円' }, { value: 'square', label: '四角' }, { value: 'triangle', label: '三角' }, { value: 'none', label: 'なし' }]} />
        <label><span>軸</span><select defaultValue="left"><option value="left">左（Y）</option><option value="right">右（第2Y）</option></select></label>
        <label><span>来歴</span><input value={activeSeries.quantity === 'unresolved' ? '数量の選択後に表示' : activeSeries.quantity === 'computed' || activeSeries.quantity === 'expression' ? '計算・式を表示' : activeSeries.quantity === 'reference' ? '参考資料・数値根拠には未使用' : activeSeries.quantity === 'measurement' ? '測定データ' : 'データセット'} readOnly /></label>
        <label><span>欠損</span><select defaultValue="gap"><option value="gap">欠損として表示・凡例に残す</option></select></label></>}
    </PropertyGroup>
        <p className="property-editor-note"><ShieldCheck size={12} />未選択・未宣言・欠損はそのまま表示し、ゼロや近傍値へ置き換えません。</p>
  </div>

  if (tab.id === 'axes') return <div className="property-editor">
    <div className="axis-picker" role="tablist" aria-label="設定する軸">
      {(['x', 'y', 'y2'] as const).map((value) => (
        <button type="button" role="tab" aria-selected={axis === value} className={axis === value ? 'active' : ''} key={value} onClick={() => setAxis(value)}>{axisNames[value]}</button>
      ))}
    </div>
    <PropertyGroup title="表題">
      <label><span>表題</span><input placeholder={`${axisNames[axis]}の表題`} /></label>
      <label><span>単位の併記</span><select defaultValue="declared"><option value="declared">宣言済みのとき付ける</option><option value="never">付けない</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="範囲">
      <label className="property-toggle"><span>自動</span><input type="checkbox" checked={axisAuto} onChange={(event) => setAxisAuto(event.target.checked)} /></label>
      {!axisAuto && <>
        <label><span>最小</span><input defaultValue="0" /></label>
        <label><span>最大</span><input defaultValue="250" /></label>
      </>}
      <label className="property-toggle"><span>対数目盛</span><input type="checkbox" /></label>
      {/* XC-001 applied to a picture: a fixed range that hides part of the data is a chart that reads as
          if the data ended there. It is allowed, and it is stated. */}
      {!axisAuto && <p className="property-editor-note warning"><AlertTriangle size={12} />固定範囲の外にある点は描かれません。範囲外の点があるときは、図とその書き出しの両方にその旨を記載します。</p>}
    </PropertyGroup>
    <PropertyGroup title="目盛" open={false}>
      <label><span>間隔</span><select defaultValue="auto"><option value="auto">自動</option><option value="custom">指定</option></select></label>
      <label><span>表記</span><select defaultValue="auto"><option value="auto">自動</option><option value="fixed">小数固定</option><option value="scientific">指数</option></select></label>
      <label><span>桁数</span><select defaultValue="3"><option value="2">2</option><option value="3">3</option><option value="4">4</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="グリッド" open={false}>
      <label className="property-toggle"><span>主グリッド</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>副グリッド</span><input type="checkbox" /></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />軸の設定は{axisNames[axis]}にだけ適用されます。単位は数量の宣言から取り、ここでは推測しません。</p>
  </div>

  if (tab.id === 'style') return <div className="property-editor">
    <PropertyGroup title="スタイル">
      {/* XC-216: the rail says which library resource is in effect; the shelf is where one is chosen.
          The field was called アセット here and スタイル in Report - one name for one thing. */}
      <label><span>適用中</span><select defaultValue="technical"><option value="technical">技術資料・標準</option><option value="workspace">ワークスペース設定</option></select></label>
      <VisualOptions label="配色" kind="palette" columns={3} value={palette} onChange={setPalette}
        options={[{ value: 'accessible', label: '識別性優先' }, { value: 'monochrome', label: 'モノクロ' }, { value: 'print', label: '印刷向け' }]} />
      <VisualOptions label="背景" kind="background" columns={3} value={chartBackground} onChange={setChartBackground}
        options={[{ value: 'light', label: '明るい' }, { value: 'transparent', label: '透過' }, { value: 'dark', label: '暗い' }]} />
    </PropertyGroup>
    {/* XC-213: these are the defaults a new series starts from. What a *particular* series looks like
        is on that series' row in データ, because the measured reference keys line, marker and colour to
        the series rather than to the chart (E-124). Grid lines moved to 軸, which is what they mark. */}
    {/* XC-221: what a series looks like unless it says otherwise. `auto` used to be the value here and
        was not one of the four options, so the control rendered with nothing selected - and the series
        tab offered the same four with no way to say "follow this", which made two identical pickers. */}
    <PropertyGroup title="系列の既定">
      <label><span>線幅</span><select value={defaultWidth} onChange={(event) => setDefaultWidth(event.target.value)}>{['1', '2', '3', '4', '5', '6'].map((w) => <option value={w} key={w}>{w} px</option>)}</select></label>
      <VisualOptions label="マーカー" kind="marker" columns={4} value={defaultMarker} onChange={setDefaultMarker}
        options={[{ value: 'circle', label: '円' }, { value: 'square', label: '四角' }, { value: 'triangle', label: '三角' }, { value: 'none', label: 'なし' }]} />
      <p className="property-editor-note"><ShieldCheck size={12} />各系列は既定のまま描かれ、系列タブで「テーマ」以外を選んだ系列だけがそこを上書きします。</p>
    </PropertyGroup>
    <PropertyGroup title="書体">
      <label><span>フォント</span><select defaultValue="workspace"><option value="workspace">ワークスペース設定</option><option value="noto-sans">Noto Sans</option><option value="source-serif">Source Serif</option></select></label>
      <label><span>タイトル</span><select defaultValue="14"><option value="12">12 pt</option><option value="14">14 pt</option><option value="16">16 pt</option></select></label>
      <label><span>軸</span><select defaultValue="10"><option value="9">9 pt</option><option value="10">10 pt</option><option value="11">11 pt</option></select></label>
      <label><span>凡例</span><select defaultValue="9"><option value="8">8 pt</option><option value="9">9 pt</option><option value="10">10 pt</option></select></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />出力では使用文字を検査し、必要な字体をライセンス条件に従って埋め込みます。素材ライブラリの「スタイル」は配色とプロットの既定に、「テキスト」は書体に適用されます。ここでは適用後のこのグラフの状態を調整します。</p>
  </div>

  return <div className="property-editor">
    <PropertyGroup title="成果物">
      <label><span>種類</span><select value={outputKind} onChange={(event) => setOutputKind(event.target.value as typeof outputKind)}><option value="image">画像</option><option value="vector">ベクター</option><option value="data">表データ</option><option value="animation">アニメーション</option></select></label>
      {outputKind === 'image' && <><label><span>形式</span><select defaultValue="png"><option value="png">PNG</option><option value="jpeg">JPEG</option><option value="tiff">TIFF</option></select></label><label><span>サイズ</span><select defaultValue="1600x900"><option value="1600x900">1600 × 900</option><option value="2400x1350">2400 × 1350</option></select></label></>}
      {outputKind === 'vector' && <label><span>形式</span><select defaultValue="svg"><option value="svg">SVG</option><option value="pdf">PDF</option></select></label>}
      {outputKind === 'data' && <><label><span>形式</span><select defaultValue="csv"><option value="csv">CSV</option><option value="xlsx">Excel</option></select></label><label className="property-toggle"><span>来歴列</span><input type="checkbox" defaultChecked /></label></>}
      {outputKind === 'animation' && <><label><span>形式</span><select defaultValue="mp4"><option value="mp4">MP4</option><option value="webm">WebM</option></select></label><label><span>時間対応</span><select defaultValue="result"><option value="result">結果軸を使用</option></select></label></>}
    </PropertyGroup>
    <PropertyGroup title="保存先">
      <label><span>パターン</span><input value="output/graph/<run>/<case>/" readOnly /></label>
      <label><span>既存出力</span><input value="上書きしない" readOnly /></label>
    </PropertyGroup>
    <div className="property-panel-action"><button type="button" className="primary-button" onClick={() => setPreflightOpen(true)}><ShieldCheck size={12} />出力前チェック</button></div>
    {outputStarted && <p className="property-editor-note" role="status"><CircleDashed size={12} />出力を開始しました。画面と同じ定義から生成します。</p>}
    <OutputPreflightDialog open={preflightOpen} onOpenChange={setPreflightOpen} title="グラフ成果物" checks={[
      unresolvedSeries.length > 0
        ? { label: '系列', detail: `${unresolvedSeries.map((series) => series.label).join('・')}のY数量が未選択です`, status: 'blocked' as const }
        : { label: '系列', detail: `${graphSeries.length}系列すべてに数量が選ばれています`, status: 'pass' as const },
      unresolvedSeries.length > 0
        ? { label: '単位', detail: '数量の選択後に互換性を検証します', status: 'blocked' as const }
        : { label: '単位', detail: '未宣言の単位があります。出力には未宣言と明記します', status: 'warning' as const },
      { label: '保存先', detail: '既存成果物を上書きしない', status: 'pass' as const },
    ]} onStart={() => { setOutputStarted(true); setPreflightOpen(false) }} />
  </div>
}

function ReportPropertyEditor({ tab, variant }: { tab: SidebarTab; variant: string }) {
  const [orientation, setOrientation] = useState('portrait')
  const [margin, setMargin] = useState('standard')
  const [columns, setColumns] = useState('single')
  const [reportPalette, setReportPalette] = useState('accessible')
  const [figureStyle, setFigureStyle] = useState('flat')
  const [bodyFont, setBodyFont] = useState('workspace')
  const [commentary, setCommentary] = useState<'mechanical' | 'generated'>(variant === 'commentary-review' || variant === 'drafting' ? 'generated' : 'mechanical')
  const [draftState, setDraftState] = useState<'none' | 'review' | 'applied'>(variant === 'commentary-review' ? 'review' : 'none')
  const [search, setSearch] = useState<'off' | 'ask'>('off')
  const [reportOutput, setReportOutput] = useState<'html' | 'pptx' | 'docx' | 'xlsx' | 'csv' | 'image' | 'video' | 'text' | 'markdown'>('html')
  const [preflightOpen, setPreflightOpen] = useState(variant === 'output-preflight')
  const [outputStarted, setOutputStarted] = useState(false)
  const [reportBlocks, setReportBlocks] = useState([
    { id: 'limitations', name: '制限事項', detail: '必須・省略不可', locked: true },
    { id: 'view', name: 'ビュー', detail: '開いているビュー・静止画', locked: false },
    { id: 'provenance', name: '来歴', detail: '必須・省略不可', locked: true },
  ])

  if (tab.id === 'overall') return <div className="property-editor">
    <PropertyGroup title="レポート">
      <label><span>名前</span><input defaultValue="設計レビュー" /></label>
      <label><span>タイトル</span><input defaultValue="解析結果レポート" /></label>
      <label><span>言語</span><select defaultValue="ja"><option value="ja">日本語</option><option value="en">English</option></select></label>
      <label><span>テンプレート</span><input value="技術メモ・サンプル / リビジョン未接続" readOnly /></label>
    </PropertyGroup>
    <PropertyGroup title="必須情報">
      <label className="property-toggle"><span>来歴</span><input type="checkbox" checked disabled readOnly /></label>
      <label className="property-toggle"><span>宣言単位</span><input type="checkbox" checked disabled readOnly /></label>
      <label className="property-toggle"><span>制限事項</span><input type="checkbox" checked disabled readOnly /></label>
      <label className="property-toggle"><span>製品バージョン</span><input type="checkbox" checked disabled readOnly /></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />必須情報は省略できません。レポートは不明点と未宣言単位を明示します。</p>
  </div>

  if (tab.id === 'style') return <div className="property-editor">
    {/* XC-214: page, palette and type are one theme. The measured reference keeps exactly this split -
        a document-wide theme covering colours, fonts and shapes, and per-block styling reached from the
        block itself (E-127) - so three tabs for one theme was three clicks to change one look. */}

    <PropertyGroup title="ページ">
      <label><span>用紙</span><select defaultValue="a4"><option value="a4">A4</option><option value="letter">Letter</option><option value="screen">画面向け</option></select></label>
      {/* XC-215: orientation, margin and columns are shapes on a page, so the page is drawn. */}
      <VisualOptions label="向き" kind="page" columns={2} value={orientation} onChange={setOrientation}
        options={[{ value: 'portrait', label: '縦' }, { value: 'landscape', label: '横' }]} />
      <VisualOptions label="余白" kind="margin" columns={3} value={margin} onChange={setMargin}
        options={[{ value: 'narrow', label: '狭い' }, { value: 'standard', label: '標準' }, { value: 'wide', label: '広い' }]} />
      <VisualOptions label="段組み" kind="columns" columns={2} value={columns} onChange={setColumns}
        options={[{ value: 'single', label: '1段' }, { value: 'double', label: '2段' }]} />
    </PropertyGroup>
    <PropertyGroup title="共通要素">
      <label className="property-toggle"><span>ヘッダー</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>フッター</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>ページ番号</span><input type="checkbox" defaultChecked /></label>
      <label><span>図の幅</span><select defaultValue="column"><option value="column">段幅</option><option value="page">ページ幅</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="アートスタイル">
      <label><span>適用中</span><select defaultValue="technical"><option value="technical">技術資料・標準</option><option value="workspace">ワークスペース設定</option></select></label>
      <VisualOptions label="配色" kind="palette" columns={3} value={reportPalette} onChange={setReportPalette}
        options={[{ value: 'accessible', label: '識別性優先' }, { value: 'monochrome', label: 'モノクロ印刷' }, { value: 'print', label: '印刷向け' }]} />
      <VisualOptions label="図表" kind="figure" columns={2} value={figureStyle} onChange={setFigureStyle}
        options={[{ value: 'flat', label: 'フラット' }, { value: 'bordered', label: '罫線あり' }]} />
      <label className="property-toggle"><span>表の縞</span><input type="checkbox" defaultChecked /></label>
    </PropertyGroup>

    <PropertyGroup title="文字表現">
      <label><span>本文</span><select value={bodyFont} onChange={(event) => setBodyFont(event.target.value)} style={{ fontFamily: fontStacks[bodyFont] }}>{Object.entries(fontLabels).map(([value, name]) => <option value={value} key={value} style={{ fontFamily: fontStacks[value] }}>{name}</option>)}</select></label>
      <label><span>見本</span><span className="font-specimen" style={{ fontFamily: fontStacks[bodyFont] }}>最大応力 235 MPa / Design review 2026</span></label>
      <label><span>見出し</span><select defaultValue="same"><option value="same">本文と同じ</option><option value="noto-sans">Noto Sans</option></select></label>
      <label><span>本文サイズ</span><select defaultValue="10"><option value="9">9 pt</option><option value="10">10 pt</option><option value="11">11 pt</option></select></label>
      <label><span>注記サイズ</span><select defaultValue="8"><option value="8">8 pt</option><option value="9">9 pt</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="埋め込み">
      <label><span>状態</span><input value="使用文字を出力前に検査" readOnly /></label>
      <label><span>範囲</span><input value="使用グリフのみ" readOnly /></label>
    </PropertyGroup>
    <p className="property-editor-note"><Paintbrush size={12} />テーマは文章や解析値を変更せず、ページ・配色・書体・図表表現だけに適用されます。</p>
    {/* XC-216: three library categories write into this one tab, and each writes a different group, so
        applying two of them is not a conflict. Saying which is what makes that readable. */}
    <p className="property-editor-note"><Grid2X2 size={12} />素材ライブラリの「レイアウト」はページと共通要素、「スタイル」は配色と図表、「テキスト」は書体に適用されます。互いに上書きしません。</p>
    <p className="property-editor-note"><ShieldCheck size={12} />表示できない文字は、空の四角で出力せず要素と文字を特定して報告します。</p>
  </div>

  if (tab.id === 'contents') return <div className="property-editor">
    <PropertyGroup title="参照範囲">
      <label><span>ワークスペース</span><select defaultValue="current"><option value="current">現在のワークスペース</option><option value="multiple">複数を選択</option></select></label>
      <label><span>ケース</span><select defaultValue="selected"><option value="selected">選択中のケース</option><option value="selection">保存済み選択</option></select></label>
      <label><span>参考資料</span><select defaultValue="none"><option value="none">なし</option><option value="workspace">登録済み資料</option></select></label>
      <label><span>解決結果</span><input value="現在のワークスペース・選択中のケース" readOnly /></label>
    </PropertyGroup>
    <PropertyGroup title="収録項目">
      <div className="report-block-list" aria-label="レポートブロック">{reportBlocks.map((block, index) => <article key={block.id}><span><b>{block.name}</b><small>{block.detail}</small></span><div><button type="button" aria-label={`${block.name}を上へ移動`} disabled={index === 0} onClick={() => setReportBlocks((current) => { const next = [...current]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; return next })}><ChevronUp size={12} /></button><button type="button" aria-label={`${block.name}を下へ移動`} disabled={index === reportBlocks.length - 1} onClick={() => setReportBlocks((current) => { const next = [...current]; [next[index], next[index + 1]] = [next[index + 1], next[index]]; return next })}><ChevronDown size={12} /></button><button type="button" aria-label={`${block.name}を削除`} disabled={block.locked} onClick={() => setReportBlocks((current) => current.filter((item) => item.id !== block.id))}>{block.locked ? <ShieldCheck size={12} /> : <X size={12} />}</button></div></article>)}</div>
      <label><span>追加</span><select defaultValue="choose" onChange={(event) => { if (event.target.value === 'choose') return; const id = `${event.target.value}-${reportBlocks.length}`; const labels: Record<string,string> = { view: 'ビュー', graph: 'グラフ', table: '数値表', text: '本文', references: '参考資料' }; setReportBlocks((current) => [...current, { id, name: labels[event.target.value], detail: '参照先を選択', locked: false }]); event.target.value = 'choose' }}><option value="choose">ブロックを選択</option><option value="view">ビュー</option><option value="graph">グラフ</option><option value="table">数値表</option><option value="text">本文</option><option value="references">参考資料</option></select></label>
      <label><span>ビュー形式</span><select defaultValue="still"><option value="still">静止画</option><option value="interactive">インタラクティブ3D</option><option value="video">動画</option></select></label>
    </PropertyGroup>
  </div>

  if (tab.id === 'drafting') return <div className="property-editor">
    {/* XC-214: the measured flow is a prompt, then an outline the user refines, then generation on the
        user's word - and the vendor states the output must be human-reviewed (E-126). This product
        cannot leave that to a caption: a generated sentence may not invent a number, so nothing enters
        the report until each statement has been seen with its kind and its source (XC-104). */}
    <PropertyGroup title="書き方">
      <label><span>方式</span><select value={commentary} onChange={(event) => setCommentary(event.target.value as typeof commentary)}><option value="mechanical">機械的要約のみ</option><option value="generated">生成コメント</option></select></label>
      {commentary === 'mechanical' && <p className="property-editor-note"><ShieldCheck size={12} />読み取った値と単位を定型文で並べます。モデルは使わず、文面はケースが変わっても同じ形です。</p>}
    </PropertyGroup>
    {commentary === 'generated' && <>
      <PropertyGroup title="方針">
        <label><span>観点</span><textarea rows={3} placeholder="議論してほしい観点" /></label>
        <label><span>深さ</span><select defaultValue="standard"><option value="brief">簡潔</option><option value="standard">標準</option><option value="detailed">詳細</option></select></label>
        <label><span>モデル</span><input value="未設定" readOnly /></label>
        <label><span>検索の可否</span><select value={search} onChange={(event) => setSearch(event.target.value as typeof search)}><option value="off">検索しない</option><option value="ask">要求ごとに許可を確認</option></select></label>
        {search === 'ask' && <p className="property-editor-note"><ShieldCheck size={12} />送信する検索語と送信しない情報を要求ごとに表示し、許可されるまで送信しません。</p>}
      </PropertyGroup>
      {/* Restored with the tab: an unset model is why the draft cannot be made, and it gates the
          action rather than being a note beside a button that still looks available. */}
      <div className="property-unresolved"><AlertTriangle size={13} /><span><b>生成コメントは現在利用できません</b><small>モデルと送信範囲を設定し、費用を確認するまで外部通信しません。</small></span></div>
      <PropertyGroup title="下書き">
        <label><span>状態</span><input value={draftState === 'none' ? '未作成' : draftState === 'review' ? '確認待ち・4文＋除外2件' : '取り込み済み・4文'} readOnly /></label>
        <div className="drafting-actions">
          <button type="button" className="primary-button" disabled={draftState === 'review'} onClick={() => setDraftState('review')}><PenLine size={12} />下書きを作る</button>
          <button type="button" disabled={draftState === 'none'} onClick={() => setDraftState('none')}><X size={12} />破棄</button>
        </div>
        {draftState === 'review' && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>確認待ちです</b><small>中央の一覧で、各文の種別と出典、除外された記述を確認します。取り込むまでレポートは変わりません。</small></span></div>}
        {draftState === 'applied' && <p className="property-editor-note"><ShieldCheck size={12} />取り込んだ文は本文ブロックとして保存され、種別と出典を保持します。ケースが変わると再確認が必要になります。</p>}
      </PropertyGroup>
    </>}
  </div>

  return <div className="property-editor">
    <PropertyGroup title="形式">
      <label><span>出力</span><select value={reportOutput} onChange={(event) => setReportOutput(event.target.value as typeof reportOutput)}><option value="html">インタラクティブHTML</option><option value="pptx">PowerPoint</option><option value="docx">Word</option><option value="xlsx">Excel</option><option value="csv">CSV</option><option value="image">画像</option><option value="video">動画</option><option value="text">プレーンテキスト</option><option value="markdown">Markdown</option></select></label>
      <label><span>3D表現</span><input value={reportOutput === 'html' ? 'インタラクティブ' : '静止画へ置換・明記'} readOnly /></label>
      <label className="property-toggle"><span>オフライン完結</span><input type="checkbox" checked disabled readOnly /></label>
      <label className="property-toggle"><span>フォントを埋め込む</span><input type="checkbox" checked disabled readOnly /></label>
    </PropertyGroup>
    <PropertyGroup title="保存先">
      <label><span>パターン</span><input value="output/report/<run>/<case>/" readOnly /></label>
      <label><span>既存出力</span><input value="上書きしない" readOnly /></label>
      <label><span>事前検査</span><input value="未実行" readOnly /></label>
    </PropertyGroup>
    <div className="property-panel-action"><button type="button" className="primary-button" onClick={() => setPreflightOpen(true)}><ShieldCheck size={12} />出力前チェック</button></div>
    {outputStarted && <p className="property-editor-note" role="status"><CircleDashed size={12} />出力を開始しました。同じ対象への二重出力は停止されています。</p>}
    <OutputPreflightDialog open={preflightOpen} onOpenChange={setPreflightOpen} title="レポート" checks={[{ label: '必須情報', detail: '来歴・宣言単位・制限事項・製品版を収録', status: 'pass' }, { label: '文字', detail: '使用グリフと埋め込み字体を出力時に検査', status: 'pass' }, { label: '3D表現', detail: reportOutput === 'html' ? '自己完結インタラクティブ表現' : '静止画への置換を文書内に記載', status: reportOutput === 'html' ? 'pass' : 'warning' }, { label: '未解決内容', detail: '値を含まないレイアウト用ビューのみ。解析結果として主張しない', status: 'warning' }]} onStart={() => { setOutputStarted(true); setPreflightOpen(false) }} />
  </div>
}

function SimulationPropertyEditor() {
  return <div className="property-editor">
    <PropertyGroup title="シミュレーション定義">
      <label><span>名前</span><input defaultValue="新規シミュレーション" /></label>
      <label><span>状態</span><input value="ドラフト・実行不可" readOnly /></label>
      <label><span>ソルバー</span><select defaultValue="unresolved"><option value="unresolved">未接続</option></select></label>
      <label><span>入力</span><select defaultValue="unresolved"><option value="unresolved">未選択</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="実行条件">
      <label><span>条件</span><input value="未定義" readOnly /></label>
      <label><span>順序</span><input value="実行条件なし" readOnly /></label>
    </PropertyGroup>
    <div className="property-unresolved"><AlertTriangle size={13} /><span><b>外部ソルバーの実行はr1対象外です</b><small>定義はドラフトとして保持できますが、未接続のフローを成功として実行しません。</small></span></div>
  </div>
}

function NetworkPropertyEditor({ tab, variant }: { tab: SidebarTab; variant: string }) {
  const [permissionOpen, setPermissionOpen] = useState(variant === 'request-review')
  const [externalEnabled, setExternalEnabled] = useState(false)
  const [webSearchEnabled, setWebSearchEnabled] = useState(false)
  const [allowedHosts, setAllowedHosts] = useState<string[]>([])
  const [hostDraft, setHostDraft] = useState('')
  const rows = auditRowsFor(variant)
  if (tab.id === 'permissions') return <div className="property-editor">
    <PropertyGroup title="ワークスペース権限">
      <label className="property-toggle"><span>外部通信</span><input type="checkbox" checked={externalEnabled} onChange={() => externalEnabled ? setExternalEnabled(false) : setPermissionOpen(true)} /></label>
      <label className="property-toggle"><span>Web検索</span><input type="checkbox" checked={webSearchEnabled} onChange={(event) => setWebSearchEnabled(event.target.checked)} disabled={!externalEnabled} /></label>
      <label className="property-toggle"><span>生成コメント</span><input type="checkbox" disabled /></label>
      <label className="property-toggle"><span>詳細調査</span><input type="checkbox" disabled /></label>
    </PropertyGroup>
    <PropertyGroup title="許可ホスト">
      {/* XC-106: the allow-list is part of the per-workspace permission, so it is edited here. The
          panel used to echo `登録なし`, `送信前に表示` and `拒否` as read-only text that the centre
          summary already stated. */}
      <div className="allowed-host-list">
        {allowedHosts.map((host) => <span key={host}><b>{host}</b><button type="button" aria-label={`${host}を削除`} onClick={() => setAllowedHosts((current) => current.filter((item) => item !== host))}><X size={10} /></button></span>)}
        {allowedHosts.length === 0 && <small>登録なし。要求ごとの確認でも、宛先が未登録であれば送信しません。</small>}
      </div>
      <label><span>追加</span><input value={hostDraft} placeholder="例：docs.example.org" onChange={(event) => setHostDraft(event.target.value)} /></label>
      <div className="property-panel-action"><button type="button" disabled={!hostDraft.trim() || !externalEnabled} onClick={() => { setAllowedHosts((current) => [...current, hostDraft.trim()]); setHostDraft('') }}>ホストを許可一覧へ追加</button></div>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />許可されるまで通信を試行しません。ケース名、値、パスを含む送信は個別に確認します。</p>
    <Dialog open={permissionOpen} onOpenChange={setPermissionOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog outbound-review-dialog"><header><span><small>ワークスペース権限</small><b>外部通信を許可しますか？</b></span><button type="button" aria-label="権限確認を閉じる" onClick={() => setPermissionOpen(false)}><X size={15} /></button></header><section className="workflow-check-list"><p><ShieldCheck size={13} /><span><b>既定</b><small>要求ごとに正確な送信内容と宛先を確認</small></span></p><p><AlertTriangle size={13} /><span><b>機密情報</b><small>ケース名、値、ファイルパスは要求ごとの追加許可が必要</small></span></p><p><ScrollText size={13} /><span><b>監査</b><small>送信内容、ホスト、日時、判断をローカルに記録</small></span></p></section><footer><button type="button" onClick={() => setPermissionOpen(false)}>オフラインを維持</button><button type="button" className="primary-button" onClick={() => { setExternalEnabled(true); setPermissionOpen(false) }}>確認を必須にして許可</button></footer></DialogContent></Dialog>
  </div>

  return <div className="property-editor">
    <PropertyGroup title="通信記録">
      <label><span>期間</span><select defaultValue="workspace"><option value="workspace">このワークスペース</option><option value="session">このセッション</option></select></label>
      <label><span>保存先</span><input value="ローカル・書き出しは明示操作" readOnly /></label>
    </PropertyGroup>
    {/* The centre owns the list. This panel reports the same records it shows - it used to carry its
        own empty state and contradict the list next to it. */}
    <section className="property-audit-summary">
      <b>記録 {rows.length}件</b>
      <ul>{(Object.keys(auditResultLabels) as AuditResult[]).map((result) => <li key={result}><span>{auditResultLabels[result]}</span><em>{rows.filter((row) => row.result === result).length}件</em></li>)}</ul>
      <small>端末外へ送信した情報は{rows.filter((row) => row.result === 'allowed').length}件です。オフライン操作は通信として記録されません。</small>
    </section>
    <div className="property-panel-action"><button type="button"><FileOutput size={12} />監査ログを書き出す</button></div>
  </div>
}

function ViewObjectPropertyEditor({ activeObject }: { activeObject: ActiveViewObject }) {
  if (activeObject.kind === 'container') {
    return (
      <div className="property-editor">
        <section className="property-selection object-selection-card">
          <span><small>選択中の行</small><b>{activeObject.name}</b><em>データセットの入れ物</em></span>
        </section>
        <div className="sidebar-context-state"><Boxes size={22} /><b>Viewオブジェクトではありません</b><small>この行は元ファイルの入れ物です。表示設定を持つのはその下の構成要素で、選択するとここに専用の項目が表示されます。</small></div>
      </div>
    )
  }
  const meta = viewObjectKinds[activeObject.kind]
  return (
    <div className="property-editor">
      <section className="property-selection object-selection-card">
        <span><small>アクティブオブジェクト</small><b>{activeObject.name}</b><em>{meta.label}</em></span>
      </section>
      <ObjectTypeProperties key={activeObject.kind} kind={activeObject.kind} />
      <p className="property-editor-note"><ShieldCheck size={12} />オブジェクトの表示定義だけを編集します。元のデータセット、解析値、単位、来歴は変更しません。</p>
    </div>
  )
}

function ObjectTypeProperties({ kind }: { kind: ViewObjectKind }) {
  const [meshRepresentation, setMeshRepresentation] = useState<MeshRepresentation>('surface-edges')
  const showsMeshEdges = meshRepresentation === 'surface-edges' || meshRepresentation === 'wireframe'

  if (kind === 'analysis-mesh' || kind === 'reference-mesh') {
    return <>
      <details className="property-group" open><summary><ChevronRight size={12} /><b>メッシュ</b></summary><div className="property-fields">
        <label><span>役割</span><input value={kind === 'analysis-mesh' ? '解析' : '参照'} readOnly /></label>
        <label><span>参照元</span><input value={kind === 'analysis-mesh' ? 'データセット・未接続' : '参照形状・未接続'} readOnly /></label>
        <VisualOptions label="表示形式" kind="representation" columns={3} value={meshRepresentation} onChange={(value) => setMeshRepresentation(value as MeshRepresentation)}
          options={[{ value: 'surface', label: 'サーフェス' }, { value: 'surface-edges', label: 'サーフェス＋エッジ' }, { value: 'wireframe', label: 'ワイヤーフレーム' }]} />
      </div></details>
      <details className="property-group" open><summary><ChevronRight size={12} /><b>表示</b></summary><div className="property-fields">
        <label className="property-toggle"><span>表示する</span><input type="checkbox" defaultChecked /></label>
        <label><span>表示不透明度</span><div className="property-range"><input type="range" min="0" max="100" defaultValue="100" /><output>100%</output></div></label>
      </div></details>
      {showsMeshEdges && <details className="property-group" open><summary><ChevronRight size={12} /><b>エッジ</b></summary><div className="property-fields">
        <label><span>色</span><input type="color" defaultValue="#26343b" aria-label="オブジェクトのエッジ色" /></label>
        <label><span>幅</span><div className="property-range"><input type="range" min="0.5" max="5" step="0.5" defaultValue="1" /><output>1 px</output></div></label>
        <label><span>不透明度</span><div className="property-range"><input type="range" min="0" max="100" defaultValue="100" /><output>100%</output></div></label>
      </div></details>}
    </>
  }

  if (kind === 'scalar-field') {
    return <>
      <details className="property-group" open><summary><ChevronRight size={12} /><b>スカラー場</b></summary><div className="property-fields">
        <label><span>フィールド</span><select defaultValue="unresolved"><option value="unresolved">未接続</option></select></label>
        <label><span>位置</span><select defaultValue="source"><option value="source">ソースに従う</option></select></label>
        <label><span>成分</span><select defaultValue="magnitude"><option value="magnitude">大きさ</option></select></label>
        <label><span>単位</span><input value="未宣言" readOnly /></label>
      </div></details>
      <details className="property-group" open><summary><ChevronRight size={12} /><b>色と範囲</b></summary><div className="property-fields">
        <label><span>カラーマップ</span><select defaultValue="technical"><option value="technical">技術表示</option></select></label>
        <label><span>範囲</span><select defaultValue="unresolved"><option value="unresolved">データ未接続</option></select></label>
        <label className="property-toggle"><span>凡例</span><input type="checkbox" defaultChecked /></label>
      </div></details>
    </>
  }

  if (kind === 'vector-field') {
    return <>
      <details className="property-group" open><summary><ChevronRight size={12} /><b>ベクトル場</b></summary><div className="property-fields">
        <label><span>フィールド</span><select defaultValue="unresolved"><option value="unresolved">未接続</option></select></label>
        <label><span>座標系</span><select defaultValue="global"><option value="global">グローバル直交</option></select></label>
        <label><span>グリフ</span><select defaultValue="arrow"><option value="arrow">矢印</option><option value="line">線</option></select></label>
        <label><span>密度</span><div className="property-range"><input type="range" min="1" max="10" defaultValue="4" /><output>低</output></div></label>
        <label><span>スケール</span><select defaultValue="explicit"><option value="explicit">明示指定</option><option value="auto">自動</option></select></label>
      </div></details>
    </>
  }

  if (kind === 'trajectory') {
    return <>
      <details className="property-group" open><summary><ChevronRight size={12} /><b>流線・軌跡</b></summary><div className="property-fields">
        <label><span>ベクトル場</span><select defaultValue="unresolved"><option value="unresolved">未接続</option></select></label>
        <label><span>シード</span><select defaultValue="unresolved"><option value="unresolved">未定義</option></select></label>
        <label><span>積分器</span><select defaultValue="rk45"><option value="rk45">Runge–Kutta 4/5</option></select></label>
        <label><span>表現</span><select defaultValue="tube"><option value="tube">チューブ</option><option value="line">線</option></select></label>
      </div></details>
      <div className="property-unresolved"><AlertTriangle size={13} /><span><b>描画条件が未解決です</b><small>フィールドとシードを指定するまで形状を生成しません。</small></span></div>
    </>
  }

  if (kind === 'point-cloud') {
    return <details className="property-group" open><summary><ChevronRight size={12} /><b>点群</b></summary><div className="property-fields">
      <label><span>参照元</span><input value="点データ・未接続" readOnly /></label>
      <label><span>点サイズ</span><div className="property-range"><input type="range" min="1" max="10" defaultValue="3" /><output>3 px</output></div></label>
      <label><span>色</span><select defaultValue="uniform"><option value="uniform">一様色</option><option value="field">値による色</option></select></label>
      <label className="property-toggle"><span>表示する</span><input type="checkbox" defaultChecked /></label>
    </div></details>
  }

  if (kind === 'annotation') {
    return <details className="property-group" open><summary><ChevronRight size={12} /><b>注釈</b></summary><div className="property-fields">
      <label><span>種類</span><select defaultValue="text"><option value="text">テキスト</option><option value="dimension">寸法</option><option value="point">点ラベル</option></select></label>
      <label><span>アンカー</span><select defaultValue="unresolved"><option value="unresolved">未設定</option></select></label>
      <label><span>来歴</span><input value="ユーザー入力" readOnly /></label>
    </div></details>
  }

  return <>
    <details className="property-group" open><summary><ChevronRight size={12} /><b>エフェクト</b></summary><div className="property-fields">
      <label><span>種類</span><select defaultValue="highlight"><option value="highlight">強調表示</option><option value="glow">グロー</option><option value="particles">パーティクル</option></select></label>
      <label><span>対象</span><select defaultValue="unresolved"><option value="unresolved">未選択</option></select></label>
      <label><span>強さ</span><div className="property-range"><input type="range" min="0" max="100" defaultValue="40" /><output>40%</output></div></label>
      <label className="property-toggle"><span>表示する</span><input type="checkbox" defaultChecked /></label>
    </div></details>
    <div className="display-only-badge"><Sparkles size={12} />表示専用・解析値を生成しません</div>
  </>
}

type MaterialEditorMode = 'basic' | 'nodes' | 'source'
type BaseColorInputMode = 'solid' | 'texture' | 'colormap' | 'formula'
type ColorMapVariable = 'unresolved' | 'stress' | 'displacement' | 'temperature' | 'position-x' | 'position-y'
type TextureMappingMode = 'none' | 'authoredUv' | 'objectTriplanar' | 'generatedAtlas' | 'planar' | 'cylindrical' | 'spherical'

function MaterialNodeGraph({ expanded = false, resultBinding = false }: { expanded?: boolean; resultBinding?: boolean }) {
  return <div className={`material-node-graph ${expanded ? 'expanded' : ''} ${resultBinding ? 'result-driven' : 'surface-only'}`} role="img" aria-label={resultBinding ? 'MaterialXノードグラフ。解析結果をカラーマップへ接続し、OpenPBR Surfaceへ合成しています。' : 'MaterialXノードグラフ。画像をOpenPBR Surfaceへ接続しています。'}>
    <svg viewBox="0 0 720 330" aria-hidden="true">{resultBinding ? <><path d="M132 79 C190 79 165 142 222 142" /><path d="M132 234 C180 234 180 180 222 180" /><path d="M352 160 C405 160 400 125 452 125" /><path d="M352 160 C405 160 400 225 452 225" /><path d="M582 154 C630 154 625 165 678 165" /><path d="M582 225 C630 225 625 185 678 185" /></> : <><path d="M132 165 C245 165 330 145 452 145" /><path d="M582 165 C625 165 635 165 678 165" /></>}</svg>
    {resultBinding && <button type="button" className="material-node result"><b>解析結果</b><small>stress_value · float</small><i /></button>}
    <button type="button" className="material-node texture"><b>画像</b><small>steel_base.png</small><i /></button>
    {resultBinding && <button type="button" className="material-node ramp"><b>カラーマップ</b><small>color + opacity</small><i /><i /></button>}
    {resultBinding && <button type="button" className="material-node mix"><b>合成</b><small>multiply</small><i /><i /></button>}
    <button type="button" className="material-node surface"><b>OpenPBR Surface</b><small>surface</small><i /><i /></button>
    <button type="button" className="material-node output"><b>Material</b><small>surfacematerial</small><i /></button>
  </div>
}

function ViewMaterialPropertyEditor({ variant, activeObject }: { variant: string; activeObject: ActiveViewObject }) {
  const meta = activeObject.kind === 'container' ? null : viewObjectKinds[activeObject.kind]
  const showFailedBinding = variant === 'material-composition'
  const [materialSlots, setMaterialSlots] = useState([
    { id: 'stress-steel', name: 'スチール＋応力コンター', target: '全体', revision: null as number | null, resultBinding: true, baseColorMode: 'colormap' as BaseColorInputMode, mappingRequired: true, mappingMode: 'objectTriplanar' as TextureMappingMode, sourceFile: 'steel_stress.mtlx' },
    { id: 'brushed-steel', name: 'ブラッシュドスチール', target: '［選択した面セット］', revision: null as number | null, resultBinding: false, baseColorMode: 'texture' as BaseColorInputMode, mappingRequired: true, mappingMode: 'objectTriplanar' as TextureMappingMode, sourceFile: 'brushed_steel.mtlx' },
  ])
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(showFailedBinding ? 'stress-steel' : 'brushed-steel')
  const [editorMode, setEditorMode] = useState<MaterialEditorMode>('basic')
  const [nodeEditorOpen, setNodeEditorOpen] = useState(false)
  const [slotTargetOpen, setSlotTargetOpen] = useState(false)
  const [newSlotTarget, setNewSlotTarget] = useState<'object' | 'part' | 'elements'>('object')
  const [colorMapEditorOpen, setColorMapEditorOpen] = useState(false)
  const [colorMapVariable, setColorMapVariable] = useState<ColorMapVariable>('unresolved')
  const [colorMapRange, setColorMapRange] = useState({ minimum: 0, maximum: 1 })
  const [colorStops, setColorStops] = useState([
    { position: 0, color: '#173a78' },
    { position: 0.35, color: '#16a6b6' },
    { position: 0.65, color: '#f0d642' },
    { position: 1, color: '#c83d4b' },
  ])
  const [opacityStops, setOpacityStops] = useState([
    { position: 0, opacity: 0 },
    { position: 0.12, opacity: 1 },
    { position: 0.88, opacity: 1 },
    { position: 1, opacity: 0 },
  ])
  const [selectedColorStop, setSelectedColorStop] = useState(1)
  const [selectedOpacityStop, setSelectedOpacityStop] = useState(1)
  const [draftSlotIds, setDraftSlotIds] = useState<string[]>([])
  const [invalidSourceSlotIds, setInvalidSourceSlotIds] = useState<string[]>([])
  const activeSlot = materialSlots.find((slot) => slot.id === selectedSlotId) ?? null
  const activeFailed = activeSlot?.id === 'stress-steel' && showFailedBinding
  const activeResultBinding = activeSlot?.resultBinding ?? false
  const activeBaseColorMode = activeSlot?.baseColorMode ?? 'solid'
  const activeMappingRequired = activeSlot?.mappingRequired ?? false
  const activeMappingMode = activeSlot?.mappingMode ?? 'none'
  const activeHasDraft = activeSlot ? draftSlotIds.includes(activeSlot.id) : false
  const activeSourceValid = activeSlot ? !invalidSourceSlotIds.includes(activeSlot.id) : true
  const colorMapRangeValid = colorMapRange.minimum < colorMapRange.maximum
  const activeMappingValid = !activeMappingRequired || activeMappingMode !== 'none'
  const activeMaterialValid = activeSourceValid && activeMappingValid && (activeBaseColorMode !== 'colormap' || colorMapRangeValid)
  const sourceStatus = activeSourceValid
    ? activeHasDraft ? '自動検証済み：構文・型・単位次元' : '読み込み時の検証済み：構文・型・単位次元'
    : 'XML構造エラー：materialxルートを閉じてください'
  const materialSource = activeResultBinding ? `<materialx version="1.39" colorspace="lin_rec709_scene">
  <geompropvalue name="stress_value" type="float">
    <input name="geomprop" type="string" value="solvia:result/stress" />
  </geompropvalue>
  <ramplr name="stress_color" type="color3">
    <input name="valuel" type="color3" value="0.09, 0.23, 0.47" />
    <input name="valuer" type="color3" value="0.78, 0.24, 0.29" />
    <input name="texcoord" type="float" nodename="stress_value" />
  </ramplr>
  <open_pbr_surface name="steel_surface" type="surfaceshader">
    <input name="base_color" type="color3"
           nodename="stress_color" />
    <input name="metalness" type="float" value="0.92" />
    <input name="specular_roughness" type="float" value="0.28" />
    <input name="geometry_opacity" type="float" value="1.0" />
  </open_pbr_surface>
  <surfacematerial name="steel_material" type="material"
      solvia_asset_id="[未接続]" solvia_asset_revision="[未接続]"
      solvia_contract="CT-011" solvia_contract_version="1.0.0"
      solvia_manifest_uri="solvia:asset/[未接続]?revision=[未接続]">
    <input name="surfaceshader" type="surfaceshader" nodename="steel_surface" />
  </surfacematerial>
</materialx>` : `<materialx version="1.39" colorspace="lin_rec709_scene">
  <image name="steel_base" type="color3">
    <input name="file" type="filename" value="steel_base.png" />
  </image>
  <open_pbr_surface name="steel_surface" type="surfaceshader">
    <input name="base_color" type="color3" nodename="steel_base" />
    <input name="metalness" type="float" value="0.92" />
    <input name="specular_roughness" type="float" value="0.28" />
    <input name="geometry_opacity" type="float" value="1.0" />
  </open_pbr_surface>
  <surfacematerial name="steel_material" type="material"
      solvia_asset_id="[アセットID]" solvia_asset_revision="[リビジョン]"
      solvia_contract="CT-011" solvia_contract_version="1.0.0"
      solvia_manifest_uri="solvia:asset/[アセットID]?revision=[リビジョン]">
    <input name="surfaceshader" type="surfaceshader" nodename="steel_surface" />
  </surfacematerial>
</materialx>`
  const colorMapGradient = `linear-gradient(90deg, ${colorStops.map((stop) => `${stop.color} ${stop.position * 100}%`).join(', ')})`
  const selectedColorPoint = colorStops[selectedColorStop]
  const selectedOpacityPoint = opacityStops[selectedOpacityStop]
  const colorMapDisplayUnit = colorMapVariable === 'unresolved' ? '未解決' : '単位未宣言'

  const markMaterialDraft = () => {
    if (!activeSlot) return
    setDraftSlotIds((current) => current.includes(activeSlot.id) ? current : [...current, activeSlot.id])
  }

  const updateSourceDraft = (source: string) => {
    if (!activeSlot) return
    markMaterialDraft()
    const structurallyValid = source.includes('<materialx') && source.includes('</materialx>')
    setInvalidSourceSlotIds((current) => structurallyValid
      ? current.filter((id) => id !== activeSlot.id)
      : current.includes(activeSlot.id) ? current : [...current, activeSlot.id])
  }

  const saveMaterialRevision = () => {
    if (!activeSlot || !activeHasDraft || !activeMaterialValid) return
    setMaterialSlots((current) => current.map((slot) => slot.id === activeSlot.id ? { ...slot, revision: (slot.revision ?? 0) + 1 } : slot))
    setDraftSlotIds((current) => current.filter((id) => id !== activeSlot.id))
  }

  const updateBaseColorMode = (mode: BaseColorInputMode) => {
    if (!activeSlot) return
    setMaterialSlots((current) => current.map((slot) => slot.id === activeSlot.id
      ? { ...slot, baseColorMode: mode, mappingRequired: mode === 'texture' ? true : slot.mappingRequired }
      : slot))
    markMaterialDraft()
  }

  const updateMappingMode = (mode: TextureMappingMode) => {
    if (!activeSlot) return
    setMaterialSlots((current) => current.map((slot) => slot.id === activeSlot.id ? { ...slot, mappingMode: mode } : slot))
    markMaterialDraft()
  }

  const updateColorMapRange = (boundary: 'minimum' | 'maximum', value: number) => {
    setColorMapRange((current) => ({ ...current, [boundary]: value }))
    markMaterialDraft()
  }

  const updateColorStop = (patch: Partial<{ position: number; color: string }>) => {
    setColorStops((current) => current.map((stop, index) => index === selectedColorStop ? { ...stop, ...patch } : stop))
  }

  const updateOpacityStop = (patch: Partial<{ position: number; opacity: number }>) => {
    setOpacityStops((current) => current.map((stop, index) => index === selectedOpacityStop ? { ...stop, ...patch } : stop))
  }

  const addColorStop = () => {
    const leftIndex = selectedColorStop === colorStops.length - 1 ? selectedColorStop - 1 : selectedColorStop
    const position = (colorStops[leftIndex].position + colorStops[leftIndex + 1].position) / 2
    const insertAt = leftIndex + 1
    setColorStops((current) => [...current.slice(0, insertAt), { position, color: colorStops[leftIndex].color }, ...current.slice(insertAt)])
    setSelectedColorStop(insertAt)
  }

  const removeColorStop = () => {
    if (selectedColorStop === 0 || selectedColorStop === colorStops.length - 1) return
    setColorStops((current) => current.filter((_, index) => index !== selectedColorStop))
    setSelectedColorStop((current) => Math.max(0, current - 1))
  }

  const addOpacityStop = () => {
    const leftIndex = selectedOpacityStop === opacityStops.length - 1 ? selectedOpacityStop - 1 : selectedOpacityStop
    const position = (opacityStops[leftIndex].position + opacityStops[leftIndex + 1].position) / 2
    const insertAt = leftIndex + 1
    setOpacityStops((current) => [...current.slice(0, insertAt), { position, opacity: opacityStops[leftIndex].opacity }, ...current.slice(insertAt)])
    setSelectedOpacityStop(insertAt)
  }

  const removeOpacityStop = () => {
    if (selectedOpacityStop === 0 || selectedOpacityStop === opacityStops.length - 1) return
    setOpacityStops((current) => current.filter((_, index) => index !== selectedOpacityStop))
    setSelectedOpacityStop((current) => Math.max(0, current - 1))
  }

  const addMaterialSlot = () => {
    setSlotTargetOpen(true)
  }

  const confirmAddMaterialSlot = () => {
    const number = materialSlots.length + 1
    const target = newSlotTarget === 'object' ? '全体' : newSlotTarget === 'part' ? '部品・選択待ち' : '要素セット・選択待ち'
    const slot = { id: `material-${Date.now()}`, name: `新規マテリアル ${number}`, target, revision: null as number | null, resultBinding: false, baseColorMode: 'solid' as BaseColorInputMode, mappingRequired: false, mappingMode: 'none' as TextureMappingMode, sourceFile: `material_${number}.mtlx` }
    setMaterialSlots((current) => [...current, slot])
    setSelectedSlotId(slot.id)
    setSlotTargetOpen(false)
  }

  const removeMaterialSlot = () => {
    if (!selectedSlotId) return
    const index = materialSlots.findIndex((slot) => slot.id === selectedSlotId)
    const next = materialSlots.filter((slot) => slot.id !== selectedSlotId)
    setMaterialSlots(next)
    setSelectedSlotId(next[Math.min(index, next.length - 1)]?.id ?? null)
  }

  const moveMaterialSlot = (direction: -1 | 1) => {
    if (!selectedSlotId) return
    const index = materialSlots.findIndex((slot) => slot.id === selectedSlotId)
    const target = index + direction
    if (index < 0 || target < 0 || target >= materialSlots.length) return
    const next = [...materialSlots]
    ;[next[index], next[target]] = [next[target], next[index]]
    setMaterialSlots(next)
  }

  if (!meta || !meta.materialSurface) {
    return <div className="property-editor material-preview-first"><div className="property-editor-scroll-content"><MaterialPreview available={false} /><div className="sidebar-context-state"><MaterialSphereIcon size={22} /><b>マテリアル設定はありません</b><small>{meta ? `${meta.label}は専用の表示設定を使用します。` : 'この行は元ファイルの入れ物です。マテリアルを持つ構成要素を選択してください。'}</small></div></div></div>
  }

  return (
    <div className="property-editor material-preview-first">
      <div className="property-editor-scroll-content">
        <div className="material-slot-manager">
          <div className="material-slot-list material-slot-list-primary" role="listbox" aria-label="マテリアルスロット">
            {materialSlots.map((slot) => <button type="button" role="option" aria-selected={selectedSlotId === slot.id} aria-label={`${slot.name}${draftSlotIds.includes(slot.id) ? '・未保存の変更あり' : ''}`} className={`material-slot-row ${selectedSlotId === slot.id ? 'selected' : ''} ${slot.id === 'stress-steel' && showFailedBinding ? 'failed' : ''} ${draftSlotIds.includes(slot.id) ? 'dirty' : ''}`} onClick={() => setSelectedSlotId(slot.id)} key={slot.id}>{slot.name}</button>)}
            {materialSlots.length === 0 && <span className="material-slot-empty">マテリアルなし</span>}
          </div>
          <div className="material-slot-controls" aria-label="マテリアルスロット操作">
            <button type="button" data-tooltip="空のマテリアルスロットを追加" aria-label="空のマテリアルスロットを追加" onClick={addMaterialSlot}><Plus size={13} /></button>
            <button type="button" data-tooltip="選択中のスロットを削除" aria-label="選択中のマテリアルスロットを削除" disabled={!activeSlot} onClick={removeMaterialSlot}><X size={13} /></button>
            <span />
            <button type="button" data-tooltip="上へ移動" aria-label="マテリアルスロットを上へ移動" disabled={!activeSlot || materialSlots[0]?.id === selectedSlotId} onClick={() => moveMaterialSlot(-1)}><ChevronUp size={13} /></button>
            <button type="button" data-tooltip="下へ移動" aria-label="マテリアルスロットを下へ移動" disabled={!activeSlot || materialSlots.at(-1)?.id === selectedSlotId} onClick={() => moveMaterialSlot(1)}><ChevronDown size={13} /></button>
          </div>
        </div>
        <MaterialPreview available={Boolean(activeSlot)} failed={activeFailed} bindingLabel={activeResultBinding && !activeFailed ? '応力コンター・実データ' : undefined} empty={!activeSlot} resultOutput={activeResultBinding} />
        {activeSlot ? <>
          <div className="material-editor-tabs" role="tablist" aria-label="マテリアル編集方法">
            {([['basic', '基本'], ['nodes', 'ノード'], ['source', 'ソース']] as const).map(([id, label]) => <button type="button" role="tab" aria-selected={editorMode === id} onClick={() => setEditorMode(id)} key={id}>{label}</button>)}
          </div>
          {editorMode === 'basic' && <section className="material-basic-editor" role="tabpanel" aria-label="基本編集" onChange={markMaterialDraft}>
            <div className="material-model-row"><Workflow size={13} /><span><b>OpenPBR Surface</b><small>MaterialX・公開入力</small></span></div>
            <details className="material-parameter-group" open><summary><ChevronRight size={11} /><b>サーフェス</b></summary><div className="property-fields">
              <label><span>Base Color</span><select value={activeBaseColorMode} onChange={(event) => updateBaseColorMode(event.target.value as BaseColorInputMode)}><option value="solid">単色</option><option value="texture">画像</option><option value="colormap">カラーマップ</option><option value="formula">数式</option></select></label>
              {activeBaseColorMode === 'solid' && <>
                <label><span>入力</span><select defaultValue="fixed"><option value="fixed">固定色</option><option value="color-variable">カラー変数</option></select></label>
                <label><span>カラー</span><input type="color" defaultValue="#78858b" aria-label="Base Colorの単色" /></label>
              </>}
              {activeBaseColorMode === 'texture' && <>
                <label><span>画像</span><input value="steel_base.png" readOnly /></label>
              </>}
              {activeBaseColorMode === 'colormap' && <>
                <label><span>入力</span><select value={activeFailed ? 'unresolved' : colorMapVariable} onChange={(event) => { setColorMapVariable(event.target.value as ColorMapVariable); markMaterialDraft() }}><option value="unresolved">未接続</option><option value="stress">応力 / von Mises</option><option value="displacement">変位 / magnitude</option><option value="temperature">温度</option><option value="position-x">位置 / X</option><option value="position-y">位置 / Y</option></select></label>
                <div className="color-map-compact" aria-label="カラーマップ範囲。範囲外は透過">
                  <input type="number" value={colorMapRange.minimum} aria-label="カラーマップ最小値" aria-invalid={!colorMapRangeValid} onChange={(event) => updateColorMapRange('minimum', Number(event.target.value))} />
                  <button type="button" className="color-map-compact-ramp" aria-label="カラーマップを編集" onClick={() => setColorMapEditorOpen(true)}><span style={{ background: colorMapGradient }} /></button>
                  <input type="number" value={colorMapRange.maximum} aria-label="カラーマップ最大値" aria-invalid={!colorMapRangeValid} onChange={(event) => updateColorMapRange('maximum', Number(event.target.value))} />
                </div>
              </>}
              {activeBaseColorMode === 'formula' && <>
                <label><span>変数</span><select defaultValue="stress"><option value="stress">stress_value</option><option value="position">position</option><option value="temperature">temperature</option></select></label>
                <label><span>数式</span><input className="material-expression-input" defaultValue="color3(clamp(stress_value / limit, 0, 1))" /></label>
              </>}
              <label><span>Metalness</span><div className="property-range"><input type="range" min="0" max="100" defaultValue="92" /><output>0.92</output></div></label>
              <label><span>Roughness</span><div className="property-range"><input type="range" min="0" max="100" defaultValue="28" /><output>0.28</output></div></label>
              <label><span>Opacity</span><div className="property-range"><input type="range" min="0" max="100" defaultValue="100" aria-label="MaterialX geometry_opacity" /><output>1.00</output></div></label>
              <label><span>Normal</span><select defaultValue={activeMappingRequired ? 'texture' : 'none'}><option value="texture">steel_normal.png</option><option value="none">未接続</option></select></label>
            </div></details>
            {activeMappingRequired && <details className="material-parameter-group"><summary><ChevronRight size={11} /><b>マッピング</b></summary><div className="property-fields">
              <label><span>方式</span><select value={activeMappingMode} aria-invalid={!activeMappingValid} onChange={(event) => updateMappingMode(event.target.value as TextureMappingMode)}><option value="none" disabled>方式を選択</option><option value="authoredUv">UV</option><option value="generatedAtlas">生成UV</option><option value="objectTriplanar">オブジェクト空間・トライプラナー</option><option value="planar">平面投影</option><option value="cylindrical">円柱投影</option><option value="spherical">球面投影</option></select></label>
              {activeMappingMode === 'authoredUv' && <label><span>UVセット</span><select defaultValue="st"><option value="st">st</option><option value="uv1">uv1</option></select></label>}
              {activeMappingMode === 'planar' && <label><span>投影面</span><select defaultValue="xy"><option value="xy">XY</option><option value="xz">XZ</option><option value="yz">YZ</option></select></label>}
              <label><span>スケール</span><div className="property-range"><input type="range" min="1" max="200" defaultValue="100" /><output>1.00 m</output></div></label>
              <label><span>回転</span><div className="property-range"><input type="range" min="-180" max="180" defaultValue="0" /><output>0°</output></div></label>
              <label><span>状態</span><input value={activeMappingMode === 'authoredUv' ? '利用可能・UV: st' : activeMappingMode === 'generatedAtlas' ? '生成待ち' : activeMappingMode === 'none' ? '未設定・方式を選択してください' : '利用可能・UV不要'} readOnly /></label>
            </div></details>}
            {activeFailed && <p className="colour-authority-note failed" role="alert"><AlertTriangle size={12} /><span><b>解析カラーを評価できません</b><small>stress_value が未接続です。解析カラー出力と外観プレビューは診断マゼンタになります。</small></span></p>}
            <p className="material-editor-mode-note">基本編集は公開された入力だけを変更します。表示できないノードは保持されます。</p>
          </section>}
          {editorMode === 'nodes' && <section className="material-nodes-editor" role="tabpanel" aria-label="ノード編集">
            <MaterialNodeGraph resultBinding={activeResultBinding} />
            <button type="button" className="material-open-node-editor" onClick={() => setNodeEditorOpen(true)}>中央でノードを編集 <ArrowUpRight size={11} /></button>
            <p className="material-editor-mode-note">型が一致するソケットだけを接続できます。</p>
          </section>}
          {editorMode === 'source' && <section className="material-source-editor" role="tabpanel" aria-label="ソース編集">
            <div className="material-source-toolbar"><span><FileText size={11} />{activeSlot.sourceFile}</span><em className={activeSourceValid ? '' : 'invalid'}>{activeSourceValid ? <ShieldCheck size={10} /> : <AlertTriangle size={10} />}自動検証</em></div>
            <textarea key={activeSlot.id} aria-label="MaterialXソース" spellCheck={false} onChange={(event) => updateSourceDraft(event.target.value)} defaultValue={materialSource} />
            <p className={`material-source-status ${activeSourceValid ? '' : 'invalid'}`} aria-live="polite">{activeSourceValid ? <ShieldCheck size={11} /> : <AlertTriangle size={11} />}{sourceStatus}</p>
            <p className="material-editor-mode-note">編集後に自動検証し、保存時に再検証します。外部コードは実行しません。</p>
          </section>}
          <div className="material-save-bar"><span><small>{activeHasDraft ? activeMaterialValid ? '未保存の変更' : '保存できません' : activeSlot.revision === null ? 'リビジョン未接続' : `Revision ${activeSlot.revision}`}</small><b>{activeSlot.sourceFile}</b></span><button type="button" disabled={!activeHasDraft || !activeMaterialValid} onClick={saveMaterialRevision}><Save size={11} />新しいリビジョンを保存</button></div>
        </> : <p className="material-editor-mode-note empty">＋でマテリアルを追加すると編集できます。</p>}
      </div>
      {slotTargetOpen && <Dialog open onOpenChange={setSlotTargetOpen}><DialogOverlay className="material-node-dialog-backdrop" /><DialogContent className="workflow-dialog material-target-dialog"><header><span><small>マテリアルスロット</small><b>割り当て先を選択</b></span><button type="button" aria-label="スロット追加を閉じる" onClick={() => setSlotTargetOpen(false)}><X size={15} /></button></header><div className="material-target-options" role="radiogroup" aria-label="新しいマテリアルの割り当て先">{([['object','オブジェクト全体'],['part','部品'],['elements','要素セット']] as const).map(([id,text]) => <label key={id}><input type="radio" name="new-slot-target" checked={newSlotTarget === id} onChange={() => setNewSlotTarget(id)} /><span>{text}</span></label>)}</div>{newSlotTarget !== 'object' && <p className="workflow-selection-mode"><Shapes size={13} /><span><b>対象選択モード</b><small>追加後、ビューポートまたはアウトライナーで対象を選択します。アクティブオブジェクトは変わりません。</small></span></p>}<footer><button type="button" onClick={() => setSlotTargetOpen(false)}>キャンセル</button><button type="button" className="primary-button" onClick={confirmAddMaterialSlot}>{newSlotTarget === 'object' ? 'スロットを追加' : '追加して対象を選択'}</button></footer></DialogContent></Dialog>}
      {colorMapEditorOpen && <Dialog open onOpenChange={setColorMapEditorOpen}>
        <DialogOverlay className="material-node-dialog-backdrop" />
        <DialogContent className="material-colormap-dialog">
          <header><span><small>Base Color</small><b>カラーマップを編集</b></span><button type="button" aria-label="カラーマップエディターを閉じる" onClick={() => setColorMapEditorOpen(false)}><X size={15} /></button></header>
          <div className="material-colormap-dialog-toolbar">
            <label><span>入力</span><select value={colorMapVariable} onChange={(event) => setColorMapVariable(event.target.value as ColorMapVariable)}><option value="stress">応力 / von Mises</option><option value="displacement">変位 / magnitude</option><option value="temperature">温度</option><option value="position-x">位置 / X</option><option value="position-y">位置 / Y</option></select></label>
            <label><span>プリセット</span><select defaultValue="technical"><option value="technical">Technical</option><option value="viridis">Viridis</option><option value="grayscale">Grayscale</option></select></label>
            <label><span>補間</span><select defaultValue="linear"><option value="linear">Linear RGB</option><option value="diverging">Diverging</option><option value="constant">Constant</option></select></label>
            <span className="material-colormap-outside">範囲外 α 0</span>
          </div>
          <div className="material-colormap-workspace">
            <section className="transfer-function-section opacity-transfer-section">
              <div className="transfer-function-heading"><b>不透明度</b><span>上：不透明　下：透明</span><div><button type="button" aria-label="不透明度制御点を追加" onClick={addOpacityStop}><Plus size={12} /></button><button type="button" aria-label="不透明度制御点を削除" disabled={selectedOpacityStop === 0 || selectedOpacityStop === opacityStops.length - 1} onClick={removeOpacityStop}><X size={12} /></button></div></div>
              <div className="opacity-transfer-editor" role="group" aria-label="不透明度制御点">
                <svg viewBox="0 0 480 70" preserveAspectRatio="none" aria-hidden="true"><polyline points={opacityStops.map((stop) => `${stop.position * 480},${68 - stop.opacity * 64}`).join(' ')} /></svg>
                {opacityStops.map((stop, index) => <button type="button" className={selectedOpacityStop === index ? 'selected' : ''} style={{ left: `${stop.position * 100}%`, bottom: `${stop.opacity * 100}%` }} aria-label={`不透明度制御点 ${index + 1}`} onClick={() => setSelectedOpacityStop(index)} key={`${stop.position}-${index}`} />)}
              </div>
              <div className="transfer-point-fields">
                <label><span>位置</span><input type="number" min={opacityStops[Math.max(0, selectedOpacityStop - 1)].position + 0.01} max={opacityStops[Math.min(opacityStops.length - 1, selectedOpacityStop + 1)].position - 0.01} step="0.01" value={selectedOpacityPoint.position} disabled={selectedOpacityStop === 0 || selectedOpacityStop === opacityStops.length - 1} onChange={(event) => updateOpacityStop({ position: Number(event.target.value) })} /></label>
                <label><span>不透明度</span><input type="range" min="0" max="1" step="0.01" value={selectedOpacityPoint.opacity} onChange={(event) => updateOpacityStop({ opacity: Number(event.target.value) })} /><output>{selectedOpacityPoint.opacity.toFixed(2)}</output></label>
              </div>
            </section>
            <section className="transfer-function-section color-transfer-section">
              <div className="transfer-function-heading"><b>カラー</b><span>{colorMapRange.minimum} – {colorMapRange.maximum} {colorMapDisplayUnit}</span><div><button type="button" aria-label="カラー制御点を追加" onClick={addColorStop}><Plus size={12} /></button><button type="button" aria-label="カラー制御点を削除" disabled={selectedColorStop === 0 || selectedColorStop === colorStops.length - 1} onClick={removeColorStop}><X size={12} /></button></div></div>
              <div className="color-transfer-editor" role="group" aria-label="カラー制御点">
                <span className="color-transfer-ramp" style={{ background: colorMapGradient }} />
                {colorStops.map((stop, index) => <button type="button" className={selectedColorStop === index ? 'selected' : ''} style={{ left: `${stop.position * 100}%`, background: stop.color }} aria-label={`カラー制御点 ${index + 1}`} onClick={() => setSelectedColorStop(index)} key={`${stop.position}-${index}`} />)}
              </div>
              <div className="transfer-point-fields">
                <label><span>位置</span><input type="number" min={colorStops[Math.max(0, selectedColorStop - 1)].position + 0.01} max={colorStops[Math.min(colorStops.length - 1, selectedColorStop + 1)].position - 0.01} step="0.01" value={selectedColorPoint.position} disabled={selectedColorStop === 0 || selectedColorStop === colorStops.length - 1} onChange={(event) => updateColorStop({ position: Number(event.target.value) })} /></label>
                <label><span>カラー</span><input type="color" value={selectedColorPoint.color} onChange={(event) => updateColorStop({ color: event.target.value })} /></label>
              </div>
            </section>
          </div>
          <footer><span className={colorMapRangeValid ? '' : 'invalid'}>{colorMapRangeValid ? <ShieldCheck size={11} /> : <AlertTriangle size={11} />}{colorMapRangeValid ? '範囲外の値は透明として評価' : '最小値は最大値より小さくしてください'}</span><button type="button" className="primary-button" disabled={!colorMapRangeValid} onClick={() => { markMaterialDraft(); setColorMapEditorOpen(false) }}>適用</button></footer>
        </DialogContent>
      </Dialog>}
      {nodeEditorOpen && <Dialog open onOpenChange={setNodeEditorOpen}>
        <DialogOverlay className="material-node-dialog-backdrop" />
        <DialogContent className="material-node-dialog">
          <header><span><small>MaterialX ノード</small><b>{activeSlot?.name}</b></span><button type="button" aria-label="ノードエディターを閉じる" onClick={() => setNodeEditorOpen(false)}><X size={15} /></button></header>
          <div className="material-node-dialog-toolbar"><button type="button"><Plus size={12} />ノードを追加</button><button type="button">選択へ移動</button><span>{activeSlot?.sourceFile}</span></div>
          <div className="material-node-dialog-workspace"><MaterialNodeGraph expanded resultBinding={activeResultBinding} /><aside><small>選択ノード</small><b>OpenPBR Surface</b><label><span>Metalness</span><input value="0.92" readOnly /></label><label><span>Roughness</span><input value="0.28" readOnly /></label></aside></div>
          <footer><span><ShieldCheck size={11} />型付きMaterialXグラフ</span><button type="button" className="primary-button" onClick={() => setNodeEditorOpen(false)}>完了</button></footer>
        </DialogContent>
      </Dialog>}
    </div>
  )
}

function ViewTextPropertyEditor({ activeObject }: { activeObject: ActiveViewObject }) {
  if (activeObject.kind === 'container' || !viewObjectKinds[activeObject.kind].textProperties) return null

  return <div className="property-editor">
    <details className="property-group" open><summary><ChevronRight size={12} /><b>内容</b></summary><div className="property-fields">
      <label><span>テキスト</span><textarea defaultValue="注釈テキスト（仮）" rows={3} /></label>
    </div></details>
    <details className="property-group" open><summary><ChevronRight size={12} /><b>文字表現</b></summary><div className="property-fields">
      <label><span>書体</span><select defaultValue="workspace"><option value="workspace">ワークスペース設定</option></select></label>
      <label><span>サイズ</span><select defaultValue="annotation"><option value="annotation">注釈の既定値</option></select></label>
      <label className="property-toggle"><span>背景を表示</span><input type="checkbox" defaultChecked /></label>
    </div></details>
    <p className="property-editor-note"><ShieldCheck size={12} />アクティブなテキスト・注釈オブジェクトだけを編集します。</p>
  </div>
}

function AutomationPropertyEditor({ tab, variant, units, onUnitsChange, selectedUnitId, onSelectUnit }: { tab: SidebarTab; variant: string; units: PipelineUnitModel[]; onUnitsChange: (units: PipelineUnitModel[]) => void; selectedUnitId: string | null; onSelectUnit: (id: string) => void }) {
  const [addedUnit, setAddedUnit] = useState<string | null>(null)
  const flattened = flattenPipelineUnits(units)
  const selectedUnit = flattened.find((unit) => unit.id === selectedUnitId) ?? null
  const selectedUnitItem = selectedUnit && (selectedUnit.kind === 'view' || selectedUnit.kind === 'graph' || selectedUnit.kind === 'report')
    ? workItemHeaderByScreen[selectedUnit.kind as ScreenId]?.items.find((item) => item.name === selectedUnit.itemName) ?? null
    : null

  if (tab.id === 'unit') {
    const addUnit = (kind: PipelineUnitKind) => {
      const meta = pipelineUnitCatalogue[kind]
      const unit: PipelineUnitModel = { id: `unit-${kind}-${units.length + 1}`, kind, title: `${meta.label}ユニット`, detail: meta.detail, addsCases: kind === 'case' ? 0 : undefined, children: meta.zone ? [] : undefined }
      onUnitsChange([...units, unit])
      onSelectUnit(unit.id)
      setAddedUnit(meta.label)
    }
    return (
      <div className="automation-property-editor">
        <p>中央の挿入位置へドラッグするか、選択して追加します。</p>
        <div className="automation-unit-palette">
          {(Object.keys(pipelineUnitCatalogue) as PipelineUnitKind[]).map((kind) => {
            const meta = pipelineUnitCatalogue[kind]
            const Icon = meta.icon
            return <button type="button" onClick={() => addUnit(kind)} key={kind}><span><Icon size={14} /></span><b>{meta.label}</b><small>{meta.detail}</small>{addedUnit === meta.label ? <CheckCircle2 size={12} /> : <Plus size={12} />}</button>
          })}
        </div>
        {addedUnit && <p className="property-editor-note" role="status"><CheckCircle2 size={12} />{addedUnit}ユニットをパイプラインの末尾に追加しました。ワークスペース変更としてUndoできます。</p>}
      </div>
    )
  }

  if (tab.id === 'history') {
    if (variant !== 'failed') {
      return (
        <div className="automation-property-editor">
          <section className="automation-history-empty"><Clock3 size={22} /><b>実行履歴はありません</b><small>ドライランはファイルを書き込まず、対象と生成物を確認します。</small></section>
        </div>
      )
    }
    return (
      <div className="automation-property-editor">
        <section className="property-selection"><span><small>直近の実行</small><b>1ケース失敗・2ケース完了</b></span></section>
        <RunOutcomeTable units={flattened} failedCase="板厚変更" />
        <p className="property-editor-note"><ShieldCheck size={12} />失敗したケースの成果物は書き出していません。書込済みの成果物は実行記録から削除できます。</p>
      </div>
    )
  }

  if (!selectedUnit) {
    return (
      <div className="automation-property-editor">
        <section className="sidebar-context-state"><Workflow size={22} /><b>ユニットが選択されていません</b><small>中央のパイプラインでユニットを選ぶと、その条件をここで編集します。</small></section>
      </div>
    )
  }

  const meta = pipelineUnitCatalogue[selectedUnit.kind]
  const update = (patch: Partial<PipelineUnitModel>) => onUnitsChange(units.map((unit) => unit.id === selectedUnit.id
    ? { ...unit, ...patch }
    : { ...unit, children: unit.children?.map((child) => child.id === selectedUnit.id ? { ...child, ...patch } : child) }))

  return (
    <div className="automation-property-editor">
      <section className="property-selection"><span><small>選択中のユニット</small><b>{selectedUnit.title}</b><em>{meta.label}</em></span></section>
      <details className="property-group" open>
        <summary><ChevronRight size={12} /><b>定義</b></summary>
        <div className="property-fields">
          <label><span>名前</span><input value={selectedUnit.title} onChange={(event) => update({ title: event.target.value })} /></label>
          <label><span>種類</span><input value={meta.label} readOnly /></label>
          {selectedUnit.kind === 'case' && <label><span>追加ケース数</span><input type="number" min={0} max={9} value={selectedUnit.addsCases ?? 0} onChange={(event) => update({ addsCases: Number(event.target.value) })} /></label>}
          {/* XC-211: a unit that produces a @View has to name which one, or the pipeline cannot say what
              it makes. A comparison is one of the choices, which is how a run produces the same
              side-by-side figure for every @Case (XC-202). */}
          {(selectedUnit.kind === 'view' || selectedUnit.kind === 'graph' || selectedUnit.kind === 'report') && <>
            <label><span>参照元</span><select value={selectedUnit.source ?? 'workspace'} onChange={(event) => update({ source: event.target.value as PipelineUnitModel['source'] })}><option value="workspace">ワークスペース項目</option><option value="template">テンプレート</option></select></label>
            <label><span>{selectedUnit.source === 'template' ? 'テンプレート' : '項目'}</span><select value={selectedUnit.itemName ?? ''} onChange={(event) => update({ itemName: event.target.value })}>
              <option value="">選択してください</option>
              {(workItemHeaderByScreen[selectedUnit.kind as ScreenId]?.items ?? []).map((item) => <option value={item.name} key={item.name}>{item.name}{item.kind === 'comparison' ? '（比較）' : ''}</option>)}
            </select></label>
            {!selectedUnit.itemName && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>参照する項目が未選択です</b><small>どの項目を作るかが決まるまで、このユニットは実行できません。既定の項目で代用することはありません。</small></span></div>}
            {selectedUnitItem?.kind === 'comparison' && <p className="property-editor-note"><ShieldCheck size={12} />比較「{selectedUnit.itemName}」は基準ビュー「{selectedUnitItem.baseViewName}」を1本の軸で振った図です。ケースごとに同じ軸・同じカラーマップで生成されます。</p>}
            <label><span>リビジョン</span><input value="固定" readOnly /></label>
          </>}
        </div>
      </details>
      {(selectedUnit.kind === 'condition' || selectedUnit.kind === 'formula') && <details className="property-group" open>
        <summary><ChevronRight size={12} /><b>{selectedUnit.kind === 'condition' ? '条件式' : '数式'}</b></summary>
        <div className="property-fields">
          <ExpressionEditor
            id={`pipeline-${selectedUnit.id}`}
            label={selectedUnit.kind === 'condition' ? '分岐条件' : '評価式'}
            initial={selectedUnit.kind === 'condition' ? '最大応力 > 設計許容応力' : '安全率 = 設計許容応力 / 最大応力'}
          />
        </div>
      </details>}
      {selectedUnit.kind === 'loop' && <details className="property-group" open>
        <summary><ChevronRight size={12} /><b>反復</b></summary>
        <div className="property-fields">
          <label><span>反復元</span><select defaultValue="variable"><option value="variable">変数の値リスト</option><option value="cases">対象ケース</option></select></label>
          <label><span>回数</span><input value="有限・値リストの要素数" readOnly /></label>
        </div>
      </details>}
      {meta.destructive && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>破壊的ユニットです</b><small>影響するケース数を示す確認を経てのみ実行できます。単一キーのショートカットはありません。</small></span></div>}
      <details className="property-group" open>
        <summary><ChevronRight size={12} /><b>実行条件</b></summary>
        <div className="property-fields">
          <label className="property-toggle"><span>失敗時も他ケースを続行</span><input type="checkbox" defaultChecked /></label>
        </div>
      </details>
      <p className="property-editor-note"><ShieldCheck size={12} />参照先の更新で固定リビジョンは自動変更されません。</p>
    </div>
  )
}

const outlinerKindIcons: Record<ViewObjectKind | 'container', typeof Boxes> = {
  container: Boxes,
  'analysis-mesh': Shapes,
  'reference-mesh': Square,
  'scalar-field': Paintbrush,
  'vector-field': Waypoints,
  trajectory: Waypoints,
  'point-cloud': Grid2X2,
  annotation: Type,
  effect: Sparkles,
}

function OutlinerTypeIcon({ name, size = 11 }: { name: string; size?: number }) {
  const Icon = outlinerKindIcons[outlinerObjectKinds[name] ?? 'container']
  const kind = outlinerObjectKinds[name]
  const label = kind && kind !== 'container' ? viewObjectKinds[kind].label : 'データセットの入れ物'
  return <span className="outliner-kind-icon" title={label} aria-label={label}><Icon size={size} /></span>
}

function OutlinerPanel({ variant, selectedNames, onSelect, borrowedFrom }: { variant: string; selectedNames: string[]; onSelect: (name: string, additive?: boolean) => void; borrowedFrom: string | null }) {
  const flat = variant === 'outliner-flat'
  const empty = variant === 'outliner-empty'
  const [rootOpen, setRootOpen] = useState(true)
  const [assemblyOpen, setAssemblyOpen] = useState(true)
  const [partOpen, setPartOpen] = useState(true)
  const [hiddenNames, setHiddenNames] = useState<string[]>(['［元ファイルの領域名］'])
  const activeName = selectedNames.at(-1)
  const allNames = ['［元ファイルのルート名］', '［元ファイルのアセンブリ名］', '［元ファイルの部品名 01］', '［元ファイルの部品名 02］', '［元ファイルの領域名］']
  const descendants: Record<string, string[]> = { '［元ファイルのルート名］': allNames, '［元ファイルのアセンブリ名］': allNames.slice(1), '［元ファイルの部品名 02］': ['［元ファイルの部品名 02］', '［元ファイルの領域名］'] }
  const changeVisibility = (name: string, mode: 'single' | 'descendants' | 'isolate') => {
    setHiddenNames((current) => {
      if (mode === 'isolate') return allNames.filter((item) => item !== name && !(descendants[name] ?? []).includes(item))
      const targets = mode === 'descendants' ? descendants[name] ?? [name] : [name]
      const willHide = targets.some((item) => !current.includes(item))
      return willHide ? Array.from(new Set([...current, ...targets])) : current.filter((item) => !targets.includes(item))
    })
  }
  const isVisible = (name: string) => !hiddenNames.includes(name)
  return (
    <section className="outliner-panel">
      <header className="outliner-header">
        <b>アウトライナー</b>
        {borrowedFrom && <em className="outliner-borrowed">基準ビュー「{borrowedFrom}」の構成</em>}
      </header>
      <div className="outliner-tools">
        <label><Search size={12} /><input placeholder="構成要素を検索" /></label>
        <button aria-label="アウトライナーを絞り込む"><SlidersHorizontal size={13} /></button>
      </div>
      {empty ? (
        <div className="outliner-empty"><HardDrive size={22} /><b>データセット未読込</b><small>読み込むと元ファイルの構成を表示します。</small></div>
      ) : (
        <>
          {flat && <div className="outliner-status">元ファイルに親子関係がありません</div>}
          <div className="outliner-tree" role="tree" aria-label="解析ファイルの構成要素">
            <OutlinerRow depth={0} expanded={rootOpen} onToggle={() => setRootOpen((open) => !open)} icon={<HardDrive size={13} />} name="［元ファイルのルート名］" visible={isVisible('［元ファイルのルート名］')} selected={selectedNames.includes('［元ファイルのルート名］')} active={activeName === '［元ファイルのルート名］'} onSelect={onSelect} onVisibility={changeVisibility} />
            {rootOpen && (flat ? (
              <>
                <OutlinerRow depth={1} icon={<OutlinerTypeIcon name="［元ファイルの部品名 01］" />} name="［元ファイルの部品名 01］" visible={isVisible('［元ファイルの部品名 01］')} selected={selectedNames.includes('［元ファイルの部品名 01］')} active={activeName === '［元ファイルの部品名 01］'} onSelect={onSelect} onVisibility={changeVisibility} />
                <OutlinerRow depth={1} icon={<OutlinerTypeIcon name="［元ファイルの部品名 02］" />} name="［元ファイルの部品名 02］" visible={isVisible('［元ファイルの部品名 02］')} selected={selectedNames.includes('［元ファイルの部品名 02］')} active={activeName === '［元ファイルの部品名 02］'} onSelect={onSelect} onVisibility={changeVisibility} />
                <OutlinerRow depth={1} icon={<OutlinerTypeIcon name="［元ファイルの領域名］" />} name="［元ファイルの領域名］" visible={isVisible('［元ファイルの領域名］')} selected={selectedNames.includes('［元ファイルの領域名］')} active={activeName === '［元ファイルの領域名］'} onSelect={onSelect} onVisibility={changeVisibility} />
              </>
            ) : (
              <>
                <OutlinerRow depth={1} expanded={assemblyOpen} onToggle={() => setAssemblyOpen((open) => !open)} icon={<OutlinerTypeIcon name="［元ファイルのアセンブリ名］" size={12} />} name="［元ファイルのアセンブリ名］" visible={isVisible('［元ファイルのアセンブリ名］')} selected={selectedNames.includes('［元ファイルのアセンブリ名］')} active={activeName === '［元ファイルのアセンブリ名］'} onSelect={onSelect} onVisibility={changeVisibility} />
                {assemblyOpen && <>
                  <OutlinerRow depth={2} icon={<OutlinerTypeIcon name="［元ファイルの部品名 01］" />} name="［元ファイルの部品名 01］" visible={isVisible('［元ファイルの部品名 01］')} selected={selectedNames.includes('［元ファイルの部品名 01］')} active={activeName === '［元ファイルの部品名 01］'} onSelect={onSelect} onVisibility={changeVisibility} />
                  <OutlinerRow depth={2} expanded={partOpen} onToggle={() => setPartOpen((open) => !open)} icon={<OutlinerTypeIcon name="［元ファイルの部品名 02］" />} name="［元ファイルの部品名 02］" visible={isVisible('［元ファイルの部品名 02］')} selected={selectedNames.includes('［元ファイルの部品名 02］')} active={activeName === '［元ファイルの部品名 02］'} onSelect={onSelect} onVisibility={changeVisibility} />
                  {partOpen && <OutlinerRow depth={3} icon={<OutlinerTypeIcon name="［元ファイルの領域名］" />} name="［元ファイルの領域名］" visible={isVisible('［元ファイルの領域名］')} selected={selectedNames.includes('［元ファイルの領域名］')} active={activeName === '［元ファイルの領域名］'} onSelect={onSelect} onVisibility={changeVisibility} />}
                </>}
              </>
            ))}
          </div>
        </>
      )}
    </section>
  )
}

function OutlinerRow({ depth, expanded, onToggle, icon, name, visible, selected, active, onSelect, onVisibility }: { depth: number; expanded?: boolean; onToggle?: () => void; icon: React.ReactNode; name: string; visible: boolean; selected?: boolean; active?: boolean; onSelect?: (name: string, additive?: boolean) => void; onVisibility?: (name: string, mode: 'single' | 'descendants' | 'isolate') => void }) {
  const select = (event: React.MouseEvent | React.KeyboardEvent) => {
    onSelect?.(name, event.shiftKey)
  }
  return <div className={`outliner-row ${selected ? 'selected' : ''} ${active ? 'active' : ''}`} role="treeitem" aria-level={depth + 1} aria-expanded={onToggle ? expanded : undefined} aria-selected={selected} aria-current={active ? 'true' : undefined} tabIndex={0} onClick={select} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(event) } }} style={{ '--tree-indent': `${depth * 15}px` } as React.CSSProperties}><Button variant="ghost" size="icon" className="outliner-disclosure" aria-label={onToggle ? expanded ? '折りたたむ' : '展開する' : undefined} onClick={(event) => { event.stopPropagation(); onToggle?.() }} disabled={!onToggle}>{onToggle ? expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} /> : <span />}</Button><span className="outliner-type-icon">{icon}</span><b title={name}>{name}</b><Button variant="ghost" size="icon" className="outliner-visibility" aria-label={visible ? `${name}を非表示` : `${name}を表示`} onClick={(event) => { event.stopPropagation(); onVisibility?.(name, event.ctrlKey ? 'isolate' : event.shiftKey ? 'descendants' : 'single') }}>{visible ? <Eye size={13} /> : <EyeOff size={13} />}</Button></div>
}

function ScreenCanvas({ scenario, draft, onDraftChange, onViewObjectSelect, onScreen, settings, onSettingsChange, pipelineUnits, onPipelineUnitsChange, selectedUnitId, onSelectUnit, selectedCase, viewItem, onViewItemChange, isComparisonItem, comparison, baseViewName, splitPanes, promoteOpen, onPromoteOpenChange }: { scenario: Scenario; draft: string; onDraftChange: (draft: string) => void; onViewObjectSelect: (name: string, additive?: boolean) => void; onScreen: (screen: ScreenId) => void; settings: ConversationSettings; onSettingsChange: (settings: ConversationSettings) => void; pipelineUnits: PipelineUnitModel[]; onPipelineUnitsChange: (units: PipelineUnitModel[]) => void; selectedUnitId: string | null; onSelectUnit: (id: string) => void; selectedCase: string; viewItem: ViewItemState; onViewItemChange: (next: ViewItemState) => void; isComparisonItem: boolean; comparison: ComparisonModel; baseViewName: string; splitPanes: number; promoteOpen: boolean; onPromoteOpenChange: (open: boolean) => void }) {
  switch (scenario.screen) {
    case 'simulation': return <SimulationScreen variant={scenario.variant} onAutomation={() => onScreen('pipeline')} />
    case 'pipeline': return <PipelineScreen variant={scenario.variant} units={pipelineUnits} onUnitsChange={onPipelineUnitsChange} selectedUnitId={selectedUnitId} onSelectUnit={onSelectUnit} />
    case 'view': return <ViewScreen variant={scenario.variant} onViewObjectSelect={onViewObjectSelect} selectedCase={selectedCase} viewItem={viewItem} onViewItemChange={onViewItemChange} isComparisonItem={isComparisonItem} comparison={comparison} baseViewName={baseViewName} splitPanes={splitPanes} promoteOpen={promoteOpen} onPromoteOpenChange={onPromoteOpenChange} />
    case 'graph': return <GraphScreen variant={scenario.variant} />
    case 'report': return <ReportScreen variant={scenario.variant} />
    case 'chat': return <ChatScreen variant={scenario.variant} draft={draft} onDraftChange={onDraftChange} settings={settings} onSettingsChange={onSettingsChange} />
    case 'settings': return <SettingsScreen variant={scenario.variant} />
    case 'network': return <NetworkScreen variant={scenario.variant} onSettings={() => onScreen('settings')} />
    default: return null
  }
}

// A saved Simulation is one flow grouping the conditions for one or more external-solver executions,
// not one row per solver process (GL-043, XC-154). Execution is a later release (XC-091): the flow is
// editable and savable now, and r1 never claims to produce a result Case from it.
const simulationSteps = [
  { name: 'メッシュ入力', detail: 'ケース「基準ケース」の入力ファイルを参照', state: 'resolved' as const },
  { name: '材料条件', detail: '設計許容応力 235 MPa を変数から束縛', state: 'resolved' as const },
  { name: '境界条件', detail: '固定面・荷重面をパートから指定', state: 'resolved' as const },
  { name: 'ソルバー呼び出し', detail: '外部ソルバーのアダプターを指定', state: 'later' as const },
]

function SimulationScreen({ variant, onAutomation }: { variant: string; onAutomation: () => void }) {
  if (variant === 'empty') {
    return <div className="centred-state"><Gauge size={34} /><h2>保存されたシミュレーションがありません</h2><p>ヘッダーの「＋ 新規シミュレーション」で、外部ソルバー実行の条件をまとめた保存フローを作成します。r1では定義の保存までを行い、結果ケースは作成しません。</p><div className="button-row"><button className="primary-button">＋ 新規シミュレーション</button><button onClick={onAutomation}>自動化を開く</button></div></div>
  }
  if (variant === 'unavailable') {
    return <div className="centred-state"><Gauge size={34} /><span className="eyebrow">後続リリース</span><h2>シミュレーション実行はr1に含まれません</h2><p>既存ソルバーの結果を取り込み、自動化モードでビュー、グラフ、レポートを生成できます。定義の保存と編集は現在も可能です。</p><button className="primary-button" onClick={onAutomation}>自動化を開く</button></div>
  }
  const unresolved = variant === 'unresolved'
  return (
    <div className="simulation-canvas">
      {unresolved
        ? <StatePanel tone="error" title="実行条件を解決できません" detail="材料条件が参照する変数「設計許容応力」が未宣言です。ソルバーアダプター「未接続」も解決していません。条件が揃うまで実行は拒否され、既存の定義は変更されていません。" />
        : <StatePanel tone="progress" title="定義は保存できます・実行は後続リリース" detail="この保存フローは条件をまとめたものです。r1では外部ソルバーを呼び出さず、結果ケースを作成しません（XC-091）。" />}
      <ol className="simulation-steps">
        {simulationSteps.map((step, index) => {
          const failed = unresolved && (step.name === '材料条件' || step.name === 'ソルバー呼び出し')
          return (
            <li className={failed ? 'failed' : step.state === 'later' ? 'later' : 'resolved'} key={step.name}>
              <span className="simulation-step-index">{index + 1}</span>
              <span>
                <b>{step.name}</b>
                <small>{failed && step.name === '材料条件' ? '変数「設計許容応力」が未宣言・代替値なし' : failed ? 'アダプター未接続・実行は拒否' : step.detail}</small>
              </span>
              <em>{failed ? '未解決' : step.state === 'later' ? '後続リリース' : '解決済み'}</em>
            </li>
          )
        })}
      </ol>
      <p className="workflow-trust-note"><AlertTriangle size={13} />このフローは1回以上の外部ソルバー実行の条件をまとめた1件の保存対象です。ソルバープロセス1件につき1行ではありません。</p>
    </div>
  )
}

// The @Pipeline the Automation centre edits. The unit list lives in the shell because the palette in
// the right sidebar and the editor in the centre act on one pipeline; two copies would let a unit
// added on the right never appear in the middle (XC-155).
type PipelineUnitKind = 'simulation' | 'case' | 'view' | 'graph' | 'report' | 'export' | 'tag' | 'clear' | 'loop' | 'variable' | 'formula' | 'condition'

type PipelineUnitModel = {
  id: string
  kind: PipelineUnitKind
  title: string
  detail: string
  addsCases?: number
  children?: PipelineUnitModel[]
  // XC-211: which item this unit produces, and whether it comes from the workspace or a template.
  source?: 'workspace' | 'template'
  itemName?: string
}

const pipelineUnitCatalogue: Record<PipelineUnitKind, { label: string; detail: string; icon: typeof Boxes; destructive?: boolean; zone?: boolean }> = {
  simulation: { label: 'シミュレーション', detail: '保存済み実行定義', icon: Gauge, zone: true },
  case: { label: 'ケース', detail: '対象セットへ追加', icon: FolderOpen },
  view: { label: 'ビュー', detail: '可視化を生成', icon: Boxes },
  graph: { label: 'グラフ', detail: '図を生成', icon: BarChart3 },
  report: { label: 'レポート', detail: '文書を生成', icon: FileText },
  export: { label: '出力', detail: 'ファイルへ書き出し', icon: FileOutput },
  tag: { label: 'タグ', detail: 'ケースへ明示的に付与', icon: Tag },
  clear: { label: 'クリア', detail: '対象データを解放', icon: Trash2, destructive: true },
  loop: { label: 'ループ', detail: '有限回の反復', icon: RefreshCw, zone: true },
  variable: { label: '変数', detail: '以降のユニットへ束縛', icon: Variable },
  formula: { label: '数式', detail: '単位付き式を評価', icon: Ruler },
  condition: { label: '条件', detail: '式による分岐', icon: Waypoints, zone: true },
}

const defaultPipelineUnits: PipelineUnitModel[] = [
  { id: 'unit-cases', kind: 'case', title: 'ケースユニット', detail: '設計スタディの3ケースを明示選択', addsCases: 3 },
  { id: 'unit-loop', kind: 'loop', title: 'ループ・material_variant', detail: '3反復', children: [
    { id: 'unit-view', kind: 'view', title: 'ビュー・ケース比較', detail: '比較「ケース比較」をケースごとに生成', source: 'workspace', itemName: 'ケース比較' },
    { id: 'unit-graph', kind: 'graph', title: 'グラフ・ケース比較', detail: 'ケースごとに生成', source: 'workspace', itemName: 'ケース比較グラフ' },
  ] },
  { id: 'unit-condition', kind: 'condition', title: '条件・許容応力の超過', detail: '式：最大応力 > 設計許容応力', children: [
    { id: 'unit-report', kind: 'report', title: 'レポート・設計レビュー', detail: '超過したケースだけ生成', source: 'workspace', itemName: '設計レビューレポート' },
  ] },
  { id: 'unit-export', kind: 'export', title: '出力ユニット', detail: '新しい実行フォルダーへ書き出し' },
  { id: 'unit-clear', kind: 'clear', title: 'クリアユニット', detail: '読み込み済みデータを解放し対象セットを空にする' },
]

// XC-099: the target set accumulates down the list, so the count a unit acts on is invisible unless it
// is computed here and drawn on every unit - including the ones inside a bounded zone.
function annotatePipelineTargets(units: PipelineUnitModel[]) {
  let targets = 0
  return units.map((unit) => {
    if (unit.kind === 'case') targets += unit.addsCases ?? 0
    const row = { unit, acts: targets, children: (unit.children ?? []).map((child) => ({ unit: child, acts: targets })) }
    if (unit.kind === 'clear') targets = 0
    return row
  })
}

function flattenPipelineUnits(units: PipelineUnitModel[]): PipelineUnitModel[] {
  return units.flatMap((unit) => [unit, ...(unit.children ?? [])])
}

const pipelineRunCases = ['基準ケース', '板厚変更', '荷重変更']
type RunOutcome = 'applied' | 'skipped' | 'failed' | 'refused'
const runOutcomeLabels: Record<RunOutcome, string> = { applied: '適用', skipped: 'スキップ', failed: '失敗', refused: '不成立' }

// The shared run outcome table: per case and per unit, what happened - and, for a condition that did
// not hold, the value it evaluated to. Without that last part a refused unit reads the same as one
// that was never reached.
function pipelineRunOutcome(units: PipelineUnitModel[], failedCase: string | null) {
  return pipelineRunCases.map((caseName) => {
    let broken = false
    const cells = units.map((unit) => {
      if (broken) return { unit, outcome: 'skipped' as RunOutcome, note: '先行ユニットの失敗により未実行' }
      if (failedCase === caseName && unit.kind === 'graph') {
        broken = true
        return { unit, outcome: 'failed' as RunOutcome, note: '参照した数量がこのケースにありません' }
      }
      if (unit.kind === 'report' && caseName === '基準ケース') {
        return { unit, outcome: 'refused' as RunOutcome, note: '条件の評価値：false（［最大応力］ ≦ ［設計許容応力］）' }
      }
      return { unit, outcome: 'applied' as RunOutcome, note: '' }
    })
    return { caseName, cells }
  })
}

function RunOutcomeTable({ units, failedCase }: { units: PipelineUnitModel[]; failedCase: string | null }) {
  const rows = pipelineRunOutcome(units, failedCase)
  return (
    <section className="run-outcome-table" aria-label="ケースとユニットごとの実行結果">
      <header><b>実行結果</b><small>ケース × ユニット。不成立には条件の評価値を併記します</small></header>
      <div className="run-outcome-scroll">
        <table>
          <thead><tr><th scope="col">ケース</th>{units.map((unit) => <th scope="col" key={unit.id}>{unit.title}</th>)}</tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.caseName}>
                <th scope="row">{row.caseName}</th>
                {row.cells.map((cell) => (
                  <td className={`run-outcome-${cell.outcome}`} key={cell.unit.id}>
                    <b>{runOutcomeLabels[cell.outcome]}</b>
                    {cell.note && <small>{cell.note}</small>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function PipelineScreen({ variant, units, onUnitsChange, selectedUnitId, onSelectUnit }: { variant: string; units: PipelineUnitModel[]; onUnitsChange: (units: PipelineUnitModel[]) => void; selectedUnitId: string | null; onSelectUnit: (id: string) => void }) {
  const [flowState, setFlowState] = useState<'editing' | 'dry-run' | 'confirm-run' | 'running' | 'finished'>(variant === 'dry-run' ? 'dry-run' : variant === 'running' ? 'running' : variant === 'failed' ? 'finished' : 'editing')
  const [scopeUnitId, setScopeUnitId] = useState<string | null>(variant === 'scope-confirmation' ? 'unit-clear' : null)
  const [authorisedUnitIds, setAuthorisedUnitIds] = useState<string[]>([])
  const [dropIndex, setDropIndex] = useState<number | null>(null)
  const [draggedId, setDraggedId] = useState<string | null>(null)
  const rows = annotatePipelineTargets(units)
  const flattened = flattenPipelineUnits(units)
  const destructiveUnits = units.filter((unit) => pipelineUnitCatalogue[unit.kind].destructive)
  const scopeUnit = units.find((unit) => unit.id === scopeUnitId) ?? null
  const scopeUnitTargets = rows.find((row) => row.unit.id === scopeUnitId)?.acts ?? 0
  const unauthorised = destructiveUnits.filter((unit) => !authorisedUnitIds.includes(unit.id))
  const running = flowState === 'running'
  const failedCase = variant === 'failed' ? '板厚変更' : null

  const moveUnit = (id: string, direction: -1 | 1) => {
    const index = units.findIndex((unit) => unit.id === id)
    const target = index + direction
    if (index < 0 || target < 0 || target >= units.length) return
    const next = [...units]
    const moved = next[index]
    next[index] = next[target]
    next[target] = moved
    onUnitsChange(next)
  }

  const dropUnit = (index: number) => {
    setDropIndex(null)
    if (!draggedId) return
    const from = units.findIndex((unit) => unit.id === draggedId)
    setDraggedId(null)
    if (from < 0) return
    const without = units.filter((unit) => unit.id !== draggedId)
    const at = index > from ? index - 1 : index
    onUnitsChange([...without.slice(0, at), units[from], ...without.slice(at)])
  }

  const removeUnit = (id: string) => onUnitsChange(units.filter((unit) => unit.id !== id))

  const dropTarget = (index: number) => ({
    onDragOver: (event: React.DragEvent) => { if (!draggedId || running) return; event.preventDefault(); setDropIndex(index) },
    onDrop: (event: React.DragEvent) => { event.preventDefault(); if (!running) dropUnit(index) },
  })

  if (units.length === 0) return <div className="centred-state"><Workflow size={34} /><h2>パイプラインが空です</h2><p>右側のユニットパレットから処理を追加し、最初にドライランで対象ケースと生成物を確認します。</p><button className="primary-button" type="button" onClick={() => onUnitsChange([defaultPipelineUnits[0]])}><Plus size={14} /> 最初のユニットを追加</button></div>

  const banner = running
    ? <StatePanel tone="progress" title="パイプライン実行中" detail="閲覧は継続できます。実行対象のワークスペースは編集できません。中止はユニット境界です。" />
    : variant === 'failed'
      ? <StatePanel tone="error" title="1ケースが失敗しました" detail="板厚変更ケースがグラフユニットで失敗しました。このケースの後続ユニットだけをスキップし、他ケースは継続しています。失敗は通知履歴にも残ります。" />
      : flowState === 'dry-run'
        ? <StatePanel tone="info" title="ドライランのみ" detail={pipelineRunCases.length + 'ケース、ユニット' + flattened.length + '件、ファイル書込0件。各ユニットの累積対象数と入れ子を以下に表示します。'} />
        : null

  return (
    <div className="pipeline-canvas">
      {banner}
      <header className="pipeline-editor-header">
        <div><span className="eyebrow">パイプライン</span><b>レポート生成フロー</b><small>上から順に実行・対象セットを累積</small></div>
        <div className="pipeline-actions"><button type="button" disabled={running} onClick={() => setFlowState('dry-run')}><Play size={14} /> ドライラン</button><button className="primary-button" type="button" disabled={running} onClick={() => setFlowState('confirm-run')}><Play size={14} /> 実行</button>{running && <button type="button" onClick={() => setFlowState('finished')}><X size={14} />ユニット境界で中止</button>}</div>
      </header>
      {unauthorised.length > 0 && !running && <p className="pipeline-authorisation-note"><AlertTriangle size={13} /><span>破壊的ユニット「{unauthorised[0].title}」は影響範囲を確認するまで実行できません。</span><button type="button" onClick={() => setScopeUnitId(unauthorised[0].id)}>範囲を確認</button></p>}
      <div className="pipeline-units">
        <div className="pipeline-boundary pipeline-boundary-start"><span>開始</span><small>対象セット 0</small></div>
        {rows.map((row, index) => {
          const meta = pipelineUnitCatalogue[row.unit.kind]
          const ZoneIcon = meta.icon
          return (
            <Fragment key={row.unit.id}>
              <div className={`pipeline-drop-line ${dropIndex === index ? 'active' : ''}`} aria-hidden="true" {...dropTarget(index)} />
              {meta.zone ? (
                <div className={`bounded-zone ${selectedUnitId === row.unit.id ? 'selected' : ''}`} draggable={!running} onDragStart={() => setDraggedId(row.unit.id)} onDragEnd={() => { setDraggedId(null); setDropIndex(null) }}>
                  <header onClick={() => onSelectUnit(row.unit.id)}><ZoneIcon size={14} /><b>{row.unit.title}</b><span>{row.unit.detail}・対象{row.acts}</span><PipelineUnitControls disabled={running} onUp={() => moveUnit(row.unit.id, -1)} onDown={() => moveUnit(row.unit.id, 1)} onRemove={() => removeUnit(row.unit.id)} title={row.unit.title} /></header>
                  {row.children.map((child) => {
                    const ChildIcon = pipelineUnitCatalogue[child.unit.kind].icon
                    return <PipelineUnit key={child.unit.id} icon={<ChildIcon />} title={child.unit.title} detail={child.unit.detail} count={`対象${child.acts}`} failed={variant === 'failed' && child.unit.kind === 'graph'} muted={variant === 'failed' && child.unit.kind === 'report'} selected={selectedUnitId === child.unit.id} onSelect={() => onSelectUnit(child.unit.id)} />
                  })}
                  {row.children.length === 0 && <p className="bounded-zone-empty">このゾーンにユニットがありません。</p>}
                </div>
              ) : (
                <div draggable={!running} onDragStart={() => setDraggedId(row.unit.id)} onDragEnd={() => { setDraggedId(null); setDropIndex(null) }}>
                  <PipelineUnit
                    icon={<ZoneIcon />}
                    title={row.unit.title}
                    detail={row.unit.detail}
                    count={`対象${row.acts}`}
                    failed={variant === 'failed' && row.unit.kind === 'graph'}
                    muted={variant === 'failed' && row.unit.kind === 'export'}
                    destructive={meta.destructive}
                    authorised={authorisedUnitIds.includes(row.unit.id)}
                    selected={selectedUnitId === row.unit.id}
                    onSelect={() => onSelectUnit(row.unit.id)}
                    onScope={meta.destructive ? () => setScopeUnitId(row.unit.id) : undefined}
                    controls={<PipelineUnitControls disabled={running} onUp={() => moveUnit(row.unit.id, -1)} onDown={() => moveUnit(row.unit.id, 1)} onRemove={() => removeUnit(row.unit.id)} title={row.unit.title} />}
                  />
                </div>
              )}
            </Fragment>
          )
        })}
        <div className={`pipeline-drop-line ${dropIndex === units.length ? 'active' : ''}`} aria-hidden="true" {...dropTarget(units.length)} />
        <button className="pipeline-insert" type="button" disabled={running} onClick={() => onUnitsChange([...units, { id: `unit-added-${units.length + 1}`, kind: 'case', title: 'ケースユニット', detail: 'ケースを選択してください', addsCases: 0 }])}><Plus size={13} /> ユニットを追加</button>
        <div className="pipeline-boundary pipeline-boundary-end"><span>完了</span><small>生成物を記録</small></div>
      </div>
      {running && <p className="pipeline-edit-lock" role="status"><AlertTriangle size={13} />実行中はこのワークスペースを編集できません。実行の対象が途中で変わってしまうためです（pipeline/AC-040）。</p>}
      {(variant === 'failed' || flowState === 'finished') && <RunOutcomeTable units={flattened} failedCase={failedCase} />}
      {scopeUnit && <ModalCard
        open
        onClose={() => setScopeUnitId(null)}
        title={`${scopeUnit.title}を許可しますか？`}
        detail={`このユニットは対象セットの${scopeUnitTargets}ケースに影響し、読み込み済みデータを解放します。書込済みファイルは削除しません。同じ数はドライランでも確認できます。`}
      >
        <button type="button" onClick={() => setScopeUnitId(null)}>キャンセル</button>
        <button type="button" className="danger-button" onClick={() => { setAuthorisedUnitIds((current) => [...current, scopeUnit.id]); setScopeUnitId(null) }}>{scopeUnitTargets}ケースの範囲で許可</button>
      </ModalCard>}
      {flowState === 'confirm-run' && <Dialog open onOpenChange={(open) => !open && setFlowState('editing')}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog"><header><span><small>実行前確認</small><b>ドライラン結果の対象で実行</b></span><button type="button" aria-label="実行確認を閉じる" onClick={() => setFlowState('editing')}><X size={15} /></button></header><section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>対象セット</b><small>各ユニットの累積対象数を確定済み</small></span></p><p><CheckCircle2 size={13} /><span><b>生成物</b><small>新しい実行フォルダーに保存・上書きなし</small></span></p><p><AlertTriangle size={13} /><span><b>編集ロック</b><small>実行中は閲覧のみ。中止はユニット境界</small></span></p>{unauthorised.length > 0 && <p><AlertTriangle size={13} /><span><b>未許可の破壊的ユニット</b><small>{unauthorised.map((unit) => unit.title).join('・')}の範囲確認が必要です</small></span></p>}</section><footer><button type="button" onClick={() => setFlowState('editing')}>キャンセル</button><button type="button" className="primary-button" disabled={unauthorised.length > 0} onClick={() => setFlowState('running')}>実行を開始</button></footer></DialogContent></Dialog>}
    </div>
  )
}

function PipelineUnitControls({ disabled, onUp, onDown, onRemove, title }: { disabled: boolean; onUp: () => void; onDown: () => void; onRemove: () => void; title: string }) {
  return <span className="pipeline-unit-controls">
    <button type="button" aria-label={`${title}を上へ移動`} disabled={disabled} onClick={(event) => { event.stopPropagation(); onUp() }}><ChevronUp size={12} /></button>
    <button type="button" aria-label={`${title}を下へ移動`} disabled={disabled} onClick={(event) => { event.stopPropagation(); onDown() }}><ChevronDown size={12} /></button>
    <button type="button" aria-label={`${title}を削除`} disabled={disabled} onClick={(event) => { event.stopPropagation(); onRemove() }}><X size={12} /></button>
  </span>
}

function PipelineUnit({ icon, title, detail, count, failed, muted, destructive, authorised, selected, onSelect, onScope, controls }: { icon: React.ReactNode; title: string; detail: string; count: string; failed?: boolean; muted?: boolean; destructive?: boolean; authorised?: boolean; selected?: boolean; onSelect?: () => void; onScope?: () => void; controls?: React.ReactNode }) {
  return <div className={`pipeline-unit ${failed ? 'failed' : ''} ${muted ? 'muted' : ''} ${destructive ? 'destructive' : ''} ${selected ? 'selected' : ''}`} onClick={onSelect}>
    <span>{icon}</span>
    <div><b>{title}</b><small>{detail}</small>{destructive && <em className={authorised ? 'unit-scope authorised' : 'unit-scope'}>{authorised ? '範囲を許可済み' : '実行前に範囲確認が必要'}</em>}</div>
    <em>{failed ? '失敗' : muted ? 'スキップ' : count}</em>
    {onScope && <button type="button" className="pipeline-unit-scope-button" onClick={(event) => { event.stopPropagation(); onScope() }}>範囲</button>}
    {controls}
    <ChevronRight size={14} />
  </div>
}

// XC-131: a @Case is indexed by an axis that is not always time. XC-160 formats the scrubber readout
// per axis and commits the exact pointer position unless the source axis is itself discrete. The
// overlay used to print `m:ss` on every variant, so the mode-axis state showed a clock.
function ViewScreen({ variant, onViewObjectSelect, selectedCase, viewItem, onViewItemChange, isComparisonItem, comparison, baseViewName, splitPanes, promoteOpen, onPromoteOpenChange }: { variant: string; onViewObjectSelect: (name: string, additive?: boolean) => void; selectedCase: string; viewItem: ViewItemState; onViewItemChange: (next: ViewItemState) => void; isComparisonItem: boolean; comparison: ComparisonModel; baseViewName: string; splitPanes: number; promoteOpen: boolean; onPromoteOpenChange: (open: boolean) => void }) {
  const [playbackVisible, setPlaybackVisible] = useState(false)
  // What each pane shows is session state too: a split is thrown away, so its bindings go with it
  // (XC-202). The count and the sync live in the area bar, above the canvas they divide (XC-204).
  const [paneBindings, setPaneBindings] = useState(() => ['cam-front', 'cam-iso', 'cam-peak', 'cam-fixture'].map((cameraId, index) => ({
    caseName: index === 0 ? selectedCase : workspaceCases[index % workspaceCases.length].name,
    cameraId,
  })))
  const bindPane = (index: number, patch: { caseName?: string; cameraId?: string }) =>
    setPaneBindings((current) => current.map((binding, position) => position === index ? { ...binding, ...patch } : binding))
  const [promoteAxis, setPromoteAxis] = useState<'case' | 'camera' | 'resultPosition'>('case')
  if (variant === 'empty') return <div className="centred-state"><Boxes size={34} /><h2>表示するケースがありません</h2><p>開始プリセットを選ぶか、ワークスペースへ結果ファイルをドロップします。</p><div className="button-row"><button className="primary-button">開始プリセット</button><button>テンプレート</button></div></div>
  if (variant === 'renderer-error') return <div className="centred-state error-state"><AlertTriangle size={34} /><h2>Omniverseレンダラーを開始できません</h2><p>バックエンドを利用できません。VTK軽量レンダラーは利用できます。</p><button className="primary-button">VTKで続ける</button></div>
  const comparisonMembers = isComparisonItem ? comparisonMemberLabels(comparison) : []
  const comparisonOverlay = isComparisonItem && comparison.arrangement === 'overlay'
  const comparisonGrid = isComparisonItem && comparison.arrangement === 'grid'
  const panes = comparisonGrid ? comparisonMembers.length : splitPanes
  const deformed = variant === 'deformation'
  const axis: ResultAxisKind = variant === 'axis-error' ? 'mode' : 'time'
  // Which case each pane shows. The tree supplies the selected case; the other panes name the case they
  // compare against, because a split view whose panes are unlabelled is a screenshot nobody can read.
  const paneCases = comparisonGrid
    ? comparisonMembers
    : Array.from({ length: panes }, (_, index) => index === 0 ? selectedCase : paneBindings[index].caseName)
  return (
    <div className="view-canvas" onMouseEnter={() => setPlaybackVisible(true)} onMouseLeave={() => setPlaybackVisible(false)}>
      {variant === 'reduced' && <StatePanel tone="warning" title="表示形状を縮退しています" detail="画面は縮退形状を使用します。表示値とレポート計算は完全データを使用します。" />}
      {variant === 'unresolved-template' && <UnresolvedList
        title="テンプレートを一部解決できません"
        source="ビューテンプレート「技術資料・標準」"
        revision="リビジョン 3"
        resolved={['レイアウト・1画面', 'カメラ・保存済み等角', '背景・スタジオライト']}
        unresolved={[
          { item: 'フィールド「応力」', reason: 'このケースに同名のフィールドがありません。代替値は使用しません' },
          { item: 'マテリアル「スチールブルー」', reason: '参照アセットのリビジョンがこのワークスペースに存在しません' },
        ]}
      />}
      {variant === 'camera-unresolved' && <StatePanel tone="error" title="視点「最大応力へ寄せる」を解決できません" detail="規則が参照する数量「最大応力」がこのケースにありません。カメラは動かしていません。結果軸ブックマークも同じ理由で解決していません。" />}
      {variant === 'cameras' && <StatePanel tone="info" title="1つのビューが複数のカメラを持ちます" detail="各画面は覗くカメラを名指しします。「最大応力へ寄せる」は座標ではなく規則を保持するため、4分割ではそれぞれのケースの位置に解決します。" />}
      {variant === 'timelines' && <StatePanel tone="info" title="1つのビューが複数のタイムラインを持ちます" detail="再生範囲・速度・カメラパスの組をそれぞれ保存します。カメラパスは「保存した結果位置 × カメラ」で組み立てるため、同じパスがケースごとに違う瞬間・違う距離になります。" />}
      {variant === 'develop-grade' && <StatePanel tone="info" title="現像プリセット：計測（無補正）" detail="根拠として引用する画像は無補正で出力します。補正を掛ける場合は、凡例も同じ補正を通すか、補正名とパラメータを成果物に記載します。" />}
      {variant === 'steady-result' && <StatePanel tone="info" title="定常結果・再生する軸がありません" detail="このケースは結果軸を持ちません。再生オーバーレイは無効な帯として置くのではなく、出しません。動画と再生プリセットは出力タブで利用不可と表示します。" />}
      {variant === 'result-bookmarks' && <StatePanel tone="info" title="結果軸ブックマーク" detail="固定位置・極値・しきい値交差を登録できます。規則はケースごとに解決し、保存位置の間に落ちたときは丸めた事実を明示します。" />}
      {variant === 'axis-error' && <StatePanel tone="error" title="指定した結果位置がありません" detail="要求されたモード8は存在しません。ビューはモード7のままで、近傍位置への丸めは行っていません。" />}
      {deformed && <StatePanel tone="warning" title="変形を50倍に誇張して表示しています" detail="測定・プローブ・レポートの値は未変形形状から計算します。画面上の形状を定規で測ると誤った寸法になります。" />}
      {/* XC-209: the canvas carries no split chrome at any pane count. Of what this strip said, the
          count, the camera sync and the way back to one pane are the area bar's menu, and each pane's
          subject is on its own badge - only the two facts unique to a split moved into that menu. */}
      {comparisonGrid && <div className="comparison-bar">
        <span className="comparison-axis-chip"><Columns3 size={12} />{comparisonAxisLabels[comparison.axis].replace('基準ビューのプロパティ：', '')}で比較・{comparisonMembers.length}メンバー</span>
        <small>{comparison.sharedColourMap ? '全ペインが同じカラーマップと同じ範囲で描かれます。' : 'ペインごとに範囲が異なります。図にその旨を記載します。'}基準ビュー「{baseViewName}」の設定を共有します。</small>
      </div>}
      {comparisonOverlay && <div className="comparison-overlay-note"><Layers3 size={13} /><span><b>重ね合わせ・結果色は1メンバーのみ</b><small>「{comparisonMembers[0]}」が結果色を持ち、{comparisonMembers.slice(1).join('と')}は参照形状として描かれます。カラーマップと範囲は共有です。基準ビュー「{baseViewName}」の設定を使います。</small></span></div>}
      {/* The canvas is laid out from the same rule the rail states, so the two cannot disagree - a
          panel reading "2行3列" over a canvas drawing one row of six is the defect XC-205 closes. */}
      <div className={`pane-grid panes-${comparisonOverlay ? 1 : panes} ${comparisonGrid ? 'comparison-grid' : ''}`} style={comparisonGrid ? { '--comparison-columns': comparisonGridColumns(comparisonMembers.length, comparison.columns) } as React.CSSProperties : undefined}>
        {paneCases.map((paneCase, index) => (
          <div className="view-pane" key={index}>
            {/* The badge is the pane's subject picker: the split bar tells the reader to click it, so
                it has to be a control rather than a label (XC-202 puts every split control here). */}
            {comparisonGrid ? (
              <span className="view-pane-subject">
                <span><FolderOpen size={11} />{paneCase}</span>
                <i aria-hidden="true" />
                <span><Camera size={11} />{viewItem.cameras.find((item) => item.id === viewItem.activeCameraId)?.name ?? '削除されたカメラ'}</span>
              </span>
            ) : (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button type="button" className="view-pane-subject" aria-label={`画面 ${index + 1} のケースとカメラを選ぶ`}>
                    <span><FolderOpen size={11} />{paneCase}{index === 0 && panes > 1 ? '・ツリー選択' : ''}</span>
                    <i aria-hidden="true" />
                    <span><Camera size={11} />{viewItem.cameras.find((item) => item.id === paneBindings[index].cameraId)?.name ?? '削除されたカメラ'}</span>
                    <ChevronDown size={10} aria-hidden="true" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="center" className="pane-subject-menu">
                  <div className="pane-subject-section"><small>ケース</small>{workspaceCases.map((item) => (
                    <DropdownMenuItem key={item.name} onSelect={() => bindPane(index, { caseName: item.name })}><span>{item.name}</span>{paneCase === item.name && <span aria-hidden="true">✓</span>}</DropdownMenuItem>
                  ))}</div>
                  <div className="pane-subject-section"><small>カメラ</small>{viewItem.cameras.map((item) => (
                    <DropdownMenuItem key={item.id} onSelect={() => bindPane(index, { cameraId: item.id })}><span>{item.name}</span>{paneBindings[index].cameraId === item.id && <span aria-hidden="true">✓</span>}</DropdownMenuItem>
                  ))}</div>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            <Viewport paneIndex={index} compact={panes > 1} onObjectSelect={onViewObjectSelect} />
            {/* INV-024: the factor is drawn into the picture, not only into a toolbar. A reader
                measuring the image never reads the toolbar, and an exported image has none. */}
            {deformed && <span className="deformation-stamp">変形倍率 ×50</span>}
          </div>
        ))}
      </div>
      {promoteOpen && <Dialog open onOpenChange={onPromoteOpenChange}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog">
        <header><span><small>画面分割</small><b>この比較を保存</b></span><button type="button" aria-label="比較の保存を閉じる" onClick={() => onPromoteOpenChange(false)}><X size={15} /></button></header>
        <p>分割はセッションの状態で、保存されません。比較として保存すると、再現でき、パイプラインからケースごとに量産できる項目になります。</p>
        <div className="settings-fields">
          <label><span>名前</span><input defaultValue="ケース比較" /></label>
          <label><span>変える軸</span><Select value={promoteAxis} onValueChange={(value) => setPromoteAxis(value as typeof promoteAxis)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>
            <SelectItem value="case">ケース</SelectItem>
            <SelectItem value="camera">カメラ</SelectItem>
            <SelectItem value="resultPosition">結果位置</SelectItem>
          </SelectContent></Select></label>
        </div>
        <p className="workflow-trust-note"><ShieldCheck size={13} />軸に選ばなかったものは全メンバーで共有されます。カラーマップと範囲も共有され、隣り合うペインを目で比べられる状態を保ちます。</p>
        <footer><button type="button" onClick={() => onPromoteOpenChange(false)}>キャンセル</button><button type="button" className="primary-button" onClick={() => onPromoteOpenChange(false)}>比較として保存</button></footer>
      </DialogContent></Dialog>}
      {variant === 'probe' && <ProbeReadout />}
      {caseHasResultAxis(selectedCase) && (playbackVisible || variant === 'result-bookmarks') && <ViewPlaybackOverlay axis={axis} caseName={selectedCase} bookmarks={viewItem.bookmarks} onBookmarksChange={(next) => onViewItemChange({ ...viewItem, bookmarks: next })} bookmarksOpen={variant === 'result-bookmarks'} bookmarksUnresolved={variant === 'camera-unresolved'} />}
    </div>
  )
}

type ResultAxisKind = 'time' | 'mode' | 'frequency'

const resultAxes: Record<ResultAxisKind, { discrete: boolean; minimum: number; maximum: number; step: number; storedStep: number; format: (position: number) => string }> = {
  time: { discrete: false, minimum: 0, maximum: 30, step: 0.1, storedStep: 1, format: (position) => `${Math.floor(position / 60)}:${String(Math.floor(position % 60)).padStart(2, '0')}` },
  mode: { discrete: true, minimum: 1, maximum: 7, step: 1, storedStep: 1, format: (position) => `モード ${Math.round(position)}・固有振動数 ［未接続］` },
  frequency: { discrete: false, minimum: 10, maximum: 2000, step: 1, storedStep: 50, format: (position) => `${position.toFixed(1)} Hz・位相 ［保持値未接続］` },
}

// Where a saved position resolves on the axis for the case in scope. Ordering shots by their place in
// the bookmark list would call a correct timeline broken: the threshold crossing is authored after the
// extremum and resolves before it.
function bookmarkAxisPosition(id: string, axis: ResultAxisKind, caseName: string, bookmarks: ResultBookmarkModel[]) {
  const definition = resultAxes[axis]
  if (id === 'first') return definition.minimum
  if (id === 'last') return definition.maximum
  const bookmark = bookmarks.find((entry) => entry.id === id)
  if (!bookmark) return definition.minimum
  return resolveBookmark(bookmark, axis, caseName, false).position
}

function ViewPlaybackOverlay({ axis, caseName, bookmarks, onBookmarksChange, bookmarksOpen = false, bookmarksUnresolved = false }: { axis: ResultAxisKind; caseName: string; bookmarks: ResultBookmarkModel[]; onBookmarksChange: (next: ResultBookmarkModel[]) => void; bookmarksOpen?: boolean; bookmarksUnresolved?: boolean }) {
  const definition = resultAxes[axis]
  const [position, setPosition] = useState(definition.minimum)
  const [hoverPosition, setHoverPosition] = useState<number | null>(null)
  const [panelOpen, setPanelOpen] = useState(bookmarksOpen)
  const [appliedBookmarkId, setAppliedBookmarkId] = useState<string | null>(null)
  const [ruleOpen, setRuleOpen] = useState(false)
  const [ruleName, setRuleName] = useState('')
  const [ruleKind, setRuleKind] = useState<'extremum' | 'crossing' | 'relative'>('extremum')
  const [ruleQuantity, setRuleQuantity] = useState('最大応力')
  const [ruleThreshold, setRuleThreshold] = useState('235 MPa')
  const span = definition.maximum - definition.minimum
  const commit = (value: number) => setPosition(definition.discrete ? Math.round(value) : value)
  const positionFromPointer = (event: React.MouseEvent<HTMLInputElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect()
    const ratio = Math.min(1, Math.max(0, (event.clientX - bounds.left) / bounds.width))
    return definition.minimum + ratio * span
  }
  const percent = ((position - definition.minimum) / span) * 100
  const hoverPercent = hoverPosition === null ? 0 : ((hoverPosition - definition.minimum) / span) * 100
  const step = (direction: -1 | 1) => commit(Math.min(definition.maximum, Math.max(definition.minimum, position + direction * (definition.discrete ? 1 : span / 30))))
  const resolved = bookmarks.map((bookmark) => ({ bookmark, resolution: resolveBookmark(bookmark, axis, caseName, bookmarksUnresolved && bookmark.rule.kind !== 'explicit' && bookmark.rule.kind !== 'relative') }))
  return <div className="view-playback-overlay" role="toolbar" aria-label="ビュー再生コントロール">
    <button aria-label="先頭へ" onClick={() => commit(definition.minimum)}><ChevronsLeft size={13} /></button>
    <button aria-label="前へ" onClick={() => step(-1)}><ChevronLeft size={13} /></button>
    <button className="playback-play" aria-label="再生"><Play size={13} /></button>
    <button aria-label="次へ" onClick={() => step(1)}><ChevronRight size={13} /></button>
    <button aria-label="末尾へ" onClick={() => commit(definition.maximum)}><ChevronsRight size={13} /></button>
    <div className="playback-timeline">
      <input
        type="range"
        min={definition.minimum}
        max={definition.maximum}
        step={definition.step}
        value={position}
        aria-label="結果位置"
        aria-valuetext={definition.format(position)}
        onMouseMove={(event) => setHoverPosition(positionFromPointer(event))}
        onMouseLeave={() => setHoverPosition(null)}
        onClick={(event) => commit(positionFromPointer(event))}
        onChange={(event) => commit(Number(event.target.value))}
      />
      {/* Bookmarks are drawn on the axis they index. A rule that did not resolve has no marker, because
          a marker at position zero would be a plausible default (XC-197). */}
      {resolved.filter((entry) => entry.resolution.state === 'resolved').map((entry) => (
        <span
          className={`playback-bookmark-marker ${appliedBookmarkId === entry.bookmark.id ? 'applied' : ''}`}
          style={{ left: `${((entry.resolution.position - definition.minimum) / span) * 100}%` }}
          title={`${entry.bookmark.name}・${definition.format(entry.resolution.position)}`}
          key={entry.bookmark.id}
          aria-hidden="true"
        />
      ))}
      <span className="playback-current-marker" style={{ left: `${percent}%` }} aria-hidden="true" />
      {hoverPosition !== null && <>
        <span className="playback-hover-marker" style={{ left: `${hoverPercent}%` }} aria-hidden="true" />
        <span className="playback-hover-time" style={{ left: `${hoverPercent}%` }}>{definition.format(definition.discrete ? Math.round(hoverPosition) : hoverPosition)}</span>
      </>}
    </div>
    <em>{definition.format(position)}</em>
    <button className="playback-speed" type="button">1× <ChevronDown size={10} /></button>
    <button type="button" className={panelOpen ? 'playback-bookmark-trigger active' : 'playback-bookmark-trigger'} aria-label="結果軸ブックマーク" aria-expanded={panelOpen} onClick={() => setPanelOpen((open) => !open)}><Bookmark size={13} /></button>
    {panelOpen && <section className="playback-bookmark-panel" aria-label="結果軸ブックマーク">
      <header><b>結果軸ブックマーク</b><small>ケース「{caseName}」で解決した位置</small></header>
      <div>
        {resolved.map(({ bookmark, resolution }) => (
          <article className={resolution.state} key={bookmark.id}>
            <span>
              <b>{bookmark.name}</b>
              <small>{describeBookmarkRule(bookmark)}</small>
              <em>{resolution.state === 'unresolved'
                ? resolution.at
                : `${definition.format(resolution.position)}${resolution.snapped ? '・保存位置へ丸め' : ''}${resolution.at ? `・値 ${resolution.at}` : ''}`}</em>
            </span>
            <button type="button" disabled={resolution.state === 'unresolved'} onClick={() => { commit(resolution.position); setAppliedBookmarkId(bookmark.id) }}>移動</button>
              <button type="button" aria-label={`${bookmark.name}を削除`} className="playback-bookmark-remove" onClick={() => onBookmarksChange(bookmarks.filter((entry) => entry.id !== bookmark.id))}><X size={11} /></button>
          </article>
        ))}
      </div>
      <footer>
        {/* A saved position is made on the axis it indexes: scrub to the moment and keep it, or state
            the rule that finds it. Until now the list was fixed and nothing could add to it, while the
            comparison, the timeline and the output all referenced it (XC-197). */}
        <div className="playback-bookmark-actions">
          <button type="button" onClick={() => onBookmarksChange([...bookmarks, { id: `bm-${bookmarks.length + 1}`, name: `位置 ${definition.format(position)}`, rule: { kind: 'explicit', position } }])}><Plus size={11} />現在位置を保存</button>
          <button type="button" onClick={() => setRuleOpen(true)}><Ruler size={11} />規則で追加</button>
        </div>
        <span><ShieldCheck size={11} />規則は座標ではなく条件を保持し、ケースごとに解決します。存在しない位置へは丸めた事実を明示します。</span>
      </footer>
    </section>}
    {ruleOpen && <Dialog open onOpenChange={setRuleOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog">
      <header><span><small>結果位置</small><b>規則で追加</b></span><button type="button" aria-label="規則の追加を閉じる" onClick={() => setRuleOpen(false)}><X size={15} /></button></header>
      <div className="settings-fields">
        <label><span>名前</span><input value={ruleName} onChange={(event) => setRuleName(event.target.value)} placeholder="例：最大応力時" /></label>
        <label><span>種類</span><Select value={ruleKind} onValueChange={(value) => setRuleKind(value as typeof ruleKind)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>
          <SelectItem value="extremum">数量の極値</SelectItem>
          <SelectItem value="crossing">しきい値の交差</SelectItem>
          <SelectItem value="relative">軸の先頭・末尾</SelectItem>
        </SelectContent></Select></label>
        {ruleKind !== 'relative' && <label><span>数量</span><Select value={ruleQuantity} onValueChange={setRuleQuantity}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="最大応力">最大応力</SelectItem><SelectItem value="変位">変位</SelectItem><SelectItem value="温度">温度</SelectItem></SelectContent></Select></label>}
        {ruleKind === 'crossing' && <label><span>しきい値</span><input value={ruleThreshold} onChange={(event) => setRuleThreshold(event.target.value)} placeholder="例：235 MPa" /></label>}
      </div>
      <p className="workflow-trust-note"><ShieldCheck size={13} />条件だけを保存します。ケースごとに解決し、解決できないときは数量を名指しして位置を動かしません。しきい値は宣言済みの単位で比較します。</p>
      <footer><button type="button" onClick={() => setRuleOpen(false)}>キャンセル</button><button type="button" className="primary-button" disabled={!ruleName.trim() || (ruleKind === 'crossing' && !ruleThreshold.trim())} onClick={() => {
        const rule: ResultBookmarkModel['rule'] = ruleKind === 'extremum'
          ? { kind: 'extremum', quantity: ruleQuantity, statistic: '最大' }
          : ruleKind === 'crossing'
            ? { kind: 'crossing', quantity: ruleQuantity, threshold: ruleThreshold.trim(), direction: '上昇' }
            : { kind: 'relative', of: '末尾' }
        onBookmarksChange([...bookmarks, { id: `bm-${bookmarks.length + 1}`, name: ruleName.trim(), rule }])
        setRuleName('')
        setRuleOpen(false)
      }}>追加</button></footer>
    </DialogContent></Dialog>}
  </div>
}

function GraphScreen({ variant }: { variant: string }) {
  if (variant === 'empty') return <div className="entry-grid"><button><SlidersHorizontal /><b>手動</b><span>物理量とケースを明示的に選択</span></button><button><Sparkles /><b>推奨</b><span>プレビューのみ・自動適用しない</span></button><button><MessageSquareText /><b>アシスタント提案</b><span>安全なグラフ定義・適用待ち</span></button></div>
  if (variant === 'no-points') return <div className="centred-state error-state"><AlertTriangle size={34} /><h2>選択条件に一致する点がありません</h2><p>条件「選択領域かつフィールドあり」によって選択が空になりました。空グラフは描画していません。</p><button>選択条件を編集</button></div>
  return <div className="graph-canvas"><div className="graph-heading"><div><span className="eyebrow">グラフ</span><h2>物理量の比較</h2><p>ケース：明示選択・集約方法：未選択</p></div></div><div className="chart-frame"><span className="y-label">物理量A［単位未宣言］</span><div className="chart-grid"><svg viewBox="0 0 600 260" role="img" aria-label="値を含まないグラフ構成モック"><polyline points="40,205 180,150 320,170 460,92 560,110" /><circle cx="40" cy="205" r="5" /><circle cx="180" cy="150" r="5" /><circle cx="320" cy="170" r="5" /><circle cx="460" cy="92" r="5" /><circle cx="560" cy="110" r="5" /></svg><span className="mock-stamp">レイアウトのみ・解析値なし</span></div><span className="x-label">ケース選択</span></div><div className="provenance-row"><span>物理量：データセット</span><span>単位：未宣言</span><span>欠損ケース：データなしとして表示</span></div></div>
}

// `report.commentary-review`: the generated passages with their statement kind and source, and the
// omissions the standard produced. XC-104 makes omission a correct outcome and requires it recorded,
// so a review that showed only the surviving sentences would hide the part a reader must check.
function ReportCommentaryReview() {
  const passages: { kind: StatementKind; source: string; text: string }[] = [
    { kind: 'value', source: 'データセット・最大応力', text: '最大応力は［値・単位未宣言］でした。単位を宣言するまで換算は行いません。' },
    { kind: 'comparison', source: '計算・安全率 = 設計許容応力 / 最大応力', text: '安全率は設計許容応力との比として算出しています。' },
    { kind: 'citation', source: '参考資料・設計ノート', text: '設計許容応力 235 MPa は設計ノートの記載です。数値根拠としては使用していません。' },
    { kind: 'user', source: '利用者の記述・コメント方向', text: '板厚変更ケースの傾向を中心に述べる、という方針を与えられています。' },
  ]
  const omissions = [
    { text: '「十分に安全な設計である」', reason: '主観的表現。1回書き直したうえで基準を満たさず、除外しました。' },
    { text: '「応力は大幅に低下した」', reason: '定量化されていない比較。数値と単位を伴う記述に置き換えられませんでした。' },
  ]
  return (
    <section className="commentary-review" aria-label="生成コメントの確認">
      <header><span className="eyebrow">生成コメント</span><h2>公開前の確認</h2><p>生成後に書式基準へ照合した結果です。基準を満たさない文は書き直しを1回試み、それでも満たさなければ除外し、除外そのものを記録します。</p></header>
      <ol className="commentary-passages">
        {passages.map((passage) => (
          <li key={passage.text}>
            <StatementKindBadge kind={passage.kind} source={passage.source} />
            <p>{passage.text}</p>
          </li>
        ))}
      </ol>
      <section className="commentary-omissions" aria-label="除外した記述">
        <b>除外した記述 {omissions.length}件</b>
        <ul>{omissions.map((omission) => <li key={omission.text}><AlertTriangle size={11} /><span><b>{omission.text}</b><small>{omission.reason}</small></span></li>)}</ul>
      </section>
      <footer className="workflow-trust-note"><ShieldCheck size={13} />確認して取り込むまで、生成文はレポートに入りません。外部モデルへの送信は権限と送信内容の確認を経てのみ行います。</footer>
    </section>
  )
}

function ReportScreen({ variant }: { variant: string }) {
  if (variant === 'commentary-review') return <div className="report-canvas"><ReportCommentaryReview /></div>
  if (variant === 'blank') return <div className="report-choices"><h2>レポートを作成</h2><p>テンプレートを選ぶか、意図的に空文書から始めます。</p><div>{['学術論文', '技術メモ', '1ページ要約', '設計レビューデッキ', 'ケース間比較', '空文書'].map((item) => <button key={item}><FileText /><b>{item}</b><small>サンプル</small></button>)}</div></div>
  const state = variant === 'exporting' ? <StatePanel tone="progress" title="自己完結HTMLを出力中" detail="同じ対象への二重出力は停止されています。キャンセルは引き続き利用できます。" /> : variant === 'export-error' ? <StatePanel tone="error" title="HTML出力を利用できません" detail="出力先フォルダーは読取専用です。前回の成果物は上書きされていません。" /> : null
  return <div className="report-canvas">{state}<article className="report-page"><span className="eyebrow">設計レビュー・モックアップ</span><h1>解析レポート表題</h1><p className="lede">このプレビューはレイアウト用の仮要素のみを含み、解析結果について何も主張しません。</p><section><div className="report-image"><Boxes /><span>ビュー・結果値なし</span></div><div><h2>判明事項</h2><p>利用可能な場合、データセットの来歴、宣言単位、アルゴリズムを表示します。</p><h2>未判明事項</h2><p>欠損値は欠損のまま維持し、明示します。</p></div></section><footer>入力識別情報・ワークスペース版・アルゴリズム版</footer></article>{variant === 'exporting' && <button className="floating-cancel"><X size={14} /> 出力をキャンセル</button>}</div>
}

function ChatScreen({ variant, draft, onDraftChange, settings, onSettingsChange }: { variant: string; draft: string; onDraftChange: (draft: string) => void; settings: ConversationSettings; onSettingsChange: (settings: ConversationSettings) => void }) {
  const [outboundOpen, setOutboundOpen] = useState(variant === 'outbound-request')
  const [outboundOutcome, setOutboundOutcome] = useState<'pending' | 'kept-offline' | 'allowed-once'>('pending')
  if (variant === 'empty') {
    return (
      <div className="chat-canvas">
        <div className="chat-empty">
          <MessageSquareText size={30} />
          <h2>ワークスペースについて尋ねる</h2>
          <p>質問、操作、レポート構成を同じチャットで続けられます。</p>
          <div className="chat-suggestions">
            {['利用可能な物理量を一覧にする', 'このテンプレートの未解決項目を確認する', 'パイプラインをドライランする'].map((item) => <button key={item} type="button" onClick={() => onDraftChange(item)}>{item}<ChevronRight size={13} /></button>)}
          </div>
        </div>
        <ChatComposer draft={draft} onDraftChange={onDraftChange} settings={settings} onSettingsChange={onSettingsChange} />
      </div>
    )
  }

  return (
    <div className="chat-canvas">
      <ConversationThread variant={variant} />
      {variant === 'outbound-request' && outboundOutcome !== 'pending' && <div className="chat-outbound-outcome" role="status">{outboundOutcome === 'kept-offline'
        ? <><ShieldCheck size={13} /><span><b>オフラインを維持しました</b><small>検索語は送信していません。ワークスペースは変更されていません。</small></span></>
        : <><Globe2 size={13} /><span><b>今回だけ許可しました</b><small>表示した検索語のみを送信し、ホスト・日時・判断をローカル監査へ記録します。</small></span></>}
        <button type="button" onClick={() => setOutboundOpen(true)}>要求内容を再表示</button>
      </div>}
      <ChatComposer draft={draft} onDraftChange={onDraftChange} settings={settings} onSettingsChange={onSettingsChange} />
      {variant === 'outbound-request' && <ModalCard open={outboundOpen} onClose={() => setOutboundOpen(false)} title="外部要求を1回許可しますか？" detail="検索語：「公式ソルバー形式文書」。送信しない情報：ファイル名、形状、値、ワークスペース情報。"><button type="button" onClick={() => { setOutboundOutcome('kept-offline'); setOutboundOpen(false) }}>オフラインを維持</button><button type="button" className="primary-button" onClick={() => { setOutboundOutcome('allowed-once'); setOutboundOpen(false) }}>今回だけ許可</button></ModalCard>}
    </div>
  )
}

function ConversationThread({ variant, compact = false }: { variant?: string; compact?: boolean }) {
  return (
    <div className={`chat-thread ${compact ? 'assistant-drawer-thread' : ''}`}>
      <div className="chat-thread-inner">
        <article className="chat-turn chat-turn-user">
          <header><span className="chat-role-mark">あ</span><b>あなた</b></header>
          <div className="chat-turn-body"><p>このワークスペースで利用可能な物理量を説明して</p></div>
        </article>
        <article className="chat-turn chat-turn-assistant">
          <header><span className="chat-role-mark"><MessageSquareText size={14} /></span><b>SOLVIA</b><small>ローカルモデル</small></header>
          <div className="chat-turn-body">
            {/* XC-104: a generated statement says which of the four kinds it is and where it came from.
                Chat is named alongside Report in the shared-components table; it carried no badge. */}
            <p><StatementKindBadge kind="user" source="利用者の質問・現在のワークスペース" />物理量一覧は、読み込んだデータセットから取得してここに表示します。値や単位は、実データで確認できるまで推測しません。</p>
            <p><StatementKindBadge kind="citation" source="製品仕様・読み取り時の項目" />読み込み後は、物理量名、種類、宣言単位、欠損の有無、来歴を順に確認できます。</p>
            <aside className="chat-safety-note"><ShieldCheck size={14} /><span><b>操作は行っていません</b><small>ワークスペースは変更されていません。</small></span></aside>
            <footer className="chat-response-actions"><button><Save size={13} /> コピー</button><button><RefreshCw size={13} /> 再生成</button></footer>
          </div>
        </article>
        {variant === 'assistant-error' && <StatePanel tone="error" title="コマンド送信前にアシスタントが失敗しました" detail="コマンドは実行されず、ワークスペースは変更されていません。ローカルモデルを利用できませんでした。" />}
      </div>
    </div>
  )
}

function AssistantDrawer({ draft, onDraftChange, onClose, onOpenChat, settings, onSettingsChange }: { draft: string; onDraftChange: (draft: string) => void; onClose: () => void; onOpenChat: () => void; settings: ConversationSettings; onSettingsChange: (settings: ConversationSettings) => void }) {
  return (
    <aside className="assistant-drawer" aria-label="アシスタントチャット">
      <header className="assistant-drawer-header">
        <div><span className="assistant-mark"><MessageSquareText size={14} /></span><span><b>アシスタント</b><small>現在のチャット</small></span></div>
        <div>
          <button type="button" className="assistant-open-chat" onClick={onOpenChat}>チャットで開く<ArrowUpRight size={13} /></button>
          <button type="button" aria-label="アシスタントを閉じる" onClick={onClose}><X size={15} /></button>
        </div>
      </header>
      <ConversationThread compact />
      <ChatComposer draft={draft} onDraftChange={onDraftChange} settings={settings} onSettingsChange={onSettingsChange} compact />
    </aside>
  )
}

// XC-150: the instruction bar and Chat are two presentations of one conversation, so switching between
// them preserves the draft *and the conversation settings*. Holding model, effort and search
// permission inside this component made each surface its own conversation the moment it unmounted.
type ConversationSettings = { model: string; effort: string; search: 'off' | 'allowed' }

function ChatComposer({ draft, onDraftChange, settings, onSettingsChange, compact }: { draft: string; onDraftChange: (draft: string) => void; settings: ConversationSettings; onSettingsChange: (settings: ConversationSettings) => void; compact?: boolean }) {
  const [permission, setPermission] = useState<'search' | 'research' | null>(null)
  const [host, setHost] = useState('')
  // XC-106: the query is the data that leaves. Nothing is sent until both the exact query and the host
  // that will receive it are on screen; deep research additionally has no request count or cost yet.
  const outboundBlockedReason = !draft.trim()
    ? '送信する検索語がありません。入力欄に問い合わせを書いてください。'
    : !host.trim()
      ? 'このワークスペースで許可するホストが未登録です。'
      : '要求数と費用見積を取得できるまで詳細調査は送信しません。'
  const outboundBlocked = !draft.trim() || !host.trim() || permission === 'research'
  // XC-207: the drawer is roughly half the width of the Chat area, so the two permission buttons drop
  // their labels there and keep them in their accessible name. Nothing is removed - a control that is
  // only an icon still says what it is to a screen reader and on hover.
  const searchLabel = settings.search === 'allowed' ? '検索オン' : '検索オフ'
  return <div className={`chat-composer ${compact ? 'compact-composer' : ''}`}><textarea rows={2} value={draft} onChange={(event) => onDraftChange(event.target.value)} placeholder="ワークスペースへの質問または操作" /><div><button className="chat-icon-button" aria-label="ファイルを追加" title="ファイルを追加"><Plus size={16} /></button><label className="chat-inline-select"><span className="sr-only">モデル</span><select value={settings.model} onChange={(event) => onSettingsChange({ ...settings, model: event.target.value })}><option value="local">ローカルモデル</option><option value="remote" disabled>外部モデル・未構成</option></select></label><label className="chat-inline-select"><span className="sr-only">推論の深さ</span><select value={settings.effort} onChange={(event) => onSettingsChange({ ...settings, effort: event.target.value })}><option value="brief">簡潔</option><option value="standard">標準</option><option value="deep">詳細</option></select></label><button type="button" className={`chat-search-status ${compact ? 'chat-icon-button' : ''}`} aria-pressed={settings.search === 'allowed'} aria-label={searchLabel} title={searchLabel} onClick={() => setPermission('search')}><ShieldCheck size={compact ? 13 : 11} />{!compact && searchLabel}</button><button type="button" className={`chat-research-button ${compact ? 'chat-icon-button' : ''}`} aria-label="詳細調査" title="詳細調査" onClick={() => setPermission('research')}>{compact ? <Telescope size={13} /> : '詳細調査'}</button><button className="chat-send chat-icon-button" aria-label="送信" title="送信" disabled={!draft.trim()}><Play size={14} /></button></div><small>回答は誤る可能性があります。解析値・単位・来歴は元データで確認してください。</small>
    <Dialog open={permission !== null} onOpenChange={(open) => !open && setPermission(null)}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog outbound-review-dialog"><header><span><small>外部通信</small><b>{permission === 'research' ? '詳細調査の許可' : 'Web検索の許可'}</b></span><button type="button" aria-label="外部通信確認を閉じる" onClick={() => setPermission(null)}><X size={15} /></button></header><section className="outbound-review"><label><span>送信する検索語</span><textarea rows={2} value={draft.trim() || '［検索語を入力してください］'} readOnly /></label><label><span>送信しない情報</span><input value="ケース名・ファイルパス・形状・解析値" readOnly /></label><label><span>許可ホスト</span><Input value={host} onChange={(event) => setHost(event.target.value)} placeholder="例：docs.example.org" aria-label="このワークスペースで許可するホスト" /></label>{permission === 'research' && <><label><span>予定要求数</span><input value="未取得" readOnly /></label><label><span>費用見積</span><input value="未取得" readOnly /></label></>}</section><p className={outboundBlocked ? 'workflow-trust-note blocked' : 'workflow-trust-note'}>{outboundBlocked ? <AlertTriangle size={13} /> : <ShieldCheck size={13} />}{outboundBlocked ? outboundBlockedReason : '表示した検索語だけを、指定したホストへ1回だけ送信します。ホスト・日時・判断はローカル監査に記録されます。'}</p><footer><button type="button" onClick={() => { onSettingsChange({ ...settings, search: 'off' }); setPermission(null) }}>オフラインを維持</button><button type="button" className="primary-button" disabled={outboundBlocked} onClick={() => { onSettingsChange({ ...settings, search: 'allowed' }); setPermission(null) }}>今回だけ許可</button></footer></DialogContent></Dialog>
  </div>
}

function ShortcutSettings() {
  const [query, setQuery] = useState('')
  const needle = query.trim()
  const groups = shortcutGroups
    .map((group) => ({ ...group, commands: group.commands.filter((command) => command.name.includes(needle)) }))
    .filter((group) => group.commands.length > 0)
  return (
    <>
      <h2>コマンドとキー</h2>
      <p>同じ操作はどのモードでも同じキーです。モードが変わるのは対象ではなく道具です。</p>
      <div className="settings-fields">
        <label>コマンドを検索<Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="コマンド名" /></label>
      </div>
      {groups.length === 0 ? (
        <div className="setting-note"><Search size={15} />「{needle}」に一致するコマンドはありません。</div>
      ) : (
        groups.map((group) => (
          <section className="shortcut-group" key={group.group}>
            <header><b>{group.group}</b><small>{group.note}</small></header>
            <ul>
              {group.commands.map((command) => (
                <li className={command.key === null ? 'no-shortcut' : undefined} key={command.name}>
                  <span>{command.name}</span>
                  {command.key === null
                    ? <em className="shortcut-refused">キーなし<small>{command.reason}</small></em>
                    : <kbd>{command.key}</kbd>}
                </li>
              ))}
            </ul>
          </section>
        ))
      )}
      <div className="setting-note"><ShieldCheck size={15} />正確なキーはプラットフォームの慣習に従います。この一覧が固定するのは、何にショートカットがあり、何に与えてはならないかです。</div>
    </>
  )
}

function SettingsScreen({ variant }: { variant: string }) {
  const applicationCategories = ['全般', '表示とアクセシビリティ', 'ショートカット', '単位', 'ネットワーク', '更新', '診断とサポート']
  const workspaceCategories = ['ワークスペース', '成分座標系', 'レンダラー', 'アートスタイル', 'アシスタント', 'ライブラリ']
  const [category, setCategory] = useState(variant === 'support-bundle' ? '診断とサポート' : variant === 'shortcuts' ? 'ショートカット' : '単位')
  const [supportOpen, setSupportOpen] = useState(variant === 'support-bundle')

  return (
    <div className="settings-canvas">
      <aside className="settings-nav" aria-label="設定カテゴリ">
        <header className="settings-nav-header">
          <span className="settings-nav-icon"><Settings size={16} /></span>
          <span><b>設定</b><small>アプリと作業環境</small></span>
        </header>
        <nav className="settings-nav-group" aria-label="アプリ全体の設定">
          <small>アプリ全体</small>
          {applicationCategories.map((item) => <button className={item === category ? 'active' : ''} onClick={() => setCategory(item)} key={item}>{item}</button>)}
        </nav>
        <nav className="settings-nav-group" aria-label="ワークスペースの設定">
          <small>現在のワークスペース</small>
          {workspaceCategories.map((item) => <button className={item === category ? 'active' : ''} onClick={() => setCategory(item)} key={item}>{item}</button>)}
        </nav>
      </aside>
      <section className="settings-form">
        <span className="settings-scope">{applicationCategories.includes(category) ? 'アプリ全体' : '現在のワークスペース'}</span>
        <span className="eyebrow">{category}</span>
        <SettingsCategoryPanel category={category} invalid={variant === 'invalid'} onSupportBundle={() => setSupportOpen(true)} />
      </section>
      <Dialog open={supportOpen} onOpenChange={setSupportOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog support-bundle-dialog"><header><span><small>診断とサポート</small><b>サポートバンドルの内容を確認</b></span><button type="button" aria-label="サポートバンドルを閉じる" onClick={() => setSupportOpen(false)}><X size={15} /></button></header><section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>含める</b><small>ローカルログ、製品版、設定、失敗理由コード</small></span></p><p><AlertTriangle size={13} /><span><b>確認が必要</b><small>ケース名と入力ファイルのパス</small></span></p><p><ShieldCheck size={13} /><span><b>含めない</b><small>形状、フィールド値、測定値、参考資料の本文</small></span></p></section><p className="workflow-trust-note"><HardDrive size={13} />作成先はローカルです。送信は別操作で、送信先と内容を再確認します。</p><footer><button type="button" onClick={() => setSupportOpen(false)}>キャンセル</button><button type="button" className="primary-button" onClick={() => setSupportOpen(false)}>ローカルに作成</button></footer></DialogContent></Dialog>
    </div>
  )
}

// `settings.invalid`: "invalid setting rejected at entry, previous value kept". The panel showed a
// banner at the top of the page while the field itself offered only valid options, so the rejection
// was described somewhere other than where it happened and no previous value was visible.
const declarableUnits = ['MPa', 'kPa', 'Pa', 'N/mm^2']

function UnitSettings({ invalid }: { invalid: boolean }) {
  const [displayUnit, setDisplayUnit] = useState(invalid ? 'unknown-unit' : 'MPa')
  const [acceptedUnit, setAcceptedUnit] = useState('MPa')
  const valid = declarableUnits.includes(displayUnit.trim())
  return <>
    <h2>宣言単位と表示単位</h2>
    <p>ファイル内容を信頼できる単位宣言として扱うことはありません。</p>
    <div className="settings-fields">
      <label>物理量の種類<Select defaultValue="stress"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="stress">応力</SelectItem></SelectContent></Select></label>
      <label>宣言単位<Select defaultValue="undeclared"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="undeclared">未宣言</SelectItem>{declarableUnits.map((unit) => <SelectItem value={unit} key={unit}>{unit}</SelectItem>)}</SelectContent></Select></label>
      <label>表示単位<Input value={displayUnit} aria-invalid={!valid} aria-describedby="display-unit-status" onChange={(event) => setDisplayUnit(event.target.value)} /></label>
    </div>
    {valid
      ? <div className="setting-note" id="display-unit-status"><ShieldCheck size={15} />表示単位「{displayUnit}」は宣言単位と次元が一致します。</div>
      : <div className="setting-note setting-note-rejected" id="display-unit-status" role="alert"><AlertTriangle size={15} /><span><b>表示単位「{displayUnit}」を拒否しました</b><small>この単位は宣言済みの単位系にありません。直前の値「{acceptedUnit}」を維持しています。</small></span></div>}
    <div className="setting-note"><ShieldCheck size={15} />単位を宣言するまで変換は無効です。</div>
    <div className="setting-note"><ShieldCheck size={15} />大きさ、フィールド名、書き出したソルバーのいずれからも、ファイルから単位を推測しません。</div>
    <Button className="primary-button" disabled={!valid} onClick={() => setAcceptedUnit(displayUnit.trim())}>設定を保存</Button>
  </>
}

function SettingsCategoryPanel({ category, invalid, onSupportBundle }: { category: string; invalid: boolean; onSupportBundle: () => void }) {
  if (category === '単位') return <UnitSettings invalid={invalid} />
  if (category === 'ショートカット') return <ShortcutSettings />
  if (category === 'ネットワーク') return <><h2>既定でオフライン</h2><p>ワークスペースごとの許可がない通信は試行しません。</p><div className="settings-fields"><label>外部通信<Select defaultValue="off"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="off">拒否</SelectItem></SelectContent></Select></label><label>検索確認<Select defaultValue="each"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="each">要求ごとに確認</SelectItem></SelectContent></Select></label><label>許可ホスト<Input value="登録なし" readOnly /></label></div><div className="setting-note"><ShieldCheck size={15} />ケース名、値、ファイルパスを含む要求は個別確認します。</div></>
  if (category === '診断とサポート') return <><h2>ローカル診断</h2><p>ログにはフィールド値を含めません。バンドル作成前に収録内容を確認できます。</p><div className="settings-action-list"><button type="button" onClick={onSupportBundle}><FolderPlus size={16} /><span><b>サポートバンドルを作成</b><small>内容を確認してローカルに保存</small></span><ChevronRight size={14} /></button><button type="button"><ScrollText size={16} /><span><b>ローカルログを開く</b><small>外部送信なし</small></span><ChevronRight size={14} /></button></div></>
  if (category === '更新') return <><h2>更新とロールバック</h2><p>更新は署名と互換性を確認し、失敗時は直前の版を保持します。</p><div className="settings-fields"><label>更新確認<Select defaultValue="manual"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="manual">手動・ネットワーク未使用</SelectItem></SelectContent></Select></label><label>現在の状態<Input value="更新情報未取得" readOnly /></label></div><div className="setting-note"><ShieldCheck size={15} />許可なく更新サーバーへ接続しません。</div></>
  if (category === '表示とアクセシビリティ') return <><h2>表示と操作</h2><p>ツールのテーマは成果物のアートスタイルとは独立しています。</p><div className="settings-fields"><label>テーマ<Select defaultValue="system"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="system">システム設定</SelectItem><SelectItem value="light">ライト</SelectItem><SelectItem value="dark">ダーク</SelectItem></SelectContent></Select></label><label>コントラスト<Select defaultValue="standard"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="standard">標準</SelectItem><SelectItem value="high">高コントラスト</SelectItem></SelectContent></Select></label><label>キーボード<Input value="すべてのコマンドに経路あり" readOnly /></label></div><div className="setting-note"><AlertTriangle size={15} />スクリーンリーダー完全対応はr1の保証範囲外です。</div></>
  if (category === 'アシスタント') return <><h2>アシスタント</h2><p>モデルを構成しなくても、画面とコマンド面の全操作を利用できます。</p><div className="settings-fields"><label>モデル<Select defaultValue="local"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="local">ローカルモデル</SelectItem></SelectContent></Select></label><label>外部モデル<Input value="未構成" readOnly /></label><label>生成コメント<Input value="利用不可・送信なし" readOnly /></label></div></>
  if (category === 'レンダラー') return <><h2>レンダラー</h2><p>機能を exact / baked / unsupported として判定し、暗黙の近似は行いません。</p><div className="settings-fields"><label>ローカル3D<Input value="VTK・利用可能" readOnly /></label><label>Web<Input value="vtk.js・利用可能" readOnly /></label><label>フォトリアル<Input value="Omniverse・未接続" readOnly /></label></div></>
  if (category === '成分座標系') return <><h2>成分座標系</h2><p>表示座標と成分座標を区別し、解決できないフレームの変換を拒否します。</p><div className="settings-fields"><label>既定<Select defaultValue="global"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="global">グローバル</SelectItem></SelectContent></Select></label><label>状態<Input value="宣言済みフレームのみ" readOnly /></label></div></>
  if (category === 'ライブラリ') return <><h2>ライブラリ</h2><p>ワークスペース内と共有のリソースを区別し、コピーで移動します。</p><div className="settings-fields"><label>既定の保存先<Select defaultValue="workspace"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="workspace">このワークスペース</SelectItem><SelectItem value="shared">共有</SelectItem></SelectContent></Select></label><label>オフライン解決<Input value="パッケージ内のみ" readOnly /></label></div></>
  if (category === 'アートスタイル') return <><h2>アートスタイル</h2><p>フォント、カラーマップ、図表表現だけを管理し、値を変更しません。</p><div className="settings-fields"><label>既定<Select defaultValue="technical"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="technical">技術資料・標準</SelectItem></SelectContent></Select></label></div></>
  if (category === 'ワークスペース') return <><h2>ワークスペース</h2><p>ジャーナル、ロック、出力容量と復元状態を管理します。</p><div className="settings-fields"><label>排他状態<Input value="このプロセスが編集ロックを保持" readOnly /></label><label>自動復元<Input value="ローカルジャーナル有効" readOnly /></label><label>出力容量<Input value="計測後に表示" readOnly /></label></div></>
  return <><h2>全般</h2><p>言語、起動、保存の基本動作を設定します。</p><div className="settings-fields"><label>言語<Select defaultValue="ja"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="ja">日本語</SelectItem><SelectItem value="en">English</SelectItem></SelectContent></Select></label><label>起動<Select defaultValue="resume"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="resume">前回のワークスペースを再開</SelectItem></SelectContent></Select></label></div></>
}

// One audit list, read by both the centre and the right rail. They used to hold separate copies: the
// centre listed two records while the rail's audit panel said there were none, on the same screen.
type AuditResult = 'not-sent' | 'local' | 'refused' | 'allowed'
const auditResultLabels: Record<AuditResult, string> = { 'not-sent': '未送信', local: 'ローカル', refused: '拒否', allowed: '許可' }

const networkAuditRows: { result: AuditResult; title: string; detail: string; variant?: string }[] = [
  { result: 'not-sent', title: '文書検索', detail: '権限なし・端末外へ送信した情報なし' },
  { result: 'local', title: 'アシスタント評価', detail: 'ネットワーク依存なし' },
  { result: 'refused', title: '文書検索・example.invalid', detail: '許可ホストに未登録・要求は送信していません', variant: 'refused' },
]

function auditRowsFor(variant: string) {
  return networkAuditRows.filter((row) => !row.variant || row.variant === variant)
}

function NetworkScreen({ variant, onSettings }: { variant: string; onSettings: () => void }) {
  const [resultFilter, setResultFilter] = useState<'all' | AuditResult>('all')
  if (variant === 'offline') return <div className="centred-state"><ShieldCheck size={35} /><h2>ネットワークアクセスはオフです</h2><p>検索とリモートアシスタント要求は実行しません。要求ごとの許可は設定画面で付与できます。</p><button onClick={onSettings}>権限設定を開く</button></div>
  const rows = auditRowsFor(variant).filter((row) => resultFilter === 'all' || row.result === resultFilter)
  return <div className="network-canvas">
    {variant === 'refused' && <StatePanel tone="error" title="外部要求を拒否しました" detail="ホスト：example.invalid・要求：文書検索・結果：未送信。" />}
    <div className="network-summary"><div><Network /><span><small>既定</small><b>オフライン</b></span></div><div><Globe2 /><span><small>許可ホスト</small><b>なし</b></span></div><div><HardDrive /><span><small>監査保存先</small><b>ローカル</b></span></div></div>
    <section className="audit-log">
      <header>
        <div><span className="eyebrow">ローカル監査</span><h2>外部要求</h2></div>
        <div className="audit-log-tools">
          <label className="sr-only" htmlFor="audit-result-filter">結果で絞り込み</label>
          <select id="audit-result-filter" value={resultFilter} onChange={(event) => setResultFilter(event.target.value as 'all' | AuditResult)}>
            <option value="all">すべて</option>
            {(Object.keys(auditResultLabels) as AuditResult[]).map((result) => <option value={result} key={result}>{auditResultLabels[result]}</option>)}
          </select>
          <button type="button">監査記録を出力</button>
        </div>
      </header>
      {rows.map((row) => <div className="audit-row" key={row.title}><span>{auditResultLabels[row.result]}</span><b>{row.title}</b><small>{row.detail}</small></div>)}
      {rows.length === 0 && <div className="audit-row"><span>—</span><b>該当する記録はありません</b><small>絞り込みを変更してください</small></div>}
    </section>
  </div>
}

function InstructionBar({ draft, onDraftChange, onOpen }: { draft: string; onDraftChange: (draft: string) => void; onOpen: () => void }) {
  return <div className="instruction-bar"><MessageSquareText size={15} /><Input className="h-auto border-0 bg-transparent p-0 type-body shadow-none focus-visible:ring-0" value={draft} onChange={(event) => onDraftChange(event.target.value)} placeholder="自然言語で操作 — 同じチャットへ送信" /><kbd>{shortcutFor('指示バーへフォーカス')?.key}</kbd><Button variant="ghost" size="icon" type="button" aria-label="チャットを開く" onClick={onOpen}><MessageSquareText size={14} /></Button></div>
}

function StatePanel({ tone, title, detail }: { tone: 'info' | 'progress' | 'warning' | 'error'; title: string; detail: string }) {
  const Icon = tone === 'error' || tone === 'warning' ? AlertTriangle : tone === 'progress' ? CircleDashed : ShieldCheck
  return <div className={`state-panel ${tone}`}><Icon size={17} /><div><b>{title}</b><span>{detail}</span></div></div>
}

// A required screen state that renders nothing is a state nobody can review. This dialog was
// uncontrolled and carried no `open`, so Radix kept it shut: `chat.outbound-request` and
// `pipeline.scope-confirmation` showed an empty canvas while the catalogue reported them covered.
// The open state belongs to the caller, which is also the thing that knows how the state is left.
function ModalCard({ title, detail, open, onClose, children }: { title: string; detail: string; open: boolean; onClose: () => void; children: React.ReactNode }) {
  return <Dialog open={open} onOpenChange={(next) => { if (!next) onClose() }}><DialogOverlay className="modal-backdrop" /><DialogContent className="modal-card"><AlertTriangle size={24} /><h2>{title}</h2><p>{detail}</p><DialogFooter>{children}</DialogFooter></DialogContent></Dialog>
}

function ScenarioCatalog({ selected, onSelect }: { selected: Scenario; onSelect: (scenario: Scenario) => void }) {
  return <aside className="scenario-catalog"><header><div><span className="eyebrow">仕様優先</span><h2>画面バリエーション</h2></div><span>{scenarios.length}</span></header><div className="scenario-current"><b>{selected.label}</b><p>{selected.intent}</p><code>{selected.id}</code></div><nav>{screenOrder.map((screen) => <section key={screen}><h3>{screenNames[screen]}<span>{scenarios.filter((item) => item.screen === screen).length}</span></h3>{scenarios.filter((item) => item.screen === screen).map((scenario) => <button className={selected.id === scenario.id ? 'active' : ''} onClick={() => onSelect(scenario)} key={scenario.id}><span>{scenario.label}</span><ChevronRight size={12} /></button>)}</section>)}</nav></aside>
}
