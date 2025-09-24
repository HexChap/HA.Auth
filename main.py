from pathlib import Path

import uvicorn as uvicorn
from fastapi import FastAPI
from fastapi.logger import logger
from ms_core import setup_app

from app.models import User
from app.settings import settings

application = FastAPI(
    title=settings.api.title,
    version=f"{settings.api.version}.{settings.api.build_version}",
)

TORTOISE_CONFIG = setup_app(
    application,
    settings.db_url,
    Path("app") / "routers",
    ["app.models", "aerich.models"],
)


@application.on_event("startup")  # if using RegisterTortoise
async def seed():
    admin = {
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": "$2b$12$070KuA1BMhdKmnWwncQTEejGJHvTl2ZVGez5jLXiw4ZzpVb4kBURa",
        "type": "admin",
        "is_active": True,
    }

    if settings.is_prod:
        return

    _, created = await User.get_or_create(admin, email=admin["email"])

    if created:
        logger.info("Seeded non-prod admin.")


# if __name__ == "__main__":
#     uvicorn.run("main:application", host="0.0.0.0", port=8000, reload=True)
