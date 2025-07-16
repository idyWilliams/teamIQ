from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio

from ..auth import get_current_user, require_roles
from ..storage import storage
from ..services.github_service import github_service
from ..services.jira_service import jira_service
from ..services.slack_service import slack_service
from ..services.ai_service import ai_service
from ..services.skill_analytics import skill_analytics
from ..services.sentiment_analysis import sentiment_analysis

router = APIRouter()

class AnalyticsResponse(BaseModel):
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    time_period: str
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime

class SkillAnalyticsResponse(BaseModel):
    user_id: int
    skill_progression: Dict[str, Any]
    competency_matrix: Dict[str, Any]
    growth_trends: List[Dict[str, Any]]
    skill_gaps: List[Dict[str, Any]]

class ProductivityAnalyticsResponse(BaseModel):
    user_id: int
    productivity_metrics: Dict[str, Any]
    code_quality_metrics: Dict[str, Any]
    collaboration_metrics: Dict[str, Any]
    time_analysis: Dict[str, Any]

class TeamAnalyticsResponse(BaseModel):
    team_id: int
    team_performance: Dict[str, Any]
    skill_distribution: Dict[str, Any]
    collaboration_index: float
    health_score: float
    sentiment_analysis: Dict[str, Any]

@router.get("/user/{user_id}/skills", response_model=SkillAnalyticsResponse)
async def get_user_skill_analytics(
    user_id: int,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive skill analytics for a user."""
    try:
        # Check permissions
        if current_user.get("role") in ["intern", "engineer"] and user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own analytics"
            )
        
        user = await storage.getUser(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user's skills
        user_skills = await storage.getUserSkills(user_id)
        
        # Get contribution data
        contributions = await _get_user_contributions(user, days)
        
        # Analyze skill progression
        skill_progression = {}
        for skill in user_skills:
            skill_name = skill["skill_name"]
            skill_contributions = [
                c for c in contributions 
                if _is_skill_relevant(skill_name, c)
            ]
            
            analysis = skill_analytics.calculate_skill_score(
                skill_contributions, 
                skill["category"]
            )
            
            skill_progression[skill_name] = {
                "current_score": analysis["score"],
                "trend": analysis["trend"],
                "confidence": analysis["confidence"],
                "evidence_count": analysis["evidence_count"],
                "category": skill["category"]
            }
        
        # Generate competency matrix
        competency_matrix = skill_analytics.generate_skill_radar_data(skill_progression)
        
        # Calculate growth trends
        growth_trends = []
        for skill_name, data in skill_progression.items():
            if data["trend"] == "improving":
                growth_trends.append({
                    "skill": skill_name,
                    "growth_rate": "positive",
                    "confidence": data["confidence"],
                    "category": data["category"]
                })
        
        # Find skill gaps
        required_skills = ["Python", "JavaScript", "React", "SQL", "Git", "Docker"]
        skill_gaps = skill_analytics.find_skill_gaps(skill_progression, required_skills)
        
        return SkillAnalyticsResponse(
            user_id=user_id,
            skill_progression=skill_progression,
            competency_matrix=competency_matrix,
            growth_trends=growth_trends,
            skill_gaps=skill_gaps
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill analytics: {str(e)}"
        )

@router.get("/user/{user_id}/productivity", response_model=ProductivityAnalyticsResponse)
async def get_user_productivity_analytics(
    user_id: int,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get productivity analytics for a user."""
    try:
        # Check permissions
        if current_user.get("role") in ["intern", "engineer"] and user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own analytics"
            )
        
        user = await storage.getUser(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get productivity metrics
        productivity_metrics = await _calculate_productivity_metrics(user, days)
        
        # Get code quality metrics
        code_quality_metrics = await _calculate_code_quality_metrics(user, days)
        
        # Get collaboration metrics
        collaboration_metrics = await _calculate_collaboration_metrics(user, days)
        
        # Get time analysis
        time_analysis = await _calculate_time_analysis(user, days)
        
        return ProductivityAnalyticsResponse(
            user_id=user_id,
            productivity_metrics=productivity_metrics,
            code_quality_metrics=code_quality_metrics,
            collaboration_metrics=collaboration_metrics,
            time_analysis=time_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get productivity analytics: {str(e)}"
        )

@router.get("/team/{team_id}/analytics", response_model=TeamAnalyticsResponse)
async def get_team_analytics(
    team_id: int,
    days: int = 30,
    current_user: dict = Depends(require_roles(["team_lead", "manager", "hr", "admin"]))
):
    """Get comprehensive team analytics."""
    try:
        team = await storage.getTeam(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Get team performance metrics
        team_performance = await _calculate_team_performance(team_id, days)
        
        # Get skill distribution
        skill_distribution = await _calculate_team_skill_distribution(team_id)
        
        # Calculate collaboration index
        collaboration_index = await _calculate_team_collaboration_index(team_id, days)
        
        # Calculate health score
        health_score = await _calculate_team_health_score(team_id, days)
        
        # Get sentiment analysis
        sentiment_analysis_data = await _calculate_team_sentiment(team_id, days)
        
        return TeamAnalyticsResponse(
            team_id=team_id,
            team_performance=team_performance,
            skill_distribution=skill_distribution,
            collaboration_index=collaboration_index,
            health_score=health_score,
            sentiment_analysis=sentiment_analysis_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team analytics: {str(e)}"
        )

@router.get("/insights/blockers")
async def get_blocker_insights(
    team_id: Optional[int] = None,
    days: int = 7,
    current_user: dict = Depends(require_roles(["team_lead", "manager", "hr", "admin"]))
):
    """Get insights about team blockers."""
    try:
        # Get team messages from Slack
        messages = []
        try:
            if team_id:
                # Get team-specific channel messages
                messages = await slack_service.get_channel_messages(days=days)
            else:
                # Get general channel messages
                messages = await slack_service.get_channel_messages(days=days)
        except Exception as e:
            print(f"Error getting Slack messages: {e}")
        
        # Analyze messages for blockers
        blockers = await ai_service.detect_blockers(messages)
        
        # Categorize blockers
        blocker_categories = {
            "technical": [],
            "process": [],
            "communication": [],
            "resource": []
        }
        
        for blocker in blockers:
            category = blocker.get("type", "technical")
            if category in blocker_categories:
                blocker_categories[category].append(blocker)
        
        # Calculate blocker frequency
        blocker_frequency = len(blockers) / len(messages) if messages else 0
        
        return {
            "blockers": blockers,
            "blocker_categories": blocker_categories,
            "blocker_frequency": blocker_frequency,
            "total_messages_analyzed": len(messages),
            "analysis_period_days": days,
            "recommendations": _generate_blocker_recommendations(blockers)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blocker insights: {str(e)}"
        )

@router.get("/insights/sentiment")
async def get_sentiment_insights(
    team_id: Optional[int] = None,
    days: int = 30,
    current_user: dict = Depends(require_roles(["team_lead", "manager", "hr", "admin"]))
):
    """Get team sentiment insights."""
    try:
        # Get team messages from Slack
        messages = []
        try:
            messages = await slack_service.get_channel_messages(days=days)
        except Exception as e:
            print(f"Error getting Slack messages: {e}")
        
        # Analyze sentiment trends
        sentiment_trends = await sentiment_analysis.analyze_team_sentiment_trends(messages, days)
        
        return {
            "sentiment_trends": sentiment_trends,
            "analysis_period_days": days,
            "team_id": team_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sentiment insights: {str(e)}"
        )

@router.get("/reports/performance")
async def get_performance_report(
    user_id: Optional[int] = None,
    team_id: Optional[int] = None,
    days: int = 30,
    current_user: dict = Depends(require_roles(["team_lead", "manager", "hr", "admin"]))
):
    """Get comprehensive performance report."""
    try:
        if user_id:
            # Individual performance report
            user = await storage.getUser(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get user tasks
            tasks = await storage.getTasks(userId=user_id)
            
            # Calculate metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "done"])
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get code metrics
            code_metrics = {}
            if user.github_username:
                try:
                    commits = await github_service.get_user_commits(user.github_username, days=days)
                    code_metrics = await github_service.analyze_code_quality(commits)
                except Exception as e:
                    print(f"Error getting GitHub metrics: {e}")
            
            return {
                "type": "individual",
                "user_id": user_id,
                "user_name": user.full_name,
                "period_days": days,
                "task_metrics": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "completion_rate": completion_rate
                },
                "code_metrics": code_metrics,
                "generated_at": datetime.now().isoformat()
            }
        
        elif team_id:
            # Team performance report
            team = await storage.getTeam(team_id)
            if not team:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )
            
            # Get team projects
            projects = await storage.getProjects(teamId=team_id)
            
            return {
                "type": "team",
                "team_id": team_id,
                "team_name": team.name,
                "period_days": days,
                "project_metrics": {
                    "total_projects": len(projects),
                    "active_projects": len([p for p in projects if p.status == "active"]),
                    "completed_projects": len([p for p in projects if p.status == "completed"])
                },
                "generated_at": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either user_id or team_id must be provided"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance report: {str(e)}"
        )

# Helper functions

async def _get_user_contributions(user, days: int):
    """Get user contributions from various sources."""
    contributions = []
    
    # GitHub contributions
    if user.github_username:
        try:
            commits = await github_service.get_user_commits(user.github_username, days=days)
            prs = await github_service.get_user_pull_requests(user.github_username, days=days)
            
            for commit in commits:
                contributions.append({
                    "type": "commit",
                    "date": commit.get("date"),
                    "files": commit.get("files", []),
                    "stats": commit.get("stats", {}),
                    "message": commit.get("message", "")
                })
            
            for pr in prs:
                contributions.append({
                    "type": "pull_request",
                    "date": pr.get("updated_at"),
                    "state": pr.get("state"),
                    "additions": pr.get("additions", 0),
                    "deletions": pr.get("deletions", 0)
                })
        except Exception as e:
            print(f"Error getting GitHub contributions: {e}")
    
    # Jira contributions
    try:
        issues = await jira_service.get_user_issues(user.username, days=days)
        for issue in issues:
            contributions.append({
                "type": "task",
                "date": issue.get("updated"),
                "status": issue.get("status"),
                "story_points": issue.get("story_points", 0)
            })
    except Exception as e:
        print(f"Error getting Jira contributions: {e}")
    
    return contributions

def _is_skill_relevant(skill_name, contribution):
    """Check if a contribution is relevant to a skill."""
    skill_lower = skill_name.lower()
    
    if contribution.get("type") == "commit":
        files = contribution.get("files", [])
        for file in files:
            if skill_lower in file.lower():
                return True
            
            # Language-specific checks
            if skill_lower == "python" and file.endswith(".py"):
                return True
            elif skill_lower == "javascript" and file.endswith((".js", ".jsx")):
                return True
            elif skill_lower == "react" and file.endswith((".jsx", ".tsx")):
                return True
    
    return False

async def _calculate_productivity_metrics(user, days: int):
    """Calculate productivity metrics for a user."""
    # Get user tasks
    tasks = await storage.getTasks(userId=user.id)
    
    # Calculate basic metrics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "done"])
    
    # Get GitHub metrics
    github_metrics = {}
    if user.github_username:
        try:
            commits = await github_service.get_user_commits(user.github_username, days=days)
            github_metrics = await github_service.analyze_code_quality(commits)
        except Exception as e:
            print(f"Error getting GitHub metrics: {e}")
    
    return {
        "task_completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "code_commits": github_metrics.get("total_commits", 0),
        "lines_of_code": github_metrics.get("total_lines_changed", 0),
        "commit_frequency": github_metrics.get("commit_frequency", 0)
    }

async def _calculate_code_quality_metrics(user, days: int):
    """Calculate code quality metrics for a user."""
    if not user.github_username:
        return {"error": "GitHub username not configured"}
    
    try:
        commits = await github_service.get_user_commits(user.github_username, days=days)
        prs = await github_service.get_user_pull_requests(user.github_username, days=days)
        
        # Calculate metrics
        total_commits = len(commits)
        total_prs = len(prs)
        merged_prs = len([pr for pr in prs if pr.get("state") == "merged"])
        
        return {
            "total_commits": total_commits,
            "total_pull_requests": total_prs,
            "merged_pull_requests": merged_prs,
            "pr_merge_rate": (merged_prs / total_prs * 100) if total_prs > 0 else 0,
            "avg_commit_size": sum(c.get("stats", {}).get("total", 0) for c in commits) / total_commits if total_commits > 0 else 0
        }
    except Exception as e:
        return {"error": f"Failed to calculate code quality metrics: {str(e)}"}

async def _calculate_collaboration_metrics(user, days: int):
    """Calculate collaboration metrics for a user."""
    try:
        # Get code reviews
        reviews = []
        if user.github_username:
            reviews = await github_service.get_user_reviews(user.github_username, days=days)
        
        # Get Slack messages
        messages = []
        if user.slack_user_id:
            messages = await slack_service.get_user_messages(user.slack_user_id, days=days)
        
        return {
            "code_reviews_given": len(reviews),
            "messages_sent": len(messages),
            "collaboration_score": min((len(reviews) + len(messages)) / 10, 1.0)  # Normalized score
        }
    except Exception as e:
        return {"error": f"Failed to calculate collaboration metrics: {str(e)}"}

async def _calculate_time_analysis(user, days: int):
    """Calculate time analysis for a user."""
    try:
        # Get Jira worklog
        worklog = await jira_service.get_user_worklog(user.username, days=days)
        
        total_hours = sum(w.get("time_spent_seconds", 0) for w in worklog) / 3600  # Convert to hours
        
        return {
            "total_logged_hours": total_hours,
            "avg_hours_per_day": total_hours / days if days > 0 else 0,
            "worklog_entries": len(worklog)
        }
    except Exception as e:
        return {"error": f"Failed to calculate time analysis: {str(e)}"}

async def _calculate_team_performance(team_id: int, days: int):
    """Calculate team performance metrics."""
    # Get team projects
    projects = await storage.getProjects(teamId=team_id)
    
    # Basic metrics
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.status == "active"])
    completed_projects = len([p for p in projects if p.status == "completed"])
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "project_completion_rate": (completed_projects / total_projects * 100) if total_projects > 0 else 0
    }

