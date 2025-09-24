from ms_core import CRUD

from . import auth, models, schemas


class UserCRUD_[M: models.User, S: schemas.UserSchema](CRUD[M, S]):
    def __init__(self) -> None:
        super().__init__(models.User, schemas.UserSchema)  # type: ignore

    async def get_or_create(
        self, payload: schemas.UserCreate | None = None, **kwargs
    ) -> tuple[S, bool]:
        """Custom create with password hashing"""
        if payload:
            kwargs.update(payload.model_dump())
            kwargs["password_hash"] = auth.hash_password(kwargs.pop("password"))
            kwargs["is_active"] = True

        return await super().get_or_create(**kwargs)


UserCRUD = UserCRUD_()
