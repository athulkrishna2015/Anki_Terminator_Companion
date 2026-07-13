# addon/patch_1468920185_anki_terminator/__init__.py
import importlib
from ..logger import companion_logger

def apply_ai_hints_patch():
    try:
        import sys
        import re
        patched_ai_hints = False
        for name, module in list(sys.modules.items()):
            if name.endswith("anki_terminator_patch"):
                if hasattr(module, "clean_ai_hints_from_text") and not hasattr(module, "_companion_optimized"):
                    original_clean = module.clean_ai_hints_from_text
                    
                    CLEAN_PAT = re.compile(
                        r'(?:[\s\n\r]|<br\s*/?>|&nbsp;|<div>\s*</div>)*<div\b[^>]*class=["\'][^"\']*(?:ai-hints-json|ai-hints-container)[^"\']*["\'][^>]*>.*?</div>(?:[\s\n\r]|<br\s*/?>|&nbsp;|<div>\s*</div>)*',
                        flags=re.DOTALL | re.IGNORECASE,
                    )
                    
                    def optimized_clean_ai_hints_from_text(text: str) -> str:
                        from aqt import mw
                        cfg = mw.addonManager.getConfig(__name__.split(".")[0]) or {}
                        if not cfg.get("enable_ai_hints_optimization", True):
                            return original_clean(text)

                        if not isinstance(text, str):
                            return text
                        if "hints" not in text and "options" not in text:
                            return text
                        
                        cleaned = CLEAN_PAT.sub("", text)
                        
                        # Strip plain/tag-stripped JSON payloads that get saved in sfld (Sort Field)
                        idx = 0
                        while True:
                            start_idx = cleaned.find("{", idx)
                            if start_idx == -1:
                                break
                            
                            # Skip cloze deletions (which start with "{{")
                            if cleaned[start_idx:start_idx+2] == "{{":
                                idx = start_idx + 2
                                continue
                                
                            chunk = cleaned[start_idx:start_idx+150]
                            if any(f'"c{i}"' in chunk for i in range(1, 10)) and ('"hints"' in chunk or '"options"' in chunk):
                                brace_count = 0
                                end_idx = -1
                                for i in range(start_idx, len(cleaned)):
                                    if cleaned[i] == '{':
                                        brace_count += 1
                                    elif cleaned[i] == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            end_idx = i
                                            break
                                if end_idx != -1:
                                    cleaned = cleaned[:start_idx] + cleaned[end_idx+1:]
                                    idx = start_idx
                                    continue
                            idx = start_idx + 1
                        return cleaned.strip()

                    module.clean_ai_hints_from_text = optimized_clean_ai_hints_from_text
                    module._companion_optimized = True
                    companion_logger.log("[AI-Hints Patch] Successfully patched clean_ai_hints_from_text with O(n) fast path!")
                    patched_ai_hints = True
                    break
        if not patched_ai_hints:
            companion_logger.log("[AI-Hints Patch] Module 'anki_terminator_patch' not found in sys.modules yet.")
    except Exception as e:
        companion_logger.log(f"[AI-Hints Patch] Patch failed: {e}")

def apply_patches():
    # Find all active target IDs
    active_targets = []
    for addon_id in ["1468920185", "1448033349"]:
        try:
            # Check if we can import the dock_web_view of this addon
            importlib.import_module(f"{addon_id}.dock_web_view")
            active_targets.append(addon_id)
        except ImportError:
            continue
            
    if not active_targets:
        companion_logger.log("[Terminator Companion] No active Anki Terminator addons found to patch.")
        return

    for target_id in active_targets:
        companion_logger.log(f"[Terminator Companion] Found target addon {target_id}. Applying patches...")
        
        # 1. Apply AdBlocker patches
        try:
            # Temporarily mock builtins.open to prevent parsing easylist.txt during import
            import builtins
            original_open = builtins.open
            
            def custom_open(file, *args, **kwargs):
                if isinstance(file, str) and "easylist.txt" in file:
                    import io
                    return io.StringIO("")
                return original_open(file, *args, **kwargs)
                
            builtins.open = custom_open
            try:
                ad_blocker_mod = importlib.import_module(f"{target_id}.ad_blocker")
            finally:
                builtins.open = original_open
                
            from . import ad_blocker_patch
            ad_blocker_patch.patch(ad_blocker_mod)
        except Exception as e:
            companion_logger.log(f"[Terminator Companion] [{target_id}] AdBlocker patch failed: {e}")

        # 2. Apply WebEngine, Lifecycle, and Context Menu patches
        try:
            dock_web_view_mod = importlib.import_module(f"{target_id}.dock_web_view")
            add_fields_mod = importlib.import_module(f"{target_id}.context_menu.add_fields")
            from . import css_patch
            from . import lifecycle_patch
            from . import context_menu_patch
            css_patch.patch(dock_web_view_mod)
            lifecycle_patch.patch(dock_web_view_mod)
            context_menu_patch.patch(add_fields_mod, dock_web_view_mod)
            
            # Register close_all_dock_widget to shutdown/profile close hooks to delete WebEnginePage properly
            if hasattr(dock_web_view_mod, "close_all_dock_widget"):
                from aqt import gui_hooks
                gui_hooks.profile_will_close.append(dock_web_view_mod.close_all_dock_widget)
                gui_hooks.exiting.append(dock_web_view_mod.close_all_dock_widget)
                companion_logger.log(f"[Terminator Companion] [{target_id}] Registered close_all_dock_widget to profile_will_close/exiting hooks.")
        except Exception as e:
            companion_logger.log(f"[Terminator Companion] [{target_id}] Webview/Lifecycle/Context Menu patch failed: {e}")

        # 3. Defer startup WebEngineView initialization to prevent thread block at startup
        try:
            add_menu_mod = importlib.import_module(f"{target_id}.add_menu")
            if hasattr(add_menu_mod, "setup_chatGPTwidget"):
                from aqt import gui_hooks
                original_setup = add_menu_mod.setup_chatGPTwidget
                
                def deferred_setup_chatGPTwidget():
                    companion_logger.log(f"[Terminator Companion] [{target_id}] Executing deferred setup_chatGPTwidget...")
                    from aqt.qt import QTimer
                    QTimer.singleShot(1000, original_setup)
                
                if original_setup in gui_hooks.main_window_did_init:
                    gui_hooks.main_window_did_init.remove(original_setup)
                    gui_hooks.main_window_did_init.append(deferred_setup_chatGPTwidget)
                    companion_logger.log(f"[Terminator Companion] [{target_id}] Successfully deferred setup_chatGPTwidget on main_window_did_init.")
        except Exception as e:
            companion_logger.log(f"[Terminator Companion] [{target_id}] Deferring startup initialization failed: {e}")

    # 4. Apply AI-Hints optimization patch
    apply_ai_hints_patch()
    try:
        from aqt.qt import QTimer
        QTimer.singleShot(2000, apply_ai_hints_patch)
    except Exception:
        pass

# Apply immediately on module import
apply_patches()

