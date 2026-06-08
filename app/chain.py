import os
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

from typing import Iterator, Optional
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from app.config import settings
from app.logger import logger


def _format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def _is_greeting(question: str) -> bool:
    """检测是否为问候语"""
    q_lower = question.strip().lower()
    for kw in settings.GREETING_KEYWORDS:
        if kw in q_lower:
            return True
    return False


def _build_prompt_with_history(history: list) -> PromptTemplate:
    """构建带对话历史的 prompt 模板"""
    history_text = ""
    if history:
        history_parts = []
        for msg in history:
            role_label = "用户" if msg["role"] == "user" else "助手"
            history_parts.append(f"{role_label}：{msg['content']}")
        history_text = "\n".join(history_parts) + "\n"

    template = """你是企业级知识库AI助手。请严格基于以下【参考知识】来回答用户问题。

你的回答必须遵循以下规则：
1. 如果【参考知识】中包含答案，请清晰、准确地提炼并回答。
2. 如果【参考知识】中没有相关信息，请坚决回答："根据现有知识库无法回答该问题，请咨询相关业务负责人。"，绝不允许编造内容。
3. 如果用户只是打招呼或自我介绍，请友好回复，无需检索知识库。
4. 回答要简洁专业，条理清晰。

【对话历史】：
{history}

【参考知识】：
{context}

用户问题：{question}

你的回答："""

    return PromptTemplate(
        template=template,
        input_variables=["context", "question", "history"]
    )


class RAGChain:
    """支持多 provider、多轮对话的 RAG 链"""

    # 提供商配置
    PROVIDER_CONFIG = {
        "dashscope": {
            "base_url": settings.DASHSCOPE_BASE_URL,
            "api_key": settings.DASHSCOPE_API_KEY,
        },
        "deepseek": {
            "base_url": settings.DEEPSEEK_BASE_URL,
            "api_key": settings.DEEPSEEK_API_KEY,
        },
    }

    def __init__(self, model_name: str = "qwen-turbo", provider: str = "dashscope"):
        self.model_name = model_name
        self.provider = provider

        # 获取 provider 配置
        pconfig = self.PROVIDER_CONFIG.get(provider)
        if not pconfig:
            raise ValueError(f"不支持的模型提供商: {provider}")

        logger.info(f"初始化 LLM: {provider}/{model_name}")

        self.llm = ChatOpenAI(
            api_key=pconfig["api_key"],
            base_url=pconfig["base_url"],
            model=model_name,
            temperature=0.1,
            streaming=True,
        )

        # 向量检索
        logger.info("加载向量存储...")
        embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = Chroma(
            persist_directory=settings.VECTOR_DB_PATH,
            embedding_function=embeddings,
            collection_name=settings.COLLECTION_NAME
        )
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": settings.DEFAULT_TOP_K}
        )
        logger.info(f"RAG 链初始化完成: {provider}/{model_name}")

    def _retrieve_and_format(self, input_dict: dict) -> dict:
        question = input_dict["question"]
        docs = self.retriever.invoke(question)
        input_dict["context"] = _format_docs(docs)
        input_dict["source_documents"] = docs
        return input_dict

    def ask(self, question: str, top_k: int = None, history: list = None) -> dict:
        """非流式问答（兼容旧接口）"""
        logger.info(f"Q: {question[:80]}...")

        if top_k and top_k != self.retriever.search_kwargs.get("k"):
            self.retriever.search_kwargs["k"] = top_k

        # 问候语检测 - 直接返回自我介绍
        if _is_greeting(question):
            logger.info("检测到问候语，返回自我介绍")
            return {"answer": settings.SELF_INTRO, "sources": []}

        docs = self.retriever.invoke(question)
        context = _format_docs(docs)

        prompt = _build_prompt_with_history(history or [])
        chain = prompt | self.llm | StrOutputParser()

        history_text = ""
        if history:
            history_parts = [f"{'用户' if m['role']=='user' else '助手'}：{m['content']}" for m in history]
            history_text = "\n".join(history_parts)

        answer = chain.invoke({
            "question": question,
            "context": context,
            "history": history_text,
        })

        sources = [doc.page_content for doc in docs]
        logger.info(f"A: {len(answer)} chars, {len(sources)} sources")
        return {"answer": answer, "sources": sources}

    def ask_stream(self, question: str, top_k: int = None, history: list = None) -> Iterator[str]:
        """流式问答，逐 token yield"""
        logger.info(f"Q (stream): {question[:80]}...")

        if top_k and top_k != self.retriever.search_kwargs.get("k"):
            self.retriever.search_kwargs["k"] = top_k

        # 问候语检测
        if _is_greeting(question):
            logger.info("问候语 -> 流式输出自我介绍")
            intro = settings.SELF_INTRO
            for char in intro:
                yield char
            return

        docs = self.retriever.invoke(question)
        context = _format_docs(docs)

        prompt = _build_prompt_with_history(history or [])
        chain = prompt | self.llm | StrOutputParser()

        history_text = ""
        if history:
            history_parts = [f"{'用户' if m['role']=='user' else '助手'}：{m['content']}" for m in history]
            history_text = "\n".join(history_parts)

        try:
            for chunk in chain.stream({
                "question": question,
                "context": context,
                "history": history_text,
            }):
                yield chunk
        except Exception as e:
            logger.error(f"流式生成错误: {e}")
            yield f"\n\n[生成中断: {str(e)}]"

    def retrieve_sources(self, question: str, top_k: int = None) -> list:
        """仅检索，不生成答案"""
        if top_k:
            self.retriever.search_kwargs["k"] = top_k
        docs = self.retriever.invoke(question)
        return [doc.page_content for doc in docs]


# ==========================================
# 全局实例缓存: (provider, model_name) -> RAGChain
# ==========================================
_rag_instances: dict = {}

def get_rag(model_name: str = "qwen-turbo", provider: str = "dashscope") -> RAGChain:
    key = (provider, model_name)
    if key not in _rag_instances:
        _rag_instances[key] = RAGChain(model_name=model_name, provider=provider)
    return _rag_instances[key]
