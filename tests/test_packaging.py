import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from cookidoo_mcp import __version__
from cookidoo_mcp.cli import main
from scripts.check_release_metadata import check, declared_versions

ROOT = Path(__file__).resolve().parents[1]


def test_release_versions_stay_in_sync() -> None:
    assert set(declared_versions().values()) == {__version__}
    check(__version__)


def test_release_version_check_rejects_wrong_tag() -> None:
    with pytest.raises(ValueError, match="tag requests 2.0.0"):
        check("2.0.0")


def fake_server(monkeypatch) -> SimpleNamespace:
    run = SimpleNamespace(called=False)
    run.run = lambda: setattr(run, "called", True)
    monkeypatch.setitem(sys.modules, "server", SimpleNamespace(mcp=run))
    return run


def test_console_entrypoint_starts_stdio_server(monkeypatch) -> None:
    run = fake_server(monkeypatch)

    main([])

    assert run.called is True


def test_console_entrypoint_loads_env_file_without_overriding_environment(
    monkeypatch,
    tmp_path,
) -> None:
    run = fake_server(monkeypatch)
    env_file = tmp_path / "cookidoo.env"
    env_file.write_text(
        "COOKIDOO_EMAIL=file@example.com\n"
        "COOKIDOO_PASSWORD=file-password\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("COOKIDOO_EMAIL", "environment@example.com")
    monkeypatch.delenv("COOKIDOO_PASSWORD", raising=False)

    main(["--env-file", str(env_file)])

    assert run.called is True
    assert os.environ["COOKIDOO_EMAIL"] == "environment@example.com"
    assert os.environ["COOKIDOO_PASSWORD"] == "file-password"


def test_console_entrypoint_reports_version(capsys) -> None:
    with pytest.raises(SystemExit, match="0"):
        main(["--version"])

    assert capsys.readouterr().out.strip() == f"cookidoo-mcp {__version__}"


def test_registry_manifest_has_secure_required_credentials() -> None:
    manifest = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    package = manifest["packages"][0]
    variables = {
        variable["name"]: variable
        for variable in package["environmentVariables"]
    }

    assert manifest["name"] == "io.github.vitaliemiron/cookidoo-mcp"
    assert package["registryType"] == "pypi"
    assert package["identifier"] == "cookidoo-mcp"
    assert package["transport"] == {"type": "stdio"}
    assert set(variables) == {"COOKIDOO_EMAIL", "COOKIDOO_PASSWORD"}
    assert all(not variable["isRequired"] for variable in variables.values())
    assert all(variable["isSecret"] for variable in variables.values())
    assert all("value" not in variable for variable in variables.values())
    assert package["packageArguments"] == [
        {
            "type": "named",
            "name": "--env-file",
            "description": (
                "Optional local .env file containing the Cookidoo login "
                "and password."
            ),
            "format": "filepath",
            "isRequired": False,
        }
    ]
