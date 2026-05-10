from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.contact import Contact
from src.models.user import User


async def get_all_contacts(
    session: AsyncSession,
    user: User,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    """
    Get all contacts for a user, with optional filtering by first name, last name, and email.

    args:
        session (AsyncSession): The database session.
        user (User): The user whose contacts are being retrieved.
        first_name (str, optional): Filter by first name. Defaults to None.
        last_name (str, optional): Filter by last name. Defaults to None.
        email (str, optional): Filter by email. Defaults to None.

    returns:
        list[Contact]: A list of contacts or an empty list if no contacts match the filters.
    """
    stmt = select(Contact).filter(Contact.user_id == user.id)
    

    if first_name:
        stmt = stmt.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        stmt = stmt.filter(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        stmt = stmt.filter(Contact.email.ilike(f"%{email}%"))

    result = await session.execute(stmt)
    contacts = result.scalars().all()
    return contacts


async def create_contact(
    session: AsyncSession, contact: Contact, user: User
) -> Contact:
    """
    Create a new contact for a user.

    args:
        session (AsyncSession): The database session.
        contact (Contact): The contact data to create.
        user (User): The user for whom the contact is being created.
    
    returns:
        Contact: The newly created contact object.
    """
    new_contact = Contact(**contact.model_dump(), user_id=user.id)
    session.add(new_contact)
    await session.commit()
    await session.refresh(new_contact)
    return new_contact


async def get_contact_by_id(
    session: AsyncSession, contact_id: int, user: User
) -> Contact | None:
    """
    Get a contact by its ID for a specific user.
    
    args:
        session (AsyncSession): The database session.
        contact_id (int): The ID of the contact to retrieve.
        user (User): The user whose contact is being retrieved.
    
    returns:
        Contact: The contact object if found, otherwise None.
    """
    stmt = select(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_contact_by_email(
    session: AsyncSession, email: str, user: User
) -> Contact | None:
    """
    Get a contact by its email for a specific user.
    
    args:
        session (AsyncSession): The database session.
        email (str): The email of the contact to retrieve.
        user (User): The user whose contact is being retrieved.
    
    returns:
        Contact: The contact object if found, otherwise None.
    """
    stmt = select(Contact).filter(Contact.email == email, Contact.user_id == user.id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def update_contact(
    session: AsyncSession, db_contact: Contact, user: User
) -> Contact:
    """
    Update a contact for a specific user.
    
    args:
        session (AsyncSession): The database session.
        db_contact (Contact): The contact object to update.
        user (User): The user whose contact is being updated.
    
    returns:
        Contact: The updated contact object if the update is successful, otherwise None.
    """
    if db_contact.user_id != user.id:
        return None
    session.add(db_contact)
    await session.commit()
    await session.refresh(db_contact)
    return db_contact


async def delete_contact(session: AsyncSession, db_contact_id: int, user: User) -> None:
    """
    Delete a contact by its ID for a specific user.
    
    args:
        session (AsyncSession): The database session.
        db_contact_id (int): The ID of the contact to delete.
        user (User): The user whose contact is being deleted.

    returns:
        None: This function does not return anything. It deletes the contact from the database if it exists and belongs to the user.
    """
    db_contact = await get_contact_by_id(session, db_contact_id, user)
    if db_contact and db_contact.user_id == user.id:
        await session.delete(db_contact)
        await session.commit()
