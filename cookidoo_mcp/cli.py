"""Console entry point for the Cookidoo MCP stdio server."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from cookidoo_mcp import __version__


def main(argv: Sequence[str] | None = None) -> None:
    """Start the MCP server, or print package metadata and exit."""

    parser = argparse.ArgumentParser(
        prog="cookidoo-mcp",
        description="Run the unofficial Cookidoo MCP server over stdio.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help=(
            "Load Cookidoo credentials from this .env file without replacing "
            "environment variables that are already set."
        ),
    )
    args = parser.parse_args(argv)

    if args.env_file is not None:
        env_file = args.env_file.expanduser()
        if not env_file.is_file():
            parser.error(f"environment file does not exist: {env_file}")

        from dotenv import load_dotenv

        load_dotenv(dotenv_path=env_file, override=False)

    # Import lazily so `--help` and `--version` stay fast and side-effect free.
    from server import mcp

    mcp.run()
