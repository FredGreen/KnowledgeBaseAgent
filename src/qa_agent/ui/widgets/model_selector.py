"""Model selector widget."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton,
)
from PyQt6.QtCore import pyqtSignal

from ...constants import Provider, PROVIDER_DISPLAY, PROVIDER_DEFAULT_MODELS


class ModelSelector(QWidget):
    """Top-bar model selector dropdown."""
    selection_changed = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel("模型:")
        label.setStyleSheet("font-weight: 600;")
        layout.addWidget(label)

        self._combo = QComboBox()
        self._combo.setMinimumWidth(180)
        self._combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self._combo)

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet("color: #22A06B;")
        layout.addWidget(self._status_dot)

    def set_providers(self, configured: list[str], active_provider: str, active_model: str):
        self._combo.blockSignals(True)
        self._combo.clear()
        for prov in configured:
            display = PROVIDER_DISPLAY.get(Provider(prov), prov)
            models = PROVIDER_DEFAULT_MODELS.get(Provider(prov), [])
            for model in models:
                self._combo.addItem(f"{display} / {model}", (prov, model))
            if not models:
                self._combo.addItem(f"{display}", (prov, ""))

        for i in range(self._combo.count()):
            data = self._combo.itemData(i)
            if data and data[0] == active_provider and data[1] == active_model:
                self._combo.setCurrentIndex(i)
                break
        self._combo.blockSignals(False)

    def _on_changed(self, index):
        data = self._combo.itemData(index)
        if data:
            self.selection_changed.emit(data[0], data[1])

    def set_status(self, ok: bool):
        self._status_dot.setStyleSheet(f"color: {'#22A06B' if ok else '#E5484D'};")
