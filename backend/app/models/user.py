from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(enum.Enum):
    INTERN = "intern"
    ENGINEER = "engineer"
    TEAM_LEAD = "team_lead"
    HR = "hr"
    RECRUITER = "recruiter"
    ADMIN = "admin"
    BOOTCAMP_ADMIN = "bootcamp_admin"
    EXECUTIVE = "executive"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.INTERN)
    is_active = Column(Boolean, default=True)
    profile_picture = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_username = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    in_app_notifications = Column(Boolean, default=True)
    
    # Relationships
    team_memberships = relationship("TeamMember", back_populates="user")
    project_memberships = relationship("ProjectMember", back_populates="user")
    skills = relationship("UserSkill", back_populates="user")
    assigned_tasks = relationship("TaskAssignment", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
