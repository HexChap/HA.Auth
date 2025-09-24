from typing import Any, Callable, Iterable, ParamSpec, TypeVar

import pytest
from fastapi import FastAPI
from fastapi.security import SecurityScopes
from fastapi.testclient import TestClient
from polyfactory.factories.pydantic_factory import ModelFactory

from app.dependencies import get_current_active_user, get_current_user
from app.routers import auth as auth_router
from app.routers import misc as misc_router
from app.routers import users as users_router
from app.schemas import CustomOAuth2FormSchema, UserCreate, UserSchema

P = ParamSpec("P")
R = TypeVar("R")


def factory(cls: Callable[P, R], /) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def inner(func):
        return func

    return inner


class UserFactory(ModelFactory[UserSchema]):
    """Factory for creating User instances for authentication tests."""

    __model__ = UserSchema


class UserCreateFactory(ModelFactory[UserCreate]):
    __model__ = UserCreate


class CustomOAuth2FormFactory(ModelFactory[CustomOAuth2FormSchema]):
    __model__ = CustomOAuth2FormSchema


@pytest.fixture
@factory(CustomOAuth2FormSchema)
def common_auth_creds(**kwargs: Any) -> CustomOAuth2FormSchema:
    return CustomOAuth2FormFactory.build(scope="", **kwargs)


@pytest.fixture
def common_user() -> UserSchema:
    return UserFactory.build(is_active=True)


@pytest.fixture
def common_user_payload() -> UserCreate:
    return UserCreateFactory.build()


@pytest.fixture()
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(auth_router.router)
    application.include_router(users_router.router)
    application.include_router(misc_router.router)
    return application


@pytest.fixture()
def client(app: FastAPI) -> Iterable[TestClient]:
    with TestClient(app) as c:
        yield c


def make_scope_enforcing_get_current_user(
    allowed_scopes: list[str] | None = None, *, active: bool = True
) -> Callable:
    allowed_scopes = allowed_scopes or ["users:me", "users:read", "users:edit"]

    async def _override(security_scopes: SecurityScopes):
        for scope in security_scopes.scopes:
            if scope not in allowed_scopes:
                from fastapi import HTTPException, status

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not enough permissions",
                    headers={
                        "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'
                    },
                )
        return UserFactory.build(is_active=active)

    return _override


@pytest.fixture()
def allow_all_users(app: FastAPI):
    app.dependency_overrides[get_current_user] = make_scope_enforcing_get_current_user()
    app.dependency_overrides[get_current_active_user] = (
        make_scope_enforcing_get_current_user(active=True)
    )
    try:
        yield
    finally:
        app.dependency_overrides.clear()
