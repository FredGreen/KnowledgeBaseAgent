"""Citation panel widget for right sidebar."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal


class CitationCard(QFrame):
    """A single citation reference card."""
    clicked = pyqtSignal(dict)

    def __init__(self, citation: dict, parent=None):
        super().__init__(parent)
        self._citation = citation
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            CitationCard {{
                background-color: #F8F9FA;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px;
            }}
            CitationCard:hover {{
                border-color: #4F6BFF;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        idx_label = QLabel(f"[{citation.get('index', 0)}]")
        idx_label.setStyleSheet("font-weight: 700; color: #4F6BFF;")
        file_label = QLabel(citation.get("file_name", ""))
        file_label.setStyleSheet("color: #1A1A2E;")
        header.addWidget(idx_label)
        header.addWidget(file_label)
        header.addStretch()
        layout.addLayout(header)

        page_label = QLabel(f"📄 {citation.get('page_or_par', '')}")
        page_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(page_label)

        score = citation.get("score", 0)
        score_label = QLabel(f"相似度: {score:.3f}")
        score_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(score_label)

        snippet = citation.get("snippet", "")[:150]
        if snippet:
            snippet_label = QLabel(snippet + "...")
            snippet_label.setWordWrap(True)
            snippet_label.setStyleSheet("color: #4B5563; font-size: 12px; margin-top: 4px;")
            layout.addWidget(snippet_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self._citation)
        super().mousePressEvent(event)


class CitationPanel(QWidget):
    """Panel showing all citations for the current answer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("📚 引用来源")
        title.setStyleSheet("font-weight: 700; font-size: 14px; padding: 4px 0;")
        layout.addWidget(title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(6)
        self._container_layout.addStretch()

        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll)

        self._empty_label = QLabel("暂无引用")
        self._empty_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_label)

    def set_citations(self, citations: list[dict]):
        while self._container_layout.count() > 1:
            item = self._container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not citations:
            self._empty_label.setVisible(True)
            return

        self._empty_label.setVisible(False)
        for cite in citations:
            card = CitationCard(cite)
            self._container_layout.insertWidget(self._container_layout.count() - 1, card)

    def clear(self):
        while self._container_layout.count() > 1:
            item = self._container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._empty_label.setVisible(True)
