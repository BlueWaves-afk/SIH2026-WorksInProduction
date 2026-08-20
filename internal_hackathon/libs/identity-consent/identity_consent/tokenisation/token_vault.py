"""Opaque farmer-token vault; callers never use phone numbers as identifiers."""

from __future__ import annotations

import uuid

from .encryption import decrypt, encrypt


class TokenVault:
    def __init__(self, encryption_key: str):
        if not encryption_key:
            raise ValueError("encryption key is required")
        self._key = encryption_key
        self._values: dict[str, str] = {}

    def mint(self, phone: str | None = None) -> str:
        token = f"farmer_{uuid.uuid4().hex}"
        if phone:
            self._values[token] = encrypt(phone, self._key)
        return token

    def put(self, token: str, phone: str) -> None:
        self._values[token] = encrypt(phone, self._key)

    def resolve(self, token: str) -> str | None:
        value = self._values.get(token)
        return decrypt(value, self._key) if value else None

    def revoke(self, token: str) -> None:
        self._values.pop(token, None)


def mint_farmer_token() -> str:
    return f"farmer_{uuid.uuid4().hex}"
