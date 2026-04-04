"""
Example protected API endpoints demonstrating authentication and authorization.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    require_role,
    require_any_role,
)
from auth.schemas import User, AuthResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions"},
    }
)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current authenticated user information.
    
    Requires: Valid Bearer token
    
    Returns:
        Current user object with all details.
    """
    logger.info(f"✅ User {current_user.email} requested their info")
    return current_user


@router.get("/health", response_model=AuthResponse)
async def auth_health_check(
    current_user: User = Depends(get_current_user_optional),
) -> AuthResponse:
    """
    Health check endpoint - works with or without authentication.
    
    Returns:
        Authentication status and optional user info.
    """
    
    if current_user:
        return AuthResponse(
            is_authenticated=True,
            user=current_user,
            message=f"Authenticated as {current_user.email}",
            token_valid=True,
        )
    
    return AuthResponse(
        is_authenticated=False,
        user=None,
        message="Not authenticated",
        token_valid=False,
    )


@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Example protected endpoint - requires valid authentication.
    
    Requires: Valid Bearer token
    
    Returns:
        Message confirming authentication.
    """
    
    logger.info(f"Protected route accessed by {current_user.email}")
    
    return {
        "message": "This is a protected route",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get("/admin-only")
async def admin_only_endpoint(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role("admin")),
) -> dict:
    """
    Admin-only endpoint.
    
    Requires: 
        - Valid Bearer token
        - User must have 'admin' role
    
    Returns:
        Admin-specific information.
    """
    
    logger.info(f"Admin endpoint accessed by {current_user.email}")
    
    return {
        "message": "Admin access granted",
        "admin": current_user.email,
        "role": current_user.role,
    }


@router.post("/analyst-report")
async def analyst_report(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_any_role("analyst", "admin", "manager")),
) -> dict:
    """
    Endpoint for analysts, managers, and admins.
    
    Requires:
        - Valid Bearer token
        - User must have one of: analyst, admin, manager
    
    Returns:
        Analyst report data.
    """
    
    logger.info(f"Report created by {current_user.email} (role: {current_user.role})")
    
    return {
        "report_id": "RPT-001",
        "created_by": current_user.email,
        "created_at": current_user.created_at.isoformat(),
        "role_used": current_user.role,
    }


@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_any_role("admin", "manager")),
) -> dict:
    """
    List all users (admin/manager only).
    
    Requires:
        - Valid Bearer token
        - User must be admin or manager
    
    Returns:
        List of users in the system.
    """
    
    # In a real application, this would query the database
    logger.info(f"User listing requested by {current_user.email}")
    
    return {
        "message": "User listing endpoint",
        "requested_by": current_user.email,
        "note": "Implement database query in production",
    }


@router.post("/login-audit")
async def audit_login(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Audit logging endpoint - records user login.
    
    Requires: Valid Bearer token
    
    Returns:
        Audit log entry confirmation.
    """
    
    logger.info(f"Login audit for {current_user.email}")
    
    return {
        "event": "user_login",
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "timestamp": current_user.created_at.isoformat(),
        "status": "logged",
    }
