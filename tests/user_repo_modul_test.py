
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.models.user import User
from src.schemas.user import UserCreate
from src.repositories.users import UserRepository

class TestUserRepository:
    def test_startup(self):
        assert True

@pytest.fixture
def mock_session():
    """create a mock AsyncSession for testing"""
    mock = AsyncMock()
    # Specify that add is a regular function (MagicMock), not an AsyncMock
    mock.add = MagicMock() 
    return mock

@pytest.fixture
def user_repo(mock_session):
    """Create a UserRepository with a mock session"""
    return UserRepository(mock_session)

@pytest.mark.asyncio
async def test_get_user_by_email_found(user_repo, mock_session):
    # Prepare data
    mock_user = User(id=1, email="test@example.com")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_session.execute.return_value = mock_result

    # Call the method
    result = await user_repo.get_user_by_email("test@example.com")

    # Checks
    assert result == mock_user
    assert result.email == "test@example.com"
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_user(user_repo, mock_session):
    # Prepare input data
    body = UserCreate(username="new_user", email="new@example.com", password="password")
    hashed_password = "hashed_pw"
    avatar = "http://avatar.url"

    # Call the method
    result = await user_repo.create_user(body, hashed_password, avatar)

    # Checks
    assert result.email == "new@example.com"
    assert result.hashed_password == hashed_password
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_confirmed_email(user_repo, mock_session):
    # Simulate an existing user
    mock_user = User(id=1, email="test@example.com", confirmed=False)
    
    # Mock the get_user_by_email method to return our mock user
    user_repo.get_user_by_email = AsyncMock(return_value=mock_user)

    # Call the method
    await user_repo.confirmed_email("test@example.com")

    # Checks
    assert mock_user.confirmed is True
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_avatar_url(user_repo, mock_session):
    mock_user = User(id=1, email="test@example.com", avatar="old_url")
    user_repo.get_user_by_email = AsyncMock(return_value=mock_user)
    
    new_url = "http://new-url.com"
    result = await user_repo.update_avatar_url("test@example.com", new_url)

    assert result.avatar == new_url
    mock_session.commit.assert_called_once()