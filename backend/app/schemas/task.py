from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority
from app.schemas.user import UserProfile


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    story_points: Optional[float] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    project_id: int
    jira_issue_key: Optional[str] = None
    github_issue_number: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    story_points: Optional[float] = None
    due_date: Optional[datetime] = None
    jira_issue_key: Optional[str] = None
    github_issue_number: Optional[int] = None


class TaskAssignmentResponse(BaseModel):
    id: int
    user: UserProfile
    assigned_at: datetime
    is_active: bool
    recommendation_score: Optional[float] = None
    recommendation_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    id: int
    project_id: int
    assignments: List[TaskAssignmentResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    jira_issue_key: Optional[str] = None
    github_issue_number: Optional[int] = None
    
    class Config:
        from_attributes = True


class TaskAssignmentRequest(BaseModel):
    task_id: int
    user_id: int
    recommendation_score: Optional[float] = None
    recommendation_reason: Optional[str] = None


class TaskAllocationRequest(BaseModel):
    project_id: int
    task_ids: List[int]
    use_ai_recommendations: bool = True
