import os
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import Header, HTTPException, status, Depends
from app.config import settings

class UserRole(str, Enum):
    CITIZEN = "citizen"
    INSPECTOR = "inspector"
    ADMIN = "admin"

ROLE_HIERARCHY = {
    UserRole.CITIZEN: 1,
    UserRole.INSPECTOR: 2,
    UserRole.ADMIN: 3
}

class AuthenticatedUser(BaseModel):
    user_id: str
    name: str
    role: UserRole

# Standard well-documented development tokens for local academic & demo workflows
DEV_TOKENS = {
    "demo-inspector-token": AuthenticatedUser(
        user_id="INSP-MUMBAI-01",
        name="Ward Field Inspector",
        role=UserRole.INSPECTOR
    ),
    "demo-admin-token": AuthenticatedUser(
        user_id="ADMIN-SYS-01",
        name="Municipal Operations Administrator",
        role=UserRole.ADMIN
    )
}

def authenticate_credentials(raw_token: Optional[str]) -> Optional[AuthenticatedUser]:
    """
    Validates token string or API key against configured secrets.
    Extracts Bearer prefix if provided.
    """
    if not raw_token:
        return None

    cleaned_token = raw_token.strip()
    if cleaned_token.lower().startswith("bearer "):
        cleaned_token = cleaned_token[7:].strip()

    if not cleaned_token:
        return None

    # 1. Environment-configured production keys (highest priority)
    if settings.admin_api_key and cleaned_token == settings.admin_api_key:
        return AuthenticatedUser(
            user_id="ADMIN-ENV-01",
            name="Configured Municipal Administrator",
            role=UserRole.ADMIN
        )

    if settings.inspector_api_key and cleaned_token == settings.inspector_api_key:
        return AuthenticatedUser(
            user_id="INSP-ENV-01",
            name="Configured Field Inspector",
            role=UserRole.INSPECTOR
        )

    # 2. Local development & academic demo tokens
    # Permitted ONLY in non-production environments when allow_dev_tokens is enabled; strictly rejected in production
    is_production = settings.env.lower() in ("production", "prod")
    dev_allowed = (not is_production) and settings.allow_dev_tokens
    if dev_allowed and cleaned_token in DEV_TOKENS:
        return DEV_TOKENS[cleaned_token]

    return None


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[AuthenticatedUser]:
    """
    FastAPI dependency: Extracts authenticated user from Authorization header or X-API-Key.
    Returns None if unauthenticated (representing Citizen role).
    """
    token = authorization or x_api_key
    if not token:
        return None
    return authenticate_credentials(token)


def require_role(min_role: UserRole):
    """
    FastAPI dependency factory enforcing minimum role hierarchy:
    - CITIZEN < INSPECTOR < ADMIN
    - Returns 401 if unauthenticated or token is invalid.
    - Returns 403 if authenticated user possesses insufficient permissions.
    """
    def dependency(
        authorization: Optional[str] = Header(None, alias="Authorization"),
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ) -> AuthenticatedUser:
        token = authorization or x_api_key
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication required: Provide a valid Bearer token or X-API-Key with {min_role.value.upper()} privileges.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user = authenticate_credentials(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if ROLE_HIERARCHY[user.role] < ROLE_HIERARCHY[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Operation requires {min_role.value.upper()} privileges. Current role: {user.role.value.upper()}."
            )

        return user

    return dependency

# Reusable role-check dependencies
require_inspector = require_role(UserRole.INSPECTOR)
require_admin = require_role(UserRole.ADMIN)
