import importlib
import urllib.parse
from aqt import mw
from aqt.qt import *
from ..logger import companion_logger


def patch(dock_web_view_mod):
    target_addon_id = dock_web_view_mod.__name__.split('.')[0]
    companion_logger.log("[Popup Nav Patch] Initiating popup navigation controls patch...")

    original_createWindow = dock_web_view_mod.CustomWebEnginePage.createWindow

    def new_createWindow(self, _type):
        new_page = original_createWindow(self, _type)

        try:
            dialog = getattr(mw, 'AnkiTerminator_new_dialog', None)
            if dialog is None:
                return new_page

            layout = dialog.layout()
            if layout is None:
                return new_page

            nav_widget = QWidget()
            nav_widget.setMaximumHeight(30)
            nav_layout = QHBoxLayout(nav_widget)
            nav_layout.setContentsMargins(4, 2, 4, 2)
            nav_layout.setSpacing(3)

            btn_back = QPushButton(" < ")
            btn_forward = QPushButton(" > ")
            btn_reload = QPushButton(" R ")
            btn_home = QPushButton(" H ")

            address_bar = QLineEdit()
            address_bar.setPlaceholderText("URL or Search...")
            address_bar.setMinimumWidth(150)
            address_bar.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            address_bar.setStyleSheet(
                "QLineEdit { border: 1px solid #555; border-radius: 4px; "
                "padding: 2px 6px; background: #2a2a2a; color: #eee; "
                "height: 20px; font-size: 13px; }"
            )

            nav_style = (
                "QPushButton { margin: 1px; padding: 1px; font-weight: bold; "
                "color: #2196F3; }"
            )
            for btn in [btn_back, btn_forward, btn_reload, btn_home]:
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(nav_style)
                btn.setToolTip("Browser Navigation")

            nav_layout.addWidget(btn_back)
            nav_layout.addWidget(btn_forward)
            nav_layout.addWidget(btn_reload)
            nav_layout.addWidget(btn_home)
            nav_layout.addWidget(address_bar)

            layout.insertWidget(0, nav_widget)

            web_view = None
            for child in dialog.findChildren(dock_web_view_mod.CustomWebEngineView):
                web_view = child
                break

            if web_view is None:
                return new_page

            def navigate_address(text):
                if not text.strip():
                    return
                if "." in text and " " not in text:
                    url_str = text if text.startswith(("http://", "https://")) else "https://" + text
                else:
                    cfg = mw.addonManager.getConfig(__name__.split(".")[0]) or {}
                    custom_url = cfg.get("custom_search_url", "https://www.google.com/search?q=")
                    url_str = custom_url + urllib.parse.quote(text)
                web_view.load(QUrl(url_str))

            btn_back.clicked.connect(web_view.back)
            btn_forward.clicked.connect(web_view.forward)
            btn_reload.clicked.connect(web_view.reload)
            btn_home.clicked.connect(lambda: web_view.reload())

            def on_return_pressed():
                if address_bar.hasFocus():
                    navigate_address(address_bar.text())

            address_bar.returnPressed.connect(on_return_pressed)

            web_view.urlChanged.connect(lambda u: address_bar.setText(u.toString()))

            companion_logger.log("[Popup Nav Patch] Injected navigation controls into popup window.")
        except Exception as e:
            companion_logger.log(f"[Popup Nav Patch] Failed to inject nav controls: {e}")

        return new_page

    dock_web_view_mod.CustomWebEnginePage.createWindow = new_createWindow
    companion_logger.log("[Popup Nav Patch] Successfully patched CustomWebEnginePage.createWindow.")
