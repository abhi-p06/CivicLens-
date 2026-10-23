import os
import hmac
import hashlib
import base64
import json
import time
from enum import Enum
from typing import Optional, Dict, Any, Tuple
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
    email: Optional[str] = None
    username: Optional[str] = None

# Standard well-documented development tokens for local academic & demo workflows
DEV_TOKENS = {
    "demo-inspector-token": AuthenticatedUser(
        user_id="INSP-MUMBAI-01",
        name="Ward Field Inspector",
        role=UserRole.INSPECTOR,
        email="inspector@civilens.org",
        username="inspector"
    ),
    "demo-admin-token": AuthenticatedUser(
        user_id="ADMIN-SYS-01",
        name="Municipal Operations Administrator",
        role=UserRole.ADMIN,
        email="admin@civilens.org",
        username="admin"
    ),
    "demo-citizen-token": AuthenticatedUser(
        user_id="CITIZEN-DEMO-01",
        name="Demo Citizen",
        role=UserRole.CITIZEN,
        email="citizen@civilens.org",
        username="citizen"
    )
}

# -----------------------------------------------------------------------------
# Password Hashing & Verification (PBKDF2-HMAC-SHA256)
# -----------------------------------------------------------------------------

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with 100,000 rounds.
    Returns (hex_hash, hex_salt).
    """
    if not salt:
        salt_bytes = os.urandom(16)
        salt = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt)

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        100_000
    )
    return dk.hex(), salt

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """
    Constant-time verification of password against salt and expected hash.
    """
    try:
        calculated_hash, _ = hash_password(password, salt=salt)
        return hmac.compare_digest(calculated_hash, expected_hash)
    except Exception:
        return False

# -----------------------------------------------------------------------------
# Cryptographically Signed Expiring Access Tokens (HMAC-SHA256)
# -----------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(
    user_id: str,
    role: UserRole,
    name: str,
    email: Optional[str] = None,
    username: Optional[str] = None,
    expires_in_seconds: int = 86400  # 24 hours
) -> str:
    """
    Creates a tamper-evident, cryptographically signed token with expiration.
    Format: <b64url_payload>.<b64url_signature>
    """
    now = int(time.time())
    payload = {
        "sub": user_id,
        "name": name,
        "role": role.value if hasattr(role, "value") else str(role),
        "email": email or "",
        "username": username or "",
        "iat": now,
        "exp": now + expires_in_seconds
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)

    secret = settings.auth_secret_key.encode("utf-8")
    signature = hmac.new(secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[AuthenticatedUser]:
    """
    Verifies signature and expiration of a signed access token.
    Returns AuthenticatedUser if valid, None if invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, sig_b64 = parts[0], parts[1]

        # Verify HMAC signature
        secret = settings.auth_secret_key.encode("utf-8")
        expected_sig = hmac.new(secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Verify expiration
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None

        role_str = payload.get("role")
        try:
            role = UserRole(role_str)
        except ValueError:
            return None

        return AuthenticatedUser(
            user_id=payload.get("sub", ""),
            name=payload.get("name", ""),
            role=role,
            email=payload.get("email") or None,
            username=payload.get("username") or None
        )
    except Exception:
        return None

# -----------------------------------------------------------------------------
# Credentials Authentication & FastAPI Dependencies
# -----------------------------------------------------------------------------

def authenticate_credentials(raw_token: Optional[str]) -> Optional[AuthenticatedUser]:
    """
    Validates token string or API key against signed tokens and configured secrets.
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
            role=UserRole.ADMIN,
            email="admin.env@civilens.org",
            username="admin_env"
        )

    if settings.inspector_api_key and cleaned_token == settings.inspector_api_key:
        return AuthenticatedUser(
            user_id="INSP-ENV-01",
            name="Configured Field Inspector",
            role=UserRole.INSPECTOR,
            email="inspector.env@civilens.org",
            username="inspector_env"
        )

    # 2. Cryptographically signed tokens (genuine login sessions)
    signed_user = decode_access_token(cleaned_token)
    if signed_user is not None:
        return signed_user

    # 3. Local development & academic demo tokens
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
    Returns None if unauthenticated.
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
require_citizen = require_role(UserRole.CITIZEN)
require_inspector = require_role(UserRole.INSPECTOR)
require_admin = require_role(UserRole.ADMIN)
