"""
Enterprise-RAG-System V2.0 - 知识库构建模块
基于 LangChain + ChromaDB 的统一文档处理与向量存储
"""

import os
import uuid
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredFileLoader
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.logger import logger


# ---- 配置常量 ----
COLLECTION_NAME = "enterprise_knowledge"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL_NAME = "shibing624/text2vec-base-chinese"


def load_document(file_path: str) -> List[Document]:
    """根据文件扩展名加载文档，支持 PDF/Word/TXT/通用格式。"""
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext in [".docx", ".doc"]:
            loader = Docx2txtLoader(file_path)
        elif ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            loader = UnstructuredFileLoader(file_path)

        return loader.load()
    except Exception as e:
        logger.error(f"加载文件失败: {file_path} | {str(e)}")
        return []


def split_documents(documents: List[Document]) -> List[Document]:
    """将长文档分割为语义文本块（chunk）。"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def get_embedding_function():
    """获取嵌入模型 —— 与 chain.py 使用相同的模型以保证向量空间一致。"""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )


def _get_existing_filenames(db) -> set:
    """从 ChromaDB 中收集已存在文档的文件名（basename），用于去重。"""
    filenames = set()
    existing_items = db.get(include=["metadatas"])
    if existing_items and "metadatas" in existing_items:
        for meta in existing_items["metadatas"]:
            if "source" in meta:
                filenames.add(os.path.basename(meta["source"]))
    return filenames


def _filter_new_chunks_by_filename(chunks: List[Document], existing_filenames: set):
    """过滤出尚未入库的文件对应的 chunk，以文件名（basename）为去重单位。
    同一文件的所有 chunk 要么全部加入，要么全部跳过。"""
    filenames_to_skip = set()
    # 第一遍：收集所有需要跳过的文件名
    for chunk in chunks:
        fname = os.path.basename(chunk.metadata.get('source', ''))
        if fname in existing_filenames:
            filenames_to_skip.add(fname)
    # 第二遍：过滤 chunk
    new_chunks = []
    skipped = 0
    for chunk in chunks:
        fname = os.path.basename(chunk.metadata.get('source', ''))
        if fname in filenames_to_skip:
            skipped += 1
            continue
        new_chunks.append(chunk)
    return new_chunks, skipped


def _generate_chunk_ids(chunks: List[Document]) -> List[str]:
    """为每个文档块生成唯一ID。"""
    return [
        f"{chunk.metadata.get('source', 'unknown')}_{chunk.metadata.get('page', 'unknown')}_{uuid.uuid4()}"
        for chunk in chunks
    ]


def add_to_chroma(chunks: List[Document]):
    """将文档块写入 ChromaDB，自动跳过已存在的文档。"""
    db = Chroma(
        persist_directory=settings.VECTOR_DB_PATH,
        embedding_function=get_embedding_function(),
        collection_name=COLLECTION_NAME
    )

    existing_filenames = _get_existing_filenames(db)
    new_chunks, skipped = _filter_new_chunks_by_filename(chunks, existing_filenames)

    if skipped > 0:
        logger.info(f"跳过 {skipped} 个已存在的文档块")

    if new_chunks:
        logger.info(f"正在写入 {len(new_chunks)} 个新文档块...")
        new_chunk_ids = _generate_chunk_ids(new_chunks)
        db.add_documents(new_chunks, ids=new_chunk_ids)
        logger.info(f"已写入 {len(new_chunks)} 个新文档块")
        return "new_chunks_added"
    else:
        logger.info("没有新文档块需要添加（所有文件已存在）")
        return "no_new_chunks"


def ingest_documents(file_paths: List[str]):
    """处理文档并构建知识库（统一入口）。"""
    if not file_paths:
        logger.warning("ingest_documents 收到空文件列表")
        return "no_documents_loaded"

    logger.info(f"开始处理 {len(file_paths)} 个文件...")

    # 加载文档。
    documents = []
    for file_path in file_paths:
        abs_path = os.path.abspath(file_path)
        logger.info(f"加载文件: {abs_path}")
        docs = load_document(file_path)
        if docs:
            documents.extend(docs)
        else:
            logger.warning(f"文件加载失败或为空: {file_path}")

    if not documents:
        logger.error("没有加载到任何文档")
        return "no_documents_loaded"

    # 分割文档。
    chunks = split_documents(documents)
    logger.info(f"分割为 {len(chunks)} 个文本块")

    # 添加到 ChromaDB
    result = add_to_chroma(chunks)
    logger.info("知识库构建完成！")
    return result
