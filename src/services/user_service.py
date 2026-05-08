from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from sqlalchemy import select

from src.repositories import users
from src.services.auth import (
    Hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from src.models.user import User
from src.schemas.user import TokenModel, UserCreate
from src.db.redis_cache import get_redis


async def create_user(session: AsyncSession, user: UserCreate) -> User:
    avatar = None

    try:
        g = Gravatar(user.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)

    users_repo = users.UserRepository(session)
    db_user = await users_repo.get_user_by_email(user.email)

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {user.email} already exists.",
        )
    return await users_repo.create_user(
        user, hashed_password=Hash().get_password_hash(user.password), avatar=avatar
    )


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    users_repo = users.UserRepository(session)
    return await users_repo.get_user_by_email(email)


async def authenticate_user(
    session: AsyncSession, form_data: OAuth2PasswordRequestForm
) -> TokenModel:
    
    db_user = await session.execute(
        select(User).filter(User.email == form_data.username)
    )

    db_user = db_user.scalar_one_or_none()
    

    if not db_user or not Hash().verify_password(
        form_data.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if not db_user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not confirmed. Please check your email and confirm your email address.",
        )

    access_token = create_access_token(data={"sub": db_user.email})

    refresh_token = create_refresh_token(data={"sub": db_user.email})

    return TokenModel(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def refresh_token_service(refresh_token: str) -> TokenModel | None:

    email = verify_refresh_token(refresh_token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


async def confirmed_email(email: str, session: AsyncSession) -> None:
    users_repo = users.UserRepository(session)
    return await users_repo.confirmed_email(email)


async def update_avatar_url(email: str, url: str, session: AsyncSession):
    repository = users.UserRepository(session)
    user = await repository.update_avatar_url(email, url)
    # Invalidate cached user so next request fetches fresh data
    redis = await get_redis()
    await redis.delete(f"user:{email}")
    return user


async def reset_password(email: str, new_password: str, session: AsyncSession) -> None:
    repository = users.UserRepository(session)
    user = await repository.update_password(email, Hash().get_password_hash(new_password))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    redis = await get_redis()
    await redis.delete(f"user:{email}")
