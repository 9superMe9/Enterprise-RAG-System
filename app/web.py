"""
Enterprise-RAG-System V2.1 - Web UI
Dark tech theme with model routing, file management
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os, shutil, tempfile
import streamlit as st
import chromadb
from app.config import settings
from app.chain import get_rag
from app.ingest import ingest_documents
from app.logger import logger

# ---- Page Config ----
st.set_page_config(
    page_title="StarTech | Enterprise RAG",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS ----
st.markdown("""<style>
.stApp { background: linear-gradient(135deg, #0a0a1a 0%, #0d1117 50%, #0a0a1a 100%); }
.main .block-container { padding-top: 1.5rem; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(10,15,30,0.98) 0%, rgba(13,17,23,0.99) 100%); border-right: 1px solid rgba(0,212,255,0.12); }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #00d4ff !important; font-weight: 600; }
.stMetric { background: rgba(0,212,255,0.04) !important; border: 1px solid rgba(0,212,255,0.12) !important; border-radius: 12px !important; padding: 12px 16px !important; }
.stMetric:hover { border-color: rgba(0,212,255,0.35) !important; box-shadow: 0 0 20px rgba(0,212,255,0.08); }
.stMetric label { color: #607B9E !important; font-size: 0.7rem; letter-spacing: 1px; text-transform: uppercase; }
.stMetric [data-testid="stMetricValue"] { color: #E6F1FF !important; font-size: 1.6rem; font-weight: 700; }
.stButton > button { background: linear-gradient(135deg, rgba(0,212,255,0.12), rgba(123,47,255,0.12)) !important; border: 1px solid rgba(0,212,255,0.25) !important; border-radius: 8px !important; color: #00d4ff !important; font-weight: 600 !important; transition: all 0.3s !important; }
.stButton > button:hover { background: linear-gradient(135deg, rgba(0,212,255,0.22), rgba(123,47,255,0.22)) !important; border-color: rgba(0,212,255,0.5) !important; box-shadow: 0 0 25px rgba(0,212,255,0.15) !important; }
[data-testid="stChatMessage"] { background: rgba(13,17,23,0.85) !important; border: 1px solid rgba(0,212,255,0.07) !important; border-radius: 14px !important; padding: 18px 22px !important; margin: 6px 0 !important; }
[data-testid="stChatInput"] textarea { background: rgba(13,17,23,0.95) !important; border: 1px solid rgba(0,212,255,0.2) !important; border-radius: 14px !important; color: #E6F1FF !important; }
[data-testid="stChatInput"] textarea:focus { border-color: rgba(0,212,255,0.5) !important; box-shadow: 0 0 30px rgba(0,212,255,0.08) !important; }
[data-testid="stFileUploader"] { background: rgba(0,212,255,0.02) !important; border: 1px dashed rgba(0,212,255,0.2) !important; border-radius: 12px !important; padding: 12px !important; }
div[data-baseweb="select"] > div { background: rgba(0,212,255,0.04) !important; border-color: rgba(0,212,255,0.15) !important; border-radius: 8px !important; }
[data-testid="stExpander"] { background: rgba(0,212,255,0.02) !important; border: 1px solid rgba(0,212,255,0.08) !important; border-radius: 10px !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0a0a1a; }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #00d4ff, #7b2fff); border-radius: 3px; }
hr { border-color: rgba(0,212,255,0.08) !important; }
.stSuccess, .stInfo, .stWarning, .stError { border-radius: 8px !important; }
</style>""", unsafe_allow_html=True)

# ---- Session State ----
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = settings.DEEPSEEK_MODEL_NAME
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


def get_kb_info():
    """Get knowledge base stats."""
    try:
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        collection = client.get_or_create_collection(settings.COLLECTION_NAME)
        total_chunks = collection.count()
        results = collection.get(include=["metadatas"])
        file_map = {}
        if results and results["metadatas"]:
            for meta in results["metadatas"]:
                src = meta.get("source", "unknown")
                fname = os.path.basename(src) if src != "unknown" else src
                file_map[fname] = file_map.get(fname, 0) + 1
        files = [{"name": k, "chunks": v} for k, v in sorted(file_map.items())]
        return total_chunks, files
    except Exception as e:
        logger.error(f"KB info error: {e}")
        return 0, []


# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:10px 0 20px 0;">
        <div style="font-size:2.2rem;">&#128302;</div>
        <div style="font-size:1rem; font-weight:700; color:#00d4ff; letter-spacing:2px;">STELLAR RAG</div>
        <div style="font-size:0.65rem; color:#4a5568; margin-top:4px;">ENTERPRISE KNOWLEDGE ENGINE</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ---- Model Router ----
    st.markdown("**&#127760; MODEL ROUTER**")
    model_options = settings.get_model_options()
    model_labels = [label for label, _ in model_options]
    model_map = {label: name for label, name in model_options}
    default_idx = 0
    for i, (label, name) in enumerate(model_options):
        if name == st.session_state.selected_model:
            default_idx = i
            break

    selected_label = st.selectbox(
        "Model",
        options=model_labels,
        index=default_idx,
        label_visibility="collapsed",
        key="model_selector"
    )
    new_model = model_map[selected_label]
    if new_model != st.session_state.selected_model:
        st.session_state.selected_model = new_model
        st.rerun()

    st.divider()

    # ---- Knowledge Base ----
    st.markdown("**&#128218; KNOWLEDGE BASE**")
    total_chunks, file_list = get_kb_info()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", len(file_list))
    with col2:
        st.metric("Chunks", total_chunks)

    if file_list:
        st.markdown("""<div style="color:#607B9E; font-size:0.7rem; letter-spacing:1px; margin:12px 0 6px 0;">
        INDEXED FILES</div>""", unsafe_allow_html=True)
        for f in file_list:
            st.markdown(f"""
            <div style="background:rgba(0,212,255,0.03); border:1px solid rgba(0,212,255,0.08);
            border-radius:6px; padding:6px 10px; margin:3px 0;
            display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#8892b0; font-size:0.75rem;">&#128196; {f["name"]}</span>
                <span style="background:rgba(0,212,255,0.12); color:#00d4ff; padding:1px 8px;
                border-radius:10px; font-size:0.65rem; font-weight:600;">{f["chunks"]} chunks</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No documents indexed yet.")

    st.divider()

    # ---- Upload ----
    st.markdown("**&#128228; UPLOAD**")
    uploaded_files = st.file_uploader(
        "drop",
        type=["pdf", "docx", "doc", "txt"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )

    if uploaded_files:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.caption(f"{len(uploaded_files)} file(s) selected")
        with col_b:
            if st.button("&#128640;", help="Process files", use_container_width=True, key="process_btn"):
                with st.spinner("Processing..."):
                    temp_dir = tempfile.mkdtemp()
                    file_paths = []
                    try:
                        for uf in uploaded_files:
                            fp = os.path.join(temp_dir, uf.name)
                            with open(fp, "wb") as f:
                                f.write(uf.getvalue())
                            file_paths.append(fp)
                        result = ingest_documents(file_paths)
                        if result == "new_chunks_added":
                            st.toast(f"Indexed {len(uploaded_files)} document(s)", icon="✅")
                        elif result == "no_new_chunks":
                            st.toast("Documents already exist", icon="ℹ️")
                        else:
                            st.toast("No new content added", icon="⚠️")
                        st.session_state.uploader_key += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {str(e)}")
                        logger.error(f"Upload error: {e}")
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)

    st.divider()

    # ---- Search Config ----
    st.markdown("**&#128269; RETRIEVAL**")
    top_k = st.slider("Top-K", 1, 10, settings.DEFAULT_TOP_K, 1, label_visibility="collapsed")
    st.caption(f"Retrieving top {top_k} chunks")

    st.divider()

    # ---- Actions ----
    if st.button("&#128465;&#65039; Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div style="text-align:center; color:#3a4560; font-size:0.6rem; letter-spacing:1px; padding-top:20px;">
        STELLAR RAG &middot; V2.1 &middot; SECURE
    </div>
    """, unsafe_allow_html=True)


# ============================================
# MAIN CHAT AREA
# ============================================
st.markdown("""
<div style="padding:0 0 8px 0;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="font-size:2.2rem;">&#128302;</div>
        <div>
            <div style="font-size:1.6rem; font-weight:800; background:linear-gradient(90deg, #00d4ff, #7b2fff);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">
                StarTech Enterprise RAG
            </div>
            <div style="color:#4a5568; font-size:0.75rem; letter-spacing:0.5px;">
                Private Knowledge Base &middot; Multi-Model &middot; Real-time Retrieval
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown(f"""
<span style="background:rgba(0,212,255,0.08); color:#00d4ff; padding:3px 14px;
border-radius:20px; font-size:0.7rem; font-weight:600; letter-spacing:1px;
border:1px solid rgba(0,212,255,0.15);">
ACTIVE: {st.session_state.selected_model}
</span>
""", unsafe_allow_html=True)

# ---- Chat History ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("&#128206; View Sources"):
                for i, src in enumerate(msg["sources"], 1):
                    st.caption(f"Source {i}")
                    st.text(src[:300] + ("..." if len(src) > 300 else ""))

# ---- Chat Input ----
if prompt := st.chat_input("Ask anything about your enterprise knowledge base..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("""
        <div style="display:flex; align-items:center; gap:10px; color:#607B9E;">
            <div style="width:8px; height:8px; background:#00d4ff; border-radius:50%;
            animation:pulse 1.2s infinite;"></div>
            <span style="font-size:0.85rem;">Retrieving knowledge &amp; generating response...</span>
        </div>
        <style>@keyframes pulse { 0%,100%{opacity:0.3} 50%{opacity:1} }</style>
        """, unsafe_allow_html=True)

        try:
            rag = get_rag(model_name=st.session_state.selected_model)
            result = rag.ask(prompt, top_k=top_k)
            answer = result["answer"]
            sources = [s[:200] + "..." if len(s) > 200 else s for s in result["sources"]]
            placeholder.markdown(answer)
            if sources:
                with st.expander("&#128206; View Sources"):
                    for i, src in enumerate(sources, 1):
                        st.caption(f"Source {i}")
                        st.text(src)
        except Exception as e:
            answer = f"Error: {str(e)}"
            placeholder.error(answer)
            sources = []
            logger.error(f"Chat error: {e}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
