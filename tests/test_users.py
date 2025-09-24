from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.schemas import UserSchema
from tests.conftest import UserFactory


def test_get_users_requires_scope(client: TestClient):
    """Test that getting users requires proper authentication scope."""
    # No overrides -> auth dependency will fail
    res = client.get("/users/")
    assert res.status_code in (401, 403)


def test_get_users_success(client: TestClient, allow_all_users):
    """Test successful retrieval of users list."""
    with patch("app.routers.users.UserCRUD.get_all", new=AsyncMock(return_value=[])):
        res = client.get("/users/")
        assert res.status_code == 200
        assert res.json() == []


def test_create_user_success(client: TestClient, common_user_payload):
    """Test successful user creation."""
    user_obj = UserFactory.build(
        id=1,
        is_active=True,
        type="default",
        **common_user_payload.model_dump(exclude=("password",)),
    )

    async def _get_or_create(p):
        # Convert Pydantic model to dict for API response
        return (user_obj.model_dump(), True)

    with patch(
        "app.routers.users.UserCRUD.get_or_create",
        new=AsyncMock(side_effect=_get_or_create),
    ):
        res = client.post("/users/", json=common_user_payload.model_dump())

        assert res.status_code == 200
        assert UserSchema(**res.json()) == user_obj


def test_create_user_conflict(client: TestClient, common_user_payload):
    """Test user creation conflict when user already exists."""

    async def _get_or_create(p):
        return (None, False)

    with patch(
        "app.routers.users.UserCRUD.get_or_create",
        new=AsyncMock(side_effect=_get_or_create),
    ):
        res = client.post("/users/", json=common_user_payload.model_dump())
        assert res.status_code == 400
        assert res.json()["detail"] == "User already exist."


def test_update_me(client: TestClient, allow_all_users):
    """Test updating current user profile."""
    updated_user = UserFactory.build(username="newname")

    with patch(
        "app.routers.users.UserCRUD.update_by",
        new=AsyncMock(return_value=updated_user),
    ):
        res = client.put("/users/@me/update", json={"username": "newname"})
        assert res.status_code == 200
        assert UserSchema(**res.json()) == updated_user
