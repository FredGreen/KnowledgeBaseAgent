"""Settings page with tabbed configuration groups."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTabWidget, QComboBox, QTextEdit, QGroupBox, QFormLayout, QCheckBox,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...constants import (
    Provider, PROVIDER_DISPLAY, PROVIDER_DEFAULT_BASE_URL, PROVIDER_DEFAULT_MODELS,
    DEFAULT_SYSTEM_PROMPT, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_MAX_TOKENS,
    DEFAULT_CONTEXT_ROUNDS, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD,
)
from ...ui.widgets.param_slider import ParamSlider


class SettingsPage(QWidget):
    """Settings page with tabs for different config groups."""
    save_provider = pyqtSignal(str, str, str, str)
    test_connection = pyqtSignal(str)
    save_system_prompt = pyqtSignal(str)
    save_generation_params = pyqtSignal(dict)
    save_kb_params = pyqtSignal(dict)
    save_embedding = pyqtSignal(str, str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._provider_fields: dict[str, dict] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("⚙️ 设置")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._tabs.addTab(self._create_model_tab(), "🤖 模型设置")
        self._tabs.addTab(self._create_prompt_tab(), "📝 提示词")
        self._tabs.addTab(self._create_generation_tab(), "🎛️ 生成参数")
        self._tabs.addTab(self._create_kb_tab(), "📚 知识库参数")
        self._tabs.addTab(self._create_general_tab(), "🔧 通用")

    def _create_model_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(12)

        for prov in [Provider.OPENAI, Provider.ANTHROPIC, Provider.QWEN,
                     Provider.ZHIPU, Provider.DEEPSEEK, Provider.CUSTOM]:
            group = QGroupBox(PROVIDER_DISPLAY[prov])
            group_layout = QFormLayout(group)

            base_url = QLineEdit()
            base_url.setPlaceholderText(PROVIDER_DEFAULT_BASE_URL.get(prov, "自定义 Base URL"))
            group_layout.addRow("Base URL:", base_url)

            api_key = QLineEdit()
            api_key.setPlaceholderText("输入 API Key")
            api_key.setEchoMode(QLineEdit.EchoMode.Password)
            group_layout.addRow("API Key:", api_key)

            model = QComboBox()
            model.setEditable(prov == Provider.CUSTOM)
            models = PROVIDER_DEFAULT_MODELS.get(prov, [])
            if models:
                model.addItems(models)
            group_layout.addRow("模型:", model)

            btn_row = QHBoxLayout()
            test_btn = QPushButton("🔗 测试连接")
            test_btn.setObjectName("secondary-btn")
            test_btn.clicked.connect(lambda checked, p=prov.value: self.test_connection.emit(p))
            save_btn = QPushButton("💾 保存")
            save_btn.setObjectName("primary-btn")
            save_btn.clicked.connect(lambda checked, p=prov.value: self._save_provider(p))
            btn_row.addWidget(test_btn)
            btn_row.addWidget(save_btn)
            btn_row.addStretch()
            group_layout.addRow(btn_row)

            self._provider_fields[prov.value] = {
                "base_url": base_url, "api_key": api_key, "model": model,
            }
            container_layout.addWidget(group)

        # Embedding section
        emb_group = QGroupBox("Embedding 模型（独立配置）")
        emb_layout = QFormLayout(emb_group)

        self._emb_model = QComboBox()
        self._emb_model.addItems(["text-embedding-v3", "text-embedding-v2", "text-embedding-v1"])
        self._emb_model.setEditable(True)
        emb_layout.addRow("模型:", self._emb_model)

        self._emb_api_key = QLineEdit()
        self._emb_api_key.setPlaceholderText("Embedding API Key")
        self._emb_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        emb_layout.addRow("API Key:", self._emb_api_key)

        emb_warning = QLabel("⚠️ 更换 Embedding 模型需全量重建索引")
        emb_warning.setStyleSheet("color: #F5A623; font-size: 12px;")
        emb_layout.addRow(emb_warning)

        emb_save = QPushButton("💾 保存 Embedding 配置")
        emb_save.setObjectName("primary-btn")
        emb_save.clicked.connect(self._save_embedding_config)
        emb_layout.addRow(emb_save)

        container_layout.addWidget(emb_group)
        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)
        return widget

    def _create_prompt_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("System Prompt（系统提示词）")
        label.setStyleSheet("font-weight: 600;")
        layout.addWidget(label)

        self._prompt_edit = QTextEdit()
        self._prompt_edit.setPlaceholderText("输入系统提示词...")
        self._prompt_edit.setMinimumHeight(200)
        layout.addWidget(self._prompt_edit)

        self._char_count = QLabel("字符: 0")
        self._char_count.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(self._char_count)
        self._prompt_edit.textChanged.connect(
            lambda: self._char_count.setText(f"字符: {len(self._prompt_edit.toPlainText())}")
        )

        btn_row = QHBoxLayout()
        restore_btn = QPushButton("恢复默认")
        restore_btn.setObjectName("secondary-btn")
        restore_btn.clicked.connect(lambda: self._prompt_edit.setPlainText(DEFAULT_SYSTEM_PROMPT))
        save_btn = QPushButton("💾 保存")
        save_btn.setObjectName("primary-btn")
        save_btn.clicked.connect(lambda: self.save_system_prompt.emit(self._prompt_edit.toPlainText()))
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _create_generation_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._temp_slider = ParamSlider("Temperature", 0.0, 2.0, DEFAULT_TEMPERATURE, 0.05)
        layout.addWidget(self._temp_slider)

        self._top_p_slider = ParamSlider("Top P", 0.0, 1.0, DEFAULT_TOP_P, 0.05)
        layout.addWidget(self._top_p_slider)

        self._max_tokens_slider = ParamSlider("最大输出长度", 256, 8192, DEFAULT_MAX_TOKENS, 256)
        layout.addWidget(self._max_tokens_slider)

        self._context_slider = ParamSlider("上下文轮数", 1, 30, DEFAULT_CONTEXT_ROUNDS, 1)
        layout.addWidget(self._context_slider)

        btn_row = QHBoxLayout()
        restore_btn = QPushButton("恢复默认")
        restore_btn.setObjectName("secondary-btn")
        restore_btn.clicked.connect(self._restore_gen_defaults)
        save_btn = QPushButton("💾 保存")
        save_btn.setObjectName("primary-btn")
        save_btn.clicked.connect(self._save_gen_params)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _create_kb_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._chunk_size_slider = ParamSlider("Chunk 大小", 100, 2000, DEFAULT_CHUNK_SIZE, 50)
        layout.addWidget(self._chunk_size_slider)

        self._chunk_overlap_slider = ParamSlider("重叠比例", 0.0, 0.5, DEFAULT_CHUNK_OVERLAP, 0.05)
        layout.addWidget(self._chunk_overlap_slider)

        self._top_k_slider = ParamSlider("Top K", 1, 20, DEFAULT_TOP_K, 1)
        layout.addWidget(self._top_k_slider)

        self._threshold_slider = ParamSlider("相似度阈值", 0.0, 1.0, DEFAULT_SIMILARITY_THRESHOLD, 0.05)
        layout.addWidget(self._threshold_slider)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 保存")
        save_btn.setObjectName("primary-btn")
        save_btn.clicked.connect(self._save_kb_params)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)

        self._proxy_edit = QLineEdit()
        self._proxy_edit.setPlaceholderText("http://proxy:port")
        layout.addRow("HTTP 代理:", self._proxy_edit)

        self._log_level = QComboBox()
        self._log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addRow("日志级别:", self._log_level)

        layout.addRow(QLabel("数据存储路径: 默认用户目录"))
        layout.addStretch()
        return widget

    def _save_provider(self, provider: str):
        fields = self._provider_fields.get(provider, {})
        base_url = fields.get("base_url", QLineEdit()).text()
        api_key = fields.get("api_key", QLineEdit()).text()
        model_widget = fields.get("model", QComboBox())
        model = model_widget.currentText() if isinstance(model_widget, QComboBox) else model_widget.text()
        self.save_provider.emit(provider, base_url, model, api_key)

    def _save_embedding_config(self):
        model = self._emb_model.currentText()
        api_key = self._emb_api_key.text()
        self.save_embedding.emit("qwen", model, api_key, "")

    def _restore_gen_defaults(self):
        self._temp_slider.set_value(DEFAULT_TEMPERATURE)
        self._top_p_slider.set_value(DEFAULT_TOP_P)
        self._max_tokens_slider.set_value(DEFAULT_MAX_TOKENS)
        self._context_slider.set_value(DEFAULT_CONTEXT_ROUNDS)

    def _save_gen_params(self):
        self.save_generation_params.emit({
            "temperature": self._temp_slider.get_value(),
            "top_p": self._top_p_slider.get_value(),
            "max_tokens": int(self._max_tokens_slider.get_value()),
            "context_rounds": int(self._context_slider.get_value()),
        })

    def _save_kb_params(self):
        self.save_kb_params.emit({
            "chunk_size": int(self._chunk_size_slider.get_value()),
            "chunk_overlap": self._chunk_overlap_slider.get_value(),
            "top_k": int(self._top_k_slider.get_value()),
            "similarity_threshold": self._threshold_slider.get_value(),
        })

    def load_config(self, config: dict):
        gen = config.get("generation", {})
        self._temp_slider.set_value(gen.get("temperature", DEFAULT_TEMPERATURE))
        self._top_p_slider.set_value(gen.get("top_p", DEFAULT_TOP_P))
        self._max_tokens_slider.set_value(gen.get("max_tokens", DEFAULT_MAX_TOKENS))
        self._context_slider.set_value(gen.get("context_rounds", DEFAULT_CONTEXT_ROUNDS))

        kb = config.get("knowledge_base", {})
        self._chunk_size_slider.set_value(kb.get("chunk_size", DEFAULT_CHUNK_SIZE))
        self._chunk_overlap_slider.set_value(kb.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP))
        self._top_k_slider.set_value(kb.get("top_k", DEFAULT_TOP_K))
        self._threshold_slider.set_value(kb.get("similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD))

        self._prompt_edit.setPlainText(config.get("system_prompt", DEFAULT_SYSTEM_PROMPT))

        providers = config.get("providers", {})
        for prov, fields in self._provider_fields.items():
            pcfg = providers.get(prov, {})
            if pcfg.get("base_url"):
                fields["base_url"].setText(pcfg["base_url"])
            if pcfg.get("model"):
                model_widget = fields["model"]
                if isinstance(model_widget, QComboBox):
                    idx = model_widget.findText(pcfg["model"])
                    if idx >= 0:
                        model_widget.setCurrentIndex(idx)
