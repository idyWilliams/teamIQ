from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.task import Task, TaskAssignment, TaskStatus
from app.models.skill import UserSkill
from app.models.project import Project, ProjectMember
from app.services.ai_service import AIService
import random


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    def get_ai_task_recommendations(self, project_id: int, task_ids: List[int]) -> List[Dict]:
        """Get AI-powered task allocation recommendations."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return []
        
        # Get project members
        project_members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        ).all()
        
        # Get tasks
        tasks = self.db.query(Task).filter(Task.id.in_(task_ids)).all()
        
        recommendations = []
        
        for task in tasks:
            # Find the best member for this task
            best_match = self.find_best_task_assignment(task, project_members)
            
            if best_match:
                recommendations.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "user_id": best_match["user_id"],
                    "username": best_match["username"],
                    "score": best_match["score"],
                    "reason": best_match["reason"]
                })
        
        return recommendations
    
    def find_best_task_assignment(self, task: Task, project_members: List) -> Optional[Dict]:
        """Find the best team member for a task using AI/ML techniques."""
        
        # Extract skill requirements from task description using AI
        skill_requirements = self.ai_service.extract_skills_from_task(task.description or task.title)
        
        best_match = None
        best_score = 0.0
        
        for member in project_members:
            user = member.user
            
            # Get user's skills
            user_skills = self.db.query(UserSkill).filter(UserSkill.user_id == user.id).all()
            
            # Calculate match score
            score = self.calculate_task_user_match_score(task, user, user_skills, skill_requirements)
            
            if score > best_score:
                best_score = score
                best_match = {
                    "user_id": user.id,
                    "username": user.username,
                    "score": score,
                    "reason": self.generate_assignment_reason(task, user, user_skills, skill_requirements)
                }
        
        return best_match
    
    def calculate_task_user_match_score(self, task: Task, user: User, user_skills: List, skill_requirements: List[str]) -> float:
        """Calculate how well a user matches a task."""
        score = 0.0
        
        # Skill match score (60% weight)
        skill_score = self.calculate_skill_match_score(user_skills, skill_requirements)
        score += skill_score * 0.6
        
        # Workload score (20% weight) - prefer less loaded users
        workload_score = self.calculate_workload_score(user.id)
        score += workload_score * 0.2
        
        # Experience score (10% weight) - based on completed tasks
        experience_score = self.calculate_experience_score(user.id)
        score += experience_score * 0.1
        
        # Growth opportunity score (10% weight) - prefer tasks that help user grow
        growth_score = self.calculate_growth_score(user_skills, skill_requirements)
        score += growth_score * 0.1
        
        return score
    
    def calculate_skill_match_score(self, user_skills: List, skill_requirements: List[str]) -> float:
        """Calculate how well user skills match task requirements."""
        if not skill_requirements:
            return 0.5  # Neutral score if no specific skills required
        
        skill_dict = {skill.skill.name.lower(): skill.proficiency_score for skill in user_skills}
        
        total_score = 0.0
        for required_skill in skill_requirements:
            skill_name = required_skill.lower()
            if skill_name in skill_dict:
                # Normalize skill score from 0-10 to 0-1
                total_score += skill_dict[skill_name] / 10.0
            else:
                # Penalty for missing skill
                total_score += 0.0
        
        return total_score / len(skill_requirements) if skill_requirements else 0.0
    
    def calculate_workload_score(self, user_id: int) -> float:
        """Calculate workload score (higher score = less loaded)."""
        # Count active task assignments
        active_tasks = self.db.query(TaskAssignment).join(Task).filter(
            TaskAssignment.user_id == user_id,
            TaskAssignment.is_active == True,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
        ).count()
        
        # Convert to score (inverse relationship)
        if active_tasks == 0:
            return 1.0
        elif active_tasks <= 3:
            return 0.8
        elif active_tasks <= 6:
            return 0.5
        else:
            return 0.2
    
    def calculate_experience_score(self, user_id: int) -> float:
        """Calculate experience score based on completed tasks."""
        completed_tasks = self.db.query(TaskAssignment).join(Task).filter(
            TaskAssignment.user_id == user_id,
            TaskAssignment.is_active == True,
            Task.status == TaskStatus.DONE
        ).count()
        
        # Normalize experience (assuming 20 completed tasks = high experience)
        return min(completed_tasks / 20.0, 1.0)
    
    def calculate_growth_score(self, user_skills: List, skill_requirements: List[str]) -> float:
        """Calculate growth opportunity score."""
        if not skill_requirements:
            return 0.0
        
        skill_dict = {skill.skill.name.lower(): skill.proficiency_score for skill in user_skills}
        
        growth_potential = 0.0
        for required_skill in skill_requirements:
            skill_name = required_skill.lower()
            if skill_name in skill_dict:
                current_score = skill_dict[skill_name]
                # Growth potential is higher for skills that are not yet mastered
                growth_potential += (10.0 - current_score) / 10.0
            else:
                # New skill = high growth potential
                growth_potential += 1.0
        
        return growth_potential / len(skill_requirements)
    
    def generate_assignment_reason(self, task: Task, user: User, user_skills: List, skill_requirements: List[str]) -> str:
        """Generate human-readable reason for task assignment."""
        reasons = []
        
        # Check skill matches
        skill_dict = {skill.skill.name.lower(): skill.proficiency_score for skill in user_skills}
        matching_skills = []
        for required_skill in skill_requirements:
            if required_skill.lower() in skill_dict:
                score = skill_dict[required_skill.lower()]
                if score >= 7.0:
                    matching_skills.append(f"Strong {required_skill} skills")
                elif score >= 5.0:
                    matching_skills.append(f"Good {required_skill} skills")
        
        if matching_skills:
            reasons.append(f"Has {', '.join(matching_skills)}")
        
        # Check workload
        active_tasks = self.db.query(TaskAssignment).join(Task).filter(
            TaskAssignment.user_id == user.id,
            TaskAssignment.is_active == True,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
        ).count()
        
        if active_tasks <= 2:
            reasons.append("Currently available")
        elif active_tasks <= 4:
            reasons.append("Manageable workload")
        
        # Check for growth opportunity
        new_skills = [skill for skill in skill_requirements if skill.lower() not in skill_dict]
        if new_skills:
            reasons.append(f"Growth opportunity in {', '.join(new_skills)}")
        
        return "; ".join(reasons) if reasons else "Good overall match"
    
    def get_task_analytics(self, user_id: int) -> Dict:
        """Get task analytics for a user."""
        # Get all task assignments for the user
        assignments = self.db.query(TaskAssignment).join(Task).filter(
            TaskAssignment.user_id == user_id,
            TaskAssignment.is_active == True
        ).all()
        
        if not assignments:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "todo_tasks": 0,
                "completion_rate": 0.0,
                "average_completion_time": 0.0
            }
        
        # Count tasks by status
        total_tasks = len(assignments)
        completed_tasks = sum(1 for a in assignments if a.task.status == TaskStatus.DONE)
        in_progress_tasks = sum(1 for a in assignments if a.task.status == TaskStatus.IN_PROGRESS)
        todo_tasks = sum(1 for a in assignments if a.task.status == TaskStatus.TODO)
        
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0.0
        
        # Calculate average completion time (simplified)
        completed_assignments = [a for a in assignments if a.task.status == TaskStatus.DONE and a.task.completed_at]
        if completed_assignments:
            total_time = sum(
                (a.task.completed_at - a.assigned_at).days
                for a in completed_assignments
            )
            average_completion_time = total_time / len(completed_assignments)
        else:
            average_completion_time = 0.0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "todo_tasks": todo_tasks,
            "completion_rate": completion_rate,
            "average_completion_time": average_completion_time
        }
    
    def get_team_task_analytics(self, team_id: int) -> Dict:
        """Get task analytics for a team."""
        # This would require joining with team members and their tasks
        # Implementation would depend on the specific team structure
        return {
            "message": "Team task analytics not implemented yet"
        }
