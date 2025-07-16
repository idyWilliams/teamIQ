from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from models import User, SentimentAnalysis, Team, TeamMember, get_db
from auth import get_current_user, require_role
from services.slack_service import SlackService
from services.ai_service import AIService

router = APIRouter()

class SentimentResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    platform: str
    sentiment_score: int
    confidence: int
    has_blockers: bool
    blocker_keywords: List[str]
    analyzed_at: datetime

class SentimentTrendResponse(BaseModel):
    user_id: int
    user_name: str
    trend_data: List[Dict[str, Any]]
    average_sentiment: float
    trend_direction: str
    blockers_count: int
    risk_level: str

class TeamSentimentResponse(BaseModel):
    team_id: int
    team_name: str
    average_sentiment: float
    sentiment_trend: str
    total_messages: int
    blockers_identified: int
    members_at_risk: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]

class SentimentAlertResponse(BaseModel):
    user_id: int
    user_name: str
    alert_type: str
    severity: str
    description: str
    sentiment_score: float
    blockers: List[str]
    recommendations: List[str]
    created_at: datetime

@router.get("/user/{user_id}", response_model=List[SentimentResponse])
async def get_user_sentiment(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30,
    platform: Optional[str] = None
):
    """Get sentiment analysis for a specific user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ['admin', 'hr', 'team_lead']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build query
    query = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.user_id == user_id,
        SentimentAnalysis.analyzed_at >= datetime.now() - timedelta(days=days)
    )
    
    if platform:
        query = query.filter(SentimentAnalysis.platform == platform)
    
    sentiment_data = query.order_by(desc(SentimentAnalysis.analyzed_at)).all()
    
    # Build response
    response = []
    for sentiment in sentiment_data:
        response.append(SentimentResponse(
            id=sentiment.id,
            user_id=sentiment.user_id,
            user_name=user.full_name,
            platform=sentiment.platform,
            sentiment_score=sentiment.sentiment_score,
            confidence=sentiment.confidence,
            has_blockers=sentiment.has_blockers,
            blocker_keywords=sentiment.blocker_keywords or [],
            analyzed_at=sentiment.analyzed_at
        ))
    
    return response

@router.get("/user/{user_id}/trend", response_model=SentimentTrendResponse)
async def get_user_sentiment_trend(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get sentiment trend for a specific user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ['admin', 'hr', 'team_lead']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get sentiment data
    sentiment_data = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.user_id == user_id,
        SentimentAnalysis.analyzed_at >= datetime.now() - timedelta(days=days)
    ).order_by(SentimentAnalysis.analyzed_at).all()
    
    if not sentiment_data:
        return SentimentTrendResponse(
            user_id=user_id,
            user_name=user.full_name,
            trend_data=[],
            average_sentiment=0.0,
            trend_direction="stable",
            blockers_count=0,
            risk_level="low"
        )
    
    # Process trend data
    trend_data = []
    daily_scores = {}
    
    for sentiment in sentiment_data:
        date_key = sentiment.analyzed_at.strftime("%Y-%m-%d")
        if date_key not in daily_scores:
            daily_scores[date_key] = []
        daily_scores[date_key].append(sentiment.sentiment_score)
    
    # Calculate daily averages
    for date, scores in daily_scores.items():
        avg_score = sum(scores) / len(scores)
        trend_data.append({
            "date": date,
            "sentiment_score": avg_score,
            "message_count": len(scores)
        })
    
    # Calculate overall metrics
    all_scores = [s.sentiment_score for s in sentiment_data]
    average_sentiment = sum(all_scores) / len(all_scores)
    
    # Calculate trend direction
    if len(trend_data) >= 2:
        first_half = trend_data[:len(trend_data)//2]
        second_half = trend_data[len(trend_data)//2:]
        
        first_avg = sum(d["sentiment_score"] for d in first_half) / len(first_half)
        second_avg = sum(d["sentiment_score"] for d in second_half) / len(second_half)
        
        if second_avg > first_avg + 10:
            trend_direction = "improving"
        elif second_avg < first_avg - 10:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "stable"
    
    # Count blockers
    blockers_count = sum(1 for s in sentiment_data if s.has_blockers)
    
    # Determine risk level
    if average_sentiment < -30 or blockers_count > 5:
        risk_level = "high"
    elif average_sentiment < -10 or blockers_count > 2:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return SentimentTrendResponse(
        user_id=user_id,
        user_name=user.full_name,
        trend_data=trend_data,
        average_sentiment=average_sentiment,
        trend_direction=trend_direction,
        blockers_count=blockers_count,
        risk_level=risk_level
    )

@router.get("/team/{team_id}", response_model=TeamSentimentResponse)
async def get_team_sentiment(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 7
):
    """Get sentiment analysis for a team"""
    # Check permissions
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    if current_user.role not in ['admin', 'hr'] and team.lead_id != current_user.id:
        # Check if user is member of this team
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ).first()
        
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Get team members
    team_members = db.query(User).join(TeamMember).filter(
        TeamMember.team_id == team_id
    ).all()
    
    member_ids = [member.id for member in team_members]
    
    # Get sentiment data for all team members
    sentiment_data = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.user_id.in_(member_ids),
        SentimentAnalysis.analyzed_at >= datetime.now() - timedelta(days=days)
    ).all()
    
    # Calculate team metrics
    if sentiment_data:
        total_messages = len(sentiment_data)
        average_sentiment = sum(s.sentiment_score for s in sentiment_data) / total_messages
        blockers_identified = sum(1 for s in sentiment_data if s.has_blockers)
    else:
        total_messages = 0
        average_sentiment = 0.0
        blockers_identified = 0
    
    # Determine sentiment trend
    if len(sentiment_data) >= 10:
        # Split data into two halves to calculate trend
        sorted_data = sorted(sentiment_data, key=lambda x: x.analyzed_at)
        first_half = sorted_data[:len(sorted_data)//2]
        second_half = sorted_data[len(sorted_data)//2:]
        
        first_avg = sum(s.sentiment_score for s in first_half) / len(first_half)
        second_avg = sum(s.sentiment_score for s in second_half) / len(second_half)
        
        if second_avg > first_avg + 10:
            sentiment_trend = "improving"
        elif second_avg < first_avg - 10:
            sentiment_trend = "declining"
        else:
            sentiment_trend = "stable"
    else:
        sentiment_trend = "stable"
    
    # Identify members at risk
    members_at_risk = []
    for member in team_members:
        member_sentiment = [s for s in sentiment_data if s.user_id == member.id]
        
        if member_sentiment:
            member_avg = sum(s.sentiment_score for s in member_sentiment) / len(member_sentiment)
            member_blockers = sum(1 for s in member_sentiment if s.has_blockers)
            
            if member_avg < -20 or member_blockers > 3:
                risk_level = "high" if member_avg < -40 else "medium"
                members_at_risk.append({
                    "user_id": member.id,
                    "user_name": member.full_name,
                    "average_sentiment": member_avg,
                    "blockers_count": member_blockers,
                    "risk_level": risk_level
                })
    
    # Get recent alerts (last 10 negative sentiment entries)
    recent_alerts = []
    negative_sentiment = [s for s in sentiment_data if s.sentiment_score < -20]
    recent_negative = sorted(negative_sentiment, key=lambda x: x.analyzed_at, reverse=True)[:10]
    
    for alert in recent_negative:
        member = next((m for m in team_members if m.id == alert.user_id), None)
        if member:
            recent_alerts.append({
                "user_id": alert.user_id,
                "user_name": member.full_name,
                "sentiment_score": alert.sentiment_score,
                "has_blockers": alert.has_blockers,
                "platform": alert.platform,
                "analyzed_at": alert.analyzed_at.isoformat()
            })
    
    return TeamSentimentResponse(
        team_id=team_id,
        team_name=team.name,
        average_sentiment=average_sentiment,
        sentiment_trend=sentiment_trend,
        total_messages=total_messages,
        blockers_identified=blockers_identified,
        members_at_risk=members_at_risk,
        recent_alerts=recent_alerts
    )

@router.get("/alerts", response_model=List[SentimentAlertResponse])
async def get_sentiment_alerts(
    current_user: User = Depends(require_role(['admin', 'hr', 'team_lead'])),
    db: Session = Depends(get_db),
    days: int = 7
):
    """Get sentiment alerts for teams managed by current user"""
    # Get teams based on user role
    if current_user.role == "team_lead":
        teams = db.query(Team).filter(Team.lead_id == current_user.id).all()
    else:
        teams = db.query(Team).all()
    
    alerts = []
    
    for team in teams:
        # Get team members
        team_members = db.query(User).join(TeamMember).filter(
            TeamMember.team_id == team.id
        ).all()
        
        member_ids = [member.id for member in team_members]
        
        # Get recent sentiment data
        sentiment_data = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.user_id.in_(member_ids),
            SentimentAnalysis.analyzed_at >= datetime.now() - timedelta(days=days)
        ).all()
        
        # Analyze each member
        for member in team_members:
            member_sentiment = [s for s in sentiment_data if s.user_id == member.id]
            
            if member_sentiment:
                avg_sentiment = sum(s.sentiment_score for s in member_sentiment) / len(member_sentiment)
                blockers = [s for s in member_sentiment if s.has_blockers]
                
                # Generate alerts based on conditions
                if avg_sentiment < -40:
                    alerts.append(SentimentAlertResponse(
                        user_id=member.id,
                        user_name=member.full_name,
                        alert_type="negative_sentiment",
                        severity="high",
                        description="Consistently negative sentiment detected",
                        sentiment_score=avg_sentiment,
                        blockers=[],
                        recommendations=[
                            "Schedule immediate 1:1 meeting",
                            "Consider workload reduction",
                            "Provide additional support"
                        ],
                        created_at=datetime.now()
                    ))
                elif avg_sentiment < -20:
                    alerts.append(SentimentAlertResponse(
                        user_id=member.id,
                        user_name=member.full_name,
                        alert_type="negative_sentiment",
                        severity="medium",
                        description="Declining sentiment trend",
                        sentiment_score=avg_sentiment,
                        blockers=[],
                        recommendations=[
                            "Schedule check-in meeting",
                            "Monitor workload",
                            "Offer mentorship"
                        ],
                        created_at=datetime.now()
                    ))
                
                if len(blockers) > 3:
                    # Get unique blocker keywords
                    all_blockers = []
                    for b in blockers:
                        if b.blocker_keywords:
                            all_blockers.extend(b.blocker_keywords)
                    
                    unique_blockers = list(set(all_blockers))
                    
                    alerts.append(SentimentAlertResponse(
                        user_id=member.id,
                        user_name=member.full_name,
                        alert_type="blockers_detected",
                        severity="high",
                        description="Multiple blockers identified",
                        sentiment_score=avg_sentiment,
                        blockers=unique_blockers,
                        recommendations=[
                            "Address technical blockers",
                            "Provide additional resources",
                            "Assign mentor for guidance"
                        ],
                        created_at=datetime.now()
                    ))
    
    # Sort alerts by severity (high first)
    alerts.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x.severity])
    
    return alerts

@router.post("/analyze-team/{team_id}")
async def analyze_team_sentiment(
    team_id: int,
    current_user: User = Depends(require_role(['admin', 'hr', 'team_lead'])),
    db: Session = Depends(get_db)
):
    """Trigger sentiment analysis for a team"""
    # Check permissions
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    if current_user.role == "team_lead" and team.lead_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Initialize services
        slack_service = SlackService()
        ai_service = AIService()
        
        # Get team channels (this would need to be configured per team)
        channels = ["general", "development"]  # This should come from team configuration
        
        # Analyze sentiment
        sentiment_overview = await slack_service.get_team_sentiment_overview(channels, since_days=7)
        
        # Store results in database
        team_members = db.query(User).join(TeamMember).filter(
            TeamMember.team_id == team_id
        ).all()
        
        for member in team_members:
            if member.username in sentiment_overview.get("user_sentiment", {}):
                user_data = sentiment_overview["user_sentiment"][member.username]
                
                # Create sentiment analysis record
                sentiment_record = SentimentAnalysis(
                    user_id=member.id,
                    platform="slack",
                    sentiment_score=int(user_data["avg_sentiment"]),
                    confidence=80,  # Default confidence
                    has_blockers=user_data.get("blockers", 0) > 0,
                    blocker_keywords=[],
                    analyzed_at=datetime.now()
                )
                
                db.add(sentiment_record)
        
        db.commit()
        
        return {
            "message": "Sentiment analysis completed successfully",
            "team_id": team_id,
            "analysis_results": sentiment_overview
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze sentiment: {str(e)}"
        )

@router.get("/platforms")
async def get_supported_platforms():
    """Get supported platforms for sentiment analysis"""
    return {
        "platforms": [
            {
                "name": "slack",
                "display_name": "Slack",
                "description": "Sentiment analysis from Slack messages",
                "enabled": True
            },
            {
                "name": "discord",
                "display_name": "Discord",
                "description": "Sentiment analysis from Discord messages",
                "enabled": False
            },
            {
                "name": "teams",
                "display_name": "Microsoft Teams",
                "description": "Sentiment analysis from Teams messages",
                "enabled": False
            }
        ]
    }

@router.get("/summary")
async def get_sentiment_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sentiment summary for current user's scope"""
    # Get relevant users based on role
    if current_user.role == "intern":
        # Only own sentiment
        relevant_users = [current_user.id]
    elif current_user.role == "team_lead":
        # Team members
        team_members = db.query(User).join(TeamMember).join(Team).filter(
            Team.lead_id == current_user.id
        ).all()
        relevant_users = [member.id for member in team_members]
    else:
        # All users
        all_users = db.query(User).all()
        relevant_users = [user.id for user in all_users]
    
    # Get recent sentiment data
    recent_sentiment = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.user_id.in_(relevant_users),
        SentimentAnalysis.analyzed_at >= datetime.now() - timedelta(days=7)
    ).all()
    
    # Calculate summary metrics
    total_analyzed = len(recent_sentiment)
    
    if total_analyzed > 0:
        avg_sentiment = sum(s.sentiment_score for s in recent_sentiment) / total_analyzed
        positive_count = len([s for s in recent_sentiment if s.sentiment_score > 20])
        negative_count = len([s for s in recent_sentiment if s.sentiment_score < -20])
        neutral_count = total_analyzed - positive_count - negative_count
        blockers_count = len([s for s in recent_sentiment if s.has_blockers])
    else:
        avg_sentiment = 0
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        blockers_count = 0
    
    # Users at risk
    users_at_risk = 0
    for user_id in relevant_users:
        user_sentiment = [s for s in recent_sentiment if s.user_id == user_id]
        if user_sentiment:
            user_avg = sum(s.sentiment_score for s in user_sentiment) / len(user_sentiment)
            user_blockers = sum(1 for s in user_sentiment if s.has_blockers)
            
            if user_avg < -20 or user_blockers > 2:
                users_at_risk += 1
    
    return {
        "total_analyzed": total_analyzed,
        "average_sentiment": avg_sentiment,
        "sentiment_distribution": {
            "positive": positive_count,
            "neutral": neutral_count,
            "negative": negative_count
        },
        "blockers_identified": blockers_count,
        "users_at_risk": users_at_risk,
        "analysis_period": "7 days"
    }
