# 🚀 Enterprise-RAG-System —— 企业级私有知识库问答系统

基于 RAG（检索增强生成）架构的企业级私有知识库智能问答系统。文档不出内网，数据安全可控。

---

## ✨ 核心亮点

- 🔒 **数据隐私**：基于本地向量库，企业数据无需上传公有云
- 🎯 **精准拒答**：优化 Prompt，超出知识库的问题坚决拒答，有效降低大模型幻觉
- ✂️ **智能分块**：基于 `RecursiveCharacterTextSplitter` 的段落语义级精准文档切割
- 🔄 **多模型支持**：DashScope (Qwen-Turbo/Plus) + DeepSeek-V3 动态切换，无需重启
- 💬 **多轮对话**：支持会话上下文记忆，历史对话可管理
- 👥 **用户体系**：JWT 认证 + 管理员/普通用户角色，支持用户管理
- 🖥️ **现代前端**：Vue 3 + TypeScript + Element Plus SPA，清爽科技风 UI

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 大模型 | 阿里云百炼 DashScope (Qwen-Turbo/Qwen-Plus) / DeepSeek-V3 |
| 编排框架 | LangChain |
| 向量数据库 | ChromaDB（本地持久化） |
| Embedding | shibing624/text2vec-base-chinese（本地 CPU 推理） |
| 后端框架 | FastAPI + Pydantic Settings |
| 数据库 | SQLite（用户、对话、消息） |
| 前端 | Vue 3 + TypeScript + Element Plus + Vite |
| 认证 | JWT (python-jose) |

---

## 📁 项目结构

```
Enterprise-RAG-System/
├── app/
│   ├── api.py           # FastAPI REST API（对话/文档/用户/推荐问题）
│   ├── auth.py          # JWT 认证 + 密码哈希
│   ├── chain.py         # RAG 核心问答链（多 provider 动态切换）
│   ├── config.py        # 全局配置（Settings 单例）
│   ├── database.py      # SQLite ORM（用户/对话/消息 CRUD）
│   ├── ingest.py        # 文档加载 → 分块 → 向量化入库
│   ├── logger.py        # 统一日志模块
│   └── main.py          # 命令行问答入口
├── frontend/
│   └── src/
│       ├── api/         # Axios 封装（auth/chat/knowledge）
│       ├── components/  # Vue 组件（布局/聊天/知识库）
│       ├── stores/      # Pinia 状态管理（auth/chat/knowledge）
│       ├── views/       # 页面（登录/聊天/知识库管理/用户管理）
│       └── router/      # Vue Router 路由配置
├── tests/
│   └── test_ingest.py   # 单元测试
├── data/                # 运行时数据（自动生成，不提交）
├── .env                 # 环境变量配置（不提交）
├── .gitignore
├── requirements.txt
├── DEVLOG.md            # 开发日志
└── README.md
```

---

## 🚀 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env`（至少配置一个模型 API Key）：

```env
# 阿里云百炼（推荐，Qwen-Turbo 免费额度）
DASHSCOPE_API_KEY=sk-your-key-here

# DeepSeek（兜底）
DEEPSEEK_API_KEY=sk-your-key-here

# JWT 密钥（生产环境务必修改）
JWT_SECRET_KEY=your-random-secret-key
```

### 3. 安装前端依赖 & 构建

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. 启动服务

```bash
python -m app.api
```

访问 http://localhost:8000 ，默认管理员账号 `admin` / `admin123`。

---

## 📡 API 端点

启动后访问 http://localhost:8000/docs 查看 Swagger 交互文档。

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/health` | GET | 健康检查 | 无需 |
| `/api/auth/login` | POST | 用户登录 | 无需 |
| `/api/auth/register` | POST | 用户注册 | 无需 |
| `/api/auth/me` | GET | 当前用户信息 | Bearer Token |
| `/api/models` | GET | 可用模型列表 | Bearer Token |
| `/api/suggestions` | GET | 首页推荐问题（LLM 动态生成） | Bearer Token |
| `/api/chat` | POST | 流式/非流式问答 | Bearer Token |
| `/api/conversations` | GET/POST | 对话列表/新建 | Bearer Token |
| `/api/conversations/{id}` | GET/PUT/DELETE | 对话详情/更新/删除 | Bearer Token |
| `/api/documents` | GET | 知识库文档列表 | Bearer Token |
| `/api/documents/upload` | POST | 上传文档入库 | Bearer Token |
| `/api/documents/{filename}` | DELETE | 删除指定文档 | Bearer Token |
| `/api/admin/users` | GET/DELETE | 用户管理（管理员） | Bearer Token |

---

## 🧪 运行测试

```bash
python -m pytest tests/ -v
```

---

## 🏗️ 系统架构

```
用户提问
   ↓
Query 向量化 (HuggingFace Embedding)
   ↓
ChromaDB 检索 Top-K 相关文档块
   ↓
Prompt 组装（参考知识 + 历史对话 + 限制指令）
   ↓
LLM 生成回答（DashScope / DeepSeek）
   ↓
流式输出答案 + 引用来源
```

---

## 📝 开发日志

详见 [DEVLOG.md](./DEVLOG.md)
