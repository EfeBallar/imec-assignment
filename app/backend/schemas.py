from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr


class UserRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAttributesUpdate(BaseModel):
    attributes: list[str] = Field(default_factory=list)


class UserAttributesRead(BaseModel):
    user_id: UUID
    attributes: list[str]


class GroupMemberRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class GroupRead(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    members: list[GroupMemberRead]


class UserGroupRead(BaseModel):
    user_id: UUID
    group: GroupRead | None


class GroupingRunResponse(BaseModel):
    assigned_users: int
    min_match: int
