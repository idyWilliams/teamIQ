from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.task import Task, TaskAssignment
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskAssignmentRequest, TaskAllocationRequest
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    project_id: int = None,
    assigned_to: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if assigned_to:
        query = query.join(TaskAssignment).filter(
            TaskAssignment.user_id == assigned_to,
            TaskAssignment.is_active == True
        )
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    # Create new task
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        project_id=task.project_id,
        story_points=task.story_points,
        due_date=task.due_date,
        jira_issue_key=task.jira_issue_key,
        github_issue_number=task.github_issue_number
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update task fields
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    # Update completion time if status changed to done
    if task_update.status and task_update.status.value == "done":
        from datetime import datetime
        task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@router.post("/assign", response_model=dict)
async def assign_task(
    assignment: TaskAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    # Check if task exists
    task = db.query(Task).filter(Task.id == assignment.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Deactivate existing assignments
    existing_assignments = db.query(TaskAssignment).filter(
        TaskAssignment.task_id == assignment.task_id,
        TaskAssignment.is_active == True
    ).all()
    for existing in existing_assignments:
        existing.is_active = False
    
    # Create new assignment
    db_assignment = TaskAssignment(
        task_id=assignment.task_id,
        user_id=assignment.user_id,
        recommendation_score=assignment.recommendation_score,
        recommendation_reason=assignment.recommendation_reason
    )
    
    db.add(db_assignment)
    db.commit()
    
    return {"message": "Task assigned successfully"}


@router.post("/allocate", response_model=dict)
async def allocate_tasks(
    allocation: TaskAllocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    task_service = TaskService(db)
    
    if allocation.use_ai_recommendations:
        recommendations = task_service.get_ai_task_recommendations(
            allocation.project_id,
            allocation.task_ids
        )
        
        # Apply recommendations
        for rec in recommendations:
            # Create task assignment
            db_assignment = TaskAssignment(
                task_id=rec["task_id"],
                user_id=rec["user_id"],
                recommendation_score=rec["score"],
                recommendation_reason=rec["reason"]
            )
            db.add(db_assignment)
        
        db.commit()
        
        return {
            "message": "Tasks allocated using AI recommendations",
            "recommendations": recommendations
        }
    else:
        return {"message": "Manual task allocation not implemented yet"}


@router.get("/user/{user_id}/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Users can only view their own tasks unless they have elevated permissions
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.HR, UserRole.TEAM_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's tasks"
        )
    
    tasks = db.query(Task).join(TaskAssignment).filter(
        TaskAssignment.user_id == user_id,
        TaskAssignment.is_active == True
    ).all()
    
    return tasks
