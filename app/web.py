"""
Enterprise-RAG-System V2.0 - Web 界面
基于 Streamlit 的企业级私有知识库问答系统 (独立运行版)
"""

import streamlit as st
# Web 框架，用 Python 写网页
import ollama
# 本地大模型客户端（调用 Ollama 服务）
from chromadb import PersistentClient
# 直接操作 ChromaDB 数据库
from langchain.prompts import PromptTemplate
# 提示词模板工具
from app.ingest import process_documents
# 复用文档处理功能（上传文档时用）

# ==========================================
# 1. 核心配置 (直接内嵌，避免跨目录导入)
# ==========================================
CHROMA_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "enterprise_knowledge"
LLM_MODEL = "qwen2.5:3b"  # 本地大模型


# ==========================================
# 2. 核心功能函数 (直接内嵌)
# ==========================================
def retrieve_context(query, top_k=5):  # 增加检索数量
    """从 ChromaDB 检索相关上下文"""
    try:
        client = PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(COLLECTION_NAME)

        query_embedding = ollama.embeddings(model="nomic-embed-text", prompt=query)["embedding"]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        context_results = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                doc_content = results['documents'][0][i]
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]

                from langchain_core.documents import Document
                doc = Document(page_content=doc_content, metadata=metadata)
                context_results.append((doc, distance))

        print(f"🔍 检索到 {len(context_results)} 条相关文档")
        for doc, dist in context_results:
            print(f"  - 内容预览: {doc.page_content[:100]}... (距离: {dist:.4f})")

        return context_results
    except Exception as e:
        print(f"❌ 检索失败: {str(e)}")
        return []

def generate_answer(query, context):
    """调用本地大模型生成回答"""
    if not context or len(context.strip()) == 0:
        return "根据现有知识库无法回答该问题"

    prompt_template = PromptTemplate(
        template="""你是企业级智能助手。请严格基于以下【参考内容】回答用户问题。
如果【参考内容】中没有相关信息，请直接回答"根据现有知识库无法回答该问题"，不要自行编造。

【参考内容】：
{context}

用户问题：{query}

专业解答：""",
        input_variables=["context", "query"]
    )

    prompt = prompt_template.format(context=context, query=query)

    print(f"📤 发送给模型的 Prompt 长度: {len(prompt)} 字符")
    print(f"📤 Prompt 预览: {prompt[:500]}...")

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response["message"]["content"]
        print(f"📥 模型回答: {answer[:200]}...")
        return answer
    except Exception as e:
        print(f"❌ 调用模型失败: {str(e)}")
        return f"调用模型失败: {str(e)}"


# ==========================================
# 页面基础配置
# ==========================================
st.set_page_config(
    page_title="星际科技 · 企业知识库",  # 浏览器标签标题
    page_icon="🤖",   # 标签图标
    layout="wide",   # 宽屏布局
)

