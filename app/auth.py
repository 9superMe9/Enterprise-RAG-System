"""
Enterprise RAG System - JWT 认证模块
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.database import get_user_by_id, get_user_by_username, verify_password, create_user
from app.logger import logger


# ==========================================
# JWT Token 工具
# ==========================================
security = HTTPBearer()


def create_access_token(data: dict, expires_minutes: int = None) -> str:
    """创建 JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Optional[dict]:
    """解析 JWT token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ==========================================
# 依赖注入：获取当前用户
# ==========================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """从 Bearer Token 中解析当前用户"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌，请重新登录",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌不完整",
        )

    user = get_user_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return user


async def get_current_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """要求当前用户具有 admin 角色"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


# ==========================================
# 认证业务逻辑
# ==========================================
def authenticate_user(username: str, password: str) -> Optional[dict]:
    """验证用户名和密码，返回用户信息或 None"""
    user = get_user_by_username(username)
    if not user:
        logger.warning(f"登录失败：用户不存在 - {username}")
        return None
    if not verify_password(password, user["password_hash"]):
        logger.warning(f"登录失败：密码错误 - {username}")
        return None
    logger.info(f"用户登录成功: {username}")
    return user


def register_user(username: str, password: str, role: str = "user") -> dict:
    """注册新用户"""
    if len(username) < 3:
        raise ValueError("用户名至少3个字符")
    if len(password) < 6:
        raise ValueError("密码至少6个字符")
    logger.info(f"新用户注册: {username}")
    return create_user(username, password, role)
