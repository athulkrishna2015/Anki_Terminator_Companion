# Changelog

All notable changes to the Anki Terminator Companion addon will be documented in this file.

### Unreleased
- **Gemini scroll-to-top after deep idle (bug fix)**:
  - After a long idle the companion unloads the sidebar page to `about:blank` so Chromium frees the renderer's heap, then restores the original URL on the next thaw. Restoring reloaded the page from scratch, which reset the scroll position to the top — so the latest response (at the bottom) disappeared and the user had to scroll all the way down again.
  - The scroll position is now captured (via a brief reactivation of the frozen page) before the unload, and restored with `window.scrollTo` once the reloaded page has painted. The frozen snapshot also stays visible until after the restore, so there is no flash of the top of the page.
  - No regression if the scroll capture fails: the unload still happens and the page simply stays at the top, as before.

### October 15, 2026 (v1.9.2)
- **Sidebar memory/CPU leaks (bug fixes)**:
  - **Response monitor re-entrancy**: every prompt submission runs JS containing `replaceValue`/`execCommand`, and each one started *another* 2s polling chain on the same sidebar. Those chains shared `stable_checks` but each ran its own `document.body.innerText.length` round-trip to the renderer every 2 seconds for as long as the response stayed unstable, so N submissions meant N concurrent pollers. `start_response_monitoring` now keeps a single chain per sidebar (`_companion_monitor_running`) and resets only the stability counter when a new prompt arrives mid-response.
  - **Popup navigation accumulation**: the target add-on reuses one `mw.AnkiTerminator_new_dialog` for every popup and only clears it when the sidebar closes, so each popup stacked another four buttons, a line edit and their signal closures onto the same layout for the lifetime of the sidebar. The previous bar is now located by object name and removed before the new one is inserted.
  - **Double-apply guards**: `lifecycle_patch`, `css_patch` and `popup_nav_patch` wrap `QWebEnginePage.runJavaScript`, `QClipboard.setText` and `createWindow`. Reapplying would wrap our own wrapper, doubling every dispatch and leaving the previous wrapper's closure chain alive, so each patch now marks the target module and skips if it has already run.
