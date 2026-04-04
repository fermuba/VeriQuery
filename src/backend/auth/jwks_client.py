"""
JWKS (JSON Web Key Set) client for fetching and caching Microsoft public keys.
Implements secure JWT signature verification.
"""

import time
import logging
from typing import Optional, Dict, Any
import httpx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt

from auth.config import auth_config

logger = logging.getLogger(__name__)


class JWKSCache:
    """
    In-memory cache for JWKS (JSON Web Key Set) from Microsoft.
    Automatically refreshes expired keys.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize JWKS cache.
        
        Args:
            ttl_seconds: Time-to-live for cached keys in seconds.
        """
        self.ttl_seconds = ttl_seconds
        self._keys: Dict[str, Any] = {}
        self._last_fetched: float = 0
    
    def is_expired(self) -> bool:
        """Check if cached keys have expired."""
        return (time.time() - self._last_fetched) > self.ttl_seconds
    
    def get(self) -> Dict[str, Any]:
        """
        Get cached keys if valid, otherwise return empty dict.
        """
        if self.is_expired():
            return {}
        return self._keys
    
    def set(self, keys: Dict[str, Any]) -> None:
        """Cache JWKS keys and update timestamp."""
        self._keys = keys
        self._last_fetched = time.time()
        logger.debug(f"✅ JWKS cache updated at {time.time()}")
    
    def clear(self) -> None:
        """Clear cached keys."""
        self._keys = {}
        self._last_fetched = 0


