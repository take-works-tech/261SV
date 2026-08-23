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
OPTION_SAMPLES = ROOT / "mockups" / "ui" / "components" / "workspace" / "option-samples.tsx"
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
    assert 'className={`chat-composer ${compact' in page
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
    assert ".outliner-row b { overflow: hidden; padding-left: 2px; font-size: var(--text-emphasis);" in styles
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
    assert "<WorkspaceSourceSections selectedCase={selectedCase}" in left_sidebar
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
    assert 'data-tooltip={isBorrowed(tab.id) ? `${label}・基準ビューの設定` : label}' in page
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
    assert "scopeLabel ? `${scopeLabel}：${label}` : label" in page
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
    assert "hoverPosition" in view_screen
    assert "onClick={(event) => commit(positionFromPointer(event))}" in view_screen
    assert "onMouseMove" in view_screen
    assert "getBoundingClientRect" in view_screen
    assert "clientX" in view_screen
    # XC-131: the axis is time, mode number or frequency, and XC-160 gives each its own value format.
    # A single `m:ss` formatter printed a clock on the mode-axis state.
    assert "resultAxes" in view_screen
    assert "'time'" in view_screen and "'mode'" in view_screen and "'frequency'" in view_screen
    assert "definition.discrete ? Math.round" in view_screen
    assert "aria-valuetext={definition.format(position)}" in view_screen
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
    # XC-148 bars a save action as *persistent chrome*; inside a dropdown it is a secondary command,
    # which is where both テンプレートとして保存 and この比較を保存 (XC-209) live
    chrome = re.sub(r"<DropdownMenuContent[\s\S]*?</DropdownMenuContent>", "", header)
    assert "<Save" not in chrome
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
        assert tabs.rindex("id: 'output'") > tabs.rindex("label: 'スタイル'")
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
        expected = {"view": "'ビュー'", "graph": "'グラフ'", "report": "'レポート'"}[screen]
        assert f"id: 'overall', label: {expected}" in page[block_start:next_block]
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
    for section in ("グラフ", "構成", "次元", "投影", "スタイル", "書体", "設定する軸", "表題", "範囲", "目盛", "グリッド", "ケース選択", "系列", "集約", "成果物", "保存先"):
        assert f'title="{section}"' in graph_editor or f'aria-label="{section}"' in graph_editor
    for output in ("画像", "ベクター", "表データ", "アニメーション"):
        assert f">{output}</option>" in graph_editor
    assert "欠損として表示" in graph_editor
    assert "未宣言" in graph_editor

    report_editor = page[page.index("function ReportPropertyEditor("):page.index("function SimulationPropertyEditor(")]
    for section in ("レポート", "必須情報", "ページ", "共通要素", "アートスタイル", "文字表現", "埋め込み", "参照範囲", "収録項目", "書き方", "方針", "下書き", "形式", "保存先"):
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
        # view/AC-076: a data-dependent Asset uses its own versioned sample fixture. It used to point
        # at technical-blue.png, which is another Asset's thumbnail.
        "result-sample.png",
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
    # No Asset borrows another Asset's rendered thumbnail, and an absent one is named rather than
    # replaced by a generic sphere (view/AC-076).
    for thumbnail in expected:
        assert page.count(f"/materials/{thumbnail}") <= 2
    assert "thumbnailMissing" in page
    assert "サムネイル未生成" in page
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
    # view/AC-068: the active object comes from the shared viewport and Outliner selection, not from
    # the scenario variant, so selecting another element changes which type-specific form is shown.
    assert "tab.id !== 'text' || (active.kind !== 'container' && viewObjectKinds[active.kind].textProperties)" in page
    assert "const active = activeViewObject(variant, selectedViewObjects)" in page
    assert "const selectedKind = name ? outlinerObjectKinds[name] : undefined" in page
    assert "annotation: { label: 'テキスト・注釈'" in page
    assert "textProperties: true" in page
    assert "if (activeObject.kind === 'container' || !viewObjectKinds[activeObject.kind].textProperties) return null" in text_editor
    assert "アクティブなテキスト・注釈オブジェクトだけを編集します" in text_editor
    assert "フォント設定はありません" not in page
    assert '<span>テキスト</span><textarea' in text_editor
    assert "適用先を選択" not in page
    assert "materialTargeting" not in page
    assert "マテリアル対象を選択中" not in page
    assert "target-compatible" not in page
    assert ".outliner-row.selected.active" in styles


def test_type_settings_are_part_of_the_style_theme_not_a_tab_of_their_own() -> None:
    """XC-213/XC-214: a `テキスト` tab beside `スタイル` split one look across two tabs. Type is part of
    the theme in Graph and Report; the View rail keeps `テキスト` because there it is a selected object's
    own content, not the document's type scale."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    graph_tabs = page[page.index("  graph: ["):page.index("  report: [")]
    report_tabs = page[page.index("  report: ["):page.index("  chat: [")]
    view_tabs = page[page.index("  view: ["):page.index("  graph: [")]
    assert "id: 'fonts'" not in graph_tabs and "id: 'fonts'" not in report_tabs
    assert "{ id: 'text', label: 'テキスト'" in view_tabs
    assert "fonts: { label: 'テキスト', icon: Type }" in page
    assert "label: 'フォント'" not in page
    assert "<span>フォント</span>" in page  # field label remains precise inside the theme


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


def test_every_required_modal_state_renders_a_controlled_dialog() -> None:
    """`chat.outbound-request` and `pipeline.scope-confirmation` used to render nothing at all.

    ModalCard wrapped a Radix Dialog with no `open`, so it stayed shut and two states the
    specification requires showed an empty canvas while the catalogue reported them covered.
    """
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "function ModalCard({ title, detail, open, onClose, children }" in page
    assert "<Dialog open={open} onOpenChange={(next) => { if (!next) onClose() }}>" in page
    assert re.search(r"<Dialog>\s", page) is None, "an uncontrolled Dialog renders nothing"
    assert "<ModalCard open={outboundOpen}" in page
    assert "{scopeUnit && <ModalCard" in page


def test_the_command_list_covers_every_group_of_the_specified_keyboard_scheme() -> None:
    """The spec's keyboard table is the source; the settings command list must answer every row.

    Four of its ten rows - case tree, outliner, instruction bar and panels - had no group in the
    mockup, so `settings.shortcuts` showed a command list that was missing whole areas of the scheme.
    """
    spec = UI_SPEC.read_text(encoding="utf-8")
    section = spec[spec.index("## The keyboard scheme") : spec.index("## Conventions")]
    groups = set()
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        first = line.split("|")[1].strip()
        if first in {"Group", ""} or set(first) <= {"-"}:
            continue
        groups.add(first.replace("**", ""))
    assert {"workspace", "case tree", "outliner", "instruction bar", "panels"} <= groups

    page = CHAT_PAGE.read_text(encoding="utf-8")
    declared = set(re.findall(r"specGroup: '([^']+)'", page))
    assert groups <= declared, f"no command group for {sorted(groups - declared)}"


def test_top_menus_name_commands_and_show_their_key_from_the_one_command_table() -> None:
    """The menus held `ファイルを開く` / `ファイルの設定` placeholders and taught no key.

    11_ui.md requires a shortcut to be discoverable beside the action in menus as well as in the
    command list, and one definition per key means the menu reads the table rather than restating it.
    """
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "{menu}を開く" not in page
    assert "{menu}の設定" not in page
    assert "const commandByName = new Map(shortcutGroups.flatMap(" in page
    assert "const command = shortcutFor(item.command)" in page
    assert "command.key === null" in page and "キーなし" in page
    assert "<kbd>{shortcutFor('指示バーへフォーカス')?.key}</kbd>" in page
    for menu in ["ファイル", "編集", "表示", "フィルタ", "ツール", "ヘルプ"]:
        assert f"menu: '{menu}'" in page


def test_case_tree_searches_selects_and_confirms_a_deletion_by_its_references() -> None:
    """Selecting a @Case changes the subject of every area, and deleting one is confirmed (XC-062)."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    # XC-217: the field is inside the case section, so it reads that section's own query prop
    assert "value={query} onChange={(event) => onQueryChange(event.target.value)}" in page
    case_section = page[page.index('<SidebarSection title="ケース"'):page.index('<SidebarSection title="変数"')]
    assert 'className="permanent-search"' in case_section
    assert page.count('className="permanent-search"') == 1
    assert "onClick={() => onSelectCase(item.name)}" in page
    assert "selectedCase={selectedCase}" in page
    assert "references: [" in page
    assert "このケースを参照している箇所は{references.length}件です" in page
    assert "代替値では埋めません" in page


