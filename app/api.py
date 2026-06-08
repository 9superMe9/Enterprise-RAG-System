"""
Enterprise RAG System - REST API v3.0
Full-featured: auth, conversations, streaming chat, knowledge base, user admin
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import json
import shutil
import tempfile
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.chain import get_rag
from app.ingest import ingest_documents
from app.logger import logger
from app.database import (
    init_db, get_user_by_username, get_user_by_id, create_user as db_create_user,
    list_users as db_list_users, delete_user as db_delete_user,
    create_conversation, get_conversations, get_conversation,
    update_conversation, delete_conversation,
    add_message, get_messages, get_conversation_history,
    auto_title_from_content,
)
from app.auth import (
    create_access_token, authenticate_user, register_user,
    get_current_user, get_current_admin,
)

# ==========================================
# 应用初始化
# ==========================================
app = FastAPI(
    title="Enterprise RAG System",
    description="企业级私有知识库问答系统 API",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()
    logger.info("API 服务启动完成")


# ==========================================
# 数据模型
# ==========================================
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
    model_name: str = Field(default="qwen-turbo")
    top_k: int = Field(default=3, ge=1, le=10)
    stream: bool = Field(default=True)

class ConversationCreate(BaseModel):
    title: str = Field(default="新对话")
    model_name: str = Field(default="qwen-turbo")

class ConversationUpdate(BaseModel):
    title: Optional[str] = None


# ==========================================
# 异常处理
# ==========================================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未处理异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"}
    )


# ==========================================
# 健康检查
# ==========================================
@app.get("/api/health")
async def health_check():
    import chromadb
    try:
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        collection = client.get_or_create_collection(settings.COLLECTION_NAME)
        chunk_count = collection.count()
    except Exception as e:
        chunk_count = -1
    return {
        "status": "healthy" if chunk_count >= 0 else "degraded",
        "version": "3.0.0",
        "chunk_count": chunk_count,
        "timestamp": datetime.now().isoformat()
    }


# ==========================================
# 认证端点
# ==========================================
@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(data={"sub": str(user["id"]), "username": user["username"]})
    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "role": user["role"]}
    }


@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    try:
        user = register_user(req.username, req.password)
        return {"message": "注册成功", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "username": current_user["username"], "role": current_user["role"]}


# ==========================================
# 模型列表
# ==========================================
@app.get("/api/models")
async def list_models(current_user: dict = Depends(get_current_user)):
    options = settings.get_model_options()
    return {
        "models": [
            {"label": label, "model_name": model, "provider": provider}
            for label, model, provider in options
        ]
    }


# ==========================================
# 对话管理
# ==========================================
@app.get("/api/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    convs = get_conversations(current_user["id"])
    return {"conversations": convs}


@app.post("/api/conversations")
async def new_conversation(req: ConversationCreate, current_user: dict = Depends(get_current_user)):
    conv = create_conversation(user_id=current_user["id"], title=req.title, model_name=req.model_name)
    return conv


@app.get("/api/conversations/{conv_id}")
async def get_conv_detail(conv_id: int, current_user: dict = Depends(get_current_user)):
    conv = get_conversation(conv_id)
    if not conv or conv["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="对话不存在")
    messages = get_messages(conv_id)
    return {"conversation": conv, "messages": messages}


@app.put("/api/conversations/{conv_id}")
async def update_conv(conv_id: int, req: ConversationUpdate, current_user: dict = Depends(get_current_user)):
    conv = get_conversation(conv_id)
    if not conv or conv["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="对话不存在")
    if req.title:
        update_conversation(conv_id, title=req.title)
    return {"message": "更新成功"}


@app.delete("/api/conversations/{conv_id}")
async def delete_conv(conv_id: int, current_user: dict = Depends(get_current_user)):
    conv = get_conversation(conv_id)
    if not conv or conv["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="对话不存在")
    delete_conversation(conv_id)
    return {"message": "删除成功"}


# ==========================================
# 聊天端点
# ==========================================
def _get_provider_for_model(model_name: str) -> str:
    options = settings.get_model_options()
    for label, model, provider in options:
        if model == model_name:
            return provider
    if "qwen" in model_name:
        return "dashscope"
    return "deepseek"


@app.post("/api/chat")
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    logger.info(f"[Chat] user={current_user['username']} model={req.model_name} q={req.question[:50]}...")

    conv_id = req.conversation_id
    if not conv_id:
        conv = create_conversation(
            user_id=current_user["id"],
            title=auto_title_from_content(req.question),
            model_name=req.model_name
        )
        conv_id = conv["id"]

    conv = get_conversation(conv_id)
    if not conv or conv["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="对话不存在")

    add_message(conv_id, "user", req.question)
    history = get_conversation_history(conv_id, limit=5)

    provider = _get_provider_for_model(req.model_name)
    rag = get_rag(model_name=req.model_name, provider=provider)

    sources = rag.retrieve_sources(req.question, req.top_k)
    sources = [s[:300] for s in sources]

    if req.stream:
        async def generate_sse():
            full_answer = ""
            try:
                for token in rag.ask_stream(req.question, req.top_k, history):
                    full_answer += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"SSE error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            finally:
                if full_answer:
                    add_message(conv_id, "assistant", full_answer, json.dumps(sources, ensure_ascii=False))
                yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'sources': sources}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
        )
    else:
        result = rag.ask(req.question, req.top_k, history)
        add_message(conv_id, "assistant", result["answer"], json.dumps(sources, ensure_ascii=False))
        return {"answer": result["answer"], "sources": sources, "conversation_id": conv_id}


# ==========================================
# 知识库管理
# ==========================================
@app.get("/api/documents")
async def list_documents(current_user: dict = Depends(get_current_user)):
    import chromadb
    try:
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        collection = client.get_or_create_collection(settings.COLLECTION_NAME)
        total = collection.count()
        results = collection.get(include=["metadatas"])
        source_map = {}
        if results and results["metadatas"]:
            for meta in results["metadatas"]:
                src = meta.get("source", "unknown")
                fname = os.path.basename(src) if src != "unknown" else src
                source_map[fname] = source_map.get(fname, 0) + 1
        docs = [{"name": k, "chunk_count": v, "source": k} for k, v in sorted(source_map.items())]
        return {"total_documents": len(docs), "total_chunks": total, "documents": docs}
    except Exception as e:
        logger.error(f"列出文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")
    allowed_exts = {".pdf", ".docx", ".doc", ".txt"}
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    try:
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed_exts:
                raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")
            file_path = os.path.join(temp_dir, file.filename)
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            file_paths.append(file_path)
        logger.info(f"用户 {current_user['username']} 上传了 {len(files)} 个文件")
        result = ingest_documents(file_paths)
        return {"status": "ok", "result": result, "file_count": len(files), "filenames": [f.filename for f in files]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.delete("/api/documents/{filename:path}")
async def delete_document(filename: str, current_user: dict = Depends(get_current_user)):
    import chromadb
    try:
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        collection = client.get_or_create_collection(settings.COLLECTION_NAME)
        results = collection.get(include=["metadatas"])
        if not results or not results["ids"]:
            raise HTTPException(status_code=404, detail="知识库为空")
        ids_to_delete = []
        for i, meta in enumerate(results["metadatas"]):
            src = meta.get("source", "")
            if os.path.basename(src) == filename or src == filename:
                ids_to_delete.append(results["ids"][i])
        if not ids_to_delete:
            raise HTTPException(status_code=404, detail=f"未找到文档: {filename}")
        collection.delete(ids=ids_to_delete)
        logger.info(f"用户 {current_user['username']} 删除了文档 {filename} ({len(ids_to_delete)} chunks)")
        return {"status": "ok", "deleted_chunks": len(ids_to_delete), "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 首页推荐问题 - 从知识库内容动态生成
# ==========================================
@app.get("/api/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    try:
        import chromadb
        from langchain_openai import ChatOpenAI
        from langchain_core.output_parsers import StrOutputParser

        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        collection = client.get_or_create_collection(settings.COLLECTION_NAME)

        total = collection.count()
        if total == 0:
            return {"questions": []}

        # 从知识库随机采样最多 10 个 chunk 的文本内容
        sample_size = min(10, total)
        results = collection.get(
            include=["documents"],
            limit=sample_size,
        )

        sample_texts = []
        if results and results["documents"]:
            sample_texts = results["documents"]

        if not sample_texts:
            return {"questions": []}

        # 拼接样本（截断避免 token 过多）
        context = "\n\n".join(text[:300] for text in sample_texts)

        # 使用默认 LLM（qwen-turbo / dashscope）生成推荐问题
        llm = ChatOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            model="qwen-turbo",
            temperature=0.7,
        )

        prompt_text = f"""请根据以下知识库内容片段，生成3个简短、自然的问题（每人会向AI助手提出的典型问题）。
