"""Integration tests own a database file of their own: one temporary file per test."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.shared.paths import DATABASE_FILE_NAME


@pytest.fixture
def db_path(tmp_path: Path) -> Iterator[Path]:
    # Under a subdirectory that does not exist yet: creating it is part of what CB-3 promises.
    yield tmp_path / "data" / DATABASE_FILE_NAME
