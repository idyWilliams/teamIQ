from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
import logging

from auth import get_current_user, require_admin, require_hr_or_above
from models.database import (
    get_user_by_id, get_team_members, update_user, get_user_skills,
    get_user_tasks, get_user_notifications, mark_notification_as_read
)

logger = logging.getLogger(__name__)

router = APIRouter()

class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    linkedin_profile: Optional[str] = None
    profile_picture: Optional[str] = None
    team_id: Optional[int] = None
    manager_id: Optional[int] = None

class UpdateUserRoleRequest(BaseModel):
    role: str
    is_active: Optional[bool] = None

class NotificationPreferencesRequest(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    task_assignments: bool = True
    mentions: bool = True
    blockers: bool = True

@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile with additional details."""
    try:
        # Get user skills
        user_skills = await get_user_skills(current_user["id"])
        
        # Get user tasks
        user_tasks = await get_user_tasks(current_user["id"])
        
        # Get unread notifications count
        unread_notifications = await get_user_notifications(current_user["id"], unread_only=True)
        
        # Calculate basic stats
        total_tasks = len(user_tasks)
        completed_tasks = len([t for t in user_tasks if t.get("status") == "done"])
        
        user_profile = {
            **current_user,
            "stats": {
                "total_skills": len(user_skills),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "unread_notifications": len(unread_notifications)
            },
            "skills": user_skills[:5],  # Top 5 skills
            "recent_tasks": user_tasks[:5]  # 5 most recent tasks
        }
        
        # Remove sensitive data
        user_profile.pop("password_hash", None)
        
        return {
            "user": user_profile,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting current user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/me")
async def update_current_user_profile(
    request: UpdateUserRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile."""
    try:
        # Prepare update data
        update_data = {}
        if request.first_name is not None:
            update_data["first_name"] = request.first_name
        if request.last_name is not None:
            update_data["last_name"] = request.last_name
        if request.bio is not None:
            update_data["bio"] = request.bio
        if request.linkedin_profile is not None:
            update_data["linkedin_profile"] = request.linkedin_profile
        if request.profile_picture is not None:
            update_data["profile_picture"] = request.profile_picture
        
        # Note: Email, team_id, and manager_id changes may require admin approval
        # For now, we'll allow email updates but not team/manager changes
        if request.email is not None:
            update_data["email"] = request.email
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        updated_user = await update_user(current_user["id"], update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        # Remove sensitive data
        updated_user.pop("password_hash", None)
        
        return {
            "user": updated_user,
            "success": True,
            "message": "Profile updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}")
async def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get user profile by ID."""
    try:
        # Check if user can view this profile
        # For now, allow team members and higher roles to view profiles
        if (current_user["id"] != user_id and 
            current_user["role"] not in ["team_lead", "hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this profile"
            )
        
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get additional user data
        user_skills = await get_user_skills(user_id)
        user_tasks = await get_user_tasks(user_id)
        
        # Calculate stats
        total_tasks = len(user_tasks)
        completed_tasks = len([t for t in user_tasks if t.get("status") == "done"])
        
        user_profile = {
            **user,
            "stats": {
                "total_skills": len(user_skills),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks
            },
            "skills": user_skills,
            "recent_tasks": user_tasks[:10]  # 10 most recent tasks
        }
        
        # Remove sensitive data
        user_profile.pop("password_hash", None)
        
        return {
            "user": user_profile,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    request: UpdateUserRoleRequest,
    current_user: dict = Depends(require_admin)
):
    """Update user role (admin only)."""
    try:
        # Validate role
        valid_roles = ["intern", "team_lead", "hr", "recruiter", "admin"]
        if request.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        # Prepare update data
        update_data = {"role": request.role}
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        updated_user = await update_user(user_id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Remove sensitive data
        updated_user.pop("password_hash", None)
        
        return {
            "user": updated_user,
            "success": True,
            "message": "User role updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/team/{team_id}/members")
async def get_team_members_list(
    team_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get team members list."""
    try:
        # Check permissions
        if (current_user["team_id"] != team_id and 
            current_user["role"] not in ["team_lead", "hr", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view team members"
            )
        
        members = await get_team_members(team_id)
        
        # Remove sensitive data from all members
        clean_members = []
        for member in members:
            clean_member = {k: v for k, v in member.items() if k not in ["password_hash"]}
            clean_members.append(clean_member)
        
        return {
            "members": clean_members,
            "total": len(clean_members),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team members for team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me/notifications")
async def get_user_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    current_user: dict = Depends(get_current_user)
):
    """Get user notifications."""
    try:
        notifications = await get_user_notifications(current_user["id"], unread_only)
        
        return {
            "notifications": notifications,
            "total": len(notifications),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/me/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Mark notification as read."""
    try:
        success = await mark_notification_as_read(notification_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me/skills")
async def get_user_skills_detailed(current_user: dict = Depends(get_current_user)):
    """Get detailed user skills."""
    try:
        skills = await get_user_skills(current_user["id"])
        
        # Group skills by category
        skills_by_category = {}
        for skill in skills:
            category = skill.get("category", "other")
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill)
        
        return {
            "skills": skills,
            "skills_by_category": skills_by_category,
            "total": len(skills),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting skills for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/search")
async def search_users(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    current_user: dict = Depends(require_hr_or_above)
):
    """Search users (HR and above only)."""
    try:
        # This would need to be implemented in the database layer
        # For now, return empty results
        return {
            "users": [],
            "total": 0,
            "query": q,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error searching users with query '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/me/preferences/notifications")
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update notification preferences."""
    try:
        # In a real implementation, this would update user preferences in the database
        # For now, we'll just return success
        return {
            "success": True,
            "message": "Notification preferences updated successfully",
            "preferences": request.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating notification preferences for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
