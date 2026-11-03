"""PB-2, PB-4: each boundary rule catches its violation and lets legitimate imports through."""

import grimp

from tests.architecture_rules import (
    Violation,
    cross_module_internal_imports,
    domain_framework_imports,
    forbidden_app_imports,
    shared_imports_module,
)


def _graph(*imports: tuple[str, str]) -> grimp.ImportGraph:
    graph = grimp.ImportGraph()
    for importer, imported in imports:
        for module in (importer, imported):
            if module not in graph.modules:
                graph.add_module(module)
        graph.add_import(importer=importer, imported=imported)
    return graph


def test_cross_module_import_of_internal_package_is_a_violation() -> None:
    graph = _graph(("app.modules.leave.service", "app.modules.balances.repository"))

    assert cross_module_internal_imports(graph) == [
        Violation(
            "cross-module-internal",
            "app.modules.leave.service",
            "app.modules.balances.repository",
        )
    ]


def test_cross_module_import_of_package_root_is_a_violation() -> None:
    graph = _graph(("app.modules.leave.service", "app.modules.balances"))

    assert len(cross_module_internal_imports(graph)) == 1


def test_cross_module_import_of_public_facade_is_allowed() -> None:
    graph = _graph(("app.modules.leave.service", "app.modules.balances.public"))

    assert cross_module_internal_imports(graph) == []


def test_import_within_the_same_module_is_allowed() -> None:
    graph = _graph(("app.modules.leave.service", "app.modules.leave.repository"))

    assert cross_module_internal_imports(graph) == []


def test_domain_importing_toolkit_or_storage_is_a_violation() -> None:
    graph = _graph(
        ("app.modules.planner.domain.rules", "PySide6.QtWidgets"),
        ("app.modules.planner.domain", "sqlite3"),
        ("app.modules.planner.domain.rules", "shutil"),
    )

    assert {v.imported for v in domain_framework_imports(graph)} == {
        "PySide6.QtWidgets",
        "sqlite3",
        "shutil",
    }


def test_non_domain_layer_may_import_toolkit_and_storage() -> None:
    graph = _graph(
        ("app.ui.main_window", "PySide6.QtWidgets"),
        ("app.modules.planner.repository", "sqlite3"),
    )

    assert domain_framework_imports(graph) == []


def test_domain_importing_standard_library_is_allowed() -> None:
    graph = _graph(("app.modules.planner.domain.rules", "decimal"))

    assert domain_framework_imports(graph) == []


def test_network_import_is_a_violation() -> None:
    """PB-4: nothing under app reaches the network — the product is offline by design."""
    graph = _graph(
        ("app.ui.main_window", "httpx"),
        ("app.shared.db", "socket"),
        ("app.modules.notes.service", "urllib.request"),
    )

    assert {v.imported for v in forbidden_app_imports(graph)} == {
        "httpx",
        "socket",
        "urllib.request",
    }


def test_orm_import_is_a_violation() -> None:
    graph = _graph(("app.modules.notes.repository", "sqlalchemy.orm"))

    assert forbidden_app_imports(graph) == [
        Violation("forbidden-package", "app.modules.notes.repository", "sqlalchemy.orm")
    ]


def test_forbidden_packages_outside_app_are_not_this_rules_business() -> None:
    """The tests themselves may use whatever they need; the ban is on the product code."""
    graph = _graph(("tests.ui.conftest", "socket"))

    assert forbidden_app_imports(graph) == []


def test_app_importing_standard_library_is_allowed() -> None:
    graph = _graph(("app.shared.db", "sqlite3"), ("app.ui.theme", "dataclasses"))

    assert forbidden_app_imports(graph) == []


def test_shared_importing_a_module_is_a_violation() -> None:
    graph = _graph(("app.shared.errors", "app.modules.leave.public"))

    assert shared_imports_module(graph) == [
        Violation("shared-imports-module", "app.shared.errors", "app.modules.leave.public")
    ]


def test_module_importing_shared_is_allowed() -> None:
    graph = _graph(("app.modules.leave.domain.rules", "app.shared.errors"))

    assert shared_imports_module(graph) == []
