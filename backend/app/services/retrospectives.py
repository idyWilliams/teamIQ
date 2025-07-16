import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from openai import OpenAI

from models.database import get_project_tasks, get_team_communications, get_user_skills

logger = logging.getLogger(__name__)

class RetrospectiveService:
    def __init__(self):
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your-openai-key-here")
        )

    async def generate_retrospective(self, project_id: int, team_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """Generate an AI-powered retrospective report."""
        try:
            # Gather data for the retrospective
            retrospective_data = await self._gather_retrospective_data(
                project_id, team_id, period_start, period_end
            )
            
            # Generate AI analysis
            ai_analysis = await self._generate_ai_analysis(retrospective_data)
            
            # Compile final retrospective
            retrospective = {
                "project_id": project_id,
                "team_id": team_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "summary": ai_analysis.get("summary", ""),
                "achievements": ai_analysis.get("achievements", []),
                "challenges": ai_analysis.get("challenges", []),
                "performance_metrics": retrospective_data["performance_metrics"],
                "skill_insights": ai_analysis.get("skill_insights", {}),
                "sentiment_trends": retrospective_data["sentiment_analysis"],
                "action_items": ai_analysis.get("action_items", []),
                "recommendations": ai_analysis.get("recommendations", []),
                "generated_at": datetime.now().isoformat()
            }
            
            return retrospective
            
        except Exception as e:
            logger.error(f"Error generating retrospective: {e}")
            return self._empty_retrospective(project_id, team_id, period_start, period_end)

    async def _gather_retrospective_data(self, project_id: int, team_id: int, 
                                       period_start: datetime, period_end: datetime) -> Dict:
        """Gather all necessary data for retrospective generation."""
        try:
            # Get project tasks
            tasks = await get_project_tasks(project_id)
            
            # Filter tasks by period
            period_tasks = [
                task for task in tasks
                if self._is_task_in_period(task, period_start, period_end)
            ]
            
            # Get team communications
            communications = await get_team_communications(team_id)
            
            # Filter communications by period
            period_communications = [
                comm for comm in communications
                if period_start <= datetime.fromisoformat(comm["timestamp"]) <= period_end
            ]
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(period_tasks)
            
            # Analyze sentiment trends
            sentiment_analysis = self._analyze_sentiment_trends(period_communications)
            
            # Get skill data
            skill_insights = await self._analyze_skill_development(team_id, period_start, period_end)
            
            return {
                "tasks": period_tasks,
                "communications": period_communications,
                "performance_metrics": performance_metrics,
                "sentiment_analysis": sentiment_analysis,
                "skill_insights": skill_insights,
                "period_start": period_start,
                "period_end": period_end
            }
            
        except Exception as e:
            logger.error(f"Error gathering retrospective data: {e}")
            return {}

    def _is_task_in_period(self, task: Dict, start: datetime, end: datetime) -> bool:
        """Check if a task falls within the retrospective period."""
        try:
            task_created = datetime.fromisoformat(task.get("created_at", ""))
            task_updated = datetime.fromisoformat(task.get("updated_at", ""))
            
            # Task is in period if it was created or updated during the period
            return (start <= task_created <= end) or (start <= task_updated <= end)
            
        except Exception:
            return False

    def _calculate_performance_metrics(self, tasks: List[Dict]) -> Dict:
        """Calculate performance metrics from tasks."""
        try:
            if not tasks:
                return self._empty_performance_metrics()
            
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get("status") == "done"])
            in_progress_tasks = len([t for t in tasks if t.get("status") == "in_progress"])
            
            # Calculate story points
            total_story_points = sum(t.get("story_points", 0) for t in tasks)
            completed_story_points = sum(
                t.get("story_points", 0) for t in tasks if t.get("status") == "done"
            )
            
            # Calculate time metrics
            total_estimated_hours = sum(t.get("estimated_hours", 0) for t in tasks)
            total_actual_hours = sum(t.get("actual_hours", 0) for t in tasks)
            
            # Calculate velocity (completed story points)
            velocity = completed_story_points
            
            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Calculate cycle time for completed tasks
            cycle_times = []
            for task in tasks:
                if task.get("status") == "done" and task.get("completed_at"):
                    created = datetime.fromisoformat(task.get("created_at", ""))
                    completed = datetime.fromisoformat(task.get("completed_at", ""))
                    cycle_time = (completed - created).days
                    cycle_times.append(cycle_time)
            
            avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
            
            # Calculate estimation accuracy
            estimation_accuracy = 100
            if total_actual_hours > 0 and total_estimated_hours > 0:
                estimation_accuracy = min(100, (total_estimated_hours / total_actual_hours) * 100)
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "completion_rate": completion_rate,
                "total_story_points": total_story_points,
                "completed_story_points": completed_story_points,
                "velocity": velocity,
                "total_estimated_hours": total_estimated_hours,
                "total_actual_hours": total_actual_hours,
                "average_cycle_time_days": avg_cycle_time,
                "estimation_accuracy": estimation_accuracy
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return self._empty_performance_metrics()

    def _empty_performance_metrics(self) -> Dict:
        """Return empty performance metrics structure."""
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "completion_rate": 0,
            "total_story_points": 0,
            "completed_story_points": 0,
            "velocity": 0,
            "total_estimated_hours": 0,
            "total_actual_hours": 0,
            "average_cycle_time_days": 0,
            "estimation_accuracy": 0
        }

    def _analyze_sentiment_trends(self, communications: List[Dict]) -> Dict:
        """Analyze sentiment trends from communications."""
        try:
            if not communications:
                return {"average_sentiment": 0.5, "trend": "stable", "total_messages": 0}
            
            # Calculate daily sentiment averages
            daily_sentiments = {}
            for comm in communications:
                date = datetime.fromisoformat(comm["timestamp"]).date()
                if date not in daily_sentiments:
                    daily_sentiments[date] = []
                
                sentiment_score = comm.get("sentiment_score", 0.5)
                daily_sentiments[date].append(sentiment_score)
            
            # Calculate daily averages
            daily_averages = {}
            for date, scores in daily_sentiments.items():
                daily_averages[date] = sum(scores) / len(scores)
            
            # Calculate overall average
            all_scores = [comm.get("sentiment_score", 0.5) for comm in communications]
            average_sentiment = sum(all_scores) / len(all_scores)
            
            # Determine trend
            if len(daily_averages) >= 3:
                dates = sorted(daily_averages.keys())
                first_third = dates[:len(dates)//3]
                last_third = dates[-len(dates)//3:]
                
                first_avg = sum(daily_averages[d] for d in first_third) / len(first_third)
                last_avg = sum(daily_averages[d] for d in last_third) / len(last_third)
                
                if last_avg > first_avg + 0.1:
                    trend = "improving"
                elif last_avg < first_avg - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"
            
            # Count blockers
            blocker_count = sum(1 for comm in communications if comm.get("has_blockers", False))
            
            return {
                "average_sentiment": average_sentiment,
                "trend": trend,
                "total_messages": len(communications),
                "blocker_count": blocker_count,
                "daily_averages": {str(k): v for k, v in daily_averages.items()}
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment trends: {e}")
            return {"average_sentiment": 0.5, "trend": "stable", "total_messages": 0}

    async def _analyze_skill_development(self, team_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """Analyze skill development during the retrospective period."""
        try:
            # In a real implementation, this would track skill changes over time
            # For now, we'll provide a basic analysis structure
            
            skill_insights = {
                "skills_improved": [],
                "skills_declining": [],
                "new_skills_acquired": [],
                "skill_gaps_identified": [],
                "training_recommendations": []
            }
            
            return skill_insights
            
        except Exception as e:
            logger.error(f"Error analyzing skill development: {e}")
            return {}

    async def _generate_ai_analysis(self, retrospective_data: Dict) -> Dict:
        """Generate AI-powered analysis of retrospective data."""
        try:
            # Prepare data for AI analysis
            analysis_prompt = self._create_analysis_prompt(retrospective_data)
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Agile coach and team analyst. Analyze the provided retrospective data and generate insights for a software development team. Focus on:
                        1. Key achievements and wins
                        2. Main challenges and obstacles
                        3. Performance trends and patterns
                        4. Skill development insights
                        5. Actionable recommendations for improvement
                        
                        Provide your analysis in JSON format with the following structure:
                        {
                            "summary": "Brief overview of the period",
                            "achievements": ["list of key achievements"],
                            "challenges": ["list of main challenges"],
                            "skill_insights": {
                                "improvements": ["skills that improved"],
                                "gaps": ["identified skill gaps"],
                                "recommendations": ["skill development recommendations"]
                            },
                            "action_items": ["specific actionable items for next period"],
                            "recommendations": ["strategic recommendations for team improvement"]
                        }"""
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            ai_analysis = json.loads(response.choices[0].message.content)
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            # Return fallback analysis
            return {
                "summary": "Retrospective analysis completed",
                "achievements": ["Tasks completed successfully"],
                "challenges": ["Areas for improvement identified"],
                "skill_insights": {
                    "improvements": [],
                    "gaps": [],
                    "recommendations": []
                },
                "action_items": ["Continue monitoring team progress"],
                "recommendations": ["Focus on continuous improvement"]
            }

    def _create_analysis_prompt(self, retrospective_data: Dict) -> str:
        """Create analysis prompt for AI processing."""
        try:
            performance = retrospective_data.get("performance_metrics", {})
            sentiment = retrospective_data.get("sentiment_analysis", {})
            
            prompt = f"""
            Analyze the following retrospective data for a software development team:

            Performance Metrics:
            - Total tasks: {performance.get('total_tasks', 0)}
            - Completed tasks: {performance.get('completed_tasks', 0)}
            - Completion rate: {performance.get('completion_rate', 0):.1f}%
            - Velocity (story points): {performance.get('velocity', 0)}
            - Average cycle time: {performance.get('average_cycle_time_days', 0):.1f} days
            - Estimation accuracy: {performance.get('estimation_accuracy', 0):.1f}%

            Team Sentiment:
            - Average sentiment: {sentiment.get('average_sentiment', 0.5):.2f}
            - Sentiment trend: {sentiment.get('trend', 'stable')}
            - Total messages: {sentiment.get('total_messages', 0)}
            - Blocker count: {sentiment.get('blocker_count', 0)}

            Period: {retrospective_data.get('period_start', '')} to {retrospective_data.get('period_end', '')}

            Please provide a comprehensive analysis with specific insights and actionable recommendations.
            """
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error creating analysis prompt: {e}")
            return "Please analyze the team's performance and provide recommendations."

    def _empty_retrospective(self, project_id: int, team_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """Return empty retrospective structure."""
        return {
            "project_id": project_id,
            "team_id": team_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "summary": "Unable to generate retrospective analysis",
            "achievements": [],
            "challenges": [],
            "performance_metrics": self._empty_performance_metrics(),
            "skill_insights": {},
            "sentiment_trends": {"average_sentiment": 0.5, "trend": "stable", "total_messages": 0},
            "action_items": [],
            "recommendations": [],
            "generated_at": datetime.now().isoformat()
        }

    async def export_retrospective(self, retrospective_data: Dict, format: str = "json") -> str:
        """Export retrospective in specified format."""
        try:
            if format.lower() == "json":
                return json.dumps(retrospective_data, indent=2)
            elif format.lower() == "markdown":
                return self._export_to_markdown(retrospective_data)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting retrospective: {e}")
            return ""

    def _export_to_markdown(self, retrospective_data: Dict) -> str:
        """Export retrospective to markdown format."""
        try:
            md_content = f"""# Sprint Retrospective

## Period
**From:** {retrospective_data.get('period_start', '')}  
**To:** {retrospective_data.get('period_end', '')}

## Summary
{retrospective_data.get('summary', '')}

## Achievements
"""
            
            for achievement in retrospective_data.get('achievements', []):
                md_content += f"- {achievement}\n"
            
            md_content += "\n## Challenges\n"
            for challenge in retrospective_data.get('challenges', []):
                md_content += f"- {challenge}\n"
            
            md_content += "\n## Performance Metrics\n"
            metrics = retrospective_data.get('performance_metrics', {})
            md_content += f"- **Completion Rate:** {metrics.get('completion_rate', 0):.1f}%\n"
            md_content += f"- **Velocity:** {metrics.get('velocity', 0)} story points\n"
            md_content += f"- **Average Cycle Time:** {metrics.get('average_cycle_time_days', 0):.1f} days\n"
            
            md_content += "\n## Action Items\n"
            for item in retrospective_data.get('action_items', []):
                md_content += f"- [ ] {item}\n"
            
            md_content += "\n## Recommendations\n"
            for rec in retrospective_data.get('recommendations', []):
                md_content += f"- {rec}\n"
            
            return md_content
            
        except Exception as e:
            logger.error(f"Error exporting to markdown: {e}")
            return "Error generating markdown export"

retrospective_service = RetrospectiveService()
