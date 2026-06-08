import os
from pathlib import Path
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ==========================================
    # Base
    # ==========================================
    BASE_DIR: str = str(PROJECT_ROOT)

    # ==========================================
    # DashScope (阿里云百炼) - 主力免费模型
    # ==========================================
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ==========================================
    # DeepSeek - 兜底模型
    # ==========================================
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # ==========================================
    # 模型路由表: 显示名 -> {model_name, provider}
    # ==========================================
    MODEL_ROUTES: str = '{}'  # JSON, will be parsed in get_model_options()

    # ==========================================
    # JWT 认证
    # ==========================================
    JWT_SECRET_KEY: str = "enterprise-rag-secret-change-me"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ==========================================
    # SQLite 数据库
    # ==========================================
    SQLITE_DB_PATH: str = str(PROJECT_ROOT / "data" / "enterprise.db")

    # ==========================================
    # 默认管理员
    # ==========================================
    DEFAULT_ADMIN_USER: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # ==========================================
    # 向量库
    # ==========================================
    VECTOR_DB_PATH: str = str(PROJECT_ROOT / "data" / "chroma_db")
    COLLECTION_NAME: str = "enterprise_knowledge"

    # ==========================================
    # 检索参数
    # ==========================================
    DEFAULT_TOP_K: int = 3
    MAX_TOP_K: int = 10
    RETRIEVAL_FETCH_K: int = 20  # MMR fetch 数量

    # ==========================================
    # AI 自我介绍
    # ==========================================
    SELF_INTRO: str = (
        "你好！我是**企业知识助手**，基于 RAG（检索增强生成）技术构建。\n\n"
        "我可以：\n"
        "- 📚 回答知识库中的问题，并提供引用来源\n"
        "- 💬 支持多轮对话，记住上下文\n"
        "- 🔄 支持多种大模型灵活切换\n\n"
        "请直接在下方输入你的问题，我会从知识库中检索相关内容来回答你！"
    )

    # 问候触发词
    GREETING_KEYWORDS: List[str] = ["你好", "hello", "hi", "嗨", "在吗", "你是谁", "介绍一下"]

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="allow"
    )

    def get_model_options(self) -> list:
        """解析模型路由表，返回 [(显示名, model_name, provider), ...]"""
        import json
        try:
            routes = json.loads(self.MODEL_ROUTES)
            if routes:
                return [(label, info["model"], info["provider"]) for label, info in routes.items()]
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        # 默认路由
        options = []
        if self.DASHSCOPE_API_KEY:
            options.append(("Qwen-Turbo", "qwen-turbo", "dashscope"))
            options.append(("Qwen-Plus", "qwen-plus", "dashscope"))
        if self.DEEPSEEK_API_KEY:
            options.append(("DeepSeek-V3", "deepseek-chat", "deepseek"))
        return options


settings = Settings()

