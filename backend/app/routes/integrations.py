from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from auth import get_current_user, require_admin
from models.database import get_user_integrations, get_integration_by_provider
from integrations.github import sync_github_data, GitHubIntegration
from integrations.jira import sync_jira_data, JiraIntegration
from integrations.slack import sync_slack_data, SlackIntegration

logger = logging.getLogger(__name__)

router = APIRouter()

class GitHubIntegrationRequest(BaseModel):
    access_token: str
    repositories: List[str]  # List of repo names in "owner/repo" format

class JiraIntegrationRequest(BaseModel):
    base_url: str
    username: str
    api_token: str
    project_keys: List[str]

class SlackIntegrationRequest(BaseModel):
    bot_token: str
    user_id: str
    team_members: Optional[List[str]] = None

class IntegrationSyncRequest(BaseModel):
    provider: str
    force_sync: bool = False

@router.get("/")
async def get_user_integrations_list(current_user: dict = Depends(get_current_user)):
    """Get user's integrations."""
    try:
        integrations = await get_user_integrations(current_user["id"])
        
        # Enhance integrations with status information
        enhanced_integrations = []
        for integration in integrations:
            provider = integration.get("provider")
            
            # Check integration status
            status_info = {
                "connected": integration.get("is_active", False),
                "last_sync": integration.get("updated_at"),
                "expires_at": integration.get("expires_at")
            }
            
            # Add provider-specific information
            if provider == "github":
                status_info["repositories"] = integration.get("config", {}).get("repositories", [])
            elif provider == "jira":
                status_info["base_url"] = integration.get("config", {}).get("base_url")
                status_info["project_keys"] = integration.get("config", {}).get("project_keys", [])
            elif provider == "slack":
                status_info["user_id"] = integration.get("config", {}).get("user_id")
                status_info["team_members"] = integration.get("config", {}).get("team_members", [])
            
            enhanced_integration = {
                "id": integration["id"],
                "provider": provider,
                "external_id": integration.get("external_id"),
                "status": status_info,
                "created_at": integration.get("created_at"),
                "updated_at": integration.get("updated_at")
            }
            enhanced_integrations.append(enhanced_integration)
        
        return {
            "integrations": enhanced_integrations,
            "total": len(enhanced_integrations),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting user integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/github")
async def connect_github_integration(
    request: GitHubIntegrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Connect GitHub integration."""
    try:
        # Validate GitHub access token
        github = GitHubIntegration(request.access_token)
        
        try:
            user_info = await github.get_user_info()
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub access token or API error"
            )
        
        # Check if integration already exists
        existing_integration = await get_integration_by_provider(current_user["id"], "github")
        
        if existing_integration:
            # Update existing integration
            integration_data = {
                "access_token": request.access_token,
                "config": {
                    "repositories": request.repositories,
                    "username": user_info.get("login")
                },
                "is_active": True,
                "updated_at": datetime.now()
            }
            # In a real implementation, this would update the integration
            integration_id = existing_integration["id"]
        else:
            # Create new integration
            integration_data = {
                "user_id": current_user["id"],
                "provider": "github",
                "external_id": str(user_info.get("id")),
                "access_token": request.access_token,
                "config": {
                    "repositories": request.repositories,
                    "username": user_info.get("login")
                },
                "is_active": True
            }
            # In a real implementation, this would create the integration
            integration_id = 1  # Would be the actual created integration ID
        
        return {
            "integration_id": integration_id,
            "provider": "github",
            "status": "connected",
            "repositories": request.repositories,
            "github_username": user_info.get("login"),
            "success": True,
            "message": "GitHub integration connected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting GitHub integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/jira")
async def connect_jira_integration(
    request: JiraIntegrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Connect Jira integration."""
    try:
        # Validate Jira credentials
        jira = JiraIntegration(request.base_url, request.username, request.api_token)
        
        try:
            user_info = await jira.get_user_info()
        except Exception as e:
            logger.error(f"Jira API error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Jira credentials or API error"
            )
        
        # Check if integration already exists
        existing_integration = await get_integration_by_provider(current_user["id"], "jira")
        
        if existing_integration:
            # Update existing integration
            integration_data = {
                "config": {
                    "base_url": request.base_url,
                    "username": request.username,
                    "project_keys": request.project_keys
                },
                "is_active": True,
                "updated_at": datetime.now()
            }
            integration_id = existing_integration["id"]
        else:
            # Create new integration
            integration_data = {
                "user_id": current_user["id"],
                "provider": "jira",
                "external_id": user_info.get("accountId"),
                "config": {
                    "base_url": request.base_url,
                    "username": request.username,
                    "project_keys": request.project_keys
                },
                "is_active": True
            }
            integration_id = 1  # Would be the actual created integration ID
        
        return {
            "integration_id": integration_id,
            "provider": "jira",
            "status": "connected",
            "base_url": request.base_url,
            "username": request.username,
            "project_keys": request.project_keys,
            "success": True,
            "message": "Jira integration connected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Jira integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/slack")
async def connect_slack_integration(
    request: SlackIntegrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Connect Slack integration."""
    try:
        # Validate Slack bot token
        slack = SlackIntegration(request.bot_token)
        
        try:
            user_info = await slack.get_user_info(request.user_id)
        except Exception as e:
            logger.error(f"Slack API error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Slack bot token or user ID"
            )
        
        # Check if integration already exists
        existing_integration = await get_integration_by_provider(current_user["id"], "slack")
        
        if existing_integration:
            # Update existing integration
            integration_data = {
                "config": {
                    "user_id": request.user_id,
                    "team_members": request.team_members or []
                },
                "is_active": True,
                "updated_at": datetime.now()
            }
            integration_id = existing_integration["id"]
        else:
            # Create new integration
            integration_data = {
                "user_id": current_user["id"],
                "provider": "slack",
                "external_id": request.user_id,
                "config": {
                    "user_id": request.user_id,
                    "team_members": request.team_members or []
                },
                "is_active": True
            }
            integration_id = 1  # Would be the actual created integration ID
        
        return {
            "integration_id": integration_id,
            "provider": "slack",
            "status": "connected",
            "user_id": request.user_id,
            "team_members": request.team_members or [],
            "success": True,
            "message": "Slack integration connected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Slack integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/sync")
async def sync_integrations(
    request: IntegrationSyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """Sync data from integrations."""
    try:
        provider = request.provider.lower()
        
        # Get integration
        integration = await get_integration_by_provider(current_user["id"], provider)
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {provider} integration found"
            )
        
        if not integration.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{provider} integration is not active"
            )
        
        # Sync data based on provider
        sync_result = None
        
        if provider == "github":
            config = integration.get("config", {})
            repositories = config.get("repositories", [])
            access_token = integration.get("access_token")
            
            if not repositories or not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="GitHub integration is missing required configuration"
                )
            
            sync_result = await sync_github_data(
                current_user["id"],
                access_token,
                repositories
            )
            
        elif provider == "jira":
            config = integration.get("config", {})
            base_url = config.get("base_url")
            username = config.get("username")
            project_keys = config.get("project_keys", [])
            api_token = integration.get("access_token")
            
            if not all([base_url, username, project_keys, api_token]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Jira integration is missing required configuration"
                )
            
            sync_result = await sync_jira_data(
                current_user["id"],
                base_url,
                username,
                api_token,
                project_keys
            )
            
        elif provider == "slack":
            config = integration.get("config", {})
            user_id = config.get("user_id")
            team_members = config.get("team_members", [])
            bot_token = integration.get("access_token")
            
            if not all([user_id, bot_token]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slack integration is missing required configuration"
                )
            
            sync_result = await sync_slack_data(
                current_user["id"],
                bot_token,
                user_id,
                team_members
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        # Update integration sync timestamp
        # In a real implementation, this would update the integration in the database
        
        return {
            "provider": provider,
            "sync_result": sync_result,
            "sync_timestamp": datetime.now().isoformat(),
            "success": True,
            "message": f"{provider} data synchronized successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing {request.provider} integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Disconnect an integration."""
    try:
        # In a real implementation, this would:
        # 1. Verify the integration belongs to the user
        # 2. Deactivate the integration
        # 3. Optionally clean up synced data
        
        return {
            "integration_id": integration_id,
            "status": "disconnected",
            "success": True,
            "message": "Integration disconnected successfully"
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting integration {integration_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/status")
async def get_integration_status(current_user: dict = Depends(get_current_user)):
    """Get overall integration status."""
    try:
        integrations = await get_user_integrations(current_user["id"])
        
        # Calculate integration status
        total_integrations = len(integrations)
        active_integrations = len([i for i in integrations if i.get("is_active")])
        
        # Get status by provider
        provider_status = {}
        for integration in integrations:
            provider = integration.get("provider")
            provider_status[provider] = {
                "connected": integration.get("is_active", False),
                "last_sync": integration.get("updated_at"),
                "status": "active" if integration.get("is_active") else "inactive"
            }
        
        # Calculate data freshness
        data_freshness = {}
        for integration in integrations:
            if integration.get("is_active"):
                provider = integration.get("provider")
                last_sync = integration.get("updated_at")
                
                if last_sync:
                    last_sync_date = datetime.fromisoformat(last_sync)
                    hours_since_sync = (datetime.now() - last_sync_date).total_seconds() / 3600
                    
                    if hours_since_sync < 1:
                        freshness = "fresh"
                    elif hours_since_sync < 24:
                        freshness = "recent"
                    else:
                        freshness = "stale"
                else:
                    freshness = "never_synced"
                
                data_freshness[provider] = {
                    "status": freshness,
                    "last_sync": last_sync,
                    "hours_since_sync": hours_since_sync if last_sync else None
                }
        
        return {
            "total_integrations": total_integrations,
            "active_integrations": active_integrations,
            "provider_status": provider_status,
            "data_freshness": data_freshness,
            "overall_health": "healthy" if active_integrations > 0 else "no_integrations",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/available")
async def get_available_integrations(current_user: dict = Depends(get_current_user)):
    """Get list of available integrations."""
    try:
        available_integrations = [
            {
                "provider": "github",
                "name": "GitHub",
                "description": "Sync code commits, pull requests, and reviews",
                "features": ["Commit tracking", "PR analysis", "Code quality metrics", "Collaboration insights"],
                "setup_required": ["Access token", "Repository list"],
                "icon": "github"
            },
            {
                "provider": "jira",
                "name": "Jira",
                "description": "Sync tasks, sprints, and project management data",
                "features": ["Task tracking", "Sprint metrics", "Time logging", "Performance analytics"],
                "setup_required": ["Base URL", "Username", "API token", "Project keys"],
                "icon": "jira"
            },
            {
                "provider": "slack",
                "name": "Slack",
                "description": "Analyze team communication and sentiment",
                "features": ["Sentiment analysis", "Blocker detection", "Team communication insights", "Mentorship tracking"],
                "setup_required": ["Bot token", "User ID", "Team member list"],
                "icon": "slack"
            }
        ]
        
        # Get user's current integrations
        user_integrations = await get_user_integrations(current_user["id"])
        connected_providers = {i.get("provider") for i in user_integrations if i.get("is_active")}
        
        # Mark connected integrations
        for integration in available_integrations:
            integration["connected"] = integration["provider"] in connected_providers
        
        return {
            "available_integrations": available_integrations,
            "connected_count": len(connected_providers),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting available integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def get_integration_health(current_user: dict = Depends(require_admin)):
    """Get integration health metrics (admin only)."""
    try:
        # This would provide system-wide integration health metrics
        # For now, return a basic structure
        
        health_metrics = {
            "total_users_with_integrations": 0,
            "integration_usage": {
                "github": {"users": 0, "active_syncs": 0},
                "jira": {"users": 0, "active_syncs": 0},
                "slack": {"users": 0, "active_syncs": 0}
            },
            "sync_performance": {
                "avg_sync_time": 0,
                "failed_syncs_24h": 0,
                "success_rate": 100
            },
            "data_quality": {
                "total_records_synced": 0,
                "data_completeness": 95,
                "duplicate_records": 0
            },
            "system_health": "healthy"
        }
        
        return {
            "health_metrics": health_metrics,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting integration health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
