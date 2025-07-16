from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.skill import Skill, UserSkill
from app.schemas.skill import SkillCreate, SkillResponse, UserSkillResponse, UserSkillUpdate, SkillAnalytics

router = APIRouter()


@router.get("/", response_model=List[SkillResponse])
async def get_skills(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skills = db.query(Skill).offset(skip).limit(limit).all()
    return skills


@router.post("/", response_model=SkillResponse)
async def create_skill(
    skill: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"]))
):
    # Check if skill already exists
    existing_skill = db.query(Skill).filter(Skill.name == skill.name).first()
    if existing_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill with this name already exists"
        )
    
    # Create new skill
    db_skill = Skill(
        name=skill.name,
        category=skill.category,
        description=skill.description
    )
    
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    
    return db_skill


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    return skill


@router.get("/user/{user_id}", response_model=List[UserSkillResponse])
async def get_user_skills(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Users can only view their own skills unless they have elevated permissions
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.HR, UserRole.TEAM_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's skills"
        )
    
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    return user_skills


@router.put("/user/{user_id}/skill/{skill_id}", response_model=UserSkillResponse)
async def update_user_skill(
    user_id: int,
    skill_id: int,
    skill_update: UserSkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id
    ).first()
    
    if not user_skill:
        # Create new user skill if it doesn't exist
        user_skill = UserSkill(
            user_id=user_id,
            skill_id=skill_id,
            proficiency_score=skill_update.proficiency_score or 0.0,
            github_commits=skill_update.github_commits or 0,
            code_reviews=skill_update.code_reviews or 0,
            jira_tickets=skill_update.jira_tickets or 0,
            peer_reviews_score=skill_update.peer_reviews_score or 0.0
        )
        db.add(user_skill)
    else:
        # Update existing user skill
        for field, value in skill_update.dict(exclude_unset=True).items():
            setattr(user_skill, field, value)
    
    db.commit()
    db.refresh(user_skill)
    
    return user_skill


@router.get("/user/{user_id}/analytics", response_model=List[SkillAnalytics])
async def get_user_skill_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Users can only view their own analytics unless they have elevated permissions
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.HR, UserRole.TEAM_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's analytics"
        )
    
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    
    # Calculate analytics for each skill
    analytics = []
    for user_skill in user_skills:
        analytics.append(SkillAnalytics(
            skill_name=user_skill.skill.name,
            category=user_skill.skill.category.value,
            current_score=user_skill.proficiency_score,
            trend="stable",  # This would be calculated from historical data
            change_percentage=0.0,  # This would be calculated from historical data
            evidence_count=user_skill.github_commits + user_skill.code_reviews + user_skill.jira_tickets,
            last_activity=user_skill.last_updated
        ))
    
    return analytics


@router.delete("/user/{user_id}/skill/{skill_id}")
async def remove_user_skill(
    user_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id
    ).first()
    
    if not user_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User skill not found"
        )
    
    db.delete(user_skill)
    db.commit()
    
    return {"message": "User skill removed successfully"}
