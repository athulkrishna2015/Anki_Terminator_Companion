# Development Guide

Local setup, testing, versioning, and building release packages.

---

## Project Structure

```
Anki_Terminator_Companion/ (Repo Root)
├── README.md                 # User-facing overview + manual installation steps
├── CHANGELOG.md              # Version history
├── AGENTS.md                 # Release/CI + distribution (GitHub-only) reference
├── bump.py                   # SemVer version bump utility
├── make_ankiaddon.py         # Packaging script → .ankiaddon
├── .github/workflows/
│   └── release.yml           # CI: check → build → attach .ankiaddon to GitHub release
├── docs/
│   ├── ARCHITECTURE.md       # Internal architecture & patch details
│   ├── CONFIGURATION.md      # Config keys, defaults, JSON reference
│   └── DEVELOPMENT.md        # This file
└── addon/
    ├── __init__.py            # Entry point: monkey-patching orchestrator
    ├── manifest.json          # Addon metadata (name, version, min/max Anki)
    ├── config.json            # Default configuration values
    ├── meta.json              # Runtime state (last_seen_version, supporter_opt_out)
    ├── VERSION                # Current SemVer string (single line)
    ├── logger.py              # Thread-safe async file logger with GUI callbacks
    ├── companion.log          # Real-time event log (truncated on startup)
    ├── config_ui.py           # Config dialog orchestrator (non-modal QDialog)
    ├── config_ui_general_tab.py  # General settings tab
    ├── config_ui_logs_tab.py  # Live performance logs tab (lazy-loaded)
    ├── tab_support.py         # Support/Donate tab (QR codes, Ko-fi)
    ├── Support/               # QR code images (UPI.jpg, BTC.jpg, ETH.jpg)
    └── patch_1468920185_anki_terminator/
        ├── __init__.py        # Patch orchestrator (discovers target, applies all patches)
        ├── ad_blocker_patch.py    # O(1) domain suffix set matching
        ├── css_patch.py           # Gemini CSS animation disabler
        ├── lifecycle_patch.py     # Freeze/thaw, nav, AI dropdown, response monitor (~1080 lines)
        ├── context_menu_patch.py  # Rich paste, cloze censor, add-to-card
        └── popup_nav_patch.py     # Popup window navigation controls
```

---

## Local Setup & Testing

### Prerequisites

1. Anki installed with the original **Anki Terminator V2** addon (`1468920185`)
2. Python 3.10+ (for build scripts)

### Symlink for Development

```shell
# Linux
ln -s "$(pwd)/addon" ~/.local/share/Anki2/addons21/Anki_Terminator_Performance_Companion

# macOS
ln -s "$(pwd)/addon" ~/Library/Application\ Support/Anki2/addons21/Anki_Terminator_Companion

# Windows (PowerShell as Admin)
New-Item -ItemType Junction -Path "$env:APPDATA\Anki2\addons21\Anki_Terminator_Performance_Companion" -Target "$(Get-Location)\addon"
```

### Verification

1. Restart Anki
2. Check terminal output or `addon/companion.log` for:
   ```
   [Terminator Companion] Found target addon 1468920185. Applying patches...
   [AdBlocker Patch] Successfully hooked AdBlocker interceptRequest...
   [Lifecycle Patch] Initiating Flicker-Free QStackedWidget...
   ```
3. Open **Tools > Add-ons > Anki Terminator Companion > Config** to verify UI
4. Confirm sidebar has nav buttons (<, >, R, H), address bar, and "C" config button

### Testing Checklist

- [ ] Sidebar loads without errors
- [ ] Nav buttons (<, >, R, H) work in sidebar
- [ ] Address bar navigates to URLs and performs search
- [ ] AI dropdown switches between providers
- [ ] Sidebar freezes after 5s idle (check CPU drops to 0%)
- [ ] Hovering unfreezes sidebar (screenshot disappears)
- [ ] After ~5 min frozen, `companion.log` shows `Deep idle: cleared page (...)` and renderer memory drops
- [ ] Hovering after a deep freeze restores the page and logs `Restored page after deep freeze`
- [ ] Popup windows show navigation controls
- [ ] Config dialog opens non-modal (Anki usable while open)
- [ ] Logs tab loads quickly and updates live
- [ ] Refresh button reloads logs
- [ ] "Add to new card" appears in right-click menu
- [ ] "Explain cloze" censors cloze deletions correctly
- [ ] Clipboard is not polluted after sending prompts