# ==========================================
# 侧边栏 - 知识库状态 & 系统配置
# ==========================================
with st.sidebar:
    st.title("⚙️ 系统状态")

    # 知识库信息
    st.subheader("📚 知识库信息")
    try:
        client = PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(COLLECTION_NAME)
        doc_count = collection.count()   # 统计知识块数量

        if doc_count == 0:
            st.warning(
                "⚠️ 知识库为空，请上传文档初始化",
                icon="⚙️"
            )
        else:
            st.metric("知识块数量", f"{doc_count} 条")  # 显示数字卡片
            all_data = collection.get(include=["metadatas"])
            sources = set()
            for meta in all_data["metadatas"]:
                if "source" in meta:
                    sources.add(meta["source"])  # 收集所有文档来源
            st.metric("文档数量", f"{len(sources)} 份")
            for source in sorted(sources):
                st.text(f"  📄 {source}")  # 列出每个文件名
    except Exception as e:
        st.error(f"⚠️ 知识库未找到")
        doc_count = 0

    st.divider()

    # 在 sidebar 中添加更严格的状态管理
    if 'upload_processing' not in st.session_state:
        st.session_state.upload_processing = False
    if 'last_uploaded_files' not in st.session_state:
        st.session_state.last_uploaded_files = []
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0

    # 文档上传区域
    st.subheader("📤 文档上传")
    uploaded_files = st.file_uploader(
        "上传企业文档 (PDF/Word/TXT)",
        type=["pdf", "docx", "doc", "txt"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}"
    )

    # 检测新上传的文件（与上次不同）
    current_file_names = [f.name for f in uploaded_files] if uploaded_files else []
    last_file_names = st.session_state.last_uploaded_files

    has_new_files = uploaded_files and not st.session_state.upload_processing and current_file_names != last_file_names

    if has_new_files:
        st.session_state.upload_processing = True
        st.session_state.last_uploaded_files = current_file_names

        with st.spinner("📄 正在处理文档..."):
            import tempfile
            import os
            import shutil

            temp_dir = tempfile.mkdtemp()
            uploaded_file_paths = []

            try:
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    uploaded_file_paths.append(file_path)

                from app.ingest import process_documents

                result = process_documents(uploaded_file_paths)

                if result == "no_new_chunks":
                    st.info("ℹ️ 文档已存在，无需重复添加")
                elif result == "new_chunks_added":
                    st.success(f"✅ 成功处理 {len(uploaded_files)} 个文档！")
                else:
                    st.success(f"✅ 处理完成！")

            except Exception as e:
                st.error(f"❌ 处理失败: {str(e)}")
            finally:
                shutil.rmtree(temp_dir)
                st.session_state.upload_processing = False
                st.session_state.uploader_key += 1
                st.rerun()

    st.divider()

    # 清空对话记录
    if st.button("🗑️ 清空对话记录", use_container_width=True):
        st.session_state.messages = []  # 清空会话状态
        st.rerun()  # 刷新页面

    st.divider()

    # 检索参数调节
    st.subheader("🔧 检索参数")
    top_k = st.slider("召回知识块数 (Top-K)", min_value=1, max_value=10, value=3, step=1)

    st.divider()
    st.caption("Enterprise-RAG-System V2.0")
    st.caption("Powered by Ollama + ChromaDB")

# ==========================================
# 主界面 - 聊天区域
# ==========================================
st.title("🤖 星际科技 · 企业知识库问答")
st.caption("基于本地大模型的企业级私有知识库，支持 PDF / Word / TXT 多格式文档")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史对话
for message in st.session_state.messages:
    with st.chat_message(message["role"]):   # role = "user" 或 "assistant"
        st.markdown(message["content"])  # 显示消息内容
        # 如果有来源信息，显示参考来源
        if "sources" in message and message["sources"]:
            with st.expander("📎 查看参考来源"):   # 可折叠区域
                for src in message["sources"]:
                    st.markdown(f"- 📄 {src}")

# 用户输入
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    # 保存到历史记录
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 回答
    with st.chat_message("assistant"):
        with st.spinner("🤔 正在检索知识库并生成回答..."):
            # 1. 检索相关上下文
            context_results = retrieve_context(prompt, top_k=top_k)

            if not context_results:
                answer = "根据现有知识库无法回答该问题"
                sources = []
            else:
                # 2. 收集来源信息
                sources = []
                for doc, score in context_results:
                    source_name = doc.metadata.get("source", "未知来源")
                    page_num = doc.metadata.get("page", None)
                    if page_num is not None:
                        source_label = f"{source_name} (第{page_num}页)"
                    else:
                        source_label = source_name
                    if source_label not in sources:
                        sources.append(f"{source_label} (相关度: {score:.4f})")

                # 3. 拼接上下文
                context_text = "\n\n".join([doc.page_content for doc, score in context_results])
                print(f"📝 拼接后的上下文长度: {len(context_text)} 字符")

                # 4. 生成回答
                answer = generate_answer(prompt, context_text)

            st.markdown(answer)

            # 5. 显示参考来源
            if sources:
                with st.expander("📎 查看参考来源"):
                    for src in sources:
                        st.markdown(f"- 📄 {src}")

    # 保存到对话历史
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
