from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.team import Team, TeamMember
from app.services.ai_service import AIService
from app.services.slack_service import SlackService
import re


class SentimentService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.slack_service = SlackService()
    
    def analyze_team_sentiment(self, team_id: int, days: int = 7) -> Dict:
        """Analyze sentiment for a team over the last N days."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"error": "Team not found"}
        
        # Get team members
        team_members = self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.is_active == True
        ).all()
        
        # Get Slack messages for analysis
        messages = self.slack_service.get_team_messages(team_id, days)
        
        # Analyze sentiment for each member
        member_sentiments = {}
        overall_sentiment = {"positive": 0, "neutral": 0, "negative": 0}
        
        for member in team_members:
            user_messages = [msg for msg in messages if msg.get('user_id') == member.user_id]
            if user_messages:
                sentiment = self.analyze_user_sentiment(user_messages)
                member_sentiments[member.user_id] = {
                    "username": member.user.username,
                    "full_name": member.user.full_name,
                    "sentiment": sentiment,
                    "message_count": len(user_messages)
                }
                
                # Add to overall sentiment
                overall_sentiment[sentiment["dominant_sentiment"]] += 1
        
        # Calculate team sentiment trends
        sentiment_trend = self.calculate_sentiment_trend(team_id, days)
        
        # Identify at-risk members
        at_risk_members = self.identify_at_risk_members(member_sentiments)
        
        return {
            "team_id": team_id,
            "team_name": team.name,
            "analysis_period": f"{days} days",
            "overall_sentiment": overall_sentiment,
            "member_sentiments": member_sentiments,
            "sentiment_trend": sentiment_trend,
            "at_risk_members": at_risk_members,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def analyze_user_sentiment(self, messages: List[Dict]) -> Dict:
        """Analyze sentiment for a specific user's messages."""
        if not messages:
            return {
                "dominant_sentiment": "neutral",
                "confidence": 0.0,
                "sentiment_scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
            }
        
        # Combine all messages into one text for analysis
        combined_text = " ".join([msg.get('text', '') for msg in messages])
        
        # Use AI service to analyze sentiment
        sentiment_result = self.ai_service.analyze_sentiment(combined_text)
        
        # Detect specific patterns
        blockers = self.detect_blockers(messages)
        stress_indicators = self.detect_stress_indicators(messages)
        
        return {
            "dominant_sentiment": sentiment_result.get("dominant_sentiment", "neutral"),
            "confidence": sentiment_result.get("confidence", 0.0),
            "sentiment_scores": sentiment_result.get("sentiment_scores", {"positive": 0.0, "neutral": 1.0, "negative": 0.0}),
            "blockers_detected": blockers,
            "stress_indicators": stress_indicators,
            "message_count": len(messages)
        }
    
    def detect_blockers(self, messages: List[Dict]) -> List[Dict]:
        """Detect blocker-related messages."""
        blocker_patterns = [
            r"\bblocked?\b",
            r"\bstuck\b",
            r"\bcan't\s+proceed\b",
            r"\bwaiting\s+for\b",
            r"\bissue\s+with\b",
            r"\bproblem\s+with\b",
            r"\bhelp\s+needed\b",
            r"\bneed\s+help\b"
        ]
        
        blockers = []
        for msg in messages:
            text = msg.get('text', '').lower()
            for pattern in blocker_patterns:
                if re.search(pattern, text):
                    blockers.append({
                        "message": msg.get('text', ''),
                        "timestamp": msg.get('timestamp', ''),
                        "pattern_matched": pattern,
                        "severity": self.classify_blocker_severity(text)
                    })
                    break
        
        return blockers
    
    def detect_stress_indicators(self, messages: List[Dict]) -> List[Dict]:
        """Detect stress indicators in messages."""
        stress_patterns = [
            r"\bstressed?\b",
            r"\boverwhelmed\b",
            r"\bburned?\s+out\b",
            r"\btired\b",
            r"\bexhausted\b",
            r"\bfrustrated\b",
            r"\bcan't\s+handle\b",
            r"\btoo\s+much\b"
        ]
        
        stress_indicators = []
        for msg in messages:
            text = msg.get('text', '').lower()
            for pattern in stress_patterns:
                if re.search(pattern, text):
                    stress_indicators.append({
                        "message": msg.get('text', ''),
                        "timestamp": msg.get('timestamp', ''),
                        "pattern_matched": pattern,
                        "severity": self.classify_stress_severity(text)
                    })
                    break
        
        return stress_indicators
    
    def classify_blocker_severity(self, text: str) -> str:
        """Classify severity of blocker."""
        high_severity_words = ["urgent", "critical", "stuck", "can't proceed", "completely blocked"]
        medium_severity_words = ["issue", "problem", "help needed", "waiting for"]
        
        text_lower = text.lower()
        if any(word in text_lower for word in high_severity_words):
            return "high"
        elif any(word in text_lower for word in medium_severity_words):
            return "medium"
        else:
            return "low"
    
    def classify_stress_severity(self, text: str) -> str:
        """Classify severity of stress."""
        high_severity_words = ["overwhelmed", "burned out", "can't handle", "exhausted"]
        medium_severity_words = ["stressed", "frustrated", "tired", "too much"]
        
        text_lower = text.lower()
        if any(word in text_lower for word in high_severity_words):
            return "high"
        elif any(word in text_lower for word in medium_severity_words):
            return "medium"
        else:
            return "low"
    
    def calculate_sentiment_trend(self, team_id: int, days: int) -> List[Dict]:
        """Calculate sentiment trend over time."""
        # This would typically store historical sentiment data
        # For now, return a simple trend structure
        trend = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            # In a real implementation, this would query historical data
            trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "sentiment_score": 0.6,  # Placeholder
                "message_count": 10  # Placeholder
            })
        
        return list(reversed(trend))
    
    def identify_at_risk_members(self, member_sentiments: Dict) -> List[Dict]:
        """Identify team members at risk based on sentiment analysis."""
        at_risk = []
        
        for user_id, sentiment_data in member_sentiments.items():
            risk_score = 0
            risk_factors = []
            
            # Check dominant sentiment
            if sentiment_data["sentiment"]["dominant_sentiment"] == "negative":
                risk_score += 3
                risk_factors.append("Negative sentiment detected")
            
            # Check confidence level
            if sentiment_data["sentiment"]["confidence"] > 0.7:
                risk_score += 1
                risk_factors.append("High confidence in sentiment analysis")
            
            # Check for blockers
            if sentiment_data["sentiment"]["blockers_detected"]:
                risk_score += 2
                risk_factors.append(f"{len(sentiment_data['sentiment']['blockers_detected'])} blockers detected")
            
            # Check for stress indicators
            if sentiment_data["sentiment"]["stress_indicators"]:
                risk_score += 2
                risk_factors.append(f"{len(sentiment_data['sentiment']['stress_indicators'])} stress indicators")
            
            # Check message volume (too high or too low could indicate issues)
            if sentiment_data["message_count"] > 50:
                risk_score += 1
                risk_factors.append("High message volume")
            elif sentiment_data["message_count"] < 5:
                risk_score += 1
                risk_factors.append("Low engagement")
            
            if risk_score >= 3:  # Threshold for at-risk
                at_risk.append({
                    "user_id": user_id,
                    "username": sentiment_data["username"],
                    "full_name": sentiment_data["full_name"],
                    "risk_score": risk_score,
                    "risk_level": "high" if risk_score >= 5 else "medium",
                    "risk_factors": risk_factors,
                    "recommended_actions": self.generate_recommended_actions(risk_factors)
                })
        
        return sorted(at_risk, key=lambda x: x["risk_score"], reverse=True)
    
    def generate_recommended_actions(self, risk_factors: List[str]) -> List[str]:
        """Generate recommended actions based on risk factors."""
        actions = []
        
        if any("negative sentiment" in factor.lower() for factor in risk_factors):
            actions.append("Schedule a 1:1 meeting to discuss concerns")
        
        if any("blocker" in factor.lower() for factor in risk_factors):
            actions.append("Help resolve blockers and provide support")
        
        if any("stress" in factor.lower() for factor in risk_factors):
            actions.append("Consider workload adjustment or mental health support")
        
        if any("low engagement" in factor.lower() for factor in risk_factors):
            actions.append("Encourage participation and check for disengagement")
        
        if any("high message volume" in factor.lower() for factor in risk_factors):
            actions.append("Monitor for signs of overwork or communication patterns")
        
        return actions if actions else ["Monitor situation and schedule regular check-ins"]
    
    def get_sentiment_alerts(self, team_id: int) -> List[Dict]:
        """Get active sentiment alerts for a team."""
        # This would typically query stored alerts
        # For now, return recent analysis as alerts
        analysis = self.analyze_team_sentiment(team_id, days=1)
        
        alerts = []
        for member in analysis.get("at_risk_members", []):
            if member["risk_level"] == "high":
                alerts.append({
                    "type": "high_risk_member",
                    "user_id": member["user_id"],
                    "username": member["username"],
                    "message": f"{member['full_name']} shows high risk indicators",
                    "severity": "high",
                    "created_at": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    def generate_sentiment_report(self, team_id: int, days: int = 30) -> Dict:
        """Generate comprehensive sentiment report for a team."""
        analysis = self.analyze_team_sentiment(team_id, days)
        
        # Calculate additional metrics
        total_members = len(analysis.get("member_sentiments", {}))
        positive_members = sum(1 for sentiment in analysis.get("member_sentiments", {}).values() 
                             if sentiment["sentiment"]["dominant_sentiment"] == "positive")
        
        report = {
            "team_id": team_id,
            "report_period": f"{days} days",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_members_analyzed": total_members,
                "positive_sentiment_rate": (positive_members / total_members * 100) if total_members > 0 else 0,
                "at_risk_members_count": len(analysis.get("at_risk_members", [])),
                "total_blockers_detected": sum(len(sentiment["sentiment"]["blockers_detected"]) 
                                             for sentiment in analysis.get("member_sentiments", {}).values())
            },
            "detailed_analysis": analysis,
            "recommendations": self.generate_team_recommendations(analysis)
        }
        
        return report
    
    def generate_team_recommendations(self, analysis: Dict) -> List[str]:
        """Generate team-level recommendations based on sentiment analysis."""
        recommendations = []
        
        at_risk_count = len(analysis.get("at_risk_members", []))
        if at_risk_count > 0:
            recommendations.append(f"Address {at_risk_count} at-risk team members immediately")
        
        overall_sentiment = analysis.get("overall_sentiment", {})
        negative_rate = overall_sentiment.get("negative", 0)
        total_members = sum(overall_sentiment.values())
        
        if total_members > 0 and negative_rate / total_members > 0.3:
            recommendations.append("Consider team-wide intervention - high negative sentiment rate")
        
        # Check for common blockers
        all_blockers = []
        for sentiment in analysis.get("member_sentiments", {}).values():
            all_blockers.extend(sentiment["sentiment"]["blockers_detected"])
        
        if len(all_blockers) > 5:
            recommendations.append("Multiple blockers detected - review team processes and dependencies")
        
        return recommendations if recommendations else ["Team sentiment appears healthy - continue monitoring"]
