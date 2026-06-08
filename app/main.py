"""
Enterprise-RAG-System - 命令行问答入口
"""
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chain import get_rag
from app.config import settings
from app.logger import logger


def main():
    print("=" * 50)
    print("🤖 星际科技私有知识库问答系统")
    print("=" * 50)

    db_path = settings.VECTOR_DB_PATH
    logger.info(f"知识库路径: {db_path}")

    if not os.path.exists(db_path):
        logger.error("未检测到知识库！请先运行: python -m app.ingest")
        return

    # 初始化 RAG
    logger.info("初始化 RAG 问答链...")
    rag = get_rag()

    # 自动化测试
    print("\n🧪 正在执行自动化测试...\n")
    test_cases = [
        "公司报销招待费有什么规定？",
        "年假有多少天？",
        "公司有下午茶吗？",
    ]

    for question in test_cases:
        print("-" * 40)
        print(f"🙋 提问: {question}")
        result = rag.ask(question)
        print(f"🤖 回答: {result['answer']}")
        if result['sources']:
            print(f"📋 来源: {result['sources'][0][:50]}...")
        else:
            print("📋 来源: 无匹配文档")
        print()

    # 交互式问答
    print("=" * 50)
    print("✅ 自动化测试完成！进入交互模式")
    print("💡 输入问题开始提问，输入 quit 退出")
    print("=" * 50 + "\n")

    while True:
        user_input = input("🙋 你: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 再见！")
            break
        if not user_input:
            continue

        result = rag.ask(user_input)
        print(f"\n🤖 AI: {result['answer']}\n")


if __name__ == "__main__":
    main()
