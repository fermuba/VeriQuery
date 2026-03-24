"""
Unit tests and validation for authentication system.
Location: tests/test_auth.py

Run tests with:
    pytest tests/test_auth.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# Adjust imports based on your project structure
import sys
from pathlib import Path

# Add src/backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from auth.config import auth_config
from auth.schemas import TokenData, User, UserCreateSchema
from auth.auth_handler import auth_handler
from auth.jwks_client import JWKSClient, JWKSCache


# ============================================================
# JWKS Cache Tests
# ============================================================

class TestJWKSCache:
    """Test JWKS caching functionality."""
    
    def test_cache_initialization(self):
        """Test cache initializes empty."""
        cache = JWKSCache(ttl_seconds=3600)
        assert cache.get() == {}
        assert cache.is_expired()
    
    def test_cache_set_and_get(self):
        """Test setting and getting cached keys."""
        cache = JWKSCache(ttl_seconds=3600)
        
        keys = {"keys": [{"kid": "test-key-1"}]}
        cache.set(keys)
        
        cached = cache.get()
        assert cached == keys
        assert not cache.is_expired()
    
    def test_cache_expiration(self):
        """Test cache expiration logic."""
        cache = JWKSCache(ttl_seconds=1)
        
        keys = {"keys": [{"kid": "test-key"}]}
        cache.set(keys)
        
        # Should not be expired immediately
        assert not cache.is_expired()
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        
        # Now should be expired
        assert cache.is_expired()
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = JWKSCache()
        cache.set({"keys": []})
        
        assert cache.get() != {}
        
        cache.clear()
        assert cache.get() == {}


# ============================================================
# TokenData Schema Tests
# ============================================================

class TestTokenData:
    """Test TokenData Pydantic schema."""
    
    def test_minimal_token_data(self):
        """Test creating TokenData with minimal required fields."""
        token_data = TokenData(
            iss="https://login.microsoftonline.com/tenant-id/v2.0",
            aud="client-id",
            exp=int(datetime.utcnow().timestamp()) + 3600,
            iat=int(datetime.utcnow().timestamp()),
            nbf=int(datetime.utcnow().timestamp()),
        )
        
        assert token_data.iss is not None
        assert token_data.aud is not None
        assert token_data.exp > 0
    
    def test_token_data_with_user_info(self):
        """Test TokenData with user information."""
        token_data = TokenData(
            sub="user-uuid",
            oid="object-id",
            email="user@company.com",
            name="John Doe",
            iss="https://login.microsoftonline.com/tenant-id/v2.0",
            aud="client-id",
            exp=int(datetime.utcnow().timestamp()) + 3600,
            iat=int(datetime.utcnow().timestamp()),
            nbf=int(datetime.utcnow().timestamp()),
            roles=["analyst", "user"],
        )
        
        assert token_data.email == "user@company.com"
        assert token_data.name == "John Doe"
        assert "analyst" in token_data.roles


# ============================================================
# User Schema Tests
# ============================================================

class TestUserSchema:
    """Test User Pydantic schema."""
    
    def test_create_user_schema(self):
        """Test creating a User."""
        user = User(
            id="user-uuid",
            email="user@company.com",
            name="John Doe",
            role="analyst",
        )
        
        assert user.id == "user-uuid"
        assert user.email == "user@company.com"
        assert user.role == "analyst"
        assert user.is_active is True
    
    def test_user_with_roles(self):
        """Test User with multiple roles."""
        user = User(
            id="user-uuid",
            email="user@company.com",
            name="John Doe",
            role="admin",
            roles=["analyst", "manager"],
        )
        
        assert user.role == "admin"
        assert "analyst" in user.roles
        assert len(user.roles) == 2


# ============================================================
# AuthHandler Tests
# ============================================================

class TestAuthHandler:
    """Test authentication handler logic."""
    
    def test_extract_user_info_from_token(self):
        """Test extracting user info from token data."""
        token_data = TokenData(
            oid="object-id",
            email="user@company.com",
            name="John Doe",
            iss="https://login.microsoftonline.com/tenant-id/v2.0",
            aud="client-id",
            exp=int(datetime.utcnow().timestamp()) + 3600,
            iat=int(datetime.utcnow().timestamp()),
            nbf=int(datetime.utcnow().timestamp()),
            tid="tenant-id",
        )
        
        user_info = auth_handler.extract_user_info_from_token(token_data)
        
        assert user_info["id"] == "object-id"
        assert user_info["email"] == "user@company.com"
        assert user_info["name"] == "John Doe"
        assert user_info["tenant_id"] == "tenant-id"
    
    def test_extract_user_info_fallback_to_sub(self):
        """Test fallback to 'sub' if 'oid' not present."""
        token_data = TokenData(
            sub="sub-value",
            email="user@company.com",
            name="John Doe",
            iss="https://login.microsoftonline.com/tenant-id/v2.0",
            aud="client-id",
            exp=int(datetime.utcnow().timestamp()) + 3600,
            iat=int(datetime.utcnow().timestamp()),
            nbf=int(datetime.utcnow().timestamp()),
        )
        
        user_info = auth_handler.extract_user_info_from_token(token_data)
        
        assert user_info["id"] == "sub-value"  # Fallback to sub


# ============================================================
# Configuration Tests
# ============================================================

class TestAuthConfig:
    """Test authentication configuration."""
    
    def test_config_loads_from_env(self):
        """Test that config loads from environment."""
        # Auth config should load from environment
        assert auth_config.CLIENT_ID is not None or auth_config.CLIENT_ID == ""
        assert auth_config.TENANT_ID is not None or auth_config.TENANT_ID == ""
    
    def test_default_values(self):
        """Test default configuration values."""
        assert auth_config.JWKS_CACHE_TTL == 3600
        assert auth_config.TOKEN_EXPIRATION_TOLERANCE == 60
        assert auth_config.DEFAULT_USER_ROLE == "analyst"


# ============================================================
# Integration Tests (requires actual Azure AD)
# ============================================================

class TestJWKSIntegration:
    """Integration tests with actual Microsoft JWKS endpoint."""
    
    @pytest.mark.asyncio
    async def test_fetch_real_jwks(self):
        """
        Test fetching real JWKS from Microsoft.
        Requires internet connection.
        """
        client = JWKSClient()
        
        try:
            jwks = await client.fetch_jwks()
            
            assert "keys" in jwks
            assert len(jwks["keys"]) > 0
            
            # Check key structure
            key = jwks["keys"][0]
            assert "kid" in key  # Key ID
            assert "kty" in key  # Key type (RSA)
            
        except Exception as e:
            pytest.skip(f"Could not fetch JWKS: {str(e)}")


# ============================================================
# Example: Running Tests
# ============================================================

if __name__ == "__main__":
    """
    Run tests with pytest:
    
        pytest tests/test_auth.py -v
    
    Run specific test:
    
        pytest tests/test_auth.py::TestJWKSCache::test_cache_set_and_get -v
    
    Run with coverage:
    
        pytest tests/test_auth.py --cov=auth --cov-report=html
    """
    
    print("✅ Test suite ready. Run with: pytest tests/test_auth.py -v")
