import datetime as dt
from datetime import datetime, timedelta
from typing import Union

import jwt
from fastapi.security import (
    OAuth2PasswordBearer,
)
import bcrypt

from app.settings import settings

SECRET_KEY, ALGORITHM = settings.security.secret_key, settings.security.algorithm

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes=settings.scopes,
)


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def verify_password(password: str, hash: str) -> bool:
    password_enc = password.encode("utf-8")
    hash_enc = hash.encode("utf-8")
    return bcrypt.checkpw(password_enc, hash_enc)


def create_access_token(
    data: dict, expires_delta: Union[timedelta, None] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(dt.UTC) + (
        expires_delta if expires_delta else timedelta(minutes=60 * 60)
    )
    to_encode["exp"] = expire

    return jwt.encode(to_encode, SECRET_KEY)
