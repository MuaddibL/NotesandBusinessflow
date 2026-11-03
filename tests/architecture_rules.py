"""Module boundary rules (docs/architecture.md, Forbidden dependencies 1-3 and 5) on a grimp graph.

Rules are generic over ``app.modules.<name>`` so a new module is covered without configuration.
"""

from dataclasses import dataclass

import grimp

APP_PACKAGE = "app"
MODULES_PACKAGE = "app.modules"
SHARED_PACKAGE = "app.shared"

# Rule 2: the domain layer is pure Python — no toolkit, no storage, no IO.
DOMAIN_FORBIDDEN_PACKAGES = frozenset({"PySide6", "shiboken6", "sqlite3", "pathlib", "shutil"})

# Rule 5: the product never reaches the network, and uses no ORM (docs/architecture.md).
APP_FORBIDDEN_PACKAGES = frozenset(
    {
        "fastapi",
        "uvicorn",
        "starlette",
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "urllib3",
        "http",
        "socket",
        "socketserver",
        "ftplib",
        "smtplib",
        "xmlrpc",
        "webbrowser",
        "sqlalchemy",
    }
)


@dataclass(frozen=True)
class Violation:
    rule: str
    importer: str
    imported: str


def build_app_graph() -> grimp.ImportGraph:
    # cache_dir=None: never write a grimp cache into the working tree.
    return grimp.build_graph("app", include_external_packages=True, cache_dir=None)


def _module_of(name: str) -> str | None:
    """``app.modules.leave.domain.x`` -> ``leave``; None outside ``app.modules.<name>``."""
    parts = name.split(".")
    if len(parts) >= 3 and ".".join(parts[:2]) == MODULES_PACKAGE:
        return parts[2]
    return None


def _is_within(name: str, package: str) -> bool:
    return name == package or name.startswith(package + ".")


def _imports(graph: grimp.ImportGraph) -> list[tuple[str, str]]:
    return sorted(
        (importer, imported)
        for importer in graph.modules
        for imported in graph.find_modules_directly_imported_by(importer)
    )


def cross_module_internal_imports(graph: grimp.ImportGraph) -> list[Violation]:
    """Rule 1: a module imports another module only through its ``public`` facade."""
    violations = []
    for importer, imported in _imports(graph):
        source, target = _module_of(importer), _module_of(imported)
        if source is None or target is None or source == target:
            continue
        if imported != f"{MODULES_PACKAGE}.{target}.public":
            violations.append(Violation("cross-module-internal", importer, imported))
    return violations


def domain_framework_imports(graph: grimp.ImportGraph) -> list[Violation]:
    """Rule 2: ``app.modules.*.domain`` never imports the UI toolkit, storage or IO packages."""
    violations = []
    for importer, imported in _imports(graph):
        module = _module_of(importer)
        if module is None or not _is_within(importer, f"{MODULES_PACKAGE}.{module}.domain"):
            continue
        if imported.split(".")[0] in DOMAIN_FORBIDDEN_PACKAGES:
            violations.append(Violation("domain-framework", importer, imported))
    return violations


def forbidden_app_imports(graph: grimp.ImportGraph) -> list[Violation]:
    """Rule 5: no part of ``app`` imports the network stack or an ORM."""
    return [
        Violation("forbidden-package", importer, imported)
        for importer, imported in _imports(graph)
        if _is_within(importer, APP_PACKAGE) and imported.split(".")[0] in APP_FORBIDDEN_PACKAGES
    ]


def shared_imports_module(graph: grimp.ImportGraph) -> list[Violation]:
    """Rule 3: ``app.shared`` never imports any ``app.modules`` package."""
    return [
        Violation("shared-imports-module", importer, imported)
        for importer, imported in _imports(graph)
        if _is_within(importer, SHARED_PACKAGE) and _is_within(imported, MODULES_PACKAGE)
    ]


def all_violations(graph: grimp.ImportGraph) -> list[Violation]:
    return (
        cross_module_internal_imports(graph)
        + domain_framework_imports(graph)
        + shared_imports_module(graph)
        + forbidden_app_imports(graph)
    )
