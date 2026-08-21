"""Officer/district email provider.

Email is an **officer** channel only — never a farmer alert channel (see the
Module 9 design: farmers overwhelmingly do not hold or check email, so routing
life-relevant alerts there is indistinguishable from not sending them).  This
module powers district/officer digests.

Two backends:
- ``smtp``: real delivery via ``smtplib`` when SMTP settings are present.
- ``mock``: structured-log delivery used in local/demo mode so the digest job
  is always operational and every send is observable without credentials.
"""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

import structlog

from app.core.config import Settings, settings as default_settings

logger = structlog.get_logger()


class EmailProviderError(RuntimeError):
    """A send failure that is safe to surface to callers/audit."""


@dataclass
class EmailResult:
    provider: str
    accepted: list[str]
    message_id: str | None = None


class BaseEmailProvider:
    provider = "base"

    @property
    def configured(self) -> bool:  # pragma: no cover - overridden
        return False

    def send(self, *, to: list[str], subject: str, text: str, html: str | None = None) -> EmailResult:  # pragma: no cover
        raise NotImplementedError


class MockEmailProvider(BaseEmailProvider):
    """Logs the message instead of sending. Always 'configured' so the digest
    job runs end to end in demo mode."""

    provider = "mock"

    @property
    def configured(self) -> bool:
        return True

    def send(self, *, to: list[str], subject: str, text: str, html: str | None = None) -> EmailResult:
        recipients = [address for address in to if address]
        if not recipients:
            raise EmailProviderError("no recipients")
        logger.info(
            "email_mock_dispatch",
            provider=self.provider,
            to=recipients,
            subject=subject,
            body_chars=len(text),
            html=html is not None,
        )
        return EmailResult(provider=self.provider, accepted=recipients, message_id="mock-email")


class SmtpEmailProvider(BaseEmailProvider):
    provider = "smtp"

    def __init__(self, cfg: Settings):
        self._cfg = cfg

    @property
    def configured(self) -> bool:
        return bool(self._cfg.smtp_host)

    def send(self, *, to: list[str], subject: str, text: str, html: str | None = None) -> EmailResult:
        recipients = [address for address in to if address]
        if not recipients:
            raise EmailProviderError("no recipients")
        if not self.configured:
            raise EmailProviderError("SMTP host is not configured")

        message = EmailMessage()
        message["From"] = f"{self._cfg.email_from_name} <{self._cfg.email_from_address}>"
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(text)
        if html:
            message.add_alternative(html, subtype="html")

        try:
            with smtplib.SMTP(self._cfg.smtp_host or "", self._cfg.smtp_port, timeout=15) as client:
                if self._cfg.smtp_use_tls:
                    client.starttls(context=ssl.create_default_context())
                if self._cfg.smtp_username and self._cfg.smtp_password:
                    client.login(self._cfg.smtp_username, self._cfg.smtp_password)
                client.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise EmailProviderError(f"SMTP send failed: {exc}") from exc

        logger.info("email_smtp_dispatch", provider=self.provider, to=recipients, subject=subject)
        return EmailResult(provider=self.provider, accepted=recipients)


def build_email_provider(cfg: Settings | None = None) -> BaseEmailProvider:
    cfg = cfg or default_settings
    provider = (cfg.email_provider or "mock").lower()
    if provider in {"smtp", "email", "real"}:
        return SmtpEmailProvider(cfg)
    return MockEmailProvider()
