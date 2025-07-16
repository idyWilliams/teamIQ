from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models import User, UserAnalytics, TeamAnalytics, SkillAnalytics
from auth import get_current_user, require_role
from services.analytics_service import analytics_service

router = APIRouter()

@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_user_analytics(
    user_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a specific user."""
    # Users can view their own analytics or authorized roles can view others
    if current_user.id != user_id and current_user.role not in ["admin", "team_lead", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's analytics"
        )
    
    try:
        # Mock user data - in production, fetch from database
        user_data = {
            "id": user_id,
            "username": f"user_{user_id}",
            "github_username": f"github_user_{user_id}",
            "jira_username": f"jira_user_{user_id}",
            "slack_user_id": f"U{user_id}SLACK",
            "slack_channel_id": "C123GENERAL"
        }
        
        analytics = await analytics_service.generate_user_analytics(user_id, user_data)
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )

@router.get("/team/{team_id}", response_model=Dict[str, Any])
async def get_team_analytics(
    team_id: int,
    days: int = 30,
    current_user: User = Depends(require_role(["admin", "team_lead", "hr"]))
):
    """Get analytics for a specific team."""
    try:
        # Mock team members data - in production, fetch from database
        team_members = [
            {
                "id": 1,
                "username": "john_doe",
                "github_username": "john-doe",
                "jira_username": "john.doe",
                "slack_user_id": "U123JOHN",
                "slack_channel_id": "C123GENERAL"
            },
            {
                "id": 2,
                "username": "jane_smith",
                "github_username": "jane-smith",
                "jira_username": "jane.smith",
                "slack_user_id": "U123JANE",
                "slack_channel_id": "C123GENERAL"
            }
        ]
        
        analytics = await analytics_service.generate_team_analytics(team_id, team_members)
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate team analytics: {str(e)}"
        )

@router.get("/user/{user_id}/skills", response_model=List[Dict[str, Any]])
async def get_user_skills(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get skill analytics for a user."""
    # Users can view their own skills or authorized roles can view others
    if current_user.id != user_id and current_user.role not in ["admin", "team_lead", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's skills"
        )
    
    # Mock skill data - in production, fetch from database
    skills = [
        {
            "skill_name": "Python",
            "category": "technical",
            "current_level": 8.5,
            "trend": "improving",
            "evidence_count": 15,
            "last_updated": datetime.now().isoformat(),
            "progression": [
                {"date": "2024-01-01", "level": 7.2},
                {"date": "2024-02-01", "level": 7.8},
                {"date": "2024-03-01", "level": 8.1},
                {"date": "2024-04-01", "level": 8.5}
            ]
        },
        {
            "skill_name": "React",
            "category": "technical",
            "current_level": 7.2,
            "trend": "stable",
            "evidence_count": 12,
            "last_updated": datetime.now().isoformat(),
            "progression": [
                {"date": "2024-01-01", "level": 6.8},
                {"date": "2024-02-01", "level": 7.0},
                {"date": "2024-03-01", "level": 7.1},
                {"date": "2024-04-01", "level": 7.2}
            ]
        },
        {
            "skill_name": "Communication",
            "category": "soft",
            "current_level": 6.8,
            "trend": "improving",
            "evidence_count": 8,
            "last_updated": datetime.now().isoformat(),
            "progression": [
                {"date": "2024-01-01", "level": 6.2},
                {"date": "2024-02-01", "level": 6.4},
                {"date": "2024-03-01", "level": 6.6},
                {"date": "2024-04-01", "level": 6.8}
            ]
        }
    ]
    
    return skills

@router.get("/user/{user_id}/skill/{skill_name}/progression")
async def get_skill_progression(
    user_id: int,
    skill_name: str,
    days: int = 90,
    current_user: User = Depends(get_current_user)
):
    """Get detailed skill progression for a user."""
    # Users can view their own progression or authorized roles can view others
    if current_user.id != user_id and current_user.role not in ["admin", "team_lead", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's skill progression"
        )
    
    try:
        progression = await analytics_service.generate_skill_progression(user_id, skill_name, days)
        return progression
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate skill progression: {str(e)}"
        )

