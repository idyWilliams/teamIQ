from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from auth import get_current_user, require_team_lead_or_above
from models.database import (
    get_user_skills, get_skills_by_category, get_team_members,
    get_user_by_id
)
from services.skill_analytics import skill_analytics

logger = logging.getLogger(__name__)

router = APIRouter()

class SkillAssessmentRequest(BaseModel):
    skill_id: int
    proficiency_level: float
    notes: Optional[str] = None

class SkillGapAnalysisRequest(BaseModel):
    project_requirements: List[dict]
    team_id: Optional[int] = None

@router.get("/me")
async def get_my_skills(current_user: dict = Depends(get_current_user)):
    """Get current user's skills."""
    try:
        skills = await get_user_skills(current_user["id"])
        
        # Group skills by category
        skills_by_category = {}
        for skill in skills:
            category = skill.get("category", "other")
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill)
        
        # Generate radar chart data
        radar_data = skill_analytics.generate_skill_radar_data(skills)
        
        # Calculate skill statistics
        total_skills = len(skills)
        avg_proficiency = sum(s.get("proficiency_level", 0) for s in skills) / total_skills if total_skills > 0 else 0
        
        # Get top skills
        top_skills = sorted(skills, key=lambda x: x.get("proficiency_level", 0), reverse=True)[:5]
        
        return {
            "skills": skills,
            "skills_by_category": skills_by_category,
            "radar_data": radar_data,
            "statistics": {
                "total_skills": total_skills,
                "average_proficiency": avg_proficiency,
                "top_skills": top_skills
            },
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting skills for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/user/{user_id}")
async def get_user_skills_by_id(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get skills for a specific user."""
    try:
        # Check permissions
        if (current_user["id"] != user_id and 
            current_user["role"] not in ["team_lead", "hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user skills"
            )
        
        # Verify user exists
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        skills = await get_user_skills(user_id)
        
        # Generate radar chart data
        radar_data = skill_analytics.generate_skill_radar_data(skills)
        
        # Calculate skill growth for the last 30 days
        skill_growth = []
        for skill in skills[:10]:  # Top 10 skills
            growth_data = skill_analytics.calculate_skill_growth(
                user_id, skill["id"], days=30
            )
            skill_growth.append({
                "skill_id": skill["id"],
                "skill_name": skill["name"],
                "current_level": skill["proficiency_level"],
                "growth_rate": growth_data.get("growth_rate", 0),
                "trend": growth_data.get("growth_trend", "stable")
            })
        
        return {
            "user_id": user_id,
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            "skills": skills,
            "radar_data": radar_data,
            "skill_growth": skill_growth,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skills for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/team/{team_id}")
async def get_team_skills(
    team_id: int,
    current_user: dict = Depends(require_team_lead_or_above)
):
    """Get skills overview for a team."""
    try:
        # Check if user has access to this team
        if (current_user["team_id"] != team_id and 
            current_user["role"] not in ["hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view team skills"
            )
        
        # Get team members
        team_members = await get_team_members(team_id)
        
        if not team_members:
            return {
                "team_id": team_id,
                "members": [],
                "skills_matrix": {"skills": [], "members": [], "data": []},
                "skill_distribution": {},
                "success": True
            }
        
        # Get all team skills
        all_skills = []
        member_skills_map = {}
        
        for member in team_members:
            member_skills = await get_user_skills(member["id"])
            all_skills.extend(member_skills)
            member_skills_map[member["id"]] = member_skills
        
        # Calculate team skills matrix
        skills_matrix = skill_analytics.calculate_team_skill_matrix(team_members, all_skills)
        
        # Calculate skill distribution
        skill_distribution = {}
        for skill in all_skills:
            skill_name = skill.get("name")
            proficiency = skill.get("proficiency_level", 0)
            
            if skill_name not in skill_distribution:
                skill_distribution[skill_name] = {
                    "beginner": 0,
                    "intermediate": 0,
                    "advanced": 0,
                    "expert": 0
                }
            
            if proficiency < 2:
                skill_distribution[skill_name]["beginner"] += 1
            elif proficiency < 3:
                skill_distribution[skill_name]["intermediate"] += 1
            elif proficiency < 4:
                skill_distribution[skill_name]["advanced"] += 1
            else:
                skill_distribution[skill_name]["expert"] += 1
        
        # Get skill recommendations for team
        recommendations = skill_analytics.generate_skill_recommendations([], all_skills)
        
        return {
            "team_id": team_id,
            "members": team_members,
            "skills_matrix": skills_matrix,
            "skill_distribution": skill_distribution,
            "recommendations": recommendations,
            "total_skills": len(set(s.get("name") for s in all_skills)),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team skills for team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/categories")
async def get_skill_categories(current_user: dict = Depends(get_current_user)):
    """Get available skill categories."""
    try:
        categories = ["technical", "soft", "domain", "leadership", "communication"]
        
        # Get skills count by category
        category_counts = {}
        for category in categories:
            skills = await get_skills_by_category(category)
            category_counts[category] = len(skills)
        
        return {
            "categories": categories,
            "category_counts": category_counts,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting skill categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/category/{category}")
async def get_skills_by_category_endpoint(
    category: str,
    current_user: dict = Depends(get_current_user)
):
    """Get skills by category."""
    try:
        skills = await get_skills_by_category(category)
        
        return {
            "category": category,
            "skills": skills,
            "total": len(skills),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting skills by category {category}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/analytics/growth")
async def get_skill_growth_analytics(
    user_id: Optional[int] = Query(None, description="User ID (defaults to current user)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get skill growth analytics."""
    try:
        target_user_id = user_id or current_user["id"]
        
        # Check permissions
        if (target_user_id != current_user["id"] and 
            current_user["role"] not in ["team_lead", "hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view skill analytics"
            )
        
        # Get user skills
        user_skills = await get_user_skills(target_user_id)
        
        # Calculate growth for each skill
        growth_analytics = []
        for skill in user_skills:
            growth_data = skill_analytics.calculate_skill_growth(
                target_user_id, skill["id"], days
            )
            growth_analytics.append({
                "skill_id": skill["id"],
                "skill_name": skill["name"],
                "category": skill.get("category", "other"),
                "current_level": skill["proficiency_level"],
                "previous_level": growth_data.get("previous_level", skill["proficiency_level"]),
                "growth_rate": growth_data.get("growth_rate", 0),
                "trend": growth_data.get("growth_trend", "stable"),
                "key_contributors": growth_data.get("key_contributors", [])
            })
        
        # Sort by growth rate
        growth_analytics.sort(key=lambda x: x["growth_rate"], reverse=True)
        
        return {
            "user_id": target_user_id,
            "analysis_period_days": days,
            "skill_growth": growth_analytics,
            "summary": {
                "total_skills": len(user_skills),
                "improving_skills": len([s for s in growth_analytics if s["growth_rate"] > 0]),
                "declining_skills": len([s for s in growth_analytics if s["growth_rate"] < 0]),
                "avg_growth_rate": sum(s["growth_rate"] for s in growth_analytics) / len(growth_analytics) if growth_analytics else 0
            },
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill growth analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/gap-analysis")
async def analyze_skill_gaps(
    request: SkillGapAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze skill gaps for project requirements."""
    try:
        # Get user skills (or team skills if team_id provided)
        if request.team_id:
            # Check permissions for team analysis
            if (current_user["team_id"] != request.team_id and 
                current_user["role"] not in ["team_lead", "hr", "admin"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to analyze team skills"
                )
            
            # Get team skills
            team_members = await get_team_members(request.team_id)
            all_skills = []
            for member in team_members:
                member_skills = await get_user_skills(member["id"])
                all_skills.extend(member_skills)
            
            # Analyze gaps for team
            gaps = skill_analytics.analyze_skill_gaps(all_skills, request.project_requirements)
            
            return {
                "analysis_type": "team",
                "team_id": request.team_id,
                "skill_gaps": gaps,
                "total_gaps": len(gaps),
                "success": True
            }
        else:
            # Analyze gaps for current user
            user_skills = await get_user_skills(current_user["id"])
            gaps = skill_analytics.analyze_skill_gaps(user_skills, request.project_requirements)
            
            return {
                "analysis_type": "user",
                "user_id": current_user["id"],
                "skill_gaps": gaps,
                "total_gaps": len(gaps),
                "success": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/recommendations")
async def get_skill_recommendations(
    user_id: Optional[int] = Query(None, description="User ID (defaults to current user)"),
    current_user: dict = Depends(get_current_user)
):
    """Get skill development recommendations."""
    try:
        target_user_id = user_id or current_user["id"]
        
        # Check permissions
        if (target_user_id != current_user["id"] and 
            current_user["role"] not in ["team_lead", "hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view skill recommendations"
            )
        
        # Get user skills
        user_skills = await get_user_skills(target_user_id)
        
        # Get team skills for comparison (if user is in a team)
        team_skills = []
        user = await get_user_by_id(target_user_id)
        if user and user.get("team_id"):
            team_members = await get_team_members(user["team_id"])
            for member in team_members:
                member_skills = await get_user_skills(member["id"])
                team_skills.extend(member_skills)
        
        # Generate recommendations
        recommendations = skill_analytics.generate_skill_recommendations(user_skills, team_skills)
        
        return {
            "user_id": target_user_id,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/search")
async def search_skills(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: dict = Depends(get_current_user)
):
    """Search skills by name or category."""
    try:
        # This would need to be implemented in the database layer
        # For now, return empty results
        return {
            "query": q,
            "category": category,
            "skills": [],
            "total": 0,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error searching skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