async def _calculate_team_skill_distribution(team_id: int):
    """Calculate team skill distribution."""
    # Placeholder - would need to implement team member skills aggregation
    return {
        "technical_skills": {},
        "soft_skills": {},
        "skill_coverage": 0.75
    }

async def _calculate_team_collaboration_index(team_id: int, days: int):
    """Calculate team collaboration index."""
    # Placeholder - would analyze team interactions
    return 0.8

async def _calculate_team_health_score(team_id: int, days: int):
    """Calculate team health score."""
    # Placeholder - would combine various health indicators
    return 0.85

async def _calculate_team_sentiment(team_id: int, days: int):
    """Calculate team sentiment analysis."""
    try:
        # Get team messages
        messages = await slack_service.get_channel_messages(days=days)
        
        # Analyze sentiment
        sentiment_trends = await sentiment_analysis.analyze_team_sentiment_trends(messages, days)
        
        return sentiment_trends
    except Exception as e:
        return {"error": f"Failed to calculate team sentiment: {str(e)}"}

def _generate_blocker_recommendations(blockers):
    """Generate recommendations based on detected blockers."""
    recommendations = []
    
    if not blockers:
        return ["No blockers detected. Team communication appears healthy."]
    
    # Categorize blockers
    technical_blockers = [b for b in blockers if b.get("type") == "technical"]
    process_blockers = [b for b in blockers if b.get("type") == "process"]
    communication_blockers = [b for b in blockers if b.get("type") == "communication"]
    
    if technical_blockers:
        recommendations.append(f"Address {len(technical_blockers)} technical blockers through code reviews and pair programming")
    
    if process_blockers:
        recommendations.append(f"Review and improve processes to resolve {len(process_blockers)} process-related blockers")
    
    if communication_blockers:
        recommendations.append(f"Enhance team communication to address {len(communication_blockers)} communication issues")
    
    # High severity blockers
    high_severity = [b for b in blockers if b.get("severity") == "high"]
    if high_severity:
        recommendations.append(f"Immediate attention required for {len(high_severity)} high-severity blockers")
    
    return recommendations
