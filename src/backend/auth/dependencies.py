"""
FastAPI dependency injection functions for authentication.
Provides reusable dependencies for protecting endpoints.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from auth.auth_handler import auth_handler
from auth.schemas import User

logger = logging.getLogger(__name__)

# HTTP Bearer authentication scheme
security = HTTPBearer(
    scheme_name="Bearer",
    description="Azure AD Bearer token",
    auto_error=False,
)


async def get_current_user(
    credentials = Depends(security),
    user_repository=None,  # Injected by FastAPI
) -> User:
    """
    FastAPI dependency to extract and validate the current user.
    
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user}
    
    Args:
        credentials: HTTP Bearer token from Authorization header.
        user_repository: Database repository (injected by FastAPI).
    
    Returns:
        Authenticated User object.
    
    Raises:
        HTTPException: 401 Unauthorized if token is missing or invalid.
        HTTPException: 403 Forbidden if user is not active.
    """
    
    # Check if credentials provided
    if not credentials:
        logger.warning("⚠️  No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate token and provision user
    token = credentials.credentials
    success, user, error_msg = await auth_handler.authenticate_and_provision_user(
        token=token,
        user_repository=user_repository,
    )
    
    if not success:
        logger.error(f"❌ Authentication failed: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"⚠️  Inactive user attempted login: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    logger.info(f"✅ User authenticated: {user.email}")
    return user


async def get_current_user_optional(
    credentials = Depends(security),
    user_repository=None,
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns None if no credentials provided (instead of raising exception).
    
    Usage:
        @app.get("/public")
        async def public_route(current_user: Optional[User] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": f"Hello {current_user.name}"}
            return {"message": "Hello anonymous"}
    """
    
    if not credentials:
        return None
    
    token = credentials.credentials
    success, user, _ = await auth_handler.authenticate_and_provision_user(
        token=token,
        user_repository=user_repository,
    )
    
    return user if success else None


def require_role(required_role: str):
    """
    Factory function to create a role-based dependency.
    
    Usage:
        @app.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_role("admin"))
        ):
            # This endpoint only accessible to admins
            return {"deleted": user_id}
    
    Args:
        required_role: The role required to access the endpoint.
    
    Returns:
        Async dependency function.
    
    Raises:
        HTTPException: 403 Forbidden if user lacks required role.
    """
    
    async def check_role(current_user: User = Depends(get_current_user)) -> None:
        """Check if user has the required role."""
        
        # Check primary role
        if current_user.role == required_role:
            return
        
        # Check additional roles
        if required_role in current_user.roles:
            return
        
        logger.warning(
            f"⚠️  User {current_user.email} lacks required role '{required_role}'. "
            f"Has: {current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This operation requires '{required_role}' role",
        )
    
    return check_role


def require_any_role(*allowed_roles: str):
    """
    Factory function to require any of multiple roles.
    
    Usage:
        @app.post("/reports")
        async def create_report(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_any_role("analyst", "admin", "manager"))
        ):
            return {"report": "created"}
    
    Args:
        allowed_roles: List of allowed roles (any will pass).
    
    Returns:
        Async dependency function.
    """
    
    async def check_any_role(current_user: User = Depends(get_current_user)) -> None:
        """Check if user has any of the allowed roles."""
        
        if current_user.role in allowed_roles:
            return
        
        if any(role in current_user.roles for role in allowed_roles):
            return
        
        logger.warning(
            f"⚠️  User {current_user.email} doesn't have any allowed role. "
            f"Allowed: {allowed_roles}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This operation requires one of: {', '.join(allowed_roles)}",
        )
    
    return check_any_role


def require_all_roles(*required_roles: str):
    """
    Factory function to require all of multiple roles (intersection).
    
    Args:
        required_roles: Roles that must all be present.
    
    Returns:
        Async dependency function.
    """
    
    async def check_all_roles(current_user: User = Depends(get_current_user)) -> None:
        """Check if user has all required roles."""
        
        user_roles = {current_user.role} | set(current_user.roles)
        required_set = set(required_roles)
        
        if required_set.issubset(user_roles):
            return
        
        missing = required_set - user_roles
        logger.warning(
            f"⚠️  User {current_user.email} missing roles: {missing}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This operation requires all of: {', '.join(required_roles)}",
        )
    
    return check_all_roles
