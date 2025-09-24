from typing import Annotated

import pydantic
from fastapi import Depends, HTTPException, Request, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
import jwt

from app.auth import oauth2_scheme
from app.settings import settings
from app import UserCRUD, User, schemas


class OAuth2PasswordBearerCookies(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not (authorization := request.headers.get("Authorization")):
            if not (authorization := request.cookies.get("Authorization")):
                raise exc

        scheme, _, token = authorization.partition(" ")

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise exc
            else:
                return None
        return token


SECRET_KEY, ALGORITHM = settings.security.secret_key, settings.security.algorithm


async def get_current_user(
    security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if not email:
            raise credentials_exception

        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(scopes=token_scopes, email=email)
    except (jwt.InvalidTokenError, pydantic.ValidationError):
        raise credentials_exception

    if not (user := await UserCRUD.get_by(email=email)):
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["users:me"])],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user."
        )

    return current_user
