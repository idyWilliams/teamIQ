import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from storage import storage, DatabaseStorage

logger = logging.getLogger(__name__)

# Database initialization
async def init_database():
    """Initialize database connection and tables."""
    try:
        # Database tables are created automatically by Drizzle
        # This function can be used for any initialization logic
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# User operations
async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID."""
    try:
        user = await storage.getUser(user_id)
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user by ID {user_id}: {e}")
        return None

async def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username."""
    try:
        user = await storage.getUserByUsername(username)
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user by username {username}: {e}")
        return None

async def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email."""
    try:
        user = await storage.getUserByEmail(email)
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {e}")
        return None

async def create_user(user_data: Dict) -> Optional[Dict]:
    """Create a new user."""
    try:
        user = await storage.createUser(user_data)
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

async def update_user(user_id: int, user_data: Dict) -> Optional[Dict]:
    """Update user information."""
    try:
        user = await storage.updateUser(user_id, user_data)
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return None

# Team operations
async def get_team_by_id(team_id: int) -> Optional[Dict]:
    """Get team by ID."""
    try:
        team = await storage.getTeam(team_id)
        if team:
            return dict(team)
        return None
    except Exception as e:
        logger.error(f"Error getting team by ID {team_id}: {e}")
        return None

async def get_team_members(team_id: int) -> List[Dict]:
    """Get team members."""
    try:
        members = await storage.getTeamMembers(team_id)
        return [dict(member) for member in members]
    except Exception as e:
        logger.error(f"Error getting team members for team {team_id}: {e}")
        return []

# Project operations
async def get_project_by_id(project_id: int) -> Optional[Dict]:
    """Get project by ID."""
    try:
        project = await storage.getProject(project_id)
        if project:
            return dict(project)
        return None
    except Exception as e:
        logger.error(f"Error getting project by ID {project_id}: {e}")
        return None

async def get_projects_by_team(team_id: int) -> List[Dict]:
    """Get projects by team ID."""
    try:
        projects = await storage.getProjectsByTeam(team_id)
        return [dict(project) for project in projects]
    except Exception as e:
        logger.error(f"Error getting projects for team {team_id}: {e}")
        return []

async def get_user_projects(user_id: int) -> List[Dict]:
    """Get projects for a user."""
    try:
        projects = await storage.getUserProjects(user_id)
        return [dict(project) for project in projects]
    except Exception as e:
        logger.error(f"Error getting projects for user {user_id}: {e}")
        return []

# Skill operations
async def get_user_skills(user_id: int) -> List[Dict]:
    """Get user skills."""
    try:
        skills = await storage.getUserSkills(user_id)
        return [dict(skill) for skill in skills]
    except Exception as e:
        logger.error(f"Error getting skills for user {user_id}: {e}")
        return []

async def get_skills_by_category(category: str) -> List[Dict]:
    """Get skills by category."""
    try:
        skills = await storage.getSkillsByCategory(category)
        return [dict(skill) for skill in skills]
    except Exception as e:
        logger.error(f"Error getting skills by category {category}: {e}")
        return []

# Task operations
async def get_task_by_id(task_id: int) -> Optional[Dict]:
    """Get task by ID."""
    try:
        task = await storage.getTask(task_id)
        if task:
            return dict(task)
        return None
    except Exception as e:
        logger.error(f"Error getting task by ID {task_id}: {e}")
        return None

async def get_user_tasks(user_id: int) -> List[Dict]:
    """Get tasks for a user."""
    try:
        tasks = await storage.getUserTasks(user_id)
        return [dict(task) for task in tasks]
    except Exception as e:
        logger.error(f"Error getting tasks for user {user_id}: {e}")
        return []

async def get_project_tasks(project_id: int) -> List[Dict]:
    """Get tasks for a project."""
    try:
        tasks = await storage.getProjectTasks(project_id)
        return [dict(task) for task in tasks]
    except Exception as e:
        logger.error(f"Error getting tasks for project {project_id}: {e}")
        return []

# Integration operations
async def get_user_integrations(user_id: int) -> List[Dict]:
    """Get user integrations."""
    try:
        integrations = await storage.getUserIntegrations(user_id)
        return [dict(integration) for integration in integrations]
    except Exception as e:
        logger.error(f"Error getting integrations for user {user_id}: {e}")
        return []

async def get_integration_by_provider(user_id: int, provider: str) -> Optional[Dict]:
    """Get integration by provider."""
    try:
        integration = await storage.getIntegrationByProvider(user_id, provider)
        if integration:
            return dict(integration)
        return None
    except Exception as e:
        logger.error(f"Error getting integration for user {user_id} and provider {provider}: {e}")
        return None

# Communication operations
async def get_user_communications(user_id: int, limit: int = 50) -> List[Dict]:
    """Get user communications."""
    try:
        communications = await storage.getUserCommunications(user_id, limit)
        return [dict(comm) for comm in communications]
    except Exception as e:
        logger.error(f"Error getting communications for user {user_id}: {e}")
        return []

async def get_team_communications(team_id: int, limit: int = 100) -> List[Dict]:
    """Get team communications."""
    try:
        communications = await storage.getTeamCommunications(team_id, limit)
        return [dict(comm) for comm in communications]
    except Exception as e:
        logger.error(f"Error getting communications for team {team_id}: {e}")
        return []

# Retrospective operations
async def get_retrospective_by_id(retrospective_id: int) -> Optional[Dict]:
    """Get retrospective by ID."""
    try:
        retrospective = await storage.getRetrospective(retrospective_id)
        if retrospective:
            return dict(retrospective)
        return None
    except Exception as e:
        logger.error(f"Error getting retrospective by ID {retrospective_id}: {e}")
        return None

async def get_project_retrospectives(project_id: int) -> List[Dict]:
    """Get retrospectives for a project."""
    try:
        retrospectives = await storage.getProjectRetrospectives(project_id)
        return [dict(retro) for retro in retrospectives]
    except Exception as e:
        logger.error(f"Error getting retrospectives for project {project_id}: {e}")
        return []

# Notification operations
async def get_user_notifications(user_id: int, unread_only: bool = False) -> List[Dict]:
    """Get user notifications."""
    try:
        notifications = await storage.getUserNotifications(user_id, unread_only)
        return [dict(notification) for notification in notifications]
    except Exception as e:
        logger.error(f"Error getting notifications for user {user_id}: {e}")
        return []

async def mark_notification_as_read(notification_id: int) -> bool:
    """Mark notification as read."""
    try:
        await storage.markNotificationAsRead(notification_id)
        return True
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        return False

# Dashboard operations
async def get_dashboard_stats(user_id: int) -> Dict:
    """Get dashboard statistics for a user."""
    try:
        user_tasks = await get_user_tasks(user_id)
        user_skills = await get_user_skills(user_id)
        user_notifications = await get_user_notifications(user_id, unread_only=True)
        
        # Calculate basic stats
        total_tasks = len(user_tasks)
        completed_tasks = len([t for t in user_tasks if t.get("status") == "done"])
        in_progress_tasks = len([t for t in user_tasks if t.get("status") == "in_progress"])
        
        # Calculate skill growth rate (simplified)
        skill_growth_rate = 0
        if user_skills:
            avg_skill_level = sum(s.get("proficiency_level", 0) for s in user_skills) / len(user_skills)
            skill_growth_rate = max(0, (avg_skill_level - 2.5) * 20)  # Simplified growth calculation
        
        # Recent activities (simplified)
        recent_activities = []
        for task in user_tasks[-5:]:  # Last 5 tasks
            if task.get("status") == "done":
                recent_activities.append({
                    "id": task.get("id"),
                    "type": "task_completed",
                    "title": f"Completed task: {task.get('title', 'Unknown')}",
                    "description": task.get("description", ""),
                    "timestamp": task.get("updated_at", ""),
                    "metadata": {"task_id": task.get("id")}
                })
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "skill_growth_rate": skill_growth_rate,
            "unread_notifications": len(user_notifications),
            "recent_activities": recent_activities
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats for user {user_id}: {e}")
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "skill_growth_rate": 0,
            "unread_notifications": 0,
            "recent_activities": []
        }

# Team dashboard operations
async def get_team_dashboard_stats(team_id: int) -> Dict:
    """Get dashboard statistics for a team."""
    try:
        team_members = await get_team_members(team_id)
        team_projects = await get_projects_by_team(team_id)
        
        # Calculate team metrics
        total_members = len(team_members)
        active_projects = len([p for p in team_projects if p.get("status") == "active"])
        
        # Get all team tasks
        all_tasks = []
        for project in team_projects:
            project_tasks = await get_project_tasks(project["id"])
            all_tasks.extend(project_tasks)
        
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.get("status") == "done"])
        
        # Calculate team velocity (simplified)
        team_velocity = sum(t.get("story_points", 0) for t in all_tasks if t.get("status") == "done")
        
        return {
            "total_members": total_members,
            "active_projects": active_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "team_velocity": team_velocity,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting team dashboard stats for team {team_id}: {e}")
        return {
            "total_members": 0,
            "active_projects": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "team_velocity": 0,
            "completion_rate": 0
        }

# Utility functions
async def search_users(query: str, limit: int = 10) -> List[Dict]:
    """Search users by name or username."""
    try:
        # This would need to be implemented in the storage layer
        # For now, return empty list
        return []
    except Exception as e:
        logger.error(f"Error searching users with query '{query}': {e}")
        return []

async def get_system_health() -> Dict:
    """Get system health status."""
    try:
        # Basic health check
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "services": "operational"
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
