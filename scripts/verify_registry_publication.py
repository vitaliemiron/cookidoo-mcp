"""Verify that a release is active in the official MCP Registry."""

from __future__ import annotations

import argparse
import json
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

REGISTRY_API = "https://registry.modelcontextprotocol.io/v0.1/servers"
SERVER_NAME = "io.github.vitaliemiron/cookidoo-mcp"


def find_active_version(
    payload: dict[str, Any],
    expected_version: str,
    *,
    server_name: str = SERVER_NAME,
) -> dict[str, Any]:
    """Return the exact active registry entry or raise a useful error."""

    for entry in payload.get("servers", []):
        server = entry.get("server", {})
        metadata = entry.get("_meta", {}).get(
            "io.modelcontextprotocol.registry/official",
            {},
        )
        if (
            server.get("name") == server_name
            and server.get("version") == expected_version
            and metadata.get("status") == "active"
        ):
            return entry

    available = sorted(
        {
            str(entry.get("server", {}).get("version"))
            for entry in payload.get("servers", [])
            if entry.get("server", {}).get("name") == server_name
        }
    )
    versions = ", ".join(available) if available else "none"
    raise ValueError(
        f"{server_name} {expected_version} is not active; "
        f"matching registry versions: {versions}"
    )


def fetch_registry_payload(
    *,
    server_name: str = SERVER_NAME,
    timeout: float = 15,
) -> dict[str, Any]:
    """Fetch exact-name search results from the public registry API."""

    url = f"{REGISTRY_API}?{urlencode({'search': server_name})}"
    with urlopen(url, timeout=timeout) as response:  # noqa: S310
        return json.load(response)


def verify(
    expected_version: str,
    *,
    attempts: int = 1,
    delay: float = 0,
) -> dict[str, Any]:
    """Retry until the expected active version is visible."""

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return find_active_version(
                fetch_registry_payload(),
                expected_version,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(delay)

    raise RuntimeError(
        f"MCP Registry verification failed after {attempts} attempt(s): "
        f"{last_error}"
    ) from last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected_version")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--delay", type=float, default=0)
    args = parser.parse_args()
    if args.attempts < 1:
        parser.error("--attempts must be at least 1")
    if args.delay < 0:
        parser.error("--delay cannot be negative")

    entry = verify(
        args.expected_version,
        attempts=args.attempts,
        delay=args.delay,
    )
    metadata = entry["_meta"]["io.modelcontextprotocol.registry/official"]
    print(
        f"Verified {SERVER_NAME} {args.expected_version} "
        f"(status={metadata['status']})"
    )


if __name__ == "__main__":
    main()
