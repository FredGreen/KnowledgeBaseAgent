"""Parameter slider widget."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal


class ParamSlider(QWidget):
    """Labeled slider with optional spin box for settings page."""
    value_changed = pyqtSignal(float)

    def __init__(self, label: str, min_val: float = 0.0, max_val: float = 1.0,
                 default: float = 0.5, step: float = 0.1, parent=None):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._step = step

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self._label = QLabel(label)
        self._label.setStyleSheet("font-weight: 500;")
        self._value_label = QLabel(str(default))
        self._value_label.setStyleSheet("color: #4F6BFF; font-weight: 600;")
        header.addWidget(self._label)
        header.addStretch()
        header.addWidget(self._value_label)
        layout.addLayout(header)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        steps = int((max_val - min_val) / step)
        self._slider.setRange(0, steps)
        self._slider.setValue(int((default - min_val) / step))
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider)

    def _on_slider_changed(self, value):
        actual = self._min + value * self._step
        self._value_label.setText(f"{actual:.2f}")
        self.value_changed.emit(actual)

    def get_value(self) -> float:
        return self._min + self._slider.value() * self._step

    def set_value(self, value: float):
        steps = int((value - self._min) / self._step)
        self._slider.setValue(steps)
        self._value_label.setText(f"{value:.2f}")
