"""
Module:        tests/conftest.py
Description:   Shared pytest fixtures: logging cleanup and auth environment isolation.
Version:       1.0.0
Created:       2026-11-10
Last updated:  2026-11-11T15:20:00-05:00
"""

import pytest

from drive_search.logging_setup import shutdown_logging

__version__ = "1.0.0"


@pytest.fixture(autouse=True)
def _reset_logging():
    """Close our log handlers after every test (avoids Windows file locks)."""
    yield
    shutdown_logging()


@pytest.fixture(autouse=True)
def _isolate_auth_env(monkeypatch):
    """Tests must never pick up real credential paths from the environment."""
    monkeypatch.delenv("GDRIVE_CREDENTIALS", raising=False)
    monkeypatch.delenv("GDRIVE_TOKEN", raising=False)
