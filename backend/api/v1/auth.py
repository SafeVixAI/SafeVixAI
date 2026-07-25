# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import AuditEvent, AuditLog
from core.database import get_db
from core.limiter import limiter
from core.security import (
    ALGORITHM,
    APP_JWT_AUDIENCE,
    APP_JWT_ISSUER,
    SECRET_KEY,
    create_access_token,
    create_secure_cookie_response,
    get_current_user,
    is_token_revoked,
    revoke_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/csrf-token")
@limiter.limit("30/minute")
async def get_csrf_token(request: Request) -> dict:
    """Return CSRF token for mutation requests.

    The token is stored in an httponly cookie. Frontend reads it
    via this endpoint and sends it back as X-CSRF-Token header.
    """
    import secrets as _secrets
    token = _secrets.token_urlsafe(32)
    response = JSONResponse(content={"csrf_token": token})
    is_prod = os.environ.get("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=86400,
    )
    return response

class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)
    name: str = Field(min_length=2, max_length=255)
    role: str = Field(default="operator", min_length=2, max_length=32)

class RegisterResponse(BaseModel):
    message: str
    operator_name: str
    email: str

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)

class LoginResponse(BaseModel):
    message: str
    operator_name: str

def _verify_pbkdf2_password(password: str, encoded_hash: str) -> bool:
    """Verify pbkdf2_sha256$iterations$salt$hex_digest from environment or database."""
    try:
        algorithm, iterations_raw, salt, expected = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def _configured_operator() -> dict[str, str] | None:
    email = os.environ.get("AUTH_OPERATOR_EMAIL", "").strip().lower()
    password_hash = os.environ.get("AUTH_OPERATOR_PASSWORD_HASH", "").strip()
    name = os.environ.get("AUTH_OPERATOR_NAME", "SafeVixAI Operator").strip()
    if not email or not password_hash:
        return None
    return {"email": email, "password_hash": password_hash, "name": name}

def _hash_password(password: str) -> str:
    """Generate PBKDF2 hash of the password."""
    salt = secrets.token_hex(16)
    iterations = 100000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"

