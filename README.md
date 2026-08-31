# Anki Terminator Companion

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D01W6NQT)

An elegant, dynamic performance-optimization add-on for Anki. 

This companion addon is designed to run seamlessly alongside the original **Anki Terminator V2 - ChatGPT DeepSeek Sidebar for Reviewer** (`1468920185`). By dynamically patching memory during Anki startup, it eliminates high-CPU bottlenecks completely **without modifying a single line of code in the original addon's directory**.
<img width="918" height="113" alt="Screenshot_20260614_133846" src="https://github.com/user-attachments/assets/e7b9fa55-1d3b-461a-8646-f1529605be45" />

---

## Key Features & Optimization Highlights

### ⚡ 1. Smart UI-Freezing with Active Hover Tracking (0% Idle CPU)
* **The Problem**: Chromium (`QtWebEngineProcess`) refuses to freeze a webpage if it's visible on the viewport, meaning Gemini/ChatGPT continue to consume high CPU even when you aren't looking at them.
* **The Solution**: 
  - When the sidebar loses focus or you are studying cards, the companion captures a pixel-perfect static screenshot of the webview (`webview.grab()`) and displays it instantly in a `QLabel` via a `QStackedWidget` layout swap.
  - While hidden behind the static view, Chromium completely suspends all paints and JavaScript loops, instantly dropping CPU usage to **0%**.
  - **Flicker-Free Transitions**: By utilizing a `QStackedWidget`, page swaps are completely imperceptible and flicker-free.
  - **Active Hover & Stream Protection**: The sidebar stays 100% active and responsive under your cursor. In addition, when Gemini is actively generating a response, freezing is automatically deferred until the response finishes streaming, allowing you to watch the answer populate in real-time.

### 🚫 2. Optimized O(1) Suffix Ad-Blocker Lookup
* **The Problem**: If the C-based Rust ad-blocker engine is unavailable, the original addon falls back to scanning a list of **~46,000 domains** using slow, linear substring matching (`domain in url`) for *every single network request*. This blocks the main Qt UI thread.
* **The Solution**: The companion parses and splits those rules into pure domain lookups, executing a set-based suffix-matching algorithm in `O(1)` time. This eliminates frame drops during page loads.

### 🎨 3. CSS Animation & Transitions Disabler
* **The Problem**: High-CPU draw on Gemini's website due to continuous background shimmer animations, blur filters, and glow gradients.
* **The Solution**: Dynamically injects highly optimized CSS when the page loads to disable background animations, transition effects, and intensive CSS blur/backdrop-filters globally.

### 📝 4. Rich HTML Context Menu Paste Support (Preserves Formatting)
* **The Problem**: Right-clicking in the sidebar to "Add selection to field" originally uses plain-text copy-pasting, stripping out all markdown, links, lists, bold text, italics, and image elements.
* **The Solution**: Dynamically intercepts the context menu triggers to extract selection text as raw HTML using a specialized JavaScript range cloner. This allows you to append formatted answers directly into your Anki fields with all formatting and styling intact.

### 📋 5. Clipboard-Free Text Injection (No Clipboard Pollution)
* **The Problem**: Original prompt inputs relied on system clipboard copy-paste actions with timers. Lag spikes often caused the webview to paste the user's restored original clipboard data instead of the prompt text, polluting their clipboard history.
* **The Solution**: Patches the input insertion mechanism to inject queries directly via Chromium's native `document.execCommand('insertText')` API. It leaves your system clipboard completely untouched and guarantees instant, race-condition-free pasting across all AI platforms.

### 🧹 6. HTML Stripping for AI Prompts (LaTeX Clean)
* **The Problem**: Card fields sent to the AI often contain extensive HTML layout tag boilerplate (`<br>`, `<div>`, `<span style="...">`), which wastes token limits and confuses LLMs.
* **The Solution**: Automatically parses and strips all raw HTML tags from prompts, preserving clean text and raw LaTeX/MathJax expressions (`\(...\)` and `\[...\]`) for optimal AI processing.

### ⚡ 7. Instant Config Access (Header Button)
* **The Problem**: To change companion settings, users had to navigate through the Add-on Manager, which is slow during active study sessions.
* **The Solution**: Injects a custom **"C" button** directly into the sidebar header toolbar (next to the settings cogwheel). Clicking it instantly opens the Terminator Companion settings dialog.

### ➕ 8. Add to New Card (Context Menu)
* **The Problem**: Saving AI-generated content into new cards required manual copying, switching to the Add Cards window, and pasting.
* **The Solution**: Adds a new **"Add to new card"** option in the sidebar's right-click context menu. It extracts the selected text or images (preserving formatting and math) and pre-populates them into the first field of a new card window instantly.

### 🗃️ 9. Multiple Fields Support
* **The Problem**: Original sidebar only reads the single designated priority field.
* **The Solution**: Allows concatenating and sending all non-empty card fields to the AI, formatted clearly as `FieldName: FieldValue`. It automatically filters out empty fields and fields containing only boilerplate spaces or tags.

