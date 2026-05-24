"""Email delivery (SMTP) with a dev-mode console fallback.

In development we usually don't have a real SMTP server configured, so to make
"sign up -> receive code" flow feel real, we *print* the email to the terminal
log in a panel that's hard to miss. As soon as `SMTP_HOST` is set, the same
service starts sending real email instead.

Usage::

    from app.core.email import send_email, send_otp_email

    send_otp_email(to="someone@example.com", code="123456", purpose="login")
"""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from app.core.config import settings

logger = logging.getLogger("app.email")
_console = Console(force_terminal=True, soft_wrap=True)


@dataclass(slots=True)
class EmailMessageSpec:
    to: str
    subject: str
    body_text: str
    body_html: str | None = None
    reply_to: str | None = None


def _smtp_configured() -> bool:
    return bool(getattr(settings, "SMTP_HOST", None))


def _send_via_smtp(msg: EmailMessageSpec) -> None:
    em = EmailMessage()
    em["From"] = settings.SMTP_FROM or settings.SMTP_USER or "no-reply@interviewer-ai.local"
    em["To"] = msg.to
    em["Subject"] = msg.subject
    if msg.reply_to:
        em["Reply-To"] = msg.reply_to
    em.set_content(msg.body_text)
    if msg.body_html:
        em.add_alternative(msg.body_html, subtype="html")

    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    use_ssl = port == 465
    timeout = 15

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=timeout) as s:
            _login_and_send(s, em)
    else:
        with smtplib.SMTP(host, port, timeout=timeout) as s:
            s.ehlo()
            if settings.SMTP_TLS:
                s.starttls()
                s.ehlo()
            _login_and_send(s, em)


def _login_and_send(s: smtplib.SMTP, em: EmailMessage) -> None:
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    s.send_message(em)


def _gmail_hint(exc: Exception) -> str | None:
    msg = str(exc).lower()
    if "application-specific password" in msg or "invalidsecondfactor" in msg:
        return (
            "Gmail rejected login: use an App Password, not your normal password. "
            "Google Account → Security → 2-Step Verification → App passwords."
        )
    if "username and password not accepted" in msg:
        return "SMTP login rejected: check SMTP_USER and SMTP_PASSWORD in .env."
    return None


def _print_to_console(
    msg: EmailMessageSpec,
    *,
    highlight: Iterable[str] = (),
    smtp_failed: bool = False,
    smtp_error: Exception | None = None,
) -> None:
    """Surface the email as a coloured panel in the terminal log."""
    body = Text(msg.body_text, style="white")
    for token in highlight:
        body.highlight_words([token], style="bold yellow on black")

    header = Text()
    header.append("To:      ", style="dim")
    header.append(f"{msg.to}\n", style="bold cyan")
    header.append("Subject: ", style="dim")
    header.append(msg.subject, style="bold")

    if smtp_failed and smtp_error:
        header.append("\n\n", style="dim")
        header.append("SMTP error: ", style="bold red")
        header.append(str(smtp_error), style="red")
        hint = _gmail_hint(smtp_error)
        if hint:
            header.append("\n\n", style="dim")
            header.append("Fix: ", style="bold yellow")
            header.append(hint, style="yellow")

    if smtp_failed:
        title = "[bold red]📧  EMAIL FAILED — OTP shown here only[/]"
        subtitle = "[dim]fix SMTP in .env, then restart make dev[/]"
        border = "red"
    else:
        title = "[bold yellow]📧  DEV EMAIL (SMTP not configured)[/]"
        subtitle = "[dim]set SMTP_HOST in .env to send real email[/]"
        border = "yellow"

    panel = Panel.fit(
        Text.assemble(header, "\n\n", body),
        title=title,
        subtitle=subtitle,
        border_style=border,
        padding=(1, 2),
    )
    _console.print()
    _console.print(panel)
    _console.print()


def send_email(msg: EmailMessageSpec, *, highlight: Iterable[str] = ()) -> bool:
    """Send `msg` via SMTP. Returns True if delivered, False if console fallback."""
    smtp_failed = False
    smtp_error: Exception | None = None

    if _smtp_configured():
        try:
            _send_via_smtp(msg)
            logger.info(
                "[green]EMAIL SENT[/]  to=%s  subject=%r  via=%s",
                msg.to,
                msg.subject,
                settings.SMTP_HOST,
            )
            return True
        except Exception as exc:
            smtp_failed = True
            smtp_error = exc
            logger.error(
                "[red bold]EMAIL SEND FAILED[/]  to=%s  via=%s  err=%s",
                msg.to,
                settings.SMTP_HOST,
                exc,
            )
            hint = _gmail_hint(exc)
            if hint:
                logger.error("[yellow]%s[/]", hint)

    _print_to_console(
        msg,
        highlight=highlight,
        smtp_failed=smtp_failed,
        smtp_error=smtp_error,
    )
    if smtp_failed:
        logger.warning(
            "[yellow]EMAIL → CONSOLE (SMTP failed)[/]  to=%s  — use the code "
            "in the panel above until SMTP is fixed",
            msg.to,
        )
    else:
        logger.info(
            "[yellow]EMAIL → CONSOLE[/]  to=%s  subject=%r  "
            "(set SMTP_HOST in .env to deliver via SMTP)",
            msg.to,
            msg.subject,
        )
    return False


# ────────────────────────────── templates ───────────────────────────────────


def send_otp_email(*, to: str, code: str, purpose: str, ttl_minutes: int) -> None:
    """Email a one-time code to the user.

    `purpose` is e.g. "login", "signup", "verify-email" – used only in the
    subject + body, no business logic depends on it.
    """
    subject = f"Your Interviewer AI {purpose} code: {code}"
    body_text = (
        f"Hi,\n\n"
        f"Your Interviewer AI {purpose} verification code is:\n\n"
        f"    {code}\n\n"
        f"This code expires in {ttl_minutes} minutes. "
        f"If you didn't request it, you can safely ignore this email.\n\n"
        f"– Interviewer AI"
    )
    body_html = f"""
    <div style="font-family: -apple-system, system-ui, sans-serif;
                max-width: 480px; margin: 0 auto; padding: 24px;">
      <h2>Interviewer AI</h2>
      <p>Hi,</p>
      <p>Your <b>{purpose}</b> verification code is:</p>
      <p style="font-size: 32px; letter-spacing: 6px; font-weight: bold;
                background:#f6f6f6; padding:16px; text-align:center;
                border-radius:8px; font-family: monospace;">{code}</p>
      <p style="color:#666;">This code expires in {ttl_minutes} minutes. If you
      didn't request it, you can ignore this email.</p>
    </div>
    """
    send_email(
        EmailMessageSpec(
            to=to,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        ),
        highlight=[code],
    )
