"""Shared pytest fixtures."""
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SCHEMA_PATH = Path(__file__).parents[3] / "schema" / "control.schema.json"


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture
def schema_path() -> Path:
    return SCHEMA_PATH
