from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from main import get_db, get_current_user
from models import User, Message, Team, TeamMember, Project
from services.analytics_service import AnalyticsService
from services.ai_service import ai_service

router = APIRouter()

class SentimentAnalysis(BaseModel):
    user_id: int
    user_name: str
    average_sentiment: float
    sentiment_trend: str  # "improving", "declining", "stable"
    blocker_count: int
    risk_level: str  # "low", "medium", "high"
    recent_messages: List[dict]

class TeamSentimentOverview(BaseModel):
    team_id: int
    team_name: str
    average_sentiment: float
    sentiment_distribution: dict
    at_risk_members: List[dict]
    blocker_summary: dict
    trend_analysis: dict

class SentimentAlert(BaseModel):
    id: int
    user_id: int
    user_name: str
    alert_type: str  # "low_sentiment", "blocker_detected", "pattern_change"
    severity: str  # "low", "medium", "high"
    message: str
    created_at: datetime
    is_acknowledged: bool

@router.get("/team/{team_id}/overview", response_model=TeamSentimentOverview)
async def get_team_sentiment_overview(
    team_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sentiment overview for a team"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view team sentiment"
        )
    
    # Get team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check if user can view this team
    if current_user.role == "team_lead" and team.team_lead_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this team's sentiment"
        )
    
    # Get team members
    team_members = db.query(User).join(TeamMember).filter(
        TeamMember.team_id == team_id
    ).all()
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Analyze sentiment for each member
    member_sentiments = []
    total_sentiment = 0
    sentiment_distribution = {"positive": 0, "neutral": 0, "negative": 0}
    at_risk_members = []
    total_blockers = 0
    
    for member in team_members:
        # Get messages for this member
        messages = db.query(Message).filter(
            Message.user_id == member.id,
            Message.message_date >= cutoff_date
        ).all()
        
        if messages:
            # Calculate average sentiment
            sentiment_scores = [float(msg.sentiment_score or 0.5) for msg in messages]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            # Count blockers
            blocker_count = sum(1 for msg in messages if msg.is_blocker)
            total_blockers += blocker_count
            
            # Determine risk level
            if avg_sentiment < 0.3 or blocker_count > 5:
                risk_level = "high"
            elif avg_sentiment < 0.4 or blocker_count > 2:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # Add to at-risk if necessary
            if risk_level in ["high", "medium"]:
                at_risk_members.append({
                    "user_id": member.id,
                    "user_name": f"{member.first_name} {member.last_name}",
                    "sentiment": avg_sentiment,
                    "blocker_count": blocker_count,
                    "risk_level": risk_level
                })
            
            # Update sentiment distribution
            if avg_sentiment > 0.6:
                sentiment_distribution["positive"] += 1
            elif avg_sentiment < 0.4:
                sentiment_distribution["negative"] += 1
            else:
                sentiment_distribution["neutral"] += 1
            
            total_sentiment += avg_sentiment
        else:
            # No messages - neutral sentiment
            sentiment_distribution["neutral"] += 1
            total_sentiment += 0.5
    
    # Calculate team average
    team_avg_sentiment = total_sentiment / len(team_members) if team_members else 0.5
    
    # Get trend analysis (compare with previous period)
    previous_cutoff = cutoff_date - timedelta(days=days)
    previous_messages = db.query(Message).join(User).join(TeamMember).filter(
        TeamMember.team_id == team_id,
        Message.message_date >= previous_cutoff,
        Message.message_date < cutoff_date
    ).all()
    
    if previous_messages:
        previous_avg = sum(float(msg.sentiment_score or 0.5) for msg in previous_messages) / len(previous_messages)
        sentiment_change = team_avg_sentiment - previous_avg
        
        if sentiment_change > 0.1:
            trend = "improving"
        elif sentiment_change < -0.1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
        sentiment_change = 0
    
    return TeamSentimentOverview(
        team_id=team_id,
        team_name=team.name,
        average_sentiment=team_avg_sentiment,
        sentiment_distribution=sentiment_distribution,
        at_risk_members=at_risk_members,
        blocker_summary={
            "total_blockers": total_blockers,
            "avg_per_member": total_blockers / len(team_members) if team_members else 0
        },
        trend_analysis={
            "trend": trend,
            "change": sentiment_change,
            "period_comparison": f"vs previous {days} days"
        }
    )

