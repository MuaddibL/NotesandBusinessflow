"""PB-2, PB-4: the real application package respects every boundary rule."""

from tests.architecture_rules import (
    APP_FORBIDDEN_PACKAGES,
    all_violations,
    build_app_graph,
    forbidden_app_imports,
)


def test_app_has_no_boundary_violations() -> None:
    assert all_violations(build_app_graph()) == []


def test_app_imports_no_network_package() -> None:
    """The ban proven on the real import graph, not only on synthetic ones (plan 0002, R-5)."""
    assert forbidden_app_imports(build_app_graph()) == []
    assert "httpx" in APP_FORBIDDEN_PACKAGES, "the set must actually name the network stack"
