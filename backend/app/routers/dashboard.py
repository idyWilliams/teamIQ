from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime, timedelta

from main import get_db, get_current_user
from models import User, Task, Commit, PullRequest, Message, Team, TeamMember, Project
from services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get role-specific dashboard data"""
    analytics = AnalyticsService(db)
    
    if current_user.role in ["intern", "engineer"]:
        return await get_intern_dashboard(current_user, db, analytics)
    elif current_user.role == "team_lead":
        return await get_team_lead_dashboard(current_user, db, analytics)
    elif current_user.role == "hr":
        return await get_hr_dashboard(current_user, db, analytics)
    elif current_user.role == "admin":
        return await get_admin_dashboard(current_user, db, analytics)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user role"
        )

async def get_intern_dashboard(user: User, db: Session, analytics: AnalyticsService) -> Dict:
    """Get dashboard data for intern/engineer"""
    # Get user's current tasks
    current_tasks = db.query(Task).filter(
        Task.assignee_id == user.id,
        Task.status.in_(["To Do", "In Progress", "In Review"])
    ).limit(5).all()
    
    # Get recent activity
    recent_commits = db.query(Commit).filter(
        Commit.user_id == user.id
    ).order_by(Commit.commit_date.desc()).limit(5).all()
    
    recent_prs = db.query(PullRequest).filter(
        PullRequest.author_id == user.id
    ).order_by(PullRequest.created_at.desc()).limit(5).all()
    
    # Get skill scores
    skill_scores = analytics.calculate_user_skill_scores(user.id)
    
    # Get productivity metrics
    productivity = analytics.get_user_productivity_metrics(user.id)
    
    # Get upcoming deadlines
    upcoming_deadlines = db.query(Task).filter(
        Task.assignee_id == user.id,
        Task.due_date.isnot(None),
        Task.due_date > datetime.utcnow(),
        Task.status.notin_(["Done", "Resolved", "Closed"])
    ).order_by(Task.due_date).limit(5).all()
    
    return {
        "user_info": {
            "id": user.id,
            "name": f"{user.first_name} {user.last_name}",
            "role": user.role
        },
        "skill_snapshot": {
            "top_skills": dict(list(skill_scores.items())[:3]),
            "total_skills": len(skill_scores)
        },
        "current_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date
            } for task in current_tasks
        ],
        "recent_activity": {
            "commits": [
                {
                    "sha": commit.sha[:8],
                    "message": commit.message,
                    "date": commit.commit_date,
                    "additions": commit.additions,
                    "deletions": commit.deletions
                } for commit in recent_commits
            ],
            "pull_requests": [
                {
                    "id": pr.external_id,
                    "title": pr.title,
                    "status": pr.status,
                    "created_at": pr.created_at
                } for pr in recent_prs
            ]
        },
        "upcoming_deadlines": [
            {
                "id": task.id,
                "title": task.title,
                "due_date": task.due_date,
                "priority": task.priority
            } for task in upcoming_deadlines
        ],
        "productivity_metrics": productivity
    }

async def get_team_lead_dashboard(user: User, db: Session, analytics: AnalyticsService) -> Dict:
    """Get dashboard data for team lead"""
    # Get teams led by this user
    teams = db.query(Team).filter(Team.team_lead_id == user.id).all()
    
    if not teams:
        return {"error": "No teams found for this team lead"}
    
    # For now, use the first team
    team = teams[0]
    
    # Get team analytics
    team_analytics = analytics.get_team_analytics(team.id)
    
    # Get team projects
    projects = db.query(Project).filter(Project.team_id == team.id).all()
    
    # Get recent team activity
    team_member_ids = [member["id"] for member in team_analytics["members"]]
    
    recent_commits = db.query(Commit).filter(
        Commit.user_id.in_(team_member_ids)
    ).order_by(Commit.commit_date.desc()).limit(10).all()
    
    # Get sentiment issues
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    at_risk_members = []
    
    for member in team_analytics["members"]:
        if member["sentiment"] < 0.4 or member["blockers"] > 2:
            at_risk_members.append({
                "id": member["id"],
                "name": member["name"],
                "sentiment": member["sentiment"],
                "blockers": member["blockers"],
                "risk_level": "high" if member["sentiment"] < 0.3 else "medium"
            })
    
    return {
        "team_info": {
            "id": team.id,
            "name": team.name,
            "size": team_analytics["team_size"]
        },
        "team_metrics": team_analytics["aggregated_metrics"],
        "skill_matrix": team_analytics["skill_distribution"],
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "start_date": project.start_date,
                "end_date": project.end_date
            } for project in projects
        ],
        "at_risk_members": at_risk_members,
        "recent_activity": [
            {
                "user_id": commit.user_id,
                "type": "commit",
                "message": commit.message,
                "date": commit.commit_date
            } for commit in recent_commits
        ],
        "team_members": team_analytics["members"]
    }

async def get_hr_dashboard(user: User, db: Session, analytics: AnalyticsService) -> Dict:
    """Get dashboard data for HR personnel"""
    # Get all users
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Get role distribution
    role_distribution = db.query(User.role, db.func.count(User.id)).group_by(User.role).all()
    
    # Get recent hires (last 30 days)
    recent_hires = db.query(User).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Get users with low sentiment (potential attrition risk)
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    # This is a simplified query - in production, you'd want more sophisticated analysis
    users_with_messages = db.query(User).join(Message).filter(
        Message.message_date >= cutoff_date
    ).distinct().all()
    
    at_risk_users = []
    for user_obj in users_with_messages:
        avg_sentiment = db.query(db.func.avg(Message.sentiment_score)).filter(
            Message.user_id == user_obj.id,
            Message.message_date >= cutoff_date
        ).scalar()
        
        if avg_sentiment and avg_sentiment < 0.4:
            at_risk_users.append({
                "id": user_obj.id,
                "name": f"{user_obj.first_name} {user_obj.last_name}",
                "role": user_obj.role,
                "sentiment": float(avg_sentiment)
            })
    
    # Get top performers
    top_performers = []
    for user_obj in users_with_messages[:10]:  # Limit to 10 for performance
        productivity = analytics.get_user_productivity_metrics(user_obj.id)
        if productivity["commits"] > 0 or productivity["tasks_completed"] > 0:
            top_performers.append({
                "id": user_obj.id,
                "name": f"{user_obj.first_name} {user_obj.last_name}",
                "role": user_obj.role,
                "productivity": productivity
            })
    
    # Sort by productivity score (simple heuristic)
    top_performers.sort(
        key=lambda x: x["productivity"]["commits"] + x["productivity"]["tasks_completed"],
        reverse=True
    )
    
    return {
        "overview": {
            "total_employees": total_users,
            "active_employees": active_users,
            "recent_hires": recent_hires,
            "role_distribution": dict(role_distribution)
        },
        "talent_analytics": {
            "at_risk_employees": at_risk_users[:10],
            "top_performers": top_performers[:10]
        },
        "retention_metrics": {
            "attrition_risk_count": len(at_risk_users),
            "average_sentiment": sum(user["sentiment"] for user in at_risk_users) / len(at_risk_users) if at_risk_users else 0.5
        }
    }

async def get_admin_dashboard(user: User, db: Session, analytics: AnalyticsService) -> Dict:
    """Get dashboard data for admin"""
    # System metrics
    total_users = db.query(User).count()
    total_teams = db.query(Team).count()
    total_projects = db.query(Project).count()
    
    # Recent activity
    recent_commits = db.query(Commit).order_by(Commit.commit_date.desc()).limit(10).all()
    recent_tasks = db.query(Task).order_by(Task.updated_at.desc()).limit(10).all()
    
    # User activity in last 30 days
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(User).join(Commit).filter(
        Commit.commit_date >= cutoff_date
    ).distinct().count()
    
    return {
        "system_overview": {
            "total_users": total_users,
            "total_teams": total_teams,
            "total_projects": total_projects,
            "active_users_30d": active_users
        },
        "recent_activity": {
            "commits": [
                {
                    "sha": commit.sha[:8],
                    "message": commit.message,
                    "user_id": commit.user_id,
                    "date": commit.commit_date
                } for commit in recent_commits
            ],
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "assignee_id": task.assignee_id,
                    "updated_at": task.updated_at
                } for task in recent_tasks
            ]
        },
        "user_role": user.role
    }
