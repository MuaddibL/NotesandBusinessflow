"""UI tests: offscreen by default, and never able to slip into the fast profile.

pytest-qt is the single owner of the ``QApplication`` lifecycle (docs/testing.md, Resource
hygiene rule 4): it creates it for the run and tears it down at the end, failures included.
"""

import os
from pathlib import Path

import pytest

UI_DIR = Path(__file__).parent

# check.conf sets this for the verification contract; setting it here too keeps a direct
# `pytest` run from opening windows on someone's desktop. Must happen before the QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # Every test under tests/ui is a ui test: a new one cannot slip into the fast profile.
    for item in items:
        if UI_DIR in item.path.parents:
            item.add_marker(pytest.mark.ui)
