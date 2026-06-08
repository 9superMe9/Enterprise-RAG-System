# 🤖 Enterprise-RAG-System (星际科技私有知识库)

基于 RAG (Retrieval-Augmented Generation) 架构的企业级私有知识库问答系统。解决大模型在垂直领域幻觉严重、数据隐私不可控的问题。

## ✅ 核心亮点
- 🔒 **数据隐私**：基于本地向量库，企业数据无需上传至公有云大模型。
- 🎯 **精准拒答**：优化 Prompt，对超出知识库的问题坚决拒绝，有效降低大模型幻觉。
- ✂️ **智能切分**：基于 `RecursiveCharacterTextSplitter` 与段落语义的精准文档切分，提升检索召回率。
- 🌐 **双界面**：命令行 + Streamlit Web + REST API 三种访问方式。

## 🛠️ 技术栈
- **大模型**：DeepSeek API (兼容 OpenAI SDK)
- **编排框架**：LangChain
- **向量数据库**：ChromaDB
- **Embedding 模型**：shibing624/text2vec-base-chinese (本地 CPU 推理)
- **Web 框架**：Streamlit + FastAPI
- **配置管理**：Pydantic Settings

## 📁 项目结构
```
Enterprise-RAG-System/
├── app/
│   ├── __init__.py
│   ├── main.py          # 命令行问答入口
│   ├── chain.py         # RAG 核心问答链（全局单例）
│   ├── config.py        # 全局配置（绝对路径 + 单例）
│   ├── ingest.py        # 文档处理与向量化入库
│   ├── api.py           # FastAPI REST API（文档管理/问答/健康检查）
│   ├── web.py           # Streamlit Web 界面
│   └── logger.py        # 统一日志模块
├── data/
│   ├── chroma_db/       # 向量数据库（自动生成）
│   └── raw_docs/        # 原始文档
├── tests/
│   ├── __init__.py
│   └── test_ingest.py   # 单元测试
├── logs/                # 运行日志（自动生成）
├── .env                 # 环境变量配置
├── .gitignore
├── requirements.txt     # 核心依赖（精简版）
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
编辑 `.env` 填入你的 DeepSeek API Key：
```
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL_NAME=deepseek-chat
```

### 3. 构建向量知识库
将文档放入 `data/raw_docs/`，然后运行：
```bash
python -m app.ingest
```

### 4. 启动服务

| 方式 | 命令 | 地址 |
|------|------|------|
| 命令行 | `python -m app.main` | 终端 |
| Web 界面 | `streamlit run app/web.py` | http://localhost:8501 |
| REST API | `python -m app.api` | http://localhost:8000 |

## 📡 API 文档

启动 API 后访问 http://localhost:8000/docs 查看 Swagger 文档。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/chat` | POST | 知识库问答 |
| `/documents` | GET | 列出所有文档 |
| `/documents/upload` | POST | 上传文档 |
| `/documents/{source}` | DELETE | 删除指定文档 |

## 🧪 运行测试
```bash
python -m pytest tests/ -v
```

## 🔄 系统架构
```
用户提问
  →
Query 向量化 (HuggingFace)
  →
ChromaDB 检索 Top-K
  →
Prompt 组装 (参考知识 + 限制指令)
  →
DeepSeek 大模型生成回答
  →
输出答案 + 来源追溯
```
