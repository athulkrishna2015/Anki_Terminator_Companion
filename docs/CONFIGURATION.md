# Configuration Reference

Complete reference for all configuration keys, default values, JSON structures, and runtime settings.

---

## config.json (Defaults)

This file ships with the addon and provides initial values for fresh installs.

```json
{
    "enable_lifecycle_freezing": true,
    "enable_adblocker_optimization": true,
    "enable_css_optimization": true,
    "enable_html_cleanup": true,
    "enable_image_pasting": true,
    "enable_ai_hints_optimization": true,
    "enable_right_click_hints_preservation": true,
    "enable_add_to_new_card": true,
    "enable_progress_bar": true,
    "enable_persistent_view": true,
    "enable_clipboard_clearing": true,
    "show_wiki_button": true,
    "show_donate_button": true,
    "search_engine": "Google",
    "custom_search_url": "https://www.google.com/search?q=",
    "thaw_duration_seconds": 30,
    "send_multiple_fields": false
}
```

---

## Config Keys

### Optimization Toggles

| Key | Type | Default | Description |
|---|---|---|---|
| `enable_lifecycle_freezing` | `bool` | `true` | Enables smart CPU freezing — captures a screenshot and freezes the Chromium lifecycle state 5s after page load, thawing on hover or prompt submission. |
| `enable_adblocker_optimization` | `bool` | `true` | Enables O(1) domain suffix set lookup for ad-blocker rules, replacing linear scanning of ~46k domains. |
| `enable_css_optimization` | `bool` | `true` | Injects CSS into Gemini pages to disable animations, transitions, backdrop-filters, and glow gradients. |
| `enable_html_cleanup` | `bool` | `true` | Strips HTML tags from card fields before sending prompts to AI, preserving clean text and LaTeX. |
| `enable_ai_hints_optimization` | `bool` | `true` | Fast-path bypass for AI-Hints regex scans when no hints are present in the field text. |
| `enable_right_click_hints_preservation` | `bool` | `true` | Preserves AI-Hints JSON data blocks at the end of fields during right-click context menu inserts. |
| `enable_image_pasting` | `bool` | `true` | Automatic image clipboard pasting (legacy feature, mostly handled by original addon now). |

### Feature Toggles

| Key | Type | Default | Description |
|---|---|---|---|
| `enable_add_to_new_card` | `bool` | `true` | Adds "Add to new card" option in the right-click context menu of the sidebar. |
| `enable_progress_bar` | `bool` | `true` | Shows a 2px blue progress bar at the top of the sidebar during page loads. |
| `enable_persistent_view` | `bool` | `true` | Keeps the current page visible (as a screenshot) while the next page loads, preventing white flash. |
| `enable_clipboard_clearing` | `bool` | `true` | Clears system clipboard 1.5s after sending a prompt to prevent clipboard pollution. |

### Toolbar Settings

| Key | Type | Default | Description |
|---|---|---|---|
| `show_wiki_button` | `bool` | `true` | Shows/hides the original addon's "?" (Wiki) button in the sidebar toolbar. |
| `show_donate_button` | `bool` | `true` | Shows/hides the original addon's donate button in the sidebar toolbar. |

### Search & Navigation

| Key | Type | Default | Description |
|---|---|---|---|
| `search_engine` | `string` | `"Google"` | Active search engine. Options: `"Google"`, `"DuckDuckGo"`, `"Bing"`, `"Custom"`. |
| `custom_search_url` | `string` | `"https://www.google.com/search?q="` | Search URL template. The query is appended as a URL-encoded parameter. Used when `search_engine` is `"Custom"` or as the actual engine URL. |

### Behavior Settings

| Key | Type | Default | Description |
|---|---|---|---|
| `thaw_duration_seconds` | `int` | `30` | How long (in seconds) the sidebar stays in Active (unfrozen) state after clicking an AI prompt button. Range: 5–300. |
| `send_multiple_fields` | `bool` | `false` | When enabled, concatenates all non-empty card fields as `FieldName: FieldValue` instead of sending only the priority field. |

---

