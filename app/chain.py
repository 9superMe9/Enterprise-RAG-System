import os
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"  # 必须在import chromadb之前设置

from langchain_openai import ChatOpenAI
# LangChain 的大模型接口（兼容 OpenAI API 格式的服务）

from langchain_chroma import Chroma
# 向量数据库接口

from langchain_community.embeddings import HuggingFaceEmbeddings
# 本地向量模型（把文字转成数字数组）

from langchain.chains import RetrievalQA
# RAG 的核心组件：检索 + 问答的组合链

from langchain.prompts import PromptTemplate
# 提示词模板（给 AI 的指令框架）

from app.config import settings
# 统一配置管理（API 密钥、路径等）

class RAGChain:
    """RAG 问答链管理类"""

    def __init__(self):
        # 1. 初始化大模型 (使用 DeepSeek)
        self.llm = ChatOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,   # 从 .env 读取密钥
            base_url=settings.DEEPSEEK_BASE_URL,   # DeepSeek 的 API 地址
            model=settings.DEEPSEEK_MODEL_NAME,   # 模型名称（deepseek-chat）
            temperature=0.1  # 企业知识库温度要低，严禁胡编乱造
        )

        # 2. 加载本地向量库
        print("-> 正在加载本地向量库...")
        embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",   # 中文向量模型
            model_kwargs={'device': 'cpu'}   # 用 CPU 运行
        )
        self.vectorstore = Chroma(
            persist_directory=settings.VECTOR_DB_PATH,    # 数据库路径
            embedding_function=embeddings    # 向量转换工具
        )

        # 3. 定义企业级 Prompt (核心防幻觉机制)
        prompt_template = """你是星际科技的内部AI助手。请严格基于以下【参考知识】来回答用户问题。
你的回答必须遵循以下规则：
1. 如果【参考知识】中包含答案，请清晰、准确地提炼并回答。
2. 如果【参考知识】中没有相关信息，请坚决回答："根据现有知识库无法回答该问题，请咨询人工HR。"，绝不允许编造内容。

【参考知识】：
{context}

用户问题：{question}

你的回答："""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]  # 这两个占位符会被替换
        )

        # 4. 构建 RetrievalQA 链
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,    # 用哪个大模型
            chain_type="stuff",   # 拼接方式
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 2}),  # 检索最相关的2个块
            return_source_documents=True,  # 返回数据来源，方便溯源
            chain_type_kwargs={"prompt": prompt}  # 传入自定义 Prompt
        )
        print("✅ RAG问答链初始化完成！")

    def ask(self, question: str) -> dict:
        """执行问答"""
        result = self.qa_chain.invoke({"query": question})
        return {
            "answer": result.get("result", "未获取到回答"),
            "sources": [doc.page_content for doc in result.get("source_documents", [])]
        }
