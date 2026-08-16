"""Knowledge base management page."""

import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...ui.widgets.document_card import DocumentCard
from ...constants import DocStatus


class KBPage(QWidget):
    """Knowledge base management page."""
    upload_requested = pyqtSignal(list)
    delete_requested = pyqtSignal(str)
    reparse_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[str, DocumentCard] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Title
        title = QLabel("📚 知识库管理")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        # Upload area
        upload_frame = QFrame()
        upload_frame.setFrameShape(QFrame.Shape.StyledPanel)
        upload_frame.setStyleSheet("""
            QFrame {
                background: #F8F9FA;
                border: 2px dashed #D1D5DB;
                border-radius: 12px;
            }
        """)
        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setContentsMargins(24, 24, 24, 24)
        upload_layout.setSpacing(12)

        upload_text = QLabel("将文件拖拽到此处，或点击选择文件（多选）")
        upload_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_text.setStyleSheet("color: #6B7280; font-size: 14px;")
        upload_layout.addWidget(upload_text)

        format_text = QLabel("支持格式: txt / md / pdf / docx / csv / xlsx / json")
        format_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        format_text.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        upload_layout.addWidget(format_text)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._upload_btn = QPushButton("📤 上传文件")
        self._upload_btn.setObjectName("primary-btn")
        self._upload_btn.setFixedWidth(160)
        self._upload_btn.clicked.connect(self._on_upload)
        btn_row.addWidget(self._upload_btn)
        btn_row.addStretch()
        upload_layout.addLayout(btn_row)

        layout.addWidget(upload_frame)

        # Document list
        list_title = QLabel("文档列表")
        list_title.setStyleSheet("font-weight: 600; font-size: 15px;")
        layout.addWidget(list_title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_container)
        layout.addWidget(self._scroll, stretch=1)

        # Empty state
        self._empty_label = QLabel("📂 上传第一份文档，开始构建你的知识库")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #9CA3AF; font-size: 15px; padding: 40px;")
        self._list_layout.insertWidget(0, self._empty_label)

        # Stats bar
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet("color: #6B7280; font-size: 13px; padding: 4px 0;")
        layout.addWidget(self._stats_label)

    def _on_upload(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "支持的文件 (*.txt *.md *.pdf *.docx *.csv *.xlsx *.json);;所有文件 (*)"
        )
        if files:
            self.upload_requested.emit(files)

    def set_documents(self, docs: list[dict]):
        has_docs = bool(docs)
        self._empty_label.setVisible(not has_docs)

        existing_ids = set()
        for doc in docs:
            doc_id = doc.get("id", "")
            existing_ids.add(doc_id)
            if doc_id in self._cards:
                self._cards[doc_id].update_doc(doc)
            else:
                card = DocumentCard(doc)
                card.delete_requested.connect(self.delete_requested.emit)
                card.reparse_requested.connect(self.reparse_requested.emit)
                self._cards[doc_id] = card
                idx = self._list_layout.count() - 1
                self._list_layout.insertWidget(idx, card)

        to_remove = [did for did in self._cards if did not in existing_ids]
        for did in to_remove:
            card = self._cards.pop(did)
            card.setParent(None)
            card.deleteLater()

    def update_stats(self, stats: dict):
        doc_count = stats.get("doc_count", 0)
        chunks = stats.get("total_chunks", 0)
        size = stats.get("total_size", 0)
        if size > 1024 * 1024:
            size_str = f"{size / (1024*1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        self._stats_label.setText(f"📊 文档 {doc_count} · Chunk {chunks} · 占用 {size_str}")

    def update_doc_status(self, doc_id: str, status: str, progress: float):
        if doc_id in self._cards:
            self._cards[doc_id].update_doc({
                "id": doc_id, "status": status, "progress": progress,
                "file_name": "", "error": "",
            })