---

## Building & Versioning

### Bump Version

```shell
# Auto-bump patch (1.9.0 → 1.9.1)
python bump.py

# Bump minor (1.9.0 → 1.10.0)
python bump.py minor

# Bump major (1.9.0 → 2.0.0)
python bump.py major

# Set explicit version
python bump.py 1.9.1
```

Updates both `addon/manifest.json` and `addon/VERSION`.

> **Note:** a minor bump drops the patch component and writes `1.10`, not `1.10.0`. If you
> want the full three-part form (which is what release tags use), run
> `python make_ankiaddon.py 1.10.0` once — it re-syncs both files via `sync_version()`.

### Build .ankiaddon

```shell
# Auto-bumps patch version
python make_ankiaddon.py

# Explicit version
python make_ankiaddon.py 1.9.0
```

Outputs a timestamped `.ankiaddon` file:
```
Anki_Terminator_Companion_v1.9.0_202608312014.ankiaddon
```

The build:
- Reads `.gitignore` to exclude build scripts, docs, pyc files
- Skips `bump.py`, `make_ankiaddon.py`, `DEVELOPMENT.md`
- Skips proxy binaries (`antigravity-proxy-*`)
- Packages only the `addon/` directory contents

### Release Flow

The add-on is **not on AnkiWeb** — the listing was removed (issue #2). A GitHub release
is the only distribution channel, and it is the only place users can download from.

**Do not build or upload the `.ankiaddon` by hand.** CI does both. The trigger is
publishing a GitHub release — creating a *draft* deliberately runs nothing.

1. Make changes and test locally
2. `python bump.py minor` (or `patch`) — updates `addon/VERSION` + `addon/manifest.json`
3. Update `CHANGELOG.md`, and `README.md` if any user-facing setting changed
   (`README.md` carries the manual install steps users land on from a release)
4. `git add -A && git commit -m "Release vX.Y.Z: ..."`
5. `git push origin master && git tag vX.Y.Z && git push origin vX.Y.Z`
6. `gh release create vX.Y.Z --title "..." --notes "..."` — **not** `--draft`
7. `gh run watch` to watch the build + release attach

The workflow byte-compiles `addon/`, builds the package, and attaches it to the GitHub
release. See `AGENTS.md` for the full trigger table and the manual
`workflow_dispatch` / `dry_run` options.

A local `python make_ankiaddon.py` is still useful for inspecting the artifact, but
its output is gitignored and never published.

> **Users must update manually.** Anki does not auto-update a manually installed
> add-on, so a release note should say "re-download and install over your existing
> copy" whenever a version actually matters.

### CI Rehearsal

Before cutting a release you can validate the whole pipeline without touching GitHub
releases:

```shell
gh workflow run release.yml --ref master -f tag=v1.9.0 -f dry_run=true
gh run watch
```

This runs the syntax check and the build, and **skips** the release attach.

---

## Code Conventions

- **No comments** in source unless explicitly requested
- All patches follow the monkey-patch pattern: save original → define replacement → assign back
- Config is always read via `mw.addonManager.getConfig(__name__.split(".")[0])` for dynamic package resolution
- Logging uses `companion_logger.log(...)` with component prefix tags like `[Lifecycle Patch]`
- GUI timers use `QTimer.singleShot(ms, callback)` for deferred operations
- All Qt imports go through `from aqt.qt import *` for PyQt5/6 compatibility
- **Check `companion.log` after every change.** The addon swallows exceptions broadly and reports
  them only there, so a patch can die silently while startup still appears to succeed.
- **Guard `gui_hooks` usage.** On Anki 26.x hooks are `_aqt.hooks.*` objects, not lists — `in`,
  `len()` and iteration all raise `TypeError`. See the compatibility table in `ARCHITECTURE.md`.
- **Clean up deep-freeze state** via `cancel_deep_freeze()` / `restore_deep_frozen_page()` rather
  than touching the sidebar's `_deep_freeze_timer` / `_deep_frozen_url` directly.
