from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import BackgroundTasks
from sqlalchemy import select
from starlette.requests import Request


from src.models import User
from src.models.user import Role
from src.api import user_api
from src.services.auth import create_email_token
from tests.conftest import TestingSessionLocal

from conftest import test_user

user_data = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.user_api.send_email", mock_send_email)
    response = client.post("/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.user_api.send_email", mock_send_email)
    response = client.post("/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == f"User with email {user_data['email']} already exists."


def test_not_confirmed_login(client):
    response = client.post(
        "/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert (
        data["detail"]
        == "Email not confirmed. Please check your email and confirm your email address."
    )


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_wrong_password_login(client):
    response = client.post(
        "/login", data={"username": user_data.get("email"), "password": "password"}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email or password"


def test_wrong_username_login(client):
    response = client.post(
        "/login", data={"username": "username", "password": user_data.get("password")}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email or password"


def test_validation_error_login(client):
    response = client.post("/login", data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


def test_confirm_email_user_not_found(client):
    token = create_email_token({"sub": "missing-user@example.com"})

    response = client.get(f"/confirmed_email/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Verification error"


@pytest.mark.asyncio
async def test_confirm_email(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == test_user["email"])
        )
        current_user = current_user.scalar_one_or_none()
        assert current_user is not None
        current_user.confirmed = False
        await session.commit()

    token = create_email_token({"sub": test_user["email"]})

    response = client.get(f"/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Email has been confirmed."


@pytest.mark.asyncio
async def test_confirm_email_already_confirmed(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == test_user["email"])
        )
        current_user = current_user.scalar_one_or_none()
        assert current_user is not None
        current_user.confirmed = True
        await session.commit()

    token = create_email_token({"sub": test_user["email"]})

    response = client.get(f"/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Email is already confirmed."


def test_get_me(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "avatar" in data


@patch("src.api.user_api.UploadFileService.upload_file")
def test_update_avatar_user(mock_upload_file, client, get_token):
    # mock the upload_file method to return a fake URL

    fake_url = "<http://example.com/avatar.jpg>"
    mock_upload_file.return_value = fake_url

    # token for authentication
    headers = {"Authorization": f"Bearer {get_token}"}

    # fake file data to upload
    file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

    # send PATCH request
    response = client.patch("/avatar", headers=headers, files=file_data)

    # Check that the request was successful
    assert response.status_code == 200, response.text

    # Check the response data
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert data["avatar"] == fake_url

    # Check that the upload_file function was called with an UploadFile object
    mock_upload_file.assert_called_once()


def test_request_password_reset(client):

    response = client.post(
        "/request_password_reset", json={"email": test_user["email"]}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert (
        data["message"]
        == "If the account exists, password reset instructions were sent."
    )


def test_reset_password(client, monkeypatch):

    async def fake_get_email_from_reset_token(token):
        return test_user["email"]

    monkeypatch.setattr(
        "src.api.user_api.get_email_from_reset_token", fake_get_email_from_reset_token
    )

    response = client.post(
        "/reset_password",
        json={"token": "valid-fake-token", "new_password": "new_secure_password"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password has been reset successfully."


def test_request_email_verification(client, monkeypatch):
    async def set_unconfirmed():
        async with TestingSessionLocal() as session:
            current_user = await session.execute(
                select(User).where(User.email == test_user["email"])
            )
            current_user = current_user.scalar_one_or_none()
            assert current_user is not None
            current_user.confirmed = False
            await session.commit()

    import asyncio

    asyncio.run(set_unconfirmed())

    monkeypatch.setattr("src.api.user_api.send_email", Mock())
    response = client.post("/request_email", json={"email": test_user["email"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for confirmation."


def test_request_email_verification_already_confirmed(client, monkeypatch):
    async def set_confirmed():
        async with TestingSessionLocal() as session:
            current_user = await session.execute(
                select(User).where(User.email == test_user["email"])
            )
            current_user = current_user.scalar_one_or_none()
            assert current_user is not None
            current_user.confirmed = True
            await session.commit()

    import asyncio

    asyncio.run(set_confirmed())

    monkeypatch.setattr("src.api.user_api.send_email", Mock())
    response = client.post("/request_email", json={"email": test_user["email"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for confirmation."


def test_request_email_verification_missing_user(client, monkeypatch):
    monkeypatch.setattr("src.api.user_api.send_email", Mock())
    response = client.post("/request_email", json={"email": "missing-user@example.com"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for confirmation."


def test_refresh_access_token(client, monkeypatch):
    async def fake_refresh_token_service(refresh_token: str):
        assert refresh_token == "valid-refresh-token"
        return {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
        }

    monkeypatch.setattr(
        "src.api.user_api.user_service.refresh_token_service",
        fake_refresh_token_service,
    )

    response = client.post("/refresh", data={"refresh_token": "valid-refresh-token"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["access_token"] == "new-access-token"
    assert data["refresh_token"] == "new-refresh-token"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_user_direct_unit(monkeypatch):
    created_user = User(
        id=99,
        username="direct-user",
        email="direct-user@example.com",
        hashed_password="hashed",
        confirmed=False,
        avatar="avatar-url",
        role=Role.USER,
    )

    async def fake_create_user(db, user):
        return created_user

    monkeypatch.setattr("src.api.user_api.user_service.create_user", fake_create_user)
    monkeypatch.setattr("src.api.user_api.send_email", Mock())

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/register",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
            "scheme": "http",
        }
    )
    background_tasks = BackgroundTasks()

    result = await user_api.register_user(
        user=MagicMock(),
        background_tasks=background_tasks,
        request=request,
        db=MagicMock(),
    )

    assert result.username == created_user.username
    assert result.email == created_user.email
    assert len(background_tasks.tasks) == 1


@pytest.mark.asyncio
async def test_confirm_email_direct_unit(monkeypatch):
    db = MagicMock()

    async def fake_get_email_from_token(token):
        return test_user["email"]

    async def fake_get_user_by_email(db, email):
        return MagicMock(confirmed=False)

    fake_confirmed_email = AsyncMock()

    monkeypatch.setattr(
        "src.api.user_api.get_email_from_token", fake_get_email_from_token
    )
    monkeypatch.setattr(
        "src.api.user_api.user_service.get_user_by_email", fake_get_user_by_email
    )
    monkeypatch.setattr(
        "src.api.user_api.user_service.confirmed_email", fake_confirmed_email
    )

    result = await user_api.confirmed_email("valid-token", db)

    assert result["message"] == "Email has been confirmed."
    fake_confirmed_email.assert_awaited_once_with(test_user["email"], db)


@pytest.mark.asyncio
async def test_request_password_reset_direct_unit(monkeypatch):
    user = MagicMock(
        email=test_user["email"], username=test_user["username"], confirmed=True
    )

    async def fake_get_user_by_email(db, email):
        return user

    monkeypatch.setattr(
        "src.api.user_api.user_service.get_user_by_email", fake_get_user_by_email
    )
    monkeypatch.setattr("src.api.user_api.send_reset_password_email", Mock())

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/request_password_reset",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
            "scheme": "http",
        }
    )
    background_tasks = BackgroundTasks()

    result = await user_api.request_password_reset(
        body=MagicMock(email=test_user["email"]),
        background_tasks=background_tasks,
        request=request,
        db=MagicMock(),
    )

    assert (
        result["message"]
        == "If the account exists, password reset instructions were sent."
    )
    assert len(background_tasks.tasks) == 1
