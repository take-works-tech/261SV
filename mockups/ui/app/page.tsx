'use client'

import { Fragment, Suspense, useState } from 'react'
import Image from 'next/image'
import { useRouter, useSearchParams } from 'next/navigation'
import { Viewport } from '@/components/workspace/viewport'
import { MaterialPreview } from '@/components/workspace/material-preview'
import { MaterialSphereIcon } from '@/components/icons/material-sphere-icon'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogFooter, DialogOverlay } from '@/components/ui/dialog'
import { Popover, PopoverContent } from '@/components/ui/popover'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import {
  AlertTriangle,
  CheckCircle2,
  ArrowUpRight,
  ArrowUpDown,
  BarChart3,
  Boxes,
  ChartNoAxesCombined,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ChevronUp,
  CircleDashed,
  Clock3,
  Copy,
  Cpu,
  FileOutput,
  FileText,
  FolderOpen,
  FolderPlus,
  Gauge,
  Globe2,
  Grid2X2,
  HardDrive,
  HelpCircle,
  Eye,
  EyeOff,
  Image as ImageIcon,
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
    { id: 'overall', label: '全体', description: '現在のビュー全体に関わる表示と操作を設定します。', icon: LayoutTemplate, scope: 'view' },
    { id: 'rendering', label: '描画', description: '表示方式とレンダリング品質を調整します。', icon: MonitorCog, scope: 'view' },
    { id: 'background', label: '背景', description: 'ビューの背景と周辺表現を設定します。', icon: ImageIcon, scope: 'view' },
    { id: 'output', label: '出力', description: '画像と動画の作成条件を設定します。', icon: FileOutput, scope: 'view' },
    { id: 'objects', label: 'オブジェクト', description: '選択中の表示オブジェクトを設定します。', icon: Shapes, scope: 'selection' },
    { id: 'text', label: 'テキスト', description: '選択中のテキスト・注釈の内容と文字表現を設定します。', icon: Type, scope: 'selection' },
    { id: 'materials', label: 'マテリアル', description: '選択中の形状と結果表示に使う外観を設定します。', icon: MaterialSphereIcon, scope: 'selection' },
  ],
  graph: [
    { id: 'overall', label: '全体', description: '現在のグラフ全体に関わる表示と操作を設定します。', icon: LayoutTemplate },
    { id: 'kind', label: '種類', description: 'データに合うグラフ形式を選択します。', icon: ChartNoAxesCombined },
    { id: 'style', label: 'スタイル', description: '線、マーカー、配色の表現を調整します。', icon: Paintbrush },
    { id: 'fonts', label: 'テキスト', description: 'タイトル、軸、凡例、注釈の文字表現を設定します。', icon: Type },
    { id: 'detail', label: '詳細', description: 'ケース、変数、参照情報などの詳細を設定します。', icon: SlidersHorizontal },
    { id: 'output', label: '出力', description: '画像、ベクター形式、表データの出力条件を設定します。', icon: FileOutput },
  ],
  report: [
    { id: 'overall', label: '全体', description: '現在のレポート全体に関わる表示と操作を設定します。', icon: LayoutTemplate },
    { id: 'layout', label: 'レイアウト', description: 'ページとコンテンツの配置を整えます。', icon: LayoutGrid },
    { id: 'style', label: 'スタイル', description: '文書全体の視覚表現を調整します。', icon: Paintbrush },
    { id: 'fonts', label: 'テキスト', description: '見出し、本文、注記の文字表現を設定します。', icon: Type },
    { id: 'detail', label: '詳細', description: '参照ケースと収録内容の詳細を設定します。', icon: SlidersHorizontal },
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

const topMenus = ['ファイル', '編集', '表示', 'フィルタ', 'ツール', 'ヘルプ']

function scenarioFor(screen: ScreenId, variant?: string) {
  return (
    scenarios.find((scenario) => scenario.screen === screen && scenario.variant === variant) ??
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
  const screen = (params.get('screen') as ScreenId | null) ?? 'home'
  const variant = params.get('variant') ?? 'default'
  const selected = scenarioFor(screenNames[screen] ? screen : 'home', variant)
  const navigate = (scenario: Scenario) => router.replace(scenario.href, { scroll: false })
  const navigateScreen = (nextScreen: ScreenId) => navigate(scenarioFor(nextScreen))

  return (
    <main className="mockup-root">
      <ProductShell key={selected.id} scenario={selected} onScreen={navigateScreen} draft={sharedDraft} onDraftChange={setSharedDraft} />
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

function ProductShell({ scenario, onScreen, draft, onDraftChange }: { scenario: Scenario; onScreen: (screen: ScreenId) => void; draft: string; onDraftChange: (draft: string) => void }) {
  const isHome = scenario.screen === 'home'
  const isChat = scenario.screen === 'chat'
  const isSettings = scenario.screen === 'settings'
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)
  const [assistantOpen, setAssistantOpen] = useState(scenario.variant === 'assistant-drawer')
  const [importOpen, setImportOpen] = useState(scenario.variant === 'import-review')
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [itemListOpen, setItemListOpen] = useState(false)
  const [itemListQuery, setItemListQuery] = useState('')
  const [leftSidebarWidth, setLeftSidebarWidth] = useState(220)
  const [rightSidebarWidth, setRightSidebarWidth] = useState(286)
  const viewObjectKind = viewObjectKindByVariant[scenario.variant] ?? 'analysis-mesh'
  const [selectedViewObjects, setSelectedViewObjects] = useState([viewObjectKinds[viewObjectKind].name])

  const selectViewObject = (name: string, additive = false) => {
    setSelectedViewObjects((current) => additive ? [...current.filter((item) => item !== name), name] : [name])
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
            {topMenus.map((menu) => <DropdownMenu key={menu}><DropdownMenuTrigger asChild><button>{menu}</button></DropdownMenuTrigger><DropdownMenuContent align="start"><DropdownMenuItem>{menu}を開く</DropdownMenuItem><DropdownMenuItem>{menu}の設定</DropdownMenuItem></DropdownMenuContent></DropdownMenu>)}
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
            <button aria-label="設定" onClick={() => onScreen('settings')}><Settings size={16} /></button>
            <button aria-label="ヘルプ"><HelpCircle size={16} /></button>
          </div>
        </div>
        {!isHome && !isSettings && <div className="work-toolbar">
          <Button variant="ghost" size="icon" className="panel-toggle panel-toggle-left" aria-label={leftOpen ? '左サイドバーを閉じる' : '左サイドバーを開く'} onClick={() => setLeftOpen((open) => !open)}><PanelLeft size={15} /></Button>
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
          className={`workbench ${isChat ? 'chat-workbench' : ''} ${!leftOpen ? 'left-closed' : ''} ${!rightOpen || itemListOpen ? 'right-closed' : ''}`}
          style={{ '--left-sidebar-width': `${leftSidebarWidth}px`, '--right-sidebar-width': `${rightSidebarWidth}px` } as React.CSSProperties}
        >
          {leftOpen && <LeftSidebar screen={scenario.screen} width={leftSidebarWidth} setWidth={setLeftSidebarWidth} />}
          <section className="centre-column">
            {scenario.screen !== 'chat' && <WorkAreaBar screen={scenario.screen} itemListOpen={itemListOpen} onItemListOpenChange={setItemListOpen} itemListQuery={itemListQuery} onItemListQueryChange={setItemListQuery} />}
            <div className={`canvas-wrap ${scenario.screen === 'chat' ? 'chat-canvas-wrap' : ''} ${scenario.screen === 'view' && !itemListOpen ? 'view-canvas-wrap' : ''} ${itemListOpen ? 'work-item-list-wrap' : ''}`}>
              {itemListOpen && scenario.screen !== 'chat' ? <WorkItemLibrary screen={scenario.screen} query={itemListQuery} onSelect={() => setItemListOpen(false)} /> : <ScreenCanvas scenario={scenario} draft={draft} onDraftChange={onDraftChange} onViewObjectSelect={selectViewObject} onScreen={onScreen} />}
              {!isChat && assistantOpen && <AssistantDrawer draft={draft} onDraftChange={onDraftChange} onClose={() => setAssistantOpen(false)} onOpenChat={() => onScreen('chat')} />}
            </div>
            {scenario.screen !== 'chat' && !itemListOpen && <AssetLibraryShelf screen={scenario.screen} variant={scenario.variant} />}
            {scenario.screen !== 'chat' && (assistantOpen ? null : <InstructionBar draft={draft} onDraftChange={onDraftChange} onOpen={() => setAssistantOpen(true)} />)}
          </section>
          {!isChat && rightOpen && !itemListOpen && <RightSidebar screen={scenario.screen} variant={scenario.variant} width={rightSidebarWidth} setWidth={setRightSidebarWidth} selectedViewObjects={selectedViewObjects} onViewObjectSelect={selectViewObject} />}
        </div>
      )}
      <ImportFlowDialog open={importOpen} onOpenChange={setImportOpen} initialStep={scenario.variant === 'import-review' ? 'review' : 'choose'} />
    </section>
  )
}

function NotificationHistory({ onClose }: { onClose: () => void }) {
  return <section className="notification-history" aria-label="通知履歴">
    <header><span><b>通知履歴</b><small>完了・失敗・拒否をローカルに保持</small></span><button type="button" aria-label="通知履歴を閉じる" onClick={onClose}><X size={14} /></button></header>
    <div className="notification-history-list">
      <article><ShieldCheck size={14} /><span><b>ワークスペースを開きました</b><small>ローカル操作・外部通信なし</small></span></article>
      <article className="warning"><AlertTriangle size={14} /><span><b>未宣言の単位があります</b><small>変換は行わず、数量を未宣言として維持しています</small></span></article>
    </div>
    <footer><button type="button">すべての通知を表示</button></footer>
  </section>
}

function ImportFlowDialog({ open, onOpenChange, initialStep = 'choose' }: { open: boolean; onOpenChange: (open: boolean) => void; initialStep?: 'choose' | 'review' }) {
  const [step, setStep] = useState<'choose' | 'review' | 'importing'>(initialStep)
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
      </>}
      {step === 'importing' && <section className="workflow-progress" aria-live="polite"><CircleDashed size={22} /><span><b>構造と完全性を検証しています</b><small>キャンセルしても部分ケースを残しません</small></span><i><span /></i></section>}
      <footer>
        <button type="button" onClick={close}>キャンセル</button>
        {step === 'choose' && <button type="button" className="primary-button" onClick={() => setStep('review')}>ファイルを選択</button>}
        {step === 'review' && <button type="button" className="primary-button" onClick={() => setStep('importing')}>検証して取込</button>}
      </footer>
    </DialogContent>
  </Dialog>
}

function WorkspaceHome({ variant, onOpenView, onImport }: { variant: string; onOpenView: () => void; onImport: () => void }) {
  const [homeQuery, setHomeQuery] = useState('')
  const [homeFilter, setHomeFilter] = useState('すべて')
  const [homeLayout, setHomeLayout] = useState<'grid' | 'list'>('grid')
  const workspaceItems = [['冷却ブラケット検討', '構造', 'ケース、テンプレート、パイプラインをまとめた設計検討', 'ローカル', '/thumbnails/bracket-1.png'], ['マニホールド流量検証', '流体', '複数条件を整理した流量検証ワークスペース', 'ローカル', '/thumbnails/manifold-1.png'], ['筐体熱解析', '熱', '熱解析結果とレポート構成を管理するワークスペース', 'ローカル', '/thumbnails/housing.png'], ['翼型空力検討', '流体', '翼型まわりの解析構成とレポートを整理するワークスペース', 'ローカル', '/thumbnails/wing.png']]
  const visibleWorkspaces = workspaceItems.filter(([name, tag, description, scope]) => `${name} ${tag} ${description}`.includes(homeQuery.trim()) && (homeFilter === 'すべて' || homeFilter === '最近使用' || homeFilter === scope))
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
      <div className="workspace-list-toolbar"><div><h1>ワークスペース一覧</h1><p>解析プロジェクトを整理・検索して開きます。</p></div><div className="home-tools"><label><Search size={15} /><input value={homeQuery} onChange={(event) => setHomeQuery(event.target.value)} placeholder="名前・説明・タグで検索" /></label><button aria-label="絞り込み"><SlidersHorizontal size={14} /></button><div className="layout-switch"><button className={homeLayout === 'grid' ? 'active' : ''} aria-label="グリッド表示" aria-pressed={homeLayout === 'grid'} onClick={() => setHomeLayout('grid')}><LayoutGrid size={14} /></button><button className={homeLayout === 'list' ? 'active' : ''} aria-label="リスト表示" aria-pressed={homeLayout === 'list'} onClick={() => setHomeLayout('list')}><List size={14} /></button></div><button className="primary-button" onClick={onOpenView}><Plus size={15} /> 新規ワークスペース</button></div></div>
      <div className="workspace-filters">{['すべて', '最近使用', 'ローカル', '共有'].map((item) => <button className={homeFilter === item ? 'active' : ''} onClick={() => setHomeFilter(item)} key={item}>{item}</button>)}</div>
      <div className={`workspace-grid ${homeLayout === 'list' ? 'workspace-list-layout' : ''}`}>
        {visibleWorkspaces.map(([name, tag, description, scope, preview]) => (
          <button className="workspace-card" key={name} onClick={onOpenView}>
            <div className="workspace-visual"><Image src={preview} alt={`${name}の参照プレビュー`} fill sizes="(max-width: 640px) 100vw, 320px" /><span>参照モック画像・解析値未連携</span></div>
            <div><div className="workspace-card-heading"><span><small>ワークスペース</small><h2>{name}</h2></span><ArrowUpRight size={15} /></div><p>{description}</p><div className="workspace-tags"><span>{tag}</span><span>{scope}</span></div><footer><span>ケース数：—</span><span>最終利用：—</span></footer></div>
          </button>
        ))}
      </div>
      {visibleWorkspaces.length === 0 && <div className="centred-state"><Search size={24} /><h2>一致するワークスペースはありません</h2><p>検索語または絞り込みを変更してください。</p></div>}
    </div>
  )
}

