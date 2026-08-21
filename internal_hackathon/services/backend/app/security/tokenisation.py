"""Opaque farmer tokens and encrypted contact values."""

from __future__ import annotations

import base64
import hashlib
import uuid

from app.core.config import settings


def new_farmer_token() -> str:
    return f"farmer_{uuid.uuid4().hex}"


def _fernet():
    if not settings.vault_encryption_key:
        return None
    from cryptography.fernet import Fernet

    digest = hashlib.sha256(settings.vault_encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    fernet = _fernet()
    if fernet is None:
        # Local fixture mode never stores a recoverable phone number.
        digest = hashlib.sha256(phone.encode("utf-8")).hexdigest()
        return f"hash:v1:{digest}"
    return "enc:v1:" + fernet.encrypt(phone.encode("utf-8")).decode("ascii")


def decrypt_phone(value: str | None) -> str | None:
    if not value or not value.startswith("enc:v1:"):
        return None
    fernet = _fernet()
    if fernet is None:
        return None
    try:
        return fernet.decrypt(value.removeprefix("enc:v1:").encode("ascii")).decode("utf-8")
    except Exception:
        return None


# Email is contact PII and follows the same vault path as the phone number, so
# a farmer who opts into email alerts is protected by the same encryption.
def encrypt_email(email: str | None) -> str | None:
    return encrypt_phone(email)


def decrypt_email(value: str | None) -> str | None:
    return decrypt_phone(value)
