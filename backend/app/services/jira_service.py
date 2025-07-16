import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings
import base64


class JiraService:
    def __init__(self):
        self.api_url = settings.JIRA_API_URL
        self.username = settings.JIRA_USERNAME
        self.api_token = settings.JIRA_API_TOKEN
        
        # Create basic auth header
        if self.username and self.api_token:
            credentials = f"{self.username}:{self.api_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        else:
            self.headers = {}
    
    def check_connection(self) -> bool:
        """Check if JIRA API is accessible."""
        try:
            if not self.api_url or not self.headers:
                return False
            
            response = requests.get(f"{self.api_url}/rest/api/2/myself", headers=self.headers)
            return response.status_code == 200
        except:
            return False
    
    def get_projects(self) -> List[Dict]:
        """Get all projects."""
        try:
            url = f"{self.api_url}/rest/api/2/project"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            projects = response.json()
            return [
                {
                    "key": project["key"],
                    "name": project["name"],
                    "description": project.get("description", ""),
                    "lead": project.get("lead", {}).get("displayName", ""),
                    "project_type": project.get("projectTypeKey", ""),
                    "url": project.get("self", ""),
                    "avatar_url": project.get("avatarUrls", {}).get("48x48", "")
                }
                for project in projects
            ]
        except requests.RequestException as e:
            print(f"Error fetching JIRA projects: {e}")
            return []
    
    def get_project_issues(self, project_key: str, assignee: str = None, days: int = 30) -> List[Dict]:
        """Get issues for a project."""
        try:
            jql = f"project = {project_key}"
            
            if assignee:
                jql += f" AND assignee = {assignee}"
            
            # Add date filter for recent issues
            since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            jql += f" AND created >= '{since_date}'"
            
            url = f"{self.api_url}/rest/api/2/search"
            params = {
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,status,assignee,reporter,created,updated,priority,issuetype,description,resolutiondate"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get("issues", [])
            
            return [
                {
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "status": issue["fields"]["status"]["name"],
                    "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None,
                    "reporter": issue["fields"]["reporter"]["displayName"] if issue["fields"]["reporter"] else None,
                    "created": issue["fields"]["created"],
                    "updated": issue["fields"]["updated"],
                    "priority": issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else None,
                    "issue_type": issue["fields"]["issuetype"]["name"],
                    "description": issue["fields"].get("description", ""),
                    "resolution_date": issue["fields"].get("resolutiondate"),
                    "url": f"{self.api_url}/browse/{issue['key']}"
                }
                for issue in issues
            ]
        except requests.RequestException as e:
            print(f"Error fetching JIRA issues: {e}")
            return []
    
    def get_user_stats(self, username: str, days: int = 30) -> Dict:
        """Get comprehensive stats for a user."""
        try:
            # Get user info
            user_url = f"{self.api_url}/rest/api/2/user"
            user_params = {"username": username}
            user_response = requests.get(user_url, headers=self.headers, params=user_params)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            # Get issues assigned to user
            assigned_issues = self.get_user_assigned_issues(username, days)
            
            # Get issues reported by user
            reported_issues = self.get_user_reported_issues(username, days)
            
            # Calculate stats
            total_assigned = len(assigned_issues)
            total_reported = len(reported_issues)
            
            # Count by status
            status_counts = {}
            for issue in assigned_issues:
                status = issue["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by priority
            priority_counts = {}
            for issue in assigned_issues:
                priority = issue["priority"] or "None"
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Calculate completion rate
            completed_issues = sum(1 for issue in assigned_issues if issue["resolution_date"])
            completion_rate = (completed_issues / total_assigned * 100) if total_assigned > 0 else 0
            
            return {
                "username": username,
                "display_name": user_info.get("displayName", ""),
                "email": user_info.get("emailAddress", ""),
                "active": user_info.get("active", False),
                "stats": {
                    "total_assigned_issues": total_assigned,
                    "total_reported_issues": total_reported,
                    "completed_issues": completed_issues,
                    "completion_rate": round(completion_rate, 2),
                    "status_distribution": status_counts,
                    "priority_distribution": priority_counts,
                    "analysis_period": f"{days} days"
                }
            }
        except requests.RequestException as e:
            print(f"Error fetching JIRA user stats: {e}")
            return {}
    
    def get_user_assigned_issues(self, username: str, days: int = 30) -> List[Dict]:
        """Get issues assigned to a user."""
        try:
            since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            jql = f"assignee = {username} AND created >= '{since_date}'"
            
            url = f"{self.api_url}/rest/api/2/search"
            params = {
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,status,created,updated,priority,issuetype,resolutiondate"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get("issues", [])
            
            return [
                {
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "status": issue["fields"]["status"]["name"],
                    "created": issue["fields"]["created"],
                    "updated": issue["fields"]["updated"],
                    "priority": issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else None,
                    "issue_type": issue["fields"]["issuetype"]["name"],
                    "resolution_date": issue["fields"].get("resolutiondate"),
                    "url": f"{self.api_url}/browse/{issue['key']}"
                }
                for issue in issues
            ]
        except requests.RequestException as e:
            print(f"Error fetching assigned issues: {e}")
            return []
    
    def get_user_reported_issues(self, username: str, days: int = 30) -> List[Dict]:
        """Get issues reported by a user."""
        try:
            since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            jql = f"reporter = {username} AND created >= '{since_date}'"
            
            url = f"{self.api_url}/rest/api/2/search"
            params = {
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,status,created,updated,priority,issuetype,assignee"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get("issues", [])
            
            return [
                {
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "status": issue["fields"]["status"]["name"],
                    "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None,
                    "created": issue["fields"]["created"],
                    "updated": issue["fields"]["updated"],
                    "priority": issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else None,
                    "issue_type": issue["fields"]["issuetype"]["name"],
                    "url": f"{self.api_url}/browse/{issue['key']}"
                }
                for issue in issues
            ]
        except requests.RequestException as e:
            print(f"Error fetching reported issues: {e}")
            return []
    
    def get_project_velocity(self, project_key: str, days: int = 30) -> Dict:
        """Get velocity metrics for a project."""
        try:
            issues = self.get_project_issues(project_key, days=days)
            
            # Group by week
            weekly_completion = {}
            for issue in issues:
                if issue["resolution_date"]:
                    # Parse resolution date and group by week
                    resolution_date = datetime.fromisoformat(issue["resolution_date"].replace("Z", "+00:00"))
                    week_key = resolution_date.strftime("%Y-W%U")
                    weekly_completion[week_key] = weekly_completion.get(week_key, 0) + 1
            
            # Calculate story points (if available)
            total_story_points = 0  # Would need to get from custom fields
            
            return {
                "project_key": project_key,
                "total_issues": len(issues),
                "completed_issues": len([i for i in issues if i["resolution_date"]]),
                "weekly_completion": weekly_completion,
                "average_weekly_completion": sum(weekly_completion.values()) / len(weekly_completion) if weekly_completion else 0,
                "total_story_points": total_story_points,
                "analysis_period": f"{days} days"
            }
        except Exception as e:
            print(f"Error calculating project velocity: {e}")
            return {}
    
    def get_issue_cycle_time(self, project_key: str, days: int = 30) -> Dict:
        """Calculate cycle time for issues."""
        try:
            issues = self.get_project_issues(project_key, days=days)
            
            cycle_times = []
            for issue in issues:
                if issue["resolution_date"]:
                    created = datetime.fromisoformat(issue["created"].replace("Z", "+00:00"))
                    resolved = datetime.fromisoformat(issue["resolution_date"].replace("Z", "+00:00"))
                    cycle_time = (resolved - created).days
                    cycle_times.append(cycle_time)
            
            if cycle_times:
                avg_cycle_time = sum(cycle_times) / len(cycle_times)
                min_cycle_time = min(cycle_times)
                max_cycle_time = max(cycle_times)
            else:
                avg_cycle_time = min_cycle_time = max_cycle_time = 0
            
            return {
                "project_key": project_key,
                "average_cycle_time_days": round(avg_cycle_time, 2),
                "min_cycle_time_days": min_cycle_time,
                "max_cycle_time_days": max_cycle_time,
                "total_completed_issues": len(cycle_times),
                "analysis_period": f"{days} days"
            }
        except Exception as e:
            print(f"Error calculating cycle time: {e}")
            return {}
    
    def create_issue(self, project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> Dict:
        """Create a new issue."""
        try:
            url = f"{self.api_url}/rest/api/2/issue"
            data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type}
                }
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            return {
                "key": result["key"],
                "id": result["id"],
                "url": f"{self.api_url}/browse/{result['key']}"
            }
        except requests.RequestException as e:
            print(f"Error creating JIRA issue: {e}")
            return {}
    
    def update_issue(self, issue_key: str, fields: Dict) -> bool:
        """Update an existing issue."""
        try:
            url = f"{self.api_url}/rest/api/2/issue/{issue_key}"
            data = {"fields": fields}
            
            response = requests.put(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            return True
        except requests.RequestException as e:
            print(f"Error updating JIRA issue: {e}")
            return False
    
    def sync_project_data(self, project_key: str) -> Dict:
        """Sync all project data from JIRA."""
        try:
            project_info = next((p for p in self.get_projects() if p["key"] == project_key), None)
            if not project_info:
                return {"error": "Project not found"}
            
            issues = self.get_project_issues(project_key)
            velocity = self.get_project_velocity(project_key)
            cycle_time = self.get_issue_cycle_time(project_key)
            
            return {
                "project_key": project_key,
                "project_info": project_info,
                "issues": issues,
                "velocity_metrics": velocity,
                "cycle_time_metrics": cycle_time,
                "synced_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error syncing JIRA project data: {e}")
            return {"error": str(e)}
