"""Fernet envelope encryption for contact values."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _fernet(key: str) -> Fernet:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(value: str, key: str) -> str:
    return "enc:v1:" + _fernet(key).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(value: str, key: str) -> str:
    if not value.startswith("enc:v1:"):
        raise ValueError("value is not an encrypted v1 envelope")
    try:
        return _fernet(key).decrypt(value.removeprefix("enc:v1:").encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("unable to decrypt value") from exc
