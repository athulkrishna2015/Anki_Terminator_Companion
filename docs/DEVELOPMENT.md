# Development Guide

Local setup, testing, versioning, and building release packages.

---

## Project Structure

```
Anki_Terminator_Companion/ (Repo Root)
├── README.md                 # User-facing overview
├── CHANGELOG.md              # Version history
├── bump.py                   # SemVer version bump utility
├── make_ankiaddon.py         # Packaging script → .ankiaddon
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
ln -s "$(pwd)/addon" ~/.local/share/Anki2/addons21/Anki_Terminator_Companion

# macOS
ln -s "$(pwd)/addon" ~/Library/Application\ Support/Anki2/addons21/Anki_Terminator_Companion

# Windows (PowerShell as Admin)
New-Item -ItemType Junction -Path "$env:APPDATA\Anki2\addons21\Anki_Terminator_Companion" -Target "$(Get-Location)\addon"
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
# Auto-bump patch (1.8.0 → 1.8.1)
python bump.py

# Bump minor (1.8.0 → 1.9.0)
python bump.py minor

# Bump major (1.8.0 → 2.0)
python bump.py major

# Set explicit version
python bump.py 1.8.0
```

Updates both `addon/manifest.json` and `addon/VERSION`.

### Build .ankiaddon

```shell
# Auto-bumps patch version
python make_ankiaddon.py

# Explicit version
python make_ankiaddon.py 1.8.0
```

Outputs a timestamped `.ankiaddon` file:
```
Anki_Terminator_Companion_v1.8.0_202608312014.ankiaddon
```

The build:
- Reads `.gitignore` to exclude build scripts, docs, pyc files
- Skips `bump.py`, `make_ankiaddon.py`, `DEVELOPMENT.md`
- Skips proxy binaries (`antigravity-proxy-*`)
- Packages only the `addon/` directory contents

### Release Flow

1. Make changes and test locally
2. `python make_ankiaddon.py 1.8.0` — builds the .ankiaddon
3. `git add -A && git commit -m "Release vX.Y.Z: ..."`
4. `git push`
5. `gh release create vX.Y.Z --title "..." --notes "..." *.ankiaddon`

---

## Code Conventions

- **No comments** in source unless explicitly requested
- All patches follow the monkey-patch pattern: save original → define replacement → assign back
- Config is always read via `mw.addonManager.getConfig(__name__.split(".")[0])` for dynamic package resolution
- Logging uses `companion_logger.log(...)` with component prefix tags like `[Lifecycle Patch]`
- GUI timers use `QTimer.singleShot(ms, callback)` for deferred operations
- All Qt imports go through `from aqt.qt import *` for PyQt5/6 compatibility