@router.get("/sentiment/{user_id}")
async def get_user_sentiment(
    user_id: int,
    days: int = 30,
    current_user: User = Depends(require_role(["admin", "team_lead", "hr"]))
):
    """Get sentiment analysis for a user."""
    # Mock sentiment data - in production, fetch from database
    sentiment_data = {
        "user_id": user_id,
        "period_days": days,
        "overall_sentiment": 0.3,
        "sentiment_trend": "positive",
        "daily_sentiment": [
            {"date": "2024-01-01", "sentiment": 0.2},
            {"date": "2024-01-02", "sentiment": 0.4},
            {"date": "2024-01-03", "sentiment": 0.1},
            {"date": "2024-01-04", "sentiment": 0.6},
            {"date": "2024-01-05", "sentiment": 0.3}
        ],
        "emotions": {
            "joy": 0.4,
            "anger": 0.1,
            "fear": 0.0,
            "sadness": 0.2,
            "surprise": 0.3
        },
        "blockers": [
            {
                "date": "2024-01-03",
                "message": "Stuck on database connection issue",
                "severity": "medium"
            }
        ],
        "risk_level": "low"
    }
    
    return sentiment_data

@router.get("/team/{team_id}/sentiment")
async def get_team_sentiment(
    team_id: int,
    days: int = 30,
    current_user: User = Depends(require_role(["admin", "team_lead", "hr"]))
):
    """Get team sentiment analysis."""
    # Mock team sentiment data
    team_sentiment = {
        "team_id": team_id,
        "period_days": days,
        "overall_sentiment": 0.2,
        "sentiment_trend": "stable",
        "team_morale": "medium",
        "member_sentiments": [
            {"user_id": 1, "username": "john_doe", "sentiment": 0.3, "risk_level": "low"},
            {"user_id": 2, "username": "jane_smith", "sentiment": 0.1, "risk_level": "medium"}
        ],
        "at_risk_members": [
            {
                "user_id": 2,
                "username": "jane_smith",
                "risk_factors": ["Negative sentiment trend", "Frequent blockers"]
            }
        ],
        "recommendations": [
            {
                "type": "team_health",
                "priority": "medium",
                "action": "Schedule team check-in meeting"
            }
        ]
    }
    
    return team_sentiment

@router.get("/productivity/{user_id}")
async def get_user_productivity(
    user_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get productivity analytics for a user."""
    # Users can view their own productivity or authorized roles can view others
    if current_user.id != user_id and current_user.role not in ["admin", "team_lead", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's productivity"
        )
    
    # Mock productivity data
    productivity_data = {
        "user_id": user_id,
        "period_days": days,
        "overall_productivity": 0.75,
        "productivity_trend": "improving",
        "metrics": {
            "commits_per_day": 2.3,
            "prs_per_week": 1.2,
            "code_reviews_per_week": 3.5,
            "issue_completion_rate": 0.85,
            "avg_response_time_hours": 4.2
        },
        "daily_activity": [
            {"date": "2024-01-01", "commits": 3, "prs": 1, "reviews": 2},
            {"date": "2024-01-02", "commits": 2, "prs": 0, "reviews": 4},
            {"date": "2024-01-03", "commits": 1, "prs": 2, "reviews": 1}
        ],
        "comparison": {
            "vs_team_average": 0.12,  # 12% above team average
            "vs_previous_period": 0.08  # 8% improvement
        }
    }
    
    return productivity_data

@router.get("/dashboard-summary/{user_id}")
async def get_dashboard_summary(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get dashboard summary for a user."""
    # Users can view their own dashboard or authorized roles can view others
    if current_user.id != user_id and current_user.role not in ["admin", "team_lead", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this dashboard"
        )
    
    # Mock dashboard summary
    summary = {
        "user_id": user_id,
        "generated_at": datetime.now().isoformat(),
        "quick_stats": {
            "active_tasks": 5,
            "completed_this_week": 3,
            "overall_skill_score": 7.4,
            "sentiment_score": 0.3
        },
        "recent_achievements": [
            {
                "type": "skill_improvement",
                "title": "Python skill improved",
                "description": "Increased from 8.1 to 8.5",
                "date": "2024-01-04"
            },
            {
                "type": "task_completion",
                "title": "Completed major feature",
                "description": "User authentication module",
                "date": "2024-01-03"
            }
        ],
        "upcoming_deadlines": [
            {
                "task": "API documentation",
                "due_date": "2024-01-10",
                "priority": "high"
            },
            {
                "task": "Code review",
                "due_date": "2024-01-08",
                "priority": "medium"
            }
        ],
        "recommendations": [
            {
                "type": "skill_development",
                "title": "Consider learning TypeScript",
                "description": "Based on your React skills and team needs"
            }
        ]
    }
    
    return summary
