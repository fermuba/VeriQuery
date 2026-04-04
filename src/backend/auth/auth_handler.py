"""
Core authentication handler logic.
Validates tokens, manages user provisioning, and handles auth flow.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from auth.config import auth_config
from auth.schemas import User, TokenData, UserCreateSchema
from auth.jwks_client import jwks_client

logger = logging.getLogger(__name__)


class AuthHandler:
    """
    Central authentication handler.
    Manages token validation and user provisioning.
    """
    
    def __init__(self):
        """Initialize authentication handler."""
        self.config = auth_config
    
    async def validate_bearer_token(self, token: str) -> Tuple[bool, Optional[TokenData], str]:
        """
        Validate a Bearer token from Authorization header.
        
        Args:
            token: JWT token string (without "Bearer " prefix).
        
        Returns:
            Tuple of (is_valid, token_data, error_message)
        """
        
        if not token:
            return False, None, "No token provided"
        
        try:
            # Validate token signature and claims
            decoded = await jwks_client.verify_token(
                token=token,
                issuer=self.config.ISSUER,
                audience=self.config.CLIENT_ID,
            )
            
            # Convert to TokenData schema
            token_data = TokenData(**decoded)
            
            logger.info(f"✅ Token validated for user: {token_data.email}")
            return True, token_data, ""
        
        except Exception as e:
            error_msg = f"Token validation failed: {str(e)}"
            logger.warning(f"⚠️  {error_msg}")
            return False, None, error_msg
    
    def extract_user_info_from_token(self, token_data: TokenData) -> dict:
        """
        Extract user information from validated token.
        
        Args:
            token_data: Decoded and validated token.
        
        Returns:
            Dictionary with user information.
        """
        
        # Use OID (Object ID) as primary ID, fall back to 'sub'
        user_id = token_data.oid or token_data.sub
        
        if not user_id:
            raise ValueError("Token must contain 'oid' or 'sub' claim")
        
        # Construct user info
        return {
            "id": user_id,
            "email": token_data.email or token_data.preferred_username or "unknown@example.com",
            "name": token_data.name or token_data.given_name or "Unknown User",
            "azure_oid": token_data.oid,
            "tenant_id": token_data.tid,
            "roles": token_data.roles or [],
        }
    
    def validate_tenant(self, token_data: TokenData) -> Tuple[bool, str]:
        """
        Validate tenant ID from token claims.
        
        Security-critical function:
        - In single-tenant mode: Ensures the token is from your organization
        - In multi-tenant mode: Logs the tenant for auditing
        
        This validation MUST happen AFTER signature verification to ensure
        we only validate tokens that are cryptographically signed by Microsoft.
        
        Args:
            token_data: Decoded and validated JWT token.
        
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if tenant is allowed, False otherwise
            - error_message: Descriptive message (empty if valid)
        """
        
        # Extract tenant ID from token
        token_tenant_id = token_data.tid
        configured_tenant_id = self.config.TENANT_ID
        
        # Always log tenant information for audit trail
        logger.info(f"🔐 Tenant validation: Token tenant={token_tenant_id}, Configured tenant={configured_tenant_id}")
        
        # ===== MULTI-TENANT MODE (Less Secure) =====
        if self.config.ALLOW_MULTI_TENANT:
            logger.warning(
                f"⚠️  MULTI-TENANT MODE ENABLED: Accepting token from tenant {token_tenant_id}. "
                f"This is not recommended for production environments."
            )
            return True, ""
        
        # ===== SINGLE-TENANT MODE (Default, Secure) =====
        # In single-tenant mode, we ONLY accept tokens from the configured tenant
        if not token_tenant_id:
            error_msg = "❌ Token missing 'tid' (tenant ID) claim"
            logger.error(error_msg)
            return False, error_msg
        
        if token_tenant_id != configured_tenant_id:
            error_msg = (
                f"❌ TENANT MISMATCH (SECURITY): Token from tenant '{token_tenant_id}' "
                f"does not match configured tenant '{configured_tenant_id}'. "
                f"This token is not from your organization."
            )
            logger.error(error_msg)
            return False, error_msg
        
        logger.info(f"✅ Tenant validation passed: {token_tenant_id}")
        return True, ""
    
    async def authenticate_and_provision_user(
        self,
        token: str,
        user_repository=None,  # Injected dependency
    ) -> Tuple[bool, Optional[User], str]:
        """
        Complete authentication flow:
        1. Validate token signature (cryptographic verification)
        2. Validate tenant ID (security-critical)
        3. Extract user info
        4. Check if user exists in database
        5. Auto-provision new user if needed
        
        Args:
            token: JWT token from Authorization header.
            user_repository: Database repository for user operations.
        
        Returns:
            Tuple of (success, user_object, error_message)
        """
        
        # Step 1: Validate token signature (RSA verification with JWKS)
        is_valid, token_data, error_msg = await self.validate_bearer_token(token)
        
        if not is_valid:
            return False, None, error_msg
        
        try:
            # Step 2: SECURITY-CRITICAL - Validate tenant ID
            # This must happen AFTER signature verification to ensure we only check
            # tokens that are cryptographically signed by Microsoft.
            is_tenant_valid, tenant_error = self.validate_tenant(token_data)
            
            if not is_tenant_valid:
                return False, None, tenant_error
            
            # Step 3: Extract user info from token
            user_info = self.extract_user_info_from_token(token_data)
            user_id = user_info["id"]
            
            # Step 4: Check if user exists in database
            if user_repository:
                existing_user = user_repository.get_by_id(user_id)
                
                if existing_user:
                    # User exists - update last login
                    logger.info(f"✅ Existing user logged in: {existing_user.email} (tenant: {user_info['tenant_id']})")
                    existing_user.last_login = datetime.utcnow()
                    user_repository.update(existing_user)
                    return True, existing_user, ""
                
                # Step 5: Auto-provision new user
                logger.info(f"Creating new user from token: {user_info['email']} (tenant: {user_info['tenant_id']})")
                
                new_user_data = UserCreateSchema(
                    id=user_id,
                    email=user_info["email"],
                    name=user_info["name"],
                    role=self.config.DEFAULT_USER_ROLE,
                    azure_oid=user_info["azure_oid"],
                    tenant_id=user_info["tenant_id"],
                )
                
                new_user = user_repository.create(new_user_data)
                logger.info(f"✅ New user provisioned: {new_user.email} with role {new_user.role} (tenant: {new_user.tenant_id})")
                
                return True, new_user, ""
            
            else:
                # No repository - create in-memory user (for testing/stateless mode)
                logger.warning("⚠️  No user repository configured. Using in-memory user.")
                
                user = User(
                    id=user_id,
                    email=user_info["email"],
                    name=user_info["name"],
                    role=self.config.DEFAULT_USER_ROLE,
                    azure_oid=user_info.get("azure_oid"),
                    tenant_id=user_info.get("tenant_id"),
                )
                
                return True, user, ""
        
        except Exception as e:
            error_msg = f"User provisioning failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, None, error_msg


# Global auth handler instance
auth_handler = AuthHandler()