### 🌐 10. Integrated Browser Navigation & Search
* **The Problem**: The sidebar was locked to the AI chatbot URL, making it difficult to quickly look up external references or navigate between pages.
* **The Solution**:
  - **Minimal Address Bar**: Direct URL entry and keyword search support.
  - **Navigation Controls**: Back, Forward, and Reload buttons integrated into the header.
  - **Custom Search Engines**: Configurable search providers (Google, DuckDuckGo, Bing, or Custom).
  - **Sleek Progress Bar**: A browser-style progress indicator at the top of the sidebar replaces intrusive loading overlays.
  - **Persistent View**: The current page remains visible while the next one loads for a smoother browsing experience.

### 🪟 13. Popup Window Navigation Controls
* **The Problem**: Links opened in new popup windows had no navigation controls — no back, forward, reload, or address bar.
* **The Solution**: Injects the same navigation toolbar (back, forward, reload, home, address bar) into every popup window, matching the sidebar's style and search engine configuration.

### ⚙️ 14. Non-Modal Config Dialog & Lazy Logs
* **The Problem**: Opening the config dialog blocked all Anki interaction. The logs tab could freeze with large log files.
* **The Solution**:
  - Config dialog is now **non-modal** — use Anki freely while it's open.
  - Logs tab **lazy-loads** only the last 200 lines on open.
  - **Refresh** button for manual log reload.
  - Auto-scroll only when you're already at the bottom.
  - Monospace font and fixed-width for better readability.

### 🤖 11. Header AI Dropdown Selector (Fast Switching & Dynamic Favicon)
* **The Problem**: Switching between different AI providers (ChatGPT, DeepSeek, Claude, Gemini, etc.) was slow and required clicking the button repeatedly to rotate through them one by one.
* **The Solution**: 
  - Replaces the static `"AI"` header button with a dropdown selector.
  - Displays full AI names and logos in the dropdown menu for fast, direct selection.
  - Automatically updates the sidebar's window title bar and tab icon (favicon) to the active AI's logo.
  - **Cache-Bypass Hard Refresh**: Selecting the already active AI triggers a cache-bypassing hard reload and clears webview history to start a fresh chat session.

### 🧩 12. Censored "Explain Cloze" Context Menu Action
* **The Problem**: Selecting card text containing active Cloze deletions (e.g. `{{c1::answer}}`) and sending it to the AI often reveals the correct answer directly within the prompt, prompting the AI to simply repeat it rather than explaining the concept.
* **The Solution**: Introduces an **"Explain cloze with AnkiTerminator"** action to the right-click selection context menu. It automatically censors all cloze deletion segments, replacing them with `[...]` before passing the text to the AI so the LLM explains or solves the blank without being biased or influenced by the answer.

---

## Configuration & Settings

The companion add-on introduces a dedicated settings dialog inside Anki's Add-on Manager (accessible via **Tools > Add-ons > Select Anki Terminator Companion > Config**).

### Tabs Overview:
1. **General Settings**:
   * **Enable Smart CPU Freezing (Lifecycle State)**: Toggles the dynamic freezing/thawing system for Gemini/ChatGPT.
   * **Enable Ad-Blocker O(1) Suffix Match Optimization**: Toggles the fast suffix domain set lookup algorithm.
   * **Inject CSS Gemini Animation Disabler**: Toggles the custom animation disabler styles.
   * **Enable HTML Stripping for AI Prompts**: Toggles stripping of HTML tags from prompts (preserves math).
   * **Enable AI-Hints O(n) Regex Bypass Optimization**: Toggles fast-path rendering when no AI hints are present.
   * **Enable AI-Hints Context Menu Preservation**: Toggles safety check when appending right-click selections.
   * **Send Multiple Fields to AI**: Toggles sending all non-empty fields instead of just the priority field (configurable in both companion config and original Terminator "Fields" tab).
   * **Thaw Duration after Query**: Configures the duration in seconds that Gemini stays Active before freezing back after clicking any prompt buttons.
2. **Performance Logs**:
   * Lazy-loads the last 200 lines on open for fast startup.
   * Displays thread-safe, real-time diagnostic and performance events from the companion.
   * Includes **Refresh**, **Copy Logs**, and **Clear Logs** buttons.
   * Auto-scrolls only when you're already at the bottom.
3. **Support**:
   * Offers direct links and QR codes to support the creator (UPI, BTC, ETH, and Ko-fi links).
   * Includes a checkbox option: `"I have supported this addon (Hide automatic update welcome)"` to disable the welcome screen popping up after future updates.

---

## Documentation

| Document | Description |
|---|---|
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Internal architecture, patch system, code details |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | All config keys, defaults, JSON structures, log format |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, testing, versioning, building releases |

