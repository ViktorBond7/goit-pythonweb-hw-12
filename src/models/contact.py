from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from sqlalchemy import Date, ForeignKey

from src.models.user import User
from src.db.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(nullable=False)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    additional_data: Mapped[str | None] = mapped_column(nullable=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="contacts")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.first_name!r}, fullname={self.last_name!r}, email={self.email!r}, phone_number={self.phone_number!r}, birthday={self.birthday!r}, additional_data={self.additional_data!r})"
