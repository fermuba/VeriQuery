"""
Pydantic schemas for authentication data structures.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TokenData(BaseModel):
    """
    Represents decoded JWT token data.
    Extracted from Microsoft Entra ID token.
    """
    
    # Standard JWT claims
    sub: Optional[str] = Field(None, description="Subject (unique user ID in Azure AD)")
    oid: Optional[str] = Field(None, description="Object ID (alternative unique identifier)")
    email: Optional[str] = Field(None, description="User email address")
    preferred_username: Optional[str] = Field(None, description="Preferred username")
    name: Optional[str] = Field(None, description="Full name of the user")
    given_name: Optional[str] = Field(None, description="First name")
    family_name: Optional[str] = Field(None, description="Last name")
    
    # Standard JWT metadata
    iss: str = Field(..., description="Token issuer")
    aud: str = Field(..., description="Audience (who the token is for)")
    exp: int = Field(..., description="Expiration time (unix timestamp)")
    iat: int = Field(..., description="Issued at time (unix timestamp)")
    nbf: int = Field(..., description="Not before time (unix timestamp)")
    
    # Azure AD specific claims
    tid: Optional[str] = Field(None, description="Tenant ID")
    unique_name: Optional[str] = Field(None, description="Unique username")
    roles: Optional[List[str]] = Field(default_factory=list, description="User roles")
    appid: Optional[str] = Field(None, description="Application ID")
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional claims not explicitly defined


class User(BaseModel):
    """
    Represents an authenticated user in the system.
    Provisioned from Azure AD token data.
    """
    
    # Primary identifier
    id: str = Field(..., description="Unique user ID (from Azure AD token)")
    
    # User information
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    
    # Role and permissions
    role: str = Field(default="analyst", description="User role in the system")
    roles: List[str] = Field(default_factory=list, description="Additional roles")
    
    # Metadata
    azure_oid: Optional[str] = Field(None, description="Azure AD Object ID")
    tenant_id: Optional[str] = Field(None, description="Azure AD Tenant ID")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation time")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Status
    is_active: bool = Field(default=True, description="Whether user account is active")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True  # For ORM compatibility


class UserCreateSchema(BaseModel):
    """
    Schema for creating a new user during auto-provisioning.
    """
    
    id: str
    email: str
    name: str
    role: str = "analyst"
    azure_oid: Optional[str] = None
    tenant_id: Optional[str] = None


class AuthResponse(BaseModel):
    """
    Response containing authentication status and user info.
    """
    
    is_authenticated: bool
    user: Optional[User] = None
    message: str = ""
    token_valid: bool = False
