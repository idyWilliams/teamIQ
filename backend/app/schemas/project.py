from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.project import ProjectStatus
from app.schemas.user import UserProfile


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    github_repo_url: Optional[str] = None
    jira_project_key: Optional[str] = None


class ProjectCreate(ProjectBase):
    team_id: int
    project_lead_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    project_lead_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    github_repo_url: Optional[str] = None
    jira_project_key: Optional[str] = None


class ProjectMemberResponse(BaseModel):
    id: int
    user: UserProfile
    joined_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class ProjectResponse(ProjectBase):
    id: int
    team_id: int
    project_lead: Optional[UserProfile] = None
    members: List[ProjectMemberResponse] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    user_id: int
