from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact import Contact
from src.models.user import Role, User
from src.repositories import contact_repo
from src.schemas.contact import ContactRequest


