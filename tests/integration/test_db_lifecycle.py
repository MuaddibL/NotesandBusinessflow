"""CB-3: the data file is created on first run and reused afterwards."""

from pathlib import Path

import pytest

from app.shared.db import MIGRATIONS, open_database, schema_version
from app.shared.errors import StorageError


def test_first_run_creates_database(db_path: Path) -> None:
    assert not db_path.exists()

    connection = open_database(db_path)
    try:
        assert db_path.exists()
        assert schema_version(connection) == len(MIGRATIONS)
    finally:
        connection.close()


def test_second_run_reuses_existing_file(db_path: Path) -> None:
    first = open_database(db_path)
    try:
        first.execute("INSERT INTO app_meta (key, value) VALUES ('marker', 'kept')")
        first.commit()
    finally:
        first.close()

    second = open_database(db_path)
    try:
        row = second.execute("SELECT value FROM app_meta WHERE key = 'marker'").fetchone()
    finally:
        second.close()

    assert row == ("kept",), "an existing file must be reused, never recreated"


def test_unopenable_file_raises_storage_error_without_leaking_the_path(db_path: Path) -> None:
    """CB-6's failure path: a directory where the database file should be cannot be opened."""
    db_path.parent.mkdir(parents=True)
    db_path.mkdir()

    with pytest.raises(StorageError) as caught:
        open_database(db_path)

    assert str(db_path) not in str(caught.value.detail)
