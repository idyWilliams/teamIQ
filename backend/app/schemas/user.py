from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    email_notifications: Optional[bool] = None
    in_app_notifications: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    profile_picture: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    email_notifications: bool
    in_app_notifications: bool

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    email: EmailStr
    role: UserRole
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
