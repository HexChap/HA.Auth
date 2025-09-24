from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from ms_core import BaseCRUDRouter, DefaultEndpoint, EndpointConfig

from app import User, UserCRUD, schemas
from app.dependencies import get_current_active_user, get_current_user
from app.schemas import UserCreate, UserSchema

router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=UserSchema,
    schema_create=UserCreate,
    # schema_update=UserUpdate,
    exclude_endpoints=[DefaultEndpoint.CREATE, DefaultEndpoint.GET_ALL],
    endpoint_configs={
        DefaultEndpoint.GET_ITEM: EndpointConfig(
            path="/{item_id}",
            methods=["GET"],
            response_model=UserSchema | None,
            summary="Get item by ID",
            description="Retrieve a specific item by its ID",
            dependencies=[Security(get_current_active_user, scopes=["users:me"])],
        ),
        DefaultEndpoint.UPDATE: EndpointConfig(
            path="/{item_id}",
            methods=["PUT"],
            response_model=UserSchema | None,
            summary="Update item",
            description="Update an existing item by its ID",
            dependencies=[Security(get_current_active_user, scopes=["users:edit"])],
        ),
        DefaultEndpoint.DELETE: EndpointConfig(
            path="/{item_id}",
            methods=["DELETE"],
            response_model=bool,
            summary="Delete item",
            description="Delete an item by its ID",
            dependencies=[Security(get_current_active_user, scopes=["users:edit"])],
        ),
    },
    prefix="/users",
    tags=["users"],
)


@router.get("/")
async def get_users(
    _: Annotated[User, Security(get_current_user, scopes=["users:read"])],
) -> list[UserSchema]:
    return await UserCRUD.get_all()


@router.post("/")
async def create_user(payload: schemas.UserCreate) -> UserSchema:
    """
    Creating user in the database. Payload must contain **username**, **email** and **password**

    :param payload: Payload for user.
    :return: None
    """
    user, is_created = await UserCRUD.get_or_create(payload)

    if is_created:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exist."
        )


@router.put("/@me/update")
async def update_me(
    payload: schemas.UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return await UserCRUD.update_by(payload, id=current_user.id)
