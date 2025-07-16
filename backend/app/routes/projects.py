from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from auth import get_current_user, require_team_lead_or_above
from models.database import (
    get_project_by_id, get_projects_by_team, get_user_projects,
    get_project_tasks, get_team_members, get_project_retrospectives
)
from services.retrospectives import retrospective_service

logger = logging.getLogger(__name__)

router = APIRouter()

class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    github_repo: Optional[str] = None
    jira_project_key: Optional[str] = None

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[str] = None
    github_repo: Optional[str] = None
    jira_project_key: Optional[str] = None

class GenerateRetrospectiveRequest(BaseModel):
    period_start: str
    period_end: str
    title: Optional[str] = None

@router.get("/")
async def get_projects(
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of projects to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get projects based on user role and permissions."""
    try:
        if current_user["role"] in ["intern", "engineer"]:
            # Get user's projects
            projects = await get_user_projects(current_user["id"])
        elif current_user["role"] in ["team_lead", "manager"]:
            # Get team projects
            if team_id and team_id != current_user.get("team_id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view projects for this team"
                )
            projects = await get_projects_by_team(team_id or current_user["team_id"])
        else:
            # HR, Recruiter, Admin can view all projects
            if team_id:
                projects = await get_projects_by_team(team_id)
            else:
                # In a real implementation, this would get all projects
                projects = []
        
        # Apply filters
        if status:
            projects = [p for p in projects if p.get("status") == status]
        
        # Limit results
        projects = projects[:limit]
        
        # Enhance projects with additional data
        enhanced_projects = []
        for project in projects:
            # Get project tasks for statistics
            project_tasks = await get_project_tasks(project["id"])
            
            total_tasks = len(project_tasks)
            completed_tasks = len([t for t in project_tasks if t.get("status") == "done"])
            
            # Calculate progress percentage
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get recent retrospectives
            retrospectives = await get_project_retrospectives(project["id"])
            recent_retrospectives = retrospectives[:3]  # Last 3 retrospectives
            
            enhanced_project = {
                **project,
                "statistics": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "progress_percentage": progress
                },
                "recent_retrospectives": recent_retrospectives
            }
            enhanced_projects.append(enhanced_project)
        
        return {
            "projects": enhanced_projects,
            "total": len(enhanced_projects),
            "filters": {
                "team_id": team_id,
                "status": status
            },
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{project_id}")
async def get_project_detail(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed project information."""
    try:
        project = await get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if current_user["role"] in ["intern", "engineer"]:
            user_projects = await get_user_projects(current_user["id"])
            if project_id not in [p["id"] for p in user_projects]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view this project"
                )
        
        # Get project tasks
        project_tasks = await get_project_tasks(project_id)
        
        # Get team members if team_id exists
        team_members = []
        if project.get("team_id"):
            team_members = await get_team_members(project["team_id"])
        
        # Calculate project statistics
        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t.get("status") == "done"])
        in_progress_tasks = len([t for t in project_tasks if t.get("status") == "in_progress"])
        
        # Calculate story points
        total_story_points = sum(t.get("story_points", 0) for t in project_tasks)
        completed_story_points = sum(
            t.get("story_points", 0) for t in project_tasks if t.get("status") == "done"
        )
        
        # Calculate time metrics
        total_estimated_hours = sum(t.get("estimated_hours", 0) for t in project_tasks)
        total_actual_hours = sum(t.get("actual_hours", 0) for t in project_tasks)
        
        # Get project retrospectives
        retrospectives = await get_project_retrospectives(project_id)
        
        # Create detailed project response
        project_detail = {
            **project,
            "tasks": project_tasks,
            "team_members": team_members,
            "statistics": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "total_story_points": total_story_points,
                "completed_story_points": completed_story_points,
                "velocity": completed_story_points,
                "total_estimated_hours": total_estimated_hours,
                "total_actual_hours": total_actual_hours
            },
            "retrospectives": retrospectives,
            "health_status": "healthy" if (completed_tasks / total_tasks * 100) > 70 else "at_risk" if total_tasks > 0 else "new"
        }
        
        return {
            "project": project_detail,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project detail {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/")
async def create_project(
    request: CreateProjectRequest,
    current_user: dict = Depends(require_team_lead_or_above)
):
    """Create a new project."""
    try:
        # Validate status
        valid_statuses = ["active", "completed", "on_hold", "cancelled"]
        
        # Check permissions for team
        if (current_user["team_id"] != request.team_id and 
            current_user["role"] not in ["hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create project for this team"
            )
        
        # In a real implementation, this would create the project in the database
        # For now, we'll return a success response
        return {
            "success": True,
            "message": "Project created successfully",
            "project_id": 1  # Would be the actual created project ID
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{project_id}")
async def update_project(
    project_id: int,
    request: UpdateProjectRequest,
    current_user: dict = Depends(require_team_lead_or_above)
):
    """Update project information."""
    try:
        project = await get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if (current_user["team_id"] != project.get("team_id") and 
            current_user["role"] not in ["hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this project"
            )
        
        # Validate status if provided
        if request.status:
            valid_statuses = ["active", "completed", "on_hold", "cancelled"]
            if request.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
        
        # In a real implementation, this would update the project in the database
        return {
            "success": True,
            "message": "Project updated successfully",
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/{project_id}/retrospectives")
async def generate_retrospective(
    project_id: int,
    request: GenerateRetrospectiveRequest,
    current_user: dict = Depends(require_team_lead_or_above)
):
    """Generate a retrospective for a project."""
    try:
        project = await get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if (current_user["team_id"] != project.get("team_id") and 
            current_user["role"] not in ["hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to generate retrospective for this project"
            )
        
        # Parse dates
        try:
            period_start = datetime.fromisoformat(request.period_start)
            period_end = datetime.fromisoformat(request.period_end)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
        
        if period_start >= period_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Period start date must be before end date"
            )
        
        # Generate retrospective
        retrospective = await retrospective_service.generate_retrospective(
            project_id, 
            project.get("team_id"),
            period_start, 
            period_end
        )
        
        return {
            "retrospective": retrospective,
            "success": True,
            "message": "Retrospective generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating retrospective for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{project_id}/retrospectives")
async def get_project_retrospectives_list(
    project_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of retrospectives to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get retrospectives for a project."""
    try:
        project = await get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if current_user["role"] in ["intern", "engineer"]:
            user_projects = await get_user_projects(current_user["id"])
            if project_id not in [p["id"] for p in user_projects]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view retrospectives for this project"
                )
        
        retrospectives = await get_project_retrospectives(project_id)
        
        # Limit results
        retrospectives = retrospectives[:limit]
        
        return {
            "project_id": project_id,
            "retrospectives": retrospectives,
            "total": len(retrospectives),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting retrospectives for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{project_id}/health")
async def get_project_health(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get project health metrics."""
    try:
        project = await get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if current_user["role"] in ["intern", "engineer"]:
            user_projects = await get_user_projects(current_user["id"])
            if project_id not in [p["id"] for p in user_projects]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view project health"
                )
        
        # Get project tasks
        project_tasks = await get_project_tasks(project_id)
        
        # Calculate health metrics
        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t.get("status") == "done"])
        overdue_tasks = len([
            t for t in project_tasks 
            if t.get("due_date") and 
            datetime.fromisoformat(t["due_date"]) < datetime.now() and
            t.get("status") != "done"
        ])
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate velocity (story points completed)
        velocity = sum(
            t.get("story_points", 0) for t in project_tasks 
            if t.get("status") == "done"
        )
        
        # Determine health status
        if completion_rate >= 80:
            health_status = "excellent"
        elif completion_rate >= 60:
            health_status = "good"
        elif completion_rate >= 40:
            health_status = "fair"
        else:
            health_status = "poor"
        
        # Calculate risk factors
        risk_factors = []
        if overdue_tasks > 0:
            risk_factors.append(f"{overdue_tasks} overdue tasks")
        if completion_rate < 50:
            risk_factors.append("Low completion rate")
        if total_tasks == 0:
            risk_factors.append("No tasks assigned")
        
        health_metrics = {
            "project_id": project_id,
            "health_status": health_status,
            "completion_rate": completion_rate,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "velocity": velocity,
            "risk_factors": risk_factors,
            "recommendations": [
                "Focus on completing overdue tasks" if overdue_tasks > 0 else None,
                "Increase task completion rate" if completion_rate < 60 else None,
                "Add more tasks to project" if total_tasks < 5 else None
            ]
        }
        
        # Remove None recommendations
        health_metrics["recommendations"] = [r for r in health_metrics["recommendations"] if r]
        
        return {
            "health_metrics": health_metrics,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project health for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/analytics/completion-trends")
async def get_project_completion_trends(
    team_id: Optional[int] = Query(None, description="Team ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get project completion trends."""
    try:
        # Check permissions
        if team_id and current_user["role"] in ["intern", "engineer"]:
            if team_id != current_user.get("team_id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view team project analytics"
                )
        
        # Get projects
        if team_id:
            projects = await get_projects_by_team(team_id)
        else:
            projects = await get_user_projects(current_user["id"])
        
        # Calculate completion trends
        completion_data = []
        for project in projects:
            project_tasks = await get_project_tasks(project["id"])
            
            total_tasks = len(project_tasks)
            completed_tasks = len([t for t in project_tasks if t.get("status") == "done"])
            
            completion_data.append({
                "project_id": project["id"],
                "project_name": project.get("name", ""),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "status": project.get("status", "active")
            })
        
        # Sort by completion rate
        completion_data.sort(key=lambda x: x["completion_rate"], reverse=True)
        
        return {
            "analysis_period_days": days,
            "team_id": team_id,
            "completion_trends": completion_data,
            "summary": {
                "total_projects": len(projects),
                "avg_completion_rate": sum(p["completion_rate"] for p in completion_data) / len(completion_data) if completion_data else 0,
                "completed_projects": len([p for p in completion_data if p["status"] == "completed"]),
                "active_projects": len([p for p in completion_data if p["status"] == "active"])
            },
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project completion trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
