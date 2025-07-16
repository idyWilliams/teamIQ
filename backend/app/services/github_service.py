import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings


class GitHubService:
    def __init__(self):
        self.api_url = settings.GITHUB_API_URL
        self.headers = {
            "Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def check_connection(self) -> bool:
        """Check if GitHub API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/user", headers=self.headers)
            return response.status_code == 200
        except:
            return False
    
    def get_user_repos(self, username: str) -> List[Dict]:
        """Get repositories for a user."""
        try:
            url = f"{self.api_url}/users/{username}/repos"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            repos = response.json()
            return [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description", ""),
                    "language": repo.get("language", ""),
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "url": repo["html_url"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "is_private": repo["private"],
                    "is_fork": repo["fork"]
                }
                for repo in repos
            ]
        except requests.RequestException as e:
            print(f"Error fetching GitHub repos: {e}")
            return []
    
    def get_repo_commits(self, username: str, repo: str, days: int = 30) -> List[Dict]:
        """Get commits for a repository."""
        try:
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            url = f"{self.api_url}/repos/{username}/{repo}/commits"
            params = {"since": since_date}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            commits = response.json()
            return [
                {
                    "sha": commit["sha"],
                    "message": commit["commit"]["message"],
                    "author": commit["commit"]["author"]["name"],
                    "author_email": commit["commit"]["author"]["email"],
                    "date": commit["commit"]["author"]["date"],
                    "url": commit["html_url"],
                    "additions": 0,  # Would need to call individual commit API
                    "deletions": 0,  # Would need to call individual commit API
                    "files_changed": 0  # Would need to call individual commit API
                }
                for commit in commits
            ]
        except requests.RequestException as e:
            print(f"Error fetching GitHub commits: {e}")
            return []
    
    def get_user_stats(self, username: str, days: int = 30) -> Dict:
        """Get comprehensive stats for a user."""
        try:
            # Get user info
            user_url = f"{self.api_url}/users/{username}"
            user_response = requests.get(user_url, headers=self.headers)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            # Get repositories
            repos = self.get_user_repos(username)
            
            # Calculate stats
            total_commits = 0
            total_stars = 0
            total_forks = 0
            languages = {}
            
            for repo in repos:
                if not repo["is_fork"]:  # Skip forked repos
                    total_stars += repo["stars"]
                    total_forks += repo["forks"]
                    
                    if repo["language"]:
                        languages[repo["language"]] = languages.get(repo["language"], 0) + 1
                    
                    # Get recent commits for this repo
                    commits = self.get_repo_commits(username, repo["name"], days)
                    total_commits += len(commits)
            
            # Get pull requests
            prs = self.get_user_pull_requests(username, days)
            
            return {
                "username": username,
                "name": user_info.get("name", ""),
                "bio": user_info.get("bio", ""),
                "location": user_info.get("location", ""),
                "company": user_info.get("company", ""),
                "public_repos": user_info["public_repos"],
                "followers": user_info["followers"],
                "following": user_info["following"],
                "created_at": user_info["created_at"],
                "stats": {
                    "total_commits_last_30_days": total_commits,
                    "total_stars": total_stars,
                    "total_forks": total_forks,
                    "primary_languages": languages,
                    "pull_requests_last_30_days": len(prs),
                    "active_repositories": len([r for r in repos if not r["is_fork"]])
                }
            }
        except requests.RequestException as e:
            print(f"Error fetching GitHub user stats: {e}")
            return {}
    
    def get_user_pull_requests(self, username: str, days: int = 30) -> List[Dict]:
        """Get pull requests for a user."""
        try:
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            url = f"{self.api_url}/search/issues"
            params = {
                "q": f"author:{username} type:pr created:>{since_date[:10]}",
                "sort": "created",
                "order": "desc"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            prs = response.json()["items"]
            return [
                {
                    "title": pr["title"],
                    "number": pr["number"],
                    "state": pr["state"],
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                    "url": pr["html_url"],
                    "repository": pr["repository_url"].split("/")[-1],
                    "labels": [label["name"] for label in pr.get("labels", [])]
                }
                for pr in prs
            ]
        except requests.RequestException as e:
            print(f"Error fetching GitHub pull requests: {e}")
            return []
    
    def get_repo_contributors(self, username: str, repo: str) -> List[Dict]:
        """Get contributors for a repository."""
        try:
            url = f"{self.api_url}/repos/{username}/{repo}/contributors"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            contributors = response.json()
            return [
                {
                    "username": contributor["login"],
                    "contributions": contributor["contributions"],
                    "avatar_url": contributor["avatar_url"],
                    "profile_url": contributor["html_url"]
                }
                for contributor in contributors
            ]
        except requests.RequestException as e:
            print(f"Error fetching GitHub contributors: {e}")
            return []
    
    def get_user_activity(self, username: str, days: int = 7) -> List[Dict]:
        """Get recent activity for a user."""
        try:
            url = f"{self.api_url}/users/{username}/events"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            events = response.json()
            recent_events = []
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            for event in events:
                event_date = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                if event_date < cutoff_date:
                    continue
                
                recent_events.append({
                    "type": event["type"],
                    "repo": event["repo"]["name"],
                    "created_at": event["created_at"],
                    "public": event["public"]
                })
            
            return recent_events
        except requests.RequestException as e:
            print(f"Error fetching GitHub activity: {e}")
            return []
    
    def analyze_code_quality(self, username: str, repo: str) -> Dict:
        """Analyze code quality metrics for a repository."""
        try:
            # Get repository info
            repo_url = f"{self.api_url}/repos/{username}/{repo}"
            repo_response = requests.get(repo_url, headers=self.headers)
            repo_response.raise_for_status()
            repo_info = repo_response.json()
            
            # Get languages
            languages_url = f"{self.api_url}/repos/{username}/{repo}/languages"
            languages_response = requests.get(languages_url, headers=self.headers)
            languages_response.raise_for_status()
            languages = languages_response.json()
            
            # Calculate metrics
            total_bytes = sum(languages.values())
            language_percentages = {
                lang: (bytes_count / total_bytes) * 100 
                for lang, bytes_count in languages.items()
            } if total_bytes > 0 else {}
            
            return {
                "repository": repo,
                "size": repo_info["size"],
                "language_distribution": language_percentages,
                "has_readme": bool(repo_info.get("description")),
                "has_license": bool(repo_info.get("license")),
                "open_issues": repo_info["open_issues_count"],
                "watchers": repo_info["watchers_count"],
                "network_count": repo_info["network_count"],
                "default_branch": repo_info["default_branch"],
                "created_at": repo_info["created_at"],
                "updated_at": repo_info["updated_at"],
                "pushed_at": repo_info["pushed_at"]
            }
        except requests.RequestException as e:
            print(f"Error analyzing code quality: {e}")
            return {}
    
    def get_commit_frequency(self, username: str, repo: str, days: int = 30) -> Dict:
        """Get commit frequency analysis."""
        commits = self.get_repo_commits(username, repo, days)
        
        # Group by date
        daily_commits = {}
        for commit in commits:
            date = commit["date"][:10]  # Extract date part
            daily_commits[date] = daily_commits.get(date, 0) + 1
        
        # Calculate metrics
        total_commits = len(commits)
        avg_commits_per_day = total_commits / days if days > 0 else 0
        
        return {
            "total_commits": total_commits,
            "average_commits_per_day": round(avg_commits_per_day, 2),
            "daily_breakdown": daily_commits,
            "most_active_day": max(daily_commits.keys(), key=lambda x: daily_commits[x]) if daily_commits else None,
            "analysis_period": f"{days} days"
        }
    
    def sync_user_data(self, username: str) -> Dict:
        """Sync all user data from GitHub."""
        try:
            user_stats = self.get_user_stats(username)
            repos = self.get_user_repos(username)
            activity = self.get_user_activity(username)
            
            return {
                "username": username,
                "user_stats": user_stats,
                "repositories": repos,
                "recent_activity": activity,
                "synced_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error syncing GitHub data: {e}")
            return {"error": str(e)}
