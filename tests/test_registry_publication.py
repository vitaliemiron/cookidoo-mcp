import json

import pytest

from scripts.verify_registry_publication import find_active_version, verify


def registry_payload(
    version: str = "1.0.0",
    *,
    status: str = "active",
) -> dict:
    return {
        "servers": [
            {
                "server": {
                    "name": "io.github.vitaliemiron/cookidoo-mcp",
                    "version": version,
                },
                "_meta": {
                    "io.modelcontextprotocol.registry/official": {
                        "status": status,
                        "isLatest": True,
                    }
                },
            }
        ]
    }


def test_find_active_version_returns_exact_match() -> None:
    entry = find_active_version(registry_payload(), "1.0.0")

    assert entry["server"]["version"] == "1.0.0"


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        (registry_payload("0.9.0"), "matching registry versions: 0.9.0"),
        (registry_payload(status="deprecated"), "1.0.0 is not active"),
        ({"servers": []}, "matching registry versions: none"),
    ],
)
def test_find_active_version_rejects_missing_or_inactive_entries(
    payload: dict,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        find_active_version(payload, "1.0.0")


def test_verify_retries_transient_registry_responses(monkeypatch) -> None:
    responses = iter(
        [
            OSError("temporary failure"),
            registry_payload("0.9.0"),
            registry_payload("1.0.0"),
        ]
    )
    sleeps: list[float] = []

    def fetch() -> dict:
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(
        "scripts.verify_registry_publication.fetch_registry_payload",
        fetch,
    )
    monkeypatch.setattr(
        "scripts.verify_registry_publication.time.sleep",
        sleeps.append,
    )

    entry = verify("1.0.0", attempts=3, delay=0.25)

    assert entry["server"]["version"] == "1.0.0"
    assert sleeps == [0.25, 0.25]


def test_verify_reports_last_registry_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.verify_registry_publication.fetch_registry_payload",
        lambda: json.loads('{"servers": []}'),
    )

    with pytest.raises(RuntimeError, match="after 2 attempt"):
        verify("1.0.0", attempts=2)
