from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Enum, String
import enum

from src.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.contact import Contact

class Role(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[str] = mapped_column(String, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)

    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )
   

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r})"



   