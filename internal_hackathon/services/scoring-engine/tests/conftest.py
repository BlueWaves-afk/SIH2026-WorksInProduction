"""Pytest fixtures for the scoring acceptance suite."""
from __future__ import annotations

from datetime import datetime

import pytest

from scoring_test_builders import NOW


@pytest.fixture
def now() -> datetime:
    return NOW
