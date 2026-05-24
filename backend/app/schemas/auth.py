"""Pydantic schemas for auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None
    role: UserRole = UserRole.candidate


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    otp_code: str | None = None  # required only when account has OTP enabled


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole


class OtpChallengeResponse(BaseModel):
    """Returned by /auth/login when the account requires an OTP step."""

    otp_required: bool = True
    delivery: str  # "email" or "totp"
    sent_to: str | None = None  # e.g. masked email "as***@example.com"
    expires_in_seconds: int
    message: str = (
        "A one-time code has been sent. Submit it via POST /auth/login again "
        "with `otp_code`, or POST /auth/otp/verify."
    )


class OtpRequestPayload(BaseModel):
    """Used by /auth/otp/request to (re)send an email code."""

    email: EmailStr


class OtpVerifyRequest(BaseModel):
    code: str = Field(min_length=4, max_length=10)
    email: EmailStr | None = None  # only required for the unauthenticated path


class OtpEnrolResponse(BaseModel):
    """Returned from /auth/otp/enrol.

    - email mode: the code has been emailed; `secret`/`otpauth_uri` are None.
    - totp  mode: returns the TOTP secret + otpauth:// URI to scan.
    """

    mode: str
    expires_in_seconds: int
    sent_to: str | None = None
    secret: str | None = None
    otpauth_uri: str | None = None
    message: str
