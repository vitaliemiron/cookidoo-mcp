"""Verify that every release-facing file declares the same version."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def declared_versions() -> dict[str, str]:
    """Return version declarations that must move together for a release."""

    with (ROOT / "pyproject.toml").open("rb") as handle:
        project_version = tomllib.load(handle)["project"]["version"]

    registry = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    fastmcp = json.loads((ROOT / "fastmcp.json").read_text(encoding="utf-8"))

    version_module = ast.parse(
        (ROOT / "cookidoo_mcp" / "__init__.py").read_text(encoding="utf-8")
    )
    package_version = next(
        ast.literal_eval(statement.value)
        for statement in version_module.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        )
    )

    return {
        "pyproject.toml": project_version,
        "cookidoo_mcp/__init__.py": package_version,
        "fastmcp.json": fastmcp["version"],
        "server.json": registry["version"],
        "server.json package": registry["packages"][0]["version"],
    }


def check(expected: str | None = None) -> None:
    """Raise when declared versions disagree or differ from *expected*."""

    versions = declared_versions()
    unique_versions = set(versions.values())
    if len(unique_versions) != 1:
        details = ", ".join(
            f"{source}={version}" for source, version in versions.items()
        )
        raise ValueError(f"Release versions do not match: {details}")

    declared = unique_versions.pop()
    if expected is not None and declared != expected:
        raise ValueError(
            f"Release metadata is {declared}, but the tag requests {expected}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "expected",
        nargs="?",
        help="Expected version, normally the release tag without its leading v.",
    )
    args = parser.parse_args()
    check(args.expected)


if __name__ == "__main__":
    main()
