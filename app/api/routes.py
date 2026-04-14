from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.schemas import (
    GroupMemberRead,
    GroupRead,
    GroupingRunResponse,
    UserAttributesRead,
    UserAttributesUpdate,
    UserCreate,
    UserGroupRead,
    UserRead,
)
from app.services.grouping import (
    get_group_members,
    get_user_attributes,
    get_user_group,
    remove_user_membership,
    run_grouping_cycle,
    set_user_attributes,
)

router = APIRouter()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.scalars(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with same username or email already exists",
        )

    user = User(username=payload.username, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.scalars(select(User).order_by(User.created_at.asc())).all()


@router.put("/users/{user_id}/attributes", response_model=UserAttributesRead)
def set_attributes(
    user_id: UUID,
    payload: UserAttributesUpdate,
    db: Session = Depends(get_db),
) -> UserAttributesRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    normalized = set_user_attributes(db, user, payload.attributes)
    # Force reevaluation on next batch run after attributes change.
    remove_user_membership(db, user.id)
    db.commit()

    return UserAttributesRead(user_id=user.id, attributes=normalized)


@router.get("/users/{user_id}/attributes", response_model=UserAttributesRead)
def get_attributes(user_id: UUID, db: Session = Depends(get_db)) -> UserAttributesRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserAttributesRead(user_id=user.id, attributes=sorted(get_user_attributes(db, user.id)))


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users/{user_id}/group", response_model=UserGroupRead)
def get_group_for_user(user_id: UUID, db: Session = Depends(get_db)) -> UserGroupRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    group = get_user_group(db, user.id)
    if group is None:
        return UserGroupRead(user_id=user.id, group=None)

    members = get_group_members(db, group.id)
    payload = GroupRead(
        id=group.id,
        name=group.name,
        created_at=group.created_at,
        members=[GroupMemberRead.model_validate(member) for member in members],
    )
    return UserGroupRead(user_id=user.id, group=payload)


@router.post("/grouping/run", response_model=GroupingRunResponse)
def run_grouping(
    min_match: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
) -> GroupingRunResponse:
    threshold = settings.min_match if min_match is None else min_match
    assigned = run_grouping_cycle(db, min_match=threshold)
    return GroupingRunResponse(assigned_users=assigned, min_match=threshold)
