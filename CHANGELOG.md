# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A four-step setup wizard for Codex, Claude Desktop, and VS Code on macOS,
  Linux, and Windows, with credentials kept in a private local file.
- Configurable Cookidoo country and language values with normalization,
  supported-pair validation, and backwards-compatible `ro` + `en` defaults.
- Non-mutating `dry_run` previews for every recipe, image, and meal-plan tool
  that changes Cookidoo account data.
- Windows package installation and environment-file smoke testing in CI.
- CycloneDX SBOM generation, GitHub build-provenance/SBOM attestations, and
  public MCP Registry publication verification for tagged releases.

### Changed

- Dependabot now groups Python and GitHub Actions updates to reduce maintenance
  noise.
- MCP Registry links now open the public registry search for this server.

## [1.0.0] - 2026-07-29

### Added

- FastMCP tools for authentication, official and customer recipe reads,
  copying, generation, validation, and partial updates.
- Structured guided-cooking support for ingredient weighing, manual
  time/temperature/speed settings, reverse direction, and supported Thermomix
  modes.
- Customer-recipe image upload through Cookidoo's signed upload flow.
- Shopping-list ingredient retrieval grouped by recipe.
- Seven-day meal-plan reads, additions, removals, and moves for official and
  customer recipes.
- Offline unit tests and scheduled authenticated Cookidoo API contract tests.
- Human documentation, AI-readable Markdown, `llms.txt`, `llms-full.txt`, and
  a structured MCP tool catalog on GitHub Pages.
- A versioned PyPI package with the `cookidoo-mcp` and
  `python -m cookidoo_mcp` launchers.
- Official MCP Registry metadata and an OIDC-based release workflow.
- Task-focused guides for translation, guided cooking, My Week, shopping-list
  retrieval, API automation, and verified annotation research.
- Contribution, support, security, roadmap, issue-form, and pull-request
  guidance for the public community.

[Unreleased]: https://github.com/vitaliemiron/cookidoo-mcp/commits/main
[1.0.0]: https://github.com/vitaliemiron/cookidoo-mcp/releases/tag/v1.0.0
