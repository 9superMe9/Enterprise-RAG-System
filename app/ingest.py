import os
from typing import List
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import settings

# 支持的文件扩展名与对应的 Loader 映射
LOADERS = {
    ".txt": TextLoader,
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader
}


def load_documents(source_dir: str) -> List:
    """读取源目录下的所有支持格式的文档"""
    documents = []
    for filename in os.listdir(source_dir):
        file_ext = os.path.splitext(filename)[1].lower()  # 获取后缀名并转小写

        if file_ext in LOADERS:
            file_path = os.path.join(source_dir, filename)
            print(f"📄 正在解析文件: {filename}")

            try:
                loader_class = LOADERS[file_ext]
                # 如果是 TXT 文件，强制使用 UTF-8 编码，防止 Windows 下中文乱码
                if file_ext == ".txt":
                    loader = loader_class(file_path, encoding="utf-8")
                else:
                    loader = loader_class(file_path)

                docs = loader.load()

                # 给每个文档的元数据加上文件名，方便后续溯源
                for doc in docs:
                    doc.metadata["source"] = filename
                    # 移除 PDF 的 page 等元数据噪声，避免干扰向量检索
                    doc.metadata.pop("page", None)
                    # print(f"   内容预览: {doc.page_content[:100]}")  # 临时加这行看看

                documents.extend(docs)
            except Exception as e:
                print(f"⚠️ 解析文件 {filename} 失败: {e}")

    return documents


def main():
    print("🚀 开始构建星际科技私有知识库...")

    source_dir = os.path.join(settings.BASE_DIR, "data", "raw_docs")

    if not os.path.exists(source_dir):
        print(f"❌ 找不到原始文档目录: {source_dir}")
        return

    # 1. 加载多格式文档
    documents = load_documents(source_dir)
    if not documents:
        print("❌ 未找到任何可解析的文档！")
        return

    print(f"✅ 文档读取完成，共加载 {len(documents)} 个页段。")

    # 2. 切分文档
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", "。", "，", " "]
    )
    split_docs = text_splitter.split_documents(documents)
    print(f"✂️ 文档切分完成，共生成 {len(split_docs)} 个知识块。")

    # 3. 初始化 Embedding 模型
    print("⏳ 正在加载本地 Embedding 模型 (首次运行需下载，请稍候)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="shibing624/text2vec-base-chinese",
        model_kwargs={'device': 'cpu'}
    )

    # 4. 向量化并存入 ChromaDB
    print("⏳ 正在计算向量并构建数据库（耗时较长，请耐心等待）...")
    db = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=settings.VECTOR_DB_PATH
    )

    print(f"✅ 知识库构建完成！共存储 {db._collection.count()} 条向量数据。")


if __name__ == "__main__":
    main()
