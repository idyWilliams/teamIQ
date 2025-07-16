from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.skill import SkillCategory


class SkillBase(BaseModel):
    name: str
    category: SkillCategory
    description: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserSkillResponse(BaseModel):
    id: int
    skill: SkillResponse
    proficiency_score: float
    last_updated: datetime
    github_commits: int
    code_reviews: int
    jira_tickets: int
    peer_reviews_score: float
    
    class Config:
        from_attributes = True


class UserSkillUpdate(BaseModel):
    proficiency_score: Optional[float] = None
    github_commits: Optional[int] = None
    code_reviews: Optional[int] = None
    jira_tickets: Optional[int] = None
    peer_reviews_score: Optional[float] = None


class SkillAnalytics(BaseModel):
    skill_name: str
    category: str
    current_score: float
    trend: str  # "up", "down", "stable"
    change_percentage: float
    evidence_count: int
    last_activity: datetime
