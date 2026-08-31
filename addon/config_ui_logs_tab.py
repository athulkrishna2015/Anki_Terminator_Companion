# addon/config_ui_logs_tab.py
from aqt.qt import *
from .logger import companion_logger

TAIL_LINES = 200

class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        companion_logger.register_callback(self.on_log_added)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.log_text = QPlainTextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_text.setMaximumBlockCount(2000)
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.log_text.setFont(font)

        btn_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh", self)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_logs)

        self.copy_btn = QPushButton("Copy Logs", self)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_logs)

        self.clear_btn = QPushButton("Clear Logs", self)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_logs)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)

        layout.addWidget(self.log_text)
        layout.addLayout(btn_layout)

        QTimer.singleShot(0, self._lazy_load)

    def _lazy_load(self):
        recent = companion_logger.get_recent_logs(TAIL_LINES)
        self.log_text.setPlainText(recent)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def refresh_logs(self):
        self.log_text.clear()
        recent = companion_logger.get_recent_logs(TAIL_LINES)
        self.log_text.setPlainText(recent)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def on_log_added(self, line):
        if not line:
            self.log_text.setPlainText("")
        else:
            self.log_text.appendPlainText(line)
            sb = self.log_text.verticalScrollBar()
            if sb.value() >= sb.maximum() - 40:
                self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def copy_logs(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
        QToolTip.showText(self.copy_btn.mapToGlobal(QPoint(0, 0)), "Logs copied to clipboard!")

    def clear_logs(self):
        companion_logger.clear()

    def disconnect_logger(self):
        companion_logger.unregister_callback(self.on_log_added)
