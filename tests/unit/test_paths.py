"""CB-3's other half: *where* the data lives (`docs/security.md`, Veri ve gizlilik).

The rest of the suite passes its own `tmp_path` in, so nothing held these functions to the
location the security rules name — a build that wrote the database into the working directory
kept every other test green (review 0002/V-1).
"""

from pathlib import Path

from app.shared.paths import (
    APP_DIR_NAME,
    DATABASE_FILE_NAME,
    LOG_FILE_NAME,
    data_dir,
    database_path,
    log_path,
)

HOME = Path("/home/berk")


def test_windows_data_dir_is_under_local_app_data() -> None:
    """The target platform: %LOCALAPPDATA%\\Notes-MJ (docs/security.md)."""
    assert (
        data_dir({"LOCALAPPDATA": r"C:\Users\berk\AppData\Local"}, HOME)
        == Path(r"C:\Users\berk\AppData\Local") / APP_DIR_NAME
    )


def test_local_app_data_wins_over_xdg() -> None:
    env = {"LOCALAPPDATA": r"C:\local", "XDG_DATA_HOME": "/xdg"}

    assert data_dir(env, HOME) == Path(r"C:\local") / APP_DIR_NAME


def test_xdg_data_home_is_used_when_there_is_no_local_app_data() -> None:
    assert data_dir({"XDG_DATA_HOME": "/xdg"}, HOME) == Path("/xdg") / APP_DIR_NAME


def test_without_either_variable_the_directory_is_under_home() -> None:
    assert data_dir({}, HOME) == HOME / ".local" / "share" / APP_DIR_NAME


def test_an_empty_variable_is_not_a_location() -> None:
    """An empty LOCALAPPDATA would otherwise put the data in a directory named Notes-MJ."""
    assert data_dir({"LOCALAPPDATA": "", "XDG_DATA_HOME": ""}, HOME) == (
        HOME / ".local" / "share" / APP_DIR_NAME
    )


def test_the_data_directory_is_never_the_working_directory() -> None:
    """The regression this file exists for: the user's data never lands next to the code.

    Stated structurally — the file hangs off the root the caller configured — rather than through
    `resolve()` or `is_absolute()`. Both of those answer differently on Windows and on Linux for
    the very strings this function is given, and the suite runs on both.
    """
    roots = (
        ({"LOCALAPPDATA": r"C:\local"}, Path(r"C:\local")),
        ({"XDG_DATA_HOME": "/xdg"}, Path("/xdg")),
        ({}, HOME / ".local" / "share"),
    )
    for env, root in roots:
        for path in (database_path(env, HOME), log_path(env, HOME)):
            assert path.parent == root / APP_DIR_NAME
            assert path.parent != Path()


def test_the_database_and_the_log_sit_next_to_each_other() -> None:
    env = {"LOCALAPPDATA": r"C:\local"}

    assert database_path(env, HOME).name == DATABASE_FILE_NAME
    assert log_path(env, HOME).name == LOG_FILE_NAME
    assert database_path(env, HOME).parent == log_path(env, HOME).parent == data_dir(env, HOME)
