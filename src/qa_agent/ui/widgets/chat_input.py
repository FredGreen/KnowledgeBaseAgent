"""Chat input widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pySignal, pyqtSignal
from PyQt6.QtGui import QKeyEvent

from ...utils.text_utils import estimate_tokens


class ChatInput(QWidget):
    """Bottom input area for chat page."""
    send_requested = pyqtSignal(str)
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        self._input = QTextEdit()
        self._input.setObjectName("chat-input")
        self._input.setPlaceholderText("输入消息... (Enter 发送, Shift+Enter 换行)")
        self._input.setMaximumHeight(120)
        self._input.setMinimumHeight(50)
        self._input.installEventFilter(self)
        layout.addWidget(self._input)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._token_label = QLabel("约 0 tokens")
        self._token_label.setStyleSheet("color: #6B7280; font-size: 12px;")

        self._send_btn = QPushButton("发送 ➤")
        self._send_btn.setObjectName("primary-btn")
        self._send_btn.setFixedWidth(100)
        self._send_btn.clicked.connect(self._on_send)

        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setObjectName("secondary-btn")
        self._stop_btn.setFixedWidth(100)
        self._stop_btn.setVisible(False)
        self._stop_btn.clicked.connect(self.stop_requested.emit)

        bottom.addWidget(self._token_label)
        bottom.addStretch()
        bottom.addWidget(self._stop_btn)
        bottom.addWidget(self._send_btn)
        layout.addLayout(bottom)

        self._input.textChanged.connect(self._on_text_changed)

    def eventFilter(self, obj, event: QKeyEvent):
        if obj == self._input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        text = self._input.toPlainText().strip()
        if text:
            self.send_requested.emit(text)
            self._input.clear()

    def _on_text_changed(self):
        text = self._input.toPlainText()
        tokens = estimate_tokens(text)
        self._token_label.setText(f"约 {tokens} tokens")

    def set_generating(self, generating: bool):
        self._send_btn.setVisible(not generating)
        self._stop_btn.setVisible(generating)
        self._input.setEnabled(not generating)

    def get_text(self) -> str:
        return self._input.toPlainText().strip()

    def clear(self):
        self._input.clear()
