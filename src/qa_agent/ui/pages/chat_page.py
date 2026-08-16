"""Chat page: main conversation interface."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton,
    QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from ...ui.widgets.message_bubble import MessageBubble
from ...ui.widgets.chat_input import ChatInput
from ...ui.widgets.citation_panel import CitationPanel
from ...constants import MessageStatus


class ChatPage(QWidget):
    """Main chat page with message area and input."""
    send_message = pyqtSignal(str)
    stop_generation = pyqtSignal()
    regenerate = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_ai_bubble = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: white; border-bottom: 1px solid #E5E7EB;")
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        self._title_label = QLabel("新会话")
        self._title_label.setStyleSheet("font-weight: 700; font-size: 16px;")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        self._model_label = QLabel()
        self._model_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        header_layout.addWidget(self._model_label)

        layout.addWidget(header)

        # Message area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._message_container = QWidget()
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.setContentsMargins(16, 16, 16, 16)
        self._message_layout.setSpacing(12)
        self._message_layout.addStretch()

        self._scroll.setWidget(self._message_container)
        layout.addWidget(self._scroll, stretch=1)

        # Welcome label (shown when empty)
        self._welcome = QLabel("💬 开始对话吧\n你可以提问、上传文档建立知识库，或切换模型")
        self._welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._welcome.setStyleSheet("color: #6B7280; font-size: 16px; padding: 40px;")
        self._message_layout.insertWidget(0, self._welcome)

        # Input area
        self._input = ChatInput()
        self._input.send_requested.connect(self._on_send)
        self._input.stop_requested.connect(self.stop_generation.emit)
        layout.addWidget(self._input)

    def _on_send(self, text: str):
        self._welcome.setVisible(False)
        self.add_user_message(text)
        self.send_message.emit(text)

    def add_user_message(self, text: str) -> MessageBubble:
        bubble = MessageBubble(role="user")
        bubble.set_content(text)
        idx = self._message_layout.count() - 1
        self._message_layout.insertWidget(idx, bubble)
        self._scroll_to_bottom()
        return bubble

    def add_ai_message(self) -> MessageBubble:
        bubble = MessageBubble(role="assistant")
        bubble.set_status(MessageStatus.GENERATING)
        bubble.stop_requested.connect(self.stop_generation.emit)
        bubble.regenerate_requested.connect(self.regenerate.emit)
        idx = self._message_layout.count() - 1
        self._message_layout.insertWidget(idx, bubble)
        self._current_ai_bubble = bubble
        self._scroll_to_bottom()
        return bubble

    def append_token(self, token: str):
        if self._current_ai_bubble:
            self._current_ai_bubble.append_text(token)
            self._scroll_to_bottom()

    def set_ai_route(self, intent: str, confidence: float, reason: str):
        if self._current_ai_bubble:
            self._current_ai_bubble.set_route_info(intent, confidence, reason)

    def set_ai_step(self, current: int, total: int, desc: str):
        if self._current_ai_bubble:
            self._current_ai_bubble.set_step_progress(current, total, desc)

    def finish_ai_message(self, status: str = MessageStatus.DONE):
        if self._current_ai_bubble:
            self._current_ai_bubble.set_status(status)
            self._current_ai_bubble = None

    def set_generating(self, generating: bool):
        self._input.set_generating(generating)

    def set_title(self, title: str):
        self._title_label.setText(title)

    def set_model_label(self, text: str):
        self._model_label.setText(text)

    def clear_messages(self):
        while self._message_layout.count() > 1:
            item = self._message_layout.takeAt(0)
            if item.widget() and item.widget() != self._welcome:
                item.widget().deleteLater()
        self._current_ai_bubble = None
        self._welcome.setVisible(True)

    def load_messages(self, messages: list[dict]):
        self.clear_messages()
        if not messages:
            return
        self._welcome.setVisible(False)
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                bubble = MessageBubble(role="user")
                bubble.set_content(content)
            else:
                bubble = MessageBubble(role="assistant")
                bubble.set_content(content)
                intent = msg.get("intent", "")
                if intent:
                    bubble.set_route_info(intent, msg.get("confidence", 0), msg.get("route_reason", ""))
                status = msg.get("status", "done")
                if status != "done":
                    bubble.set_status(status)
                bubble.regenerate_requested.connect(self.regenerate.emit)
            idx = self._message_layout.count() - 1
            self._message_layout.insertWidget(idx, bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))
