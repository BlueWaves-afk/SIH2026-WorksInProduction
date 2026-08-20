"""Dependency-injection registry for Mock/Real source implementations."""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from .interfaces import AdapterMode


class AdapterRegistry:
    def __init__(self):
        self._adapters: dict[str, Any] = {}

    def register(self, source: str, adapter: Any) -> None:
        key = source.strip().lower()
        if not key:
            raise ValueError("adapter source cannot be empty")
        self._adapters[key] = adapter

    def get(self, source: str) -> Any:
        key = source.strip().lower()
        try:
            return self._adapters[key]
        except KeyError as exc:
            raise KeyError(f"no adapter registered for {source!r}") from exc

    def sources(self) -> tuple[str, ...]:
        """Return registered source names for diagnostics and readiness checks."""
        return tuple(sorted(self._adapters))

    def configured_mode(
        self, source: str, environ: dict[str, str] | None = None
    ) -> AdapterMode:
        env = environ if environ is not None else os.environ
        raw = env.get(f"ADAPTER_MODE_{source.upper()}", AdapterMode.MOCK.value).lower()
        try:
            return AdapterMode(raw)
        except ValueError as exc:
            raise ValueError(f"invalid adapter mode for {source}: {raw!r}") from exc

    @classmethod
    def from_factories(
        cls,
        source: str,
        factories: dict[AdapterMode, Callable[[], Any]],
        environ: dict[str, str] | None = None,
    ) -> AdapterRegistry:
        registry = cls()
        mode = registry.configured_mode(source, environ)
        if mode not in factories:
            raise KeyError(f"no {mode.value} factory registered for {source}")
        registry.register(source, factories[mode]())
        return registry
