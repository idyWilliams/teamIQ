from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from main import get_db, get_current_user
from models import User, Skill, UserSkill
from services.analytics_service import AnalyticsService

router = APIRouter()

class SkillCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None

class SkillResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserSkillResponse(BaseModel):
    skill_id: int
    skill_name: str
    category: str
    proficiency_level: float
    evidence: Optional[dict] = None
    last_updated: datetime

class SkillProgressionResponse(BaseModel):
    skill_name: str
    current_level: float
    previous_level: float
    change_percentage: float
    trend: str  # "improving", "declining", "stable"
    evidence: Optional[dict] = None

@router.get("/", response_model=List[SkillResponse])
async def get_skills(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available skills, optionally filtered by category"""
    query = db.query(Skill)
    if category:
        query = query.filter(Skill.category == category)
    
    skills = query.all()
    return skills

@router.post("/", response_model=SkillResponse)
async def create_skill(
    skill: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new skill (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create skills"
        )
    
    # Check if skill already exists
    existing_skill = db.query(Skill).filter(Skill.name == skill.name).first()
    if existing_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill already exists"
        )
    
    new_skill = Skill(
        name=skill.name,
        category=skill.category,
        description=skill.description
    )
    
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    
    return new_skill

@router.get("/categories")
async def get_skill_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all skill categories"""
    categories = db.query(Skill.category).distinct().all()
    return [category[0] for category in categories]

@router.get("/user/{user_id}", response_model=List[UserSkillResponse])
async def get_user_skills(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get skills for a specific user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user skills"
        )
    
    user_skills = db.query(UserSkill).join(Skill).filter(
        UserSkill.user_id == user_id
    ).all()
    
    return [
        UserSkillResponse(
            skill_id=us.skill_id,
            skill_name=us.skill.name,
            category=us.skill.category,
            proficiency_level=float(us.proficiency_level),
            evidence=us.evidence,
            last_updated=us.last_updated
        )
        for us in user_skills
    ]

@router.get("/user/{user_id}/progression", response_model=List[SkillProgressionResponse])
async def get_user_skill_progression(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get skill progression for a user over time"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user skill progression"
        )
    
    analytics = AnalyticsService(db)
    
    # Get current skill scores
    current_skills = analytics.calculate_user_skill_scores(user_id, days)
    
    # Get previous skill scores for comparison
    previous_skills = analytics.calculate_user_skill_scores(user_id, days * 2)
    
    progression = []
    for skill_name, current_level in current_skills.items():
        previous_level = previous_skills.get(skill_name, 0)
        
        if previous_level > 0:
            change_percentage = ((current_level - previous_level) / previous_level) * 100
        else:
            change_percentage = 100 if current_level > 0 else 0
        
        if change_percentage > 5:
            trend = "improving"
        elif change_percentage < -5:
            trend = "declining"
        else:
            trend = "stable"
        
        progression.append(SkillProgressionResponse(
            skill_name=skill_name,
            current_level=current_level,
            previous_level=previous_level,
            change_percentage=change_percentage,
            trend=trend,
            evidence=None  # Could be enhanced with specific evidence
        ))
    
    return progression

@router.get("/analytics/{user_id}")
async def get_user_skill_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive skill analytics for a user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user analytics"
        )
    
    analytics = AnalyticsService(db)
    
    # Get skill scores and progression
    skill_scores = analytics.calculate_user_skill_scores(user_id)
    productivity_metrics = analytics.get_user_productivity_metrics(user_id)
    
    # Get user activity for AI analysis
    user_activity = {
        "commits": productivity_metrics["commits"],
        "pull_requests": productivity_metrics["pull_requests"],
        "tasks_completed": productivity_metrics["tasks_completed"],
        "lines_added": productivity_metrics["lines_added"],
        "skill_scores": skill_scores
    }
    
    # Use AI service for skill analysis
    from services.ai_service import ai_service
    ai_analysis = ai_service.analyze_skill_progression(user_activity)
    
    return {
        "skill_scores": skill_scores,
        "productivity_metrics": productivity_metrics,
        "ai_analysis": ai_analysis,
        "recommendations": ai_analysis.get("recommendations", [])
    }

@router.get("/team/{team_id}/matrix")
async def get_team_skill_matrix(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get skill matrix for a team"""
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view team skill matrix"
        )
    
    analytics = AnalyticsService(db)
    team_analytics = analytics.get_team_analytics(team_id)
    
    return {
        "team_id": team_id,
        "skill_distribution": team_analytics.get("skill_distribution", {}),
        "members": team_analytics.get("members", []),
        "skill_gaps": [],  # Could be enhanced with gap analysis
        "recommendations": []  # Could be enhanced with AI recommendations
    }

@router.put("/user/{user_id}/skill/{skill_id}")
async def update_user_skill(
    user_id: int,
    skill_id: int,
    proficiency_level: float,
    evidence: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user skill proficiency (admin/team_lead only)"""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update user skills"
        )
    
    if proficiency_level < 0 or proficiency_level > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proficiency level must be between 0 and 100"
        )
    
    # Check if skill exists
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update or create user skill
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id
    ).first()
    
    if user_skill:
        user_skill.proficiency_level = str(proficiency_level)
        user_skill.evidence = evidence
        user_skill.last_updated = datetime.utcnow()
    else:
        user_skill = UserSkill(
            user_id=user_id,
            skill_id=skill_id,
            proficiency_level=str(proficiency_level),
            evidence=evidence,
            last_updated=datetime.utcnow()
        )
        db.add(user_skill)
    
    db.commit()
    db.refresh(user_skill)
    
    return {"message": "User skill updated successfully"}
