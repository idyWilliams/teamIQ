import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.core.config import settings


class SlackService:
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        self.channel_id = settings.SLACK_CHANNEL_ID
    
    def check_connection(self) -> bool:
        """Check if Slack API is accessible."""
        try:
            if not settings.SLACK_BOT_TOKEN:
                return False
            
            response = self.client.auth_test()
            return response["ok"]
        except SlackApiError:
            return False
    
    def get_channels(self) -> List[Dict]:
        """Get all channels."""
        try:
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                exclude_archived=True
            )
            
            channels = []
            for channel in response["channels"]:
                channels.append({
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_private": channel["is_private"],
                    "num_members": channel.get("num_members", 0),
                    "topic": channel.get("topic", {}).get("value", ""),
                    "purpose": channel.get("purpose", {}).get("value", ""),
                    "created": channel["created"]
                })
            
            return channels
        except SlackApiError as e:
            print(f"Error fetching Slack channels: {e}")
            return []
    
    def get_channel_messages(self, channel_id: str, limit: int = 100, days: int = 7) -> List[Dict]:
        """Get messages from a channel."""
        try:
            # Calculate timestamp for N days ago
            oldest_timestamp = (datetime.utcnow() - timedelta(days=days)).timestamp()
            
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit,
                oldest=str(oldest_timestamp)
            )
            
            messages = []
            for message in response["messages"]:
                # Skip bot messages and system messages
                if message.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                    continue
                
                messages.append({
                    "ts": message["ts"],
                    "user": message.get("user", ""),
                    "text": message.get("text", ""),
                    "timestamp": datetime.fromtimestamp(float(message["ts"])).isoformat(),
                    "thread_ts": message.get("thread_ts"),
                    "reply_count": message.get("reply_count", 0),
                    "reactions": message.get("reactions", [])
                })
            
            return messages
        except SlackApiError as e:
            print(f"Error fetching Slack messages: {e}")
            return []
    
    def get_user_info(self, user_id: str) -> Dict:
        """Get user information."""
        try:
            response = self.client.users_info(user=user_id)
            user = response["user"]
            
            return {
                "id": user["id"],
                "name": user["name"],
                "real_name": user.get("real_name", ""),
                "display_name": user.get("profile", {}).get("display_name", ""),
                "email": user.get("profile", {}).get("email", ""),
                "title": user.get("profile", {}).get("title", ""),
                "is_admin": user.get("is_admin", False),
                "is_bot": user.get("is_bot", False),
                "timezone": user.get("tz", ""),
                "avatar": user.get("profile", {}).get("image_192", "")
            }
        except SlackApiError as e:
            print(f"Error fetching Slack user info: {e}")
            return {}
    
    def get_team_messages(self, team_id: int, days: int = 7) -> List[Dict]:
        """Get messages from team members across all channels."""
        try:
            # This would typically require mapping team members to Slack users
            # For now, return messages from the default channel
            return self.get_channel_messages(self.channel_id, limit=1000, days=days)
        except Exception as e:
            print(f"Error fetching team messages: {e}")
            return []
    
    def send_message(self, channel: str, text: str, blocks: List[Dict] = None) -> Dict:
        """Send a message to a channel."""
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            
            return {
                "ok": response["ok"],
                "ts": response["ts"],
                "channel": response["channel"],
                "message": response["message"]
            }
        except SlackApiError as e:
            print(f"Error sending Slack message: {e}")
            return {"ok": False, "error": str(e)}
    
    def send_direct_message(self, user_id: str, text: str) -> Dict:
        """Send a direct message to a user."""
        try:
            # Open DM channel
            dm_response = self.client.conversations_open(users=user_id)
            dm_channel = dm_response["channel"]["id"]
            
            # Send message
            response = self.client.chat_postMessage(
                channel=dm_channel,
                text=text
            )
            
            return {
                "ok": response["ok"],
                "ts": response["ts"],
                "channel": response["channel"]
            }
        except SlackApiError as e:
            print(f"Error sending direct message: {e}")
            return {"ok": False, "error": str(e)}
    
    def get_user_activity(self, user_id: str, days: int = 7) -> Dict:
        """Get activity metrics for a user."""
        try:
            # Get all channels the user is in
            channels = self.get_channels()
            
            total_messages = 0
            total_reactions = 0
            channels_active = 0
            
            for channel in channels:
                messages = self.get_channel_messages(channel["id"], limit=1000, days=days)
                user_messages = [msg for msg in messages if msg["user"] == user_id]
                
                if user_messages:
                    channels_active += 1
                    total_messages += len(user_messages)
                    
                    # Count reactions given by user
                    for message in messages:
                        for reaction in message.get("reactions", []):
                            if user_id in reaction.get("users", []):
                                total_reactions += 1
            
            return {
                "user_id": user_id,
                "total_messages": total_messages,
                "total_reactions": total_reactions,
                "channels_active": channels_active,
                "messages_per_day": round(total_messages / days, 2) if days > 0 else 0,
                "analysis_period": f"{days} days"
            }
        except Exception as e:
            print(f"Error fetching user activity: {e}")
            return {}
    
    def search_messages(self, query: str, count: int = 100) -> List[Dict]:
        """Search for messages."""
        try:
            response = self.client.search_messages(
                query=query,
                count=count
            )
            
            messages = []
            for match in response["messages"]["matches"]:
                messages.append({
                    "text": match["text"],
                    "user": match.get("user", ""),
                    "username": match.get("username", ""),
                    "timestamp": match["ts"],
                    "channel": match["channel"]["name"],
                    "permalink": match["permalink"]
                })
            
            return messages
        except SlackApiError as e:
            print(f"Error searching messages: {e}")
            return []
    
    def get_channel_analytics(self, channel_id: str, days: int = 30) -> Dict:
        """Get analytics for a channel."""
        try:
            messages = self.get_channel_messages(channel_id, limit=10000, days=days)
            
            if not messages:
                return {}
            
            # User activity
            user_activity = {}
            for message in messages:
                user_id = message["user"]
                if user_id:
                    user_activity[user_id] = user_activity.get(user_id, 0) + 1
            
            # Daily activity
            daily_activity = {}
            for message in messages:
                date = message["timestamp"][:10]  # Extract date
                daily_activity[date] = daily_activity.get(date, 0) + 1
            
            # Most active users
            most_active_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "channel_id": channel_id,
                "total_messages": len(messages),
                "unique_users": len(user_activity),
                "messages_per_day": round(len(messages) / days, 2) if days > 0 else 0,
                "daily_activity": daily_activity,
                "most_active_users": [
                    {"user_id": user_id, "message_count": count}
                    for user_id, count in most_active_users
                ],
                "analysis_period": f"{days} days"
            }
        except Exception as e:
            print(f"Error getting channel analytics: {e}")
            return {}
    
    def monitor_keywords(self, keywords: List[str], days: int = 1) -> List[Dict]:
        """Monitor for specific keywords in messages."""
        try:
            alerts = []
            
            for keyword in keywords:
                messages = self.search_messages(keyword, count=50)
                
                # Filter by time period
                cutoff_time = datetime.utcnow() - timedelta(days=days)
                recent_messages = [
                    msg for msg in messages
                    if datetime.fromtimestamp(float(msg["timestamp"])) > cutoff_time
                ]
                
                if recent_messages:
                    alerts.append({
                        "keyword": keyword,
                        "message_count": len(recent_messages),
                        "messages": recent_messages[:5]  # Top 5 recent messages
                    })
            
            return alerts
        except Exception as e:
            print(f"Error monitoring keywords: {e}")
            return []
    
    def get_team_sentiment_data(self, team_id: int, days: int = 7) -> List[Dict]:
        """Get sentiment data for a team."""
        try:
            # Get messages from team channels
            messages = self.get_team_messages(team_id, days)
            
            # Group messages by user
            user_messages = {}
            for message in messages:
                user_id = message["user"]
                if user_id:
                    if user_id not in user_messages:
                        user_messages[user_id] = []
                    user_messages[user_id].append(message)
            
            # Return structured data for sentiment analysis
            sentiment_data = []
            for user_id, msgs in user_messages.items():
                user_info = self.get_user_info(user_id)
                sentiment_data.append({
                    "user_id": user_id,
                    "user_info": user_info,
                    "messages": msgs,
                    "message_count": len(msgs)
                })
            
            return sentiment_data
        except Exception as e:
            print(f"Error getting team sentiment data: {e}")
            return []
    
    def create_reminder(self, channel: str, text: str, time: str) -> Dict:
        """Create a reminder."""
        try:
            response = self.client.chat_scheduleMessage(
                channel=channel,
                text=text,
                post_at=time
            )
            
            return {
                "ok": response["ok"],
                "scheduled_message_id": response["scheduled_message_id"],
                "channel": response["channel"],
                "post_at": response["post_at"]
            }
        except SlackApiError as e:
            print(f"Error creating reminder: {e}")
            return {"ok": False, "error": str(e)}
