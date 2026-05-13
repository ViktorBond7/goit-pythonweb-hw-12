import pytest
from unittest.mock import AsyncMock, MagicMock
from src.repositories import contact_repo 
from src.models import Contact, User


@pytest.fixture
def mock_session():
    mock = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def mock_user():
    return User(id=1, email="owner@test.com")


@pytest.mark.asyncio
async def test_get_all_contacts(mock_session, mock_user):
    # prepare mock data
    mock_contacts = [Contact(id=1, first_name="John"), Contact(id=2, first_name="Jane")]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_contacts
    mock_session.execute.return_value = mock_result

    # test with no filters
    result = await contact_repo.get_all_contacts(session=mock_session, user=mock_user)

    assert len(result) == 2
    assert result[0].first_name == "John"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_contact(mock_session, mock_user):
    # data for creating a contact
    contact_data = MagicMock()
    contact_data.model_dump.return_value = {
        "first_name": "Viktor",
        "last_name": "B",
        "email": "v@test.com",
    }

    result = await contact_repo.create_contact(
        session=mock_session, contact=contact_data, user=mock_user
    )

    assert result.first_name == "Viktor"
    assert result.user_id == mock_user.id
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_contact_by_id_found(mock_session, mock_user):
    mock_contact = Contact(id=10, user_id=mock_user.id)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    result = await contact_repo.get_contact_by_id(
        session=mock_session, contact_id=10, user=mock_user
    )

    assert result.id == 10
    assert result.user_id == mock_user.id


@pytest.mark.asyncio
async def test_update_contact_success(mock_session, mock_user):
    db_contact = Contact(id=1, user_id=mock_user.id, first_name="Old Name")

    # update data
    result = await contact_repo.update_contact(
        session=mock_session, db_contact=db_contact, user=mock_user
    )

    assert result == db_contact
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact_wrong_user(mock_session, mock_user):
    # contact belongs to another user
    db_contact = Contact(id=1, user_id=99)

    result = await contact_repo.update_contact(
        session=mock_session, db_contact=db_contact, user=mock_user
    )

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_contact_found(mock_session, mock_user, monkeypatch):
    mock_contact = Contact(id=1, user_id=mock_user.id)
    # mock the get_contact_by_id to return our contact
    monkeypatch.setattr(
        contact_repo, "get_contact_by_id", AsyncMock(return_value=mock_contact)
    )

    await contact_repo.delete_contact(
        session=mock_session, db_contact_id=1, user=mock_user
    )

    mock_session.delete.assert_called_once_with(mock_contact)
    mock_session.commit.assert_called_once()
