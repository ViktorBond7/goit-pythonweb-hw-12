from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.contact import ContactResponse, ContactRequest, ContactUpdateRequest
from src.db.session import open_session
from src.services import contact_service
from src.models.user import User
from src.services.auth import get_current_user

router = APIRouter()


# Get all or search contacts from db
@router.get("/contacts/", response_model=list[ContactResponse])
async def get_all_or_search_contacts(
    first_name: str | None = Query(default=None),
    last_name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    session: AsyncSession = Depends(open_session),
    user: User = Depends(get_current_user),
):
    contacts = await contact_service.get_all_contacts(
        session, user, first_name, last_name, email
    )
    return [ContactResponse.model_validate(c) for c in contacts]


# Create new contact
@router.post(
    "/contacts/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED
)
async def create_contact(
    contact: ContactRequest,
    session: AsyncSession = Depends(open_session),
    user: User = Depends(get_current_user),
):
    new_contact = await contact_service.create_contact(session, contact, user)
    return ContactResponse.model_validate(new_contact)


# Get upcoming birthdays
@router.get("/contacts/birthdays/upcoming", response_model=list[ContactResponse])
async def get_upcoming_birthdays(
    session: AsyncSession = Depends(open_session),
    user: User = Depends(get_current_user),
):
    contacts = await contact_service.get_upcoming_birthdays(session, user=user)
    return [ContactResponse.model_validate(c) for c in contacts]


# Get contact by id
@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(
    contact_id: int,
    session: AsyncSession = Depends(open_session),
    user: User = Depends(get_current_user),
):
    contact = await contact_service.get_contact_by_id(session, contact_id, user)
    return ContactResponse.model_validate(contact)


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdateRequest,
    session: AsyncSession = Depends(open_session),
    user: User = Depends(get_current_user),
):
    db_contact = await contact_service.get_contact_by_id(session, contact_id, user)
    updated_contact = await contact_service.update_contact(
        session, db_contact, contact, user
    )
    return ContactResponse.model_validate(updated_contact)


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(open_session),
    user: User = Depends(get_current_user),
):
    await contact_service.delete_contact(session, contact_id, user)

    return {"message": f'Contact with id "{contact_id}" deleted successfully'}
