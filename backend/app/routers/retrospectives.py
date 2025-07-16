from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from main import get_db, get_current_user
from models import User, Retrospective, Project, Team, TeamMember
from services.analytics_service import AnalyticsService
from services.ai_service import ai_service

router = APIRouter()

class RetrospectiveCreate(BaseModel):
    title: str
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    period_start: datetime
    period_end: datetime

class RetrospectiveResponse(BaseModel):
    id: int
    title: str
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    period_start: datetime
    period_end: datetime
    summary: Optional[str] = None
    achievements: Optional[dict] = None
    challenges: Optional[dict] = None
    action_items: Optional[dict] = None
    metrics: Optional[dict] = None
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RetrospectiveMetrics(BaseModel):
    period_start: datetime
    period_end: datetime
    team_performance: dict
    project_metrics: dict
    sentiment_analysis: dict
    skill_development: dict
    recommendations: List[str]

@router.get("/", response_model=List[RetrospectiveResponse])
async def get_retrospectives(
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get retrospectives with optional filtering"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view retrospectives"
        )
    
    query = db.query(Retrospective)
    
    # Apply filters
    if project_id:
        query = query.filter(Retrospective.project_id == project_id)
    if team_id:
        query = query.filter(Retrospective.team_id == team_id)
    
    # Role-based filtering
    if current_user.role == "team_lead":
        # Team leads can only see retrospectives for their teams
        led_teams = db.query(Team).filter(Team.team_lead_id == current_user.id).all()
        team_ids = [t.id for t in led_teams]
        query = query.filter(Retrospective.team_id.in_(team_ids))
    
    retrospectives = query.order_by(Retrospective.created_at.desc()).offset(skip).limit(limit).all()
    return retrospectives

@router.post("/", response_model=RetrospectiveResponse)
async def create_retrospective(
    retrospective: RetrospectiveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new retrospective"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create retrospectives"
        )
    
    # Validate that either project_id or team_id is provided
    if not retrospective.project_id and not retrospective.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either project_id or team_id must be provided"
        )
    
    # Verify project/team exists and user has access
    if retrospective.project_id:
        project = db.query(Project).filter(Project.id == retrospective.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if current_user.role == "team_lead":
            team = db.query(Team).filter(Team.id == project.team_id).first()
            if not team or team.team_lead_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to create retrospectives for this project"
                )
    
    if retrospective.team_id:
        team = db.query(Team).filter(Team.id == retrospective.team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        if current_user.role == "team_lead" and team.team_lead_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create retrospectives for this team"
            )
    
    new_retrospective = Retrospective(
        title=retrospective.title,
        project_id=retrospective.project_id,
        team_id=retrospective.team_id,
        period_start=retrospective.period_start,
        period_end=retrospective.period_end,
        created_by=current_user.id
    )
    
    db.add(new_retrospective)
    db.commit()
    db.refresh(new_retrospective)
    
    return new_retrospective

