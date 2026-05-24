"""Signup, login, OTP (email-delivered code, with TOTP as an alternative).

Flows
-----

* **Signup**     `POST /auth/signup`      → 200 `TokenResponse`
* **Login (no OTP)**            `POST /auth/login` with `email`+`password`
                                → 200 `TokenResponse`
* **Login (OTP-enabled, step 1)** `POST /auth/login` with `email`+`password`
                                → 202 `OtpChallengeResponse` *and* a code is
                                emailed (or, in dev with no SMTP, printed in
                                the API terminal panel).
* **Login (OTP-enabled, step 2)** `POST /auth/login` with `email`+`password`
                                +`otp_code`  → 200 `TokenResponse`.
* **Resend code**  `POST /auth/otp/request` (unauthenticated, email-only)
* **Enrol OTP**    `POST /auth/otp/enrol`   (authenticated)
* **Verify code**  `POST /auth/otp/verify`  (authenticated; finalises enrol)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_db
from app.core.email import send_otp_email
from app.core.security import (
    create_access_token,
    generate_email_otp,
    generate_otp_secret,
    hash_otp,
    hash_password,
    verify_otp_hash,
    verify_password,
    verify_totp,
)
from app.helpers.api_error import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)
from app.middlewares.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    OtpChallengeResponse,
    OtpEnrolResponse,
    OtpRequestPayload,
    OtpVerifyRequest,
    SignupRequest,
    TokenResponse,
)

logger = logging.getLogger("app.auth")
router = APIRouter()

_MAX_OTP_ATTEMPTS = 5


# ────────────────────────── small helpers ───────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _mask_email(email: str) -> str:
    name, _, domain = email.partition("@")
    if not domain:
        return "***"
    visible = name[:2]
    return f"{visible}{'*' * max(1, len(name) - 2)}@{domain}"


def _issue_email_otp(user: User, db: Session, *, purpose: str) -> int:
    """Generate a code, store its hash + expiry on the user, email it, commit.

    Returns the TTL in seconds so callers can include it in the response.
    """
    code = generate_email_otp(settings.OTP_LENGTH)
    user.otp_code_hash = hash_otp(code)
    user.otp_code_expires_at = _utc_now() + timedelta(seconds=settings.OTP_TTL_SECONDS)
    user.otp_attempts = 0
    db.add(user)
    db.commit()

    send_otp_email(
        to=user.email,
        code=code,
        purpose=purpose,
        ttl_minutes=max(1, settings.OTP_TTL_SECONDS // 60),
    )
    logger.info(
        "OTP issued  user_id=%s  email=%s  purpose=%s  ttl=%ds",
        user.id,
        _mask_email(user.email),
        purpose,
        settings.OTP_TTL_SECONDS,
    )
    return settings.OTP_TTL_SECONDS


def _consume_email_otp(user: User, code: str, db: Session) -> bool:
    """Verify a code against the stored hash. Single-use: clears on success."""
    if not user.otp_code_hash or not user.otp_code_expires_at:
        return False
    if user.otp_attempts >= _MAX_OTP_ATTEMPTS:
        return False
    if _utc_now() > user.otp_code_expires_at:
        return False

    if not verify_otp_hash(code, user.otp_code_hash):
        user.otp_attempts += 1
        db.add(user)
        db.commit()
        return False

    user.otp_code_hash = None
    user.otp_code_expires_at = None
    user.otp_attempts = 0
    db.add(user)
    db.commit()
    return True


# ───────────────────────────── endpoints ────────────────────────────────────


@router.post("/signup", response_model=TokenResponse, status_code=200)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise ConflictError("Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), extra_claims={"role": user.role.value})
    logger.info("Signup  user_id=%s  email=%s", user.id, _mask_email(user.email))
    return TokenResponse(access_token=token, user_id=user.id, role=user.role)


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")
    if not user.is_active:
        raise UnauthorizedError("Account disabled")

    # No OTP enabled → straight to token.
    if not user.otp_enabled:
        token = create_access_token(
            str(user.id), extra_claims={"role": user.role.value}
        )
        return TokenResponse(access_token=token, user_id=user.id, role=user.role)

    # OTP enabled but no code provided → issue a challenge.
    if not payload.otp_code:
        if settings.OTP_MODE == "totp":
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=OtpChallengeResponse(
                    delivery="totp",
                    sent_to=None,
                    expires_in_seconds=30,
                    message=(
                        "Open your authenticator app and resubmit with the "
                        "6-digit code in `otp_code`."
                    ),
                ).model_dump(),
            )
        ttl = _issue_email_otp(user, db, purpose="login")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=OtpChallengeResponse(
                delivery="email",
                sent_to=_mask_email(user.email),
                expires_in_seconds=ttl,
            ).model_dump(),
        )

    # Step 2: code submitted.
    if settings.OTP_MODE == "totp":
        if not verify_totp(user.otp_secret or "", payload.otp_code):
            raise UnauthorizedError("Invalid OTP code")
    else:
        if not _consume_email_otp(user, payload.otp_code, db):
            raise UnauthorizedError("Invalid or expired OTP code")

    token = create_access_token(str(user.id), extra_claims={"role": user.role.value})
    return TokenResponse(access_token=token, user_id=user.id, role=user.role)


@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
def otp_request(payload: OtpRequestPayload, db: Session = Depends(get_db)):
    """Resend (or initially send) the login email-OTP for a known account.

    We always respond 202 even when the email is unknown, to avoid leaking
    account existence via timing / status codes.
    """
    if settings.OTP_MODE != "email":
        raise BadRequestError(
            "OTP_MODE is not 'email'; use /auth/otp/enrol with an authenticator app."
        )

    user = db.exec(select(User).where(User.email == payload.email)).first()
    if user and user.is_active:
        ttl = _issue_email_otp(user, db, purpose="login")
        return OtpChallengeResponse(
            delivery="email",
            sent_to=_mask_email(user.email),
            expires_in_seconds=ttl,
        ).model_dump()
    return OtpChallengeResponse(
        delivery="email",
        sent_to=_mask_email(payload.email),
        expires_in_seconds=settings.OTP_TTL_SECONDS,
        message="If the email is registered, a code has been sent.",
    ).model_dump()


@router.post("/otp/enrol", response_model=OtpEnrolResponse)
def otp_enrol(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OtpEnrolResponse:
    """Begin OTP enrolment for the authenticated user.

    - email mode: emails a one-time code; user calls /auth/otp/verify with it.
    - totp  mode: returns a TOTP secret + otpauth:// URI to add to an
                  authenticator app; user then calls /auth/otp/verify.
    """
    if settings.OTP_MODE == "totp":
        secret = generate_otp_secret()
        user.otp_secret = secret
        db.add(user)
        db.commit()

        import pyotp

        uri = pyotp.TOTP(secret).provisioning_uri(
            name=user.email, issuer_name="Interviewer AI"
        )
        return OtpEnrolResponse(
            mode="totp",
            expires_in_seconds=30,
            secret=secret,
            otpauth_uri=uri,
            message=(
                "Add this secret (or scan the otpauth URI) in your authenticator "
                "app, then POST the 6-digit code to /auth/otp/verify."
            ),
        )

    # email mode (default)
    ttl = _issue_email_otp(user, db, purpose="enrol")
    return OtpEnrolResponse(
        mode="email",
        expires_in_seconds=ttl,
        sent_to=_mask_email(user.email),
        message=(
            "A 6-digit code was emailed to you. POST it to /auth/otp/verify "
            "to finish enrolling."
        ),
    )


@router.post("/otp/verify")
def otp_verify(
    payload: OtpVerifyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Confirm an OTP code – finalises enrolment by setting `otp_enabled=True`."""
    if settings.OTP_MODE == "totp":
        if not user.otp_secret:
            raise BadRequestError("OTP not enrolled; call /auth/otp/enrol first")
        if not verify_totp(user.otp_secret, payload.code):
            raise UnauthorizedError("Invalid code")
    else:
        if not _consume_email_otp(user, payload.code, db):
            raise UnauthorizedError("Invalid or expired code")
        user.email_verified = True

    user.otp_enabled = True
    db.add(user)
    db.commit()
    logger.info(
        "OTP enrolled  user_id=%s  email=%s  mode=%s",
        user.id,
        _mask_email(user.email),
        settings.OTP_MODE,
    )
    return {"otp_enabled": True, "mode": settings.OTP_MODE}
