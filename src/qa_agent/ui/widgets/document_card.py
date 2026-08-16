"""Document status card widget for knowledge base page."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...constants import DocStatus, DOC_STATUS_DISPLAY


class DocumentCard(QFrame):
    """A single document row in the knowledge base list."""
    delete_requested = pyqtSignal(str)
    reparse_requested = pyqtSignal(str)

    def __init__(self, doc: dict, parent=None):
        super().__init__(parent)
        self._doc = doc
        self._doc_id = doc.get("id", "")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            DocumentCard {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px;
            }
            DocumentCard:hover {
                border-color: #4F6BFF;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        icon = QLabel(self._get_icon())
        icon.setFixedWidth(30)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(self._doc.get("file_name", ""))
        name.setStyleSheet("font-weight: 600; font-size: 14px;")
        info.addWidget(name)

        meta_parts = []
        size = self._doc.get("size", 0)
        if size > 1024 * 1024:
            meta_parts.append(f"{size / (1024*1024):.1f} MB")
        elif size > 1024:
            meta_parts.append(f"{size / 1024:.1f} KB")
        else:
            meta_parts.append(f"{size} B")

        chunks = self._doc.get("chunk_count", 0)
        if chunks:
            meta_parts.append(f"{chunks} chunks")

        meta = QLabel(" · ".join(meta_parts))
        meta.setStyleSheet("color: #6B7280; font-size: 12px;")
        info.addWidget(meta)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        info.addWidget(self._progress)

        layout.addLayout(info, stretch=1)

        self._status_label = QLabel()
        self._update_status()
        layout.addWidget(self._status_label)

        actions = QHBoxLayout()
        actions.setSpacing(4)

        reparse_btn = QPushButton("🔄")
        reparse_btn.setObjectName("icon-btn")
        reparse_btn.setToolTip("重新解析")
        reparse_btn.clicked.connect(lambda: self.reparse_requested.emit(self._doc_id))
        actions.addWidget(reparse_btn)

        del_btn = QPushButton("🗑️")
        del_btn.setObjectName("icon-btn")
        del_btn.setToolTip("删除")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._doc_id))
        actions.addWidget(del_btn)

        layout.addLayout(actions)

    def _get_icon(self) -> str:
        ft = self._doc.get("file_type", "")
        return {".pdf": "📕", ".docx": "📄", ".xlsx": "📊", ".csv": "📊",
                ".md": "📝", ".txt": "📝", ".json": "📋"}.get(ft, "📄")

    def _update_status(self):
        status = self._doc.get("status", DocStatus.QUEUED)
        progress = self._doc.get("progress", 0.0)
        error = self._doc.get("error", "")

        display = DOC_STATUS_DISPLAY.get(status, status)
        if status == DocStatus.DONE:
            self._status_label.setText(f"🟢 {display}")
            self._status_label.setStyleSheet("color: #22A06B;")
            self._progress.setVisible(False)
        elif status in (DocStatus.PARSING, DocStatus.VECTORIZING):
            self._status_label.setText(f"🔵 {display} {int(progress*100)}%")
            self._status_label.setStyleSheet("color: #2E90FA;")
            self._progress.setVisible(True)
            self._progress.setValue(int(progress * 100))
        elif status == DocStatus.QUEUED:
            self._status_label.setText(f"🟠 {display}")
            self._status_label.setStyleSheet("color: #F5A623;")
            self._progress.setVisible(False)
        elif status == DocStatus.FAILED:
            self._status_label.setText(f"🔴 {display}")
            self._status_label.setStyleSheet("color: #E5484D;")
            if error:
                self._status_label.setToolTip(error)
            self._progress.setVisible(False)

    def update_doc(self, doc: dict):
        self._doc = doc
        self._update_status()
