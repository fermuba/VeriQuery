"""
FastAPI Authentication Integration Guide.

This file shows how to integrate the authentication system with your FastAPI app.
Copy relevant parts to your main.py
"""

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# ============================================================
# 1. Import authentication components
# ============================================================

from auth.config import auth_config
from auth.models import Base
from auth.user_repository import UserRepository
from auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    require_role,
    require_any_role,
)
from auth.schemas import User
from auth.protected_routes import router as auth_router

# Import your database session
# from database import SessionLocal, engine

# ============================================================
# 2. Lifespan context (FastAPI startup/shutdown)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan events (startup and shutdown).
    """
    # ============ STARTUP ============
    
    # Create database tables (including auth tables)
    print("🔄 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Validate auth configuration
    print("🔐 Validating authentication configuration...")
    try:
        auth_config.validate()
        print("✅ Authentication configuration valid")
    except ValueError as e:
        print(f"⚠️  Warning: {e}")
    
    yield
    
    # ============ SHUTDOWN ============
    print("🛑 Shutting down...")


# ============================================================
# 3. Dependency injection for database session
# ============================================================

def get_db_session() -> Session:
    """
    FastAPI dependency to get database session.
    Modify based on your actual database setup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repository(db: Session = Depends(get_db_session)) -> UserRepository:
    """
    FastAPI dependency to get user repository.
    """
    return UserRepository(db)


# ============================================================
# 4. Override FastAPI dependencies with your database
# ============================================================

# This is optional but recommended for production
# It allows you to inject the user_repository into auth dependencies

async def get_current_user_with_db(
    credentials = Depends(HTTPBearer()),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Custom get_current_user that uses database.
    """
    from auth.auth_handler import auth_handler
    from fastapi import HTTPException, status
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )
    
    success, user, error_msg = await auth_handler.authenticate_and_provision_user(
        token=credentials.credentials,
        user_repository=user_repo,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Invalid token",
        )
    
    return user


# ============================================================
# 5. Create FastAPI app with authentication
# ============================================================

app = FastAPI(
    title="ForensicGuardian API",
    description="Enterprise-grade forensic analysis platform with secure authentication",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# 6. Include authentication routes
# ============================================================

app.include_router(auth_router)


# ============================================================
# 7. Example: Protected endpoints
# ============================================================

@app.get("/")
async def root():
    """Public endpoint - no authentication required."""
    return {
        "message": "ForensicGuardian API",
        "docs": "/docs",
        "auth_health": "/api/v1/auth/health"
    }


@app.get("/api/user-profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Protected endpoint - requires valid Bearer token.
    
    Usage:
        curl -H "Authorization: Bearer <TOKEN>" \
             http://localhost:8000/api/user-profile
    """
    return {
        "profile": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "created_at": current_user.created_at,
        }
    }


@app.post("/api/analysis/run")
async def run_analysis(
    analysis_config: dict,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_any_role("analyst", "admin")),
) -> dict:
    """
    Analyst-only endpoint - requires analyst or admin role.
    
    Usage:
        curl -X POST -H "Authorization: Bearer <TOKEN>" \
             -H "Content-Type: application/json" \
             -d '{"query": "..."}' \
             http://localhost:8000/api/analysis/run
    """
    return {
        "analysis_id": "ANALYSIS-001",
        "created_by": current_user.email,
        "status": "running",
    }


@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role("admin")),
) -> dict:
    """
    Admin-only endpoint - requires admin role.
    """
    return {"deleted": user_id}


@app.get("/api/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user_optional),
) -> dict:
    """
    Semi-public endpoint - works with or without authentication.
    """
    if current_user:
        return {
            "dashboard": "personalized",
            "user": current_user.email,
        }
    return {
        "dashboard": "public",
        "message": "Sign in for personalized dashboard",
    }


# ============================================================
# 8. Error handlers (optional)
# ============================================================

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Custom validation error handler."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
        },
    )


# ============================================================
# 9. Run the app
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # For development
        log_level="info",
    )
