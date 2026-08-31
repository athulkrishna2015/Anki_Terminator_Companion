# Architecture

Technical reference for the Anki Terminator Companion addon internals.

---

## How It Works

The companion addon **never modifies files** in the original addon's directory. At Anki startup, it:

1. Imports the original addon's Python modules via `importlib.import_module()`
2. Saves references to original methods
3. Defines replacement functions with enhanced behavior
4. Assigns the replacements back onto the original classes (`monkey-patching`)

This runs entirely in-memory and is completely reversible on shutdown.

---

## Patch Pipeline

Entry point: `addon/__init__.py` calls `apply_patches()` from `addon/patch_1468920185_anki_terminator/__init__.py`.

```
__init__.py
  |
  +-- load_companion_patches()
  |     |
  |     +-- patch_1468920185_anki_terminator/__init__.py  (orchestrator)
  |           |
  |           +-- 1. ad_blocker_patch.py      (O(1) domain matching)
  |           +-- 2. css_patch.py             (CSS animation disabler)
  |           +-- 3. lifecycle_patch.py       (freeze/thaw, nav, AI dropdown, response monitor)
  |           +-- 4. context_menu_patch.py    (rich paste, cloze censor, add-to-card)
  |           +-- 5. popup_nav_patch.py       (popup window navigation controls)
  |
  +-- init_config()  -->  config_ui.py
  |     |
  |     +-- config_ui_general_tab.py
  |     +-- config_ui_logs_tab.py
  |     +-- tab_support.py (SupportTabMixin)
  |
  +-- check_support_on_update()  [gui_hooks.profile_did_open]
```

---

## Patch Details

### 1. Ad-Blocker Patch (`ad_blocker_patch.py`)

**Target:** `1468920185.ad_blocker`

| Attribute | Detail |
|---|---|
| Hooked method | `AdBlocker.interceptRequest` |
| Strategy | Separates pure domain rules (~44k) from path-specific rules (~2k). Pure domains use `O(1)` set-suffix lookup. |
| Fallback | Path-specific rules use original `in` substring check. |
| Lazy init | Ad-blocker rule compilation is deferred until the first network request, not at import time. |

### 2. CSS Patch (`css_patch.py`)

**Target:** `1468920185.dock_web_view.ResizableWebView.inject_javascript`

| Attribute | Detail |
|---|---|
| Hooked method | `inject_javascript` |
| Injection target | Only Gemini (`Google_Bard`) pages |
| CSS injected | Disables `animation`, `transition`, `backdrop-filter`, `background` animations, `@keyframes` |
| When | On every `loadFinished` signal from the sidebar webview |

### 3. Lifecycle Patch (`lifecycle_patch.py`)

**Target:** `1468920185.dock_web_view` (multiple classes)

This is the largest patch (~1080 lines). It hooks:

| Hooked Target | Purpose |
|---|---|
| `ResizableWebView.__init__` | Injects nav buttons, address bar, progress bar, snapshot label, hover tracking, response monitor |
| `ResizableWebView.enterEvent` | Thaws (unfreezes) sidebar on hover |
| `ResizableWebView.leaveEvent` | Freezes sidebar when mouse leaves |
| `ResizableWebView.last_text_toolbar` | Replaces static "AI" button with dropdown `QToolButton` |
| `ResizableWebView.change_AI_type` | Syncs favicon/icon on AI switch |
| `ResizableWebView.auto_click_v2` | 200ms thaw delay before JS execution |
| `ResizableWebView.handle_audio_state` | Suppresses audio timer when frozen/hidden |
| `ResizableWebView.set_last_text` | HTML cleanup before sending to AI |
| `ResizableWebView.get_field_text` | Multiple fields concatenation |
| `QWebEnginePage.runJavaScript` | Thaws sidebar + starts response monitoring on submit actions |
| `QClipboard.setText` / `setMimeData` | Clipboard privacy hints + restore scheduling |
| `SetPopupConfig.__init__` | Injects companion checkboxes into original config dialog |
| `SetPopupConfig.save_config_fontfamiles` | Saves companion config values from original dialog |

