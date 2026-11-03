"""CB-4, CB-5: schema versions move forward, data survives, and an upgrade backs the file up.

Spec 0002 creates version 1, so there is no genuinely old file to migrate yet. The forward step
is proven with a synthetically produced older file, exactly as the spec states.
"""

import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.shared.db import Migration, backup_path, migrate, open_database, schema_version
from app.shared.errors import SchemaTooNewError, StorageError


def _create_people(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE people (name TEXT NOT NULL) STRICT")


def _add_nickname(connection: sqlite3.Connection) -> None:
    connection.execute("ALTER TABLE people ADD COLUMN nickname TEXT")


VERSION_1: Sequence[Migration] = (_create_people,)
VERSION_2: Sequence[Migration] = (_create_people, _add_nickname)


def _older_file(db_path: Path) -> sqlite3.Connection:
    """A file synthetically produced at version 1, with a row in it."""
    connection = open_database(db_path, migrations=VERSION_1)
    connection.execute("INSERT INTO people (name) VALUES ('Berk')")
    connection.commit()
    return connection


def test_synthetic_older_version_is_migrated_forward(db_path: Path) -> None:
    connection = _older_file(db_path)
    try:
        assert schema_version(connection) == 1

        assert migrate(connection, db_path, migrations=VERSION_2) == 2
        assert schema_version(connection) == 2
    finally:
        connection.close()


def test_data_survives_migration(db_path: Path) -> None:
    connection = _older_file(db_path)
    try:
        migrate(connection, db_path, migrations=VERSION_2)

        row = connection.execute("SELECT name, nickname FROM people").fetchone()
    finally:
        connection.close()

    assert row == ("Berk", None)


def test_applying_twice_is_idempotent(db_path: Path) -> None:
    connection = _older_file(db_path)
    try:
        migrate(connection, db_path, migrations=VERSION_2)

        assert migrate(connection, db_path, migrations=VERSION_2) == 2
        rows = connection.execute("SELECT name FROM people").fetchall()
    finally:
        connection.close()

    assert rows == [("Berk",)], "a second run must not re-apply migrations or duplicate data"


def test_backup_written_before_upgrading_existing_file(db_path: Path) -> None:
    connection = _older_file(db_path)
    try:
        migrate(connection, db_path, migrations=VERSION_2)
    finally:
        connection.close()

    backups = list(db_path.parent.glob("*.bak"))
    assert len(backups) == 1

    restored = sqlite3.connect(backups[0])
    try:
        # The backup is the pre-migration file: version 1, and without the new column.
        assert schema_version(restored) == 1
        assert restored.execute("SELECT name FROM people").fetchall() == [("Berk",)]
    finally:
        restored.close()


def test_backup_name_carries_source_version_and_date(db_path: Path) -> None:
    moment = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)

    connection = _older_file(db_path)
    try:
        migrate(connection, db_path, migrations=VERSION_2, now=moment)
    finally:
        connection.close()

    expected = backup_path(db_path, 1, moment)
    assert expected.name == f"{db_path.name}.v1.2026-11-03.bak"
    assert expected.exists()


def _explodes_after_its_ddl(connection: sqlite3.Connection) -> None:
    connection.execute("ALTER TABLE people ADD COLUMN nickname TEXT")
    raise RuntimeError("migration failed half-way")


def test_a_failed_step_leaves_the_file_as_it_was(db_path: Path) -> None:
    """Otherwise the next run re-applies the step onto a changed schema and can never open it."""
    connection = _older_file(db_path)
    try:
        with pytest.raises(RuntimeError):
            migrate(connection, db_path, migrations=(_create_people, _explodes_after_its_ddl))

        assert schema_version(connection) == 1
        columns = [row[1] for row in connection.execute("PRAGMA table_info(people)")]
        assert columns == ["name"], "the half-applied DDL must not survive the failure"
        assert connection.execute("SELECT name FROM people").fetchall() == [("Berk",)]
    finally:
        connection.close()


def test_the_file_can_still_be_migrated_after_a_failed_attempt(db_path: Path) -> None:
    connection = _older_file(db_path)
    try:
        with pytest.raises(RuntimeError):
            migrate(connection, db_path, migrations=(_create_people, _explodes_after_its_ddl))

        assert migrate(connection, db_path, migrations=VERSION_2) == 2
        row = connection.execute("SELECT name, nickname FROM people").fetchone()
    finally:
        connection.close()

    assert row == ("Berk", None), "a fixed build must be able to pick the file up again"


def test_a_file_from_a_newer_version_is_refused_and_left_alone(db_path: Path) -> None:
    """A file ahead of this build is a mismatch, and the user is told that, not "maybe corrupt"."""
    connection = open_database(db_path, migrations=VERSION_2)
    try:
        with pytest.raises(SchemaTooNewError) as caught:
            migrate(connection, db_path, migrations=VERSION_1)

        assert schema_version(connection) == 2, "a refusal must not move the file backwards"
    finally:
        connection.close()

    assert caught.value.detail != StorageError.detail, "not the generic 'maybe corrupt' text"
    assert list(db_path.parent.glob("*.bak")) == [], "nothing migrated, so nothing to back up"


def test_creating_a_new_file_takes_no_backup(db_path: Path) -> None:
    """R-2 (plan 0002): a file created right now has nothing to back up."""
    connection = open_database(db_path, migrations=VERSION_2)
    connection.close()

    assert list(db_path.parent.glob("*.bak")) == []
