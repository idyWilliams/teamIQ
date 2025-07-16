from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from auth import get_current_user, require_team_lead_or_above
from models.database import (
    get_user_tasks, get_task_by_id, get_project_tasks, get_team_members,
    get_user_skills, get_projects_by_team
)
from services.task_allocation import task_allocation_engine

logger = logging.getLogger(__name__)

router = APIRouter()

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    due_date: Optional[str] = None

class TaskAllocationRequest(BaseModel):
    task_ids: List[int]
    team_id: Optional[int] = None
    force_reallocation: bool = False

class TaskFilterRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    due_date_from: Optional[str] = None
    due_date_to: Optional[str] = None

@router.get("/me")
async def get_my_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=100, description="Number of tasks to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's tasks."""
    try:
        tasks = await get_user_tasks(current_user["id"])
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        
        if priority:
            tasks = [t for t in tasks if t.get("priority") == priority]
        
        # Limit results
        tasks = tasks[:limit]
        
        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == "done"])
        in_progress_tasks = len([t for t in tasks if t.get("status") == "in_progress"])
        
        # Get upcoming deadlines
        upcoming_deadlines = []
        for task in tasks:
            if task.get("due_date") and task.get("status") != "done":
                due_date = datetime.fromisoformat(task["due_date"])
                if due_date >= datetime.now():
                    upcoming_deadlines.append({
                        "task_id": task["id"],
                        "title": task.get("title", ""),
                        "due_date": task["due_date"],
                        "priority": task.get("priority", "medium"),
                        "days_until_due": (due_date - datetime.now()).days
                    })
        
        # Sort upcoming deadlines by due date
        upcoming_deadlines.sort(key=lambda x: x["due_date"])
        
        return {
            "tasks": tasks,
            "statistics": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "upcoming_deadlines": upcoming_deadlines[:5],  # Next 5 deadlines
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting tasks for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{task_id}")
async def get_task_details(
    task_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get task details."""
    try:
        task = await get_task_by_id(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check permissions
        if (task.get("assignee_id") != current_user["id"] and 
            current_user["role"] not in ["team_lead", "hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this task"
            )
        
        # Add additional task context
        task_details = {
            **task,
            "time_tracking": {
                "estimated_hours": task.get("estimated_hours", 0),
                "actual_hours": task.get("actual_hours", 0),
                "remaining_hours": max(0, (task.get("estimated_hours", 0) - task.get("actual_hours", 0)))
            },
            "progress": {
                "status": task.get("status", "to_do"),
                "completion_percentage": 100 if task.get("status") == "done" else (
                    75 if task.get("status") == "in_review" else (
                        50 if task.get("status") == "in_progress" else 0
                    )
                )
            }
        }
        
        return {
            "task": task_details,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task details for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{task_id}")
async def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update task details."""
    try:
        task = await get_task_by_id(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check permissions
        if (task.get("assignee_id") != current_user["id"] and 
            current_user["role"] not in ["team_lead", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this task"
            )
        
        # Validate status
        if request.status:
            valid_statuses = ["to_do", "in_progress", "in_review", "done"]
            if request.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
        
        # Validate priority
        if request.priority:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if request.priority not in valid_priorities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
                )
        
        # In a real implementation, this would update the task in the database
        # For now, we'll just return success
        return {
            "success": True,
            "message": "Task updated successfully",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/project/{project_id}")
async def get_project_tasks_list(
    project_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee"),
    current_user: dict = Depends(get_current_user)
):
    """Get tasks for a specific project."""
    try:
        tasks = await get_project_tasks(project_id)
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        
        if assignee_id:
            tasks = [t for t in tasks if t.get("assignee_id") == assignee_id]
        
        # Calculate project statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == "done"])
        in_progress_tasks = len([t for t in tasks if t.get("status") == "in_progress"])
        
        # Calculate story points
        total_story_points = sum(t.get("story_points", 0) for t in tasks)
        completed_story_points = sum(
            t.get("story_points", 0) for t in tasks if t.get("status") == "done"
        )
        
        return {
            "project_id": project_id,
            "tasks": tasks,
            "statistics": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "total_story_points": total_story_points,
                "completed_story_points": completed_story_points,
                "velocity": completed_story_points
            },
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting tasks for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/allocate")
async def allocate_tasks(
    request: TaskAllocationRequest,
    current_user: dict = Depends(require_team_lead_or_above)
):
    """Allocate tasks to team members using AI recommendations."""
    try:
        team_id = request.team_id or current_user.get("team_id")
        
        if not team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team ID is required for task allocation"
            )
        
        # Check permissions
        if (current_user["team_id"] != team_id and 
            current_user["role"] not in ["hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to allocate tasks for this team"
            )
        
        # Get team members
        team_members = await get_team_members(team_id)
        
        if not team_members:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No team members found"
            )
        
        # Get team skills
        team_skills = []
        for member in team_members:
            member_skills = await get_user_skills(member["id"])
            team_skills.extend(member_skills)
        
        # Get tasks to allocate
        tasks_to_allocate = []
        for task_id in request.task_ids:
            task = await get_task_by_id(task_id)
            if task:
                tasks_to_allocate.append(task)
        
        if not tasks_to_allocate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid tasks found for allocation"
            )
        
        # Get AI recommendations
        recommendations = task_allocation_engine.allocate_tasks(
            tasks_to_allocate, team_members, team_skills
        )
        
        # Optimize allocation for team balance
        optimization_result = task_allocation_engine.optimize_team_allocation(
            tasks_to_allocate, team_members, team_skills
        )
        
        return {
            "team_id": team_id,
            "tasks_analyzed": len(tasks_to_allocate),
            "recommendations": recommendations,
            "optimized_allocation": optimization_result.get("optimized_allocation", []),
            "team_metrics": optimization_result.get("team_metrics", {}),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error allocating tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/team/{team_id}/workload")
async def get_team_workload(
    team_id: int,
    current_user: dict = Depends(require_team_lead_or_above)
):
    """Get workload distribution for a team."""
    try:
        # Check permissions
        if (current_user["team_id"] != team_id and 
            current_user["role"] not in ["hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view team workload"
            )
        
        # Get team members
        team_members = await get_team_members(team_id)
        
        # Calculate workload for each member
        workload_data = []
        for member in team_members:
            member_tasks = await get_user_tasks(member["id"])
            
            # Calculate workload metrics
            total_tasks = len(member_tasks)
            active_tasks = len([t for t in member_tasks if t.get("status") in ["to_do", "in_progress"]])
            completed_tasks = len([t for t in member_tasks if t.get("status") == "done"])
            
            # Calculate story points
            total_story_points = sum(t.get("story_points", 0) for t in member_tasks)
            active_story_points = sum(
                t.get("story_points", 0) for t in member_tasks 
                if t.get("status") in ["to_do", "in_progress"]
            )
            
            # Calculate time allocation
            estimated_hours = sum(t.get("estimated_hours", 0) for t in member_tasks if t.get("status") in ["to_do", "in_progress"])
            actual_hours = sum(t.get("actual_hours", 0) for t in member_tasks)
            
            workload_data.append({
                "member": {
                    "id": member["id"],
                    "name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    "role": member.get("role", "")
                },
                "tasks": {
                    "total": total_tasks,
                    "active": active_tasks,
                    "completed": completed_tasks
                },
                "story_points": {
                    "total": total_story_points,
                    "active": active_story_points
                },
                "time_allocation": {
                    "estimated_hours": estimated_hours,
                    "actual_hours": actual_hours,
                    "capacity_percentage": min(100, (estimated_hours / 40) * 100)  # Assuming 40-hour work week
                }
            })
        
        # Calculate team totals
        team_totals = {
            "total_tasks": sum(w["tasks"]["total"] for w in workload_data),
            "active_tasks": sum(w["tasks"]["active"] for w in workload_data),
            "completed_tasks": sum(w["tasks"]["completed"] for w in workload_data),
            "total_story_points": sum(w["story_points"]["total"] for w in workload_data),
            "active_story_points": sum(w["story_points"]["active"] for w in workload_data)
        }
        
        return {
            "team_id": team_id,
            "workload_data": workload_data,
            "team_totals": team_totals,
            "team_size": len(team_members),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team workload for team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/analytics/completion-trends")
async def get_completion_trends(
    team_id: Optional[int] = Query(None, description="Team ID (optional)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get task completion trends."""
    try:
        if team_id:
            # Check permissions for team analytics
            if (current_user["team_id"] != team_id and 
                current_user["role"] not in ["team_lead", "hr", "admin"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view team analytics"
                )
            
            # Get team tasks
            team_members = await get_team_members(team_id)
            all_tasks = []
            for member in team_members:
                member_tasks = await get_user_tasks(member["id"])
                all_tasks.extend(member_tasks)
        else:
            # Get user tasks
            all_tasks = await get_user_tasks(current_user["id"])
        
        # Filter tasks by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_tasks = [
            t for t in all_tasks 
            if datetime.fromisoformat(t.get("created_at", "")) >= cutoff_date
        ]
        
        # Calculate daily completion trends
        daily_completions = {}
        for task in recent_tasks:
            if task.get("status") == "done" and task.get("completed_at"):
                completion_date = datetime.fromisoformat(task["completed_at"]).date()
                if completion_date not in daily_completions:
                    daily_completions[completion_date] = 0
                daily_completions[completion_date] += 1
        
        # Fill in missing dates with 0
        current_date = cutoff_date.date()
        end_date = datetime.now().date()
        
        while current_date <= end_date:
            if current_date not in daily_completions:
                daily_completions[current_date] = 0
            current_date += timedelta(days=1)
        
        # Convert to chart data
        chart_data = [
            {"date": str(date), "completions": count}
            for date, count in sorted(daily_completions.items())
        ]
        
        # Calculate summary statistics
        total_completions = sum(daily_completions.values())
        avg_daily_completions = total_completions / days if days > 0 else 0
        
        return {
            "analysis_period_days": days,
            "team_id": team_id,
            "chart_data": chart_data,
            "summary": {
                "total_completions": total_completions,
                "avg_daily_completions": avg_daily_completions,
                "peak_day": max(daily_completions.items(), key=lambda x: x[1]) if daily_completions else None
            },
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting completion trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
