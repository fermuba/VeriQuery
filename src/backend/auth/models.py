"""
SQLAlchemy ORM models for user management.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserModel(Base):
    """
    User database model.
    Stores user information provisioned from Azure AD tokens.
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(String(255), primary_key=True, index=True, nullable=False)
    
    # User information
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    
    # Role and permissions
    role = Column(String(50), default="analyst", nullable=False, index=True)
    roles = Column(JSON, default=list, nullable=False)  # Additional roles
    
    # Azure AD metadata
    azure_oid = Column(String(255), unique=True, index=True, nullable=True)
    tenant_id = Column(String(255), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Metadata
    login_count = Column(Integer, default=0, nullable=False)
    
    def __repr__(self) -> str:
        return f"<UserModel id={self.id} email={self.email} role={self.role}>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "roles": self.roles or [],
            "azure_oid": self.azure_oid,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "is_active": self.is_active,
            "login_count": self.login_count,
        }
