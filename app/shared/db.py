"""SQLite access and forward-only schema migrations (docs/conventions.md, Data rules).

The schema version lives in ``PRAGMA user_version``: migration *n* in ``MIGRATIONS`` takes the
file from version ``n-1`` to ``n``, so the list index is the version. An existing file is backed
up before it is upgraded (spec 0002/CB-5); a file created right now has nothing to back up
(plan 0002, R-2).
"""

import shutil
import sqlite3
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from app.shared.errors import SchemaTooNewError, StorageError

Migration = Callable[[sqlite3.Connection], None]


def _migration_01_app_meta(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT")
    connection.execute(
        "INSERT INTO app_meta (key, value) VALUES (?, ?)",
        ("created_at", datetime.now(UTC).isoformat()),
    )


MIGRATIONS: tuple[Migration, ...] = (_migration_01_app_meta,)


def schema_version(connection: sqlite3.Connection) -> int:
    row: tuple[int] = connection.execute("PRAGMA user_version").fetchone()
    return row[0]


def _set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    # PRAGMA takes no bound parameters, so the value is interpolated. It is never user input:
    # it is this module's own migration index, coerced to int (docs/security.md, Input & output).
    connection.execute(f"PRAGMA user_version = {int(version)}")


def backup_path(path: Path, from_version: int, now: datetime) -> Path:
    """Backup next to the database, naming the version it came from and the day (CB-5)."""
    return path.with_name(f"{path.name}.v{from_version}.{now.date().isoformat()}.bak")


def migrate(
    connection: sqlite3.Connection,
    path: Path,
    *,
    migrations: Sequence[Migration] = MIGRATIONS,
    now: datetime | None = None,
) -> int:
    """Brings the file up to the latest version and returns it. Idempotent (CB-4)."""
    current = schema_version(connection)
    target = len(migrations)
    if current == target:
        return current
    if current > target:
        # The dialog reads the class attributes, never Exception.args, so the reason has to be
        # the type rather than a message (review 0002/F-7).
        raise SchemaTooNewError
    if current > 0:
        shutil.copy2(path, backup_path(path, current, now or datetime.now(UTC)))
    for index in range(current, target):
        # One explicit transaction per step. sqlite3 only opens implicit transactions for DML, so
        # without BEGIN a CREATE TABLE or an ALTER TABLE commits on its own: a step that failed
        # after its DDL left the schema changed while user_version still pointed at the old
        # version, and the next run re-applied the same migration onto it and could never open
        # the file again (review 0002/F-3). Per step rather than per run, so a long upgrade does
        # not hold a write lock over every migration at once.
        connection.execute("BEGIN")
        try:
            migrations[index](connection)
            _set_schema_version(connection, index + 1)
        except BaseException:
            connection.rollback()
            raise
        connection.commit()
    return target


def open_database(
    path: Path,
    *,
    migrations: Sequence[Migration] = MIGRATIONS,
    now: datetime | None = None,
) -> sqlite3.Connection:
    """Opens (creating it on first run) and migrates the database at ``path`` (CB-3, CB-4)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
    except (sqlite3.Error, OSError) as error:
        # sqlite3 reports an unopenable file as OperationalError, not OSError — both are failures
        # to open. The path and the exception text stay inside the cause; neither reaches the user.
        raise StorageError from error
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        migrate(connection, path, migrations=migrations, now=now)
    except (sqlite3.Error, OSError) as error:
        connection.close()
        raise StorageError from error
    except BaseException:
        connection.close()
        raise
    return connection
