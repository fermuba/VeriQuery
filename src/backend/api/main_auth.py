"""
ForensicGuardian API - Main app with proper authentication integration.

This is the CORRECT way to integrate the auth system with FastAPI.
Uses dependency injection to properly wire UserRepository through the chain.

Architecture:
    Endpoint → get_current_user → get_user_repo → get_db → Database
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

# ============================================================
# 1. Import Auth Components
# ============================================================

from auth.config import auth_config
from auth.models import Base
from auth.user_repository import UserRepository
from auth.auth_handler import auth_handler
from auth.schemas import User
from auth.dependencies import HTTPBearer
from auth.protected_routes import router as auth_router

# ============================================================
# 2. Setup Database (from your existing setup)
# ============================================================

from database import SessionLocal, engine

logger = logging.getLogger(__name__)


# ============================================================
# 3. FastAPI Dependency Chain (CRITICAL PART)
# ============================================================

def get_db() -> Session:
    """
    Dependency: Database session.
    FastAPI will call this and inject the session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """
    Dependency: User repository with database session.
    This gets injected into get_current_user.
    """
    return UserRepository(db)


async def get_current_user(
    credentials: HTTPBearer = Depends(HTTPBearer(auto_error=False)),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Dependency: Current authenticated user.
    
    This is called on EVERY protected endpoint.
    It:
    1. Extracts Bearer token from Authorization header
    2. Validates token signature with JWKS
    3. Validates tenant ID (security)
    4. Auto-provisions user if needed
    5. Returns User object
    
    Raises:
        HTTPException 401: No token or invalid token
        HTTPException 403: User not active
    """
    
    # Check credentials present
    if not credentials:
        logger.warning("❌ No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Authenticate and provision user (FULL FLOW)
    success, user, error_msg = await auth_handler.authenticate_and_provision_user(
        token=credentials.credentials,
        user_repository=user_repo,
    )
    
    if not success:
        logger.error(f"❌ Auth failed: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"❌ Inactive user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    logger.info(f"✅ User authenticated: {user.email} (role: {user.role})")
    return user


# ============================================================
# 4. Lifespan: Startup/Shutdown
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan events: startup and shutdown.
    """
    
    # ===== STARTUP =====
    print("\n" + "=" * 70)
    print("🚀 STARTING ForensicGuardian API")
    print("=" * 70)
    
    # Create database tables (including auth tables)
    print("🔄 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
    except Exception as e:
        print(f"⚠️  Error creating tables: {e}")
    
    # Validate authentication configuration
    print("🔐 Validating authentication configuration...")
    try:
        auth_config.validate()
        print("✅ Authentication configuration valid")
        print(f"   - Client ID: {auth_config.CLIENT_ID[:20]}...")
        print(f"   - Tenant ID: {auth_config.TENANT_ID[:20]}...")
        print(f"   - Tenant mode: {'multi-tenant ⚠️' if auth_config.ALLOW_MULTI_TENANT else 'single-tenant ✅'}")
    except ValueError as e:
        print(f"❌ Auth config error: {e}")
    
    print("=" * 70)
    print("✅ API READY\n")
    
    yield
    
    # ===== SHUTDOWN =====
    print("\n🛑 Shutting down ForensicGuardian API...")


# ============================================================
# 5. Create FastAPI App
# ============================================================

app = FastAPI(
    title="ForensicGuardian API",
    description="Enterprise-grade forensic analysis with secure authentication",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# 6. Include Auth Routes
# ============================================================

app.include_router(auth_router)


# ============================================================
# 7. Protected Endpoints (Examples)
# ============================================================

@app.get("/")
async def root():
    """Public endpoint - no auth required."""
    return {
        "message": "ForensicGuardian API",
        "docs": "/docs",
        "auth_health": "/api/v1/auth/health"
    }


@app.get("/api/profile")
async def get_profile(current_user: User = Depends(get_current_user)) -> dict:
    """
    Protected endpoint - requires Bearer token.
    
    Usage:
        curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/profile
    """
    return {
        "profile": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "tenant_id": current_user.tenant_id,
            "created_at": current_user.created_at.isoformat(),
        }
    }


@app.get("/api/dashboard")
async def dashboard(current_user: User = Depends(get_current_user)) -> dict:
    """
    Protected dashboard endpoint.
    Only accessible to authenticated users.
    """
    return {
        "dashboard": "ForensicGuardian",
        "user": current_user.email,
        "role": current_user.role,
    }


# ============================================================
# 8. Health Check
# ============================================================

@app.get("/health")
async def health_check() -> dict:
    """Health check - public endpoint."""
    return {
        "status": "healthy",
        "service": "ForensicGuardian API",
    }


# ============================================================
# 9. Run Server (Development)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_auth:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
