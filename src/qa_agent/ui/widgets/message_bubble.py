"""Message bubble widget for chat page."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor

from ...constants import Intent, INTENT_DISPLAY, INTENT_ICON, MessageStatus


class RouteBadge(QWidget):
    """Route intent badge shown at top of AI message bubble."""
    expanded = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)

        self._icon_label = QLabel()
        self._text_label = QLabel()
        self._confidence_label = QLabel()
        self._toggle_btn = QPushButton("▾")
        self._toggle_btn.setFixedSize(20, 20)
        self._toggle_btn.setObjectName("icon-btn")
        self._toggle_btn.clicked.connect(self._toggle)

        self._reason_label = QLabel()
        self._reason_label.setWordWrap(True)
        self._reason_label.setStyleSheet("color: #6B7280; font-size: 12px; margin-top: 2px;")
        self._reason_label.setVisible(False)

        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)
        layout.addWidget(self._confidence_label)
        layout.addWidget(self._toggle_btn)
        layout.addStretch()

        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

    def _toggle(self):
        visible = not self._reason_label.isVisible()
        self._reason_label.setVisible(visible)
        self._toggle_btn.setText("▴" if visible else "▾")
        self.expanded.emit(visible)

    def set_route(self, intent: str, confidence: float, reason: str):
        icon = INTENT_ICON.get(intent, "⚡")
        display = INTENT_DISPLAY.get(intent, intent)
        self._icon_label.setText(icon)
        self._text_label.setText(display)
        self._confidence_label.setText(f"· 置信度 {confidence:.2f}")
        self._reason_label.setText(reason)

    def get_widgets(self):
        return self, self._reason_label


class MessageBubble(QWidget):
    """A single message bubble in the chat."""
    copy_requested = pyqtSignal()
    regenerate_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, role: str = "user", parent=None):
        super().__init__(parent)
        self._role = role
        self._status = MessageStatus.DONE
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        if self._role == "user":
            main_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            self._bubble = QWidget()
            self._bubble.setObjectName("bubble-user")
            self._bubble.setMaximumWidth(600)
        else:
            main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self._route_badge = RouteBadge()
            self._route_badge.setVisible(False)
            main_layout.addWidget(self._route_badge)
            self._route_reason_container = QWidget()
            reason_layout = QVBoxLayout(self._route_reason_container)
            reason_layout.setContentsMargins(12, 0, 0, 0)
            reason_layout.setSpacing(0)
            main_layout.addWidget(self._route_reason_container)

            self._step_label = QLabel()
            self._step_label.setStyleSheet("color: #2E90FA; font-size: 12px;")
            self._step_label.setVisible(False)
            main_layout.addWidget(self._step_label)

            self._bubble = QWidget()
            self._bubble.setObjectName("bubble-ai")
            self._bubble.setMaximumWidth(650)

        bubble_layout = QVBoxLayout(self._bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setFrameShape(QFrame.Shape.NoFrame)
        self._content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._content.setMinimumHeight(30)
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        if self._role == "user":
            self._content.setStyleSheet("background: transparent; color: #1A1A2E;")
        else:
            self._content.setStyleSheet("background: transparent; color: #1A1A2E;")
        bubble_layout.addWidget(self._content)

        self._status_label = QLabel()
        self._status_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        self._status_label.setVisible(False)
        bubble_layout.addWidget(self._status_label)

        if self._role == "assistant":
            actions = QHBoxLayout()
            actions.setSpacing(8)

            self._copy_btn = QPushButton("📋 复制")
            self._copy_btn.setObjectName("icon-btn")
            self._copy_btn.clicked.connect(self.copy_requested.emit)

            self._regen_btn = QPushButton("🔄 重新生成")
            self._regen_btn.setObjectName("icon-btn")
            self._regen_btn.clicked.connect(self.regenerate_requested.emit)

            self._stop_btn = QPushButton("⏹ 停止")
            self._stop_btn.setObjectName("icon-btn")
            self._stop_btn.setStyleSheet("color: #E5484D;")
            self._stop_btn.clicked.connect(self.stop_requested.emit)
            self._stop_btn.setVisible(False)

            actions.addWidget(self._copy_btn)
            actions.addWidget(self._regen_btn)
            actions.addWidget(self._stop_btn)
            actions.addStretch()
            bubble_layout.addLayout(actions)

        main_layout.addWidget(self._bubble)
        self._bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

    def set_content(self, text: str):
        self._content.setPlainText(text)
        self._adjust_height()

    def append_text(self, text: str):
        cursor = self._content.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self._content.setTextCursor(cursor)
        self._adjust_height()

    def _adjust_height(self):
        doc = self._content.document()
        doc.setTextWidth(self._content.width() - 20)
        height = int(doc.size().height()) + 10
        self._content.setFixedHeight(max(30, min(height, 600)))

    def set_route_info(self, intent: str, confidence: float, reason: str):
        if self._role == "assistant":
            self._route_badge.setVisible(True)
            self._route_badge.set_route(intent, confidence, reason)
            badge, reason_label = self._route_badge.get_widgets()
            reason_layout = self._route_reason_container.layout()
            if reason_layout:
                reason_layout.addWidget(reason_label)

    def set_step_progress(self, current: int, total: int, description: str):
        if self._role == "assistant":
            self._step_label.setVisible(True)
            self._step_label.setText(f"步骤 {current}/{total}: {description}")

    def set_status(self, status: str):
        self._status = status
        if status == MessageStatus.GENERATING:
            self._status_label.setText("生成中...")
            self._status_label.setVisible(True)
            if hasattr(self, '_stop_btn'):
                self._stop_btn.setVisible(True)
                self._copy_btn.setVisible(False)
                self._regen_btn.setVisible(False)
        elif status == MessageStatus.STOPPED:
            self._status_label.setText("⏹ 已停止")
            self._status_label.setStyleSheet("color: #6B7280; font-size: 12px;")
            self._status_label.setVisible(True)
            if hasattr(self, '_stop_btn'):
                self._stop_btn.setVisible(False)
                self._copy_btn.setVisible(True)
                self._regen_btn.setVisible(True)
        elif status == MessageStatus.ERROR:
            self._status_label.setStyleSheet("color: #E5484D; font-size: 12px;")
            self._status_label.setVisible(True)
            if hasattr(self, '_stop_btn'):
                self._stop_btn.setVisible(False)
                self._copy_btn.setVisible(True)
                self._regen_btn.setVisible(True)
        else:
            self._status_label.setVisible(False)
            if hasattr(self, '_stop_btn'):
                self._stop_btn.setVisible(False)
                self._copy_btn.setVisible(True)
                self._regen_btn.setVisible(True)

    def get_content(self) -> str:
        return self._content.toPlainText()
