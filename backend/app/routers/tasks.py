from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from main import get_db, get_current_user
from models import User, Task, Project, TeamMember
from services.analytics_service import AnalyticsService

router = APIRouter()

class TaskCreate(BaseModel):
    external_id: str
    title: str
    description: Optional[str] = None
    project_id: int
    assignee_id: Optional[int] = None
    reporter_id: int
    status: str
    priority: Optional[str] = None
    story_points: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    story_points: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: int
    external_id: str
    title: str
    description: Optional[str] = None
    project_id: int
    assignee_id: Optional[int] = None
    reporter_id: int
    status: str
    priority: Optional[str] = None
    story_points: Optional[int] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TaskAllocationSuggestion(BaseModel):
    task_id: int
    suggested_assignee_id: int
    assignee_name: str
    confidence: float
    reasoning: str
    skill_match: dict
    workload_impact: str

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks with optional filtering"""
    query = db.query(Task)
    
    # Apply filters
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if status:
        query = query.filter(Task.status == status)
    
    # Role-based filtering
    if current_user.role in ["intern", "engineer"]:
        # Users can only see their own tasks
        query = query.filter(Task.assignee_id == current_user.id)
    elif current_user.role == "team_lead":
        # Team leads can see tasks for their team projects
        team_projects = db.query(Project).join(TeamMember).filter(
            TeamMember.user_id == current_user.id
        ).all()
        project_ids = [p.id for p in team_projects]
        query = query.filter(Task.project_id.in_(project_ids))
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create tasks"
        )
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify assignee exists if provided
    if task.assignee_id:
        assignee = db.query(User).filter(User.id == task.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )
    
    new_task = Task(
        external_id=task.external_id,
        title=task.title,
        description=task.description,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        reporter_id=task.reporter_id,
        status=task.status,
        priority=task.priority,
        story_points=task.story_points,
        due_date=task.due_date
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return new_task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check permissions
    if current_user.role in ["intern", "engineer"] and task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task"
        )
    
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check permissions
    if current_user.role in ["intern", "engineer"] and task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )
    
    # Update fields
    for field, value in task_update.dict(exclude_unset=True).items():
        if field == "assignee_id" and value:
            # Verify assignee exists
            assignee = db.query(User).filter(User.id == value).first()
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignee not found"
                )
        setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    return task

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a task"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete tasks"
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

@router.get("/user/{user_id}/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    user_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks assigned to a specific user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user tasks"
        )
    
    query = db.query(Task).filter(Task.assignee_id == user_id)
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.all()
    return tasks

@router.post("/allocate", response_model=List[TaskAllocationSuggestion])
async def get_task_allocation_suggestions(
    project_id: int,
    unassigned_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered task allocation suggestions"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to get allocation suggestions"
        )
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get tasks
    query = db.query(Task).filter(Task.project_id == project_id)
    if unassigned_only:
        query = query.filter(Task.assignee_id.is_(None))
    
    tasks = query.all()
    
    # Get team members
    team_members = db.query(User).join(TeamMember).filter(
        TeamMember.team_id == project.team_id
    ).all()
    
    if not team_members:
        return []
    
    # Prepare data for AI service
    analytics = AnalyticsService(db)
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "story_points": task.story_points,
            "status": task.status
        })
    
    members_data = []
    for member in team_members:
        member_skills = analytics.calculate_user_skill_scores(member.id)
        member_workload = len(db.query(Task).filter(
            Task.assignee_id == member.id,
            Task.status.in_(["To Do", "In Progress", "In Review"])
        ).all())
        
        members_data.append({
            "id": member.id,
            "name": f"{member.first_name} {member.last_name}",
            "role": member.role,
            "skills": member_skills,
            "current_workload": member_workload
        })
    
    # Get AI suggestions
    from services.ai_service import ai_service
    suggestions = ai_service.suggest_task_allocation(tasks_data, members_data)
    
    # Format response
    allocation_suggestions = []
    for suggestion in suggestions:
        task_id = suggestion.get("task_id")
        assigned_to = suggestion.get("assigned_to")
        
        # Find member details
        member = next((m for m in members_data if m["id"] == assigned_to), None)
        if member:
            allocation_suggestions.append(TaskAllocationSuggestion(
                task_id=task_id,
                suggested_assignee_id=assigned_to,
                assignee_name=member["name"],
                confidence=suggestion.get("confidence", 0.5),
                reasoning=suggestion.get("reasoning", "AI recommendation"),
                skill_match=member["skills"],
                workload_impact=f"Current workload: {member['current_workload']} tasks"
            ))
    
    return allocation_suggestions

@router.post("/allocate/confirm")
async def confirm_task_allocations(
    allocations: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm and apply task allocations"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to confirm allocations"
        )
    
    confirmed_allocations = []
    
    for allocation in allocations:
        task_id = allocation.get("task_id")
        assignee_id = allocation.get("assignee_id")
        
        # Update task
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.assignee_id = assignee_id
            task.updated_at = datetime.utcnow()
            confirmed_allocations.append({
                "task_id": task_id,
                "assignee_id": assignee_id,
                "status": "confirmed"
            })
    
    db.commit()
    
    return {
        "message": f"Confirmed {len(confirmed_allocations)} task allocations",
        "allocations": confirmed_allocations
    }

@router.get("/project/{project_id}/metrics")
async def get_project_task_metrics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task metrics for a project"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view project metrics"
        )
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get tasks
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    # Calculate metrics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status in ["Done", "Resolved", "Closed"]])
    in_progress_tasks = len([t for t in tasks if t.status in ["In Progress", "In Review"]])
    todo_tasks = len([t for t in tasks if t.status in ["To Do", "Open"]])
    
    total_story_points = sum(t.story_points or 0 for t in tasks)
    completed_story_points = sum(t.story_points or 0 for t in tasks if t.status in ["Done", "Resolved", "Closed"])
    
    # Priority distribution
    priority_distribution = {}
    for task in tasks:
        priority = task.priority or "None"
        priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
    
    # Assignee distribution
    assignee_distribution = {}
    for task in tasks:
        if task.assignee_id:
            assignee = db.query(User).filter(User.id == task.assignee_id).first()
            if assignee:
                name = f"{assignee.first_name} {assignee.last_name}"
                assignee_distribution[name] = assignee_distribution.get(name, 0) + 1
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "task_counts": {
            "total": total_tasks,
            "completed": completed_tasks,
            "in_progress": in_progress_tasks,
            "todo": todo_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        },
        "story_points": {
            "total": total_story_points,
            "completed": completed_story_points,
            "completion_rate": (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0
        },
        "priority_distribution": priority_distribution,
        "assignee_distribution": assignee_distribution
    }
