"""
Enterprise RAG System - SQLite 数据库层
管理用户表、对话表、消息表
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from passlib.context import CryptContext

from app.config import settings
from app.logger import logger

# ==========================================
# 密码加密
# ==========================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
# 数据库连接管理
# ==========================================
DB_PATH = settings.SQLITE_DB_PATH


def get_db_path() -> str:
    """确保数据库目录存在并返回路径"""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return DB_PATH


@contextmanager
def get_db():
    """获取数据库连接（上下文管理器）"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==========================================
# 表初始化
# ==========================================
def init_db():
    """创建表结构 + 默认管理员账号"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                password_hash TEXT  NOT NULL,
                role        TEXT    NOT NULL DEFAULT 'user',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                title       TEXT    NOT NULL DEFAULT '新对话',
                model_name  TEXT    NOT NULL DEFAULT 'qwen-turbo',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role            TEXT    NOT NULL CHECK(role IN ('user','assistant','system')),
                content         TEXT    NOT NULL,
                sources_json    TEXT    DEFAULT '[]',
                created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")

    # 创建默认管理员
    _ensure_default_admin()

    logger.info("数据库初始化完成")


def _ensure_default_admin():
    """确保默认管理员账号存在"""
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (settings.DEFAULT_ADMIN_USER,)
        ).fetchone()
        if not existing:
            password_hash = hash_password(settings.DEFAULT_ADMIN_PASSWORD)
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (settings.DEFAULT_ADMIN_USER, password_hash, "admin")
            )
            logger.info(f"默认管理员账号已创建: {settings.DEFAULT_ADMIN_USER}")
        else:
            logger.info(f"管理员账号已存在: {settings.DEFAULT_ADMIN_USER}")


# ==========================================
# 密码工具
# ==========================================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# 用户操作
# ==========================================
def get_user_by_username(username: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?",
            (username,)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
    return dict(row) if row else None


def create_user(username: str, password: str, role: str = "user") -> dict:
    password_hash = hash_password(password)
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            user_id = cursor.lastrowid
            return {"id": user_id, "username": username, "role": role}
        except sqlite3.IntegrityError:
            raise ValueError(f"用户名已存在: {username}")


def list_users() -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_user(user_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ==========================================
# 对话操作
# ==========================================
def create_conversation(user_id: int, title: str = "新对话", model_name: str = "qwen-turbo") -> dict:
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            "INSERT INTO conversations (user_id, title, model_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, model_name, now, now)
        )
        conv_id = cursor.lastrowid
    return {"id": conv_id, "user_id": user_id, "title": title, "model_name": model_name,
            "created_at": now, "updated_at": now}


def get_conversations(user_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT c.id, c.title, c.model_name, c.created_at, c.updated_at,
                      (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as msg_count
               FROM conversations c
               WHERE c.user_id = ?
               ORDER BY c.updated_at DESC""",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_conversation(conv_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, user_id, title, model_name, created_at, updated_at FROM conversations WHERE id = ?",
            (conv_id,)
        ).fetchone()
    return dict(row) if row else None


def update_conversation(conv_id: int, **kwargs):
    fields = []
    values = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    fields.append("updated_at = ?")
    values.append(conv_id)
    with get_db() as conn:
        conn.execute(
            f"UPDATE conversations SET {', '.join(fields)} WHERE id = ?",
            values
        )


def delete_conversation(conv_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))


# ==========================================
# 消息操作
# ==========================================
def add_message(conversation_id: int, role: str, content: str, sources_json: str = "[]") -> dict:
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            "INSERT INTO messages (conversation_id, role, content, sources_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, role, content, sources_json, now)
        )
        # 更新对话时间
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id)
        )
        msg_id = cursor.lastrowid
    return {"id": msg_id, "conversation_id": conversation_id, "role": role,
            "content": content, "sources_json": sources_json, "created_at": now}


def get_messages(conversation_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, conversation_id, role, content, sources_json, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_conversation_history(conversation_id: int, limit: int = 10) -> list:
    """获取最近 N 条消息作为对话上下文"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT role, content FROM messages
               WHERE conversation_id = ? AND role IN ('user','assistant')
               ORDER BY id DESC LIMIT ?""",
            (conversation_id, limit * 2)  # user+assistant pairs
        ).fetchall()
    # 反转回正序
    return [dict(r) for r in reversed(rows)]


def auto_title_from_content(content: str) -> str:
    """从首条消息内容自动生成对话标题"""
    # 取前20个字符，清理换行
    title = content.replace("\n", " ").strip()
    if len(title) > 20:
        title = title[:20] + "..."
    return title or "新对话"
