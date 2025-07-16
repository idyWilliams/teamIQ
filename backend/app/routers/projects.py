from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from main import get_db, get_current_user
from models import User, Project, Team, TeamMember, Task, Commit, PullRequest
from services.analytics_service import AnalyticsService

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: int
    status: str = "active"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    github_repo: Optional[str] = None
    jira_project_key: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    github_repo: Optional[str] = None
    jira_project_key: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    team_id: int
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    github_repo: Optional[str] = None
    jira_project_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectMetrics(BaseModel):
    project_id: int
    project_name: str
    task_metrics: dict
    code_metrics: dict
    team_metrics: dict
    timeline: dict
    health_score: float

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get projects with optional filtering"""
    query = db.query(Project)
    
    # Apply filters
    if team_id:
        query = query.filter(Project.team_id == team_id)
    if status:
        query = query.filter(Project.status == status)
    
    # Role-based filtering
    if current_user.role in ["intern", "engineer"]:
        # Users can only see projects they're involved in
        user_teams = db.query(Team).join(TeamMember).filter(
            TeamMember.user_id == current_user.id
        ).all()
        team_ids = [t.id for t in user_teams]
        query = query.filter(Project.team_id.in_(team_ids))
    elif current_user.role == "team_lead":
        # Team leads can see projects for teams they lead
        led_teams = db.query(Team).filter(Team.team_lead_id == current_user.id).all()
        team_ids = [t.id for t in led_teams]
        query = query.filter(Project.team_id.in_(team_ids))
    
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create projects"
        )
    
    # Verify team exists
    team = db.query(Team).filter(Team.id == project.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # If team lead, verify they lead this team
    if current_user.role == "team_lead" and team.team_lead_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create projects for this team"
        )
    
    new_project = Project(
        name=project.name,
        description=project.description,
        team_id=project.team_id,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        github_repo=project.github_repo,
        jira_project_key=project.jira_project_key
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if current_user.role in ["intern", "engineer"]:
        # Check if user is in the project's team
        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this project"
            )
    elif current_user.role == "team_lead":
        # Check if user leads this team
        team = db.query(Team).filter(Team.id == project.team_id).first()
        if team and team.team_lead_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this project"
            )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update projects"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # If team lead, verify they lead this team
    if current_user.role == "team_lead":
        team = db.query(Team).filter(Team.id == project.team_id).first()
        if team and team.team_lead_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this project"
            )
    
    # Update fields
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project"""
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete projects"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/metrics", response_model=ProjectMetrics)
async def get_project_metrics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive metrics for a project"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view project metrics"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    analytics = AnalyticsService(db)
    project_analytics = analytics.get_project_analytics(project_id)
    
    # Get team metrics
    team_analytics = analytics.get_team_analytics(project.team_id)
    
    # Calculate health score
    task_completion_rate = project_analytics.get("task_metrics", {}).get("completion_rate", 0)
    story_point_completion_rate = project_analytics.get("story_points", {}).get("completion_rate", 0)
    team_sentiment = team_analytics.get("aggregated_metrics", {}).get("average_sentiment", 0.5)
    
    health_score = (task_completion_rate * 0.4 + story_point_completion_rate * 0.4 + team_sentiment * 20) / 100
    
    return ProjectMetrics(
        project_id=project_id,
        project_name=project.name,
        task_metrics=project_analytics.get("task_metrics", {}),
        code_metrics=project_analytics.get("code_metrics", {}),
        team_metrics=team_analytics.get("aggregated_metrics", {}),
        timeline=project_analytics.get("timeline", {}),
        health_score=min(100, max(0, health_score))
    )

@router.get("/{project_id}/tasks")
async def get_project_tasks(
    project_id: int,
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if current_user.role in ["intern", "engineer"]:
        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this project's tasks"
            )
    
    query = db.query(Task).filter(Task.project_id == project_id)
    
    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    tasks = query.all()
    
    return [
        {
            "id": task.id,
            "external_id": task.external_id,
            "title": task.title,
            "description": task.description,
            "assignee_id": task.assignee_id,
            "status": task.status,
            "priority": task.priority,
            "story_points": task.story_points,
            "due_date": task.due_date,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        for task in tasks
    ]

@router.get("/{project_id}/team")
async def get_project_team(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team members for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get team members
    team_members = db.query(User).join(TeamMember).filter(
        TeamMember.team_id == project.team_id
    ).all()
    
    # Get analytics for each member
    analytics = AnalyticsService(db)
    team_data = []
    
    for member in team_members:
        member_metrics = analytics.get_user_productivity_metrics(member.id)
        member_skills = analytics.calculate_user_skill_scores(member.id)
        
        team_data.append({
            "id": member.id,
            "name": f"{member.first_name} {member.last_name}",
            "email": member.email,
            "role": member.role,
            "skills": member_skills,
            "metrics": member_metrics
        })
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "team_id": project.team_id,
        "team_members": team_data
    }

@router.get("/{project_id}/code-metrics")
async def get_project_code_metrics(
    project_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get code metrics for a project"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view code metrics"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get commits
    commits = db.query(Commit).filter(
        Commit.project_id == project_id,
        Commit.commit_date >= cutoff_date
    ).all()
    
    # Get pull requests
    pull_requests = db.query(PullRequest).filter(
        PullRequest.project_id == project_id,
        PullRequest.created_at >= cutoff_date
    ).all()
    
    # Analyze commits
    total_commits = len(commits)
    total_additions = sum(c.additions or 0 for c in commits)
    total_deletions = sum(c.deletions or 0 for c in commits)
    total_files_changed = sum(c.files_changed or 0 for c in commits)
    
    # Language distribution
    language_stats = {}
    for commit in commits:
        if commit.languages:
            for lang, lines in commit.languages.items():
                language_stats[lang] = language_stats.get(lang, 0) + lines
    
    # Contributor stats
    contributor_stats = {}
    for commit in commits:
        if commit.user_id:
            contributor_stats[commit.user_id] = contributor_stats.get(commit.user_id, 0) + 1
    
    # Pull request stats
    pr_stats = {
        "total_prs": len(pull_requests),
        "merged_prs": len([pr for pr in pull_requests if pr.merged_at]),
        "open_prs": len([pr for pr in pull_requests if pr.status == "open"]),
        "avg_review_comments": sum(pr.review_comments or 0 for pr in pull_requests) / len(pull_requests) if pull_requests else 0
    }
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "period_days": days,
        "commit_stats": {
            "total_commits": total_commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "net_changes": total_additions - total_deletions,
            "files_changed": total_files_changed
        },
        "language_distribution": language_stats,
        "contributor_stats": contributor_stats,
        "pull_request_stats": pr_stats,
        "activity_trend": []  # Could be enhanced with daily/weekly breakdown
    }
