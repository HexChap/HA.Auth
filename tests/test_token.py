from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import CustomOAuth2FormFactory, UserFactory


def test_token_success_sets_cookie_and_returns_token(
    client: TestClient, common_auth_creds
):
    """Test successful token generation with cookie setting."""
    # Create a realistic admin user using the factory
    admin_user = UserFactory.build(is_active=True, type="admin")

    with (
        patch(
            "app.routers.auth.UserCRUD.get_by", new=AsyncMock(return_value=admin_user)
        ),
        patch("app.routers.auth.auth.verify_password", return_value=True),
        patch("app.routers.auth.auth.create_access_token", return_value="tok123"),
    ):
        res = client.post(
            "/token",
            data=common_auth_creds.model_dump(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert res.status_code == 200
        body = res.json()
        assert body["access_token"] == "tok123"
        assert body["token_type"] == "bearer"
        # Cookie set
        assert res.cookies.get("Authorization", "").startswith('"Bearer ')  # type: ignore


def test_token_user_not_found(client: TestClient, common_auth_creds):
    """Test token generation when user is not found."""
    with patch("app.routers.auth.UserCRUD.get_by", new=AsyncMock(return_value=None)):
        res = client.post(
            "/token",
            data=common_auth_creds.model_dump(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 400
        assert res.json()["detail"] == "The user with this email could not be found"


def test_token_inactive_user(client: TestClient, common_auth_creds):
    """Test token generation for inactive user."""
    inactive_user = UserFactory.build(
        is_active=False,
    )

    with patch(
        "app.routers.auth.UserCRUD.get_by", new=AsyncMock(return_value=inactive_user)
    ):
        res = client.post(
            "/token",
            data=common_auth_creds.model_dump(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 400
        assert res.json()["detail"] == "Inactive user."


def test_token_wrong_password(client: TestClient, common_user, common_auth_creds):
    """Test token generation with wrong password."""
    # Create a regular user with proper structure
    with (
        patch(
            "app.routers.auth.UserCRUD.get_by", new=AsyncMock(return_value=common_user)
        ),
        patch("app.routers.auth.auth.verify_password", return_value=False),
    ):
        res = client.post(
            "/token",
            data=common_auth_creds.model_dump(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 400
        assert res.json()["detail"] == "The password is incorrect"


def test_token_invalid_scope(client: TestClient):
    """Test token generation with invalid scope for user type."""
    default_user = UserFactory.build(is_active=True, type="default")

    with (
        patch(
            "app.routers.auth.UserCRUD.get_by", new=AsyncMock(return_value=default_user)
        ),
        patch("app.routers.auth.auth.verify_password", return_value=True),
    ):
        res = client.post(
            "/token",
            data=CustomOAuth2FormFactory.build(scope="users:edit").model_dump(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401
        assert res.json()["detail"]["message"] == "Not enough permissions"


@pytest.mark.parametrize(
    "user_type,scope,expected_status",
    [
        ("admin", "users:edit", 200),
        ("admin", "users:read", 200),
        ("default", "users:edit", 401),
        ("default", "users:read", 200),
        ("default", "users:me", 200),
    ],
)
def test_token_scope_permissions(client: TestClient, user_type, scope, expected_status):
    """Test different user types and scope combinations."""
    user = UserFactory.build(is_active=True, type=user_type)

    with (
        patch("app.routers.auth.UserCRUD.get_by", new=AsyncMock(return_value=user)),
        patch("app.routers.auth.auth.verify_password", return_value=True),
        patch("app.routers.auth.auth.create_access_token", return_value="tok123"),
    ):
        res = client.post(
            "/token",
            data=CustomOAuth2FormFactory.build(scope=scope).model_dump(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == expected_status