def test_expressions_use_the_shared_editor_with_scope_units_and_an_error_position() -> None:
    """`Expression editor` is a shared component in 11_ui.md; Graph and Pipeline wrote bare inputs."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "function ExpressionEditor({ id, label, initial }" in page
    assert "function checkExpression(text: string): ExpressionCheck" in page
    assert "はスコープにありません" in page
    assert "の単位が未宣言のため、次元を検査できません" in page
    assert "比較の左右で次元が違います" in page
    assert "expression-caret" in page
    assert "文字目：" in page
    assert "<ExpressionEditor id={`graph-${activeSeries.id}`}" in page
    assert "<ExpressionEditor\n            id={`pipeline-${selectedUnit.id}`}" in page
    assert 'placeholder="単位付きの式"' not in page


def test_pipeline_units_reorder_with_a_drop_position_shown_before_the_drop() -> None:
    """11_ui.md: a drop position is previewed as a line before the drop, and units are reordered."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "pipeline-drop-line" in page
    assert "setDropIndex(index)" in page
    assert "const dropUnit = (index: number)" in page
    assert "const moveUnit = (id: string, direction: -1 | 1)" in page
    assert "を上へ移動" in page and "を下へ移動" in page
    assert "function annotatePipelineTargets" in page
    assert "対象{row.acts}" in page


