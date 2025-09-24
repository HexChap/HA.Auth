import enum

from ms_core import AbstractModel
from tortoise import fields

from app.validators import EmailValidator


class UserType(enum.StrEnum):
    DEFAULT = enum.auto()
    ADMIN = enum.auto()


class User(AbstractModel):
    username = fields.TextField()
    email = fields.CharField(256, unique=True, validators=[EmailValidator()])
    password_hash = fields.TextField()
    is_active = fields.BooleanField()
    type = fields.CharEnumField(UserType, default=UserType.DEFAULT)

    class Meta:  # type: ignore
        table = "users"
