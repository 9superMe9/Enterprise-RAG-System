import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings
from app.config import settings, PROJECT_ROOT



def ingest_data(file_path: str):
    """读取文档、分块、向量化并存入本地数据库"""
    print(f"-> 开始加载文档: {file_path}")

    # 1. 加载文档
    loader = TextLoader(file_path, encoding='utf-8')
    docs = loader.load()

    # 2. 切分文档 (chunk_size调小，让每个知识块更精准)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,  # 从200改为100
        chunk_overlap=20,  # 从50改为20
        length_function=len,
        separators=["\n\n", "\n", "。", "，", " "]  # 新增：优先按空行切分
    )

    splits = text_splitter.split_documents(docs)
    print(f"-> 文档切分完成，共生成 {len(splits)} 个知识块。")

    # 3. 初始化本地 Embedding 模型 (完全离线，保护隐私)
    # 首次运行会自动从HuggingFace下载模型，需稍等片刻
    print("-> 正在加载本地Embedding模型 (首次运行需下载)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="shibing624/text2vec-base-chinese",
        model_kwargs={'device': 'cpu'}  # 确保在没有GPU的机器上也能跑
    )

    # 4. 存入 Chroma 向量数据库
    print("-> 正在进行向量化并持久化存储...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=settings.VECTOR_DB_PATH
    )
    print(f"✅ 知识库构建完成！保存路径: {settings.VECTOR_DB_PATH}")


if __name__ == "__main__":
    # 使用配置中的路径，而不是硬编码相对路径
    import os
    from app.config import settings

    data_dir = os.path.join(str(PROJECT_ROOT), "data")
    data_file = os.path.join(data_dir, "company_knowledge.txt")

    if os.path.exists(data_file):
        ingest_data(data_file)
    else:
        print(f"❌ 找不到数据文件: {data_file}")