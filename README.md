# 🪐 Enterprise-RAG-System (星际科技私有知识库)

基于 RAG (Retrieval-Augmented Generation) 架构的企业级私有知识库问答系统。解决了大模型在垂直领域幻觉严重、数据隐私不可控的问题。

## ✨ 核心亮点
- 🔒 **数据隐私**：基于本地向量库，企业数据无需上传至公有云大模型。
- 🎯 **精准拒答**：优化 Prompt，对超出知识库的问题坚决拒绝，有效降低大模型幻觉。
- ✂️ **智能切分**：基于 `RecursiveCharacterTextSplitter` 与段落语义的精准文档切分，提升检索召回率。

## 🛠️ 技术栈
- **大模型**：DeepSeek API (兼容 OpenAI SDK)
- **编排框架**：LangChain
- **向量数据库**：ChromaDB
- **Embedding 模型**：shibing624/text2vec-base-chinese (本地 CPU 推理，保障数据隐私)
- **配置管理**：Pydantic Settings

## 🏗️ 系统架构
\`\`\`
用户提问 
  ↓
Query 向量化 (BGE) 
  ↓
ChromaDB 检索 Top-K 
  ↓
Prompt 组装 (参考知识 + 限制指令) 
  ↓
DeepSeek 大模型生成回答 
  ↓
输出答案 + 来源追溯
\`\`\`

## 🚀 快速开始

1. **克隆项目并安装依赖**
\`\`\`bash
git clone https://github.com/你的用户名/Enterprise-RAG-System.git
cd Enterprise-RAG-System
pip install -r requirements.txt
\`\`\`

2. **配置环境变量**
复制 `.env.example` 为 `.env`，填入你的 DeepSeek API Key：
\`\`\`bash
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY
\`\`\`

3. **构建向量知识库**
\`\`\`bash
python -m app.ingest
\`\`\`

4. **启动问答系统**
\`\`\`bash
python -m app.main
\`\`\`

## 📂 项目结构
\`\`\`Enterprise-RAG-System/
├── app/
│   ├── __init__.py
│   ├── main.py          # 程序统一启动入口
│   ├── chain.py         # RAG 核心问答链
│   ├── config.py        # 全局配置（绝对路径/单例）
│   └── ingest.py        # 数据清洗与向量化入库
├── data/
│   └── company_knowledge.txt  # 企业私有知识源
├── .env.example         # 环境变量示例
├── .gitignore
└── README.md
\`\`\`
