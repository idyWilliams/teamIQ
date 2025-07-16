from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.core.database import get_db


class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password."""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, username: str, email: str, full_name: str, password: str, role: str) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_password(self, user: User, new_password: str) -> bool:
        """Update user password."""
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True
    
    def deactivate_user(self, user: User) -> bool:
        """Deactivate user account."""
        user.is_active = False
        self.db.commit()
        return True
    
    def activate_user(self, user: User) -> bool:
        """Activate user account."""
        user.is_active = True
        self.db.commit()
        return True
