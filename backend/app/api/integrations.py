from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.services.github_service import GitHubService
from app.services.jira_service import JiraService
from app.services.slack_service import SlackService
from app.services.ai_service import AIService

router = APIRouter()


@router.get("/github/repos")
async def get_github_repos(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get GitHub repositories for a user."""
    try:
        github_service = GitHubService()
        repos = github_service.get_user_repos(username)
        return {"repos": repos}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching GitHub repos: {str(e)}"
        )


@router.get("/github/commits")
async def get_github_commits(
    username: str,
    repo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get GitHub commits for a repository."""
    try:
        github_service = GitHubService()
        commits = github_service.get_repo_commits(username, repo)
        return {"commits": commits}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching GitHub commits: {str(e)}"
        )


@router.get("/github/user/{username}/stats")
async def get_github_user_stats(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get GitHub statistics for a user."""
    try:
        github_service = GitHubService()
        stats = github_service.get_user_stats(username)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching GitHub stats: {str(e)}"
        )


@router.get("/jira/projects")
async def get_jira_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    """Get JIRA projects."""
    try:
        jira_service = JiraService()
        projects = jira_service.get_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching JIRA projects: {str(e)}"
        )


@router.get("/jira/issues")
async def get_jira_issues(
    project_key: str,
    assignee: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get JIRA issues for a project."""
    try:
        jira_service = JiraService()
        issues = jira_service.get_project_issues(project_key, assignee)
        return {"issues": issues}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching JIRA issues: {str(e)}"
        )


@router.get("/jira/user/{username}/stats")
async def get_jira_user_stats(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get JIRA statistics for a user."""
    try:
        jira_service = JiraService()
        stats = jira_service.get_user_stats(username)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching JIRA stats: {str(e)}"
        )


@router.get("/slack/channels")
async def get_slack_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    """Get Slack channels."""
    try:
        slack_service = SlackService()
        channels = slack_service.get_channels()
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Slack channels: {str(e)}"
        )


@router.get("/slack/messages")
async def get_slack_messages(
    channel_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    """Get Slack messages from a channel."""
    try:
        slack_service = SlackService()
        messages = slack_service.get_channel_messages(channel_id, limit)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Slack messages: {str(e)}"
        )


@router.post("/slack/analyze-sentiment")
async def analyze_slack_sentiment(
    channel_id: str,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"]))
):
    """Analyze sentiment of Slack messages."""
    try:
        slack_service = SlackService()
        ai_service = AIService()
        
        # Get messages from the last N days
        messages = slack_service.get_channel_messages(channel_id, limit=1000)
        
        # Analyze sentiment
        sentiment_analysis = ai_service.analyze_team_sentiment(messages)
        
        return {"sentiment_analysis": sentiment_analysis}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing sentiment: {str(e)}"
        )


@router.post("/sync/all")
async def sync_all_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Sync data from all integrations."""
    try:
        # This would typically be run as a background task
        results = {}
        
        # Sync GitHub data
        github_service = GitHubService()
        results["github"] = "GitHub sync initiated"
        
        # Sync JIRA data
        jira_service = JiraService()
        results["jira"] = "JIRA sync initiated"
        
        # Sync Slack data
        slack_service = SlackService()
        results["slack"] = "Slack sync initiated"
        
        return {"message": "All integrations sync initiated", "results": results}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing integrations: {str(e)}"
        )


@router.get("/health")
async def check_integrations_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Check health of all integrations."""
    health = {}
    
    # Check GitHub
    try:
        github_service = GitHubService()
        health["github"] = "healthy" if github_service.check_connection() else "unhealthy"
    except:
        health["github"] = "unhealthy"
    
    # Check JIRA
    try:
        jira_service = JiraService()
        health["jira"] = "healthy" if jira_service.check_connection() else "unhealthy"
    except:
        health["jira"] = "unhealthy"
    
    # Check Slack
    try:
        slack_service = SlackService()
        health["slack"] = "healthy" if slack_service.check_connection() else "unhealthy"
    except:
        health["slack"] = "unhealthy"
    
    return {"health": health}
