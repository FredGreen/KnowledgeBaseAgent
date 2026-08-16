"""Main window: sidebar navigation + page stack."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QStatusBar, QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from ..ui.pages.chat_page import ChatPage
from ..ui.pages.kb_page import KBPage
from ..ui.pages.settings_page import SettingsPage
from ..ui.pages.onboarding_page import OnboardingPage
from ..ui.widgets.model_selector import ModelSelector
from ..ui.theme import get_stylesheet
from ..services.config_service import ConfigService
from ..services.session_service import SessionService
from ..services.chat_service import ChatService
from ..services.kb_service import KBService
from ..constants import NavPage, MessageStatus


class MainWindow(QMainWindow):
    """Application main window with sidebar navigation."""

    def __init__(self, config_service: ConfigService, session_service: SessionService,
                 chat_service: ChatService, kb_service: KBService):
        super().__init__()
        self._config = config_service
        self._session = session_service
        self._chat = chat_service
        self._kb = kb_service
        self._setup_ui()
        self._connect_signals()
        self._init_state()

    def _setup_ui(self):
        self.setWindowTitle("智能问答 Agent")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(get_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(4)

        app_title = QLabel("🤖 智能问答")
        app_title.setStyleSheet("font-size: 18px; font-weight: 700; padding: 8px;")
        sidebar_layout.addWidget(app_title)
        sidebar_layout.addSpacing(12)

        self._nav_buttons: dict[str, QPushButton] = {}
        nav_items = [
            (NavPage.CHAT, "💬 聊天"),
            (NavPage.KB, "📚 知识库"),
            (NavPage.SETTINGS, "⚙️ 设置"),
        ]
        for page_id, label in nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=page_id: self._switch_page(p))
            sidebar_layout.addWidget(btn)
            self._nav_buttons[page_id] = btn

        sidebar_layout.addStretch()

        # Session list
        session_title = QLabel("📋 历史会话")
        session_title.setStyleSheet("font-size: 13px; font-weight: 600; padding: 4px 8px; color: #6B7280;")
        sidebar_layout.addWidget(session_title)

        self._session_list = QVBoxLayout()
        self._session_list.setSpacing(2)
        sidebar_layout.addLayout(self._session_list)

        new_session_btn = QPushButton("+ 新会话")
        new_session_btn.setObjectName("primary-btn")
        new_session_btn.clicked.connect(self._new_session)
        sidebar_layout.addWidget(new_session_btn)

        main_layout.addWidget(sidebar)

        # Right content area
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Model selector toolbar
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 0, 16, 0)

        self._model_selector = ModelSelector()
        self._model_selector.selection_changed.connect(self._on_model_changed)
        toolbar_layout.addWidget(self._model_selector)
        toolbar_layout.addStretch()

        self._route_label = QLabel()
        self._route_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        toolbar_layout.addWidget(self._route_label)

        right_layout.addWidget(toolbar)

        # Page stack
        self._pages = QStackedWidget()
        self._chat_page = ChatPage()
        self._kb_page = KBPage()
        self._settings_page = SettingsPage()
        self._onboarding_page = OnboardingPage()

        self._pages.addWidget(self._chat_page)
        self._pages.addWidget(self._kb_page)
        self._pages.addWidget(self._settings_page)
        self._pages.addWidget(self._onboarding_page)

        right_layout.addWidget(self._pages, stretch=1)
        main_layout.addWidget(right, stretch=1)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("就绪")
        self._status_bar.addWidget(self._status_label)

        # Start on chat page
        self._switch_page(NavPage.CHAT)

    def _connect_signals(self):
        self._chat_page.send_message.connect(self._on_send_message)
        self._chat_page.stop_generation.connect(self._on_stop)
        self._chat_page.regenerate.connect(self._on_regenerate)

        self._kb_page.upload_requested.connect(self._on_upload_docs)
        self._kb_page.delete_requested.connect(self._on_delete_doc)
        self._kb_page.reparse_requested.connect(self._on_reparse_doc)

        self._settings_page.save_provider.connect(self._on_save_provider)
        self._settings_page.test_connection.connect(self._on_test_connection)
        self._settings_page.save_system_prompt.connect(self._on_save_prompt)
        self._settings_page.save_generation_params.connect(self._on_save_gen_params)
        self._settings_page.save_kb_params.connect(self._on_save_kb_params)

        self._onboarding_page.skip_requested.connect(self._on_skip_onboarding)
        self._onboarding_page.start_chat.connect(self._on_skip_onboarding)

    def _init_state(self):
        if not self._config.is_initialized():
            self._pages.setCurrentWidget(self._onboarding_page)
            return

        self._refresh_model_selector()
        self._refresh_session_list()
        self._settings_page.load_config(self._config.get_all())
        self._refresh_kb_docs()

    def _switch_page(self, page: str):
        page_map = {
            NavPage.CHAT: self._chat_page,
            NavPage.KB: self._kb_page,
            NavPage.SETTINGS: self._settings_page,
        }
        widget = page_map.get(page)
        if widget:
            self._pages.setCurrentWidget(widget)
        for pid, btn in self._nav_buttons.items():
            btn.setProperty("active", pid == page)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _refresh_model_selector(self):
        providers = self._config.list_configured_providers()
        active = self._config.get_active_provider()
        model = self._config.get_active_model()
        self._chat_page.set_model_label(f"{active} / {model}")
        self._model_selector.set_providers(providers, active, model)

    def _refresh_session_list(self):
        while self._session_list.count() > 0:
            item = self._session_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sessions = self._session.list_sessions()
        active_id = self._session.get_active_session_id()
        for s in sessions[:10]:
            btn = QPushButton(s.get("title", "未命名会话"))
            btn.setCheckable(True)
            btn.setChecked(s["id"] == active_id)
            btn.setStyleSheet("font-size: 12px; padding: 4px 8px;")
            btn.clicked.connect(lambda checked, sid=s["id"]: self._load_session(sid))
            self._session_list.addWidget(btn)

    def _refresh_kb_docs(self):
        docs = self._kb.list_documents()
        self._kb_page.set_documents(docs)
        stats = self._kb.get_stats()
        self._kb_page.update_stats(stats)

    def _new_session(self):
        session = self._session.create_session()
        self._chat_page.clear_messages()
        self._chat_page.set_title(session["title"])
        self._refresh_session_list()

    def _load_session(self, session_id: str):
        self._session.set_active_session(session_id)
        messages = self._session.get_messages(session_id)
        self._chat_page.load_messages(messages)
        session = self._session.get_session(session_id)
        if session:
            self._chat_page.set_title(session.get("title", ""))
        self._refresh_session_list()

    def _on_send_message(self, text: str):
        session_id = self._session.get_active_session_id()
        self._session.add_message(session_id, "user", text)
        self._chat_page.set_generating(True)
        ai_bubble = self._chat_page.add_ai_message()

        async def _run():
            try:
                async for event in self._chat.send_message(session_id, text):
                    event_type = event.get("type", "")
                    if event_type == "route":
                        self._chat_page.set_ai_route(
                            event["intent"], event["confidence"], event["reason"]
                        )
                        self._route_label.setText(
                            f"路由: {event['intent']} (置信度 {event['confidence']:.2f})"
                        )
                    elif event_type == "step":
                        self._chat_page.set_ai_step(
                            event["current"], event["total"], event["description"]
                        )
                    elif event_type == "token":
                        self._chat_page.append_token(event["content"])
                    elif event_type == "done":
                        self._session.add_message(
                            session_id, "assistant", event["content"],
                            intent=event.get("intent", ""),
                            confidence=event.get("confidence", 0),
                            route_reason=event.get("route_reason", ""),
                            citations=event.get("citations", []),
                        )
                        self._chat_page.finish_ai_message(MessageStatus.DONE)
                    elif event_type == "error":
                        self._chat_page.finish_ai_message(MessageStatus.ERROR)
                        self._status_label.setText(f"错误: {event['message']}")
            except Exception as e:
                self._chat_page.finish_ai_message(MessageStatus.ERROR)
                self._status_label.setText(f"错误: {e}")
            finally:
                self._chat_page.set_generating(False)

        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(_run())

    def _on_stop(self):
        self._chat.stop_generation()
        self._chat_page.finish_ai_message(MessageStatus.STOPPED)
        self._chat_page.set_generating(False)

    def _on_regenerate(self):
        session_id = self._session.get_active_session_id()
        messages = self._session.get_messages(session_id)
        if messages and messages[-1]["role"] == "assistant":
            self._session.delete_last_assistant_message(session_id)
        last_user = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user = msg["content"]
                break
        if last_user:
            self._on_send_message(last_user)

    def _on_model_changed(self, provider: str, model: str):
        self._config.set_active_provider(provider)
        self._config.set_active_model(model)
        self._chat_page.set_model_label(f"{provider} / {model}")

    def _on_upload_docs(self, file_paths: list[str]):
        for path in file_paths:
            doc_id = self._kb.upload_document(path)
            self._status_label.setText(f"已上传: {path}")

        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(self._kb.process_pending_documents())
        self._refresh_kb_docs()

    def _on_delete_doc(self, doc_id: str):
        self._kb.delete_document(doc_id)
        self._refresh_kb_docs()

    def _on_reparse_doc(self, doc_id: str):
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(self._kb.reprocess_document(doc_id))
        self._refresh_kb_docs()

    def _on_save_provider(self, provider: str, base_url: str, model: str, api_key: str):
        self._config.set_provider(provider, base_url, model, api_key)
        self._refresh_model_selector()
        self._status_label.setText(f"已保存 {provider} 配置")

    def _on_test_connection(self, provider: str):
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(self._test_provider_connection(provider))

    async def _test_provider_connection(self, provider: str):
        try:
            from ..infra.llm_factory import LLMFactory
            cfg = self._config.get_provider_config(provider)
            if not cfg.get("api_key"):
                self._status_label.setText(f"{provider}: 请先输入 API Key")
                return
            llm = LLMFactory.create(provider, cfg)
            result = await llm.ainvoke("ping")
            self._status_label.setText(f"{provider}: 连接成功 ✅")
            self._model_selector.set_status(True)
        except Exception as e:
            self._status_label.setText(f"{provider}: 连接失败 - {e}")
            self._model_selector.set_status(False)

    def _on_save_prompt(self, prompt: str):
        self._config.set_system_prompt(prompt)
        self._status_label.setText("已保存系统提示词")

    def _on_save_gen_params(self, params: dict):
        self._config.set_generation_params(**params)
        self._status_label.setText("已保存生成参数")

    def _on_save_kb_params(self, params: dict):
        self._config.set_kb_params(**params)
        self._status_label.setText("已保存知识库参数")

    def _on_skip_onboarding(self):
        self._config.mark_initialized()
        self._pages.setCurrentWidget(self._chat_page)
        self._refresh_model_selector()
        self._refresh_session_list()
