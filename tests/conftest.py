"""Pytest configuration and fixtures."""
from pathlib import Path

import pytest


@pytest.fixture
def data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"