class JWKSClient:
    """
    Fetches and manages Microsoft Entra ID JWKS (public keys).
    Validates JWT signatures using the correct public key.
    """
    
    def __init__(
        self,
        jwks_url: str = auth_config.JWKS_URL,
        cache_ttl: int = auth_config.JWKS_CACHE_TTL,
    ):
        """
        Initialize JWKS client.
        
        Args:
            jwks_url: URL to fetch JWKS from (Microsoft endpoint).
            cache_ttl: Cache TTL in seconds.
        """
        self.jwks_url = jwks_url
        self.cache = JWKSCache(ttl_seconds=cache_ttl)
        self.http_client = httpx.Client(timeout=10.0)
    
    async def fetch_jwks(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch JWKS from Microsoft endpoint with caching.
        
        Args:
            force_refresh: Force fetch from remote even if cached.
        
        Returns:
            Dictionary containing 'keys' array from JWKS endpoint.
        
        Raises:
            Exception: If unable to fetch JWKS from Microsoft.
        """
        
        # Try to use cached keys if not expired
        if not force_refresh:
            cached = self.cache.get()
            if cached:
                logger.debug("Using cached JWKS keys")
                return cached
        
        try:
            logger.info(f"Fetching JWKS from {self.jwks_url}")
            
            # Use httpx for async-compatible HTTP request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
            
            jwks_data = response.json()
            
            # Cache the keys
            self.cache.set(jwks_data)
            
            logger.info(f"✅ JWKS fetched successfully. Keys available: {len(jwks_data.get('keys', []))}")
            return jwks_data
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch JWKS from Microsoft: {str(e)}")
            
            # Try to use expired cache as fallback
            if self.cache._keys:
                logger.warning("Using expired cached JWKS keys as fallback")
                return self.cache._keys
            
            raise
    
    async def get_signing_key(self, token_header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the public key from JWKS that matches the token's 'kid' (Key ID).
        
        Args:
            token_header: JWT header containing 'kid' (key ID).
        
        Returns:
            The matching key from JWKS, or None if not found.
        """
        token_kid = token_header.get("kid")
        
        if not token_kid:
            logger.error("❌ Token header missing 'kid' (Key ID)")
            return None
        
        # Fetch JWKS (from cache or remote)
        jwks_data = await self.fetch_jwks()
        keys = jwks_data.get("keys", [])
        
        # Find the key matching the token's 'kid'
        for key in keys:
            if key.get("kid") == token_kid:
                logger.debug(f"✅ Found matching key with kid={token_kid}")
                return key
        
        logger.error(f"❌ No key found in JWKS matching token kid={token_kid}")
        logger.debug(f"Available keys: {[k.get('kid') for k in keys]}")
        return None
    
    @staticmethod
    def _build_rsa_public_key(jwk: Dict[str, Any]):
        """
        Convert JWK (JSON Web Key) format to RSA public key.
        
        Args:
            jwk: Key in JWK format from JWKS endpoint.
        
        Returns:
            RSA public key object.
        """
        
        # Extract JWK components (base64url encoded)
        n = jwk.get("n")  # Modulus
        e = jwk.get("e")  # Exponent
        
        if not n or not e:
            raise ValueError("Invalid JWK: missing 'n' or 'e' component")
        
        # Decode base64url and convert to integers
        from base64 import urlsafe_b64decode
        
        def decode_base64url(value):
            """Decode base64url string to bytes."""
            # Add padding if needed
            padding = 4 - (len(value) % 4)
            if padding:
                value += "=" * padding
            return urlsafe_b64decode(value)
        
        n_bytes = decode_base64url(n)
        e_bytes = decode_base64url(e)
        
        # Convert to integers
        n_int = int.from_bytes(n_bytes, byteorder="big")
        e_int = int.from_bytes(e_bytes, byteorder="big")
        
        # Create RSA public key
        public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key(default_backend())
        
        return public_key
    
    async def verify_token(
        self,
        token: str,
        issuer: str,
        audience: str,
        algorithms: list = None,
    ) -> Dict[str, Any]:
        """
        Verify JWT token signature and claims.
        
        CRITICAL: This performs full cryptographic signature verification.
        Do NOT skip this step.
        
        Args:
            token: JWT token string.
            issuer: Expected token issuer (iss claim).
            audience: Expected audience (aud claim).
            algorithms: Allowed algorithms (default: ["RS256"]).
        
        Returns:
            Decoded token claims if valid.
        
        Raises:
            jwt.InvalidSignatureError: If signature is invalid.
            jwt.InvalidIssuerError: If issuer doesn't match.
            jwt.InvalidAudienceError: If audience doesn't match.
            jwt.ExpiredSignatureError: If token is expired.
            Exception: Other JWT validation errors.
        """
        
        if algorithms is None:
            algorithms = ["RS256"]
        
        try:
            # Decode without verification first to get the header
            unverified_header = jwt.get_unverified_header(token)
            
            # Get the signing key from JWKS
            signing_key = await self.get_signing_key(unverified_header)
            
            if not signing_key:
                raise jwt.InvalidKeyError("No matching key found in JWKS")
            
            # Convert JWK to RSA public key
            public_key = self._build_rsa_public_key(signing_key)
            
            # Verify and decode the token
            # This performs:
            # 1. Signature verification using the public key
            # 2. Issuer validation
            # 3. Audience validation
            # 4. Expiration check
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=algorithms,
                issuer=issuer,
                audience=audience,
                options={"leeway": auth_config.TOKEN_EXPIRATION_TOLERANCE},
            )
            
            logger.info(f"✅ Token verified successfully for user: {decoded.get('email', decoded.get('preferred_username'))}")
            return decoded
        
        except jwt.InvalidSignatureError:
            logger.error("❌ Token signature is invalid")
            raise
        except jwt.InvalidIssuerError:
            logger.error(f"❌ Token issuer mismatch. Expected: {issuer}")
            raise
        except jwt.InvalidAudienceError:
            logger.error(f"❌ Token audience mismatch. Expected: {audience}")
            raise
        except jwt.ExpiredSignatureError:
            logger.error("❌ Token has expired")
            raise
        except Exception as e:
            logger.error(f"❌ Token verification failed: {str(e)}")
            raise


# Global JWKS client instance
jwks_client = JWKSClient()
