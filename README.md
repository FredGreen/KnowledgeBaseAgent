# 智能问答 Agent

基于 Python + PyQt6 的桌面应用，提供本地知识库 + 多供应商云端模型的智能问答能力。支持意图路由工作流（LangGraph）、RAG 检索增强生成、多轮对话、流式输出。

## 功能特性

### M1 - 基础对话

- **多供应商 LLM 接入**：OpenAI / Anthropic / 通义千问 / 智谱 / DeepSeek / 自定义兼容端点
- **多轮对话**：支持上下文记忆，可配置保留轮数
- **流式输出**：实时逐字显示 AI 回答
- **System Prompt**：自定义系统提示词
- **生成参数调节**：Temperature / TopP / MaxTokens 可视化滑块调节
- **会话管理**：新建 / 切换 / 删除 / 重命名会话

### M2 - 知识库 & RAG

- **知识库管理**：上传 / 删除 / 重新索引文档
- **多格式支持**：PDF / DOCX / CSV / XLSX / Markdown / TXT / JSON
- **智能切分**：递归字符切分 + 重叠窗口
- **向量检索**：Milvus Lite 内嵌向量数据库，零配置
- **意图路由**：LangGraph 工作流自动判断直答 / RAG / 复杂推理路径
- **引用来源**：回答附带文档引用，可追溯原文

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| GUI | PyQt6 + qasync |
| Agent 编排 | LangChain v1.1.2 + LangGraph v1.0.2 |
| 向量数据库 | Milvus Lite（内嵌模式） |
| 关系数据库 | SQLite |
| 密钥管理 | keyring |
| 包管理 | uv / pip |

## 项目结构

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
│   │   ├── config_service.py        # 配置管理
│   │   ├── session_service.py       # 会话管理（SQLite）
│   │   ├── chat_service.py          # 聊天服务（调用 Agent 图）
│   │   └── kb_service.py            # 知识库服务（上传/解析/检索）
│   ├── agent/
│   │   ├── schema.py                # QAState（TypedDict）
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

## Agent 工作流

```
START → router → {direct_qa | rag → reasoning} → output → END
```

- **router**：LLM 结构化输出判断意图（direct / rag / complex）
- **direct_qa**：直答路径，无需检索知识库
- **rag**：向量检索 + 上下文构建
- **reasoning**：LLM 流式生成回答
- **output**：格式化输出 + 引用提取

## 安装与运行

### 环境要求

- Python 3.10+
- 桌面环境（需要 GUI 支持）

### 安装依赖

```bash
pip install PyQt6 qasync langchain==1.1.2 "langgraph>=1.0.2,<1.1.0" \
  langchain-openai langchain-anthropic pymilvus pypdf python-docx \
  openpyxl pandas markdown-it-py beautifulsoup4 keyring numpy
```

或使用 uv：

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

### 运行

```bash
python main.py
```

### 首次使用

1. 启动后进入引导页，配置 LLM 供应商 API Key
2. 配置 Embedding 模型（默认通义千问 text-embedding-v3）
3. 进入聊天页，开始对话
4. 在知识库页上传文档，启用 RAG 增强

## 配置存储

- **配置文件**：`~/.intelligent_qa_agent/settings.json`
- **会话数据库**：`~/.intelligent_qa_agent/sessions.db`
- **文档数据库**：`~/.intelligent_qa_agent/documents.db`
- **向量数据**：`~/.intelligent_qa_agent/milvus_data/`

## 支持的 LLM 供应商

| 供应商 | 模型示例 |
|--------|----------|
| OpenAI | gpt-4o, gpt-4o-mini |
| Anthropic | claude-3-5-sonnet-20241022 |
| 通义千问 | qwen-plus, qwen-turbo |
| 智谱 | glm-4-plus, glm-4-air |
| DeepSeek | deepseek-chat |
| 自定义 | 任何 OpenAI 兼容端点 |

## License

MIT
