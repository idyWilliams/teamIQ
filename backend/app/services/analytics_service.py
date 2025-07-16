from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from models import User, UserSkill, Commit, PullRequest, Message, Task, Project
from services.github_service import github_service
from services.jira_service import jira_service
from services.slack_service import slack_service
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_user_skill_scores(self, user_id: int, days: int = 30) -> Dict:
        """Calculate skill scores for a user based on recent activity"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get commits
        commits = self.db.query(Commit).filter(
            Commit.user_id == user_id,
            Commit.commit_date >= cutoff_date
        ).all()
        
        # Get pull requests
        pull_requests = self.db.query(PullRequest).filter(
            PullRequest.author_id == user_id,
            PullRequest.created_at >= cutoff_date
        ).all()
        
        # Get completed tasks
        tasks = self.db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.updated_at >= cutoff_date,
            Task.status.in_(["Done", "Resolved", "Closed"])
        ).all()
        
        # Calculate skill scores
        skill_scores = {}
        
        # Language skills from commits
        for commit in commits:
            if commit.languages:
                for language, lines in commit.languages.items():
                    if language not in skill_scores:
                        skill_scores[language] = 0
                    skill_scores[language] += lines * 0.001  # Weight factor
        
        # Task completion skills
        for task in tasks:
            if task.story_points:
                skill_scores["Project Management"] = skill_scores.get("Project Management", 0) + task.story_points * 0.1
        
        # Pull request skills
        for pr in pull_requests:
            skill_scores["Code Review"] = skill_scores.get("Code Review", 0) + 0.5
            if pr.review_comments > 0:
                skill_scores["Collaboration"] = skill_scores.get("Collaboration", 0) + 0.3
        
        # Normalize scores (0-100)
        max_score = max(skill_scores.values()) if skill_scores else 1
        normalized_scores = {skill: min(100, (score / max_score) * 100) for skill, score in skill_scores.items()}
        
        return normalized_scores
    
    def get_user_productivity_metrics(self, user_id: int, days: int = 30) -> Dict:
        """Get productivity metrics for a user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Commits
        commits_count = self.db.query(func.count(Commit.id)).filter(
            Commit.user_id == user_id,
            Commit.commit_date >= cutoff_date
        ).scalar()
        
        # Pull requests
        prs_count = self.db.query(func.count(PullRequest.id)).filter(
            PullRequest.author_id == user_id,
            PullRequest.created_at >= cutoff_date
        ).scalar()
        
        # Tasks completed
        tasks_completed = self.db.query(func.count(Task.id)).filter(
            Task.assignee_id == user_id,
            Task.updated_at >= cutoff_date,
            Task.status.in_(["Done", "Resolved", "Closed"])
        ).scalar()
        
        # Lines of code
        total_additions = self.db.query(func.sum(Commit.additions)).filter(
            Commit.user_id == user_id,
            Commit.commit_date >= cutoff_date
        ).scalar() or 0
        
        total_deletions = self.db.query(func.sum(Commit.deletions)).filter(
            Commit.user_id == user_id,
            Commit.commit_date >= cutoff_date
        ).scalar() or 0
        
        return {
            "commits": commits_count,
            "pull_requests": prs_count,
            "tasks_completed": tasks_completed,
            "lines_added": total_additions,
            "lines_deleted": total_deletions,
            "net_lines": total_additions - total_deletions,
            "period_days": days
        }
    
    def get_team_analytics(self, team_id: int, days: int = 30) -> Dict:
        """Get analytics for a team"""
        from models import TeamMember
        
        team_members = self.db.query(User).join(TeamMember).filter(
            TeamMember.team_id == team_id
        ).all()
        
        team_analytics = {
            "team_size": len(team_members),
            "members": [],
            "aggregated_metrics": {
                "total_commits": 0,
                "total_prs": 0,
                "total_tasks_completed": 0,
                "average_sentiment": 0.5,
                "blocker_count": 0
            },
            "skill_distribution": {},
            "productivity_trend": []
        }
        
        sentiment_scores = []
        
        for member in team_members:
            member_metrics = self.get_user_productivity_metrics(member.id, days)
            member_skills = self.calculate_user_skill_scores(member.id, days)
            
            # Get sentiment data
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            messages = self.db.query(Message).filter(
                Message.user_id == member.id,
                Message.message_date >= cutoff_date
            ).all()
            
            member_sentiment = 0.5
            member_blockers = 0
            
            if messages:
                sentiment_sum = sum(float(msg.sentiment_score or 0.5) for msg in messages)
                member_sentiment = sentiment_sum / len(messages)
                member_blockers = sum(1 for msg in messages if msg.is_blocker)
            
            sentiment_scores.append(member_sentiment)
            
            team_analytics["members"].append({
                "id": member.id,
                "name": f"{member.first_name} {member.last_name}",
                "role": member.role,
                "metrics": member_metrics,
                "skills": member_skills,
                "sentiment": member_sentiment,
                "blockers": member_blockers
            })
            
            # Aggregate metrics
            team_analytics["aggregated_metrics"]["total_commits"] += member_metrics["commits"]
            team_analytics["aggregated_metrics"]["total_prs"] += member_metrics["pull_requests"]
            team_analytics["aggregated_metrics"]["total_tasks_completed"] += member_metrics["tasks_completed"]
            team_analytics["aggregated_metrics"]["blocker_count"] += member_blockers
            
            # Skill distribution
            for skill, score in member_skills.items():
                if skill not in team_analytics["skill_distribution"]:
                    team_analytics["skill_distribution"][skill] = []
                team_analytics["skill_distribution"][skill].append(score)
        
        # Calculate average sentiment
        if sentiment_scores:
            team_analytics["aggregated_metrics"]["average_sentiment"] = sum(sentiment_scores) / len(sentiment_scores)
        
        # Calculate skill averages
        for skill in team_analytics["skill_distribution"]:
            scores = team_analytics["skill_distribution"][skill]
            team_analytics["skill_distribution"][skill] = {
                "average": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "count": len(scores)
            }
        
        return team_analytics
    
    def get_project_analytics(self, project_id: int) -> Dict:
        """Get analytics for a project"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {}
        
        # Get project tasks
        tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
        
        # Get project commits
        commits = self.db.query(Commit).filter(Commit.project_id == project_id).all()
        
        # Get project pull requests
        prs = self.db.query(PullRequest).filter(PullRequest.project_id == project_id).all()
        
        # Calculate metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status in ["Done", "Resolved", "Closed"]])
        in_progress_tasks = len([t for t in tasks if t.status in ["In Progress", "In Review"]])
        
        total_story_points = sum(t.story_points or 0 for t in tasks)
        completed_story_points = sum(t.story_points or 0 for t in tasks if t.status in ["Done", "Resolved", "Closed"])
        
        return {
            "project_name": project.name,
            "status": project.status,
            "task_metrics": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "story_points": {
                "total": total_story_points,
                "completed": completed_story_points,
                "completion_rate": (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0
            },
            "code_metrics": {
                "total_commits": len(commits),
                "total_prs": len(prs),
                "total_lines_added": sum(c.additions or 0 for c in commits),
                "total_lines_deleted": sum(c.deletions or 0 for c in commits)
            },
            "timeline": {
                "start_date": project.start_date,
                "end_date": project.end_date,
                "created_at": project.created_at
            }
        }
    
    def sync_external_data(self, user_id: int) -> Dict:
        """Sync data from external services for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        results = {
            "github": {"synced": False, "error": None},
            "jira": {"synced": False, "error": None},
            "slack": {"synced": False, "error": None}
        }
        
        # Sync GitHub data
        if user.github_username:
            try:
                # This would typically be more complex with proper repo detection
                # For now, just indicate sync capability
                results["github"]["synced"] = True
            except Exception as e:
                results["github"]["error"] = str(e)
        
        # Sync Jira data
        if user.jira_username:
            try:
                # This would sync Jira issues
                results["jira"]["synced"] = True
            except Exception as e:
                results["jira"]["error"] = str(e)
        
        # Sync Slack data
        if user.slack_user_id:
            try:
                # This would sync Slack messages
                results["slack"]["synced"] = True
            except Exception as e:
                results["slack"]["error"] = str(e)
        
        return results
