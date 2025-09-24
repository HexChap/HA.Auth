from typing import Annotated, Union

from fastapi import Form
from fastapi.security import OAuth2PasswordRequestForm
from ms_core.utils.partial_model import partial_model
from pydantic import BaseModel, EmailStr, constr
from tortoise.contrib.pydantic import pydantic_model_creator
from typing_extensions import Doc

from .models import User


class APIInfo(BaseModel):
    api_version: str
    build_version: str


_UserSchema = pydantic_model_creator(User)


class UserSchema(_UserSchema):
    email: EmailStr


_UserCreate = pydantic_model_creator(
    User,
    name="UserCreate",
    exclude=("password_hash", "type", "is_active"),
    exclude_readonly=True,
)


class UserCreate(_UserCreate):
    email: EmailStr
    password: constr(min_length=8)


UserUpdate = partial_model(UserCreate, "UserUpdate")


class CredentialsRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class TokenData(BaseModel):
    email: EmailStr
    scopes: list[str]


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class CustomOAuth2FormSchema(BaseModel):
    grant_type: constr(pattern="password")
    username: EmailStr
    password: constr(min_length=8)
    scope: str
    client_id: str | None
    client_secret: str | None


class CustomOAuth2Form(OAuth2PasswordRequestForm):
    def __init__(
        self,
        *,
        grant_type: Annotated[
            Union[str, None],
            Form(pattern="password"),
            Doc("""
                    The OAuth2 spec says it is required and MUST be the fixed string
                    "password". Nevertheless, this dependency class is permissive and
                    allows not passing it. If you want to enforce it, use instead the
                    `OAuth2PasswordRequestFormStrict` dependency.
                    """),
        ] = None,
        username: Annotated[
            EmailStr,
            Form(min_length=1),
            Doc("""
                    `username` string. The OAuth2 spec requires the exact field name
                    `username`.
                    """),
        ],
        password: Annotated[
            str,
            Form(min_length=8),
            Doc("""
                    `password` string. The OAuth2 spec requires the exact field name
                    `password".
                    """),
        ],
        scope: Annotated[
            str,
            Form(),
            Doc("""
                    A single string with actually several scopes separated by spaces. Each
                    scope is also a string.

                    For example, a single string with:

                    ```python
                    "items:read items:write users:read profile openid"
                    ````

                    would represent the scopes:

                    * `items:read`
                    * `items:write`
                    * `users:read`
                    * `profile`
                    * `openid`
                    """),
        ] = "",
        client_id: Annotated[
            Union[str, None],
            Form(),
            Doc("""
                    If there's a `client_id`, it can be sent as part of the form fields.
                    But the OAuth2 specification recommends sending the `client_id` and
                    `client_secret` (if any) using HTTP Basic auth.
                    """),
        ] = None,
        client_secret: Annotated[
            Union[str, None],
            Form(),
            Doc("""
                    If there's a `client_password` (and a `client_id`), they can be sent
                    as part of the form fields. But the OAuth2 specification recommends
                    sending the `client_id` and `client_secret` (if any) using HTTP Basic
                    auth.
                    """),
        ] = None,
    ):
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )
