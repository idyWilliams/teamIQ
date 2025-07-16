from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.skill import Skill, UserSkill, SkillCategory
from app.models.team import Team, TeamMember
from app.services.github_service import GitHubService
from app.services.jira_service import JiraService
import statistics


class SkillService:
    def __init__(self, db: Session):
        self.db = db
        self.github_service = GitHubService()
        self.jira_service = JiraService()
    
    def calculate_skill_score(self, user_id: int, skill_id: int) -> float:
        """Calculate skill score based on various metrics."""
        user = self.db.query(User).filter(User.id == user_id).first()
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        
        if not user or not skill:
            return 0.0
        
        # Get existing user skill record
        user_skill = self.db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id
        ).first()
        
        if not user_skill:
            return 0.0
        
        # Calculate score based on different factors
        score = 0.0
        
        # GitHub contributions weight: 40%
        if user.github_username and user_skill.github_commits > 0:
            # Normalize commits (assuming 100 commits = 100% for this skill)
            commit_score = min(user_skill.github_commits / 100.0, 1.0)
            score += commit_score * 0.4
        
        # Code reviews weight: 30%
        if user_skill.code_reviews > 0:
            # Normalize code reviews (assuming 50 reviews = 100% for this skill)
            review_score = min(user_skill.code_reviews / 50.0, 1.0)
            score += review_score * 0.3
        
        # JIRA tickets weight: 20%
        if user_skill.jira_tickets > 0:
            # Normalize tickets (assuming 20 tickets = 100% for this skill)
            ticket_score = min(user_skill.jira_tickets / 20.0, 1.0)
            score += ticket_score * 0.2
        
        # Peer review score weight: 10%
        if user_skill.peer_reviews_score > 0:
            # Peer review score is already normalized (0-1)
            score += user_skill.peer_reviews_score * 0.1
        
        # Convert to 0-10 scale
        return min(score * 10, 10.0)
    
    def update_skill_from_github(self, user_id: int, skill_name: str, commits: int):
        """Update skill score based on GitHub activity."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.github_username:
            return
        
        skill = self.db.query(Skill).filter(Skill.name == skill_name).first()
        if not skill:
            return
        
        user_skill = self.db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill.id
        ).first()
        
        if not user_skill:
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill.id,
                github_commits=commits
            )
            self.db.add(user_skill)
        else:
            user_skill.github_commits = commits
        
        # Recalculate proficiency score
        user_skill.proficiency_score = self.calculate_skill_score(user_id, skill.id)
        self.db.commit()
    
    def update_skill_from_jira(self, user_id: int, skill_name: str, tickets: int):
        """Update skill score based on JIRA activity."""
        skill = self.db.query(Skill).filter(Skill.name == skill_name).first()
        if not skill:
            return
        
        user_skill = self.db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill.id
        ).first()
        
        if not user_skill:
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill.id,
                jira_tickets=tickets
            )
            self.db.add(user_skill)
        else:
            user_skill.jira_tickets = tickets
        
        # Recalculate proficiency score
        user_skill.proficiency_score = self.calculate_skill_score(user_id, skill.id)
        self.db.commit()
    
    def get_user_skill_analytics(self, user_id: int) -> List[Dict]:
        """Get skill analytics for a user."""
        user_skills = self.db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
        
        analytics = []
        for user_skill in user_skills:
            analytics.append({
                "skill_name": user_skill.skill.name,
                "category": user_skill.skill.category.value,
                "proficiency_score": user_skill.proficiency_score,
                "github_commits": user_skill.github_commits,
                "code_reviews": user_skill.code_reviews,
                "jira_tickets": user_skill.jira_tickets,
                "peer_reviews_score": user_skill.peer_reviews_score,
                "last_updated": user_skill.last_updated.isoformat()
            })
        
        return analytics
    
    def get_team_skill_matrix(self, team_id: int) -> Dict:
        """Get skill matrix for a team."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {}
        
        # Get all team members
        team_members = self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.is_active == True
        ).all()
        
        # Get all skills for team members
        skill_data = {}
        for member in team_members:
            user_skills = self.db.query(UserSkill).filter(
                UserSkill.user_id == member.user_id
            ).all()
            
            for user_skill in user_skills:
                skill_name = user_skill.skill.name
                if skill_name not in skill_data:
                    skill_data[skill_name] = {
                        "skill_name": skill_name,
                        "category": user_skill.skill.category.value,
                        "team_members": [],
                        "average_score": 0.0,
                        "skill_distribution": {"beginner": 0, "intermediate": 0, "advanced": 0}
                    }
                
                skill_data[skill_name]["team_members"].append({
                    "user_id": member.user_id,
                    "username": member.user.username,
                    "full_name": member.user.full_name,
                    "proficiency_score": user_skill.proficiency_score
                })
        
        # Calculate averages and distributions
        for skill_name, data in skill_data.items():
            scores = [member["proficiency_score"] for member in data["team_members"]]
            data["average_score"] = statistics.mean(scores) if scores else 0.0
            
            # Categorize skill levels
            for score in scores:
                if score < 4:
                    data["skill_distribution"]["beginner"] += 1
                elif score < 7:
                    data["skill_distribution"]["intermediate"] += 1
                else:
                    data["skill_distribution"]["advanced"] += 1
        
        return {
            "team_id": team_id,
            "team_name": team.name,
            "skills": list(skill_data.values())
        }
    
    def identify_skill_gaps(self, team_id: int, required_skills: List[str]) -> List[Dict]:
        """Identify skill gaps in a team."""
        team_skills = self.get_team_skill_matrix(team_id)
        
        gaps = []
        for required_skill in required_skills:
            skill_found = False
            for team_skill in team_skills.get("skills", []):
                if team_skill["skill_name"] == required_skill:
                    skill_found = True
                    if team_skill["average_score"] < 5.0:  # Below average threshold
                        gaps.append({
                            "skill_name": required_skill,
                            "current_average": team_skill["average_score"],
                            "gap_severity": "high" if team_skill["average_score"] < 3.0 else "medium",
                            "team_members_with_skill": len(team_skill["team_members"]),
                            "recommendation": f"Consider training or hiring for {required_skill}"
                        })
                    break
            
            if not skill_found:
                gaps.append({
                    "skill_name": required_skill,
                    "current_average": 0.0,
                    "gap_severity": "critical",
                    "team_members_with_skill": 0,
                    "recommendation": f"No team members have {required_skill} - urgent hiring/training needed"
                })
        
        return gaps
    
    def get_skill_recommendations(self, user_id: int) -> List[Dict]:
        """Get skill recommendations for a user."""
        user_skills = self.db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
        
        recommendations = []
        
        # Find skills that need improvement (score < 5)
        for user_skill in user_skills:
            if user_skill.proficiency_score < 5.0:
                recommendations.append({
                    "skill_name": user_skill.skill.name,
                    "current_score": user_skill.proficiency_score,
                    "recommendation_type": "improve",
                    "suggestion": f"Consider more practice with {user_skill.skill.name}",
                    "priority": "high" if user_skill.proficiency_score < 3.0 else "medium"
                })
        
        # Suggest related skills based on current strengths
        strong_skills = [us for us in user_skills if us.proficiency_score >= 7.0]
        if strong_skills:
            for strong_skill in strong_skills[:3]:  # Top 3 strong skills
                if strong_skill.skill.category == SkillCategory.PROGRAMMING_LANGUAGE:
                    recommendations.append({
                        "skill_name": f"Advanced {strong_skill.skill.name}",
                        "current_score": 0.0,
                        "recommendation_type": "learn",
                        "suggestion": f"Build on your {strong_skill.skill.name} expertise",
                        "priority": "low"
                    })
        
        return recommendations
