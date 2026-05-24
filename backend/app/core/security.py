"""Auth primitives: JWT, password hashing, TOTP-based 2FA."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
import pyotp

from app.core.config import settings

# bcrypt's input limit is 72 bytes; longer inputs are silently truncated.
_BCRYPT_MAX_BYTES = 72


def _coerce(password: str) -> bytes:
    raw = password.encode("utf-8")
    return raw[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_coerce(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_coerce(password), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: str,
    *,
    extra_claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = now + timedelta(minutes=minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"require": ["exp", "sub"]},
    )


def generate_otp_secret() -> str:
    return pyotp.random_base32()


def get_totp(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret)


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    try:
        return get_totp(secret).verify(code, valid_window=1)
    except Exception:
        return False


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


# ── Email OTP (server-emailed numeric codes) ────────────────────────────────


def generate_email_otp(length: int | None = None) -> str:
    """Cryptographically random numeric code of `length` digits (default 6)."""
    n = length or settings.OTP_LENGTH
    return "".join(secrets.choice("0123456789") for _ in range(n))


def hash_otp(code: str) -> str:
    """Hash an OTP code with bcrypt for at-rest storage."""
    return bcrypt.hashpw(_coerce(code), bcrypt.gensalt()).decode("utf-8")


def verify_otp_hash(code: str, code_hash: str) -> bool:
    if not code or not code_hash:
        return False
    try:
        return bcrypt.checkpw(_coerce(code), code_hash.encode("utf-8"))
    except Exception:
        return False
