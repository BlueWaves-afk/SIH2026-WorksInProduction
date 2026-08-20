"""Data-principal rights are expressed as repository callbacks."""

from collections.abc import Callable
from typing import Any


def export_my_data(farmer_token: str, exporter: Callable[[str], dict[str, Any]]) -> dict[str, Any]:
    return exporter(farmer_token)


def delete_my_data(farmer_token: str, deleter: Callable[[str], None]) -> None:
    deleter(farmer_token)
