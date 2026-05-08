import json
from datetime import datetime, timedelta, UTC, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.models.user import User
from src.db.session import open_session
from src.db.redis_cache import get_redis
from src.config import app_config as config
from src.models.user import Role

password_hash = PasswordHash.recommended()


class Hash:

    def verify_password(self, plain_password, hashed_password) -> bool:
        return password_hash.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return password_hash.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# define a function to generate a new access token
def create_access_token(data: dict) -> str:
    issue_date_time = datetime.now(timezone.utc)
    expire_date_time = issue_date_time + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        **data,
        "iat": issue_date_time,
        "exp": expire_date_time,
        "type": "access",
    }

    res = jwt.encode(
        payload, config.settings.SECRET_KEY, algorithm=config.settings.ALGORITHM
    )

    return res


def create_refresh_token(data: dict) -> str:
    issue_date_time = datetime.now(timezone.utc)
    expire_date_time = issue_date_time + timedelta(
        days=config.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        **data,
        "iat": issue_date_time,
        "exp": expire_date_time,
        "type": "refresh",
    }
    return jwt.encode(
        payload, config.settings.SECRET_KEY, algorithm=config.settings.ALGORITHM
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(open_session),
    redis=Depends(get_redis),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None or payload.get("type") != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Try to get user from Redis cache
    cache_key = f"user:{email}"
    cached = await redis.get(cache_key)
    if cached:
       
        user_data = json.loads(cached)
        user = User(**user_data)
        return user

    # Cache miss — fetch from DB and store in cache
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
 
    if user is None:
        raise credentials_exception

    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "avatar": user.avatar,
        "confirmed": user.confirmed,
        "role": user.role.value,
    }
    await redis.set(cache_key, json.dumps(user_dict), ex=config.USER_CACHE_TTL)

    return user


def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(
        to_encode, config.settings.SECRET_KEY, algorithm=config.settings.ALGORITHM
    )
    return token


async def get_email_from_token(token: str):
    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token for email verification",
        )


def verify_refresh_token(token: str) -> Optional[str] | None:
    try:

        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
        )

        email = payload.get("sub")

        type_ = payload.get("type")

        if email is None or type_ != "refresh":
            return None
        return email
    except JWTError:
        return None


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user