## meta.json (Runtime State)

Managed by Anki's addon manager. The companion reads/writes specific keys.

```json
{
    "last_seen_version": "1.8.0",
    "supporter_opt_out": false,
    "config": { ... },
    "disabled": false,
    "mod": 0,
    "conflicts": [],
    "max_point_version": 0,
    "min_point_version": 0,
    "branch_index": 0,
    "update_enabled": true
}
```

| Key | Used By | Description |
|---|---|---|
| `last_seen_version` | `check_support_on_update()` | Tracks the last version the user saw. Compared against `VERSION` file to trigger the Support tab on update. |
| `supporter_opt_out` | `SupportTabMixin` | When `true`, suppresses the automatic Support tab popup after addon updates. |

---

## manifest.json (Addon Metadata)

```json
{
    "name": "Anki Terminator Companion",
    "package": "Anki_Terminator_Companion",
    "desc": "Companion addon for Anki Terminator V2...",
    "version": "1.8.0",
    "human_version": "1.8.0",
    "min_point_version": 1,
    "max_point_version": 250902
}
```

| Key | Description |
|---|---|
| `version` / `human_version` | SemVer version, kept in sync by `bump.py`. |
| `min_point_version` | Minimum Anki point version required. |
| `max_point_version` | Maximum Anki point version supported. |

---

## VERSION File

Single-line text file containing the current SemVer version string (e.g., `1.8.0`). Used by:
- `bump.py` — reads and writes during version bumps
- `make_ankiaddon.py` — reads during build
- `check_support_on_update()` — compares against `meta.json:last_seen_version`

---

## Companion Log Format

Each line in `companion.log` follows:

```
[HH:MM:SS.mmm] [Component Name] Message text
```

### Log Components

| Component | Source File | What It Logs |
|---|---|---|
| `Lifecycle Patch` | `lifecycle_patch.py` | Freeze/thaw events, snapshot captures, nav injection, progress bar state, load events |
| `AdBlocker Patch` | `ad_blocker_patch.py` | Rule optimization stats, blocked ad URLs |
| `CSS Patch` | `css_patch.py` | Gemini CSS injection |
| `Context Menu Patch` | `context_menu_patch.py` | Right-click actions, HTML extraction, cloze censoring |
| `Popup Nav Patch` | `popup_nav_patch.py` | Popup window nav control injection |
| `AI Dropdown` | `lifecycle_patch.py` | AI switching, hard refresh, sound playback |
| `Clipboard Patch` | `lifecycle_patch.py` | Prompt copy interception, privacy hints, restore scheduling |
| `AI-Hints Patch` | `__init__.py` (orchestrator) | AI-Hints optimization hook status |
| `Sync Icon` | `lifecycle_patch.py` | Sidebar/dock icon synchronization |

### Log Sample

```
[19:58:34.325] Initializing Anki Terminator Companion...
[19:58:34.330] [Terminator Companion] Found target addon 1468920185. Applying patches...
[19:58:34.333] [AdBlocker Patch] Successfully hooked AdBlocker interceptRequest with O(1) matching & diagnostic logs.
[19:58:34.345] [Lifecycle Patch] Initiating Flicker-Free QStackedWidget and Response Monitor hooks...
[19:58:43.475] [AI Dropdown] Successfully replaced 'AI' button with QToolButton text dropdown.
[19:58:43.530] [Lifecycle Patch] Injected Nav buttons and Config button into QToolBar header.
[19:58:52.645] [Lifecycle Patch] webview.loadStarted triggered.
[20:00:07.065] [Popup Nav Patch] Injected navigation controls into popup window.
```

---

## Saved Config Location

User-modified config is stored by Anki at:

```
~/.local/share/Anki2/<profile>/addons21/Anki_Terminator_Companion/config.json
```

On Windows:
```
%APPDATA%\Anki2\<profile>\addons21\Anki_Terminator_Companion\config.json
```

The companion also syncs `send_multiple_fields` into the original addon's config:
```
~/.local/share/Anki2/<profile>/addons21/1468920185/config.json
```
