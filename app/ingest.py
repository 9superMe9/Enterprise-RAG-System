"""
Enterprise-RAG-System V2.0 - 知识库构建模块
基于 LangChain + ChromaDB 的文档处理与向量存储
"""

import os
import sys
import uuid
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain.chains import LLMChain

# 添加项目根目录到 Python 路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 正确的导入方式
from chromadb import PersistentClient

# 或者
import chromadb
db = chromadb.PersistentClient(path="data/chroma_db")

# 配置常量
CHROMA_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "enterprise_knowledge"
LLM_MODEL = "qwen2.5:3b"
EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_document(file_path: str) -> List[Document]:
    """根据文件类型加载文档"""
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)  # 用 PDF 阅读器
        elif ext in [".docx", ".doc"]:
            loader = Docx2txtLoader(file_path)  # 用 Word 阅读器
        elif ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")   # 用记事本
        else:
            loader = UnstructuredFileLoader(file_path)   # 万能备用

        return loader.load()    # 读取内容，返回 Document 对象列表
    except Exception as e:
        print(f"❌ 加载文件 {file_path} 失败: {str(e)}")
        return []    # 失败返回空列表，不中断程序


def split_documents(documents: List[Document]) -> List[Document]:
    """分割文档为文本块"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,   # 1000 字符
        chunk_overlap=CHUNK_OVERLAP,   # 200 字符重叠
        length_function=len,     # 用 len() 计算长度
        is_separator_regex=False,    # 不用正则表达式分隔
    )
    return text_splitter.split_documents(documents)


def get_embedding_function():
    """获取嵌入模型"""
    return OllamaEmbeddings(model=EMBEDDING_MODEL)


def add_to_chroma(chunks: List[Document]):
    """将文档块添加到 ChromaDB"""
    # 初始化 ChromaDB 客户端
    db = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=get_embedding_function(),
        collection_name=COLLECTION_NAME
    )

    # 获取现有文档的来源（去重）
    existing_sources = set()
    existing_items = db.get(include=["metadatas"])
    if existing_items and "metadatas" in existing_items:
        for meta in existing_items["metadatas"]:
            if "source" in meta:
                existing_sources.add(meta["source"])

    # 过滤掉已存在的文档
    new_chunks = []
    skipped_count = 0

    for chunk in chunks:
        source = chunk.metadata.get('source', '')

        # 如果该来源已存在，跳过
        if source in existing_sources:
            skipped_count += 1
            continue

        new_chunks.append(chunk)
        # 标记为已处理（避免同一批次重复）
        existing_sources.add(source)

    if skipped_count > 0:
        print(f"⚠️ 跳过 {skipped_count} 个已存在的文档块")

    if new_chunks:
        print(f"🆕 发现 {len(new_chunks)} 个新文档块")

        # 生成唯一ID
        new_chunk_ids = []
        for chunk in new_chunks:
            source = chunk.metadata.get('source', 'unknown')
            page = chunk.metadata.get('page', 'unknown')
            chunk_id = f"{source}_{page}_{uuid.uuid4()}"
            new_chunk_ids.append(chunk_id)

        # 添加新文档块
        db.add_documents(new_chunks, ids=new_chunk_ids)
        print("✅ 新文档块已添加到知识库")
        return "new_chunks_added"
    else:
        print("ℹ️ 没有新文档块需要添加（所有文档已存在）")
        return "no_new_chunks"

def ingest_documents(file_paths: List[str]):
    """处理文档并构建知识库"""
    print(f"📄 开始处理 {len(file_paths)} 个文档...")

    # 加载文档
    documents = []
    for file_path in file_paths:
        print(f"📖 加载文档: {file_path}")
        docs = load_document(file_path)
        if docs:
            documents.extend(docs)
        else:
            print(f"⚠️ 文档 {file_path} 加载失败或为空")

    if not documents:
        print("❌ 没有加载到任何文档")
        return "no_documents_loaded"

    # 分割文档
    chunks = split_documents(documents)
    print(f"📝 分割为 {len(chunks)} 个文本块")

    # 添加到 ChromaDB
    result = add_to_chroma(chunks)

    print("✅ 知识库构建完成！")
    return result


def process_documents(file_paths: List[str]):
    """处理上传的文档并构建知识库"""
    print(f"开始处理 {len(file_paths)} 个文档...")

    # 复用原有的 ingest 逻辑
    result = ingest_documents(file_paths)

    print("文档处理完成！")
    return result


# 导出必要的函数
# ingest_documents = ingest_documents
# process_documents = process_documents
