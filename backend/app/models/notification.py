from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class NotificationType(enum.Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    MENTION = "mention"
    SKILL_MILESTONE = "skill_milestone"
    SENTIMENT_ALERT = "sentiment_alert"
    RETROSPECTIVE_READY = "retrospective_ready"
    SYSTEM_ALERT = "system_alert"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional link to related entity
    related_entity_id = Column(Integer, nullable=True)
    related_entity_type = Column(String, nullable=True)  # task, project, user, etc.
    
    # Relationships
    user = relationship("User", back_populates="notifications")
