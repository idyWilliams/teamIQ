from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import timedelta
import logging

from auth import authenticate_user, create_access_token, get_current_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from models.database import get_user_by_username, get_user_by_email, create_user, update_user

logger = logging.getLogger(__name__)

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    role: str = "intern"

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/login")
async def login(request: LoginRequest):
    """Authenticate user and return access token."""
    try:
        user = await authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"]}, expires_delta=access_token_expires
        )
        
        # Update last login
        await update_user(user["id"], {"last_login": "now()"})
        
        # Remove sensitive data from response
        user_response = {k: v for k, v in user.items() if k not in ["password_hash"]}
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/register")
async def register(request: RegisterRequest):
    """Register a new user."""
    try:
        # Check if username already exists
        existing_user = await get_user_by_username(request.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await get_user_by_email(request.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate role
        valid_roles = ["intern", "team_lead", "hr", "recruiter", "admin"]
        if request.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        # Create user
        user_data = {
            "username": request.username,
            "email": request.email,
            "password_hash": get_password_hash(request.password),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "role": request.role,
            "is_active": True
        }
        
        user = await create_user(user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Remove sensitive data from response
        user_response = {k: v for k, v in user.items() if k not in ["password_hash"]}
        
        return {
            "user": user_response,
            "success": True,
            "message": "User registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Initiate password reset process."""
    try:
        user = await get_user_by_email(request.email)
        if not user:
            # Don't reveal if email exists or not
            return {
                "success": True,
                "message": "If the email exists, a password reset link has been sent"
            }
        
        # In a real implementation, this would:
        # 1. Generate a secure reset token
        # 2. Store it in the database with expiration
        # 3. Send email with reset link
        
        # For now, we'll just return success
        return {
            "success": True,
            "message": "Password reset link has been sent to your email"
        }
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset user password with token."""
    try:
        # In a real implementation, this would:
        # 1. Validate the reset token
        # 2. Check if token is not expired
        # 3. Update user password
        # 4. Invalidate the token
        
        # For now, we'll return an error since we don't have token validation
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change user password."""
    try:
        from auth import verify_password
        
        # Verify current password
        if not verify_password(request.current_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_password_hash = get_password_hash(request.new_password)
        updated_user = await update_user(current_user["id"], {"password_hash": new_password_hash})
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    try:
        # Remove sensitive data
        user_response = {k: v for k, v in current_user.items() if k not in ["password_hash"]}
        
        return {
            "user": user_response,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (for completeness, JWT tokens are stateless)."""
    try:
        # In a real implementation with refresh tokens, this would:
        # 1. Invalidate refresh tokens
        # 2. Add JWT token to blacklist
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/validate-token")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Validate JWT token."""
    try:
        return {
            "valid": True,
            "user_id": current_user["id"],
            "username": current_user["username"],
            "role": current_user["role"],
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