function LeftSidebar({ screen, width, setWidth }: { screen: ScreenId; width: number; setWidth: React.Dispatch<React.SetStateAction<number>> }) {
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
            <div className="permanent-search"><Search size={13} /><input placeholder="ケースを検索・タグ絞込" /></div>
            <WorkspaceSourceSections />
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

function WorkspaceSourceSections() {
  return (
    <>
      <SidebarSection title="ケース" icon={<FolderOpen size={13} />}>
        <button className="tree-row active"><ChevronDown size={12} /><span><b>設計スタディ</b><small>3ケース</small></span></button>
        {['基準ケース', '板厚変更', '荷重変更'].map((item) => <button className="tree-row nested" key={item}><Square size={10} /><span><b>{item}</b><small>単位未宣言</small></span></button>)}
      </SidebarSection>
      <SidebarSection title="変数" icon={<Variable size={13} />}><button className="variable-row"><span>荷重</span><b>—</b><small>単位未宣言</small></button><button className="variable-row"><span>応力場</span><b>—</b><small>データセット</small></button></SidebarSection>
      <SidebarSection title="参考資料" icon={<FileText size={13} />}><button className="tree-row"><FileText size={11} /><span><b>設計ノート</b><small>数値根拠には使用しない</small></span></button></SidebarSection>
    </>
  )
}

function SidebarSection({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return <section className="sidebar-section"><h3>{icon}{title}<ChevronDown size={11} /></h3>{children}</section>
}

type WorkItemHeader = {
  title: string
  itemLabel: string
  detail: string
  createLabel: string
  items: string[]
}

const workItemHeaderByScreen: Partial<Record<ScreenId, WorkItemHeader>> = {
  simulation: { title: 'シミュレーション', itemLabel: 'シミュレーション', detail: '外部ソルバー実行定義・後続リリース', createLabel: '新規シミュレーション', items: ['基準シミュレーション', '材料条件スタディ'] },
  view: { title: 'ビュー', itemLabel: 'ビュー', detail: 'ワークスペース内のビューを編集中', createLabel: '新規ビュー', items: ['標準ビュー', 'ケース比較ビュー'] },
  graph: { title: 'グラフ', itemLabel: 'グラフ', detail: 'ワークスペース内のグラフを編集中', createLabel: '新規グラフ', items: ['ケース比較グラフ', '結果推移グラフ'] },
  report: { title: 'レポート', itemLabel: 'レポート', detail: 'ワークスペース内のレポートを編集中', createLabel: '新規レポート', items: ['設計レビューレポート', '要約レポート'] },
  pipeline: { title: '自動化', itemLabel: 'パイプライン', detail: '結果処理と成果物生成を自動化', createLabel: '新規パイプライン', items: ['レポート生成フロー', 'ケース比較フロー'] },
}

function WorkAreaBar({ screen, itemListOpen, onItemListOpenChange, itemListQuery, onItemListQueryChange }: { screen: ScreenId; itemListOpen: boolean; onItemListOpenChange: (open: boolean) => void; itemListQuery: string; onItemListQueryChange: (query: string) => void }) {
  const itemHeader = workItemHeaderByScreen[screen]
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [previewIndex, setPreviewIndex] = useState<number | null>(null)
  const [previewTop, setPreviewTop] = useState<number | null>(null)
  const [selectedByScreen, setSelectedByScreen] = useState<Partial<Record<ScreenId, string>>>({})
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteItem, setDeleteItem] = useState<string | null>(null)
  const [itemNotice, setItemNotice] = useState('')

  if (!itemHeader) {
    return <div className="work-area-bar"><div className="work-area-static"><span className="eyebrow">{screenNames[screen]}</span><b>{screenNames[screen]}</b><small>対象ワークスペースは変わりません</small></div></div>
  }
  const selectedItem = selectedByScreen[screen] ?? itemHeader.items[0]
  const visibleItems = itemHeader.items.filter((item) => item.includes(query.trim()))

  const selectItem = (item: string) => {
    setSelectedByScreen((current) => ({ ...current, [screen]: item }))
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
          <span className="work-item-selector-copy"><small className="work-item-selector-kind">{itemHeader.itemLabel}</small><b>{selectedItem}</b></span>
          <ChevronDown size={14} aria-hidden="true" />
        </button>
        {open && (
          <section className="work-item-popover" aria-label={`${itemHeader.itemLabel}一覧`}>
            <label><Search size={13} aria-hidden="true" /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`${itemHeader.itemLabel}を検索`} /></label>
            <div id={`work-item-list-${screen}`} role="listbox" aria-label={`${itemHeader.itemLabel}一覧`} onMouseLeave={() => { setPreviewIndex(null); setPreviewTop(null) }}>
              {visibleItems.map((item, index) => (
                <div className={`work-item-option ${selectedItem === item ? 'active' : ''}`} key={item} onMouseEnter={(event) => showPreview(event, index)} onFocus={(event) => showPreview(event, index)}>
                  <button type="button" role="option" aria-selected={selectedItem === item} onClick={() => selectItem(item)}><span>{item}</span><small>{selectedItem === item ? '編集中' : 'ワークスペース項目'}</small></button>
                  <DropdownMenu><DropdownMenuTrigger asChild><button type="button" className="work-item-more" aria-label={`${item}の操作`}><MoreHorizontal size={14} /></button></DropdownMenuTrigger><DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => setItemNotice(`${item}の名前編集を開始しました`)}><Pencil size={12} />名前を変更</DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => setItemNotice(`${item}を独立した複製として作成しました`)}><Copy size={12} />複製</DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => setDeleteItem(item)}><Trash2 size={12} />削除</DropdownMenuItem>
                  </DropdownMenuContent></DropdownMenu>
                </div>
              ))}
              {visibleItems.length === 0 && <p>一致する{itemHeader.itemLabel}はありません。</p>}
            </div>
            {open && previewIndex !== null && (screen === 'view' || screen === 'graph' || screen === 'report') && <div className="work-item-popover-preview" style={{ top: `${previewTop ?? 48}px` }}><WorkItemPreview screen={screen} index={previewIndex} /></div>}
          </section>
        )}
      </div>}
      {itemListOpen && <div className="work-area-list-tools">
        <div className="work-area-list-search"><Search size={14} aria-hidden="true" /><Input value={itemListQuery} onChange={(event) => onItemListQueryChange(event.target.value)} className="work-area-list-search-input" placeholder={`${itemHeader.itemLabel}・説明・タグで検索`} aria-label={`${itemHeader.itemLabel}を検索`} /></div>
        <Button variant="outline" size="icon" aria-label="絞り込み"><SlidersHorizontal size={14} /></Button>
        <div className="layout-switch"><Button variant="ghost" size="icon" className="active" aria-label="グリッド表示"><LayoutGrid size={14} /></Button><Button variant="ghost" size="icon" aria-label="リスト表示"><List size={14} /></Button></div>
      </div>}
      <Button className="primary-button" aria-label={`${itemHeader.createLabel}を作成`} onClick={() => setCreateOpen(true)}><Plus size={14} /> {itemHeader.createLabel}</Button>
      {itemNotice && <span className="work-item-notice" role="status">{itemNotice}</span>}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog"><header><span><small>{itemHeader.itemLabel}</small><b>{itemHeader.createLabel}</b></span><button type="button" aria-label="新規作成を閉じる" onClick={() => setCreateOpen(false)}><X size={15} /></button></header><div className="creation-options"><button type="button" onClick={() => { setItemNotice(`空の${itemHeader.itemLabel}を作成しました`); setCreateOpen(false) }}><Plus size={18} /><span><b>空から作成</b><small>独立したワークスペース項目</small></span></button>{screen !== 'simulation' && <button type="button" onClick={() => { setItemNotice('テンプレートの解決確認へ進みます'); setCreateOpen(false) }}><LayoutTemplate size={18} /><span><b>テンプレートから作成</b><small>解決結果を確認してから作成</small></span></button>}</div>{screen === 'simulation' && <p className="workflow-trust-note"><AlertTriangle size={13} />定義は保存できますが、r1では外部ソルバーを実行しません。</p>}</DialogContent></Dialog>
      <Dialog open={Boolean(deleteItem)} onOpenChange={(open) => !open && setDeleteItem(null)}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog"><header><span><small>削除の確認</small><b>{deleteItem}</b></span><button type="button" aria-label="削除確認を閉じる" onClick={() => setDeleteItem(null)}><X size={15} /></button></header><p>この{itemHeader.itemLabel}だけを削除します。テンプレートや出力済みファイルは削除しません。</p><footer><button type="button" onClick={() => setDeleteItem(null)}>キャンセル</button><button type="button" className="danger-button" onClick={() => { setItemNotice(`${deleteItem}を削除しました`); setDeleteItem(null) }}>削除</button></footer></DialogContent></Dialog>
    </div>
  )
}

