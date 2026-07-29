# Contributing to Cookidoo MCP

Thank you for helping make meal-planning automation safer, clearer, and more
useful. Contributions of code, documentation, test cases, API observations,
translations, and reproducible bug reports are welcome.

Cookidoo MCP is an unofficial project. It is not affiliated with or endorsed
by Cookidoo, Vorwerk, or Thermomix.

## Good ways to contribute

- Improve setup instructions for a particular MCP client.
- Add a focused unit test for an API response or edge case.
- Clarify human or AI-readable documentation.
- Report a changed Cookidoo API contract with sanitized evidence.
- Tackle an issue labeled
  [`good first issue`](https://github.com/vitaliemiron/cookidoo-mcp/labels/good%20first%20issue).

For questions and early ideas, start a
[GitHub Discussion](https://github.com/vitaliemiron/cookidoo-mcp/discussions).
For a confirmed problem or scoped proposal, use an
[issue form](https://github.com/vitaliemiron/cookidoo-mcp/issues/new/choose).
Security issues belong in a
[private vulnerability report](https://github.com/vitaliemiron/cookidoo-mcp/security/advisories/new).

## Before opening a pull request

1. Read [`AGENTS.md`](AGENTS.md) completely. It is the source of truth for
   account safety, API behavior, recipe structure, and test expectations.
2. Search existing issues and pull requests to avoid duplicate work.
3. Open an issue before a large behavioral or architectural change.
4. Keep the change focused. Unrelated cleanup is easier to review separately.
5. Give the pull request a Conventional Commit title. Use `feat:` for a new
   user-facing capability, `fix:` for a correction, and `chore:`, `docs:`, or
   `test:` when the change should not independently bump the package version.
   The squash title becomes the release input used by Release Please.

## Local setup

Python 3.12 or newer is required.

```bash
git clone https://github.com/vitaliemiron/cookidoo-mcp.git
cd cookidoo-mcp
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Add real Cookidoo credentials only to the local `.env` file. Never commit,
paste, record, or print credentials, cookies, signatures, session data, or
account identifiers.

Run the server:

```bash
venv/bin/fastmcp run server.py
```

## Development rules

### Protect Cookidoo accounts

- Prefer read-only investigation.
- Never delete or overwrite customer content without explicit authorization.
- Live tests may create temporary content only when cleanup is guaranteed in a
  `finally` block.
- Never expose real credentials to pull-request workflows or forks.
- Upload only images the account owner has the right to use.

### Keep recipe steps explicit

Ingredient handling and Thermomix actions must be separate:

1. A weighing or adding step contains only `INGREDIENT` annotations.
2. The following chopping, mixing, heating, cooking, or kneading step contains
   its `TTS` or `MODE` annotation.

Never combine `INGREDIENT` with `TTS` or `MODE` in one step. Annotation
positions use JavaScript UTF-16 code units; use `schemas.position_for` rather
than ordinary Python string indexes.

### Treat Cookidoo endpoints as unstable

Cookidoo APIs used by this project are undocumented. An API-facing change
should include:

- a unit test with a fake or sanitized fixture;
- a safe live contract test when the operation can be reversed reliably;
- explicit parsing of the observed response shape;
- updated human and AI-readable documentation when tool behavior changes.

Do not weaken a contract assertion only to make a test pass.

## Tests and documentation

Run lint and all offline tests:

```bash
venv/bin/ruff check cookidoo_service.py schemas.py server.py tests
venv/bin/python -m pytest -m "not live" --strict-markers -q
```

Authenticated tests are opt-in and must never run on untrusted pull requests:

```bash
set -a
source .env
set +a
COOKIDOO_LIVE_TESTS=1 \
COOKIDOO_LIVE_MUTATIONS=1 \
venv/bin/python -m pytest tests/live -m live --strict-markers -v
```

When an MCP tool changes, update `site/tools.json`, the relevant HTML and raw
Markdown documentation, `site/llms.txt` or `site/llms-full.txt` when
applicable, and `AGENTS.md`. `tests/test_docs_site.py` verifies the public tool
catalog and local links.

## Pull-request checklist

A ready pull request should:

- explain the user problem and the chosen solution;
- link the related issue when one exists;
- include tests proportionate to the risk;
- preserve credentials and account data;
- document any new behavior or limitation;
- pass the offline test suite;
- identify any live verification performed and confirm cleanup.

By contributing, you agree that your contribution is licensed under the
repository's [Apache License 2.0](LICENSE).
