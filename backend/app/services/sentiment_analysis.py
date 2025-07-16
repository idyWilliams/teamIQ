import os
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import json
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    def __init__(self):
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your-openai-key-here")
        )
        
        self.blocker_keywords = [
            "blocked", "stuck", "can't", "unable", "issue", "problem", 
            "error", "failed", "broken", "help", "struggling", "difficult",
            "impediment", "obstacle", "roadblock", "halt", "stop", "barrier"
        ]
        
        self.risk_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8
        }

    async def analyze_message_sentiment(self, message: str) -> Dict:
        """Analyze sentiment of a single message using OpenAI."""
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a sentiment analysis expert specializing in workplace communication. 
                        Analyze the sentiment of the message and provide a rating from 0 to 1 (where 0 is very negative, 
                        0.5 is neutral, and 1 is very positive) and a confidence score between 0 and 1.
                        Also identify if this message indicates any blockers or impediments to work.
                        Respond with JSON in this format: {
                            "sentiment_score": number,
                            "confidence": number,
                            "has_blockers": boolean,
                            "blocker_keywords": [array of strings],
                            "emotional_tone": string,
                            "urgency_level": string
                        }"""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "sentiment_score": max(0, min(1, result.get("sentiment_score", 0.5))),
                "confidence": max(0, min(1, result.get("confidence", 0.5))),
                "has_blockers": result.get("has_blockers", False),
                "blocker_keywords": result.get("blocker_keywords", []),
                "emotional_tone": result.get("emotional_tone", "neutral"),
                "urgency_level": result.get("urgency_level", "low"),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment with OpenAI: {e}")
            # Fallback to simple keyword-based analysis
            return self._simple_sentiment_analysis(message)

    def _simple_sentiment_analysis(self, message: str) -> Dict:
        """Simple fallback sentiment analysis using keywords."""
        try:
            message_lower = message.lower()
            
            positive_keywords = [
                "great", "awesome", "excellent", "good", "happy", "thanks", 
                "love", "amazing", "perfect", "solved", "success", "complete",
                "accomplished", "pleased", "satisfied", "excited"
            ]
            
            negative_keywords = [
                "frustrated", "angry", "disappointed", "sad", "worried", 
                "concerned", "stressed", "overwhelmed", "tired", "annoyed",
                "upset", "confused", "lost", "behind", "delayed"
            ]
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in message_lower)
            negative_count = sum(1 for keyword in negative_keywords if keyword in message_lower)
            blocker_count = sum(1 for keyword in self.blocker_keywords if keyword in message_lower)
            
            # Simple scoring
            sentiment_score = 0.5  # Neutral base
            if positive_count > negative_count:
                sentiment_score += min(0.4, positive_count * 0.1)
            elif negative_count > positive_count:
                sentiment_score -= min(0.4, negative_count * 0.1)
            
            # Adjust for blockers
            if blocker_count > 0:
                sentiment_score -= min(0.2, blocker_count * 0.05)
            
            sentiment_score = max(0, min(1, sentiment_score))
            
            return {
                "sentiment_score": sentiment_score,
                "confidence": min(1.0, (positive_count + negative_count + blocker_count) / 10),
                "has_blockers": blocker_count > 0,
                "blocker_keywords": [kw for kw in self.blocker_keywords if kw in message_lower],
                "emotional_tone": "positive" if sentiment_score > 0.6 else "negative" if sentiment_score < 0.4 else "neutral",
                "urgency_level": "high" if blocker_count > 2 else "medium" if blocker_count > 0 else "low",
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in simple sentiment analysis: {e}")
            return {
                "sentiment_score": 0.5,
                "confidence": 0.0,
                "has_blockers": False,
                "blocker_keywords": [],
                "emotional_tone": "neutral",
                "urgency_level": "low",
                "analysis_timestamp": datetime.now().isoformat()
            }

    async def analyze_user_sentiment_trend(self, user_communications: List[Dict], days: int = 30) -> Dict:
        """Analyze sentiment trend for a user over time."""
        try:
            if not user_communications:
                return self._empty_trend_analysis()
            
            # Filter communications by date
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_communications = [
                comm for comm in user_communications
                if datetime.fromisoformat(comm.get("timestamp", "")) >= cutoff_date
            ]
            
            if not recent_communications:
                return self._empty_trend_analysis()
            
            # Analyze each communication
            sentiment_scores = []
            blocker_count = 0
            total_confidence = 0
            
            for comm in recent_communications:
                analysis = await self.analyze_message_sentiment(comm.get("content", ""))
                sentiment_scores.append({
                    "score": analysis["sentiment_score"],
                    "timestamp": comm.get("timestamp"),
                    "has_blockers": analysis["has_blockers"]
                })
                
                if analysis["has_blockers"]:
                    blocker_count += 1
                
                total_confidence += analysis["confidence"]
            
            # Calculate trend
            avg_sentiment = sum(s["score"] for s in sentiment_scores) / len(sentiment_scores)
            
            # Calculate trend direction
            if len(sentiment_scores) > 5:
                recent_scores = [s["score"] for s in sentiment_scores[-5:]]
                earlier_scores = [s["score"] for s in sentiment_scores[:-5]]
                
                recent_avg = sum(recent_scores) / len(recent_scores)
                earlier_avg = sum(earlier_scores) / len(earlier_scores)
                
                if recent_avg > earlier_avg + 0.1:
                    trend = "improving"
                elif recent_avg < earlier_avg - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"
            
            # Determine risk level
            risk_level = self._calculate_risk_level(avg_sentiment, blocker_count, len(recent_communications))
            
            return {
                "user_id": user_communications[0].get("user_id") if user_communications else None,
                "analysis_period_days": days,
                "message_count": len(recent_communications),
                "average_sentiment": avg_sentiment,
                "sentiment_trend": trend,
                "blocker_count": blocker_count,
                "blocker_rate": blocker_count / len(recent_communications),
                "risk_level": risk_level,
                "confidence": total_confidence / len(sentiment_scores),
                "sentiment_timeline": sentiment_scores,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user sentiment trend: {e}")
            return self._empty_trend_analysis()

    def _empty_trend_analysis(self) -> Dict:
        """Return empty trend analysis structure."""
        return {
            "user_id": None,
            "analysis_period_days": 30,
            "message_count": 0,
            "average_sentiment": 0.5,
            "sentiment_trend": "stable",
            "blocker_count": 0,
            "blocker_rate": 0.0,
            "risk_level": "low",
            "confidence": 0.0,
            "sentiment_timeline": [],
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _calculate_risk_level(self, avg_sentiment: float, blocker_count: int, message_count: int) -> str:
        """Calculate risk level based on sentiment and blocker data."""
        try:
            # Sentiment risk (inverted - lower sentiment = higher risk)
            sentiment_risk = 1 - avg_sentiment
            
            # Blocker risk
            blocker_rate = blocker_count / message_count if message_count > 0 else 0
            
            # Combined risk score
            risk_score = (sentiment_risk * 0.7) + (blocker_rate * 0.3)
            
            if risk_score >= self.risk_thresholds["high"]:
                return "high"
            elif risk_score >= self.risk_thresholds["medium"]:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {e}")
            return "low"

    async def analyze_team_sentiment(self, team_communications: List[Dict]) -> Dict:
        """Analyze sentiment for an entire team."""
        try:
            if not team_communications:
                return self._empty_team_analysis()
            
            # Group communications by user
            user_communications = {}
            for comm in team_communications:
                user_id = comm.get("user_id")
                if user_id not in user_communications:
                    user_communications[user_id] = []
                user_communications[user_id].append(comm)
            
            # Analyze each user
            user_analyses = {}
            team_sentiment_scores = []
            team_blocker_count = 0
            
            for user_id, communications in user_communications.items():
                user_analysis = await self.analyze_user_sentiment_trend(communications)
                user_analyses[user_id] = user_analysis
                
                team_sentiment_scores.append(user_analysis["average_sentiment"])
                team_blocker_count += user_analysis["blocker_count"]
            
            # Calculate team aggregates
            team_avg_sentiment = sum(team_sentiment_scores) / len(team_sentiment_scores) if team_sentiment_scores else 0.5
            
            # Identify at-risk members
            at_risk_members = [
                {"user_id": user_id, "risk_level": analysis["risk_level"], "sentiment": analysis["average_sentiment"]}
                for user_id, analysis in user_analyses.items()
                if analysis["risk_level"] in ["medium", "high"]
            ]
            
            # Sort by risk level
            at_risk_members.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["risk_level"]], reverse=True)
            
            return {
                "team_size": len(user_communications),
                "analysis_period_days": 30,
                "team_average_sentiment": team_avg_sentiment,
                "team_sentiment_trend": self._calculate_team_trend(user_analyses),
                "total_blockers": team_blocker_count,
                "at_risk_members": at_risk_members,
                "user_analyses": user_analyses,
                "team_health_score": self._calculate_team_health_score(team_avg_sentiment, len(at_risk_members), len(user_communications)),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing team sentiment: {e}")
            return self._empty_team_analysis()

    def _empty_team_analysis(self) -> Dict:
        """Return empty team analysis structure."""
        return {
            "team_size": 0,
            "analysis_period_days": 30,
            "team_average_sentiment": 0.5,
            "team_sentiment_trend": "stable",
            "total_blockers": 0,
            "at_risk_members": [],
            "user_analyses": {},
            "team_health_score": 0.5,
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _calculate_team_trend(self, user_analyses: Dict) -> str:
        """Calculate overall team sentiment trend."""
        try:
            trends = [analysis["sentiment_trend"] for analysis in user_analyses.values()]
            
            improving_count = trends.count("improving")
            declining_count = trends.count("declining")
            
            if improving_count > declining_count:
                return "improving"
            elif declining_count > improving_count:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error calculating team trend: {e}")
            return "stable"

    def _calculate_team_health_score(self, avg_sentiment: float, at_risk_count: int, team_size: int) -> float:
        """Calculate overall team health score."""
        try:
            # Base score from sentiment
            sentiment_score = avg_sentiment
            
            # Penalty for at-risk members
            risk_penalty = (at_risk_count / team_size) * 0.3 if team_size > 0 else 0
            
            # Combined health score
            health_score = max(0, min(1, sentiment_score - risk_penalty))
            
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating team health score: {e}")
            return 0.5

    async def generate_intervention_recommendations(self, user_analysis: Dict) -> List[Dict]:
        """Generate intervention recommendations for at-risk users."""
        try:
            recommendations = []
            
            risk_level = user_analysis.get("risk_level", "low")
            avg_sentiment = user_analysis.get("average_sentiment", 0.5)
            blocker_count = user_analysis.get("blocker_count", 0)
            
            if risk_level == "high":
                recommendations.append({
                    "priority": "urgent",
                    "action": "schedule_1on1",
                    "title": "Schedule immediate 1:1 meeting",
                    "description": "User shows signs of high stress or significant blockers. Schedule a meeting within 24 hours.",
                    "suggested_duration": "30-60 minutes"
                })
                
                if blocker_count > 5:
                    recommendations.append({
                        "priority": "high",
                        "action": "technical_support",
                        "title": "Provide technical support",
                        "description": "User is experiencing multiple technical blockers. Assign a senior team member to provide assistance.",
                        "suggested_duration": "ongoing"
                    })
                    
            elif risk_level == "medium":
                recommendations.append({
                    "priority": "medium",
                    "action": "check_in",
                    "title": "Casual check-in",
                    "description": "User sentiment is declining. Schedule a casual check-in within the next few days.",
                    "suggested_duration": "15-30 minutes"
                })
                
                if blocker_count > 2:
                    recommendations.append({
                        "priority": "medium",
                        "action": "pair_programming",
                        "title": "Pair programming session",
                        "description": "User is experiencing blockers. Arrange pair programming with a team member.",
                        "suggested_duration": "1-2 hours"
                    })
            
            # General recommendations based on sentiment
            if avg_sentiment < 0.3:
                recommendations.append({
                    "priority": "medium",
                    "action": "workload_review",
                    "title": "Review workload",
                    "description": "User sentiment is consistently low. Review current workload and priorities.",
                    "suggested_duration": "meeting"
                })
                
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating intervention recommendations: {e}")
            return []

sentiment_service = SentimentAnalysisService()
