import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 自动计算项目根目录（config.py 在 app/ 下，所以它的上一级就是根目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """全局配置类，自动读取 .env 文件"""
    # DeepSeek 配置
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # 向量库配置
    VECTOR_DB_PATH: str = str(PROJECT_ROOT / "data" / "chroma_db")

    # 关键修改：使用绝对路径指向 .env 文件，彻底避免路径找不到的问题
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8"
    )


# 实例化配置，全局单例
settings = Settings()