@router.get("/user/{user_id}/analysis", response_model=SentimentAnalysis)
async def get_user_sentiment_analysis(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed sentiment analysis for a user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user sentiment"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get user messages
    messages = db.query(Message).filter(
        Message.user_id == user_id,
        Message.message_date >= cutoff_date
    ).order_by(Message.message_date.desc()).all()
    
    if not messages:
        return SentimentAnalysis(
            user_id=user_id,
            user_name=f"{user.first_name} {user.last_name}",
            average_sentiment=0.5,
            sentiment_trend="stable",
            blocker_count=0,
            risk_level="low",
            recent_messages=[]
        )
    
    # Calculate sentiment metrics
    sentiment_scores = [float(msg.sentiment_score or 0.5) for msg in messages]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # Count blockers
    blocker_count = sum(1 for msg in messages if msg.is_blocker)
    
    # Determine trend
    if len(messages) >= 10:
        recent_half = sentiment_scores[:len(sentiment_scores)//2]
        older_half = sentiment_scores[len(sentiment_scores)//2:]
        
        recent_avg = sum(recent_half) / len(recent_half)
        older_avg = sum(older_half) / len(older_half)
        
        if recent_avg > older_avg + 0.1:
            trend = "improving"
        elif recent_avg < older_avg - 0.1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Determine risk level
    if avg_sentiment < 0.3 or blocker_count > 5:
        risk_level = "high"
    elif avg_sentiment < 0.4 or blocker_count > 2:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Format recent messages
    recent_messages = [
        {
            "id": msg.id,
            "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
            "sentiment_score": float(msg.sentiment_score or 0.5),
            "is_blocker": msg.is_blocker,
            "date": msg.message_date,
            "channel_id": msg.channel_id
        }
        for msg in messages[:10]
    ]
    
    return SentimentAnalysis(
        user_id=user_id,
        user_name=f"{user.first_name} {user.last_name}",
        average_sentiment=avg_sentiment,
        sentiment_trend=trend,
        blocker_count=blocker_count,
        risk_level=risk_level,
        recent_messages=recent_messages
    )

@router.get("/alerts")
async def get_sentiment_alerts(
    days: int = 7,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sentiment alerts for teams managed by current user"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view sentiment alerts"
        )
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    alerts = []
    
    # Get teams based on user role
    if current_user.role == "team_lead":
        teams = db.query(Team).filter(Team.team_lead_id == current_user.id).all()
    else:
        teams = db.query(Team).all()
    
    for team in teams:
        # Get team members
        team_members = db.query(User).join(TeamMember).filter(
            TeamMember.team_id == team.id
        ).all()
        
        for member in team_members:
            # Get recent messages
            messages = db.query(Message).filter(
                Message.user_id == member.id,
                Message.message_date >= cutoff_date
            ).all()
            
            if messages:
                # Calculate sentiment
                sentiment_scores = [float(msg.sentiment_score or 0.5) for msg in messages]
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                blocker_count = sum(1 for msg in messages if msg.is_blocker)
                
                # Generate alerts
                if avg_sentiment < 0.3:
                    alerts.append({
                        "id": f"sentiment_{member.id}_{int(datetime.utcnow().timestamp())}",
                        "user_id": member.id,
                        "user_name": f"{member.first_name} {member.last_name}",
                        "alert_type": "low_sentiment",
                        "severity": "high",
                        "message": f"User has very low sentiment score ({avg_sentiment:.2f})",
                        "created_at": datetime.utcnow(),
                        "is_acknowledged": False
                    })
                elif avg_sentiment < 0.4:
                    alerts.append({
                        "id": f"sentiment_{member.id}_{int(datetime.utcnow().timestamp())}",
                        "user_id": member.id,
                        "user_name": f"{member.first_name} {member.last_name}",
                        "alert_type": "low_sentiment",
                        "severity": "medium",
                        "message": f"User has low sentiment score ({avg_sentiment:.2f})",
                        "created_at": datetime.utcnow(),
                        "is_acknowledged": False
                    })
                
                if blocker_count > 3:
                    alerts.append({
                        "id": f"blocker_{member.id}_{int(datetime.utcnow().timestamp())}",
                        "user_id": member.id,
                        "user_name": f"{member.first_name} {member.last_name}",
                        "alert_type": "blocker_detected",
                        "severity": "high" if blocker_count > 5 else "medium",
                        "message": f"User has {blocker_count} blocker messages in the past {days} days",
                        "created_at": datetime.utcnow(),
                        "is_acknowledged": False
                    })
    
    # Filter by severity if specified
    if severity:
        alerts = [alert for alert in alerts if alert["severity"] == severity]
    
    return {"alerts": alerts}

@router.post("/analyze-message")
async def analyze_message_sentiment(
    message_content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze sentiment of a message using AI"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze messages"
        )
    
    # Use AI service to analyze sentiment
    analysis = ai_service.analyze_sentiment(message_content)
    
    return {
        "message": message_content,
        "sentiment_analysis": analysis,
        "timestamp": datetime.utcnow()
    }

@router.get("/project/{project_id}/sentiment")
async def get_project_sentiment(
    project_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sentiment analysis for a project team"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view project sentiment"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get team sentiment overview
    team_sentiment = await get_team_sentiment_overview(project.team_id, days, db, current_user)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "team_sentiment": team_sentiment,
        "analysis_period": f"{days} days"
    }

@router.get("/trends")
async def get_sentiment_trends(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization-wide sentiment trends"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view organization trends"
        )
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all messages in the period
    messages = db.query(Message).filter(
        Message.message_date >= cutoff_date,
        Message.sentiment_score.isnot(None)
    ).order_by(Message.message_date).all()
    
    # Group by week
    weekly_sentiment = {}
    weekly_blockers = {}
    
    for message in messages:
        week_key = message.message_date.strftime("%Y-W%U")
        
        if week_key not in weekly_sentiment:
            weekly_sentiment[week_key] = []
            weekly_blockers[week_key] = 0
        
        weekly_sentiment[week_key].append(float(message.sentiment_score))
        if message.is_blocker:
            weekly_blockers[week_key] += 1
    
    # Calculate averages
    trend_data = []
    for week in sorted(weekly_sentiment.keys()):
        avg_sentiment = sum(weekly_sentiment[week]) / len(weekly_sentiment[week])
        trend_data.append({
            "week": week,
            "average_sentiment": avg_sentiment,
            "blocker_count": weekly_blockers[week],
            "message_count": len(weekly_sentiment[week])
        })
    
    return {
        "period_days": days,
        "trend_data": trend_data,
        "summary": {
            "total_messages": len(messages),
            "total_blockers": sum(weekly_blockers.values()),
            "overall_sentiment": sum(float(msg.sentiment_score) for msg in messages) / len(messages) if messages else 0.5
        }
    }
