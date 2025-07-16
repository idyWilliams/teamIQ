import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class SkillAnalytics:
    def __init__(self):
        self.skill_weights = {
            "commits": 0.3,
            "pr_reviews": 0.2,
            "code_quality": 0.2,
            "task_completion": 0.2,
            "collaboration": 0.1
        }
        
        self.language_skills = {
            "py": "Python",
            "js": "JavaScript",
            "ts": "TypeScript",
            "jsx": "React",
            "tsx": "React",
            "html": "HTML",
            "css": "CSS",
            "java": "Java",
            "cpp": "C++",
            "c": "C",
            "go": "Go",
            "rs": "Rust",
            "php": "PHP",
            "rb": "Ruby",
            "sql": "SQL"
        }

    def calculate_skill_score(self, github_data: Dict, jira_data: Dict, skill_name: str) -> float:
        """Calculate skill score based on multiple data sources."""
        try:
            score = 0.0
            
            # GitHub-based scoring
            if github_data:
                score += self._calculate_github_skill_score(github_data, skill_name)
            
            # Jira-based scoring
            if jira_data:
                score += self._calculate_jira_skill_score(jira_data, skill_name)
            
            # Normalize to 0-5 scale
            return min(5.0, max(0.0, score))
        except Exception as e:
            logger.error(f"Error calculating skill score: {e}")
            return 0.0

    def _calculate_github_skill_score(self, github_data: Dict, skill_name: str) -> float:
        """Calculate skill score from GitHub data."""
        commits = github_data.get("commits", [])
        prs = github_data.get("pull_requests", [])
        
        score = 0.0
        
        # Language-specific scoring
        if skill_name in self.language_skills.values():
            file_extension = self._get_file_extension_for_skill(skill_name)
            
            # Count commits with this language
            language_commits = 0
            total_lines = 0
            
            for commit in commits:
                # This would be populated by the GitHub integration
                files = commit.get("files", [])
                for file in files:
                    if file.get("filename", "").endswith(file_extension):
                        language_commits += 1
                        total_lines += file.get("additions", 0)
            
            # Base score from commit frequency
            if language_commits > 0:
                score += min(2.0, language_commits / 10)  # Up to 2 points for commits
                score += min(1.0, total_lines / 1000)     # Up to 1 point for lines of code
        
        # PR review scoring
        collaboration_metrics = github_data.get("collaboration_metrics", {})
        for repo_metrics in collaboration_metrics.values():
            reviews_given = repo_metrics.get("reviews_given", 0)
            score += min(1.0, reviews_given / 20)  # Up to 1 point for reviews
        
        return score

    def _calculate_jira_skill_score(self, jira_data: Dict, skill_name: str) -> float:
        """Calculate skill score from Jira data."""
        performance_metrics = jira_data.get("performance_metrics", {})
        
        score = 0.0
        
        # Task completion scoring
        for project_metrics in performance_metrics.values():
            completion_rate = project_metrics.get("completion_rate", 0) / 100
            velocity = project_metrics.get("velocity", 0)
            
            score += completion_rate * 0.5  # Up to 0.5 points for completion rate
            score += min(1.0, velocity / 20)  # Up to 1 point for velocity
        
        return score

    def _get_file_extension_for_skill(self, skill_name: str) -> str:
        """Get file extension for a skill."""
        extension_map = {
            "Python": ".py",
            "JavaScript": ".js",
            "TypeScript": ".ts",
            "React": ".jsx",
            "HTML": ".html",
            "CSS": ".css",
            "Java": ".java",
            "C++": ".cpp",
            "C": ".c",
            "Go": ".go",
            "Rust": ".rs",
            "PHP": ".php",
            "Ruby": ".rb",
            "SQL": ".sql"
        }
        return extension_map.get(skill_name, "")

    def generate_skill_radar_data(self, user_skills: List[Dict]) -> Dict:
        """Generate radar chart data for user skills."""
        try:
            # Get top skills by proficiency
            top_skills = sorted(user_skills, key=lambda x: x.get("proficiency_level", 0), reverse=True)[:8]
            
            labels = []
            values = []
            
            for skill in top_skills:
                labels.append(skill.get("name", ""))
                values.append(skill.get("proficiency_level", 0))
            
            # Ensure we have at least 5 skills for a good radar chart
            while len(labels) < 5:
                labels.append("")
                values.append(0)
            
            return {
                "labels": labels,
                "values": values,
                "max_value": 5
            }
        except Exception as e:
            logger.error(f"Error generating radar data: {e}")
            return {"labels": [], "values": [], "max_value": 5}

    def calculate_skill_growth(self, user_id: int, skill_id: int, days: int = 30) -> Dict:
        """Calculate skill growth over time."""
        try:
            # This would query historical skill data from the database
            # For now, we'll simulate growth calculation
            
            # In a real implementation, this would:
            # 1. Get historical skill scores from skill_evidence table
            # 2. Calculate growth rate over the specified period
            # 3. Identify key contributors to growth
            
            # Simulated growth data
            growth_data = {
                "current_level": 3.2,
                "previous_level": 2.8,
                "growth_rate": 14.3,  # Percentage
                "growth_trend": "up",
                "key_contributors": [
                    {"type": "github_commits", "impact": 0.2},
                    {"type": "pr_reviews", "impact": 0.1},
                    {"type": "task_completion", "impact": 0.1}
                ],
                "period_days": days
            }
            
            return growth_data
        except Exception as e:
            logger.error(f"Error calculating skill growth: {e}")
            return {}

    def analyze_skill_gaps(self, user_skills: List[Dict], project_requirements: List[Dict]) -> List[Dict]:
        """Analyze skill gaps for project requirements."""
        try:
            gaps = []
            
            # Create skill lookup
            user_skill_map = {skill["name"]: skill["proficiency_level"] for skill in user_skills}
            
            for requirement in project_requirements:
                skill_name = requirement.get("skill_name")
                required_level = requirement.get("required_level", 0)
                current_level = user_skill_map.get(skill_name, 0)
                
                if current_level < required_level:
                    gap = {
                        "skill_name": skill_name,
                        "required_level": required_level,
                        "current_level": current_level,
                        "gap_size": required_level - current_level,
                        "priority": requirement.get("priority", "medium")
                    }
                    gaps.append(gap)
            
            # Sort by gap size (largest gaps first)
            gaps.sort(key=lambda x: x["gap_size"], reverse=True)
            
            return gaps
        except Exception as e:
            logger.error(f"Error analyzing skill gaps: {e}")
            return []

    def generate_skill_recommendations(self, user_skills: List[Dict], team_skills: List[Dict]) -> List[Dict]:
        """Generate skill development recommendations."""
        try:
            recommendations = []
            
            # Analyze team skill distribution
            team_skill_map = {}
            for skill in team_skills:
                skill_name = skill.get("name")
                if skill_name not in team_skill_map:
                    team_skill_map[skill_name] = []
                team_skill_map[skill_name].append(skill.get("proficiency_level", 0))
            
            # Calculate average team proficiency for each skill
            team_averages = {}
            for skill_name, levels in team_skill_map.items():
                team_averages[skill_name] = sum(levels) / len(levels)
            
            # Generate recommendations based on gaps
            user_skill_map = {skill["name"]: skill["proficiency_level"] for skill in user_skills}
            
            for skill_name, team_avg in team_averages.items():
                user_level = user_skill_map.get(skill_name, 0)
                
                if user_level < team_avg - 1:  # Significant gap
                    recommendation = {
                        "skill_name": skill_name,
                        "current_level": user_level,
                        "target_level": team_avg,
                        "priority": "high" if team_avg - user_level > 2 else "medium",
                        "recommendation_type": "catch_up",
                        "suggested_actions": [
                            f"Practice {skill_name} through targeted exercises",
                            f"Pair with team members strong in {skill_name}",
                            f"Take on tasks requiring {skill_name}"
                        ]
                    }
                    recommendations.append(recommendation)
            
            return recommendations[:5]  # Return top 5 recommendations
        except Exception as e:
            logger.error(f"Error generating skill recommendations: {e}")
            return []

    def calculate_team_skill_matrix(self, team_members: List[Dict], team_skills: List[Dict]) -> Dict:
        """Calculate team skill matrix for visualization."""
        try:
            # Create member skill map
            member_skills = {}
            for member in team_members:
                member_id = member.get("id")
                member_skills[member_id] = {
                    "name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    "skills": {}
                }
            
            # Populate skills
            for skill in team_skills:
                member_id = skill.get("user_id")
                if member_id in member_skills:
                    member_skills[member_id]["skills"][skill.get("name")] = skill.get("proficiency_level", 0)
            
            # Get unique skills
            all_skills = set()
            for member_data in member_skills.values():
                all_skills.update(member_data["skills"].keys())
            
            # Create matrix
            matrix = {
                "skills": sorted(list(all_skills)),
                "members": [],
                "data": []
            }
            
            for member_id, member_data in member_skills.items():
                matrix["members"].append(member_data["name"])
                member_row = []
                
                for skill in matrix["skills"]:
                    member_row.append(member_data["skills"].get(skill, 0))
                
                matrix["data"].append(member_row)
            
            return matrix
        except Exception as e:
            logger.error(f"Error calculating team skill matrix: {e}")
            return {"skills": [], "members": [], "data": []}

skill_analytics = SkillAnalytics()
