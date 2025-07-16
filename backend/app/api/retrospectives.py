from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from models import User, Retrospective, Project, Team, TeamMember, get_db
from auth import get_current_user, require_role
from services.ai_service import AIService
from services.analytics_service import AnalyticsService

router = APIRouter()

class RetrospectiveCreate(BaseModel):
    title: str
    period_start: datetime
    period_end: datetime
    project_id: Optional[int] = None
    team_id: Optional[int] = None

class RetrospectiveResponse(BaseModel):
    id: int
    title: str
    period_start: datetime
    period_end: datetime
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    summary: Optional[str] = None
    achievements: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    skill_insights: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    created_by: int
    created_by_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class RetrospectiveGenerateRequest(BaseModel):
    title: str
    period_start: datetime
    period_end: datetime
    project_id: Optional[int] = None
    team_id: Optional[int] = None

@router.get("/", response_model=List[RetrospectiveResponse])
async def get_retrospectives(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get retrospectives based on user permissions"""
    query = db.query(Retrospective)
    
    # Apply role-based filtering
    if current_user.role == "intern":
        # Interns can see retrospectives from their teams
        user_teams = db.query(Team).join(TeamMember).filter(
            TeamMember.user_id == current_user.id
        ).all()
        team_ids = [team.id for team in user_teams]
        
        if team_ids:
            query = query.filter(Retrospective.team_id.in_(team_ids))
        else:
            return []
            
    elif current_user.role == "team_lead":
        # Team leads can see retrospectives from teams they lead
        user_teams = db.query(Team).filter(Team.lead_id == current_user.id).all()
        team_ids = [team.id for team in user_teams]
        
        if team_ids:
            query = query.filter(Retrospective.team_id.in_(team_ids))
        else:
            return []
    
    # Apply filters
    if project_id:
        query = query.filter(Retrospective.project_id == project_id)
    
    if team_id:
        query = query.filter(Retrospective.team_id == team_id)
    
    retrospectives = query.order_by(desc(Retrospective.created_at)).offset(skip).limit(limit).all()
    
    # Build response
    response = []
    for retro in retrospectives:
        retro_response = RetrospectiveResponse.from_orm(retro)
        
        # Add related names
        if retro.project:
            retro_response.project_name = retro.project.name
        
        if retro.team:
            retro_response.team_name = retro.team.name
        
        if retro.creator:
            retro_response.created_by_name = retro.creator.full_name
        
        # Parse JSON fields
        retro_response.achievements = retro.achievements or []
        retro_response.challenges = retro.challenges or []
        retro_response.action_items = retro.action_items or []
        retro_response.skill_insights = retro.skill_insights or {}
        retro_response.performance_metrics = retro.performance_metrics or {}
        
        response.append(retro_response)
    
    return response

@router.get("/{retrospective_id}", response_model=RetrospectiveResponse)
async def get_retrospective(
    retrospective_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific retrospective"""
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    # Check permissions
    can_view = False
    
    if current_user.role in ["admin", "hr"]:
        can_view = True
    elif current_user.id == retrospective.created_by:
        can_view = True
    elif current_user.role == "team_lead" and retrospective.team:
        if retrospective.team.lead_id == current_user.id:
            can_view = True
    elif current_user.role == "intern" and retrospective.team:
        # Check if user is member of the retrospective's team
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == retrospective.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if is_member:
            can_view = True
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build response
    retro_response = RetrospectiveResponse.from_orm(retrospective)
    
    if retrospective.project:
        retro_response.project_name = retrospective.project.name
    
    if retrospective.team:
        retro_response.team_name = retrospective.team.name
    
    if retrospective.creator:
        retro_response.created_by_name = retrospective.creator.full_name
    
    # Parse JSON fields
    retro_response.achievements = retrospective.achievements or []
    retro_response.challenges = retrospective.challenges or []
    retro_response.action_items = retrospective.action_items or []
    retro_response.skill_insights = retrospective.skill_insights or {}
    retro_response.performance_metrics = retrospective.performance_metrics or {}
    
    return retro_response

@router.post("/generate", response_model=RetrospectiveResponse)
async def generate_retrospective(
    request: RetrospectiveGenerateRequest,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    """Generate an AI-powered retrospective"""
    # Validate that either project_id or team_id is provided
    if not request.project_id and not request.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either project_id or team_id must be provided"
        )
    
    # Validate project if provided
    project = None
    if request.project_id:
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if current_user.role == "team_lead" and project.team.lead_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Validate team if provided
    team = None
    if request.team_id:
        team = db.query(Team).filter(Team.id == request.team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check permissions
        if current_user.role == "team_lead" and team.lead_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    try:
        # Initialize services
        ai_service = AIService()
        analytics_service = AnalyticsService()
        
        # Collect data for the retrospective period
        sprint_data = await _collect_sprint_data(
            request.period_start,
            request.period_end,
            request.project_id,
            request.team_id,
            db
        )
        
        # Generate retrospective using AI
        retrospective_content = await ai_service.generate_retrospective(sprint_data)
        
        # Create retrospective record
        new_retrospective = Retrospective(
            title=request.title,
            period_start=request.period_start,
            period_end=request.period_end,
            project_id=request.project_id,
            team_id=request.team_id,
            summary=retrospective_content.get("summary", ""),
            achievements=retrospective_content.get("achievements", []),
            challenges=retrospective_content.get("challenges", []),
            action_items=retrospective_content.get("action_items", []),
            skill_insights=retrospective_content.get("individual_highlights", {}),
            performance_metrics=retrospective_content.get("metrics_comparison", {}),
            created_by=current_user.id
        )
        
        db.add(new_retrospective)
        db.commit()
        db.refresh(new_retrospective)
        
        # Build response
        retro_response = RetrospectiveResponse.from_orm(new_retrospective)
        
        if new_retrospective.project:
            retro_response.project_name = new_retrospective.project.name
        
        if new_retrospective.team:
            retro_response.team_name = new_retrospective.team.name
        
        retro_response.created_by_name = current_user.full_name
        
        # Parse JSON fields
        retro_response.achievements = new_retrospective.achievements or []
        retro_response.challenges = new_retrospective.challenges or []
        retro_response.action_items = new_retrospective.action_items or []
        retro_response.skill_insights = new_retrospective.skill_insights or {}
        retro_response.performance_metrics = new_retrospective.performance_metrics or {}
        
        return retro_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate retrospective: {str(e)}"
        )

@router.post("/", response_model=RetrospectiveResponse)
async def create_retrospective(
    retrospective_data: RetrospectiveCreate,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    """Create a manual retrospective"""
    # Validate that either project_id or team_id is provided
    if not retrospective_data.project_id and not retrospective_data.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either project_id or team_id must be provided"
        )
    
    # Validate project if provided
    if retrospective_data.project_id:
        project = db.query(Project).filter(Project.id == retrospective_data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if current_user.role == "team_lead" and project.team.lead_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Validate team if provided
    if retrospective_data.team_id:
        team = db.query(Team).filter(Team.id == retrospective_data.team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check permissions
        if current_user.role == "team_lead" and team.lead_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Create retrospective
    new_retrospective = Retrospective(
        title=retrospective_data.title,
        period_start=retrospective_data.period_start,
        period_end=retrospective_data.period_end,
        project_id=retrospective_data.project_id,
        team_id=retrospective_data.team_id,
        created_by=current_user.id
    )
    
    db.add(new_retrospective)
    db.commit()
    db.refresh(new_retrospective)
    
    # Build response
    retro_response = RetrospectiveResponse.from_orm(new_retrospective)
    
    if new_retrospective.project:
        retro_response.project_name = new_retrospective.project.name
    
    if new_retrospective.team:
        retro_response.team_name = new_retrospective.team.name
    
    retro_response.created_by_name = current_user.full_name
    
    return retro_response

@router.put("/{retrospective_id}", response_model=RetrospectiveResponse)
async def update_retrospective(
    retrospective_id: int,
    retrospective_data: RetrospectiveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a retrospective"""
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    # Check permissions
    can_update = False
    
    if current_user.role in ["admin", "hr"]:
        can_update = True
    elif current_user.id == retrospective.created_by:
        can_update = True
    elif current_user.role == "team_lead" and retrospective.team:
        if retrospective.team.lead_id == current_user.id:
            can_update = True
    
    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update retrospective
    retrospective.title = retrospective_data.title
    retrospective.period_start = retrospective_data.period_start
    retrospective.period_end = retrospective_data.period_end
    retrospective.project_id = retrospective_data.project_id
    retrospective.team_id = retrospective_data.team_id
    
    db.commit()
    db.refresh(retrospective)
    
    # Build response
    retro_response = RetrospectiveResponse.from_orm(retrospective)
    
    if retrospective.project:
        retro_response.project_name = retrospective.project.name
    
    if retrospective.team:
        retro_response.team_name = retrospective.team.name
    
    if retrospective.creator:
        retro_response.created_by_name = retrospective.creator.full_name
    
    return retro_response

@router.delete("/{retrospective_id}")
async def delete_retrospective(
    retrospective_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a retrospective"""
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    # Check permissions (only creator, admin, or HR can delete)
    if (current_user.role not in ["admin", "hr"] and 
        current_user.id != retrospective.created_by):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    db.delete(retrospective)
    db.commit()
    
    return {"message": "Retrospective deleted successfully"}

@router.get("/team/{team_id}/recent")
async def get_recent_team_retrospectives(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get recent retrospectives for a team"""
    # Check permissions
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    can_view = False
    
    if current_user.role in ["admin", "hr"]:
        can_view = True
    elif current_user.role == "team_lead" and team.lead_id == current_user.id:
        can_view = True
    elif current_user.role == "intern":
        # Check if user is member of this team
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if is_member:
            can_view = True
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get recent retrospectives
    retrospectives = db.query(Retrospective).filter(
        Retrospective.team_id == team_id
    ).order_by(desc(Retrospective.created_at)).limit(limit).all()
    
    # Build response
    response = []
    for retro in retrospectives:
        response.append({
            "id": retro.id,
            "title": retro.title,
            "period_start": retro.period_start.isoformat(),
            "period_end": retro.period_end.isoformat(),
            "project_name": retro.project.name if retro.project else None,
            "created_by_name": retro.creator.full_name if retro.creator else None,
            "created_at": retro.created_at.isoformat(),
            "has_content": bool(retro.summary or retro.achievements or retro.challenges)
        })
    
    return {"retrospectives": response}

@router.get("/project/{project_id}/recent")
async def get_recent_project_retrospectives(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get recent retrospectives for a project"""
    # Check permissions
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    can_view = False
    
    if current_user.role in ["admin", "hr"]:
        can_view = True
    elif current_user.role == "team_lead" and project.team and project.team.lead_id == current_user.id:
        can_view = True
    elif current_user.role == "intern" and project.team:
        # Check if user is member of the project's team
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if is_member:
            can_view = True
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get recent retrospectives
    retrospectives = db.query(Retrospective).filter(
        Retrospective.project_id == project_id
    ).order_by(desc(Retrospective.created_at)).limit(limit).all()
    
    # Build response
    response = []
    for retro in retrospectives:
        response.append({
            "id": retro.id,
            "title": retro.title,
            "period_start": retro.period_start.isoformat(),
            "period_end": retro.period_end.isoformat(),
            "team_name": retro.team.name if retro.team else None,
            "created_by_name": retro.creator.full_name if retro.creator else None,
            "created_at": retro.created_at.isoformat(),
            "has_content": bool(retro.summary or retro.achievements or retro.challenges)
        })
    
    return {"retrospectives": response}

async def _collect_sprint_data(
    period_start: datetime,
    period_end: datetime,
    project_id: Optional[int],
    team_id: Optional[int],
    db: Session
) -> Dict[str, Any]:
    """Collect data for retrospective generation"""
    from models import Task, User, TeamMember, SkillAnalytics, SentimentAnalysis
    
    # Get team members
    if team_id:
        team_members = db.query(User).join(TeamMember).filter(
            TeamMember.team_id == team_id
        ).all()
    elif project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and project.team_id:
            team_members = db.query(User).join(TeamMember).filter(
                TeamMember.team_id == project.team_id
            ).all()
        else:
            team_members = []
    else:
        team_members = []
    
    # Get tasks for the period
    task_query = db.query(Task).filter(
        Task.updated_at >= period_start,
        Task.updated_at <= period_end
    )
    
    if project_id:
        task_query = task_query.filter(Task.project_id == project_id)
    elif team_id:
        # Get tasks from projects belonging to this team
        project_ids = db.query(Project.id).filter(Project.team_id == team_id).all()
        project_ids = [p[0] for p in project_ids]
        if project_ids:
            task_query = task_query.filter(Task.project_id.in_(project_ids))
    
    tasks = task_query.all()
    
    # Calculate metrics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "done"])
    
    # Get individual contributions
    individual_contributions = {}
    for member in team_members:
        member_tasks = [t for t in tasks if t.assignee_id == member.id]
        member_completed = len([t for t in member_tasks if t.status == "done"])
        
        # Get sentiment data for this member
        member_sentiment = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.user_id == member.id,
            SentimentAnalysis.analyzed_at >= period_start,
            SentimentAnalysis.analyzed_at <= period_end
        ).all()
        
        avg_sentiment = 0
        if member_sentiment:
            avg_sentiment = sum(s.sentiment_score for s in member_sentiment) / len(member_sentiment)
        
        individual_contributions[member.full_name] = {
            "tasks_assigned": len(member_tasks),
            "tasks_completed": member_completed,
            "completion_rate": (member_completed / len(member_tasks) * 100) if member_tasks else 0,
            "avg_sentiment": avg_sentiment
        }
    
    # Get average sentiment for the team
    all_sentiment = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.user_id.in_([m.id for m in team_members]),
        SentimentAnalysis.analyzed_at >= period_start,
        SentimentAnalysis.analyzed_at <= period_end
    ).all()
    
    avg_sentiment = 0
    blockers = 0
    if all_sentiment:
        avg_sentiment = sum(s.sentiment_score for s in all_sentiment) / len(all_sentiment)
        blockers = sum(1 for s in all_sentiment if s.has_blockers)
    
    return {
        "sprint_name": f"Sprint {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
        "duration": (period_end - period_start).days,
        "team_size": len(team_members),
        "tasks_completed": completed_tasks,
        "tasks_started": total_tasks,
        "story_points_completed": completed_tasks * 5,  # Simple estimation
        "story_points_planned": total_tasks * 5,
        "commits": sum(20 for _ in team_members),  # Placeholder - would come from GitHub
        "pull_requests": sum(5 for _ in team_members),  # Placeholder
        "code_reviews": sum(10 for _ in team_members),  # Placeholder
        "avg_sentiment": avg_sentiment,
        "blockers": blockers,
        "individual_contributions": individual_contributions
    }
