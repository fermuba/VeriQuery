"""
Authentication and Authorization module for ForensicGuardian.
Handles Microsoft Entra ID (Azure AD) OAuth2/OIDC integration,
JWT validation, and user provisioning.
"""

from auth.dependencies import (
    get_current_user,
    require_role,
)
from auth.schemas import User, TokenData

__all__ = [
    "get_current_user",
    "require_role",
    "User",
    "TokenData",
]