**Freeze/Thaw cycle:**
1. After page load completes, a 5-second timer starts
2. If the sidebar is not hovered and not responding, it captures a screenshot (`webview.grab()`)
3. The screenshot is shown in a `QLabel` overlay, and `QWebEnginePage.LifecycleState.Frozen` is set
4. On hover, the screenshot hides and lifecycle state returns to `Active`
5. Response monitoring polls `document.body.innerText.length` — after 3 stable checks (6s), freezing resumes

**Response monitoring:**
- Triggered by `runJavaScript` calls containing `replaceValue` or `execCommand` (prompt submissions)
- Polls text length every 2 seconds
- After 3 consecutive equal lengths, marks as finished and re-freezes

### 4. Context Menu Patch (`context_menu_patch.py`)

**Target:** `1468920185.context_menu.add_fields`

| Hooked Target | Purpose |
|---|---|
| `context_menu` | Adds "Add to new card" and "Explain cloze" menu actions |
| `_add_text_to_card` | Rich HTML extraction via JS range cloning, MathJax/KaTeX/Wikipedia formula recovery, HTML comment stripping |
| `ResizableWebView.contextMenu` | Preserves AI-Hints JSON blocks during right-click insert |

### 5. Popup Navigation Patch (`popup_nav_patch.py`)

**Target:** `1468920185.dock_web_view.CustomWebEnginePage`

| Attribute | Detail |
|---|---|
| Hooked method | `createWindow` |
| Purpose | Injects back/forward/reload/home buttons + address bar into popup windows |
| UI | Horizontal toolbar inserted at top of popup `QVBoxLayout` |
| Signals | Button clicks connected to `web_view.back()`/`forward()`/`reload()`, address bar `returnPressed` triggers URL/search navigation |

---

## UI Components

### Sidebar (ResizableWebView)

```
QVBoxLayout
  +-- QToolBar (header)
  |     +-- AI Dropdown (QToolButton + QMenu)
  |     +-- Nav buttons (<, >, R, H)
  |     +-- Companion Config button (C)
  |     +-- Original settings cogwheel
  +-- QToolBar (prompt area)
  |     +-- Mnemonic button (original)
  |     +-- Address bar (QLineEdit in QWidget)
  +-- QWebEngineView (webview)
  +-- QLabel (snapshot overlay - for freeze)
  +-- QProgressBar (2px, top of sidebar)
```

### Config Dialog (CompanionConfigDialog)

```
QDialog (non-modal, allows Anki use while open)
  +-- QTabWidget
  |     +-- Tab 0: GeneralTab (QScrollArea-like with checkboxes/spinboxes)
  |     +-- Tab 1: LogsTab (QPlainTextEdit + Refresh/Copy/Clear buttons)
  |     +-- Tab 2: Support (QR codes, Ko-fi widget, opt-out checkbox)
  +-- Save Settings button
  +-- Close button
```

### Popup Window (from createWindow)

```
QWidget (Qt.WindowType.Window)
  +-- QHBoxLayout (nav toolbar, injected by companion)
  |     +-- QPushButton (<, >, R, H)
  |     +-- QLineEdit (address bar)
  +-- QWebEngineView (original)
```

---

## Logger System (`logger.py`)

| Component | Detail |
|---|---|
| Class | `CompanionLogger` (singleton: `companion_logger`) |
| Storage | In-memory `list` + async file write via `queue.Queue` + daemon thread |
| Log file | `addon/companion.log` (truncated on startup) |
| Callbacks | GUI tabs register via `register_callback(cb)` for live updates |
| Thread safety | `queue.Queue` for file writes, callbacks called on main thread |
| API | `.log(msg)`, `.get_logs()`, `.get_recent_logs(n)`, `.clear()` |

---

## Target Addon Detection

The orchestrator tries to import modules from two known addon IDs:

| ID | Addon |
|---|---|
| `1468920185` | Anki Terminator V2 (original) |
| `1448033349` | Anki Terminator V2 (alternate build) |

Only detected addons are patched. If neither is found, a log message is emitted and the companion becomes a no-op.
