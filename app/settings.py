from pathlib import Path
import logging

from pydantic import Field
from pydantic_settings import BaseSettings

ENVS_PATH = Path("env")
logger = logging.getLogger("uvicorn")

__all__ = ["settings", "logger"]


class _SecuritySettings(BaseSettings):
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(
        alias="REFRESH_TOKEN_EXPIRE_DAYS", default=7
    )  # New
    secret_key: str = Field(alias="JWT_ACCESS_SECRET_KEY")
    algorithm: str = Field(alias="JWT_ALGORITHM")


# noinspection PyUnboundLocalVariable
class _APISettings(BaseSettings):
    title: str
    version: str | Path = Path("v1")
    build_version: str
    version_path: Path | None = Path(version)


class _Settings(BaseSettings):
    security: _SecuritySettings
    api: _APISettings
    db_url: str = Field(alias="DB_URL")
    is_prod: bool = Field(alias="IS_PRODUCTION")

    scopes: dict[str, str] = {
        "users:me": "Read information about the current user.",
        "users:read": "Read users.",
        "users:edit": "Edit users."
    }


_security_settings = _SecuritySettings(_env_file=ENVS_PATH / "security.env")  # type: ignore
_api_settings = _APISettings(_env_file=ENVS_PATH / "api.env")  # type: ignore

settings = _Settings(security=_security_settings, api=_api_settings)  # type: ignore
