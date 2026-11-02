"""Where the application keeps its data (docs/security.md, Veri ve gizlilik)."""

from collections.abc import Mapping
from pathlib import Path

APP_DIR_NAME = "Notes-MJ"
DATABASE_FILE_NAME = "notes-mj.sqlite3"


def data_dir(env: Mapping[str, str], home: Path) -> Path:
    """The per-user application data directory.

    Windows is the target platform (%LOCALAPPDATA%); the other branches keep the tests and CI
    honest on Linux. ``env`` and ``home`` are parameters, not reads, so this stays testable.
    """
    local_app_data = env.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_DIR_NAME
    xdg_data_home = env.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / APP_DIR_NAME
    return home / ".local" / "share" / APP_DIR_NAME


def database_path(env: Mapping[str, str], home: Path) -> Path:
    return data_dir(env, home) / DATABASE_FILE_NAME
