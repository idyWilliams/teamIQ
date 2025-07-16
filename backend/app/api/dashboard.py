from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta

from models import User, Task, Project, Team, TeamMember, UserSkill, Skill, SkillAnalytics, SentimentAnalysis, get_db
from auth import get_current_user
from services.analytics_service import AnalyticsService

router = APIRouter()

class DashboardStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    active_projects: int
    team_members: int
    avg_sentiment: float
    skills_improved: int

class SkillSummary(BaseModel):
    name: str
    proficiency_level: int
    trend: str
    category: str

class TaskSummary(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    due_date: str = None
    project_name: str = None

class ProjectSummary(BaseModel):
    id: int
    name: str
    status: str
    completion_percentage: float
    team_name: str = None

class TeamMemberSummary(BaseModel):
    id: int
    full_name: str
    role: str
    sentiment_score: float
    productivity_score: float
    current_tasks: int

class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_tasks: List[TaskSummary]
    top_skills: List[SkillSummary]
    active_projects: List[ProjectSummary]
    team_members: List[TeamMemberSummary] = []
    sentiment_alerts: List[Dict[str, Any]] = []

@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user"""
    analytics_service = AnalyticsService()
    
    # Get user's tasks
    user_tasks = db.query(Task).filter(Task.assignee_id == current_user.id).all()
    completed_tasks = [t for t in user_tasks if t.status == 'done']
    
    # Get user's projects
    user_projects = db.query(Project).join(Team).join(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()
    
    active_projects = [p for p in user_projects if p.status == 'active']
    
    # Get team members if user is a team lead
    team_members = []
    if current_user.role in ['team_lead', 'admin', 'hr']:
        team_members = db.query(User).join(TeamMember).join(Team).filter(
            Team.lead_id == current_user.id
        ).all()
    
    # Get user's skills
    user_skills = db.query(UserSkill).join(Skill).filter(
        UserSkill.user_id == current_user.id
    ).all()
    
    # Get recent skill analytics
    recent_analytics = db.query(SkillAnalytics).filter(
        SkillAnalytics.user_id == current_user.id,
        SkillAnalytics.date >= datetime.now() - timedelta(days=30)
    ).all()
    
    skills_improved = len([a for a in recent_analytics if a.trend == 'up'])
    
    # Get sentiment data
    recent_sentiment = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.user_id == current_user.id,
        SentimentAnalysis.analyzed_at >= datetime.now() - timedelta(days=7)
    ).all()
    
    avg_sentiment = 0
    if recent_sentiment:
        avg_sentiment = sum(s.sentiment_score for s in recent_sentiment) / len(recent_sentiment)
    
    # Build response
    stats = DashboardStats(
        total_tasks=len(user_tasks),
        completed_tasks=len(completed_tasks),
        active_projects=len(active_projects),
        team_members=len(team_members),
        avg_sentiment=avg_sentiment,
        skills_improved=skills_improved
    )
    
    # Recent tasks
    recent_tasks = []
    for task in user_tasks[:10]:  # Last 10 tasks
        recent_tasks.append(TaskSummary(
            id=task.id,
            title=task.title,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date.isoformat() if task.due_date else None,
            project_name=task.project.name if task.project else None
        ))
    
    # Top skills
    top_skills = []
    for user_skill in user_skills[:5]:  # Top 5 skills
        # Get latest trend
        latest_analytics = db.query(SkillAnalytics).filter(
            SkillAnalytics.user_id == current_user.id,
            SkillAnalytics.skill_id == user_skill.skill_id
        ).order_by(desc(SkillAnalytics.date)).first()
        
        trend = latest_analytics.trend if latest_analytics else 'stable'
        
        top_skills.append(SkillSummary(
            name=user_skill.skill.name,
            proficiency_level=user_skill.proficiency_level,
            trend=trend,
            category=user_skill.skill.category
        ))
    
    # Active projects summary
    projects_summary = []
    for project in active_projects[:5]:  # Top 5 projects
        # Calculate completion percentage
        project_tasks = db.query(Task).filter(Task.project_id == project.id).all()
        completed_project_tasks = [t for t in project_tasks if t.status == 'done']
        completion_pct = (len(completed_project_tasks) / len(project_tasks) * 100) if project_tasks else 0
        
        projects_summary.append(ProjectSummary(
            id=project.id,
            name=project.name,
            status=project.status,
            completion_percentage=completion_pct,
            team_name=project.team.name if project.team else None
        ))
    
    # Team members summary (for team leads)
    team_members_summary = []
    if current_user.role in ['team_lead', 'admin', 'hr']:
        for member in team_members[:10]:  # Top 10 team members
            # Get member's current tasks
            member_tasks = db.query(Task).filter(
                Task.assignee_id == member.id,
                Task.status != 'done'
            ).count()
            
            # Get member's sentiment
            member_sentiment = db.query(SentimentAnalysis).filter(
                SentimentAnalysis.user_id == member.id,
                SentimentAnalysis.analyzed_at >= datetime.now() - timedelta(days=7)
            ).all()
            
            sentiment_score = 0
            if member_sentiment:
                sentiment_score = sum(s.sentiment_score for s in member_sentiment) / len(member_sentiment)
            
            # Simple productivity score calculation
            productivity_score = min(100, member_tasks * 10)
            
            team_members_summary.append(TeamMemberSummary(
                id=member.id,
                full_name=member.full_name,
                role=member.role,
                sentiment_score=sentiment_score,
                productivity_score=productivity_score,
                current_tasks=member_tasks
            ))
    
    return DashboardResponse(
        stats=stats,
        recent_tasks=recent_tasks,
        top_skills=top_skills,
        active_projects=projects_summary,
        team_members=team_members_summary
    )

@router.get("/analytics/{user_id}")
async def get_user_analytics(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ['admin', 'hr', 'team_lead']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    analytics_service = AnalyticsService()
    
    # Get comprehensive analytics
    user_analytics = await analytics_service.calculate_user_skill_scores(user_id, db)
    performance_report = await analytics_service.generate_performance_report(user_id, 30, db)
    
    return {
        "user_id": user_id,
        "skill_analytics": user_analytics,
        "performance_report": performance_report
    }

@router.get("/team-analytics/{team_id}")
async def get_team_analytics(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team analytics"""
    # Check if user has access to this team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check permissions
    if current_user.role not in ['admin', 'hr'] and team.lead_id != current_user.id:
        # Check if user is a member of this team
        membership = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    analytics_service = AnalyticsService()
    team_analytics = await analytics_service.get_team_analytics(team_id, db)
    
    return team_analytics

@router.get("/sentiment-alerts")
async def get_sentiment_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sentiment alerts for teams managed by current user"""
    if current_user.role not in ['team_lead', 'admin', 'hr']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    analytics_service = AnalyticsService()
    
    # Get teams managed by current user
    if current_user.role == 'team_lead':
        teams = db.query(Team).filter(Team.lead_id == current_user.id).all()
    else:
        teams = db.query(Team).all()
    
    all_alerts = []
    for team in teams:
        team_alerts = await analytics_service.detect_team_sentiment_alerts(team.id, db)
        all_alerts.extend(team_alerts)
    
    return {"alerts": all_alerts}

@router.get("/task-recommendations/{project_id}")
async def get_task_recommendations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task allocation recommendations for a project"""
    # Check permissions
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if current_user.role not in ['admin', 'team_lead'] and project.team.lead_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    analytics_service = AnalyticsService()
    recommendations = await analytics_service.generate_task_allocation_recommendations(project_id, db)
    
    return {"recommendations": recommendations}
