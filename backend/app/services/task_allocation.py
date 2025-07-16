import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class TaskAllocationEngine:
    def __init__(self):
        self.allocation_weights = {
            "skill_match": 0.4,
            "workload_balance": 0.2,
            "growth_opportunity": 0.2,
            "collaboration_fit": 0.1,
            "availability": 0.1
        }

    def allocate_tasks(self, tasks: List[Dict], team_members: List[Dict], team_skills: List[Dict]) -> List[Dict]:
        """Allocate tasks to team members using AI recommendations."""
        try:
            recommendations = []
            
            # Create skill matrices
            member_skill_matrix = self._create_member_skill_matrix(team_members, team_skills)
            task_requirement_matrix = self._create_task_requirement_matrix(tasks)
            
            # Calculate workload for each member
            member_workloads = self._calculate_member_workloads(team_members)
            
            for task in tasks:
                if task.get("assignee_id"):
                    continue  # Skip already assigned tasks
                
                recommendation = self._recommend_assignee(
                    task, 
                    team_members, 
                    member_skill_matrix, 
                    member_workloads
                )
                
                if recommendation:
                    recommendations.append(recommendation)
            
            return recommendations
        except Exception as e:
            logger.error(f"Error in task allocation: {e}")
            return []

    def _create_member_skill_matrix(self, team_members: List[Dict], team_skills: List[Dict]) -> Dict:
        """Create skill matrix for team members."""
        try:
            # Get unique skills
            all_skills = list(set(skill["name"] for skill in team_skills))
            
            # Create member skill map
            member_skills = {}
            for member in team_members:
                member_id = member["id"]
                member_skills[member_id] = {skill: 0 for skill in all_skills}
            
            # Populate skills
            for skill in team_skills:
                member_id = skill["user_id"]
                skill_name = skill["name"]
                if member_id in member_skills:
                    member_skills[member_id][skill_name] = skill["proficiency_level"]
            
            return {
                "skills": all_skills,
                "members": member_skills
            }
        except Exception as e:
            logger.error(f"Error creating member skill matrix: {e}")
            return {"skills": [], "members": {}}

    def _create_task_requirement_matrix(self, tasks: List[Dict]) -> Dict:
        """Create task requirement matrix."""
        try:
            task_requirements = {}
            
            for task in tasks:
                task_id = task["id"]
                # In a real implementation, this would come from task_skills table
                # For now, we'll infer from task description and title
                requirements = self._infer_task_requirements(task)
                task_requirements[task_id] = requirements
            
            return task_requirements
        except Exception as e:
            logger.error(f"Error creating task requirement matrix: {e}")
            return {}

    def _infer_task_requirements(self, task: Dict) -> Dict:
        """Infer skill requirements from task description."""
        try:
            title = task.get("title", "").lower()
            description = task.get("description", "").lower()
            text = f"{title} {description}"
            
            # Simple keyword-based inference
            skill_keywords = {
                "Python": ["python", "django", "flask", "fastapi"],
                "JavaScript": ["javascript", "js", "node", "express"],
                "React": ["react", "jsx", "frontend"],
                "TypeScript": ["typescript", "ts"],
                "SQL": ["sql", "database", "query", "postgresql", "mysql"],
                "Docker": ["docker", "container", "deployment"],
                "AWS": ["aws", "cloud", "s3", "ec2"],
                "Testing": ["test", "testing", "unit test", "integration"],
                "API": ["api", "rest", "endpoint", "service"],
                "UI/UX": ["ui", "ux", "design", "interface"]
            }
            
            requirements = {}
            for skill, keywords in skill_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                if score > 0:
                    # Normalize score to 1-5 scale
                    requirements[skill] = min(5, max(1, score))
            
            return requirements
        except Exception as e:
            logger.error(f"Error inferring task requirements: {e}")
            return {}

    def _calculate_member_workloads(self, team_members: List[Dict]) -> Dict:
        """Calculate current workload for each team member."""
        try:
            workloads = {}
            
            for member in team_members:
                member_id = member["id"]
                # In a real implementation, this would query current tasks
                # For now, we'll simulate workload calculation
                
                # This would be calculated from:
                # 1. Current open tasks
                # 2. Estimated hours remaining
                # 3. Sprint capacity
                
                # Simulated workload (0-100%)
                workloads[member_id] = {
                    "current_load": np.random.randint(30, 90),  # Simulated current load
                    "capacity": 100,
                    "available_hours": np.random.randint(10, 40)
                }
            
            return workloads
        except Exception as e:
            logger.error(f"Error calculating member workloads: {e}")
            return {}

    def _recommend_assignee(self, task: Dict, team_members: List[Dict], 
                          member_skill_matrix: Dict, member_workloads: Dict) -> Optional[Dict]:
        """Recommend the best assignee for a task."""
        try:
            task_id = task["id"]
            task_requirements = self._infer_task_requirements(task)
            
            if not task_requirements:
                return None
            
            recommendations = []
            
            for member in team_members:
                member_id = member["id"]
                
                # Calculate skill match score
                skill_match = self._calculate_skill_match(
                    task_requirements, 
                    member_skill_matrix["members"].get(member_id, {})
                )
                
                # Calculate workload score (lower workload = higher score)
                workload_data = member_workloads.get(member_id, {})
                workload_score = max(0, 100 - workload_data.get("current_load", 100)) / 100
                
                # Calculate growth opportunity score
                growth_score = self._calculate_growth_opportunity(
                    task_requirements, 
                    member_skill_matrix["members"].get(member_id, {})
                )
                
                # Calculate overall score
                overall_score = (
                    skill_match * self.allocation_weights["skill_match"] +
                    workload_score * self.allocation_weights["workload_balance"] +
                    growth_score * self.allocation_weights["growth_opportunity"]
                )
                
                recommendations.append({
                    "member_id": member_id,
                    "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    "overall_score": overall_score,
                    "skill_match": skill_match,
                    "workload_score": workload_score,
                    "growth_score": growth_score,
                    "rationale": self._generate_rationale(task, member, skill_match, workload_score, growth_score)
                })
            
            # Sort by overall score
            recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
            
            return {
                "task_id": task_id,
                "task_title": task.get("title", ""),
                "recommendations": recommendations[:3],  # Top 3 recommendations
                "suggested_assignee": recommendations[0] if recommendations else None
            }
        except Exception as e:
            logger.error(f"Error recommending assignee: {e}")
            return None

    def _calculate_skill_match(self, task_requirements: Dict, member_skills: Dict) -> float:
        """Calculate how well member skills match task requirements."""
        try:
            if not task_requirements:
                return 0.5  # Neutral score if no requirements
            
            total_match = 0
            total_weight = 0
            
            for skill, required_level in task_requirements.items():
                member_level = member_skills.get(skill, 0)
                
                # Calculate match score (1.0 if member level >= required, scaled down if less)
                if member_level >= required_level:
                    match_score = 1.0
                else:
                    match_score = max(0, member_level / required_level)
                
                total_match += match_score * required_level
                total_weight += required_level
            
            return total_match / total_weight if total_weight > 0 else 0.5
        except Exception as e:
            logger.error(f"Error calculating skill match: {e}")
            return 0.5

    def _calculate_growth_opportunity(self, task_requirements: Dict, member_skills: Dict) -> float:
        """Calculate growth opportunity score."""
        try:
            if not task_requirements:
                return 0.0
            
            growth_score = 0
            skill_count = len(task_requirements)
            
            for skill, required_level in task_requirements.items():
                member_level = member_skills.get(skill, 0)
                
                # Growth opportunity is higher when member level is slightly below required
                if member_level == 0:
                    # New skill - high growth opportunity
                    growth_score += 0.8
                elif member_level < required_level:
                    # Skill improvement opportunity
                    gap = required_level - member_level
                    growth_score += min(0.6, gap / 2)  # Moderate growth opportunity
                else:
                    # Already proficient - low growth opportunity
                    growth_score += 0.1
            
            return growth_score / skill_count if skill_count > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating growth opportunity: {e}")
            return 0.0

    def _generate_rationale(self, task: Dict, member: Dict, skill_match: float, 
                          workload_score: float, growth_score: float) -> str:
        """Generate human-readable rationale for recommendation."""
        try:
            rationale_parts = []
            
            # Skill match rationale
            if skill_match > 0.8:
                rationale_parts.append("Strong skill match")
            elif skill_match > 0.6:
                rationale_parts.append("Good skill match")
            else:
                rationale_parts.append("Skill development opportunity")
            
            # Workload rationale
            if workload_score > 0.7:
                rationale_parts.append("low current workload")
            elif workload_score > 0.4:
                rationale_parts.append("moderate workload")
            else:
                rationale_parts.append("high workload")
            
            # Growth rationale
            if growth_score > 0.6:
                rationale_parts.append("excellent growth opportunity")
            elif growth_score > 0.3:
                rationale_parts.append("some growth potential")
            
            member_name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
            
            return f"{member_name}: {', '.join(rationale_parts)}"
        except Exception as e:
            logger.error(f"Error generating rationale: {e}")
            return "Recommended based on analysis"

    def optimize_team_allocation(self, tasks: List[Dict], team_members: List[Dict], 
                               team_skills: List[Dict]) -> Dict:
        """Optimize allocation across all tasks for the team."""
        try:
            # Get individual recommendations
            individual_recommendations = self.allocate_tasks(tasks, team_members, team_skills)
            
            # Optimize for team balance
            optimized_allocation = self._optimize_workload_balance(
                individual_recommendations, 
                team_members
            )
            
            return {
                "individual_recommendations": individual_recommendations,
                "optimized_allocation": optimized_allocation,
                "team_metrics": self._calculate_team_metrics(optimized_allocation, team_members)
            }
        except Exception as e:
            logger.error(f"Error optimizing team allocation: {e}")
            return {}

    def _optimize_workload_balance(self, recommendations: List[Dict], 
                                 team_members: List[Dict]) -> List[Dict]:
        """Optimize allocation to balance workload across team."""
        try:
            # Simple greedy optimization
            member_task_counts = {member["id"]: 0 for member in team_members}
            optimized = []
            
            for recommendation in recommendations:
                best_assignee = None
                best_score = -1
                
                for candidate in recommendation["recommendations"]:
                    member_id = candidate["member_id"]
                    
                    # Adjust score based on current allocation
                    current_load = member_task_counts.get(member_id, 0)
                    load_penalty = current_load * 0.1  # Penalty for high allocation
                    
                    adjusted_score = candidate["overall_score"] - load_penalty
                    
                    if adjusted_score > best_score:
                        best_score = adjusted_score
                        best_assignee = candidate
                
                if best_assignee:
                    member_task_counts[best_assignee["member_id"]] += 1
                    optimized.append({
                        "task_id": recommendation["task_id"],
                        "task_title": recommendation["task_title"],
                        "assigned_to": best_assignee,
                        "optimization_score": best_score
                    })
            
            return optimized
        except Exception as e:
            logger.error(f"Error optimizing workload balance: {e}")
            return []

    def _calculate_team_metrics(self, allocation: List[Dict], team_members: List[Dict]) -> Dict:
        """Calculate team metrics for the allocation."""
        try:
            member_task_counts = {member["id"]: 0 for member in team_members}
            total_optimization_score = 0
            
            for assignment in allocation:
                member_id = assignment["assigned_to"]["member_id"]
                member_task_counts[member_id] += 1
                total_optimization_score += assignment["optimization_score"]
            
            # Calculate balance metrics
            task_counts = list(member_task_counts.values())
            workload_balance = {
                "min_tasks": min(task_counts) if task_counts else 0,
                "max_tasks": max(task_counts) if task_counts else 0,
                "avg_tasks": sum(task_counts) / len(task_counts) if task_counts else 0,
                "std_dev": np.std(task_counts) if task_counts else 0
            }
            
            return {
                "total_tasks_allocated": len(allocation),
                "average_optimization_score": total_optimization_score / len(allocation) if allocation else 0,
                "workload_balance": workload_balance,
                "team_utilization": len([c for c in task_counts if c > 0]) / len(team_members) if team_members else 0
            }
        except Exception as e:
            logger.error(f"Error calculating team metrics: {e}")
            return {}

task_allocation_engine = TaskAllocationEngine()