@router.get("/{retrospective_id}", response_model=RetrospectiveResponse)
async def get_retrospective(
    retrospective_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific retrospective"""
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    # Check permissions
    if current_user.role == "team_lead":
        if retrospective.team_id:
            team = db.query(Team).filter(Team.id == retrospective.team_id).first()
            if not team or team.team_lead_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this retrospective"
                )
        elif retrospective.project_id:
            project = db.query(Project).filter(Project.id == retrospective.project_id).first()
            if project:
                team = db.query(Team).filter(Team.id == project.team_id).first()
                if not team or team.team_lead_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to view this retrospective"
                    )
    
    return retrospective

@router.post("/{retrospective_id}/generate")
async def generate_retrospective_content(
    retrospective_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered retrospective content"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate retrospective content"
        )
    
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    # Check permissions
    if current_user.role == "team_lead":
        if retrospective.team_id:
            team = db.query(Team).filter(Team.id == retrospective.team_id).first()
            if not team or team.team_lead_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to generate content for this retrospective"
                )
    
    analytics = AnalyticsService(db)
    
    # Gather data for the retrospective period
    team_id = retrospective.team_id
    project_id = retrospective.project_id
    
    if project_id and not team_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            team_id = project.team_id
    
    # Get project data
    project_data = {}
    if project_id:
        project_analytics = analytics.get_project_analytics(project_id)
        project_data = {
            "name": project_analytics.get("project_name", "Unknown"),
            "commits": project_analytics.get("code_metrics", {}).get("total_commits", 0),
            "pull_requests": project_analytics.get("code_metrics", {}).get("total_prs", 0),
            "issues_completed": project_analytics.get("task_metrics", {}).get("completed", 0),
            "issues_created": project_analytics.get("task_metrics", {}).get("total", 0)
        }
    
    # Get team data
    team_data = {}
    if team_id:
        team_analytics = analytics.get_team_analytics(team_id)
        team_data = {
            "members": team_analytics.get("members", []),
            "average_sentiment": team_analytics.get("aggregated_metrics", {}).get("average_sentiment", 0.5),
            "blocker_messages": team_analytics.get("aggregated_metrics", {}).get("blocker_count", 0)
        }
    
    # Time period data
    time_period = {
        "start": retrospective.period_start.isoformat(),
        "end": retrospective.period_end.isoformat()
    }
    
    # Generate retrospective using AI
    ai_retrospective = ai_service.generate_retrospective(project_data, team_data, time_period)
    
    # Update retrospective with generated content
    retrospective.summary = ai_retrospective.get("summary", "")
    retrospective.achievements = ai_retrospective.get("achievements", [])
    retrospective.challenges = ai_retrospective.get("challenges", [])
    retrospective.action_items = ai_retrospective.get("action_items", [])
    retrospective.metrics = ai_retrospective.get("metrics", {})
    
    db.commit()
    db.refresh(retrospective)
    
    return {
        "retrospective_id": retrospective_id,
        "generated_content": ai_retrospective,
        "status": "generated"
    }

@router.get("/{retrospective_id}/metrics", response_model=RetrospectiveMetrics)
async def get_retrospective_metrics(
    retrospective_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed metrics for a retrospective period"""
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    # Check permissions
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view retrospective metrics"
        )
    
    analytics = AnalyticsService(db)
    
    # Get team and project data
    team_id = retrospective.team_id
    project_id = retrospective.project_id
    
    if project_id and not team_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            team_id = project.team_id
    
    # Team performance metrics
    team_performance = {}
    if team_id:
        team_analytics = analytics.get_team_analytics(team_id)
        team_performance = {
            "team_size": team_analytics.get("team_size", 0),
            "total_commits": team_analytics.get("aggregated_metrics", {}).get("total_commits", 0),
            "total_prs": team_analytics.get("aggregated_metrics", {}).get("total_prs", 0),
            "tasks_completed": team_analytics.get("aggregated_metrics", {}).get("total_tasks_completed", 0),
            "average_sentiment": team_analytics.get("aggregated_metrics", {}).get("average_sentiment", 0.5)
        }
    
    # Project metrics
    project_metrics = {}
    if project_id:
        project_analytics = analytics.get_project_analytics(project_id)
        project_metrics = project_analytics
    
    # Sentiment analysis for the period
    sentiment_analysis = {}
    if team_id:
        from datetime import datetime, timedelta
        
        # Get team members
        team_members = db.query(User).join(TeamMember).filter(
            TeamMember.team_id == team_id
        ).all()
        
        # Analyze sentiment for each member during the period
        member_sentiment = []
        for member in team_members:
            from models import Message
            messages = db.query(Message).filter(
                Message.user_id == member.id,
                Message.message_date >= retrospective.period_start,
                Message.message_date <= retrospective.period_end
            ).all()
            
            if messages:
                avg_sentiment = sum(float(msg.sentiment_score or 0.5) for msg in messages) / len(messages)
                blocker_count = sum(1 for msg in messages if msg.is_blocker)
                
                member_sentiment.append({
                    "user_id": member.id,
                    "name": f"{member.first_name} {member.last_name}",
                    "sentiment": avg_sentiment,
                    "blockers": blocker_count
                })
        
        sentiment_analysis = {
            "team_sentiment": sum(m["sentiment"] for m in member_sentiment) / len(member_sentiment) if member_sentiment else 0.5,
            "members": member_sentiment,
            "total_blockers": sum(m["blockers"] for m in member_sentiment)
        }
    
    # Skill development analysis
    skill_development = {}
    if team_id:
        team_members = db.query(User).join(TeamMember).filter(
            TeamMember.team_id == team_id
        ).all()
        
        skill_changes = []
        for member in team_members:
            # This would ideally compare skills at the start vs end of the period
            # For now, we'll get current skills
            current_skills = analytics.calculate_user_skill_scores(member.id)
            skill_changes.append({
                "user_id": member.id,
                "name": f"{member.first_name} {member.last_name}",
                "skills": current_skills
            })
        
        skill_development = {
            "team_members": skill_changes
        }
    
    # Generate recommendations
    recommendations = [
        "Continue regular team retrospectives",
        "Focus on improving team communication",
        "Invest in skill development for identified gaps"
    ]
    
    if sentiment_analysis.get("team_sentiment", 0.5) < 0.4:
        recommendations.append("Address team sentiment issues through one-on-one meetings")
    
    if sentiment_analysis.get("total_blockers", 0) > 5:
        recommendations.append("Implement better blocker resolution processes")
    
    return RetrospectiveMetrics(
        period_start=retrospective.period_start,
        period_end=retrospective.period_end,
        team_performance=team_performance,
        project_metrics=project_metrics,
        sentiment_analysis=sentiment_analysis,
        skill_development=skill_development,
        recommendations=recommendations
    )

@router.put("/{retrospective_id}")
async def update_retrospective(
    retrospective_id: int,
    summary: Optional[str] = None,
    achievements: Optional[dict] = None,
    challenges: Optional[dict] = None,
    action_items: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update retrospective content"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update retrospectives"
        )
    
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    # Check permissions
    if current_user.role == "team_lead":
        if retrospective.team_id:
            team = db.query(Team).filter(Team.id == retrospective.team_id).first()
            if not team or team.team_lead_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this retrospective"
                )
    
    # Update fields
    if summary is not None:
        retrospective.summary = summary
    if achievements is not None:
        retrospective.achievements = achievements
    if challenges is not None:
        retrospective.challenges = challenges
    if action_items is not None:
        retrospective.action_items = action_items
    
    db.commit()
    db.refresh(retrospective)
    
    return {"message": "Retrospective updated successfully"}

@router.delete("/{retrospective_id}")
async def delete_retrospective(
    retrospective_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a retrospective"""
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete retrospectives"
        )
    
    retrospective = db.query(Retrospective).filter(Retrospective.id == retrospective_id).first()
    if not retrospective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retrospective not found"
        )
    
    db.delete(retrospective)
    db.commit()
    
    return {"message": "Retrospective deleted successfully"}
