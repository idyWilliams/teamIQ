import os
import openai
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.core.config import settings
import json
import re


class AIService:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Analyze the sentiment of the text and provide a detailed analysis. Respond with JSON in this format: {'dominant_sentiment': 'positive|neutral|negative', 'confidence': 0.0-1.0, 'sentiment_scores': {'positive': 0.0-1.0, 'neutral': 0.0-1.0, 'negative': 0.0-1.0}, 'key_phrases': ['phrase1', 'phrase2'], 'emotional_indicators': ['indicator1', 'indicator2']}"
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the sentiment of this text: {text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {
                "dominant_sentiment": "neutral",
                "confidence": 0.0,
                "sentiment_scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                "key_phrases": [],
                "emotional_indicators": []
            }
    
    def extract_skills_from_task(self, task_description: str) -> List[str]:
        """Extract required skills from task description."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical skills extraction expert. Extract the required technical skills from the task description. Focus on programming languages, frameworks, tools, and technologies. Respond with JSON in this format: {'skills': ['skill1', 'skill2', 'skill3'], 'skill_categories': {'programming_languages': ['lang1'], 'frameworks': ['framework1'], 'tools': ['tool1']}, 'difficulty_level': 'beginner|intermediate|advanced'}"
                    },
                    {
                        "role": "user",
                        "content": f"Extract required skills from this task: {task_description}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("skills", [])
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return []
    
    def generate_retrospective(self, project_data: Dict, team_data: Dict, timeframe: str) -> Dict:
        """Generate an automated retrospective report."""
        try:
            # Prepare data for analysis
            context = f"""
            Project: {project_data.get('name', 'Unknown')}
            Timeframe: {timeframe}
            Team Size: {len(team_data.get('members', []))}
            Completed Tasks: {project_data.get('completed_tasks', 0)}
            Total Tasks: {project_data.get('total_tasks', 0)}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Agile coach generating sprint retrospectives. Analyze the project data and create a comprehensive retrospective report. Respond with JSON in this format: {'summary': 'brief summary', 'achievements': ['achievement1', 'achievement2'], 'challenges': ['challenge1', 'challenge2'], 'improvements': ['improvement1', 'improvement2'], 'action_items': ['action1', 'action2'], 'team_performance': {'velocity': 0.0, 'quality': 'high|medium|low', 'collaboration': 'excellent|good|fair|poor'}, 'recommendations': ['rec1', 'rec2']}"
                    },
                    {
                        "role": "user",
                        "content": f"Generate a retrospective report for this project data: {context}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["generated_at"] = datetime.utcnow().isoformat()
            result["timeframe"] = timeframe
            return result
        except Exception as e:
            print(f"Error generating retrospective: {e}")
            return {
                "summary": "Error generating retrospective",
                "achievements": [],
                "challenges": [],
                "improvements": [],
                "action_items": [],
                "team_performance": {"velocity": 0.0, "quality": "unknown", "collaboration": "unknown"},
                "recommendations": []
            }
    
    def analyze_code_quality(self, code_metrics: Dict) -> Dict:
        """Analyze code quality metrics and provide insights."""
        try:
            metrics_text = json.dumps(code_metrics, indent=2)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code quality expert. Analyze the code metrics and provide insights. Respond with JSON in this format: {'overall_score': 0.0-10.0, 'quality_level': 'excellent|good|fair|poor', 'strengths': ['strength1', 'strength2'], 'weaknesses': ['weakness1', 'weakness2'], 'recommendations': ['rec1', 'rec2'], 'technical_debt': 'low|medium|high', 'maintainability': 'high|medium|low'}"
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these code quality metrics: {metrics_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error analyzing code quality: {e}")
            return {
                "overall_score": 5.0,
                "quality_level": "unknown",
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "technical_debt": "unknown",
                "maintainability": "unknown"
            }
    
    def analyze_team_sentiment(self, messages: List[Dict]) -> Dict:
        """Analyze team sentiment from messages."""
        try:
            # Prepare message data
            message_text = ""
            for msg in messages[:50]:  # Limit to recent messages
                message_text += f"{msg.get('text', '')}\n"
            
            if not message_text.strip():
                return {
                    "overall_sentiment": "neutral",
                    "confidence": 0.0,
                    "sentiment_trend": "stable",
                    "key_concerns": [],
                    "positive_indicators": []
                }
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a team sentiment analysis expert. Analyze the team communication and identify overall sentiment, concerns, and positive indicators. Respond with JSON in this format: {'overall_sentiment': 'positive|neutral|negative', 'confidence': 0.0-1.0, 'sentiment_trend': 'improving|stable|declining', 'key_concerns': ['concern1', 'concern2'], 'positive_indicators': ['indicator1', 'indicator2'], 'team_morale': 'high|medium|low', 'stress_level': 'low|medium|high'}"
                    },
                    {
                        "role": "user",
                        "content": f"Analyze team sentiment from these messages: {message_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error analyzing team sentiment: {e}")
            return {
                "overall_sentiment": "neutral",
                "confidence": 0.0,
                "sentiment_trend": "stable",
                "key_concerns": [],
                "positive_indicators": [],
                "team_morale": "medium",
                "stress_level": "medium"
            }
    
    def generate_task_recommendations(self, user_profile: Dict, available_tasks: List[Dict]) -> List[Dict]:
        """Generate task recommendations for a user."""
        try:
            profile_text = json.dumps(user_profile, indent=2)
            tasks_text = json.dumps(available_tasks, indent=2)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a task assignment expert. Analyze the user profile and available tasks to recommend the best matches. Consider skill level, growth opportunities, and workload. Respond with JSON in this format: {'recommendations': [{'task_id': 'id', 'match_score': 0.0-1.0, 'reasoning': 'explanation', 'growth_opportunity': 'high|medium|low', 'estimated_difficulty': 'easy|medium|hard'}]}"
                    },
                    {
                        "role": "user",
                        "content": f"User profile: {profile_text}\n\nAvailable tasks: {tasks_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("recommendations", [])
        except Exception as e:
            print(f"Error generating task recommendations: {e}")
            return []
    
    def analyze_skill_gaps(self, team_skills: Dict, project_requirements: List[str]) -> Dict:
        """Analyze skill gaps in a team."""
        try:
            team_skills_text = json.dumps(team_skills, indent=2)
            requirements_text = json.dumps(project_requirements, indent=2)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skill gap analysis expert. Compare team skills with project requirements and identify gaps. Respond with JSON in this format: {'skill_gaps': [{'skill': 'skill_name', 'gap_severity': 'critical|high|medium|low', 'current_level': 'beginner|intermediate|advanced', 'required_level': 'beginner|intermediate|advanced', 'recommendations': ['rec1', 'rec2']}], 'overall_readiness': 'high|medium|low', 'training_priorities': ['priority1', 'priority2']}"
                    },
                    {
                        "role": "user",
                        "content": f"Team skills: {team_skills_text}\n\nProject requirements: {requirements_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error analyzing skill gaps: {e}")
            return {
                "skill_gaps": [],
                "overall_readiness": "medium",
                "training_priorities": []
            }
    
    def generate_career_recommendations(self, user_profile: Dict, industry_trends: Dict) -> Dict:
        """Generate career path recommendations."""
        try:
            profile_text = json.dumps(user_profile, indent=2)
            trends_text = json.dumps(industry_trends, indent=2)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a career development expert. Analyze the user profile and industry trends to provide career recommendations. Respond with JSON in this format: {'career_paths': [{'path': 'path_name', 'fit_score': 0.0-1.0, 'required_skills': ['skill1', 'skill2'], 'timeline': 'short|medium|long', 'growth_potential': 'high|medium|low'}], 'immediate_actions': ['action1', 'action2'], 'skill_development_plan': [{'skill': 'skill_name', 'priority': 'high|medium|low', 'resources': ['resource1', 'resource2']}]}"
                    },
                    {
                        "role": "user",
                        "content": f"User profile: {profile_text}\n\nIndustry trends: {trends_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error generating career recommendations: {e}")
            return {
                "career_paths": [],
                "immediate_actions": [],
                "skill_development_plan": []
            }
    
    def detect_anomalies(self, metrics: Dict) -> Dict:
        """Detect anomalies in team or project metrics."""
        try:
            metrics_text = json.dumps(metrics, indent=2)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an anomaly detection expert. Analyze the metrics and identify unusual patterns or potential issues. Respond with JSON in this format: {'anomalies': [{'metric': 'metric_name', 'anomaly_type': 'spike|drop|pattern', 'severity': 'high|medium|low', 'description': 'explanation', 'potential_causes': ['cause1', 'cause2'], 'recommended_actions': ['action1', 'action2']}], 'overall_health': 'healthy|warning|critical'}"
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these metrics for anomalies: {metrics_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return {
                "anomalies": [],
                "overall_health": "healthy"
            }
    
    def generate_learning_recommendations(self, user_skills: Dict, learning_goals: List[str]) -> Dict:
        """Generate personalized learning recommendations."""
        try:
            skills_text = json.dumps(user_skills, indent=2)
            goals_text = json.dumps(learning_goals, indent=2)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a learning and development expert. Create personalized learning recommendations based on current skills and goals. Respond with JSON in this format: {'learning_path': [{'skill': 'skill_name', 'current_level': 'beginner|intermediate|advanced', 'target_level': 'beginner|intermediate|advanced', 'learning_resources': [{'type': 'course|tutorial|book|project', 'title': 'title', 'difficulty': 'easy|medium|hard', 'estimated_time': 'time'}], 'milestones': ['milestone1', 'milestone2']}], 'timeline': 'short|medium|long', 'priority_order': ['skill1', 'skill2']}"
                    },
                    {
                        "role": "user",
                        "content": f"Current skills: {skills_text}\n\nLearning goals: {goals_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error generating learning recommendations: {e}")
            return {
                "learning_path": [],
                "timeline": "medium",
                "priority_order": []
            }
