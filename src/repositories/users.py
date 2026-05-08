from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.user import UserCreate
from src.models.user import User


class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_user_by_email(self, email: str):
        stmt = select(User).filter(User.email == email)
        result = await self.db_session.execute(stmt)
        if result is None:
            raise Exception(f"Failed to execute query for email: {email}")
        return result.scalars().first()

    async def create_user(
        self, body: UserCreate, hashed_password: str = None, avatar: str = None
    ) -> User:
        new_user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=hashed_password,
            avatar=avatar,
        )

        self.db_session.add(new_user)
        await self.db_session.commit()
        await self.db_session.refresh(new_user)
        return new_user

    async def confirmed_email(self, email: str) -> None:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        user.confirmed = True
        await self.db_session.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def update_password(self, email: str, hashed_password: str) -> User | None:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        user.hashed_password = hashed_password
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user