@router.post("/register", response_model=RegisterResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Register a new municipal operator profile dynamically in the system.

    Hashes the user password securely via PBKDF2 with unique salts, checks email
    uniqueness, and persists the record to the backend SQL database.

    Args:
        request: The FastAPI request instance.
        body: RegisterRequest containing email, password, name, and role.
        db: Database session injection.

    Returns:
        JSONResponse (201) detailing success message, name, and email of the user.

    Raises:
        HTTPException (400): If an operator account with the same email already exists.
    """
    from sqlalchemy import select

    from models.user import OperatorUser

    email = body.email.strip().lower()

    # Check if user already exists
    stmt = select(OperatorUser).where(OperatorUser.email == email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Operator with this email already exists")

    hashed = _hash_password(body.password)
    new_operator = OperatorUser(
        email=email,
        hashed_password=hashed,
        name=body.name,
        role=body.role,
        is_active=True
    )

    db.add(new_operator)
    await db.commit()
    await db.refresh(new_operator)
    AuditLog.log_auth_login(str(new_operator.id), request.client.host if request.client else "unknown", new_operator.name)

    return JSONResponse(
        status_code=201,
        content={
            "message": "Operator registered successfully",
            "operator_name": new_operator.name,
            "email": new_operator.email
        }
    )

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Authenticate municipal operators and issue secure HTTP-only session cookies.

    Performs dynamic multi-operator database lookups first, falling back to
    environment-based static operator settings if required. Validates passwords
    via secure PBKDF2 comparison.

    Args:
        request: The FastAPI request instance.
        body: LoginRequest containing email and plain-text password.
        db: Database session injection.

    Returns:
        JSONResponse containing confirmation message and operator display name,
        decorated with an HTTP-only JWT access cookie.

    Raises:
        HTTPException (401): If credentials are invalid or user is inactive.
    """
    from sqlalchemy import select

    from models.user import OperatorUser

    email = body.email.strip().lower()

    # 1. Try database-backed operator authentication
    stmt = select(OperatorUser).where(OperatorUser.email == email, OperatorUser.is_active)
    result = await db.execute(stmt)
    db_operator = result.scalar_one_or_none()

    if db_operator is not None:
        if _verify_pbkdf2_password(body.password, db_operator.hashed_password):
            token = create_access_token(
                data={"sub": email, "name": db_operator.name},
                role=db_operator.role,
            )
            ip = request.client.host if request.client else "unknown"
            AuditLog.log_auth_login(email, ip, db_operator.name)
            return create_secure_cookie_response(
                content={"message": "Login successful", "operator_name": db_operator.name},
                token=token,
            )
        else:
            ip = request.client.host if request.client else "unknown"
            AuditLog.log_auth_failed(email, ip, "invalid_password_db")
            raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2. Fall back to environment-based single-operator authentication
    operator = _configured_operator()
    if operator is not None and email == operator["email"] and _verify_pbkdf2_password(body.password, operator["password_hash"]):
            token = create_access_token(
                data={"sub": email, "name": operator["name"]},
                role="operator",
            )
            ip = request.client.host if request.client else "unknown"
            AuditLog.log_auth_login(email, ip, operator["name"])
            return create_secure_cookie_response(
                content={"message": "Login successful", "operator_name": operator["name"]},
                token=token,
            )

    ip = request.client.host if request.client else "unknown"
    AuditLog.log_auth_failed(email, ip, "invalid_credentials_fallback")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
@limiter.limit("10/minute")
async def logout(request: Request) -> JSONResponse:
    """
    Terminate operator sessions and clear secure cookies.

    Deletes the 'access_token' cookie from the client browser matching path,
    domain, and security attributes.

    Args:
        request: The FastAPI request instance.

    Returns:
        JSONResponse confirming successful session termination.
    """
    from core.security import COOKIE_HTTPONLY, COOKIE_PATH, COOKIE_SAMESITE, COOKIE_SECURE
    ip = request.client.host if request.client else "unknown"
    AuditLog.log(AuditEvent.AUTH_LOGOUT, ip_address=ip)
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(
        key="access_token",
        path=COOKIE_PATH,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE
    )
    return response

@router.get("/verify")
@limiter.limit("20/minute")
async def verify_token(request: Request, current_user: dict = Depends(get_current_user)) -> dict:
    """
    Validate the caller's active session bearer token.

    Decodes JWT token structures, validating expiration, audience, issuer,
    and checks if the token has been JTI blacklisted.

    Args:
        request: The FastAPI request instance.
        current_user: JWT payload context injected from request bearer dependencies.

    Returns:
        A dictionary containing token status, subject identifier (email), and authorization role.
    """
    return {"status": "valid", "sub": current_user.get("sub"), "role": current_user.get("role")}


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)


@router.post("/refresh")
@limiter.limit("5/minute")
async def refresh_access_token(request: Request, body: RefreshTokenRequest) -> JSONResponse:
    """
    Issue a new JWT access token using a valid, unexpired refresh token.

    Verifies refresh token signatures, audience, issuer, validates purpose constraints,
    and verifies that the token's JTI has not been blacklisted.

    Args:
        request: The FastAPI request instance.
        body: RefreshTokenRequest containing the raw refresh JWT string.

    Returns:
        JSONResponse with a new access JWT decorated as a secure browser cookie.

    Raises:
        HTTPException (401): If the refresh token has expired, is invalid, or has been revoked.
    """
    try:
        payload = jwt.decode(
            body.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=APP_JWT_AUDIENCE,
            issuer=APP_JWT_ISSUER,
        )
        if payload.get("purpose") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token purpose")
        jti = payload.get("jti")
        if jti:
            cache = getattr(request.app.state, 'cache', None)
            if await is_token_revoked(jti, cache):
                raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    new_token = create_access_token(
        data={"sub": payload["sub"], "name": payload.get("name", "")},
        role=payload.get("role", "user"),
    )
    return create_secure_cookie_response(
        content={"message": "Token refreshed successfully"},
        token=new_token,
    )


@router.post("/revoke")
@limiter.limit("10/minute")
async def revoke_access_token(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Revoke the current user's session token.

    Adds the token's JTI (JWT ID) to the blacklisted cache registry to immediately
    block any subsequent requests utilizing the token.

    Args:
        request: The FastAPI request instance.
        current_user: Current authenticated JWT payload.

    Returns:
        A dictionary confirming successful revocation.
    """
    jti = current_user.get("jti")
    if jti:
        cache = getattr(request.app.state, 'cache', None)
        await revoke_token(jti, cache)
    return {"message": "Token revoked successfully"}
