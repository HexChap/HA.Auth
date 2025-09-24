from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app import UserCRUD, auth, schemas
from app.dependencies import get_current_active_user
from app.models import User, UserType
from app.settings import settings

user_type_to_scopes = {
    UserType.DEFAULT: {"users:me", "users:read"},
    UserType.ADMIN: {"users:me", "users:read", "users:edit"},
}

router = APIRouter(tags=["auth"])


@router.post("/token")
async def login_for_token(
    *, form_data: Annotated[schemas.CustomOAuth2Form, Depends()], response: Response
) -> schemas.TokenSchema:
    if not (user := await UserCRUD.get_by(email=form_data.username)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email could not be found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user."
        )

    if not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The password is incorrect"
        )

    scopes = form_data.scopes if form_data.scopes else ["users:me"]
    allowed_scopes = user_type_to_scopes[user.type]

    if not set(form_data.scopes).issubset(allowed_scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Not enough permissions",
                "allowed_scopes": " ".join(allowed_scopes),
            },
            headers={"WWW-Authenticate": "bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.security.access_token_expire_minutes
    )
    token = auth.create_access_token(
        data={"sub": user.email, "scopes": scopes}, expires_delta=access_token_expires
    )
    response.set_cookie(
        "Authorization",
        f"Bearer {token}",
        expires=settings.security.access_token_expire_minutes,
        httponly=True,
    )

    return schemas.TokenSchema(access_token=token, token_type="bearer")


@router.get("/logout")
async def logout(
    response: Response, _: Annotated[User, Depends(get_current_active_user)]
):
    response.delete_cookie(key="Authorization")

    return {"message": "Logout successful"}
