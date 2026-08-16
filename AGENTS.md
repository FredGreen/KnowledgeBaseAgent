# 智能问答 Agent

## 项目概述

基于 Python + PyQt6 的桌面应用，提供本地知识库 + 多供应商云端模型的智能问答能力。支持意图路由工作流（LangGraph）、RAG 检索增强生成、多轮对话、流式输出。

## 技术栈

- **语言**: Python 3.10+
- **GUI**: PyQt6 + qasync（Qt 与 asyncio 桥接）
- **Agent 编排**: LangChain v1.1.2 + LangGraph v1.0.2（StateGraph）
- **向量数据库**: Milvus Lite（内嵌模式，零配置）
- **关系数据库**: SQLite（会话/文档元数据）
- **密钥管理**: keyring
- **包管理**: uv

## 目录结构

```
├── main.py                          # 应用入口
├── pyproject.toml                   # 依赖声明
├── config/default_settings.json     # 默认配置
├── src/qa_agent/
│   ├── app.py                       # Application 类：组装所有服务
│   ├── constants.py                 # 全局常量、枚举、默认值
│   ├── ui/
│   │   ├── main_window.py           # 主窗口：侧边栏 + 页面栈
│   │   ├── theme.py                 # QSS 主题样式
│   │   ├── pages/
│   │   │   ├── chat_page.py         # 聊天页
│   │   │   ├── kb_page.py           # 知识库管理页
│   │   │   ├── settings_page.py     # 设置页（分 Tab）
│   │   │   └── onboarding_page.py   # 首次引导页
│   │   └── widgets/
│   │       ├── message_bubble.py    # 消息气泡（含路由徽章）
│   │       ├── citation_panel.py    # 引用来源面板
│   │       ├── chat_input.py        # 聊天输入框
│   │       ├── model_selector.py    # 模型选择器
│   │       ├── param_slider.py      # 参数滑块
│   │       └── document_card.py     # 文档状态卡片
│   ├── services/
│   │   ├── config_service.py        # 配置管理（settings.json）
│   │   ├── session_service.py       # 会话管理（SQLite）
│   │   ├── chat_service.py          # 聊天服务（调用 Agent 图）
│   │   └── kb_service.py            # 知识库服务（上传/解析/检索）
│   ├── agent/
│   │   ├── schema.py                # AgentState（TypedDict）
│   │   ├── graph_builder.py         # 构建 LangGraph 工作流
│   │   ├── streaming.py             # 流式桥接（astream → Qt 信号）
│   │   └── nodes/
│   │       ├── router.py            # 意图路由节点
│   │       ├── direct_qa.py         # 直答节点
│   │       ├── rag.py               # RAG 检索节点
│   │       ├── reasoning.py         # 推理/生成节点
│   │       └── output.py            # 输出格式化节点
│   ├── data/
│   │   ├── vector_store.py          # Milvus 向量存储封装
│   │   ├── embeddings.py            # Embedding 适配器
│   │   ├── splitter.py              # 文本切分器
│   │   ├── parsers/                 # 文档解析器（PDF/DOCX/CSV/XLSX/MD/TXT/JSON）
│   │   └── repositories/            # SQLite 仓储（session/message/document）
│   ├── infra/
│   │   ├── llm_factory.py           # LLM 工厂（多供应商）
│   │   ├── embedding_factory.py     # Embedding 工厂
│   │   ├── security.py              # 密钥安全存储（keyring）
│   │   └── logging.py               # 日志配置
│   └── utils/
│       ├── errors.py                # 异常类型
│       └── text_utils.py            # 文本工具函数
```

## 关键入口

- **启动**: `python main.py`（需要 PyQt6 和 qasync）
- **Application 类**: `src/qa_agent/app.py` — 组装所有服务
- **Agent 图构建**: `src/qa_agent/agent/graph_builder.py` — LangGraph StateGraph
- **配置存储**: `~/.intelligent_qa_agent/settings.json`
- **数据库**: `~/.intelligent_qa_agent/sessions.db`, `documents.db`
- **向量数据**: `~/.intelligent_qa_agent/milvus_data/`

## 运行与预览

- **类型**: 桌面应用（PyQt6），不可在 Web 沙箱中预览
- **运行**: 需本地安装 PyQt6 + qasync，执行 `python main.py`
- **预览**: 不支持（preview_enable = disabled）

## 核心架构

### Agent 工作流（LangGraph）

```
START → router → {direct_qa | rag → reasoning} → output → END
```

- **router**: LLM 结构化输出判断意图（direct/rag/complex）
- **direct_qa**: 直答路径，无检索
- **rag**: 向量检索 + 上下文构建
- **reasoning**: LLM 流式生成回答
- **output**: 格式化输出 + 引用提取

### 多供应商支持

OpenAI / Anthropic / 通义千问 / 智谱 / DeepSeek / 自定义兼容端点

### Embedding

默认使用通义千问 text-embedding-v3，独立于 LLM 配置。

## 用户偏好与长期约束

- LangChain/LangGraph 使用 v1.1.2（langgraph 实际安装 v1.0.2，因依赖约束）
- Embedding 默认通义千问 text-embedding-v3
- Milvus 默认 Lite 模式
- 不安装 PyQt6，代码写完由用户本地运行验证
