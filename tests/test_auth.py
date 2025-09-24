from fastapi.testclient import TestClient
from polyfactory.factories.pydantic_factory import ModelFactory

from app.schemas import APIInfo


class APIInfoFactory(ModelFactory):
    """Factory for creating API info responses."""

    __model__ = APIInfo


def test_api_info_endpoint(client: TestClient):
    """Test API info endpoint returns expected structure."""
    res = client.get("/api-info")
    assert res.status_code == 200
    data = res.json()
    assert "api_version" in data and "build_version" in data


def test_logout_requires_auth(client: TestClient):
    """Test logout endpoint requires authentication."""
    res = client.get("/logout")
    assert res.status_code in (401, 403)


def test_logout_success_with_token_cookie(client: TestClient, allow_all_users):
    """Test successful logout clears authorization cookie."""
    # Dependency override simulates authenticated user
    res = client.get("/logout")
    assert res.status_code == 200
    assert res.json()["message"] == "Logout successful"
    # Cookie is deleted
    assert "authorization" not in {k.lower() for k in res.cookies.keys()}


def test_api_info_structure_validation():
    """Example test validating API info structure using factory."""
    # Generate mock API info for testing
    api_info = APIInfoFactory.build()

    assert hasattr(api_info, "api_version")
    assert hasattr(api_info, "build_version")
