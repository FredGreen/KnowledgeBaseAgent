"""Onboarding page: first-time setup wizard."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...constants import Provider, PROVIDER_DISPLAY, PROVIDER_DEFAULT_MODELS


class OnboardingPage(QWidget):
    """First-time setup wizard page."""
    setup_complete = pyqtSignal(str, str, str, str)
    skip_requested = pyqtSignal()
    start_chat = pyqtSignal()
    go_to_kb = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._step = 1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("🎉 欢迎使用 智能问答 Agent")
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: #1A1A2E;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("你的本地私有知识库 + 多模型智能问答助手")
        subtitle.setStyleSheet("font-size: 16px; color: #6B7280;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Step indicator
        self._step_label = QLabel("步骤 1/3: 选择一个模型供应商")
        self._step_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #4F6BFF;")
        self._step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._step_label)

        # Provider selection
        self._provider_combo = QComboBox()
        for prov in [Provider.OPENAI, Provider.ANTHROPIC, Provider.QWEN, Provider.ZHIPU, Provider.DEEPSEEK]:
            self._provider_combo.addItem(PROVIDER_DISPLAY[prov], prov.value)
        self._provider_combo.setMinimumWidth(200)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        layout.addWidget(self._provider_combo, alignment=Qt.AlignmentFlag.AlignCenter)

        # API Key input
        key_layout = QHBoxLayout()
        key_layout.setSpacing(8)
        self._api_key_input = QLineEdit()
        self._api_key_input.setPlaceholderText("输入 API Key")
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setMinimumWidth(300)
        key_layout.addWidget(self._api_key_input)

        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(160)
        self._model_combo.setEditable(True)
        key_layout.addWidget(self._model_combo)
        self._on_provider_changed(0)

        layout.addLayout(key_layout)

        # Test result
        self._test_result = QLabel()
        self._test_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._test_result.setStyleSheet("font-size: 14px;")
        layout.addWidget(self._test_result)

        test_btn = QPushButton("🔗 测试连接")
        test_btn.setObjectName("secondary-btn")
        test_btn.setFixedWidth(160)
        test_btn.clicked.connect(self._test)
        layout.addWidget(test_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Navigation buttons
        nav = QHBoxLayout()
        skip_btn = QPushButton("跳过引导")
        skip_btn.setObjectName("secondary-btn")
        skip_btn.clicked.connect(self.skip_requested.emit)

        self._next_btn = QPushButton("下一步 →")
        self._next_btn.setObjectName("primary-btn")
        self._next_btn.clicked.connect(self._next_step)

        nav.addWidget(skip_btn)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

    def _on_provider_changed(self, index):
        models = PROVIDER_DEFAULT_MODELS.get(Provider(self._provider_combo.currentData()), [])
        self._model_combo.clear()
        self._model_combo.addItems(models)

    def _test(self):
        self._test_result.setText("⏳ 测试中...")
        self._test_result.setStyleSheet("color: #2E90FA; font-size: 14px;")

    def set_test_result(self, success: bool, message: str):
        if success:
            self._test_result.setText(f"✅ {message}")
            self._test_result.setStyleSheet("color: #22A06B; font-size: 14px;")
        else:
            self._test_result.setText(f"❌ {message}")
            self._test_result.setStyleSheet("color: #E5484D; font-size: 14px;")

    def _next_step(self):
        self._step += 1
        if self._step == 2:
            self._step_label.setText("步骤 2/3: 测试连接")
            self._test()
        elif self._step == 3:
            self._step_label.setText("步骤 3/3: 开始使用")
            self._next_btn.setText("💬 开始对话")
            self._next_btn.clicked.disconnect()
            self._next_btn.clicked.connect(self.start_chat.emit)
        else:
            self.setup_complete.emit(
                self._provider_combo.currentData(),
                "",
                self._model_combo.currentText(),
                self._api_key_input.text(),
            )

    def get_config(self) -> tuple[str, str, str, str]:
        return (
            self._provider_combo.currentData(),
            "",
            self._model_combo.currentText(),
            self._api_key_input.text(),
        )
