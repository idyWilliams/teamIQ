from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.user import UserProfile


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    team_lead_id: Optional[int] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team_lead_id: Optional[int] = None


class TeamMemberResponse(BaseModel):
    id: int
    user: UserProfile
    joined_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    id: int
    team_lead: Optional[UserProfile] = None
    members: List[TeamMemberResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class TeamMemberAdd(BaseModel):
    user_id: int