要求：
- 每个问题不超过20个字
- 问题应该覆盖不同方面的内容
- 只输出问题，每行一个，不要编号，不要任何其他文字

【知识库内容片段】：
{context}

请输出3个问题："""

        answer = llm.invoke(prompt_text)
        questions = [q.strip() for q in answer.content.strip().split("\n") if q.strip()]
        questions = questions[:3]  # 最多3个

        logger.info(f"为用户 {current_user['username']} 生成了 {len(questions)} 个推荐问题")
        return {"questions": questions}

    except Exception as e:
        logger.error(f"生成推荐问题失败: {e}")
        return {"questions": []}


# ==========================================
# 用户管理（admin）
# ==========================================
@app.get("/api/admin/users")
async def admin_list_users(current_user: dict = Depends(get_current_admin)):
    users = db_list_users()
    return {"users": users}


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, current_user: dict = Depends(get_current_admin)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    target = get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    db_delete_user(user_id)
    logger.info(f"管理员 {current_user['username']} 删除了用户 {target['username']}")
    return {"message": f"已删除用户: {target['username']}"}


# ==========================================
# SPA 静态文件 - 必须在所有 API 路由之后注册
# ==========================================
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if STATIC_DIR.exists():
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str = ""):
        """SPA fallback - serve index.html for all non-API routes"""
        from fastapi.responses import FileResponse
        # Skip API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = STATIC_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")


# ==========================================
# 启动入口
# ==========================================
if __name__ == "__main__":
    import uvicorn
    logger.info("启动 Enterprise RAG System API v3.0")
    uvicorn.run(app, host="0.0.0.0", port=8000)

