from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
import logging
from datetime import datetime, timedelta

from auth import get_current_user, require_team_lead_or_above
from models.database import (
    get_dashboard_stats, get_team_dashboard_stats, get_user_skills,
    get_user_tasks, get_team_members, get_user_communications,
    get_team_communications, get_user_projects
)
from services.skill_analytics import skill_analytics
from services.sentiment_analysis import sentiment_service
from services.task_allocation import task_allocation_engine

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/intern")
async def get_intern_dashboard(current_user: dict = Depends(get_current_user)):
    """Get intern/engineer dashboard data."""
    try:
        if current_user["role"] not in ["intern", "engineer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This dashboard is only available for interns and engineers"
            )
        
        # Get basic stats
        stats = await get_dashboard_stats(current_user["id"])
        
        # Get user skills for skill snapshot
        user_skills = await get_user_skills(current_user["id"])
        skill_radar_data = skill_analytics.generate_skill_radar_data(user_skills)
        
        # Get recent tasks
        user_tasks = await get_user_tasks(current_user["id"])
        current_tasks = [t for t in user_tasks if t.get("status") in ["to_do", "in_progress"]]
        
        # Get user projects
        user_projects = await get_user_projects(current_user["id"])
        
        # Get recent communications for activity feed
        user_communications = await get_user_communications(current_user["id"], limit=10)
        
        # Calculate skill growth trends
        skill_growth = []
        for skill in user_skills[:5]:  # Top 5 skills
            growth_data = skill_analytics.calculate_skill_growth(
                current_user["id"], skill["id"], days=30
            )
            skill_growth.append({
                "skill_name": skill["name"],
                "current_level": skill["proficiency_level"],
                "growth_rate": growth_data.get("growth_rate", 0)
            })
        
        dashboard_data = {
            "user_info": {
                "name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
                "role": current_user.get("role"),
                "team_id": current_user.get("team_id")
            },
            "stats": stats,
            "skill_snapshot": {
                "radar_data": skill_radar_data,
                "top_skills": user_skills[:3],
                "skill_growth": skill_growth
            },
            "current_tasks": current_tasks[:5],
            "projects": user_projects,
            "recent_activities": stats.get("recent_activities", []),
            "upcoming_deadlines": [
                t for t in user_tasks 
                if t.get("due_date") and 
                datetime.fromisoformat(t["due_date"]) <= datetime.now() + timedelta(days=7)
            ]
        }
        
        return {
            "dashboard": dashboard_data,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting intern dashboard for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/team-lead")
async def get_team_lead_dashboard(current_user: dict = Depends(require_team_lead_or_above)):
    """Get team lead/manager dashboard data."""
    try:
        if not current_user.get("team_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not assigned to a team"
            )
        
        team_id = current_user["team_id"]
        
        # Get team stats
        team_stats = await get_team_dashboard_stats(team_id)
        
        # Get team members
        team_members = await get_team_members(team_id)
        
        # Get team skills matrix
        team_skills = []
        for member in team_members:
            member_skills = await get_user_skills(member["id"])
            team_skills.extend(member_skills)
        
        skill_matrix = skill_analytics.calculate_team_skill_matrix(team_members, team_skills)
        
        # Get team communications for sentiment analysis
        team_communications = await get_team_communications(team_id, limit=100)
        
        # Analyze team sentiment
        sentiment_analysis = await sentiment_service.analyze_team_sentiment(team_communications)
        
        # Get task allocation recommendations
        all_tasks = []
        for member in team_members:
            member_tasks = await get_user_tasks(member["id"])
            all_tasks.extend(member_tasks)
        
        unassigned_tasks = [t for t in all_tasks if not t.get("assignee_id")]
        
        allocation_recommendations = []
        if unassigned_tasks:
            allocation_recommendations = task_allocation_engine.allocate_tasks(
                unassigned_tasks, team_members, team_skills
            )
        
        # Calculate team health score
        team_health = {
            "overall_score": sentiment_analysis.get("team_health_score", 0.5),
            "sentiment_score": sentiment_analysis.get("team_average_sentiment", 0.5),
            "at_risk_count": len(sentiment_analysis.get("at_risk_members", [])),
            "blocker_count": sentiment_analysis.get("total_blockers", 0)
        }
        
        dashboard_data = {
            "team_info": {
                "team_id": team_id,
                "member_count": len(team_members),
                "lead_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
            },
            "team_stats": team_stats,
            "team_health": team_health,
            "skill_matrix": skill_matrix,
            "sentiment_overview": {
                "average_sentiment": sentiment_analysis.get("team_average_sentiment", 0.5),
                "trend": sentiment_analysis.get("team_sentiment_trend", "stable"),
                "at_risk_members": sentiment_analysis.get("at_risk_members", [])
            },
            "task_allocation": {
                "unassigned_tasks": len(unassigned_tasks),
                "recommendations": allocation_recommendations[:5]  # Top 5 recommendations
            },
            "team_members": team_members,
            "recent_blockers": [
                blocker for member_analysis in sentiment_analysis.get("user_analyses", {}).values()
                for blocker in member_analysis.get("recent_blockers", [])
            ][:10]
        }
        
        return {
            "dashboard": dashboard_data,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team lead dashboard for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/hr")
async def get_hr_dashboard(current_user: dict = Depends(get_current_user)):
    """Get HR dashboard data."""
    try:
        if current_user["role"] not in ["hr", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This dashboard is only available for HR personnel"
            )
        
        # In a real implementation, this would aggregate data across all teams
        # For now, we'll provide a basic structure
        
        dashboard_data = {
            "organization_stats": {
                "total_employees": 0,
                "active_teams": 0,
                "active_projects": 0,
                "avg_team_sentiment": 0.5
            },
            "talent_analytics": {
                "top_performers": [],
                "skill_gaps": [],
                "training_needs": []
            },
            "retention_insights": {
                "at_risk_employees": [],
                "retention_rate": 0,
                "attrition_predictions": []
            },
            "performance_trends": {
                "monthly_velocity": [],
                "completion_rates": [],
                "team_health_scores": []
            },
            "compliance_metrics": {
                "active_users": 0,
                "data_sync_status": "healthy",
                "last_audit": datetime.now().isoformat()
            }
        }
        
        return {
            "dashboard": dashboard_data,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting HR dashboard for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/recruiter")
async def get_recruiter_dashboard(current_user: dict = Depends(get_current_user)):
    """Get recruiter dashboard data."""
    try:
        if current_user["role"] not in ["recruiter", "hr", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This dashboard is only available for recruiters"
            )
        
        dashboard_data = {
            "candidate_pipeline": {
                "total_candidates": 0,
                "active_interviews": 0,
                "pending_offers": 0,
                "recent_hires": []
            },
            "skill_demand": {
                "top_demanded_skills": [],
                "skill_gap_analysis": [],
                "market_trends": []
            },
            "hiring_metrics": {
                "time_to_hire": 0,
                "offer_acceptance_rate": 0,
                "source_effectiveness": {}
            },
            "team_needs": {
                "open_positions": [],
                "skill_requirements": [],
                "urgent_hires": []
            },
            "candidate_profiles": {
                "top_candidates": [],
                "skill_matches": [],
                "diversity_metrics": {}
            }
        }
        
        return {
            "dashboard": dashboard_data,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recruiter dashboard for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/admin")
async def get_admin_dashboard(current_user: dict = Depends(get_current_user)):
    """Get admin dashboard data."""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This dashboard is only available for administrators"
            )
        
        dashboard_data = {
            "system_health": {
                "status": "healthy",
                "uptime": "99.9%",
                "active_users": 0,
                "api_response_time": "120ms"
            },
            "user_management": {
                "total_users": 0,
                "active_users": 0,
                "recent_registrations": [],
                "role_distribution": {}
            },
            "integration_status": {
                "github": {"status": "connected", "last_sync": datetime.now().isoformat()},
                "jira": {"status": "connected", "last_sync": datetime.now().isoformat()},
                "slack": {"status": "connected", "last_sync": datetime.now().isoformat()}
            },
            "data_analytics": {
                "total_projects": 0,
                "total_tasks": 0,
                "data_quality_score": 0.95,
                "storage_usage": "45%"
            },
            "security_metrics": {
                "failed_logins": 0,
                "security_events": [],
                "compliance_status": "compliant"
            },
            "performance_metrics": {
                "avg_response_time": 120,
                "error_rate": 0.1,
                "throughput": 1000
            }
        }
        
        return {
            "dashboard": dashboard_data,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting admin dashboard for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats/summary")
async def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    """Get dashboard summary based on user role."""
    try:
        if current_user["role"] in ["intern", "engineer"]:
            stats = await get_dashboard_stats(current_user["id"])
            return {"stats": stats, "success": True}
        
        elif current_user["role"] in ["team_lead", "manager"]:
            if current_user.get("team_id"):
                stats = await get_team_dashboard_stats(current_user["team_id"])
                return {"stats": stats, "success": True}
            else:
                return {"stats": {}, "success": True}
        
        else:
            # HR, Recruiter, Admin - return basic stats
            return {
                "stats": {
                    "total_users": 0,
                    "active_projects": 0,
                    "system_health": "healthy"
                },
                "success": True
            }
            
    except Exception as e:
        logger.error(f"Error getting dashboard summary for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
