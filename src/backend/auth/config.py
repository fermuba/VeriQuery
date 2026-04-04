"""
Authentication configuration for Microsoft Entra ID.
Loads and validates environment variables.
"""

import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    """Azure AD authentication configuration."""

    # ============================================
    # Azure AD / Entra ID Configuration
    # ============================================
    
    # CLIENT_ID: The application ID of your Azure AD app
    # Get from: Azure Portal > App registrations > Your app > Application (client) ID
    CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    
    # TENANT_ID: Your Azure AD tenant ID
    # Get from: Azure Portal > Azure AD > Overview > Tenant ID
    TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    
    # ISSUER: The token issuer URL
    # Format: https://login.microsoftonline.com/{tenant_id}/v2.0
    ISSUER: str = os.getenv(
        "AZURE_ISSUER",
        f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID', '')}/v2.0"
    )
    
    # JWKS_URL: Microsoft's JWKS endpoint for fetching public keys
    JWKS_URL: str = os.getenv(
        "AZURE_JWKS_URL",
        "https://login.microsoftonline.com/common/discovery/v2.0/keys"
    )
    
    # AUDIENCE: Who the token is intended for (typically your Client ID)
    AUDIENCE: Optional[str] = os.getenv("AZURE_AUDIENCE")
    
    # ============================================
    # JWT Validation Settings
    # ============================================
    
    # Token expiration tolerance (in seconds) for clock skew
    TOKEN_EXPIRATION_TOLERANCE: int = int(os.getenv("TOKEN_EXPIRATION_TOLERANCE", "60"))
    
    # ============================================
    # Caching Configuration
    # ============================================
    
    # JWKS cache TTL (Time To Live) in seconds
    # Default: 3600 (1 hour) - Microsoft rotates keys periodically
    JWKS_CACHE_TTL: int = int(os.getenv("JWKS_CACHE_TTL", "3600"))
    
    # ============================================
    # Tenant Validation Configuration (Multi-Tenant Support)
    # ============================================
    
    # ALLOW_MULTI_TENANT: If False (default), only accept tokens from configured TENANT_ID
    # If True, accept tokens from any tenant (less secure, for demos/hackathons)
    # 
    # Security Note:
    # - Single-tenant (False) is recommended for production
    # - Multi-tenant (True) should only be used for testing/demo scenarios
    ALLOW_MULTI_TENANT: bool = os.getenv("ALLOW_MULTI_TENANT", "false").lower() in ("true", "1", "yes")
    
    # ============================================
    # Default Role Configuration
    # ============================================
    
    # Default role for newly provisioned users
    DEFAULT_USER_ROLE: str = os.getenv("DEFAULT_USER_ROLE", "analyst")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars from other modules
        extra = "ignore"  # Ignore extra env vars from other modules
    
    def validate(self) -> bool:
        """
        Validate that all required configuration is set.
        
        Returns:
            bool: True if all required fields are configured, False otherwise.
        
        Raises:
            ValueError: If critical configuration is missing.
        """
        required_fields = ["CLIENT_ID", "TENANT_ID", "ISSUER"]
        missing = [f for f in required_fields if not getattr(self, f)]
        
        if missing:
            raise ValueError(
                f"Missing required Azure AD configuration: {', '.join(missing)}. "
                "Please set environment variables: "
                "AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_ISSUER"
            )
        
        # Log multi-tenant configuration
        tenant_mode = "multi-tenant (⚠️  less secure)" if self.ALLOW_MULTI_TENANT else "single-tenant (✅ secure)"
        print(f"🔐 Tenant validation mode: {tenant_mode}")
        
        return True


# Global config instance
auth_config = AuthConfig()

# Validate configuration on import
try:
    auth_config.validate()
except ValueError as e:
    print(f"⚠️  Warning: {e}")
    print("Some features may not work correctly.")