def test_pipeline_reports_an_outcome_per_case_and_unit_including_a_false_condition() -> None:
    """The `Run outcome table` of 11_ui.md: applied, skipped, failed, refused - and the value a false
    condition evaluated to, without which a refused unit reads like one never reached."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "function RunOutcomeTable(" in page
    for outcome in ["applied", "skipped", "failed", "refused"]:
        assert f"'{outcome}'" in page
        assert f".run-outcome-{outcome}" in styles
    assert "条件の評価値：false" in page
    assert "先行ユニットの失敗により未実行" in page


def test_a_destructive_pipeline_unit_states_its_scope_before_it_is_authorised() -> None:
    """XC-094: authorised once, for a named scope, with the case count stated."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "clear: { label: 'クリア'" in page and "destructive: true" in page
    assert "実行前に範囲確認が必要" in page
    assert "ケースの範囲で許可" in page
    assert "disabled={unauthorised.length > 0}" in page
    assert "同じ数はドライランでも確認できます" in page


def test_import_review_proposes_grouping_and_tags_without_applying_them() -> None:
    """XC-120: proposals, nothing applied until accepted, and a rejected proposal is not re-offered."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "const importTagProposals = [" in page
    assert "受け入れるまで何も適用しません" in page
    assert "setGroupingAccepted" in page
    assert "setRejectedTags" in page
    assert "このセッションでは再提案しません" in page
    assert "提案を適用せず取込" in page


def test_material_library_originals_carry_workspace_or_shared_scope() -> None:
    """GL-019: an original is workspace-scoped or shared, labelled inside オリジナル rather than folded
    into the サンプル/オリジナル choice. The original source used to render an empty state everywhere."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "const libraryOriginals: Record<string, LibraryItem[]>" in page
    assert "libraryScopeLabels: Record<LibraryScope, string> = { workspace: 'このワークスペース', shared: '共有' }" in page
    assert "library-scope-filter" in page
    assert "ドラッグでの移動は複写です" in page
    assert "source === 'sample' ? samples : originals" in page


def test_report_and_chat_statements_carry_which_kind_they_are_and_their_source() -> None:
    """XC-104's four statement kinds. The `Provenance badge` shared component names Report and Chat as
    its users; the mockup had only the quantity-provenance badge, which answers a different question."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "type StatementKind = 'value' | 'comparison' | 'citation' | 'user'" in page
    assert "function StatementKindBadge({ kind, source }" in page
    assert "function ReportCommentaryReview()" in page
    assert "除外した記述" in page
    assert "書き直しを1回試み" in page
    assert page.count("<StatementKindBadge") >= 3
    chat_thread = page[page.index("function ConversationThread(") : page.index("function AssistantDrawer(")]
    assert "<StatementKindBadge" in chat_thread


def test_an_unresolved_template_lists_what_failed_with_its_source_revision() -> None:
    """XC-063 keeps the unresolved list plus the template identifier and revision reachable. The state
    was a paragraph of prose, which is neither a list nor an identity."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "function UnresolvedList({ title, source, revision, resolved, unresolved }" in page
    assert 'source="ビューテンプレート「技術資料・標準」"' in page
    assert 'revision="リビジョン 3"' in page
    assert "既定値で埋めません" in page


def test_split_view_names_the_case_in_each_pane_and_offers_camera_synchronisation() -> None:
    """`Split layout`: one to four panes with per-pane case and camera synchronisation."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert ": Array.from({ length: panes }, (_, index) => index === 0 ? selectedCase" in page
    # one overlay per pane naming both the case and the camera, so it cannot collide with the
    # viewport's own controls the way two corner pills did (11_ui.md)
    assert 'className="view-pane-subject"' in page
    assert 'className="view-pane-camera"' not in page
    assert "カメラ同期" in page
    # the pane badge is the control, and it is a dropdown trigger rather than a label, so no sentence
    # on the canvas has to say it can be clicked (XC-209)
    assert "各画面のケースとカメラは、画面上部の表示をクリックして選びます。" not in page


def test_the_three_viewport_carries_one_mock_label_and_shares_names_with_the_outliner() -> None:
    """11_ui.md: no separate status footer - the in-viewport mock label is sufficient - and the
    Outliner row is synchronized with viewport selection, which two naming schemes made impossible."""
    viewport = THREE_VIEWPORT.read_text(encoding="utf-8")
    scene = THREE_SCENE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "viewport-status" not in viewport
    assert ".viewport-status" not in styles
    assert viewport.count("表示用モック・データ未接続") == 0
    assert "viewport-badge-selection" in viewport
    for name in ["［元ファイルの部品名 01］", "［元ファイルの部品名 02］", "［元ファイルの領域名］"]:
        assert name in scene
    assert 'label="ベース（仮）"' not in scene


def test_network_has_no_case_tree_and_one_audit_source() -> None:
    """The layout table grants the left column to five work areas and Chat; Network is in neither list.
    Its rail also claimed there were no audit records while the centre listed some."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "const showsCaseSidebar = scenario.screen !== 'network'" in page
    assert "{leftOpen && showsCaseSidebar && <LeftSidebar" in page
    assert "const networkAuditRows" in page
    assert "function auditRowsFor(variant: string)" in page
    assert "property-audit-empty" not in page
    assert '<span className="eyebrow">{screenNames[screen]}</span><b>{screenNames[screen]}</b>' not in page


def test_the_work_item_catalogue_has_exactly_one_grid_and_list_switch() -> None:
    """XC-149 puts search, filtering and the display switch in the shared title bar. The catalogue
    added a second switch of its own, and the title-bar pair was decorative."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    library = page[page.index("function WorkItemLibrary(") : page.index("function WorkItemCatalogPreview(")]

    assert "layout-switch" not in library
    assert "workspace-filters" not in library
    assert "layout={itemListLayout}" in page
    assert "onClick={() => onItemListLayoutChange('grid')}" in page
    assert "work-area-list-scope" in page


def test_the_workspace_list_filters_only_by_metadata_its_cards_carry() -> None:
    """A `最近使用` chip returned the whole list while every card said `最終利用：—`."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    home = page[page.index("function WorkspaceHome(") : page.index("function LeftSidebar(")]

    assert "'最近使用'" not in home
    assert "const availableHomeTags = Array.from(new Set(workspaceItems.map(([, tag]) => tag)))" in home
    assert "setHomeTags" in home
    assert "共有スコープのワークスペースはこのモックアップにありません" in home


def test_one_conversation_keeps_its_settings_across_the_bar_and_chat() -> None:
    """XC-150: switching surfaces preserves the draft *and* the conversation settings. Model, effort
    and search permission lived inside the composer, so each surface reset them on mount."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "type ConversationSettings = { model: string; effort: string; search: 'off' | 'allowed' }" in page
    assert "useState<ConversationSettings>({ model: 'local', effort: 'standard', search: 'off' })" in page
    assert page.count("<ChatComposer draft={draft} onDraftChange={onDraftChange} settings={settings} onSettingsChange={onSettingsChange}") == 3
    assert "onSettingsChange({ ...settings, model: event.target.value })" in page


def test_an_invalid_setting_is_rejected_at_its_field_with_the_previous_value_kept() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "function UnitSettings({ invalid }" in page
    assert "aria-invalid={!valid}" in page
    assert "を拒否しました" in page
    assert "直前の値「{acceptedUnit}」を維持しています" in page
    assert 'role="alert"' in page


def test_the_view_rail_gives_camera_its_own_tab_and_overall_keeps_none_of_it() -> None:
    """XC-196. `全体` held the camera as one selector, which stops working the moment saved viewpoints,
    a focus target and depth of field exist - and XC-197 adds exactly those."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    view_tabs = page[page.index("  view: ["):page.index("  graph: [")]

    order = re.findall(r"id: '([a-z]+)', label: '([^']+)'", view_tabs)
    assert [label for _, label in order][:5] == ["ビュー", "カメラ", "描画", "背景", "出力"]
    assert [ident for ident, _ in order][5:] == ["objects", "text", "materials"]

    overall = page[page.index("if (tab.id === 'overall') return"):page.index("if (tab.id === 'camera') return")]
    assert "投影" not in overall, "projection stayed in 全体 after moving to カメラ"
    assert "<span>カメラ</span>" not in overall
    assert "画面分割" not in overall, "the split is session state and belongs on the canvas (XC-202)"
    assert "ガイド" in overall


def test_a_view_holds_several_named_cameras_each_storing_its_rule() -> None:
    """XC-197 and XC-199: one camera object carries its pose and its lens, and a pose rule resolves per
    case. Storing the resolved numbers would show four panes one case's critical moment; separating the
    pose from the lens would mean changing the lens for one saved position changed it for all."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "type CameraModel = {" in page
    assert "pose: 'explicit' | 'framed'" in page
    assert "focalLengthMm: number" in page and "projection: 'perspective' | 'orthographic'" in page
    assert "ViewpointModel" not in page, "the viewpoint concept was merged into the camera"
    assert "kind: 'extremum'; quantity: string; statistic:" in page
    assert "function resolveCamera(" in page
    assert "規則：${camera.focus.quantity}の${camera.focus.statistic}へ寄せる" in page
    # the unresolved path names the quantity and leaves the camera alone
    assert "がこのケースにありません。カメラは動かしていません" in page
    assert "座標は保存せず、ケースごとに解決し直します" in page
    # several cameras, and a pane names the one it looks through
    assert "const seedCameras: CameraModel[] = [" in page
    # a pane's camera is session state, chosen on the canvas, so it is not a member of the saved item
    assert "paneCameraIds" not in page
    assert "const [paneBindings, setPaneBindings] = useState" in page
    assert 'className="view-pane-subject"' in page


def test_result_bookmarks_resolve_per_case_snap_to_a_stored_position_and_say_so() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "type ResultBookmarkModel = {" in page
    for kind in ["'explicit'", "'extremum'", "'crossing'", "'relative'"]:
        assert f"kind: {kind}" in page
    assert "function resolveBookmark(" in page
    assert "storedStep" in page
    assert "保存位置へ丸め" in page
    assert "caseName" in page and 'small>ケース「{caseName}」で解決した位置' in page
    # an unresolved rule draws no marker: a marker at the axis minimum would be a plausible default
    assert "resolved.filter((entry) => entry.resolution.state === 'resolved').map" in page
    assert ".playback-bookmark-marker" in styles


def test_grading_is_a_group_inside_rendering_that_defaults_to_no_grade() -> None:
    """XC-198. Both references ship grading; neither has this product's constraint that a value must not
    show as two colours in two screenshots."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "type GradePreset = 'measurement' | 'standard' | 'technicalDocument' | 'presentation' | 'photoreal'" in page
    assert "useState<GradePreset>('measurement')" in page
    rendering = page[page.index("if (tab.id === 'rendering') return"):page.index("if (tab.id === 'background') return")]
    assert 'PropertyGroup title="照明"' in rendering
    assert 'PropertyGroup title="現像"' in rendering
    assert rendering.index('title="照明"') < rendering.index('title="現像"')
    assert "計測プリセットは無補正です" in rendering
    assert "凡例も同じ補正を通すか、補正名とパラメータを成果物に記載します" in rendering
    # a treatment the backend cannot perform is named rather than offered
    assert "フォトリアル経路は未接続です" in rendering


def test_a_property_row_is_laid_out_by_its_shape_not_by_its_depth() -> None:
    """The row grid was bound to the direct-child position, so wrapping a few rows in a group to give
    them one accessible name silently dropped it and left the caption and the control out of line with
    their neighbours. A rule that stops applying when a wrapper appears, with nothing to notice, is the
    structure at fault rather than the one site that hit it."""
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert ".property-fields > label {" not in styles
    assert ".property-fields label:has(> span) { display: grid; grid-template-columns: 68px minmax(0, 1fr);" in styles
    # a label with no caption span - the expression editor's - is deliberately not a row
    assert ".expression-editor > label" in styles


def test_type_is_declared_only_through_the_scale() -> None:
    """XC-201. The catalogue had grown twenty distinct sizes across 368 declarations, four of them
    within a pixel of each other and sixteen at 5 or 6 pixels, while the button primitives rendered at
    14 (E-122). None of that was chosen; it accumulated because no check could see it. This is the
    check: outside the token block, no rule states a type value of its own.
    """
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    root_start = styles.index(":root {")
    tokens = styles[root_start:styles.index("\n}", root_start)]
    rules = styles[styles.index("\n}", root_start):]

    for step in ["--text-caption", "--text-body", "--text-emphasis", "--text-title", "--text-heading", "--text-display"]:
        assert f"{step}: var(--size-" in tokens, f"{step} is not defined on the primitive layer"
    for primitive in ["--size-1", "--size-6", "--weight-regular", "--weight-bold", "--leading-none",
                      "--leading-relaxed", "--tracking-wide", "--tracking-tight", "--family-ui",
                      "--family-mono", "--family-deliverable"]:
        assert f"{primitive}:" in tokens, f"{primitive} is missing from the primitive layer"

    allowed = {"inherit", "0"}
    for prop in ["font-size", "font-weight", "line-height", "letter-spacing", "font-family"]:
        raw = [
            match.group(0)
            for match in re.finditer(prop + r": ([^;]*);", rules)
            if "var(--" not in match.group(1) and match.group(1).strip() not in allowed
        ]
        assert not raw, f"{len(raw)} rule(s) set {prop} without a token: {raw[:4]}"

    # One monospace stack, one UI stack, and the deliverable's serif named as a different thing (GL-013)
    assert styles.count("Cascadia Mono") == 1
    assert styles.count("Noto Sans JP") == 1
    assert "--family-deliverable" in tokens and "Georgia" in tokens

    # Figures align in columns wherever a number appears, set once rather than per table (11_ui.md)
    assert styles.count("font-variant-numeric: tabular-nums") == 1
    document_rule = styles[styles.index("html, body {"):styles.index("\n", styles.index("html, body {"))]
    assert "font-variant-numeric: tabular-nums" in document_rule


def test_component_primitives_take_the_scale_instead_of_their_own_sizes() -> None:
    """A primitive that ships with `text-sm` renders one and a half times the label beside it."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    primitives = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "mockups" / "ui" / "components" / "ui").glob("*.tsx"))
    )
    for source, label in ((page, "page.tsx"), (primitives, "components/ui")):
        for banned in ["text-sm", "text-xs", "text-base", "text-[9px]", "text-[10px]", "text-[length:"]:
            assert banned not in source, f"{label} still sets type outside the scale: {banned}"
    for step in ["type-body", "type-caption"]:
        assert step in primitives


def test_a_comparison_varies_one_axis_which_may_be_a_property_of_its_base_view() -> None:
    """XC-202. Three sets alone cannot express stress against temperature, or a surface against a
    section - both everyday CAE figures. Sweeping one published property of the base View keeps
    "everything else is provably identical" true, because the varied thing is that View's own."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "type ComparisonAxis = 'case' | 'resultPosition' | 'camera' | 'quantity' | 'deformation' | 'representation'" in page
    assert "const comparisonPropertyAxes: ComparisonAxis[] = ['quantity', 'deformation', 'representation']" in page
    assert "基準ビュー自身のプロパティを振ります" in page
    # several saved Views are never the members: that case is the split
    assert "'view'" not in page.split("type ComparisonAxis")[1].split("\n")[0]


def test_a_comparison_holds_a_live_reference_and_deleting_its_base_view_names_it() -> None:
    """XC-202, against XC-109: a template copies and a comparison references. A live reference is why
    the comparison holds nothing of its own, and why deleting the View it points at is confirmed by
    naming what breaks rather than by repointing it somewhere plausible (XC-062)."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "生きた参照・「${baseViewName}」の編集が全ペインに反映" in page
    assert "usedBy?: string[]" in page
    assert "deleteItemReferences" in page
    assert "を参照している項目が{deleteItemReferences.length}件あります" in page
    assert "別の{itemHeader.itemLabel}へ付け替えることはしません" in page


def test_the_view_area_holds_two_item_kinds_chosen_at_creation() -> None:
    """XC-202. Until the kind was an attribute of the item, a comparison existed only as two scenario
    states: the creation dialogue offered no choice, the selector showed a plain name, and the rail
    could not know what it was editing."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "type WorkItemKind = 'single' | 'comparison'" in page
    assert "kind?: WorkItemKind; baseViewName?: string" in page
    assert "kind: 'comparison', baseViewName: '標準ビュー'" in page
    # the choice is made where the item is created
    assert 'className="creation-kind"' in page
    assert "['single', '単一ビュー'" in page
    assert "['comparison', '比較'" in page
    # and the open item, not the scenario variant, is what the rail and the canvas read
    assert "const isComparisonItem = openViewItem?.kind === 'comparison'" in page
    assert "const isComparison = isComparisonItem" in page
    assert "variant === 'comparison' ||" not in page


def test_the_kind_is_readable_in_the_selector_and_the_catalogue() -> None:
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "work-item-kind-badge" in page
    assert "基準：{selectedWorkItem.baseViewName}" in page
    assert "`基準ビュー：${entry.baseViewName}`" in page
    assert "item.kind === 'comparison' ? '比較' : itemHeader.itemLabel" in page


def test_a_comparison_names_the_tabs_it_borrows_instead_of_offering_a_copy() -> None:
    """XC-202 with XC-182: an editable copy would let one pane's material differ, which destroys the one
    guarantee a comparison makes. The borrowed tabs stay visible so the reader is told where the setting
    lives rather than left hunting for a tab that vanished."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "function BorrowedSettingPanel(" in page
    assert "この設定は基準ビューが持っています" in page
    assert "を編集" in page
    # the check sits above the per-tab dispatch, or materials, objects and text would never reach it
    borrowed = page.index("if (screen === 'view' && isComparisonItem &&")
    objects = page.index("if (screen === 'view' && tab.id === 'objects')")
    assert borrowed < objects
    for tab in ["'camera'", "'rendering'", "'background'", "'objects'", "'text'", "'materials'"]:
        assert tab in page[borrowed:objects]
    # 全体 and 出力 are the comparison's own and are not in that list
    assert "'overall'" not in page[borrowed:objects]
    assert "'output'" not in page[borrowed:objects]


def test_the_pane_badge_is_the_control_the_split_bar_says_it_is() -> None:
    """The split bar tells the reader to click the pane's subject to change it, so the badge has to be a
    control. It was a span: copy that promises an interaction nobody can perform."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert 'className="view-pane-subject" aria-label={`画面 ${index + 1} のケースとカメラを選ぶ`}' in page
    assert "bindPane(index, { caseName: item.name })" in page
    assert "bindPane(index, { cameraId: item.id })" in page
    # a comparison's panes come from its members, so there is nothing to pick there
    assert "{comparisonGrid ? (" in page


def test_the_layout_control_sets_the_arrangement_and_nothing_else_does() -> None:
    """XC-204 and XC-206: the property rail edits the saved item, so a session control there is the
    confusion XC-202 removed - but the canvas is not the answer either. One control in the area bar
    answers one question, how this canvas is laid out, for both kinds of item."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    overall = page[page.index("if (tab.id === 'overall') return"):page.index("if (tab.id === 'camera') return")]

    assert 'PropertyGroup title="画面分割"' not in overall
    assert "各画面のケース" not in overall
    assert "カメラ同期" not in overall
    # exactly one control sets the count, and it is the area bar's menu
    assert 'className="split-count"' not in page
    assert page.count("onSplitPanesChange(count)") == 1
    assert 'aria-label="画面レイアウト"' in page
    assert "work-area-split" in page
    assert page.count("カメラ同期") == 1  # the menu item; the canvas states nothing (XC-209)
    # what only makes sense once split is in the same menu, behind a guard, not on the canvas (XC-209)
    assert "{splitPanes > 1 && <>" in page
    assert "この分割は見ながら比べるための一時的な状態です。" in page


def test_the_layout_control_does_not_vanish_between_the_two_kinds_of_view_item() -> None:
    """XC-206: a control that disappears without saying why reads as a missing feature. A @Comparison's
    pane count is its member count, so the same control sets the columns those members wrap at instead -
    and it is still absent where there is no canvas of panes to lay out."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "const layoutControl: { kind: 'split' } | { kind: 'comparison'; members: number } | null" in page
    assert "scenario.screen !== 'view'" in page
    # an overlaid comparison draws one picture, so there is no arrangement to set
    assert "comparison.arrangement === 'grid' ? { kind: 'comparison', members:" in page
    assert "{layoutControl && !itemListOpen && <DropdownMenu>" in page
    assert "onComparisonColumnsChange(value)" in page
    assert "ペイン数はメンバー数（{layoutControl.members}件）です。" in page
    # the column count is set in exactly one place; the rail reports what it resolved to
    assert page.count("onComparisonColumnsChange") == 4
    assert 'SelectTrigger aria-label="列数"' not in page
    assert "列数は画面上部の「画面レイアウト」で選びます" in page


def test_a_comparison_marks_the_tabs_it_borrows_in_the_rail_itself() -> None:
    """Keeping the tabs answers "where did the material go"; marking them stops a reader opening six of
    them to find the two that are the comparison's own (XC-202)."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "const isBorrowed = (tabId: string) =>" in page
    assert "isBorrowed(tab.id) ? 'borrowed' : ''" in page
    assert "（基準ビューの設定）" in page
    assert "sidebar-tab-borrowed-mark" in page
    assert ".sidebar-tab-button.borrowed" in styles
    # the Outliner is the base View's too, and says whose it is
    assert 'className="outliner-borrowed"' in page
    assert "borrowedFrom={isComparisonItem ? baseViewName : null}" in page


def test_a_comparison_writes_down_the_values_every_pane_shares() -> None:
    """"Everything else is shared" is only checkable when the shared values are on screen. A comparison
    over cases has to say which single camera and which single result position every pane uses."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert 'className="comparison-shared"' in page
    assert "comparison.axis !== 'case' && <label><span>共有ケース</span>" in page
    assert "comparison.axis !== 'camera' && <label><span>共有カメラ</span>" in page
    assert "comparison.axis !== 'resultPosition' && <label><span>共有結果位置</span>" in page


def test_an_ordered_comparison_axis_can_divide_a_range_instead_of_listing_members() -> None:
    """A contact sheet over time should not require naming every position as a bookmark first. The
    reference distributes a swept parameter across the grid as a range - its comparative cue carries
    UpdateWholeRange, UpdateXRange and UpdateYRange beside UpdateValue (E-123)."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "memberMode: 'enumerate' | 'range'" in page
    assert "const orderedAxes: ComparisonAxis[] = ['resultPosition', 'deformation']" in page
    assert "function rangeMembers(count: number)" in page
    assert "<span>分割数</span>" in page
    # the axis says which quantities it can be, so time is findable without contradicting XC-131
    assert "resultPosition: '結果位置（時刻・モード・周波数）'" in page
    # a generated member lands on a position that exists, and says when it snapped
    assert "保存位置へ丸め" in page
    assert "snapped: Math.abs(value - raw[index]) > 1e-9" in page
    # two members on one stored position are reported rather than drawn as two identical panes
    assert "duplicate: snapped.indexOf(value) !== index" in page
    assert "同じ位置に解決するメンバーがあります" in page
    # and the canvas draws the generated members, not the enumerated list
    assert "rangeMembers(comparison.rangeCount).map((member) => member.label)" in page
    # the grid figures are derived from the same member list the canvas draws, so they cannot disagree
    assert "const comparisonColumns = comparisonGridColumns(effectiveMembers.length, comparison.columns)" in page
    assert "rows: number" not in page.split("type ComparisonModel")[1].split("}")[0]


def test_motion_follows_the_data_not_only_the_chosen_output_kind() -> None:
    """XC-131: a @Case may be steady, and then there is no axis to play along. XC-160 already required
    the playback overlay to be absent rather than disabled there; the same follows for the video output
    and its playback preset, which offered a range over an axis that does not exist."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "resultAxis: 'time' | 'steady'" in page
    assert "const caseHasResultAxis = (name: string)" in page
    assert "resultAxis: 'steady'" in page
    # absent, not disabled
    assert "{caseHasResultAxis(selectedCase) && (playbackVisible" in page
    # video and its preset name the reason instead of being offered
    # the video is refused for two distinct reasons now, and the flag names both (XC-212)
    assert 'disabled={!canWriteVideo}' in page
    assert "const canWriteVideo = hasResultAxis && !axisPinsEveryPane" in page
    assert "は定常結果です" in page
    assert "{outputMode === 'video' && canWriteVideo && <PropertyGroup title=\"再生プリセット\">" in page


def test_the_timeline_is_a_group_in_output_and_not_a_rail_tab() -> None:
    """The tab was abolished with the shot list: a timeline is six values, and the thing that names one
    is the video output (XC-200)."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    view_tabs = page[page.index("  view: ["):page.index("  graph: [")]

    assert "label: 'タイムライン'" not in view_tabs
    assert "id: 'timeline'" not in view_tabs
    assert "if (tab.id === 'timeline')" not in page
    assert '<PropertyGroup title="再生プリセット">' in page


def test_a_saved_result_position_can_be_created_on_the_axis_it_indexes() -> None:
    """XC-197 holds the saved positions on the @View, and the comparison, the timeline and the output
    all reference them - but nothing could add one: the list was a constant with no creation path."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "bookmarks: ResultBookmarkModel[]" in page.split("type ViewItemState")[1].split("}")[0]
    assert "現在位置を保存" in page
    assert "規則で追加" in page
    # the explicit kind keeps the position being looked at; the rule kinds state a condition
    assert "rule: { kind: 'explicit', position }" in page
    for kind in ["extremum", "crossing", "relative"]:
        assert f"SelectItem value=\"{kind}\"" in page
    assert "playback-bookmark-remove" in page
    assert "onBookmarksChange" in page


def test_the_canvas_carries_no_split_chrome_at_any_pane_count() -> None:
    """XC-209: the strip that appeared once split repeated the area bar four ways - the pane count, the
    camera sync, the way back to one pane, and a sentence teaching that a dropdown trigger can be
    clicked. Only two of its parts were unique, and they are in the bar's menu."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "pane-grid-controls" not in page and "pane-grid-controls" not in styles
    assert "pane-session-note" not in page and "pane-session-note" not in styles
    assert "1画面に戻す" not in page
    assert "panes === 1 ? 'compact' : ''" not in page
    # the two facts unique to a split are in the layout menu, behind the same guard
    menu = page[page.index("{splitPanes > 1 && <>"):page.index("</> : <>")]
    assert "onSelect={onPromoteSplit}" in menu
    assert "この分割は見ながら比べるための一時的な状態です。保存も書き出しもされません。" in menu
    # the dialogue it opens is the canvas's, so its open state is the shell's
    assert "const [splitPromoteOpen, setSplitPromoteOpen] = useState(false)" in page
    assert "{promoteOpen && <Dialog open onOpenChange={onPromoteOpenChange}>" in page


def test_a_comparison_grid_sets_its_columns_and_derives_its_rows() -> None:
    """XC-205: the rows absorb the remainder, so no column count can leave a member undrawn - which is
    the only reason the arrangement had been made read-only. The area bar's split control stays absent
    here because a comparison's panes are its members."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert "columns: 'auto' | number" in page
    assert "const comparisonGridColumns = (members: number, columns: 'auto' | number) =>" in page
    # the rows are computed, never stored and never set
    assert "rows:" not in page.split("type ComparisonModel")[1].split("}")[0]
    assert 'aria-label="行数" ' in page and "readOnly" in page
    assert 'aria-label="列数"' in page
    assert "自動（" in page
    # one rule feeds both the panel and the canvas, so they cannot state different grids
    assert page.count("comparisonGridColumns(") == 3
    assert page.count("const comparisonMemberLabels = (comparison: ComparisonModel) =>") == 1
    assert "'--comparison-columns': comparisonGridColumns(comparisonMembers.length, comparison.columns)" in page
    assert "repeat(var(--comparison-columns, 1), minmax(0, 1fr))" in styles
    assert "grid-template-rows: 1fr; grid-template-areas: none; }" not in styles


def test_entering_an_area_lands_on_its_declared_baseline_state() -> None:
    """XC-207: the View area opened on `assistant-drawer` because it sorts first, so the chat covered
    the 3D view the moment the area was entered - a demonstration state shown as the resting state."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    scenarios = json.loads(CATALOG.read_text(encoding="utf-8"))["scenarios"]

    assert "scenario.variant === 'default'" in page.split("function scenarioFor")[1].split("}")[0] + page.split("function scenarioFor")[1][:600]
    screens = {item["screen"] for item in scenarios}
    for screen in screens:
        defaults = [item for item in scenarios if item["screen"] == screen and item["variant"] == "default"]
        assert len(defaults) == 1, f"{screen} has {len(defaults)} baseline states"
    # the drawer is reached, never landed on
    assert "useState(scenario.variant === 'assistant-drawer')" in page


def test_a_composer_button_is_sized_for_its_label_not_for_an_icon() -> None:
    """XC-207: a blanket rule made every button in the composer a 27px circle, so 検索オフ and 詳細調査
    wrapped one character per line and spilled out of the frame. The blanket rule is the defect."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert ".chat-composer button { width: 27px" not in styles
    assert ".chat-composer .chat-icon-button { width: 27px; height: 27px;" in styles
    assert "white-space: nowrap" in styles.split(".chat-composer button {")[1].split("}")[0]
    # the narrow drawer drops the labels and keeps the meaning
    assert 'aria-label={searchLabel} title={searchLabel}' in page
    assert "{compact ? <Telescope size={13} /> : '詳細調査'}" in page
    assert "compact ? 'compact-composer' : ''" in page


def test_the_assistant_mark_is_a_chat_mark() -> None:
    """XC-207: a four-point sparkle is another assistant's brand mark."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    for site in ['<span className="chat-role-mark">', '<span className="assistant-mark">']:
        assert f"{site}<MessageSquareText size={{14}} /></span>" in page
    assert "Sparkles" not in page.split("function ChatScreen(")[1].split("function AssistantDrawer(")[0]
    assert "instruction-bar\"><MessageSquareText size={15} />" in page


def test_a_draggable_variable_row_is_drawn_as_something_that_can_be_picked_up() -> None:
    """XC-207: the rows were `border: 0; background: transparent`, so nothing but a sentence under the
    list said the drag existed."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    assert '<GripVertical size={11} className="variable-grip" aria-hidden="true" />' in page
    row = styles.split(".variable-row {")[1].split("}")[0]
    assert "border: 1px solid var(--line)" in row
    assert "cursor: grab" in row
    assert ".variable-row:active { cursor: grabbing; }" in styles


def test_the_first_view_tab_is_named_after_the_item_it_edits() -> None:
    """XC-207: `全体` drew no distinction in a rail where カメラ, 描画, 背景 and 出力 are the whole view
    too. Graph and Report keep it, where the contrast with their per-selection tabs is real."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "{ id: 'overall', label: 'ビュー'" in page
    assert "{ id: 'overall', label: 'グラフ'" in page
    assert "{ id: 'overall', label: 'レポート'" in page
    assert "label: '全体'" not in page
    assert "tab.id === 'overall' && screen === 'view' && isComparisonItem ? '比較' : tab.label" in page
    assert "selectedTab.id === 'overall' && screen === 'view' && isComparisonItem ? '比較' : selectedTab.label" in page


def test_the_first_tab_of_every_editing_area_names_its_item_and_shares_one_icon() -> None:
    """XC-208: `全体` said nothing in a rail where every other tab is the whole item too, and it wore
    LayoutTemplate - the icon of the one concept XC-149 renamed it away from."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    for label in ["'ビュー'", "'グラフ'", "'レポート'"]:
        assert f"{{ id: 'overall', label: {label}" in page
    assert page.count("id: 'overall', label: '") == 3
    assert page.count("icon: IdCard") == 3
    # LayoutTemplate now stands for one concept only
    for site in ["template: { label: 'テンプレート', icon: LayoutTemplate }", "<LayoutTemplate size={12} />テンプレートとして保存"]:
        assert site in page
    assert "icon: LayoutTemplate" not in page.split("const rightSidebarTabs")[1].split("\n}\n")[0]


def test_no_rail_icon_stands_for_two_unrelated_concepts() -> None:
    """11_ui.md asks a repeated concept to keep one icon; the inverse has to hold too, or the rail
    teaches a symbol and then contradicts it. SlidersHorizontal stood for pipeline 設定 and for the two
    `詳細` buckets at once."""
    import re
    page = CHAT_PAGE.read_text(encoding="utf-8")
    block = page[page.index("const rightSidebarTabs"):page.index("\n}\n", page.index("const rightSidebarTabs"))]
    by_icon: dict[str, list[tuple[str, str]]] = {}
    for tab_id, label, icon in re.findall(r"id: '([\w-]+)', label: '([^']+)'.*?icon: (\w+)", block):
        by_icon.setdefault(icon, []).append((tab_id, label))
    for icon, tabs in by_icon.items():
        ids = {tab_id for tab_id, _ in tabs}
        labels = {label for _, label in tabs}
        # one icon may cover several tabs only when they are the same concept: one shared id (the open
        # item, named per area) or one shared label (出力, テキスト).
        assert len(ids) == 1 or len(labels) == 1, f"{icon} stands for {sorted(tabs)}"


def test_the_data_and_contents_tabs_are_named_for_what_they_hold() -> None:
    """XC-208: `詳細` named a bucket. The graph tab holds the cases and series the graph is drawn from;
    the report tab holds the reference scope, the blocks and the commentary."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "{ id: 'series', label: '系列'" in page
    assert "{ id: 'contents', label: '内容'" in page
    assert "{ id: 'drafting', label: '執筆'" in page
    assert "label: '詳細'" not in page
    assert "if (tab.id === 'series') return" in page
    assert "if (tab.id === 'contents') return" in page
    assert "variant === 'series-unresolved' || variant === 'series' ? 'series'" in page
    assert "variant === 'commentary-review' || variant === 'drafting' ? 'drafting'" in page


def test_the_background_tab_uses_a_world_icon_rather_than_a_picture() -> None:
    """XC-208: the panel is solid, gradient, image or environment, so a picture icon names one of its
    four cases. The measured reference calls this tab World (E-120)."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "{ id: 'background', label: '背景'" in page
    assert "icon: Globe, scope: 'view' }" in page


def test_a_split_is_not_an_export_path_and_the_output_tab_says_so() -> None:
    """XC-210: XC-202 promised a split export "labelled a capture of a layout" and no such export was
    ever built - the output tab writes one named camera. The claim is removed rather than implemented,
    and stated where a user would expect the side-by-side they are looking at."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "画面分割は書き出しに含まれません" in page
    assert "{splitPanes > 1 && !isComparisonItem && <div className=\"property-unresolved\">" in page
    # the same fact where the split is made, naming the route that does produce a figure
    assert "並べた図を成果物にする場合は「この比較を保存」から比較項目を作ります。" in page
    # nothing offers to export the layout: the subject of an image is a camera, and the only mention of
    # the split layout left in the product is the shortcut that enters and leaves it
    assert "レイアウトの記録" not in page
    # the note may name the layout menu; the fields that choose what is written may not offer a layout
    fields = page[page.index('<label><span>成果物の種類</span><select value={outputMode}'):page.index('<OutputPreflightDialog')]
    assert "レイアウト" not in fields
    assert "<label><span>カメラ</span>" in fields
    assert page.count("分割レイアウト") == 2  # the shortcut, and the command it is bound to
    assert "{ name: '分割レイアウトへ入る・出る'" in page


def test_a_pipeline_unit_names_the_item_it_produces() -> None:
    """XC-211: XC-202 claims a pipeline can produce a comparison per case, and the unit editor had no way
    to say which item at all - only `ワークスペース項目` or `テンプレート`."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "source?: 'workspace' | 'template'" in page
    assert "itemName?: string" in page
    assert "workItemHeaderByScreen[selectedUnit.kind as ScreenId]?.items ?? []" in page
    assert "item.kind === 'comparison' ? '（比較）' : ''" in page
    # unresolved rather than defaulted (XC-001)
    assert "{!selectedUnit.itemName && <div className=\"property-unresolved\">" in page
    assert "既定の項目で代用することはありません。" in page
    # the seeded pipeline names real items, one of them a comparison
    assert "itemName: 'ケース比較' }" in page


def test_a_comparison_output_reports_its_bindings_instead_of_asking_again() -> None:
    """XC-212: the output tab was the single-View one unchanged, so it offered a camera picker beside a
    comparison whose axis was already the camera - two controls for one value, in a file that leaves the
    building."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "{isComparisonItem ? <>" in page
    assert "comparison.axis === 'camera' ? '比較の軸・メンバーごと' : '比較で共有・比較タブで設定'" in page
    assert "comparison.axis === 'resultPosition' ? '比較の軸・メンバーごと' : '比較で共有・比較タブで設定'" in page
    # a result-axis comparison has nothing left to play, and says so rather than writing stills
    assert "const axisPinsEveryPane = isComparisonItem && comparison.axis === 'resultPosition'" in page
    assert "この比較は結果位置を軸にしています" in page
    assert "{outputMode === 'video' && canWriteVideo && <PropertyGroup" in page


def test_the_graph_rail_is_five_sections_and_one_of_them_is_the_axis() -> None:
    """XC-213: the rail had a tab for the chart's dimension and another for its fonts, and no way to set
    an axis title, range or log scale at all - while the measured reference spends 100 of a chart's 115
    properties on axes (E-124)."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    graph_tabs = page[page.index("  graph: ["):page.index("  report: [")]
    ids = re.findall(r"id: '([\w-]+)'", graph_tabs)
    assert ids == ["overall", "series", "axes", "style", "output"]
    # one axis is chosen and the same fields serve it, rather than the fields repeating per axis
    assert "const [axis, setAxis] = useState<'x' | 'y' | 'y2'>('x')" in page
    assert "axisNames: Record<'x' | 'y' | 'y2', string>" in page
    assert page.count('<PropertyGroup title="範囲">') == 1
    assert ".axis-picker" in styles
    # a fixed range that cuts off data says so (XC-001)
    assert "固定範囲の外にある点は描かれません。" in page
    assert "{!axisAuto && <p className=\"property-editor-note warning\">" in page


def test_the_graph_rail_divides_what_a_series_is_from_how_it_looks() -> None:
    """XC-226: 系列 holds what each series plots; スタイル holds how each series looks, per series, and
    both address the same selection. XC-213 was right that appearance cannot be chart-wide - several
    series would be indistinguishable - and wrong to conclude it must therefore sit on the data row."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    editor = page[page.index("function GraphPropertyEditor("):page.index("function ReportPropertyEditor(")]
    series = editor[editor.index("if (tab.id === 'series') return"):editor.index("if (tab.id === 'axes') return")]
    style = editor[editor.index("if (tab.id === 'style') return"):]

    # what it plots
    for field in ("<span>X</span>", "<span>Y</span>", "<span>単位</span>", "<span>来歴</span>", "<span>使用する軸</span>"):
        assert field in series, field
    assert 'kind="line"' not in series and 'kind="marker"' not in series
    assert "<span>色</span>" not in series

    # how it looks, per series, in the style tab
    assert '<PropertyGroup title="系列の外観">' in style
    assert "<span>色</span>" in style
    assert 'label="線" kind="line"' in style
    assert 'label="マーカー" kind="marker"' in style

    # one selection, addressed from both
    assert 'className="series-chips"' in style
    assert "onClick={() => setActiveSeriesId(series.id)}" in style
    assert page.count("const [activeSeriesId, setActiveSeriesId]") == 1

    # still deferring to the applied asset, not to a chart-wide control (XC-224)
    assert "{ value: 'theme', label: 'テーマ', sample: assetDefaults.marker" in page
    assert '<PropertyGroup title="系列の既定">' not in page


def test_each_graph_appearance_property_has_exactly_one_editable_control() -> None:
    """XC-224: three times the same duplication was reported, and twice it was answered by renaming.
    This is the check that would have caught it - not what the controls are called, but how many of them
    can change one thing."""
    import collections
    page = CHAT_PAGE.read_text(encoding="utf-8")
    editor = page[page.index("function GraphPropertyEditor("):page.index("function ReportPropertyEditor(")]
    marks = [(m.group(1), m.start()) for m in re.finditer(r"^  if \(tab\.id === '(\w+)'\) return", editor, re.M)]
    fallback = re.search(r"^  return <div className=\"property-editor\">", editor, re.M).start()
    blocks = {name: editor[start:(marks[i + 1][1] if i + 1 < len(marks) else fallback)]
              for i, (name, start) in enumerate(marks)}
    blocks["output"] = editor[fallback:]

    APPEARANCE = ("線", "マーカー", "線幅", "配色", "背景")
    where: dict[str, list[str]] = collections.defaultdict(list)
    for tab, body in blocks.items():
        for m in re.finditer(r'<(?:label[^>]*><span>([^<]+)</span>|VisualOptions label="([^"]+)")', body):
            name = m.group(1) or m.group(2)
            if name not in APPEARANCE:
                continue
            window = body[m.start():m.start() + 300]
            if "readOnly" in window or "palette-readout" in window:
                continue  # a read-out is not a control
            where[name].append(tab)

    for name, tabs in where.items():
        assert len(tabs) == 1, f"{name} can be changed in {tabs}"
    # appearance is now all in one tab, and it is the style tab (XC-226)
    assert where["線"] == ["style"]
    assert where["マーカー"] == ["style"]
    assert where["配色"] == ["style"]


def test_the_graph_item_tab_holds_which_cases_and_no_two_fields_share_a_name() -> None:
    """XC-221: a series spans every selected case, so the case selection is the graph's, not a series'.
    And the item tab had two fields called タイトル - the text and its visibility."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    item = page[page.index("if (tab.id === 'overall') return", page.index("function GraphPropertyEditor(")):page.index("if (tab.id === 'series') return")]
    assert '<PropertyGroup title="ケース選択">' in item
    assert '<PropertyGroup title="集約"' in item
    assert "<span>タイトルを表示</span>" in item
    assert "<span>凡例を表示</span>" in item
    labels = re.findall(r"<span>([^<]+)</span>", item)
    duplicated = {label for label in labels if labels.count(label) > 1}
    assert not duplicated, f"two fields share a name in one tab: {duplicated}"


def test_report_writing_is_a_reviewed_sequence_rather_than_a_group_of_settings() -> None:
    """XC-214: the measured tool produces an outline before content and generates on the user's word,
    and its vendor states the output must be human-reviewed (E-126). The rail had four settings in a
    group called コメント inside the contents tab, and no way to reach the review or see its state."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    report_tabs = page[page.index("  report: ["):page.index("  chat: [")]
    ids = re.findall(r"id: '([\w-]+)'", report_tabs)
    assert ids == ["overall", "contents", "drafting", "style", "output"]
    assert "const [draftState, setDraftState] = useState<'none' | 'review' | 'applied'>" in page
    assert "下書きを作る" in page
    assert "確認待ち・4文＋除外2件" in page
    assert "取り込むまでレポートは変わりません。" in page
    # an unset model blocks the action rather than annotating it
    assert "生成コメントは現在利用できません" in page
    # the theme is one tab: page, palette and type together
    style = page[page.index("if (tab.id === 'style') return", page.index("function ReportPropertyEditor(")):page.index("if (tab.id === 'drafting') return")]
    for group in ("ページ", "共通要素", "アートスタイル", "文字表現", "埋め込み"):
        assert f'title="{group}"' in style, group


def test_appearance_is_chosen_from_drawn_samples_with_the_name_kept() -> None:
    """XC-215: neither measured reference asks for an appearance by name - ParaView renders every preset
    to a pixmap and reflows them into a grid, Blender ships 42 studio-light previews and draws them
    (E-128). One control does this, and the name stays beside the picture."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    styles = CHAT_STYLES.read_text(encoding="utf-8")
    samples = OPTION_SAMPLES.read_text(encoding="utf-8")

    assert "export function VisualOptions(" in samples
    assert "export function OptionSample(" in samples
    assert page.count("function VisualOptions(") == 0, "one implementation, imported"
    assert "import { VisualOptions, OptionSample } from '@/components/workspace/option-samples'" in page

    # every appearance choice named by the decision is drawn
    for kind in ("chart", "palette", "background", "line", "marker", "page", "margin", "columns", "figure", "representation", "grade"):
        assert f'kind="{kind}"' in page, kind

    # the name is kept: each option renders a label, and the group carries an accessible name
    assert '<small>{option.label}</small>' in samples
    assert 'role="radiogroup"' in samples and 'aria-label={label}' in samples
    assert 'aria-checked={value === option.value}' in samples

    # samples are drawn, not loaded - the mockup ships no image for them
    assert "<img" not in samples and "next/image" not in samples
    assert ".visual-option-sample" in styles

    # a typeface is shown in itself
    assert "fontFamily: fontStacks[bodyFont]" in page
    assert "font-specimen" in page and ".font-specimen" in styles


def test_settings_that_are_not_about_appearance_stay_as_text() -> None:
    """XC-215: a picture of `PNG` teaches nothing. The drawn samples are bounded to appearance."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    for text_only in (">PNG</option>", ">JPEG</option>", ">MP4</option>", ">CSV</option>"):
        assert text_only in page, text_only
    assert 'kind="format"' not in page
    assert 'kind="unit"' not in page


def test_the_shelf_and_the_rail_name_their_seam_the_same_way_everywhere() -> None:
    """XC-216: the shelf chooses a reusable resource, the rail adjusts the item and names what is
    applied. The field was called アセット in Graph and スタイル in Report - one concept, two names."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert page.count("<span>適用中</span>") == 2
    assert "<span>アセット</span>" not in page
    # the rail never grows the shelf's browsing apparatus (XC-149)
    rail = page[page.index("function GraphPropertyEditor("):page.index("function SimulationPropertyEditor(")]
    for browser in ("library-source", "library-sort", "library-tag", "setSource(", "setSort("):
        assert browser not in rail, browser
    # a template is named as provenance, not as a live binding: XC-109 makes it a copy with no link
    assert '<label><span>テンプレート</span><input value="技術メモ・サンプル / リビジョン未接続" readOnly />' in rail


def test_every_rail_tab_fed_by_the_library_says_which_category_feeds_it() -> None:
    """XC-216: after XC-214 merged three tabs into one theme, three library categories write into that
    one tab. Saying which group each supplies is what makes applying two of them readable as composition
    rather than a conflict."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "素材ライブラリの「レイアウト」はページと共通要素、「スタイル」は配色と図表、「テキスト」は書体に適用されます。互いに上書きしません。" in page
    assert "素材ライブラリの「スタイル」は配色とプロットの既定に、「テキスト」は書体に適用されます。" in page
    assert "再利用する背景は素材ライブラリから適用し、このタブでは現在のビューへの配置を調整します。" in page
    # the library still offers those categories, so the statement is about something that exists
    categories = page[page.index("const libraryCategories"):page.index("const libraryCategoryMeta")]
    assert "graph: ['template', 'style', 'fonts']" in categories
    assert "report: ['template', 'layout', 'style', 'fonts']" in categories


def test_the_graph_panels_are_written_in_the_order_the_rail_shows_them() -> None:
    """XC-221: they were not - overall, style, axes, series against a rail reading overall, series,
    axes, style - and a test slicing "this tab" by the next tab's marker read an empty string and
    asserted nothing against it. Twice, in one sitting."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    editor = page[page.index("function GraphPropertyEditor("):page.index("function ReportPropertyEditor(")]
    written = re.findall(r"if \(tab\.id === '(\w+)'\) return", editor)

    graph_tabs = page[page.index("  graph: ["):page.index("  report: [")]
    shown = re.findall(r"id: '([\w-]+)'", graph_tabs)

    # the last section is the fallback `return`, so it is not in the written list
    assert written == shown[:-1], f"written {written} against rail {shown}"


def test_no_graph_control_name_means_two_things_in_two_tabs() -> None:
    """XC-222: five did. 軸 was the axis a series is drawn against and the size of an axis label; 種類
    was the chart's kind and the output's; マーカー and 線幅 were a value and its default, named
    identically in adjacent tabs, which is what made the pair read as a duplicate rather than as a
    default and an override."""
    import collections
    page = CHAT_PAGE.read_text(encoding="utf-8")
    editor = page[page.index("function GraphPropertyEditor("):page.index("function ReportPropertyEditor(")]
    marks = [(m.group(1), m.start()) for m in re.finditer(r"^  if \(tab\.id === '(\w+)'\) return", editor, re.M)]
    fallback = re.search(r"^  return <div className=\"property-editor\">", editor, re.M).start()
    blocks = {name: editor[start:(marks[i + 1][1] if i + 1 < len(marks) else fallback)]
              for i, (name, start) in enumerate(marks)}
    blocks["output"] = editor[fallback:]

    where: dict[str, set[str]] = collections.defaultdict(set)
    for tab, body in blocks.items():
        names = re.findall(r"<label[^>]*><span>([^<]+)</span>", body) + re.findall(r'<VisualOptions label="([^"]+)"', body)
        for name in names:
            if name.strip():
                where[name].add(tab)

    # The one exemption, stated rather than silent: the graph's title text and the size of its type.
    # The group name 書体 and the pt value carry the difference, and the alternatives -
    # 「タイトルの大きさ」 and its siblings - wrap in a 68px label column, which is its own defect.
    exempt = {"タイトル": {"overall", "style"}}
    collisions = {name: tabs for name, tabs in where.items() if len(tabs) > 1 and exempt.get(name) != tabs}
    assert not collisions, f"one name, two meanings: { {k: sorted(v) for k, v in collisions.items()} }"


def test_the_series_colour_is_one_decision_without_an_inert_control() -> None:
    """XC-222: the colour well sat beside the mode and did nothing while the mode was パレット順, and
    the palette it would have drawn from was reported again on a row of its own - three elements for
    one decision, one of them with no effect."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert "const [seriesColour, setSeriesColour] = useState('palette')" in page
    assert "{seriesColour === 'palette'" in page
    # the well exists only in the branch where it does something
    colour = page[page.index("<span>色</span>"):page.index('label="線" kind="line"')]
    assert colour.count('type="color"') == 1
    assert "seriesColour === 'palette'" in colour
    assert "この系列はパレットの" in colour


def test_the_output_tab_shows_one_format_field_at_a_time() -> None:
    """The source names 形式 four times; they are the four mutually exclusive branches of 成果物の種類,
    so one renders. Asserted rather than assumed, because a repeated label is exactly what a reader
    reports as a duplicate."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    editor = page[page.index("function GraphPropertyEditor("):page.index("function ReportPropertyEditor(")]
    output = editor[re.search(r"^  return <div className=\"property-editor\">", editor, re.M).start():]

    assert output.count("<span>形式</span>") == 4
    for kind in ("image", "vector", "data", "animation"):
        assert f"outputKind === '{kind}'" in output


def test_a_colour_map_is_chosen_by_its_gradient_wherever_one_is_chosen() -> None:
    """XC-223: the reference ships `pqPresetToPixmap` for exactly this chooser (E-128), and in this
    product a wrong colour map is a wrong picture rather than an ugly one. Both places named one by a
    word: the scalar object's map, and the material editor's preset."""
    page = CHAT_PAGE.read_text(encoding="utf-8")
    samples = OPTION_SAMPLES.read_text(encoding="utf-8")

    assert page.count('kind="colormap"') == 2
    assert "const colourMaps: Record<string, string> = {" in samples
    for name in ("technical", "viridis", "grayscale", "coolwarm", "inferno"):
        assert f"  {name}:" in samples
    assert '<select defaultValue="technical"><option value="technical">技術表示</option></select>' not in page


def test_the_other_subjects_that_have_a_picture_show_it() -> None:
    """XC-223 extends XC-215 past appearance settings: a view direction, a glyph and a typeface all have
    pictures, and were words."""
    page = CHAT_PAGE.read_text(encoding="utf-8")

    assert 'kind="viewdir"' in page
    assert 'kind="glyph"' in page
    # the graph's typeface is rendered in itself, as the report's already was
    assert page.count("fontFamily: fontStacks[") >= 4
    assert page.count("font-specimen") == 2  # the graph's and the report's
    # and the applied style asset shows what it applies
    assert '<span>見本</span><span className="palette-readout"><OptionSample kind="palette" value={palette} /><OptionSample kind="background"' in page


def test_a_sample_fills_its_tile() -> None:
    """XC-223: at four columns in a 286px rail, 5px of padding a side plus the border spent about a
    fifth of every sample's width on air. The label is padded; the sample is not."""
    styles = CHAT_STYLES.read_text(encoding="utf-8")

    tile = styles.split(".visual-option {")[1].split("}")[0]
    assert "padding: 0" in tile
    assert "overflow: hidden" in tile  # the tile clips the sample to its own radius
    label = styles.split(".visual-option small {")[1].split("}")[0]
    assert "padding:" in label
    # the samples themselves no longer round their own corners inside a clipping tile
    band = styles.split(".option-sample-band {")[1].split("}")[0]
    assert "border-radius" not in band


def test_no_rail_lets_two_controls_change_the_same_thing() -> None:
    """XC-225 generalises XC-222 and XC-224 past the graph. Within one property rail, a reader scanning
    for a control finds one. The check is per editor, because the same word naming a different object's
    property in a different area is not a collision - every item has a 名前."""
    import collections
    page = CHAT_PAGE.read_text(encoding="utf-8")
    editors = ["ViewPropertyEditor", "ViewObjectPropertyEditor", "ViewTextPropertyEditor",
               "ViewMaterialPropertyEditor", "GraphPropertyEditor", "ReportPropertyEditor",
               "SimulationPropertyEditor", "NetworkPropertyEditor", "AutomationPropertyEditor"]
    starts = sorted(((name, page.index(f"function {name}(")) for name in editors), key=lambda kv: kv[1])

    # The one exemption, stated: the graph's title text and the size of its type (XC-222).
    exempt = {("GraphPropertyEditor", "タイトル")}
    collisions = []
    for i, (name, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(page)
        body = page[start:end]
        marks = [(m.group(1), m.start()) for m in re.finditer(r"^  if \(tab\.id === '(\w+)'\) return", body, re.M)]
        fallback = re.search(r"^  return <div className=\"property-editor\">", body, re.M)
        blocks = {}
        if marks:
            for k, (tab, at) in enumerate(marks):
                blocks[tab] = body[at:(marks[k + 1][1] if k + 1 < len(marks) else (fallback.start() if fallback else len(body)))]
            if fallback:
                blocks["(last)"] = body[fallback.start():]
        else:
            blocks["(all)"] = body

        where: dict[str, set[str]] = collections.defaultdict(set)
        for tab, block in blocks.items():
            for m in re.finditer(r'<(?:label[^>]*><span>([^<]+)</span>|VisualOptions label="([^"]+)")', block):
                control = m.group(1) or m.group(2)
                window = block[m.start():m.start() + 300]
                if "readOnly" in window or "palette-readout" in window or not control.strip():
                    continue  # a read-out is not a control
                where[control].add(tab)
        for control, tabs in where.items():
            if len(tabs) > 1 and (name, control) not in exempt:
                collisions.append(f"{name}: {control} in {sorted(tabs)}")

    assert not collisions, "two controls change one thing: " + "; ".join(collisions)