function WorkItemLibrary({ screen, query, onSelect }: { screen: ScreenId; query: string; onSelect: () => void }) {
  const [scope, setScope] = useState('すべて')
  const [layout, setLayout] = useState<'grid' | 'list'>('grid')
  const itemHeader = workItemHeaderByScreen[screen]
  if (!itemHeader) return null
  const visibleItems = itemHeader.items.map((item, index) => ({ item, index })).filter(({ item }) => item.includes(query.trim())).filter(() => scope !== '共有')
  return <section className="home-page work-item-library" aria-label={`${itemHeader.itemLabel}一覧`}>
    <div className="workspace-filters"><div>{['すべて', '最近使用', 'ローカル', '共有'].map((item) => <button className={scope === item ? 'active' : ''} onClick={() => setScope(item)} key={item}>{item}</button>)}</div><div className="layout-switch"><button className={layout === 'grid' ? 'active' : ''} onClick={() => setLayout('grid')} aria-label="グリッド表示"><LayoutGrid size={14} /></button><button className={layout === 'list' ? 'active' : ''} onClick={() => setLayout('list')} aria-label="リスト表示"><List size={14} /></button></div></div>
    <div className={`workspace-grid ${layout === 'list' ? 'workspace-list-layout' : ''}`}>{visibleItems.map(({ item, index }) => <button type="button" className="workspace-card" key={item} onClick={onSelect}><WorkItemCatalogPreview screen={screen} index={index} label={itemHeader.itemLabel} /><div><div className="workspace-card-heading"><span><small>{itemHeader.itemLabel}</small><h2>{item}</h2></span><ArrowUpRight size={15} /></div><p>ワークスペースに保存された{itemHeader.itemLabel}の設定と表示内容。</p><div className="workspace-tags"><span>{index === 0 ? '現在使用中' : 'ローカル'}</span><span>{itemHeader.title}</span></div><footer><span>項目番号 {index + 1}</span><span>最近使用</span></footer></div></button>)}</div>
    {visibleItems.length === 0 && <div className="centred-state"><Search size={24} /><h2>一致する{itemHeader.itemLabel}はありません</h2><p>検索語を変更してください。</p></div>}
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
type LibraryItem = { id: string; name: string; detail: string; tags: string[]; tone: string; thumbnail?: string }

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
    { id: 'stress-steel', name: 'スチール＋応力コンター', detail: '解析データ依存・サンプルデータ', tags: ['応力', 'MaterialX'], tone: 'blue', thumbnail: '/materials/technical-blue.png' },
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
  const libraryTagSuggestions = Array.from(new Set(samples.flatMap((item) => item.tags))).sort((a, b) => a.localeCompare(b, 'ja'))
  const sourceLabel = source === 'sample' ? 'サンプル' : 'オリジナル'
  const hasFilter = query.trim().length > 0 || selectedTags.length > 0
  const visibleTags = libraryTagSuggestions.filter((tag) => tag.toLocaleLowerCase('ja').includes(tagQuery.trim().toLocaleLowerCase('ja')))
  const normalizedQuery = query.trim().toLocaleLowerCase('ja')
  const visibleItems = (source === 'sample' ? samples : [])
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
            <Tabs value={source} onValueChange={(value) => setSource(value as LibrarySource)} className="contents">
              <TabsList className="template-source-tabs" aria-label={`${label}の種類`}>
                <TabsTrigger value="sample" className={source === 'sample' ? 'active' : ''}>サンプル</TabsTrigger>
                <TabsTrigger value="original" className={source === 'original' ? 'active' : ''}>オリジナル</TabsTrigger>
              </TabsList>
            </Tabs>
            <div className="template-library-search" role="search" aria-label={`${label}を検索・絞り込み`}>
              <div className="template-search-row">
                <label className="template-text-search"><Search size={13} aria-hidden="true" /><Input className="h-auto border-0 bg-transparent p-0 text-[9px] shadow-none focus-visible:ring-0" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`${label}を検索`} aria-label={`${label}を検索`} /></label>
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
                    <label className="template-tag-search"><Search size={12} aria-hidden="true" /><Input className="h-auto border-0 bg-transparent p-0 text-[9px] shadow-none focus-visible:ring-0" value={tagQuery} onChange={(event) => setTagQuery(event.target.value)} placeholder="タグを絞り込み" role="combobox" aria-autocomplete="list" aria-expanded="true" aria-controls="template-tag-options" /></label>
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
              {selectedTags.length > 0 && <div className="template-tag-chips" aria-label="選択中のタグ">{selectedTags.map((tag) => <button type="button" className="template-tag-chip" aria-label={`${tag}を解除`} onClick={() => toggleTag(tag)} key={tag}><span>{tag}</span><X size={10} aria-hidden="true" /></button>)}</div>}
            </div>
          </div>
          {visibleItems.length > 0 ? (
            <div className="library-card-grid" role="list" aria-label={`${sourceLabel}の${label}`}>
              {visibleItems.map((item) => <div role="listitem" key={item.id}><button type="button" draggable className={`library-card ${selectedItem === item.id ? 'selected' : ''}`} aria-pressed={selectedItem === item.id} onClick={() => setSelectedItem(item.id)} onDragStart={(event) => event.dataTransfer.setData('text/plain', item.id)}>
                <span className={`library-card-preview ${item.thumbnail ? 'material-sphere-thumbnail' : `tone-${item.tone}`}`}>{item.thumbnail ? <Image src={item.thumbnail} alt="" width={54} height={54} sizes="54px" aria-hidden="true" /> : <Icon size={20} strokeWidth={1.45} />}</span>
                <span className="library-card-copy"><b>{item.name}</b><small>{item.detail}</small></span>
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
          {selectedItem && <footer className="library-selection-bar"><span><small>{applyComplete ? '適用済み' : '選択中'}</small><b>{samples.find((item) => item.id === selectedItem)?.name}</b></span><span>{applyComplete ? 'ワークスペースの変更としてUndo可能' : 'ドラッグして対象へ適用'}</span><button type="button" className="primary-button" onClick={() => { setApplyComplete(false); setApplyOpen(true) }}>適用</button></footer>}
        </div>
      </div>
      }
      <Dialog open={applyOpen} onOpenChange={setApplyOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog library-apply-dialog"><header><span><small>{label}を適用</small><b>{samples.find((item) => item.id === selectedItem)?.name}</b></span><button type="button" aria-label="適用確認を閉じる" onClick={() => setApplyOpen(false)}><X size={15} /></button></header>
        {category === 'template' && <section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>解決済み</b><small>レイアウトと表示設定</small></span></p><p><AlertTriangle size={13} /><span><b>確認が必要</b><small>数量・ケース・参照アセットは新しい項目で明示的に結び付けます</small></span></p><p><FolderPlus size={13} /><span><b>作成方法</b><small>開いている項目を置換せず、独立した新規項目を作成</small></span></p></section>}
        {category === 'materials' && <section><p className="workflow-trust-note"><MaterialSphereIcon size={13} />アクティブオブジェクトの新しいマテリアルスロットとして追加します。</p><div className="material-target-options" role="radiogroup" aria-label="マテリアルの割り当て先">{([['object','オブジェクト全体'],['part','部品'],['elements','要素セット']] as const).map(([id,text]) => <label key={id}><input type="radio" name="material-target" checked={materialTarget === id} onChange={() => setMaterialTarget(id)} /><span>{text}</span></label>)}</div>{materialTarget !== 'object' && <p className="workflow-selection-mode"><Shapes size={13} /><span><b>適用後に選択モードを開始</b><small>ビューポートまたはアウトライナーで重複しない対象を選択します</small></span></p>}</section>}
        {category === 'objects' && <section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>独立オブジェクトを作成</b><small>元アセットの識別子とリビジョンを来歴として記録</small></span></p><p><AlertTriangle size={13} /><span><b>参照解決</b><small>必要なフィールドや座標がなければ作成せず理由を表示</small></span></p></section>}
        {!['template','materials','objects'].includes(category) && <p className="workflow-trust-note"><ShieldCheck size={13} />表示表現だけを変更し、解析値・単位・来歴は変更しません。</p>}
        <footer><button type="button" onClick={() => setApplyOpen(false)}>キャンセル</button><button type="button" className="primary-button" onClick={() => { setApplyComplete(true); setApplyOpen(false) }}>{category === 'template' ? '確認して新規作成' : materialTarget !== 'object' && category === 'materials' ? '選択モードへ' : '適用'}</button></footer>
      </DialogContent></Dialog>
    </section>
  )
}

function RightSidebar({ screen, variant, width, setWidth, selectedViewObjects, onViewObjectSelect }: { screen: ScreenId; variant: string; width: number; setWidth: React.Dispatch<React.SetStateAction<number>>; selectedViewObjects: string[]; onViewObjectSelect: (name: string, additive?: boolean) => void }) {
  const activeViewObjectKind = viewObjectKindByVariant[variant] ?? 'analysis-mesh'
  const tabs = rightSidebarTabs[screen].filter((tab) => screen !== 'view' || tab.id !== 'text' || viewObjectKinds[activeViewObjectKind].textProperties)
  const [selectedByScreen, setSelectedByScreen] = useState<Partial<Record<ScreenId, string>>>({})
  const variantTab = variant.startsWith('object-') ? 'objects' : variant.startsWith('material-') ? 'materials' : variant.includes('output-preflight') ? 'output' : variant === 'series-unresolved' || variant === 'commentary-review' ? 'detail' : undefined
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
      {screen === 'view' && <OutlinerPanel variant={variant} selectedNames={selectedViewObjects} onSelect={onViewObjectSelect} />}
      <div className="sidebar-editor">
        <nav className="sidebar-tab-rail" role="tablist" aria-label={`${screenNames[screen]}の設定`} aria-orientation="vertical">
          {tabs.map((tab, index) => {
            const Icon = tab.icon
            const active = tab.id === selectedTab.id
            const startsSelectionGroup = tab.scope === 'selection' && tabs[index - 1]?.scope !== 'selection'
            const scopeLabel = tab.scope === 'selection' ? '選択中のオブジェクト' : tab.scope === 'view' ? 'ビュー全体' : undefined
            return (
              <Fragment key={tab.id}>
                {startsSelectionGroup && <span className="sidebar-tab-scope-separator" aria-hidden="true" />}
                <button
                  id={`sidebar-tab-${screen}-${tab.id}`}
                  className={`sidebar-tab-button ${active ? 'active' : ''}`}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  aria-controls={`sidebar-panel-${screen}`}
                  aria-label={scopeLabel ? `${scopeLabel}：${tab.label}` : tab.label}
                  data-tooltip={tab.label}
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
            <span><b>{selectedTab.label}</b></span>
          </header>
          <p className="sidebar-tab-summary">{selectedTab.description}</p>
          <PropertyEditor key={`${screen}-${selectedTab.id}`} screen={screen} tab={selectedTab} variant={variant} selectedViewObjects={selectedViewObjects} />
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

function PropertyEditor({ screen, tab, variant, selectedViewObjects }: { screen: ScreenId; tab: SidebarTab; variant: string; selectedViewObjects: string[] }) {
  if (screen === 'pipeline') return <AutomationPropertyEditor tab={tab} />
  if (screen === 'view' && tab.id === 'objects') return <ViewObjectPropertyEditor variant={variant} selectedViewObjects={selectedViewObjects} />
  if (screen === 'view' && tab.id === 'materials') return <ViewMaterialPropertyEditor variant={variant} />
  if (screen === 'view' && tab.id === 'text') return <ViewTextPropertyEditor variant={variant} />
  if (screen === 'view') return <ViewPropertyEditor tab={tab} variant={variant} />
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

function PropertyGroup({ title, children, open = true }: { title: string; children: React.ReactNode; open?: boolean }) {
  return <details className="property-group" open={open}><summary><ChevronRight size={12} /><b>{title}</b></summary><div className="property-fields">{children}</div></details>
}

type PreflightCheck = { label: string; detail: string; status: 'pass' | 'warning' | 'blocked' }

function OutputPreflightDialog({ open, onOpenChange, title, checks, onStart }: { open: boolean; onOpenChange: (open: boolean) => void; title: string; checks: PreflightCheck[]; onStart: () => void }) {
  const blocked = checks.some((check) => check.status === 'blocked')
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog preflight-dialog"><header><span><small>出力前チェック</small><b>{title}</b></span><button type="button" aria-label="出力前チェックを閉じる" onClick={() => onOpenChange(false)}><X size={15} /></button></header><section className="preflight-checks">{checks.map((check) => <article className={check.status} key={check.label}>{check.status === 'pass' ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}<span><b>{check.label}</b><small>{check.detail}</small></span><em>{check.status === 'pass' ? '合格' : check.status === 'warning' ? '要記載' : '出力不可'}</em></article>)}</section><p className={blocked ? 'workflow-trust-note blocked' : 'workflow-trust-note'}>{blocked ? <AlertTriangle size={13} /> : <ShieldCheck size={13} />}{blocked ? '不足項目を解決するまで通常出力は開始しません。既存成果物は変更されません。' : '新しい実行フォルダーへ保存し、既存成果物を上書きしません。'}</p><footer><button type="button" onClick={() => onOpenChange(false)}>戻る</button><button type="button" className="primary-button" disabled={blocked} onClick={onStart}>出力を開始</button></footer></DialogContent></Dialog>
}

function ViewPropertyEditor({ tab, variant }: { tab: SidebarTab; variant: string }) {
  const [backgroundMode, setBackgroundMode] = useState<'solid' | 'gradient' | 'image' | 'environment'>('gradient')
  const [outputMode, setOutputMode] = useState<'image' | 'video'>('image')
  const [renderer, setRenderer] = useState<'vtk' | 'omniverse'>('vtk')
  const [lightingSource, setLightingSource] = useState<'studio' | 'background-environment' | 'unlit'>('studio')
  const [preflightOpen, setPreflightOpen] = useState(variant === 'output-preflight')
  const [outputStarted, setOutputStarted] = useState(false)

  if (tab.id === 'overall') return <div className="property-editor">
    <PropertyGroup title="ビュー">
      <label><span>名前</span><input defaultValue="変形＋応力" /></label>
      <label><span>レイアウト</span><select defaultValue="single"><option value="single">単一ビュー</option><option value="horizontal">上下分割</option><option value="vertical">左右分割</option><option value="quad">4分割</option></select></label>
      <label><span>投影</span><select defaultValue="perspective"><option value="perspective">透視投影</option><option value="orthographic">平行投影</option></select></label>
      <label><span>カメラ</span><select defaultValue="saved"><option value="saved">保存済みカメラ</option><option value="front">正面</option><option value="right">右</option><option value="top">上</option><option value="isometric">等角</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="ガイド">
      <label className="property-toggle"><span>座標軸</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>グリッド</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>凡例</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>選択輪郭</span><input type="checkbox" defaultChecked /></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />カメラとガイドは表示状態です。解析値と正規データは変更しません。</p>
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
    <PropertyGroup title="画質">
      <label><span>アンチエイリアス</span><select defaultValue="taa"><option value="none">なし</option><option value="fxaa">FXAA</option><option value="taa">TAA</option></select></label>
      <label><span>トーンマップ</span><select defaultValue="neutral"><option value="neutral">Neutral</option><option value="aces">ACES</option><option value="none">なし</option></select></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />未対応レンダラーへ黙って切り替えず、利用できない理由を表示します。</p>
  </div>

  if (tab.id === 'background') return <div className="property-editor">
    <PropertyGroup title="背景">
      <label><span>種類</span><select value={backgroundMode} onChange={(event) => setBackgroundMode(event.target.value as typeof backgroundMode)}><option value="solid">単色</option><option value="gradient">グラデーション</option><option value="image">画像</option><option value="environment">環境</option></select></label>
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
      <label><span>種類</span><select value={outputMode} onChange={(event) => setOutputMode(event.target.value as typeof outputMode)}><option value="image">画像</option><option value="video">動画</option></select></label>
      {outputMode === 'image' ? <>
        <label><span>形式</span><select defaultValue="png"><option value="png">PNG</option><option value="jpeg">JPEG</option><option value="tiff">TIFF</option></select></label>
        <label><span>サイズ</span><select defaultValue="1920x1080"><option value="1920x1080">1920 × 1080</option><option value="3840x2160">3840 × 2160</option><option value="viewport">現在の表示領域</option></select></label>
        <label className="property-toggle"><span>背景を透過</span><input type="checkbox" /></label>
      </> : <>
        <label><span>形式</span><select defaultValue="mp4"><option value="mp4">MP4</option><option value="webm">WebM</option><option value="frames">PNG連番</option></select></label>
        <label><span>カメラパス</span><select defaultValue="unresolved"><option value="unresolved">未選択</option></select></label>
        <label><span>再生軸</span><select defaultValue="result"><option value="result">結果軸</option><option value="camera">カメラのみ</option></select></label>
        <label><span>速度</span><select defaultValue="1"><option value="0.5">0.5×</option><option value="1">1.0×</option><option value="2">2.0×</option></select></label>
        <label><span>フレームレート</span><select defaultValue="30"><option value="24">24 fps</option><option value="30">30 fps</option><option value="60">60 fps</option></select></label>
      </>}
    </PropertyGroup>
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
  const [outputKind, setOutputKind] = useState<'image' | 'vector' | 'data' | 'animation'>('image')
  const [preflightOpen, setPreflightOpen] = useState(variant === 'output-preflight')
  const [outputStarted, setOutputStarted] = useState(false)
  const [caseSelectionMode, setCaseSelectionMode] = useState<'selected' | 'saved' | 'tag' | 'code'>('selected')
  const [graphSeries, setGraphSeries] = useState([{ id: 'series-1', label: '系列 1', quantity: 'unresolved', source: 'dataset' }])
  const [activeSeriesId, setActiveSeriesId] = useState('series-1')
  const activeSeries = graphSeries.find((series) => series.id === activeSeriesId) ?? graphSeries[0]

  if (tab.id === 'overall') return <div className="property-editor">
    <PropertyGroup title="グラフ">
      <label><span>名前</span><input defaultValue="ケース比較" /></label>
      <label><span>タイトル</span><input defaultValue="最大変位の比較" /></label>
      <label><span>副題</span><input placeholder="任意" /></label>
      <label><span>説明</span><textarea rows={3} placeholder="図が示す内容を記載" /></label>
    </PropertyGroup>
    <PropertyGroup title="構成">
      <label className="property-toggle"><span>タイトル</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>凡例</span><input type="checkbox" defaultChecked /></label>
      <label><span>凡例位置</span><select defaultValue="right"><option value="right">右</option><option value="bottom">下</option><option value="inside">プロット内</option></select></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />グラフは値のコピーではなく、数量・単位・来歴を参照する定義として保存します。</p>
  </div>

  if (tab.id === 'kind') return <div className="property-editor">
    <PropertyGroup title="次元">
      <label><span>次元</span><select value={dimension} onChange={(event) => setDimension(event.target.value as typeof dimension)}><option value="2d">2D</option><option value="3d">3D</option></select></label>
      <label><span>種類</span>{dimension === '2d' ? <select defaultValue="line"><option value="line">折れ線</option><option value="scatter">散布図</option><option value="bar">棒</option><option value="distribution">分布</option><option value="heatmap">ヒートマップ</option></select> : <select defaultValue="surface"><option value="surface">サーフェス</option><option value="scatter3d">3D散布図</option><option value="contour3d">2変数コンター</option></select>}</label>
    </PropertyGroup>
    {dimension === '3d' && <PropertyGroup title="投影">
      <label><span>投影</span><select defaultValue="perspective"><option value="perspective">透視投影</option><option value="orthographic">平行投影</option></select></label>
      <label><span>視線</span><select defaultValue="saved"><option value="saved">保存済み</option><option value="isometric">等角</option><option value="front">正面</option><option value="top">上</option></select></label>
    </PropertyGroup>}
    <p className="property-editor-note"><ChartNoAxesCombined size={12} />種類を変えても数量の参照と単位互換性の検証は維持されます。</p>
  </div>

  if (tab.id === 'style') return <div className="property-editor">
    <PropertyGroup title="スタイル">
      <label><span>アセット</span><select defaultValue="technical"><option value="technical">技術資料・標準</option><option value="workspace">ワークスペース設定</option></select></label>
      <label><span>配色</span><select defaultValue="accessible"><option value="accessible">識別性優先</option><option value="monochrome">モノクロ</option></select></label>
      <label><span>背景</span><select defaultValue="light"><option value="light">明るい</option><option value="transparent">透過</option><option value="dark">暗い</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="プロット">
      <label><span>線幅</span><div className="property-range"><input type="range" min="1" max="6" defaultValue="2" /><output>2 px</output></div></label>
      <label><span>マーカー</span><select defaultValue="auto"><option value="auto">自動</option><option value="circle">円</option><option value="square">四角</option><option value="none">なし</option></select></label>
      <label className="property-toggle"><span>主グリッド</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>副グリッド</span><input type="checkbox" /></label>
    </PropertyGroup>
    <p className="property-editor-note"><Paintbrush size={12} />再利用するスタイルは素材ライブラリから適用し、ここでは開いているグラフの表現を調整します。</p>
  </div>

  if (tab.id === 'fonts') return <div className="property-editor">
    <PropertyGroup title="書体">
      <label><span>フォント</span><select defaultValue="workspace"><option value="workspace">ワークスペース設定</option><option value="noto-sans">Noto Sans</option><option value="source-serif">Source Serif</option></select></label>
      <label><span>タイトル</span><select defaultValue="14"><option value="12">12 pt</option><option value="14">14 pt</option><option value="16">16 pt</option></select></label>
      <label><span>軸</span><select defaultValue="10"><option value="9">9 pt</option><option value="10">10 pt</option><option value="11">11 pt</option></select></label>
      <label><span>凡例</span><select defaultValue="9"><option value="8">8 pt</option><option value="9">9 pt</option><option value="10">10 pt</option></select></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />出力では使用文字を検査し、必要な字体をライセンス条件に従って埋め込みます。</p>
  </div>

  if (tab.id === 'detail') return <div className="property-editor">
    <PropertyGroup title="ケース選択">
      <label><span>対象</span><select value={caseSelectionMode} onChange={(event) => setCaseSelectionMode(event.target.value as typeof caseSelectionMode)}><option value="selected">選択中のケース</option><option value="saved">保存済み選択</option><option value="tag">宣言的な条件</option><option value="code">Python選択</option></select></label>
      {caseSelectionMode === 'saved' && <label><span>選択</span><select defaultValue="unresolved"><option value="unresolved">選択を指定</option></select></label>}
      {caseSelectionMode === 'tag' && <label><span>条件</span><input placeholder="タグ・状態・変数の条件" /></label>}
      {caseSelectionMode === 'code' && <><label><span>スクリプト</span><textarea rows={3} defaultValue={'def select(cases):\n    return []'} /></label><p className="property-editor-note"><ShieldCheck size={12} />メタデータだけを受け取り、ファイル・データセット・ネットワークへアクセスしません。失敗は空選択ではなく拒否として報告します。</p></>}
      <label><span>選択結果</span><input value={caseSelectionMode === 'selected' ? '選択中のケース・1件' : '条件の解決待ち'} readOnly /></label>
      <label><span>反復</span><select defaultValue="separate"><option value="separate">反復ごとに表示</option><option value="combined">反復を集約</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="系列">
      <div className="compact-definition-list"><div role="listbox" aria-label="グラフ系列">{graphSeries.map((series) => <button type="button" role="option" aria-selected={activeSeriesId === series.id} className={activeSeriesId === series.id ? 'selected' : ''} onClick={() => setActiveSeriesId(series.id)} key={series.id}><span><b>{series.label}</b><small>{series.quantity === 'unresolved' ? '数量未選択' : series.quantity === 'expression' ? '式による計算・解析モジュール' : '数量参照・単位未宣言'}</small></span>{series.quantity === 'unresolved' && <AlertTriangle size={12} />}</button>)}</div><aside><button type="button" aria-label="系列を追加" onClick={() => { const id = `series-${graphSeries.length + 1}`; setGraphSeries((current) => [...current, { id, label: `系列 ${current.length + 1}`, quantity: 'unresolved', source: 'dataset' }]); setActiveSeriesId(id) }}><Plus size={12} /></button><button type="button" aria-label="選択中の系列を削除" disabled={graphSeries.length === 1} onClick={() => { const next = graphSeries.filter((series) => series.id !== activeSeriesId); setGraphSeries(next); setActiveSeriesId(next[0]?.id ?? '') }}><X size={12} /></button></aside></div>
      {activeSeries && <><label><span>X</span><select defaultValue="parameter"><option value="parameter">パラメーターを選択</option><option value="result-axis">結果軸</option></select></label>
        <label><span>Y</span><select value={activeSeries.quantity} onChange={(event) => setGraphSeries((current) => current.map((series) => series.id === activeSeries.id ? { ...series, quantity: event.target.value } : series))}><option value="unresolved">数量を選択</option><option value="dataset">データセットの数量</option><option value="computed">計算済み数量</option><option value="measurement">測定値</option><option value="reference">参考ファイルの値</option><option value="expression">式</option></select></label>
        {activeSeries.quantity === 'expression' && <label><span>式</span><input placeholder="単位付きの式" /></label>}
        <label><span>単位</span><input value={activeSeries.quantity === 'unresolved' ? '数量の選択後に表示' : '未宣言'} readOnly /></label>
        <label><span>来歴</span><input value={activeSeries.quantity === 'unresolved' ? '数量の選択後に表示' : activeSeries.quantity === 'computed' || activeSeries.quantity === 'expression' ? '計算・式を表示' : activeSeries.quantity === 'reference' ? '参考資料・数値根拠には未使用' : activeSeries.quantity === 'measurement' ? '測定データ' : 'データセット'} readOnly /></label>
        <label><span>欠損</span><select defaultValue="gap"><option value="gap">欠損として表示・凡例に残す</option></select></label></>}
    </PropertyGroup>
    <PropertyGroup title="集約" open={false}>
      <label><span>方法</span><select defaultValue="none"><option value="none">集約しない</option><option value="weighted">関連量で重み付け</option><option value="unweighted">単純平均・重みなし</option></select></label>
      <label><span>範囲</span><select defaultValue="whole"><option value="whole">全体</option><option value="selection">選択範囲</option></select></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />未選択・未宣言・欠損はそのまま表示し、ゼロや近傍値へ置き換えません。</p>
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
    <OutputPreflightDialog open={preflightOpen} onOpenChange={setPreflightOpen} title="グラフ成果物" checks={[{ label: '系列', detail: 'Y数量が未選択です', status: 'blocked' }, { label: '単位', detail: '数量選択後に互換性を検証します', status: 'blocked' }, { label: '保存先', detail: '既存成果物を上書きしない', status: 'pass' }]} onStart={() => { setOutputStarted(true); setPreflightOpen(false) }} />
  </div>
}

function ReportPropertyEditor({ tab, variant }: { tab: SidebarTab; variant: string }) {
  const [commentary, setCommentary] = useState<'mechanical' | 'generated'>(variant === 'commentary-review' ? 'generated' : 'mechanical')
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

  if (tab.id === 'layout') return <div className="property-editor">
    <PropertyGroup title="ページ">
      <label><span>用紙</span><select defaultValue="a4"><option value="a4">A4</option><option value="letter">Letter</option><option value="screen">画面向け</option></select></label>
      <label><span>向き</span><select defaultValue="portrait"><option value="portrait">縦</option><option value="landscape">横</option></select></label>
      <label><span>余白</span><select defaultValue="standard"><option value="standard">標準</option><option value="narrow">狭い</option><option value="wide">広い</option></select></label>
      <label><span>段組み</span><select defaultValue="single"><option value="single">1段</option><option value="double">2段</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="共通要素">
      <label className="property-toggle"><span>ヘッダー</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>フッター</span><input type="checkbox" defaultChecked /></label>
      <label className="property-toggle"><span>ページ番号</span><input type="checkbox" defaultChecked /></label>
      <label><span>図の幅</span><select defaultValue="column"><option value="column">段幅</option><option value="page">ページ幅</option></select></label>
    </PropertyGroup>
  </div>

  if (tab.id === 'style') return <div className="property-editor">
    <PropertyGroup title="アートスタイル">
      <label><span>スタイル</span><select defaultValue="technical"><option value="technical">技術資料・標準</option><option value="workspace">ワークスペース設定</option></select></label>
      <label><span>配色</span><select defaultValue="accessible"><option value="accessible">識別性優先</option><option value="monochrome">モノクロ印刷</option></select></label>
      <label><span>図表</span><select defaultValue="flat"><option value="flat">フラット</option><option value="bordered">罫線あり</option></select></label>
      <label className="property-toggle"><span>表の縞</span><input type="checkbox" defaultChecked /></label>
    </PropertyGroup>
    <p className="property-editor-note"><Paintbrush size={12} />スタイルは文章や解析値を変更せず、フォント・配色・図表表現だけに適用されます。</p>
  </div>

  if (tab.id === 'fonts') return <div className="property-editor">
    <PropertyGroup title="文字表現">
      <label><span>本文</span><select defaultValue="workspace"><option value="workspace">ワークスペース設定</option><option value="noto-sans">Noto Sans</option><option value="source-serif">Source Serif</option></select></label>
      <label><span>見出し</span><select defaultValue="same"><option value="same">本文と同じ</option><option value="noto-sans">Noto Sans</option></select></label>
      <label><span>本文サイズ</span><select defaultValue="10"><option value="9">9 pt</option><option value="10">10 pt</option><option value="11">11 pt</option></select></label>
      <label><span>注記サイズ</span><select defaultValue="8"><option value="8">8 pt</option><option value="9">9 pt</option></select></label>
    </PropertyGroup>
    <PropertyGroup title="埋め込み">
      <label><span>状態</span><input value="使用文字を出力前に検査" readOnly /></label>
      <label><span>範囲</span><input value="使用グリフのみ" readOnly /></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />表示できない文字は、空の四角で出力せず要素と文字を特定して報告します。</p>
  </div>

  if (tab.id === 'detail') return <div className="property-editor">
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
    <PropertyGroup title="コメント">
      <label><span>方式</span><select value={commentary} onChange={(event) => setCommentary(event.target.value as typeof commentary)}><option value="mechanical">機械的要約のみ</option><option value="generated">生成コメント</option></select></label>
      {commentary === 'generated' && <><label><span>方向</span><textarea rows={3} placeholder="議論してほしい観点" /></label><label><span>深さ</span><select defaultValue="standard"><option value="brief">簡潔</option><option value="standard">標準</option><option value="detailed">詳細</option></select></label><label><span>モデル</span><input value="未設定" readOnly /></label><label><span>検索</span><input value="許可されていません" readOnly /></label></>}
    </PropertyGroup>
    {commentary === 'generated' && <div className="property-unresolved"><AlertTriangle size={13} /><span><b>生成コメントは現在利用できません</b><small>モデルと送信範囲を設定し、費用を確認するまで外部通信しません。</small></span></div>}
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
  if (tab.id === 'permissions') return <div className="property-editor">
    <PropertyGroup title="ワークスペース権限">
      <label className="property-toggle"><span>外部通信</span><input type="checkbox" checked={externalEnabled} onChange={() => externalEnabled ? setExternalEnabled(false) : setPermissionOpen(true)} /></label>
      <label className="property-toggle"><span>Web検索</span><input type="checkbox" checked={webSearchEnabled} onChange={(event) => setWebSearchEnabled(event.target.checked)} disabled={!externalEnabled} /></label>
      <label className="property-toggle"><span>生成コメント</span><input type="checkbox" disabled /></label>
      <label className="property-toggle"><span>詳細調査</span><input type="checkbox" disabled /></label>
    </PropertyGroup>
    <PropertyGroup title="許可先">
      <label><span>ホスト</span><input value="登録なし" readOnly /></label>
      <label><span>送信内容</span><input value="送信前に表示" readOnly /></label>
      <label><span>既定動作</span><input value="拒否" readOnly /></label>
    </PropertyGroup>
    <p className="property-editor-note"><ShieldCheck size={12} />許可されるまで通信を試行しません。ケース名、値、パスを含む送信は個別に確認します。</p>
    <Dialog open={permissionOpen} onOpenChange={setPermissionOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog outbound-review-dialog"><header><span><small>ワークスペース権限</small><b>外部通信を許可しますか？</b></span><button type="button" aria-label="権限確認を閉じる" onClick={() => setPermissionOpen(false)}><X size={15} /></button></header><section className="workflow-check-list"><p><ShieldCheck size={13} /><span><b>既定</b><small>要求ごとに正確な送信内容と宛先を確認</small></span></p><p><AlertTriangle size={13} /><span><b>機密情報</b><small>ケース名、値、ファイルパスは要求ごとの追加許可が必要</small></span></p><p><ScrollText size={13} /><span><b>監査</b><small>送信内容、ホスト、日時、判断をローカルに記録</small></span></p></section><footer><button type="button" onClick={() => setPermissionOpen(false)}>オフラインを維持</button><button type="button" className="primary-button" onClick={() => { setExternalEnabled(true); setPermissionOpen(false) }}>確認を必須にして許可</button></footer></DialogContent></Dialog>
  </div>

  return <div className="property-editor">
    <PropertyGroup title="通信記録">
      <label><span>期間</span><select defaultValue="workspace"><option value="workspace">このワークスペース</option><option value="session">このセッション</option></select></label>
      <label><span>結果</span><select defaultValue="all"><option value="all">すべて</option><option value="allowed">許可</option><option value="blocked">拒否</option></select></label>
    </PropertyGroup>
    <section className="property-audit-empty"><ScrollText size={20} /><b>外部通信の記録はありません</b><small>オフライン操作は通信として記録されません。</small></section>
    <div className="property-panel-action"><button type="button"><FileOutput size={12} />監査ログを書き出す</button></div>
  </div>
}

function ViewObjectPropertyEditor({ variant, selectedViewObjects }: { variant: string; selectedViewObjects: string[] }) {
  const kind = viewObjectKindByVariant[variant] ?? 'analysis-mesh'
  const meta = viewObjectKinds[kind]
  const selectedName = selectedViewObjects.at(-1) ?? meta.name

  return (
    <div className="property-editor">
      <section className="property-selection object-selection-card">
        <span><small>アクティブオブジェクト</small><b>{selectedName}</b><em>{meta.label}</em></span>
      </section>
      <ObjectTypeProperties kind={kind} />
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
        <label><span>表示形式</span><select value={meshRepresentation} onChange={(event) => setMeshRepresentation(event.target.value as MeshRepresentation)}><option value="surface">サーフェス</option><option value="surface-edges">サーフェス＋エッジ</option><option value="wireframe">ワイヤーフレーム</option></select></label>
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

function ViewMaterialPropertyEditor({ variant }: { variant: string }) {
  const kind = viewObjectKindByVariant[variant] ?? 'analysis-mesh'
  const meta = viewObjectKinds[kind]
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

  if (!meta.materialSurface) {
    return <div className="property-editor material-preview-first"><div className="property-editor-scroll-content"><MaterialPreview available={false} /><div className="sidebar-context-state"><MaterialSphereIcon size={22} /><b>マテリアル設定はありません</b><small>{meta.label}は専用の表示設定を使用します。</small></div></div></div>
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

function ViewTextPropertyEditor({ variant }: { variant: string }) {
  const kind = viewObjectKindByVariant[variant] ?? 'analysis-mesh'

  if (!viewObjectKinds[kind].textProperties) return null

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

function AutomationPropertyEditor({ tab }: { tab: SidebarTab }) {
  const [addedUnit, setAddedUnit] = useState<string | null>(null)
  if (tab.id === 'unit') {
    const units = [
      { label: 'シミュレーション', detail: '保存済み実行定義', icon: <Gauge size={14} /> },
      { label: 'ケース', detail: '対象セットへ追加', icon: <FolderOpen size={14} /> },
      { label: 'ビュー', detail: '可視化を生成', icon: <Boxes size={14} /> },
      { label: 'グラフ', detail: '図を生成', icon: <BarChart3 size={14} /> },
      { label: 'レポート', detail: '文書を生成', icon: <FileText size={14} /> },
      { label: '出力', detail: 'ファイルへ書き出し', icon: <FileOutput size={14} /> },
      { label: 'タグ', detail: 'ケースへ明示的に付与', icon: <Tag size={14} /> },
      { label: 'クリア', detail: '対象データを解放', icon: <Trash2 size={14} /> },
      { label: 'ループ', detail: '有限回の反復', icon: <RefreshCw size={14} /> },
      { label: '変数', detail: '以降のユニットへ束縛', icon: <Variable size={14} /> },
      { label: '数式', detail: '単位付き式を評価', icon: <Ruler size={14} /> },
      { label: '条件', detail: '式による分岐', icon: <Waypoints size={14} /> },
    ]
    return (
      <div className="automation-property-editor">
        <p>中央の挿入位置へドラッグするか、選択して追加します。</p>
        <div className="automation-unit-palette">
          {units.map((unit) => <button type="button" onClick={() => setAddedUnit(unit.label)} key={unit.label}><span>{unit.icon}</span><b>{unit.label}</b><small>{unit.detail}</small>{addedUnit === unit.label ? <CheckCircle2 size={12} /> : <Plus size={12} />}</button>)}
        </div>
        {addedUnit && <p className="property-editor-note" role="status"><CheckCircle2 size={12} />{addedUnit}ユニットを選択位置に追加しました。ワークスペース変更としてUndoできます。</p>}
      </div>
    )
  }

  if (tab.id === 'history') {
    return (
      <div className="automation-property-editor">
        <section className="automation-history-empty"><Clock3 size={22} /><b>実行履歴はありません</b><small>ドライランはファイルを書き込まず、対象と生成物を確認します。</small></section>
      </div>
    )
  }

  return (
    <div className="automation-property-editor">
      <section className="property-selection"><span><small>選択中のユニット</small><b>比較グラフ</b></span><button type="button">選択を解除</button></section>
      <details className="property-group" open>
        <summary><ChevronRight size={12} /><b>参照</b></summary>
        <div className="property-fields">
          <label><span>種類</span><input value="グラフ" readOnly /></label>
          <label><span>参照元</span><select defaultValue="workspace"><option value="workspace">ワークスペース項目</option><option value="template">テンプレート</option></select></label>
          <label><span>グラフ</span><select defaultValue="comparison"><option value="comparison">ケース比較</option></select></label>
          <label><span>リビジョン</span><input value="固定" readOnly /></label>
        </div>
      </details>
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

function OutlinerPanel({ variant, selectedNames, onSelect }: { variant: string; selectedNames: string[]; onSelect: (name: string, additive?: boolean) => void }) {
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
                <OutlinerRow depth={1} icon={<Square size={11} />} name="［元ファイルの部品名 01］" visible={isVisible('［元ファイルの部品名 01］')} selected={selectedNames.includes('［元ファイルの部品名 01］')} active={activeName === '［元ファイルの部品名 01］'} onSelect={onSelect} onVisibility={changeVisibility} />
                <OutlinerRow depth={1} icon={<Square size={11} />} name="［元ファイルの部品名 02］" visible={isVisible('［元ファイルの部品名 02］')} selected={selectedNames.includes('［元ファイルの部品名 02］')} active={activeName === '［元ファイルの部品名 02］'} onSelect={onSelect} onVisibility={changeVisibility} />
                <OutlinerRow depth={1} icon={<Grid2X2 size={11} />} name="［元ファイルの領域名］" visible={isVisible('［元ファイルの領域名］')} selected={selectedNames.includes('［元ファイルの領域名］')} active={activeName === '［元ファイルの領域名］'} onSelect={onSelect} onVisibility={changeVisibility} />
              </>
            ) : (
              <>
                <OutlinerRow depth={1} expanded={assemblyOpen} onToggle={() => setAssemblyOpen((open) => !open)} icon={<Boxes size={12} />} name="［元ファイルのアセンブリ名］" visible={isVisible('［元ファイルのアセンブリ名］')} selected={selectedNames.includes('［元ファイルのアセンブリ名］')} active={activeName === '［元ファイルのアセンブリ名］'} onSelect={onSelect} onVisibility={changeVisibility} />
                {assemblyOpen && <>
                  <OutlinerRow depth={2} icon={<Square size={11} />} name="［元ファイルの部品名 01］" visible={isVisible('［元ファイルの部品名 01］')} selected={selectedNames.includes('［元ファイルの部品名 01］')} active={activeName === '［元ファイルの部品名 01］'} onSelect={onSelect} onVisibility={changeVisibility} />
                  <OutlinerRow depth={2} expanded={partOpen} onToggle={() => setPartOpen((open) => !open)} icon={<Square size={11} />} name="［元ファイルの部品名 02］" visible={isVisible('［元ファイルの部品名 02］')} selected={selectedNames.includes('［元ファイルの部品名 02］')} active={activeName === '［元ファイルの部品名 02］'} onSelect={onSelect} onVisibility={changeVisibility} />
                  {partOpen && <OutlinerRow depth={3} icon={<Grid2X2 size={11} />} name="［元ファイルの領域名］" visible={isVisible('［元ファイルの領域名］')} selected={selectedNames.includes('［元ファイルの領域名］')} active={activeName === '［元ファイルの領域名］'} onSelect={onSelect} onVisibility={changeVisibility} />}
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

function ScreenCanvas({ scenario, draft, onDraftChange, onViewObjectSelect, onScreen }: { scenario: Scenario; draft: string; onDraftChange: (draft: string) => void; onViewObjectSelect: (name: string, additive?: boolean) => void; onScreen: (screen: ScreenId) => void }) {
  switch (scenario.screen) {
    case 'simulation': return <SimulationScreen onAutomation={() => onScreen('pipeline')} />
    case 'pipeline': return <PipelineScreen variant={scenario.variant} />
    case 'view': return <ViewScreen variant={scenario.variant} onViewObjectSelect={onViewObjectSelect} />
    case 'graph': return <GraphScreen variant={scenario.variant} />
    case 'report': return <ReportScreen variant={scenario.variant} />
    case 'chat': return <ChatScreen variant={scenario.variant} draft={draft} onDraftChange={onDraftChange} />
    case 'settings': return <SettingsScreen variant={scenario.variant} />
    case 'network': return <NetworkScreen variant={scenario.variant} onSettings={() => onScreen('settings')} />
    default: return null
  }
}

function SimulationScreen({ onAutomation }: { onAutomation: () => void }) {
  return <div className="centred-state"><Gauge size={34} /><span className="eyebrow">後続リリース</span><h2>シミュレーション実行はr1に含まれません</h2><p>既存ソルバーの結果を取り込み、自動化モードでビュー、グラフ、レポートを生成できます。</p><button className="primary-button" onClick={onAutomation}>自動化を開く</button></div>
}

function PipelineScreen({ variant }: { variant: string }) {
  const [flowState, setFlowState] = useState<'editing' | 'dry-run' | 'confirm-run' | 'running'>(variant === 'dry-run' ? 'dry-run' : variant === 'running' ? 'running' : 'editing')
  if (variant === 'empty') return <div className="centred-state"><Workflow size={34} /><h2>パイプラインが空です</h2><p>右側から処理を追加し、最初にドライランで対象ケースと生成物を確認します。</p><button className="primary-button"><Plus size={14} /> 最初のユニットを追加</button></div>
  const banner = flowState === 'running'
    ? <StatePanel tone="progress" title="パイプライン実行中" detail="閲覧は継続できます。現在のユニット境界までワークスペース編集は停止されます。" />
    : variant === 'failed'
      ? <StatePanel tone="error" title="1ケースが失敗しました" detail="板厚変更ケースがグラフで失敗しました。このケースのレポートと出力はスキップされ、他ケースは継続します。" />
      : flowState === 'dry-run'
        ? <StatePanel tone="info" title="ドライランのみ" detail="3ケース、生成物9件、ファイル書込0件。入れ子ユニットと対象数を以下に表示します。" />
        : null
  return (
    <div className="pipeline-canvas">
      {banner}
      <header className="pipeline-editor-header">
        <div><span className="eyebrow">パイプライン</span><b>レポート生成フロー</b><small>上から順に実行・対象セットを累積</small></div>
        <div className="pipeline-actions"><button disabled={flowState === 'running'} onClick={() => setFlowState('dry-run')}><Play size={14} /> ドライラン</button><button className="primary-button" disabled={flowState === 'running'} onClick={() => setFlowState('confirm-run')}><Play size={14} /> 実行</button>{flowState === 'running' && <button type="button" onClick={() => setFlowState('editing')}><X size={14} />ユニット境界で中止</button>}</div>
      </header>
      <div className="pipeline-units">
        <div className="pipeline-boundary pipeline-boundary-start"><span>開始</span><small>対象セット 0</small></div>
        <PipelineUnit icon={<FolderOpen />} title="ケースユニット" detail="3ケース選択" count="対象3" />
        <div className="bounded-zone"><header><RefreshCw size={14} /><b>ループ・material_variant</b><span>3反復・対象3</span></header><PipelineUnit icon={<Boxes />} title="ビューテンプレート" detail="技術資料・標準" count="対象3" /><PipelineUnit icon={<BarChart3 />} title="グラフテンプレート" detail="比較図" count="対象3" failed={variant === 'failed'} /></div>
        <PipelineUnit icon={<FileText />} title="レポートテンプレート" detail="設計レビュー" count="対象3" muted={variant === 'failed'} />
        <button className="pipeline-insert" type="button"><Plus size={13} /> ユニットを追加</button>
        <div className="pipeline-boundary pipeline-boundary-end"><span>完了</span><small>生成物を記録</small></div>
      </div>
      {variant === 'scope-confirmation' && <ModalCard title="対象セットを消去しますか？" detail="このユニットは3ケースに影響し、読み込み済みデータを解放します。書込済みファイルは削除しません。"><button>キャンセル</button><button className="danger-button">3ケースを消去</button></ModalCard>}
      {flowState === 'confirm-run' && <Dialog open onOpenChange={(open) => !open && setFlowState('editing')}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog compact-workflow-dialog"><header><span><small>実行前確認</small><b>ドライラン結果の対象で実行</b></span><button type="button" aria-label="実行確認を閉じる" onClick={() => setFlowState('editing')}><X size={15} /></button></header><section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>対象セット</b><small>各ユニットの累積対象数を確定済み</small></span></p><p><CheckCircle2 size={13} /><span><b>生成物</b><small>新しい実行フォルダーに保存・上書きなし</small></span></p><p><AlertTriangle size={13} /><span><b>編集ロック</b><small>実行中は閲覧のみ。中止はユニット境界</small></span></p></section><footer><button type="button" onClick={() => setFlowState('editing')}>キャンセル</button><button type="button" className="primary-button" onClick={() => setFlowState('running')}>実行を開始</button></footer></DialogContent></Dialog>}
    </div>
  )
}

function PipelineUnit({ icon, title, detail, count, failed, muted }: { icon: React.ReactNode; title: string; detail: string; count: string; failed?: boolean; muted?: boolean }) {
  return <div className={`pipeline-unit ${failed ? 'failed' : ''} ${muted ? 'muted' : ''}`}><span>{icon}</span><div><b>{title}</b><small>{detail}</small></div><em>{failed ? '失敗' : muted ? 'スキップ' : count}</em><ChevronRight size={14} /></div>
}

function ViewScreen({ variant, onViewObjectSelect }: { variant: string; onViewObjectSelect: (name: string, additive?: boolean) => void }) {
  const [playbackVisible, setPlaybackVisible] = useState(false)
  if (variant === 'empty') return <div className="centred-state"><Boxes size={34} /><h2>表示するケースがありません</h2><p>開始プリセットを選ぶか、ワークスペースへ結果ファイルをドロップします。</p><div className="button-row"><button className="primary-button">開始プリセット</button><button>テンプレート</button></div></div>
  if (variant === 'renderer-error') return <div className="centred-state error-state"><AlertTriangle size={34} /><h2>Omniverseレンダラーを開始できません</h2><p>バックエンドを利用できません。VTK軽量レンダラーは利用できます。</p><button className="primary-button">VTKで続ける</button></div>
  const panes = variant === 'split-two' ? 2 : variant === 'split-three' ? 3 : variant === 'split-four' ? 4 : 1
  return (
    <div className="view-canvas" onMouseEnter={() => setPlaybackVisible(true)} onMouseLeave={() => setPlaybackVisible(false)}>
      {variant === 'reduced' && <StatePanel tone="warning" title="表示形状を縮退しています" detail="画面は縮退形状を使用します。表示値とレポート計算は完全データを使用します。" />}
      {variant === 'unresolved-template' && <StatePanel tone="warning" title="テンプレートを一部解決できません" detail="形状とカメラは解決済みです。フィールド「応力」とマテリアル「スチールブルー」は未解決で、代替値を使用していません。" />}
      {variant === 'axis-error' && <StatePanel tone="error" title="指定した結果位置がありません" detail="要求されたモード8は存在しません。ビューはモード7のままで、近傍位置への丸めは行っていません。" />}
      <div className={`pane-grid panes-${panes}`}>
        {Array.from({ length: panes }).map((_, index) => <div className="view-pane" key={index}><Viewport paneIndex={index} compact={panes > 1} onObjectSelect={onViewObjectSelect} /></div>)}
      </div>
      {playbackVisible && <ViewPlaybackOverlay />}
    </div>
  )
}

function ViewPlaybackOverlay() {
  const [currentPercent, setCurrentPercent] = useState(0)
  const [hoverTime, setHoverTime] = useState<number | null>(null)
  const [hoverPercent, setHoverPercent] = useState(0)
  const percentFromPointer = (event: React.MouseEvent<HTMLInputElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect()
    return Math.min(100, Math.max(0, ((event.clientX - bounds.left) / bounds.width) * 100))
  }
  const handleTimelineMove = (event: React.MouseEvent<HTMLInputElement>) => {
    const percent = percentFromPointer(event)
    setHoverPercent(percent)
    setHoverTime((percent / 100) * 30)
  }
  const handleTimelineClick = (event: React.MouseEvent<HTMLInputElement>) => setCurrentPercent(percentFromPointer(event))
  return <div className="view-playback-overlay" role="toolbar" aria-label="ビュー再生コントロール"><button aria-label="先頭へ"><ChevronsLeft size={13} /></button><button aria-label="前へ"><ChevronLeft size={13} /></button><button className="playback-play" aria-label="再生"><Play size={13} /></button><button aria-label="次へ"><ChevronRight size={13} /></button><button aria-label="末尾へ"><ChevronsRight size={13} /></button><div className="playback-timeline"><input type="range" min="0" max="100" value={currentPercent} aria-label="結果位置" onMouseMove={handleTimelineMove} onMouseLeave={() => setHoverTime(null)} onClick={handleTimelineClick} onChange={(event) => setCurrentPercent(Number(event.target.value))} /><span className="playback-current-marker" style={{ left: `${currentPercent}%` }} aria-hidden="true" />{hoverTime !== null && <><span className="playback-hover-marker" style={{ left: `${hoverPercent}%` }} aria-hidden="true" /><span className="playback-hover-time" style={{ left: `${hoverPercent}%` }}>{formatPlaybackTime(hoverTime)}</span></>}</div><em>{formatPlaybackTime((currentPercent / 100) * 30)}</em><button className="playback-speed" type="button">1× <ChevronDown size={10} /></button></div>
}

function formatPlaybackTime(seconds: number) {
  const wholeSeconds = Math.floor(seconds)
  return `${Math.floor(wholeSeconds / 60)}:${String(wholeSeconds % 60).padStart(2, '0')}`
}

function GraphScreen({ variant }: { variant: string }) {
  if (variant === 'empty') return <div className="entry-grid"><button><SlidersHorizontal /><b>手動</b><span>物理量とケースを明示的に選択</span></button><button><Sparkles /><b>推奨</b><span>プレビューのみ・自動適用しない</span></button><button><MessageSquareText /><b>アシスタント提案</b><span>安全なグラフ定義・適用待ち</span></button></div>
  if (variant === 'no-points') return <div className="centred-state error-state"><AlertTriangle size={34} /><h2>選択条件に一致する点がありません</h2><p>条件「選択領域かつフィールドあり」によって選択が空になりました。空グラフは描画していません。</p><button>選択条件を編集</button></div>
  return <div className="graph-canvas"><div className="graph-heading"><div><span className="eyebrow">グラフ</span><h2>物理量の比較</h2><p>ケース：明示選択・集約方法：未選択</p></div></div><div className="chart-frame"><span className="y-label">物理量A［単位未宣言］</span><div className="chart-grid"><svg viewBox="0 0 600 260" role="img" aria-label="値を含まないグラフ構成モック"><polyline points="40,205 180,150 320,170 460,92 560,110" /><circle cx="40" cy="205" r="5" /><circle cx="180" cy="150" r="5" /><circle cx="320" cy="170" r="5" /><circle cx="460" cy="92" r="5" /><circle cx="560" cy="110" r="5" /></svg><span className="mock-stamp">レイアウトのみ・解析値なし</span></div><span className="x-label">ケース選択</span></div><div className="provenance-row"><span>物理量：データセット</span><span>単位：未宣言</span><span>欠損ケース：データなしとして表示</span></div></div>
}

function ReportScreen({ variant }: { variant: string }) {
  if (variant === 'blank') return <div className="report-choices"><h2>レポートを作成</h2><p>テンプレートを選ぶか、意図的に空文書から始めます。</p><div>{['学術論文', '技術メモ', '1ページ要約', '設計レビューデッキ', 'ケース間比較', '空文書'].map((item) => <button key={item}><FileText /><b>{item}</b><small>サンプル</small></button>)}</div></div>
  const state = variant === 'exporting' ? <StatePanel tone="progress" title="自己完結HTMLを出力中" detail="同じ対象への二重出力は停止されています。キャンセルは引き続き利用できます。" /> : variant === 'export-error' ? <StatePanel tone="error" title="HTML出力を利用できません" detail="出力先フォルダーは読取専用です。前回の成果物は上書きされていません。" /> : null
  return <div className="report-canvas">{state}<article className="report-page"><span className="eyebrow">設計レビュー・モックアップ</span><h1>解析レポート表題</h1><p className="lede">このプレビューはレイアウト用の仮要素のみを含み、解析結果について何も主張しません。</p><section><div className="report-image"><Boxes /><span>ビュー・結果値なし</span></div><div><h2>判明事項</h2><p>利用可能な場合、データセットの来歴、宣言単位、アルゴリズムを表示します。</p><h2>未判明事項</h2><p>欠損値は欠損のまま維持し、明示します。</p></div></section><footer>入力識別情報・ワークスペース版・アルゴリズム版</footer></article>{variant === 'exporting' && <button className="floating-cancel"><X size={14} /> 出力をキャンセル</button>}</div>
}

function ChatScreen({ variant, draft, onDraftChange }: { variant: string; draft: string; onDraftChange: (draft: string) => void }) {
  if (variant === 'empty') {
    return (
      <div className="chat-canvas">
        <div className="chat-empty">
          <Sparkles size={30} />
          <h2>ワークスペースについて尋ねる</h2>
          <p>質問、操作、レポート構成を同じチャットで続けられます。</p>
          <div className="chat-suggestions">
            {['利用可能な物理量を一覧にする', 'このテンプレートの未解決項目を確認する', 'パイプラインをドライランする'].map((item) => <button key={item}>{item}<ChevronRight size={13} /></button>)}
          </div>
        </div>
        <ChatComposer draft={draft} onDraftChange={onDraftChange} />
      </div>
    )
  }

  return (
    <div className="chat-canvas">
      <ConversationThread variant={variant} />
      <ChatComposer draft={draft} onDraftChange={onDraftChange} />
      {variant === 'outbound-request' && <ModalCard title="外部要求を1回許可しますか？" detail="検索語：「公式ソルバー形式文書」。送信しない情報：ファイル名、形状、値、ワークスペース情報。"><button>オフラインを維持</button><button className="primary-button">今回だけ許可</button></ModalCard>}
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
          <header><span className="chat-role-mark"><Sparkles size={14} /></span><b>SOLVIA</b><small>ローカルモデル</small></header>
          <div className="chat-turn-body">
            <p>物理量一覧は、読み込んだデータセットから取得してここに表示します。値や単位は、実データで確認できるまで推測しません。</p>
            <p>読み込み後は、物理量名、種類、宣言単位、欠損の有無、来歴を順に確認できます。</p>
            <aside className="chat-safety-note"><ShieldCheck size={14} /><span><b>操作は行っていません</b><small>ワークスペースは変更されていません。</small></span></aside>
            <footer className="chat-response-actions"><button><Save size={13} /> コピー</button><button><RefreshCw size={13} /> 再生成</button></footer>
          </div>
        </article>
        {variant === 'assistant-error' && <StatePanel tone="error" title="コマンド送信前にアシスタントが失敗しました" detail="コマンドは実行されず、ワークスペースは変更されていません。ローカルモデルを利用できませんでした。" />}
      </div>
    </div>
  )
}

function AssistantDrawer({ draft, onDraftChange, onClose, onOpenChat }: { draft: string; onDraftChange: (draft: string) => void; onClose: () => void; onOpenChat: () => void }) {
  return (
    <aside className="assistant-drawer" aria-label="アシスタントチャット">
      <header className="assistant-drawer-header">
        <div><span className="assistant-mark"><Sparkles size={14} /></span><span><b>アシスタント</b><small>現在のチャット</small></span></div>
        <div>
          <button type="button" className="assistant-open-chat" onClick={onOpenChat}>チャットで開く<ArrowUpRight size={13} /></button>
          <button type="button" aria-label="アシスタントを閉じる" onClick={onClose}><X size={15} /></button>
        </div>
      </header>
      <ConversationThread compact />
      <ChatComposer draft={draft} onDraftChange={onDraftChange} />
    </aside>
  )
}

function ChatComposer({ draft, onDraftChange }: { draft: string; onDraftChange: (draft: string) => void }) {
  const [model, setModel] = useState('local')
  const [effort, setEffort] = useState('standard')
  const [permission, setPermission] = useState<'search' | 'research' | null>(null)
  return <div className="chat-composer"><textarea rows={2} value={draft} onChange={(event) => onDraftChange(event.target.value)} placeholder="ワークスペースへの質問または操作" /><div><button aria-label="ファイルを追加"><Plus size={16} /></button><label className="chat-inline-select"><span className="sr-only">モデル</span><select value={model} onChange={(event) => setModel(event.target.value)}><option value="local">ローカルモデル</option><option value="remote" disabled>外部モデル・未構成</option></select></label><label className="chat-inline-select"><span className="sr-only">推論の深さ</span><select value={effort} onChange={(event) => setEffort(event.target.value)}><option value="brief">簡潔</option><option value="standard">標準</option><option value="deep">詳細</option></select></label><button type="button" className="chat-search-status" onClick={() => setPermission('search')}><ShieldCheck size={11} />検索オフ</button><button type="button" className="chat-research-button" onClick={() => setPermission('research')}>詳細調査</button><button className="chat-send" aria-label="送信" disabled={!draft.trim()}><Play size={14} /></button></div><small>回答は誤る可能性があります。解析値・単位・来歴は元データで確認してください。</small>
    <Dialog open={permission !== null} onOpenChange={(open) => !open && setPermission(null)}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog outbound-review-dialog"><header><span><small>外部通信</small><b>{permission === 'research' ? '詳細調査の許可' : 'Web検索の許可'}</b></span><button type="button" aria-label="外部通信確認を閉じる" onClick={() => setPermission(null)}><X size={15} /></button></header><section className="outbound-review"><label><span>送信する検索語</span><textarea rows={2} value={draft.trim() || '［検索語を入力してください］'} readOnly /></label><label><span>送信しない情報</span><input value="ケース名・ファイルパス・形状・解析値" readOnly /></label><label><span>許可ホスト</span><input value="登録なし" readOnly /></label>{permission === 'research' && <><label><span>予定要求数</span><input value="未取得" readOnly /></label><label><span>費用見積</span><input value="未取得" readOnly /></label></>}</section><p className="workflow-trust-note blocked"><AlertTriangle size={13} />許可ホストと{permission === 'research' ? '要求数・費用見積' : '正確な検索語'}を確認できるまで送信しません。</p><footer><button type="button" onClick={() => setPermission(null)}>オフラインを維持</button><button type="button" className="primary-button" disabled>今回だけ許可</button></footer></DialogContent></Dialog>
  </div>
}

function SettingsScreen({ variant }: { variant: string }) {
  const applicationCategories = ['全般', '表示とアクセシビリティ', '単位', 'ネットワーク', '更新', '診断とサポート']
  const workspaceCategories = ['ワークスペース', '成分座標系', 'レンダラー', 'アートスタイル', 'アシスタント', 'ライブラリ']
  const [category, setCategory] = useState(variant === 'support-bundle' ? '診断とサポート' : '単位')
  const [supportOpen, setSupportOpen] = useState(variant === 'support-bundle')

  return (
    <div className="settings-canvas">
      {variant === 'invalid' && <StatePanel tone="error" title="設定を拒否しました" detail="表示単位「unknown-unit」は無効です。直前の表示単位を維持しています。" />}
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
        <SettingsCategoryPanel category={category} onSupportBundle={() => setSupportOpen(true)} />
      </section>
      <Dialog open={supportOpen} onOpenChange={setSupportOpen}><DialogOverlay className="modal-backdrop" /><DialogContent className="workflow-dialog support-bundle-dialog"><header><span><small>診断とサポート</small><b>サポートバンドルの内容を確認</b></span><button type="button" aria-label="サポートバンドルを閉じる" onClick={() => setSupportOpen(false)}><X size={15} /></button></header><section className="workflow-check-list"><p><CheckCircle2 size={13} /><span><b>含める</b><small>ローカルログ、製品版、設定、失敗理由コード</small></span></p><p><AlertTriangle size={13} /><span><b>確認が必要</b><small>ケース名と入力ファイルのパス</small></span></p><p><ShieldCheck size={13} /><span><b>含めない</b><small>形状、フィールド値、測定値、参考資料の本文</small></span></p></section><p className="workflow-trust-note"><HardDrive size={13} />作成先はローカルです。送信は別操作で、送信先と内容を再確認します。</p><footer><button type="button" onClick={() => setSupportOpen(false)}>キャンセル</button><button type="button" className="primary-button" onClick={() => setSupportOpen(false)}>ローカルに作成</button></footer></DialogContent></Dialog>
    </div>
  )
}

function SettingsCategoryPanel({ category, onSupportBundle }: { category: string; onSupportBundle: () => void }) {
  if (category === '単位') return <><h2>宣言単位と表示単位</h2><p>ファイル内容を信頼できる単位宣言として扱うことはありません。</p><div className="settings-fields"><label>物理量の種類<Select defaultValue="stress"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="stress">応力</SelectItem></SelectContent></Select></label><label>宣言単位<Select defaultValue="undeclared"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="undeclared">未宣言</SelectItem></SelectContent></Select></label><label>表示単位<Select defaultValue="same"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="same">宣言単位と同じ</SelectItem></SelectContent></Select></label></div><div className="setting-note"><ShieldCheck size={15} />単位を宣言するまで変換は無効です。</div><div className="setting-note"><ShieldCheck size={15} />大きさ、フィールド名、書き出したソルバーのいずれからも、ファイルから単位を推測しません。</div><Button className="primary-button">設定を保存</Button></>
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

function NetworkScreen({ variant, onSettings }: { variant: string; onSettings: () => void }) {
  if (variant === 'offline') return <div className="centred-state"><ShieldCheck size={35} /><h2>ネットワークアクセスはオフです</h2><p>検索とリモートアシスタント要求は実行しません。要求ごとの許可は設定画面で付与できます。</p><button onClick={onSettings}>権限設定を開く</button></div>
  return <div className="network-canvas">{variant === 'refused' && <StatePanel tone="error" title="外部要求を拒否しました" detail="ホスト：example.invalid・要求：文書検索・結果：未送信。" />}<div className="network-summary"><div><Network /><span><small>既定</small><b>オフライン</b></span></div><div><Globe2 /><span><small>許可ホスト</small><b>なし</b></span></div><div><HardDrive /><span><small>監査保存先</small><b>ローカル</b></span></div></div><section className="audit-log"><header><div><span className="eyebrow">ローカル監査</span><h2>外部要求</h2></div><button>監査記録を出力</button></header><div className="audit-row"><span>未送信</span><b>文書検索</b><small>権限なし・端末外へ送信した情報なし</small></div><div className="audit-row"><span>ローカル</span><b>アシスタント評価</b><small>ネットワーク依存なし</small></div></section></div>
}

function InstructionBar({ draft, onDraftChange, onOpen }: { draft: string; onDraftChange: (draft: string) => void; onOpen: () => void }) {
  return <div className="instruction-bar"><Sparkles size={15} /><Input className="h-auto border-0 bg-transparent p-0 text-[10px] shadow-none focus-visible:ring-0" value={draft} onChange={(event) => onDraftChange(event.target.value)} placeholder="自然言語で操作 — 同じチャットへ送信" /><kbd>Ctrl K</kbd><Button variant="ghost" size="icon" type="button" aria-label="チャットを開く" onClick={onOpen}><MessageSquareText size={14} /></Button></div>
}

function StatePanel({ tone, title, detail }: { tone: 'info' | 'progress' | 'warning' | 'error'; title: string; detail: string }) {
  const Icon = tone === 'error' || tone === 'warning' ? AlertTriangle : tone === 'progress' ? CircleDashed : ShieldCheck
  return <div className={`state-panel ${tone}`}><Icon size={17} /><div><b>{title}</b><span>{detail}</span></div></div>
}

function ModalCard({ title, detail, children }: { title: string; detail: string; children: React.ReactNode }) {
  return <Dialog><DialogOverlay className="modal-backdrop" /><DialogContent className="modal-card"><AlertTriangle size={24} /><h2>{title}</h2><p>{detail}</p><DialogFooter>{children}</DialogFooter></DialogContent></Dialog>
}

function ScenarioCatalog({ selected, onSelect }: { selected: Scenario; onSelect: (scenario: Scenario) => void }) {
  return <aside className="scenario-catalog"><header><div><span className="eyebrow">仕様優先</span><h2>画面バリエーション</h2></div><span>{scenarios.length}</span></header><div className="scenario-current"><b>{selected.label}</b><p>{selected.intent}</p><code>{selected.id}</code></div><nav>{screenOrder.map((screen) => <section key={screen}><h3>{screenNames[screen]}<span>{scenarios.filter((item) => item.screen === screen).length}</span></h3>{scenarios.filter((item) => item.screen === screen).map((scenario) => <button className={selected.id === scenario.id ? 'active' : ''} onClick={() => onSelect(scenario)} key={scenario.id}><span>{scenario.label}</span><ChevronRight size={12} /></button>)}</section>)}</nav></aside>
}
