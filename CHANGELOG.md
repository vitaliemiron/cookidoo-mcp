# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0](https://github.com/vitaliemiron/cookidoo-mcp/compare/v1.1.1...v1.2.0) (2026-07-29)


### Features

* **site:** add localized marketing pages ([#25](https://github.com/vitaliemiron/cookidoo-mcp/issues/25)) ([719f4f8](https://github.com/vitaliemiron/cookidoo-mcp/commit/719f4f8702303d474180bc2edc40cc0bb89cd37a))
* **site:** follow the browser language ([#27](https://github.com/vitaliemiron/cookidoo-mcp/issues/27)) ([844f7cf](https://github.com/vitaliemiron/cookidoo-mcp/commit/844f7cfbedf7e9b7e94f37ebf1dd4f25218b5239))

## [1.1.1](https://github.com/vitaliemiron/cookidoo-mcp/compare/v1.1.0...v1.1.1) (2026-07-29)


### Bug Fixes

* **release:** attest reproducible CycloneDX SBOMs ([#23](https://github.com/vitaliemiron/cookidoo-mcp/issues/23)) ([01b7443](https://github.com/vitaliemiron/cookidoo-mcp/commit/01b74430caa506729e1aa1bcfd1616cc9d9d04f1))

## [1.1.0](https://github.com/vitaliemiron/cookidoo-mcp/compare/v1.0.0...v1.1.0) (2026-07-29)


### Features

* improve setup safety and release trust ([#20](https://github.com/vitaliemiron/cookidoo-mcp/issues/20)) ([eee0602](https://github.com/vitaliemiron/cookidoo-mcp/commit/eee06023453a0f9e43a83723db91d5ffa373d235))
* **release:** automate versioned releases ([#21](https://github.com/vitaliemiron/cookidoo-mcp/issues/21)) ([d0db602](https://github.com/vitaliemiron/cookidoo-mcp/commit/d0db6021b5b52826536cb7f659e98f2ad947157a))

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

[1.0.0]: https://github.com/vitaliemiron/cookidoo-mcp/releases/tag/v1.0.0