- **Distribution change — removed from AnkiWeb** (issue #2):
  - The AnkiWeb listing (`542586361`) has been taken down. This add-on is **no longer published to, or updated on, AnkiWeb**, and the release workflow no longer uploads to it. The `ANKIWEB_USERNAME` / `ANKIWEB_PASSWORD` Actions secrets are no longer read by the workflow.
  - GitHub Releases is now the only distribution channel: CI still byte-compiles, builds and attaches the `.ankiaddon` to the GitHub release.
  - **Users must install and upgrade manually** — download the `.ankiaddon` from the Releases page, then **Tools → Add-ons → Install from file…**. Anki does not auto-update manually installed add-ons.
  - Documentation: added an **Installation** section to `README.md`; rewrote the release/distribution sections of `AGENTS.md` (the old listing constants are kept only as a historical record, with a warning not to reintroduce them into the workflow); updated the release flow and CI rehearsal steps in `docs/DEVELOPMENT.md`.
  - Docs: corrected the development-symlink path — the installed folder is `Anki_Terminator_Performance_Companion`, not `Anki_Terminator_Companion`.
- **Packaging (first GitHub-only release)**:
  - `addon/meta.json` is no longer included in the `.ankiaddon`. It is Anki's per-add-on meta store (`mw.addonManager.addonMeta()` reads and writes `<addon_dir>/meta.json`; it is *not* kept in `prefs21.db`), and Anki's installer never creates one — it is written lazily on first run. Shipping it meant every fresh install began with the build machine's `last_seen_version` already matching the current version, so the one-time support/welcome screen never appeared. Anki regenerates the file on first launch, and the welcome screen now appears correctly on both first install and each upgrade.
  - Repo hygiene only, no runtime effect: stopped tracking `__pycache__/*.pyc` and run-time/tool state, and set `core.fileMode false` locally for the portable mount.

### October 13, 2026 (v1.9.1)
- **Black Sidebar After Deep-Idle Unload (bug fix)**:
  - Deep idle navigated the sidebar page to `about:blank` to free renderer memory, which fires the sidebar's own `loadStarted`/`loadFinished` handlers. Two of them sabotaged the frozen screenshot: `on_initial_load` hides `snapshot_label` after 150ms (exposing the blank page), then re-schedules `freeze_sidebar` 5s later, which grabs the now-empty page and **permanently overwrites the screenshot with a black frame** — so the sidebar stayed black even after thawing.
  - `deep_freeze()` now flags its own navigation (`sidebar._companion_deep_unload`). `on_load_started` returns immediately, keeping the snapshot and progress bar as-is; `on_initial_load` consumes the flag and returns without hiding the snapshot or re-scheduling a freeze.
  - `restore_deep_frozen_page()` clears the flag before navigating, so a deep unload whose `loadFinished` never arrived cannot leave the flag set and suppress the next real page load.
  - Thawing is unchanged: the restored navigation runs the normal handlers, so the snapshot hides and the sidebar refreezes after 5s.
  - **Affects only users who left `deep_freeze_seconds` at its default (300s).** Set it to `0` in the config dialog to disable deep idle reclamation entirely.

### October 13, 2026 (v1.9.0)
- **Anki 26.x Compatibility (bug fix)**:
  - `gui_hooks.exiting` was removed in Anki 26.x. The companion registered `close_all_dock_widget` on it unconditionally, which raised `AttributeError` on every launch and aborted the rest of the patch block. It now registers on whichever shutdown hooks the running Anki actually exposes (`profile_will_close`, and `exiting` on older versions).
  - Anki 26.x `gui_hooks` are custom `_aqt.hooks.*` objects rather than plain lists, so the membership test used to defer `setup_chatGPTwidget` raised `TypeError`. **This silently disabled the startup deferral**, so the Terminator webview was built synchronously during `main_window_did_init` on every launch — the "prevent thread block at startup" optimization had been dead since the Anki 26 upgrade. The check now reads the hook's backing `_hooks` list, falling back to the hook object on older Anki.
- **Deep Idle Memory Free (new setting)**:
  - `LifecycleState.Frozen` only suspends a page so it can resume quickly; it does **not** release the renderer's heap. A long Gemini/ChatGPT conversation kept its DOM and JS heap alive, so the sidebar could sit on ~1 GiB of `QtWebEngineProcess` memory while appearing frozen.
  - After a configurable idle period the companion now navigates the sidebar to `about:blank`, letting Chromium free that memory, and restores the original URL on the next thaw. Short absences are unaffected — the existing instant screenshot freeze still fires first.
  - New **"Deep Idle Memory Free"** setting in the config dialog (default 300s, `0` disables). Note that thawing after a deep idle reloads the page, and unsent composer text is discarded.
- **CI**: added `.github/workflows/release.yml` — byte-compiles the package, builds the `.ankiaddon`, attaches it to the GitHub release, and uploads it to AnkiWeb (listing 542586361). See `AGENTS.md`.
- **Documentation**:
  - Added `AGENTS.md` — release/CI trigger table, the AnkiWeb listing constants (and why `addon-id` must stay set), credential setup, and the Anki 26.x `gui_hooks` API change.
  - `docs/CONFIGURATION.md` — documented `deep_freeze_seconds` and added a "Deep idle reclamation" section covering the two-tier freeze and its trade-offs.
  - `docs/ARCHITECTURE.md` — documented the deep-idle helpers and the two-tier freeze/thaw cycle.
  - `docs/DEVELOPMENT.md` — replaced the manual local-build release flow with the CI flow; added the CI dry-run rehearsal step.
  - Added `deep_freeze_seconds` to the shipped `config.json` defaults for discoverability. Behaviour is unchanged — the code already fell back to 300 when the key was absent.

### August 31, 2026 (v1.8.0)
- **Popup Window Navigation Controls**:
  - Added back, forward, reload, home buttons and address bar to all popup windows opened from the sidebar.
  - New `popup_nav_patch.py` monkey-patches `CustomWebEnginePage.createWindow` to inject a navigation toolbar.
  - Address bar supports direct URL entry and keyword search, matching sidebar search engine configuration.
  - URL bar auto-syncs with page navigation via `urlChanged` signal.
- **Non-Modal Config Dialog**:
  - Config dialog now uses `.show()` instead of `.exec()`, allowing Anki to be used freely while the settings window is open.
  - Dialog reference stored on `mw._companion_config_dialog` to prevent garbage collection.
  - Save button no longer auto-closes the dialog.
- **Lazy Log Loading & Refresh**:
  - Performance Logs tab now lazy-loads only the last 200 lines via `QTimer.singleShot(0, ...)` to prevent UI freeze on open.
  - Added `get_recent_logs(count)` method to `CompanionLogger` for efficient tail loading.
  - Added **Refresh** button for manual log reload at any time.
  - `QPlainTextEdit` capped at 2000 blocks with `setMaximumBlockCount` to prevent memory growth.
  - Auto-scroll only triggers when the scrollbar is already near the bottom, respecting manual scrolling.
  - Monospace font and `NoWrap` line mode for better log readability.
- **Documentation Overhaul**:
  - Created `docs/` folder with `ARCHITECTURE.md`, `CONFIGURATION.md`, and `DEVELOPMENT.md`.
  - Moved root `DEVELOPMENT.md` into `docs/` and expanded with full config key reference, log format details, and testing checklist.
  - Updated `README.md` with new features (#13, #14) and documentation table.

### July 13, 2026 (v1.7.8)
- **Startup Performance Optimization**:
  - Bypassed synchronous `easylist.txt` file reading and parsing during startup imports by mocking `builtins.open` during the target's `ad_blocker` module load.
  - Defer the loading and compilation of ad-blocker domains to be done lazily only when the first network request is intercepted.
  - Hooked and wrapped `setup_chatGPTwidget` to defer its execution on `main_window_did_init` by `1000ms`, avoiding blocking Anki's main thread loop at startup.
- **Safe Profile Shutdown Hook**:
  - Registered the target's `close_all_dock_widget` cleanup routine to Anki's `profile_will_close` and `exiting` hooks.
  - This ensures all active `WebEnginePage`, `ResizableWebView`, and `QDockWidget` instances are deleted and freed properly on profile close or app exit, resolving profile release warnings ("WebEnginePage still not deleted. Expect troubles!") and shutdown hangs.

### July 13, 2026 (v1.7.7)
- **Clipboard Privacy & Pollution Fix**:
  - Implemented CPython stack trace analysis (`sys._getframe`) to differentiate between the target addon copying prompt inputs and restoring original user clipboard states.
  - Set custom private `QMimeData` objects tagged with platform-specific clipboard manager bypass hints (`x-kde-passwordManagerHint` on Linux, `ExcludeClipboardContentFromMonitorProcessing` on Windows, and `org.nspasteboard.TransientType` on macOS) to prevent clipboard history/monitors from storing prompt texts.
  - Scheduled a fail-safe clipboard restore `1.5s` later as a backup to the target addon's own restore.
  - Added `"enable_clipboard_clearing"` setting with a toggle UI checkbox in the companion's settings tab.

### June 21, 2026 (v1.7.5)
- **Google UI LaTeX Copying & Comment Stripping**:
  - Implemented dynamic parsing of formula comments (e.g. `data-xpm-latex`) generated by Google UI renderers to correctly recover original LaTeX equations (e.g. `\(PO_{2}\)`) when right-click "Add to Card" is used.
  - Added a complete cleanup pass to sanitize and strip all HTML comment node artifacts (such as `<!--TgQPHd-->` and others) from copied selections.
  - Designed a safe element containment check so that formulas nested within text containers (like `<strong>` or `<p>`) only replace visual junk while preserving surrounding text.
  - Fixed an issue where `<anki-mathjax>` tags were copied as plain unformatted/truncated text due to `innerText` being empty on disconnected DOM elements. Added `textContent` and secondary attribute lookups as a fallback for reliable formula extraction.

### June 20, 2026 (v1.7.4)
- **Active AI Icon & Tab Bar Sync**:
  - Fixed a configuration loading error (`now_ai` NameError) during initial toolbar construction.
  - Implemented dynamic pointer-matching (`tabData(index)`) to automatically synchronize the sidebar tab icon when the dock widget is tabbed/tabified inside the main QMainWindow.
- **AI-Hints Cloze Skipping**:
  - Added a double-brace (`{{`) skip check inside the optimized `clean_ai_hints_from_text` loop to prevent cloze deletions from being stripped and cleared.

### June 19, 2026 (v1.7.3)
- **Dynamic Deck Selection for Add to New Card Action**:
  - Automatically sets the target deck in the "Add Cards" dialog to match the currently reviewed card's deck.
  - Safely handles filtered/cram decks by extracting and targeting the card's original home deck (`card.odid`) instead of the temporary filtered deck.

### June 14, 2026 (v1.7.2)
- **Robust Unicode Word Boundary Checks for Cloze Censoring**:
  - Replaced regular expression `\w` word boundaries with a custom Unicode character classification algorithm (`unicodedata`).
  - Correctly recognizes and preserves combining characters, marks, and script-specific conjuncts (such as Malayalam viramas/consonant conjuncts).
  - Prevents active cloze answers (e.g., `പുലി`) from being incorrectly censored when they occur as substrings of larger words (e.g., `കരിമ്പുലി`).

### June 13, 2026 (v1.7.1)
- **Rich Text & Table Selection Preservation**:
  - Added full support for rich text elements when right-clicking and copying selections to Anki fields.
  - Preserves standard HTML tables (`<table>`, `<tbody>`, `<tr>`, `<td>`, etc.) including cell-spanning layout attributes (`colspan`, `rowspan`) and borders.
  - Preserves blockquotes (`<blockquote>`), horizontal rules (`<hr>`), strikethroughs (`<s>`, `<del>`, `<strike>`), and custom `<anki-mathjax>` tags.

### June 10, 2026 (v1.7.0)
- **AI Dropdown Selector in Header**:
  - Replaced the static "AI" button with a dynamic `QToolButton` dropdown.
  - Displays a menu containing all available AIs with their logos and full names for fast switching.
  - Selecting the active AI performs a hard reload/cache-bypass and clears browser history.
- **Explain Cloze Context Menu Action**:
  - Added a new right-click context menu option **"Explain cloze with AnkiTerminator"**.
  - Automatically censors cloze deletion blocks (e.g., `{{c1::answer}}`) in selected text to `[...]` before sending it to the AI, ensuring the model is not influenced by the cloze answer.
- **Sidebar Favicon Syncing**:
  - Automatically updates the sidebar's dock widget title bar and tab icon to match the favicon/logo of the active AI dynamically on startup and when switching AIs.

### June 10, 2026 (v1.6.1)
- **UI Stability & Transition Fixes**:
  - Refined **Persistent View** to eliminate white/blank screens during navigation using action-based pre-capturing and buffered hiding.
  - Moved the **Sleek Progress Bar** to the absolute top of the sidebar for a more native browser feel.
  - Implemented aggressive, multi-stage suppression of original addon loading screens, specifically targeting branding elements to ensure a clean UI.
- **Enhanced Configuration**:
  - Added new settings toggles to enable/disable **Sleek Progress Bar** and **Persistent View** independently.
- **Visual Refinement**: Improved Z-order layering to ensure progress indicators and snapshots stay correctly stacked during layout shifts.

### June 9, 2026 (v1.6.0)
- **Configuration & Installation Fix**: Fixed a bug where 'Wiki' and 'Donate' buttons were not hidden when unchecked, caused by a hardcoded package name constraint. Configuration paths are now dynamically resolved (`__name__.split(".")[0]`), ensuring preferences are correctly applied regardless of the installation directory name.
- **Full Browser Integration**:
  - Added a minimal **Address Bar** next to the prompt buttons for direct URL entry and searching.
  - Added **Back, Forward, and Reload** navigation buttons.
  - Integrated **Configurable Search Engines**: Choose between Google, DuckDuckGo, Bing, or a Custom search URL via Companion settings.
  - Replaced the intrusive full-screen loading overlay with a sleek, browser-style **Progress Bar** at the top.
  - Sidebar now stays on the current page while a new one is loading, providing a smoother experience.
- **UI Refinement**:
  - Removed the "+" header button (functionality remains available in the right-click context menu).
  - Minimalist layout preserves vertical space while adding powerful navigation tools.

### June 9, 2026 (v1.5.0)
- **Add to New Card (Context Menu)**:
  - Added a new context menu option "Add to new card" to the sidebar.
  - Automatically extracts selection (text, math, and images) and opens a pre-filled "Add Cards" window.
  - Preserves LaTeX delimiters and rich HTML formatting during the transfer.

### June 7, 2026 (v1.4.1)
- **Fixed Button Race Condition**:
  - Added a 200ms lifecycle-aware delay when clicking AI prompt buttons while the sidebar is frozen.
  - This ensures Chromium has transitioned from `Frozen` to `Active` state before executing the prompt injection, resolving the issue where buttons occasionally had to be pressed twice.

### June 7, 2026 (v1.4.0)
- **Instant Config Access (Header Button)**:
  - Injected a new **"C" button** in the sidebar header next to the existing settings cogwheel.
  - Provides immediate access to the companion settings dialog during study sessions.
- **Improved Text Detection & Stability**:
  - Refactored `patched_get_field_text` to correctly fall back to the original add-on logic, resolving "empty text window" issues.
  - Refined `is_responding` state management to only trigger on explicit prompt submissions, preventing interference with background JS calls.
- **HTML Cleanup Fallback**:
  - Enhanced the HTML stripper with a robust regex-based fallback to ensure text is always captured even if the primary parser encounters edge cases.
- **Removed Experimental Features**:
  - Reverted experimental image pasting and regex-based `runJavaScript` optimizations to prioritize core stability and text detection accuracy.

### June 7, 2026 (v1.3.3)
- **Idle CPU Optimization & Busy Loop Mitigation**:
  - Implemented visibility-aware checks for the background `findAndClickButton` interval (`setInterval`), suspending it when the sidebar is hidden/inactive.
  - Patched `ResizableWebView.handle_audio_state` and the sidebar freeze routine to stop active audio recording timers (`stop_timer`) when the sidebar is not visible or currently frozen.
  - Optimized the AI-Hints `clean_ai_hints_from_text` routine with a fast `O(n)` substring pre-check, preventing expensive regular expression scans on every field lookup when no hints are present.
- **HTML Stripping for AI Prompts**:
  - Automatically strips raw HTML tags (such as `<br>`, `<hr>`, `<div>`, `<span>`) from card field texts before sending them to the AI, ensuring only clean text and LaTeX/MathJax expressions are transmitted.
- **Automatic Image Clipboard Pasting**:
  - Automatically detects and extracts any referenced card images (`<img>` tags) in the field. Loads and places the image on the system clipboard, focuses the AI input area, and triggers a native WebEngine paste event to upload the image to the chatbot.
  - Automatically backs up and restores the user's original system clipboard immediately after pasting, preserving the clipboard state.
- **Multiple Fields Support**:
  - Added support for concatenating and sending all non-empty card fields to the AI, rather than only the priority field.
  - Fully configurable via the "Fields" tab in both the main Anki Terminator settings dialog and the Terminator Companion config UI (disabled by default).
  - Automatically filters out fields that contain only HTML boilerplate or whitespace to ensure clean transmission.

### June 6, 2026 (v1.3.2)
- **AI-Hints Preservation**:
  - Patched note saving to detect and keep AI-Hints JSON blocks at the absolute end of the field when appending selection text via the right-click menu.

### June 6, 2026 (v1.3.1)
- **AI Chatbot MathJax & HTML Sanitization**:
  - Added support for extracting and reconstructing LaTeX formulas from chatbot-rendered containers (supporting MathJax v2, MathJax v3, KaTeX, and Wikipedia formats) to standard Anki delimiters (`\( ... \)` and `\[ ... \]`).
  - Resolved partial selection bugs by implementing a range-expansion logic that automatically captures the complete formula.
  - Implemented strict HTML tag whitelist and attribute sanitization to strip all Angular scoping attributes, tracking data, and citation/footnote chips, ensuring only clean formatting is sent to Anki.
  - Added context-menu action logs to the performance log viewer.

### June 5, 2026 (v1.3.0)
- **Clipboard-Free Text Injection**: Patched the input insertion mechanism to inject queries directly via Chromium's native `document.execCommand('insertText')` API, completely avoiding system clipboard pollution and resolving clipboard paste race conditions.
- **Support & Customization Settings**: Added Ko-fi support badges and detailed configuration settings descriptions.

### June 5, 2026 (v1.2.0)
- **Rename & Branding**: Renamed add-on from "Anki Terminator Performance Companion" to "Anki Terminator Companion".
- **Rich HTML Context Menu Paste**: Intercepted context menu triggers to extract selection text as raw HTML using a specialized JavaScript range cloner, allowing formatted text insertion into Anki fields.

### June 2, 2026 (v1.1.0)
- **Config UI Improvements**: Refactored settings dialog into a modular tabbed layout and added a new QR Support tab.
- **Supporter Welcome Hook**: Implemented a supporter status check hook on startup.

### June 2, 2026 (v1.0.2)
- **WebView Performance**: Optimized `runJavaScript` targeting, fixed loading layout screen representation, and resolved mouse hover transition flickers.

### June 1, 2026 (v1.0.0)
- **Initial Release**: Released version 1.0.0 featuring core optimizations: smart CPU freezing (0% idle CPU), O(1) suffix ad-blocker lookup, and CSS animation/transition disabler.
