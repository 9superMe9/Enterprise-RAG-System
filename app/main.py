import os
from app.chain import RAGChain
from app.config import settings  # 新增：导入配置

def main():
    print("=" * 50)
    print("🪐 星际科技私有知识库问答系统")
    print("=" * 50)

    # 修改：使用配置中的绝对路径，而不是相对路径
    # if not os.path.exists(settings.VECTOR_DB_PATH):
    #     print("❌ 未检测到知识库！请先在 Terminal 中运行：")
    #     print("   python -m app.ingest")
    #     return
    # 调试：先打印程序到底在找哪个路径
    db_path = settings.VECTOR_DB_PATH
    print(f"🔍 正在检查知识库路径: {db_path}")
    print(f"🔍 该路径是否存在: {os.path.exists(db_path)}")

    if not os.path.exists(db_path):
        print("❌ 未检测到知识库！请先在 Terminal 中运行：")
        print("   python -m app.ingest")
        return

    # 初始化 RAG 问答链
    rag = RAGChain()

    # 3. 自动化测试（验证系统是否正常）
    print("\n📋 正在执行自动化测试...\n")

    test_cases = [
        "公司报销招待费有什么规定？",   # 应该能回答
        "年假有多少天？",               # 应该能回答
        "公司有下午茶吗？",             # 应该拒绝回答（防幻觉测试）
    ]

    for question in test_cases:
        print("-" * 40)
        print(f"👤 提问: {question}")
        result = rag.ask(question)
        print(f"🤖 回答: {result['answer']}")
        if result['sources']:
            print(f"📄 来源: {result['sources'][0][:50]}...")
        else:
            print("📄 来源: 无匹配文档")
        print()

    # 4. 进入交互式问答模式
    print("=" * 50)
    print("✅ 自动化测试完成！进入交互模式")
    print("💡 输入问题开始提问，输入 quit 退出")
    print("=" * 50 + "\n")

    while True:
        user_input = input("👤 你: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 再见，星际旅者！")
            break
        if not user_input:
            continue

        result = rag.ask(user_input)
        print(f"\n🤖 AI: {result['answer']}\n")

if __name__ == "__main__":
    main()
