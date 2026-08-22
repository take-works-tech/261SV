"""The UI mockup must expose every screen state committed in specs/11_ui.md.

The mockup is a design artefact, not product code, so this test checks its scenario
catalogue rather than pretending that a screenshot proves behaviour.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "mockups" / "ui" / "lib" / "screen-catalog.json"
CHAT_PAGE = ROOT / "mockups" / "ui" / "app" / "page.tsx"
CHAT_STYLES = ROOT / "mockups" / "ui" / "app" / "globals.css"
THREE_VIEWPORT = ROOT / "mockups" / "ui" / "components" / "workspace" / "viewport.tsx"
THREE_SCENE = ROOT / "mockups" / "ui" / "components" / "workspace" / "scene.tsx"
MATERIAL_PREVIEW = ROOT / "mockups" / "ui" / "components" / "workspace" / "material-preview.tsx"
MATERIAL_SPHERE_ICON = ROOT / "mockups" / "ui" / "components" / "icons" / "material-sphere-icon.tsx"
MATERIAL_THUMBNAIL_DIR = ROOT / "mockups" / "ui" / "public" / "materials"
VIEW_SCHEMA = ROOT / "specs" / "contracts" / "schema" / "CT-004.json"
MATERIAL_SCHEMA = ROOT / "specs" / "contracts" / "schema" / "CT-011.json"
MOCKUP_THUMBNAILS = ROOT / "mockups" / "ui" / "public" / "thumbnails"

UI_SPEC = ROOT / "specs" / "11_ui.md"

# `view.object-analysis-mesh` … `view.object-effect` in the spec table stands for one row per taxonomy
# type. The ellipsis is expanded here because the taxonomy itself is enumerated in prose above it, and
# a table row per type would repeat that list - the duplication P7 forbids. Each name below must appear
# in the taxonomy section, which the next check asserts.
ELLIPSIS_RANGES = {
    "view.object-analysis-mesh": (
        "view.object-analysis-mesh",
        "view.object-reference-mesh",
        "view.object-scalar-field",
        "view.object-vector-field",
        "view.object-trajectory",
        "view.object-point-cloud",
        "view.object-annotation",
        "view.object-effect",
    ),
    "view.library-collapsed": (
        "view.library-collapsed",
        "view.library-one-row",
        "view.library-expanded",
        "view.library-searching",
        "view.library-selected",
        "view.library-narrow",
    ),
}


def expected_scenarios() -> set[str]:
    """The required states, read from `specs/11_ui.md` rather than restated here.

    This set used to be a hand-written literal, and the coverage test compared the catalogue against
    it. Both were copies of one list, so a state the specification required and neither copy carried
    was undetectable: the check reported coverage while measuring only that two copies agreed. The
    spec table is now the single source, and this function is the reader.
    """
    section = UI_SPEC.read_text(encoding="utf-8").split("### Required screen states", 1)
    assert len(section) == 2, "specs/11_ui.md no longer carries a 'Required screen states' table"
    required: set[str] = set()
    for line in section[1].splitlines():
        if not line.startswith("|"):
            continue
        first = line.split("|")[1]
        names = re.findall(r"`([a-z]+\.[a-z0-9-]+)`", first)
        if not names:
            continue
        if "…" in first and names[0] in ELLIPSIS_RANGES:
            required.update(ELLIPSIS_RANGES[names[0]])
        else:
            required.update(names)
    assert len(required) > 40, f"only {len(required)} states parsed; the table shape changed"
    return required


EXPECTED_SCENARIOS = expected_scenarios()


def test_the_taxonomy_states_named_by_an_ellipsis_are_real_types() -> None:
    """The expansion above must not drift from the taxonomy the spec enumerates."""
    spec = UI_SPEC.read_text(encoding="utf-8")
    taxonomy = spec[spec.index("### View object taxonomy") : spec.index("## Workspace list")]
    for name in ELLIPSIS_RANGES["view.object-analysis-mesh"]:
        japanese = {
            "analysis-mesh": "解析メッシュ",
            "reference-mesh": "参照メッシュ",
            "scalar-field": "スカラー場",
            "vector-field": "ベクトル場",
            "trajectory": "流線・軌跡",
            "point-cloud": "点群",
            "annotation": "テキスト・注釈",
            "effect": "エフェクト",
        }[name.removeprefix("view.object-")]
        assert japanese in taxonomy, f"{name} names a type the taxonomy does not define"


def load_catalog() -> list[dict[str, object]]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))["scenarios"]


def test_ui_mockup_catalog_covers_every_specified_screen_state() -> None:
    scenarios = load_catalog()
    ids = {str(item["id"]) for item in scenarios}
    assert ids == EXPECTED_SCENARIOS


def test_every_mockup_scenario_is_deep_linkable_and_explains_its_spec_intent() -> None:
    scenarios = load_catalog()
    for item in scenarios:
        scenario_id = str(item["id"])
        screen, variant = scenario_id.split(".", maxsplit=1)
        assert item["screen"] == screen
        assert item["variant"] == variant
        assert str(item["label"]).strip()
        assert str(item["intent"]).strip()
        assert item["href"] == f"?screen={screen}&variant={variant}"


def test_scenario_labels_and_intents_are_japanese_first() -> None:
    scenarios = load_catalog()
    japanese = re.compile(r"[ぁ-んァ-ヶ一-龠]")
    for item in scenarios:
        assert japanese.search(str(item["label"])), item["id"]
        assert japanese.search(str(item["intent"])), item["id"]


def test_chat_uses_a_single_column_document_flow_instead_of_message_bubbles() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "className={`chat-thread ${compact ? 'assistant-drawer-thread' : ''}`}" in page
    assert 'className="chat-turn chat-turn-user"' in page
    assert 'className="chat-turn chat-turn-assistant"' in page
    assert 'className="chat-composer"' in page
    assert 'className="user-message"' not in page
    assert 'className="assistant-message"' not in page
    assert ".user-message" not in styles
    assert ".assistant-message" not in styles


def test_work_areas_offer_one_shared_conversation_in_a_right_overlay_drawer() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "const [sharedDraft, setSharedDraft] = useState('')" in page
    assert "function ConversationThread(" in page
    assert "function AssistantDrawer(" in page
    assert 'className="assistant-drawer"' in page
    assert 'aria-label="アシスタントを閉じる"' in page
    assert '>チャットで開く<' in page
    assert "onScreen('chat')" in page
    assert "assistantOpen ? null : <InstructionBar" in page
    assert "<ConversationThread compact />" in page
    assert "<ConversationThread variant={variant}" in page
    assert 'value={draft}' in page
    assert 'onChange={(event) => onDraftChange(event.target.value)}' in page
    assert ".assistant-drawer {" in styles
    assert "position: absolute" in styles
    assert "right: 0" in styles
    assert ".assistant-drawer-thread" in styles
    assert ".assistant-drawer .chat-composer" in styles


def test_dataset_components_live_in_the_view_outliner_not_the_left_sidebar() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert '<SidebarSection title="部品"' not in page
    assert "function OutlinerPanel" in page
    assert 'className="outliner-panel"' in page
    assert 'className="outliner-tree"' in page
    assert "<button>データセット" not in page
    assert ".outliner-header button" not in styles
    assert ".outliner-panel { min-height: 248px;" in styles
    assert re.search(r"\.outliner-panel\s*\{[^}]*background: #f7f9fa", styles)
    assert re.search(r"\.outliner-header\s*\{[^}]*background: #edf2f5", styles)
    assert ".outliner-row { --tree-indent: 0px; position: relative; height: 27px;" in styles
    assert ".outliner-row b { overflow: hidden; padding-left: 2px; font-size: 10px;" in styles
    assert re.search(r"\.outliner-row\.selected\.active\s*\{[^}]*background: #dceafe", styles)
    assert re.search(r"\.outliner-row\.selected\.active\s*\{[^}]*box-shadow: inset 2px 0 var\(--blue\)", styles)
    assert 'className="outliner-hint"' not in page
    assert "Shift：子も切替" not in page
    assert "Ctrl：枝を分離" not in page
    assert ".outliner-hint" not in styles
    assert "view.outliner-flat" in EXPECTED_SCENARIOS
    assert "view.outliner-empty" in EXPECTED_SCENARIOS


def test_shell_preserves_the_reference_workspace_navigation_and_panel_controls() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    for menu in ("ファイル", "編集", "表示", "フィルタ", "ツール", "ヘルプ"):
        assert f"'{menu}'" in page
    assert ">ワークスペース一覧<" in page
    assert "ケース一覧" not in page
    assert 'className="work-toolbar"' in page
    assert 'className="panel-toggle panel-toggle-left"' in page
    assert 'className="panel-toggle panel-toggle-right"' in page
    assert page.count("<PanelLeft ") == 1
    assert page.count("<PanelRight ") == 1
    assert page.index('className="panel-toggle panel-toggle-left"') < page.index('className="area-tabs"')
    assert page.index('className="area-tabs"') < page.index('className="panel-toggle panel-toggle-right"')
    assert 'className="sidebar-title"' not in page
    assert ".sidebar-title" not in styles
    assert "<b>{chat ? '会話' : 'ワークスペース'}</b>" not in page
    assert "ビューのアセット" not in page
    assert "ビューのオブジェクト" not in page
    assert ".outliner-panel" in styles
    assert "background: #303337" not in styles


def test_settings_is_a_dedicated_page_without_workspace_sidebars_or_composer() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    shell = page[page.index("function ProductShell(") : page.index("function WorkspaceHome(")]
    settings_branch = shell[shell.index(") : isSettings ? (") : shell.index(") : (", shell.index(") : isSettings ? (") + 1)]
    settings_screen = page[page.index("function SettingsScreen(") : page.index("function NetworkScreen(")]

    assert "const isSettings = scenario.screen === 'settings'" in shell
    assert "!isHome && !isSettings && <div className=\"work-toolbar\"" in shell
    assert 'className="settings-page"' in settings_branch
    assert "<SettingsScreen variant={scenario.variant} />" in settings_branch
    assert "LeftSidebar" not in settings_branch
    assert "RightSidebar" not in settings_branch
    assert "InstructionBar" not in settings_branch
    assert "WorkAreaBar" not in settings_branch
    assert "AssetLibraryShelf" not in settings_branch
    assert "アプリ全体" in settings_screen
    assert "現在のワークスペース" in settings_screen
    # Membership, not a frozen literal. The previous version pinned the exact array, so adding the
    # command list the spec requires (the keyboard scheme) failed a test about sidebars - the assertion
    # was really "nobody may add a Settings category", which is not what it claimed to check.
    for required in ("全般", "表示とアクセシビリティ", "ショートカット", "単位", "ネットワーク", "更新", "診断とサポート"):
        assert f"'{required}'" in settings_screen, f"Settings is missing the {required} category"
    assert "['ワークスペース', '成分座標系', 'レンダラー'" in settings_screen
    assert ".settings-page {" in styles
    assert "grid-template-columns: 210px minmax(0, 1fr)" in styles


def test_chat_left_sidebar_returns_to_conversation_history() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    left_sidebar = page[page.index("function LeftSidebar(") : page.index("function SidebarSection(")]

    assert "const chat = screen === 'chat'" in left_sidebar
    assert "className=\"conversation-list\"" in left_sidebar
    assert "<WorkspaceSourceSections />" in left_sidebar
    assert "className=\"permanent-search\"" in left_sidebar
    assert "conversation-search" in left_sidebar
    assert "新しいチャット" in left_sidebar
    assert "conversationQuery" in left_sidebar


def test_chat_history_is_available_from_the_centre_header_without_changing_sidebar_grammar() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "function ChatHeader(" not in page
    composer = page[page.index("function ChatComposer(") : page.index("function SettingsScreen(")]
    assert "ローカルモデル" in composer
    assert "検索オフ" in composer


def test_chat_does_not_add_a_secondary_conversation_sidebar() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "conversation-rail-toggle" not in page
    assert "conversation-rail-open" not in page
    assert "conversation-sidebar ${open ? 'open' : 'collapsed'}" not in page
    assert "conversationRailOpen" not in page
    assert "function ConversationSidebar(" not in page
    assert ".chat-workbench.conversation-rail-open" not in styles


def test_automation_is_the_rightmost_work_mode_and_owns_pipeline_navigation() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    area_tabs = page[page.index("const areaTabs") : page.index("type SidebarTab")]
    left_sidebar = page[page.index("function LeftSidebar(") : page.index("function SidebarSection(")]
    work_headers = page[page.index("const workItemHeaderByScreen") : page.index("type LibrarySource")]

    assert "{ id: 'pipeline', label: '自動化'" in area_tabs
    assert "{ id: 'chat', label: 'チャット'" not in area_tabs
    assert area_tabs.index("label: 'シミュレーション'") < area_tabs.index("label: 'ビュー'")
    assert area_tabs.index("label: 'ビュー'") < area_tabs.index("label: 'グラフ'")
    assert area_tabs.index("label: 'グラフ'") < area_tabs.index("label: 'レポート'")
    assert area_tabs.index("label: 'レポート'") < area_tabs.index("label: '自動化'")
    assert 'className={isChat ? \'chat-global-button active\' : \'chat-global-button\'}' in page
    assert 'className="work-toolbar-utilities"' in page
    assert "pipeline: '自動化'" in page
    assert "const automation = screen === 'pipeline'" not in left_sidebar
    assert 'className="automation-sidebar-layout"' not in left_sidebar
    assert 'className="automation-pipeline-navigation"' not in left_sidebar
    assert 'className="automation-source-navigation"' not in left_sidebar
    assert 'placeholder="パイプラインを検索"' not in left_sidebar
    assert '<SidebarSection title="パイプライン一覧"' not in left_sidebar
    assert '<SidebarSection title="パイプライン"' not in left_sidebar
    assert "onClick={() => onScreen('pipeline')}" not in left_sidebar
    assert "pipeline: { title: '自動化'" in work_headers
    assert "createLabel: '新規パイプライン'" in work_headers
    assert "新規自動化" not in page

    assert ".automation-sidebar-layout" not in styles
    assert ".automation-pipeline-navigation" not in styles
    assert ".automation-source-navigation" not in styles
    assert ".chat-mode-button" not in styles
    assert ".work-toolbar-utilities" in styles


def test_every_saved_work_item_switches_from_the_shared_centre_header() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    work_headers = page[page.index("const workItemHeaderByScreen") : page.index("type LibrarySource")]

    for screen, title, item in (
        ("simulation", "シミュレーション", "基準シミュレーション"),
        ("view", "ビュー", "標準ビュー"),
        ("graph", "グラフ", "ケース比較グラフ"),
        ("report", "レポート", "設計レビューレポート"),
        ("pipeline", "自動化", "レポート生成フロー"),
    ):
        assert f"{screen}: {{ title: '{title}'" in work_headers
        assert item in work_headers

    assert 'className="work-item-selector"' in work_headers
    assert 'className="work-item-selector-kind"' in work_headers
    assert 'aria-label={`${itemHeader.itemLabel}を選択`}' in work_headers
    assert 'aria-haspopup="listbox"' in work_headers
    assert 'className="work-item-popover"' in work_headers
    assert 'placeholder={`${itemHeader.itemLabel}を検索`}' in work_headers
    assert 'role="listbox"' in work_headers
    assert 'aria-selected={selectedItem === item}' in work_headers
    assert "WorkItemPreview" in work_headers
    assert "work-item-preview" in work_headers
    assert "screen === 'view'" in work_headers
    assert "screen !== 'graph'" in work_headers
    assert "screen === 'view' || screen === 'graph' || screen === 'report'" in work_headers
    assert "work-item-popover-preview" in work_headers
    assert "previewIndex" in work_headers
    assert "previewTop" in work_headers
    assert "getBoundingClientRect" in work_headers
    assert "style={{ top:" in work_headers
    assert "ビュー静止プレビュー" not in work_headers
    assert "グラフ静止プレビュー" not in work_headers
    work_item_styles = styles[styles.index(".work-item-popover") : styles.index(".eyebrow")]
    assert "overflow-x: auto" not in work_item_styles
    assert 'aria-label={`${item}の操作`}' in work_headers
    assert 'className="work-area-static"' in work_headers
    assert ".work-item-selector" in styles
    assert ".work-item-popover" in styles
    assert ".work-item-option" in styles
    preview_styles = styles[styles.index(".work-item-popover-preview") : styles.index(".work-item-preview-content")]
    assert "z-index: 1000" in preview_styles
    assert "transform: translateY(-50%)" in preview_styles


def test_non_chat_right_sidebar_uses_a_vertical_icon_rail_with_a_visible_active_label() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    view_tabs = page[page.index("  view: ["):page.index("  graph: [")]

    assert 'className="sidebar-editor"' in page
    assert 'className="sidebar-tab-rail"' in page
    assert 'role="tablist"' in page
    assert 'aria-orientation="vertical"' in page
    assert 'role="tabpanel"' in page
    assert 'aria-selected={active}' in page
    assert 'data-tooltip={tab.label}' in page
    assert "selectedTab.label" in page
    assert "sidebar-tab-panel-title" in page
    assert "<small>{screenNames[screen]}</small>" not in page
    assert "rightSidebarTabs" in page
    assert 'className="right-tabs"' not in page
    assert ".right-tabs" not in styles
    assert "grid-template-columns: 42px minmax(0, 1fr)" in styles
    assert ".sidebar-tab-rail" in styles
    assert ".sidebar-tab-button.active" in styles
    assert ".sidebar-tab-panel-title" in styles
    assert "scope?: 'view' | 'selection'" in page
    for tab_id in ("overall", "rendering", "background", "output"):
        assert f"id: '{tab_id}'" in view_tabs
        tab_definition = view_tabs[view_tabs.index(f"id: '{tab_id}'"):view_tabs.index(f"id: '{tab_id}'") + 240]
        assert "scope: 'view'" in tab_definition
    for tab_id in ("objects", "text", "materials"):
        assert f"id: '{tab_id}'" in view_tabs
        tab_definition = view_tabs[view_tabs.index(f"id: '{tab_id}'"):view_tabs.index(f"id: '{tab_id}'") + 280]
        assert "scope: 'selection'" in tab_definition
    ordered_tabs = [view_tabs.index(f"id: '{tab_id}'") for tab_id in ("overall", "rendering", "background", "output", "objects", "text", "materials")]
    assert ordered_tabs == sorted(ordered_tabs)
    assert 'className="sidebar-tab-scope-separator" aria-hidden="true"' in page
    assert "startsSelectionGroup" in page
    assert "scopeLabel ? `${scopeLabel}：${tab.label}` : tab.label" in page
    assert ".sidebar-tab-scope-separator" in styles
    assert page.index("{screen === 'view' && <OutlinerPanel") < page.index('className="sidebar-editor"')


def test_view_playback_controls_float_over_the_canvas_on_hover() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    view_screen = page[page.index("function ViewScreen(") : page.index("function GraphScreen(")]
    assert "view-playback-overlay" in view_screen
    assert "onMouseEnter" in view_screen
    assert "onMouseLeave" in view_screen
    assert "role=\"toolbar\"" in view_screen
    assert "時間軸" not in view_screen
    assert "playback-hover-time" in view_screen
    assert "playback-hover-marker" in view_screen
    assert "playback-current-marker" in view_screen
    assert "currentPercent" in view_screen
    assert "onClick={handleTimelineClick}" in view_screen
    assert "onMouseMove" in view_screen
    assert "getBoundingClientRect" in view_screen
    assert "clientX" in view_screen
    assert "formatPlaybackTime" in view_screen
    assert ".view-playback-overlay" in styles
    marker_css = styles[styles.index(".playback-hover-marker") : styles.index(".playback-hover-marker") + 300]
    assert "width: 8px" in marker_css
    assert "height: 8px" in marker_css
    assert "border: 0" in marker_css
    assert "position: absolute" in styles[styles.index(".view-playback-overlay") : styles.index(".view-playback-overlay") + 240]


def test_three_viewport_keeps_camera_stable_during_panel_resize() -> None:
    scene = (ROOT / "mockups" / "ui" / "components" / "workspace" / "scene.tsx").read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "<Bounds fit clip observe" not in scene
    assert "<Bounds fit clip margin" in scene
    assert ".three-viewport" in styles
    assert "contain: strict" in styles[styles.index(".three-viewport") : styles.index(".three-viewport") + 180]


def test_simulation_view_graph_report_headers_offer_only_named_new_item_creation() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    header = page[page.index("const workItemHeaderByScreen") : page.index("type LibrarySource")]

    assert "simulation: { title: 'シミュレーション'" in header
    assert "view: { title: 'ビュー'" in header
    assert "view: { title: '現在のビュー'" not in header
    assert "graph: { title: 'グラフ'" in header
    assert "report: { title: 'レポート'" in header
    assert "pipeline: { title: '自動化'" in header
    for old_title in ("現在のシミュレーション", "現在のビュー", "現在のグラフ", "現在のレポート", "現在のパイプライン"):
        assert old_title not in header
    assert "<Plus size={14} /> {itemHeader.createLabel}" in header
    assert "＋ 新規作成" not in header
    assert "新規シミュレーション" in page
    assert "新規ビュー" in page
    assert "新規グラフ" in page
    assert "新規レポート" in page
    # XC-148 forbids save-as-template as *persistent header chrome* and requires it as a secondary
    # command on the selected item. The slice above covers the whole component, item menu included,
    # so a blanket absence check made the required command indistinguishable from the forbidden
    # button - and forbade both. The two are separated here: not in the persistent title row, and
    # present in the per-item menu that drops out of the selector.
    title_row = header[header.index("work-item-selector") : header.index("work-item-popover")]
    assert "テンプレートとして保存" not in title_row
    assert "テンプレート" not in title_row
    item_menu = header[header.index("work-item-more") : header.index("</DropdownMenuContent>")]
    assert "テンプレートとして保存" in item_menu, "the secondary save-as-template command is missing"
    assert "このワークスペース" in page and "共有" in page, "saving a template must offer its scope (GL-019)"
    assert "<FolderOpen" not in header
    assert "<Save" not in header
    assert "TemplateBar" not in page
    assert 'className="work-area-bar"' in header
    assert ".work-area-bar" in styles
    assert ".work-item-selector small { display: none; }" in styles
    assert ".work-area-bar > .primary-button { width: 28px;" in styles
    assert ".template-bar" not in styles


def test_central_asset_shelf_owns_library_browsing_without_adding_one_to_simulation() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    simulation_tabs = page[page.index("  simulation: [") : page.index("  pipeline: [")]

    assert "id: 'template'" not in simulation_tabs
    assert "function AssetLibraryShelf(" in page
    assert "<AssetLibraryShelf" in page
    assert 'className={`asset-library-shelf' in page
    assert 'className="library-category-rail"' in page
    assert 'className="template-source-tabs"' in page
    assert '>サンプル</TabsTrigger>' in page
    assert '>オリジナル</TabsTrigger>' in page
    assert 'placeholder={`${label}を検索`}' in page
    assert "template-tag-trigger" in page
    assert 'aria-haspopup="listbox"' in page
    assert 'placeholder="タグを絞り込み"' in page
    assert 'role="listbox"' in page
    assert 'aria-multiselectable="true"' in page
    assert "登録済みタグはありません。" in page
    assert 'className="template-tag-chip"' in page
    assert "template-sort-trigger" in page
    assert 'aria-haspopup="menu"' in page
    assert 'className="template-sort-popover"' in page
    assert 'role="menu"' in page
    assert "既定順" in page
    assert "名前：昇順" in page
    assert "名前：降順" in page
    assert "更新順" not in page
    assert 'className="template-empty-state"' in page
    assert "<b>{label}</b>" in page
    assert "`${sourceLabel}の${label}は空です。`" in page
    assert ".template-source-tabs" in styles
    assert "grid-template-columns: 1fr 1fr" in styles
    assert ".template-library-search" in styles
    assert ".template-tag-popover" in styles
    assert ".template-tag-chip" in styles
    assert ".template-sort-trigger" in styles
    assert ".template-sort-popover" in styles
    assert ".template-empty-state" in styles
    assert ".asset-library-shelf" in styles
    assert ".library-category-rail" in styles
    assert ".library-splitter" in styles
    assert ".library-card-grid" in styles
    assert ".library-shelf-collapsed" in styles
    assert 'className="library-collapsed-trigger"' in page
    assert '<b>素材ライブラリ</b>' in page
    assert '<span><small>素材ライブラリ</small><b>{label}</b></span>' not in page
    assert ".library-collapsed-trigger" in styles
    assert 'className="library-open-collapse-trigger"' in page
    assert 'aria-label="素材ライブラリを閉じる"' in page
    assert '<b>素材ライブラリ</b><span className="library-toggle-indicator">' in page
    assert "library-shelf-actions" not in page
    assert "library-shelf-actions" not in styles
    assert "ライブラリを拡張" not in page
    assert 'className={mode === \'expanded\' ? \'active\' : \'\'}' not in page
    open_header = page[page.index('className="library-shelf-header"') : page.index('className="library-shelf-body"')]
    assert 'className="library-category-rail"' in open_header
    assert ".library-open-collapse-trigger" in styles
    assert "@media (max-width: 900px)" in styles


def test_persistent_peer_tab_groups_use_stable_equal_widths() -> None:
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    area_tabs = styles[styles.index(".area-tabs {") : styles.index(".area-tabs > button:hover")]
    assert "--area-tab-width: 112px" in area_tabs
    assert "width: var(--area-tab-width)" in area_tabs
    assert "flex: 0 0 var(--area-tab-width)" in area_tabs
    assert "justify-content: center" in area_tabs
    assert "white-space: nowrap" in area_tabs

    library_tabs = styles[styles.index(".library-category-rail {") : styles.index(".template-library {")]
    assert "--library-category-tab-width: 104px" in library_tabs
    assert "width: var(--library-category-tab-width)" in library_tabs
    assert "flex: 0 0 var(--library-category-tab-width)" in library_tabs
    assert "justify-content: center" in library_tabs
    assert "overflow-x: auto" in library_tabs

    medium_tabs = styles[styles.index("@media (max-width: 1180px)") : styles.index("@media (max-width: 900px)")]
    assert ".area-tabs { --area-tab-width: 96px; }" in medium_tabs
    assert ".area-tabs button svg { display: none; }" in medium_tabs

    narrow_tabs = styles[styles.index("@media (max-width: 900px)") : styles.index("@media (max-width: 620px)")]
    assert ".area-tabs { --area-tab-width: 38px; }" in narrow_tabs
    assert ".area-tabs button { font-size: 0; }" in narrow_tabs
    assert ".area-tabs button svg { display: block; }" in narrow_tabs


def test_material_library_keeps_a_visible_title_adjacent_chevron_in_both_states() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert '<span className="library-toggle-indicator"><ChevronUp size={14}' in page
    assert '<span className="library-toggle-indicator"><ChevronDown size={14}' in page
    assert page.count('className="library-toggle-indicator"') == 2
    assert ".library-toggle-indicator {" in styles
    assert "flex: 0 0 22px" in styles
    assert ".library-toggle-indicator svg { display: block;" in styles


def test_graph_and_report_output_tabs_are_last_without_detaching_from_the_tab_sequence() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    graph_tabs = page[page.index("  graph: [") : page.index("  report: [")]
    report_tabs = page[page.index("  report: [") : page.index("  chat: [")]
    for tabs in (graph_tabs, report_tabs):
        assert "id: 'output'" in tabs
        assert tabs.rindex("id: 'output'") > tabs.rindex("id: 'detail'")
    assert "bottomDocked" not in page
    assert "bottom-docked" not in page
    assert ".sidebar-tab-button.bottom-docked" not in styles
    assert "margin-top: auto" not in styles[styles.index(".sidebar-tab-rail") : styles.index(".sidebar-tab-panel")]


def test_graph_canvas_has_no_redundant_apply_button() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    graph_screen = page[page.index("function GraphScreen(") : page.index("function ReportScreen(")]
    graph_heading = graph_screen[graph_screen.index('className="graph-heading"') : graph_screen.index('className="chart-frame"')]
    assert ">適用</button>" not in graph_heading
    assert 'className="primary-button"' not in graph_heading


def test_requested_library_categories_reuse_the_shared_central_library_shelf() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "const libraryCategories" in page
    assert "view: ['template', 'objects', 'materials', 'background', 'fonts']" in page
    assert "graph: ['template', 'style', 'fonts']" in page
    assert "report: ['template', 'layout', 'style', 'fonts']" in page
    assert "libraryCategories[screen]" in page
    assert "librarySidebarTabs" not in page
    assert "placeholder={`${label}を検索`}" in page
    assert "<b>{label}</b>" in page
    assert "右側ではなく中央下のライブラリ" not in page


def test_view_object_and_reusable_asset_terms_are_distinct_in_the_ui_catalogue() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "{ id: 'objects', label: 'オブジェクト'" in page
    assert "view: ['template', 'objects', 'materials', 'background', 'fonts']" in page
    assert "objects: { label: 'オブジェクト', icon: Shapes }" in page
    assert "scope: 'selection'" in page
    assert "選択中のオブジェクト" in page
    assert "{ id: 'assets', label: 'アセット'" not in page
    assert "view: ['template', 'assets'" not in page
    assert "選択中の表示要素" not in page
    assert "function AssetLibraryShelf" in page


def test_right_sidebar_is_context_editing_only_and_template_is_renamed_overall() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    next_screen_by_screen = {"view": "graph", "graph": "report", "report": "chat"}
    for screen in ("view", "graph", "report"):
        block_start = page.index(f"  {screen}: [")
        next_block = page.index(f"  {next_screen_by_screen[screen]}: [", block_start)
        assert "id: 'overall', label: '全体'" in page[block_start:next_block]
    sidebar = page[page.index("function RightSidebar") : page.index("function OutlinerPanel")]
    assert "<LibraryPanel" not in sidebar
    assert "template-source-tabs" not in sidebar
    assert "PropertyEditor" in sidebar
    assert "選択中" in page


def test_every_right_sidebar_mode_uses_responsibility_specific_editors() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    for editor in (
        "ViewPropertyEditor",
        "GraphPropertyEditor",
        "ReportPropertyEditor",
        "SimulationPropertyEditor",
        "NetworkPropertyEditor",
        "AutomationPropertyEditor",
        "ViewObjectPropertyEditor",
        "ViewTextPropertyEditor",
        "ViewMaterialPropertyEditor",
    ):
        assert f"function {editor}(" in page

    property_router = page[page.index("function PropertyEditor("):page.index("function PropertyGroup(")]
    for screen in ("view", "graph", "report", "simulation", "network"):
        assert f"screen === '{screen}'" in property_router
    assert "screen === 'settings'" not in property_router
    assert "return null" in property_router
    assert "基本設定" not in property_router
    assert "選択を変更" not in property_router

    view_editor = page[page.index("function ViewPropertyEditor("):page.index("function GraphPropertyEditor(")]
    for section in ("ビュー", "ガイド", "レンダラー", "照明", "画質", "背景", "成果物", "保存先"):
        assert f'title="{section}"' in view_editor
    assert "backgroundMode === 'solid'" in view_editor
    assert "backgroundMode === 'gradient'" in view_editor
    assert "value={lightingSource}" in view_editor
    assert "背景の環境" in view_editor
    assert "背景タブの環境アセットと回転" in view_editor
    assert "lightingSource !== 'unlit'" in view_editor
    assert "<span>表示強度</span>" in view_editor
    assert "<span>カメラに表示</span>" in view_editor
    assert 'title="ライティング"' not in view_editor
    assert "<span>環境光</span>" not in view_editor
    assert "outputMode === 'image'" in view_editor
    assert "カメラパス" in view_editor

    graph_editor = page[page.index("function GraphPropertyEditor("):page.index("function ReportPropertyEditor(")]
    for section in ("グラフ", "構成", "次元", "投影", "スタイル", "プロット", "書体", "ケース選択", "系列", "集約", "成果物", "保存先"):
        assert f'title="{section}"' in graph_editor
    for output in ("画像", "ベクター", "表データ", "アニメーション"):
        assert f">{output}</option>" in graph_editor
    assert "欠損として表示" in graph_editor
    assert "未宣言" in graph_editor

    report_editor = page[page.index("function ReportPropertyEditor("):page.index("function SimulationPropertyEditor(")]
    for section in ("レポート", "必須情報", "ページ", "共通要素", "アートスタイル", "文字表現", "埋め込み", "参照範囲", "収録項目", "コメント", "形式", "保存先"):
        assert f'title="{section}"' in report_editor
    for output in ("インタラクティブHTML", "PowerPoint", "Word", "Excel", "CSV", "画像", "動画", "プレーンテキスト", "Markdown"):
        assert f">{output}</option>" in report_editor
    assert "オフライン完結" in report_editor
    assert "生成コメントは現在利用できません" in report_editor

    assert "外部ソルバーの実行はr1対象外です" in page
    assert "ファイルから単位を推測しません" in page
    assert "暗黙の近似" in page
    assert "許可されるまで通信を試行しません" in page
    assert "property-panel-action" in styles
    assert "property-audit-empty" in styles
    assert 'key={`${screen}-${selectedTab.id}`}' in page


def test_asset_library_shelf_sits_between_canvas_and_instruction_bar_and_has_all_mock_states() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    catalogue = {str(item["id"]) for item in load_catalog()}

    centre = page[page.index('className="centre-column"') : page.index("</section>", page.index('className="centre-column"'))]
    assert centre.index("canvas-wrap") < centre.index("<AssetLibraryShelf") < centre.index("<InstructionBar")
    assert "scenario.screen !== 'chat'" in centre
    for state in (
        "view.library-collapsed",
        "view.library-one-row",
        "view.library-expanded",
        "view.library-searching",
        "view.library-selected",
        "view.library-narrow",
    ):
        assert state in catalogue


def test_sidebars_and_open_material_library_resize_from_full_edge_splitters() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "--left-sidebar-width" in page
    assert "--right-sidebar-width" in page
    assert 'className="dock-splitter sidebar-splitter-left"' in page
    assert 'className="dock-splitter sidebar-splitter-right"' in page
    assert 'className="dock-splitter library-splitter"' in page
    assert page.count('role="separator"') == 3
    assert 'aria-orientation="vertical"' in page
    assert 'aria-orientation="horizontal"' in page
    assert "aria-valuenow={width}" in page
    assert "aria-valuenow={mode === 'expanded' ? shelfHeight : 169}" in page
    assert 'aria-controls="left-sidebar"' in page
    assert 'aria-controls="right-sidebar"' in page
    assert 'aria-controls="asset-library-shelf"' in page
    assert "onPointerDown" in page
    assert "onKeyDown" in page
    assert "startHorizontalPanelResize" in page
    assert "startLibraryResize" in page
    assert ".dock-splitter" in styles
    assert ".sidebar-splitter-left" in styles
    assert ".sidebar-splitter-right" in styles
    assert ".library-splitter" in styles
    assert "cursor: ew-resize" in styles
    assert "cursor: ns-resize" in styles
    assert "dock-resize-handle" not in page
    assert "dock-resize-handle" not in styles


def test_material_library_resize_starts_from_rendered_height_and_tracks_pointer_without_animation() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "const shelf = handle.closest<HTMLElement>('.asset-library-shelf')" in page
    assert "const startHeight = shelf.getBoundingClientRect().height" in page
    assert "const next = baselineHeight - (moveEvent.clientY - startY)" in page
    assert "transition: height" not in styles


def test_material_library_resize_is_clamped_to_centre_column_without_page_overflow() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "function getLibraryMaximumHeight(shelf: HTMLElement)" in page
    assert "const centreColumn = shelf.closest<HTMLElement>('.centre-column')" in page
    assert "centreColumn.clientHeight - reservedHeight" in page
    assert "aria-valuemax={shelfMaximum}" in page
    assert ".product-shell {" in styles and "height: 100vh" in styles
    assert ".workbench {" in styles and "overflow: hidden" in styles
    assert ".centre-column {" in styles and "overflow: hidden" in styles
    assert "max-height: calc(100% - var(--work-area-height) - var(--instruction-height))" in styles


def test_workspace_cards_reuse_the_reference_four_by_three_thumbnails() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    thumbnails = ("bracket-1.png", "manifold-1.png", "housing.png", "wing.png")

    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in styles
    assert "aspect-ratio: 4 / 3" in styles
    assert "object-fit: cover" in styles
    for name in thumbnails:
        assert f"/thumbnails/{name}" in page
        data = (MOCKUP_THUMBNAILS / name).read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        assert int.from_bytes(data[16:20], "big") > 0
        assert int.from_bytes(data[20:24], "big") > 0


def test_view_uses_an_interactive_threejs_mock_without_invented_analysis_values() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    viewport = THREE_VIEWPORT.read_text(encoding="utf-8")
    scene = THREE_SCENE.read_text(encoding="utf-8")

    assert "import { Viewport } from '@/components/workspace/viewport'" in page
    assert "<Viewport paneIndex={index}" in page
    for control in ("Canvas", "OrbitControls", "GizmoHelper", "GizmoViewport", "Grid"):
        assert control in scene
    assert 'alignment="top-right"' in scene
    assert 'margin={[54, 102]}' in scene
    assert 'scale={36}' in scene
    assert 'axisHeadScale={1.1}' in scene
    assert 'font="600 22px Inter, Arial, sans-serif"' in scene
    assert 'alignment="bottom-right"' not in scene
    assert "representation" in viewport
    assert "自動回転" in viewport
    assert "解析値なし" in viewport
    assert 'className="view-footer"' not in page
    assert "表示用仮形状・解析データ未接続" not in page
    assert "border: 1px solid #6f7f88" not in styles
    assert "scenario.screen === 'view' && !itemListOpen ? 'view-canvas-wrap'" in page
    assert ".view-canvas-wrap { overflow: hidden; background: #151b20; padding: 0; }" in styles
    assert "fake \"stress\"" not in scene
    assert "von Mises" not in viewport


def test_view_object_properties_are_specific_to_all_first_release_object_types() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    view_schema = json.loads(VIEW_SCHEMA.read_text(encoding="utf-8"))

    for object_type in (
        "解析メッシュ",
        "参照メッシュ",
        "スカラー場",
        "ベクトル場",
        "流線・軌跡",
        "点群",
        "テキスト・注釈",
        "エフェクト",
    ):
        assert f"label: '{object_type}'" in page
    for variant in (
        "object-analysis-mesh",
        "object-reference-mesh",
        "object-scalar-field",
        "object-vector-field",
        "object-trajectory",
        "object-point-cloud",
        "object-annotation",
        "object-effect",
    ):
        assert f"'{variant}'" in page
    assert "function ViewObjectPropertyEditor(" in page
    assert "function ObjectTypeProperties(" in page
    assert "元のデータセット、解析値、単位、来歴は変更しません" in page
    assert "フィールドとシードを指定するまで形状を生成しません" in page
    assert "表示専用・解析値を生成しません" in page
    object_editor = page[page.index("function ViewObjectPropertyEditor("):page.index("function ObjectTypeProperties(")]
    object_type_editor = page[page.index("function ObjectTypeProperties("):page.index("function MaterialNodeGraph(")]
    assert "<MaterialPreview" not in object_editor
    assert "type MeshRepresentation = 'surface' | 'surface-edges' | 'wireframe'" in page
    assert "value={meshRepresentation}" in object_type_editor
    assert "setMeshRepresentation" in object_type_editor
    assert "showsMeshEdges && <details" in object_type_editor
    assert "<span>表示不透明度</span>" in object_type_editor
    assert '<summary><ChevronRight size={12} /><b>エッジ</b></summary>' in object_type_editor
    assert "オブジェクトのエッジ色" in object_type_editor
    assert "<span>幅</span>" in object_type_editor
    assert '<label className="property-toggle"><span>エッジ</span>' not in object_type_editor
    presentations = view_schema["properties"]["objectPresentations"]
    presentation = presentations["items"]
    assert view_schema["version"] == "3.1.0"
    assert set(presentation["required"]) == {"objectId", "representation", "visible", "displayOpacity"}
    assert presentation["properties"]["displayOpacity"]["minimum"] == 0
    assert presentation["properties"]["displayOpacity"]["maximum"] == 1
    assert set(presentation["properties"]["edgeSettings"]["required"]) == {"colourSrgb", "widthPx", "opacity"}
    assert "material" not in presentation["properties"]["edgeSettings"]["properties"]


def test_material_properties_use_one_materialx_slot_model_with_typed_dependencies() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    view_schema = json.loads(VIEW_SCHEMA.read_text(encoding="utf-8"))
    material_schema = json.loads(MATERIAL_SCHEMA.read_text(encoding="utf-8"))
    slots = view_schema["properties"]["materialBindings"]["items"]
    editor = page[page.index("function ViewMaterialPropertyEditor("):page.index("function ViewTextPropertyEditor(")]

    assert {"bindingId", "objectId", "target", "materialRef", "inputBindings"} <= set(slots["required"])
    assert set(slots["properties"]["target"]["properties"]["kind"]["enum"]) == {"wholeObject", "part", "elementSet"}
    assert slots["properties"]["materialRef"]["required"] == ["entryId", "revision"]
    assert "solviaResult" in str(view_schema["$defs"]["materialInputBinding"])
    assert material_schema["properties"]["contract"]["const"] == "CT-011"
    assert "profile" not in material_schema["properties"]
    assert "materialKind" not in material_schema["properties"]
    assert "role=\"listbox\" aria-label=\"マテリアルスロット\"" in editor
    assert "materialSlots.map" in editor
    assert "addMaterialSlot" in editor
    assert "removeMaterialSlot" in editor
    assert "空のマテリアルスロットを追加" in editor
    assert "選択中のマテリアルスロットを削除" in editor
    assert "stress_value" in editor
    assert "単位次元" in editor
    assert "解析カラーを評価できません" in editor
    assert "material-editor-tabs" in editor
    for mode in ("基本", "ノード", "ソース"):
        assert f"'{mode}'" in editor
    assert "function MaterialOutputPreviews(" not in page
    assert "selectedChannel" not in editor
    assert "material-output-previews" not in styles
    assert "MaterialNodeGraph" in page
    assert "resultBinding={activeResultBinding}" in editor
    assert "中央でノードを編集" in editor
    assert "MaterialXソース" in editor
    assert "type BaseColorInputMode = 'solid' | 'texture' | 'colormap' | 'formula'" in page
    assert "value={activeBaseColorMode}" in editor
    assert "updateBaseColorMode" in editor
    assert '<option value="connection">ノード接続</option>' not in editor
    assert ">ノード接続</option>" not in editor
    assert "activeBaseColorMode === 'solid'" in editor
    assert "activeBaseColorMode === 'texture'" in editor
    assert "activeBaseColorMode === 'colormap'" in editor
    assert "activeBaseColorMode === 'formula'" in editor
    assert '<option value="analysis">解析結果</option>' not in editor
    for option in ('単色', '画像', 'カラーマップ', '数式'):
        assert f">{option}</option>" in editor
    assert "応力 / von Mises" in editor
    assert "変位 / magnitude" in editor
    assert "位置 / X" in editor
    assert "<span>座標</span>" not in editor
    assert "<span>投影面</span>" in editor
    for plane in ("XY", "XZ", "YZ"):
        assert f">{plane}</option>" in editor
    assert "color-map-compact" in editor
    assert "colorMapRange.minimum" in editor
    assert "colorMapRange.maximum" in editor
    assert "colorMapRangeValid" in editor
    assert "activeMaterialValid" in editor
    assert "updateColorMapRange" in editor
    assert "カラーマップを編集" in editor
    assert "不透明度制御点" in editor
    assert "カラー制御点" in editor
    assert "プリセット" in editor
    assert "補間" in editor
    assert "最小値は最大値より小さくしてください" in editor
    assert "範囲外の値は透明として評価" in editor
    assert "material-colormap-dialog" in styles
    assert "<b>解析入力</b>" not in editor
    assert "外部コードは実行しません" in editor
    assert "自動検証" in editor
    assert ">検証</button>" not in editor
    assert "読み込み時の検証済み" in editor
    assert "新しいリビジョンを保存" in editor
    assert "saveMaterialRevision" in editor
    assert "activeSlot.sourceFile" in editor
    assert "brushed_steel.mtlx" in editor
    assert "material-save-bar" in editor
    assert "material-model-row" in editor
    assert "<span>Opacity</span>" in editor
    assert 'aria-label="MaterialX geometry_opacity"' in editor
    assert editor.count('name="geometry_opacity" type="float" value="1.0"') == 2
    assert "<b>マッピング</b>" in editor
    assert "activeMappingRequired && <details" in editor
    assert "value={activeMappingMode}" in editor
    assert "activeMappingMode === 'authoredUv'" in editor
    assert "<span>UVセット</span>" in editor
    assert "activeMappingMode === 'planar'" in editor
    for mode in ("UV", "生成UV", "オブジェクト空間・トライプラナー", "平面投影", "円柱投影", "球面投影"):
        assert f">{mode}</option>" in editor
    assert "mappingRequired: false" in editor
    assert "利用可能・UV不要" in editor
    assert "<span>Height</span>" not in editor
    assert "<option value=\"openpbr\">OpenPBR Surface</option>" not in editor
    assert "サーフェス</small>" not in editor
    assert "結果カラー</small>" not in editor
    assert "material-display-modes" not in editor
    assert "<b>割り当て</b>" not in editor
    assert "バリアントとマッピング" not in editor
    assert "追跡可能性" not in editor
    assert "<Image" not in editor
    assert "material-slot-card" not in editor


def test_material_library_uses_thumbnails_while_sidebar_slots_use_names_only() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    expected = {
        "technical-blue.png",
        "neutral-gray.png",
        "inspection-orange.png",
        "translucent-cyan.png",
        "brushed-steel.png",
    }

    assert {path.name for path in MATERIAL_THUMBNAIL_DIR.glob("*.png")} == expected
    for thumbnail in expected:
        data = (MATERIAL_THUMBNAIL_DIR / thumbnail).read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        assert int.from_bytes(data[16:20], "big") == 512
        assert int.from_bytes(data[20:24], "big") == 512
        assert data[25] == 6  # PNG RGBA colour type
        assert f"/materials/{thumbnail}" in page

    assert "item.thumbnail ? <Image" in page
    assert "thumbnail: '/materials/brushed-steel.png'" in page
    assert page.count("/materials/brushed-steel.png") == 1
    assert ".library-card-preview.material-sphere-thumbnail" in styles
    assert ".material-slot-row" in styles
    assert ".material-slot-controls" in styles
    assert 'className="material-slot-icon result"' not in page


def test_view_property_tabs_follow_the_last_selected_active_object_without_a_second_target_picker() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    scene = THREE_SCENE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "[...current.filter((item) => item !== name), name]" in page
    assert "selectedViewObjects.at(-1)" in page
    assert "const activeName = selectedNames.at(-1)" in page
    assert "aria-current={active ? 'true' : undefined}" in page
    assert "event.shiftKey" in page
    assert "event.shiftKey" in scene
    view_tabs = page[page.index("  view: ["):page.index("  graph: [")]
    text_editor = page[page.index("function ViewTextPropertyEditor("):page.index("function AutomationPropertyEditor(")]
    assert "{ id: 'text', label: 'テキスト'" in view_tabs
    assert "{ id: 'fonts', label: 'フォント'" not in view_tabs
    assert "tab.id !== 'text' || viewObjectKinds[activeViewObjectKind].textProperties" in page
    assert "annotation: { label: 'テキスト・注釈'" in page
    assert "textProperties: true" in page
    assert "if (!viewObjectKinds[kind].textProperties) return null" in text_editor
    assert "アクティブなテキスト・注釈オブジェクトだけを編集します" in text_editor
    assert "フォント設定はありません" not in page
    assert '<span>テキスト</span><textarea' in text_editor
    assert "適用先を選択" not in page
    assert "materialTargeting" not in page
    assert "マテリアル対象を選択中" not in page
    assert "target-compatible" not in page
    assert ".outliner-row.selected.active" in styles


def test_every_user_facing_font_tab_is_named_text() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    graph_tabs = page[page.index("  graph: ["):page.index("  report: [")]
    report_tabs = page[page.index("  report: ["):page.index("  chat: [")]
    assert "{ id: 'fonts', label: 'テキスト'" in graph_tabs
    assert "{ id: 'fonts', label: 'テキスト'" in report_tabs
    assert "fonts: { label: 'テキスト', icon: Type }" in page
    assert "label: 'フォント'" not in page
    assert "<span>フォント</span>" in page  # field label remains precise inside the Text tab


def test_live_material_preview_defaults_to_sphere_and_offers_neutral_test_shapes() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    preview = MATERIAL_PREVIEW.read_text(encoding="utf-8")
    material_icon = MATERIAL_SPHERE_ICON.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "import { MaterialPreview }" in page
    assert page.count("<MaterialPreview") == 2
    assert "useState<PreviewShape>('sphere')" in preview
    for shape in ("sphere", "cube", "plane", "cylinder", "plane2d"):
        assert f"id: '{shape}'" in preview
    for channel in ("マテリアル", "Base Color", "Roughness", "Metalness", "Normal", "解析カラー"):
        assert f"label: '{channel}'" in preview
    assert "label: 'Height'" not in preview
    for control in ("Canvas", "OrbitControls", "meshPhysicalMaterial", "ContactShadows"):
        assert control in preview
    assert "外観プレビュー" in preview
    assert "サンプルデータ" in preview
    assert "マテリアル表示失敗" in preview
    assert "#ff00ff" in preview
    assert "<header>" not in preview
    assert "<footer" not in preview
    assert "result-colour-preview" not in preview
    assert "title={item.label}" in preview
    assert "aria-label={item.id === 'plane2d' ? '2D面で固定プレビュー'" in preview
    assert "!isTwoDimensional && <OrbitControls" in preview
    assert "!isTwoDimensional && <ContactShadows" in preview
    assert "isTwoDimensional ? '固定表示' : 'ドラッグで回転'" in preview
    assert "useState<PreviewChannel>('material')" in preview
    assert "{ id: 'material', label: 'マテリアル', icon: MaterialSphereIcon }" in preview
    assert "{ id: 'base-color', label: 'Base Color', icon: Palette }" in preview
    assert "{ id: 'materials', label: 'マテリアル', description:" in page
    assert "icon: MaterialSphereIcon" in page
    assert "materials: { label: 'マテリアル', icon: MaterialSphereIcon }" in page
    assert '<circle cx="12" cy="12" r="9" />' in material_icon
    assert "c1.9 2 2.7 4.8 2.1 7.6" in material_icon
    assert 'className="material-preview-channels"' in preview
    assert 'aria-label="表示するマテリアル出力"' in preview
    assert "resultOutput ? previewChannels" in preview
    assert "von Mises" not in preview
    assert "stress" not in preview.lower()
    assert ".material-preview-panel" in styles
    assert "flex: 0 0 224px" in styles
    assert ".sidebar-tab-panel.has-fixed-preview" not in styles
    assert ".material-preview-shapes { position: absolute" in styles
    assert ".material-preview-channels { position: absolute" in styles
    assert "left: 7px" in styles[styles.index(".material-preview-channels"):styles.index(".material-preview-shapes")]
    assert "right: 7px" in styles[styles.index(".material-preview-shapes"):styles.index(".material-preview-canvas")]
    assert "flex-direction: column" in styles

    object_editor = page[page.index("function ViewObjectPropertyEditor("):page.index("function ObjectTypeProperties(")]
    material_editor = page[page.index("function ViewMaterialPropertyEditor("):page.index("function ViewTextPropertyEditor(")]
    assert "<ObjectTypeProperties" in object_editor
    assert "<MaterialPreview" not in object_editor
    slot_list_index = material_editor.index("material-slot-manager")
    active_preview_index = material_editor.index("<MaterialPreview", slot_list_index)
    assert slot_list_index < active_preview_index < material_editor.index("material-editor-tabs")
    assert "resultOutput={activeResultBinding}" in material_editor
