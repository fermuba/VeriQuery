"""
User repository for database operations.
Handles CRUD operations for user management.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from auth.models import UserModel
from auth.schemas import User, UserCreateSchema

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Data access layer for user operations.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize user repository.
        
        Args:
            db_session: SQLAlchemy database session.
        """
        self.db = db_session
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User's unique ID.
        
        Returns:
            User object or None if not found.
        """
        try:
            user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            
            if user_model:
                return self._model_to_schema(user_model)
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error fetching user {user_id}: {str(e)}")
            raise
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email.
        
        Returns:
            User object or None if not found.
        """
        try:
            user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
            
            if user_model:
                return self._model_to_schema(user_model)
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error fetching user by email {email}: {str(e)}")
            raise
    
    def get_by_azure_oid(self, azure_oid: str) -> Optional[User]:
        """
        Get user by Azure Object ID.
        
        Args:
            azure_oid: Azure AD Object ID.
        
        Returns:
            User object or None if not found.
        """
        try:
            user_model = self.db.query(UserModel).filter(
                UserModel.azure_oid == azure_oid
            ).first()
            
            if user_model:
                return self._model_to_schema(user_model)
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error fetching user by azure_oid: {str(e)}")
            raise
    
    def create(self, user_data: UserCreateSchema) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data.
        
        Returns:
            Created User object.
        
        Raises:
            IntegrityError: If user already exists or unique constraint violated.
        """
        try:
            user_model = UserModel(
                id=user_data.id,
                email=user_data.email,
                name=user_data.name,
                role=user_data.role,
                azure_oid=user_data.azure_oid,
                tenant_id=user_data.tenant_id,
                is_active=True,
                login_count=1,
            )
            
            self.db.add(user_model)
            self.db.commit()
            self.db.refresh(user_model)
            
            logger.info(f"✅ Created new user: {user_model.email}")
            return self._model_to_schema(user_model)
        
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"❌ Integrity error creating user: {str(e)}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating user: {str(e)}")
            raise
    
    def update(self, user: User) -> User:
        """
        Update an existing user.
        
        Args:
            user: User object with updated data.
        
        Returns:
            Updated User object.
        """
        try:
            user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
            
            if not user_model:
                raise ValueError(f"User {user.id} not found")
            
            # Update fields
            user_model.email = user.email
            user_model.name = user.name
            user_model.role = user.role
            user_model.roles = user.roles
            user_model.is_active = user.is_active
            user_model.last_login = user.last_login
            user_model.updated_at = datetime.utcnow()
            
            # Increment login count if last_login was updated
            if user.last_login:
                user_model.login_count += 1
            
            self.db.commit()
            self.db.refresh(user_model)
            
            logger.info(f"✅ Updated user: {user_model.email}")
            return self._model_to_schema(user_model)
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating user: {str(e)}")
            raise
    
    def deactivate(self, user_id: str) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID to deactivate.
        
        Returns:
            True if deactivated, False if user not found.
        """
        try:
            user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            
            if not user_model:
                return False
            
            user_model.is_active = False
            user_model.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"✅ Deactivated user: {user_model.email}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error deactivating user: {str(e)}")
            raise
    
    def list_by_role(self, role: str, limit: int = 100) -> list[User]:
        """
        List all users with a specific role.
        
        Args:
            role: Role to filter by.
            limit: Maximum number of results.
        
        Returns:
            List of User objects.
        """
        try:
            user_models = self.db.query(UserModel).filter(
                UserModel.role == role
            ).limit(limit).all()
            
            return [self._model_to_schema(u) for u in user_models]
        
        except Exception as e:
            logger.error(f"❌ Error listing users by role: {str(e)}")
            raise
    
    def list_active_users(self, limit: int = 1000) -> list[User]:
        """
        List all active users.
        
        Args:
            limit: Maximum number of results.
        
        Returns:
            List of User objects.
        """
        try:
            user_models = self.db.query(UserModel).filter(
                UserModel.is_active == True
            ).limit(limit).all()
            
            return [self._model_to_schema(u) for u in user_models]
        
        except Exception as e:
            logger.error(f"❌ Error listing active users: {str(e)}")
            raise
    
    @staticmethod
    def _model_to_schema(user_model: UserModel) -> User:
        """
        Convert SQLAlchemy model to Pydantic schema.
        
        Args:
            user_model: SQLAlchemy UserModel instance.
        
        Returns:
            Pydantic User schema.
        """
        return User(
            id=user_model.id,
            email=user_model.email,
            name=user_model.name,
            role=user_model.role,
            roles=user_model.roles or [],
            azure_oid=user_model.azure_oid,
            tenant_id=user_model.tenant_id,
            created_at=user_model.created_at,
            last_login=user_model.last_login,
            is_active=user_model.is_active,
        )
