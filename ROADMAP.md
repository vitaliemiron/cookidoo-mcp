# Cookidoo MCP roadmap

This roadmap communicates direction, not delivery dates. Priorities may change
when Cookidoo updates its undocumented APIs or when community feedback reveals
a safer or more useful path.

## Available today

- Read official recipe metadata and ingredients.
- Copy official recipes to private customer recipes for full-step workflows.
- Create, translate, validate, and update customer recipes.
- Add structured ingredient weighing, time, temperature, speed, direction, and
  supported Thermomix mode annotations.
- Upload user-owned recipe images.
- Read shopping-list ingredients grouped by recipe.
- Read and manage a rolling seven-day Cookidoo meal plan.
- Run offline unit tests and daily authenticated API contract monitoring.
- Serve human, AI-readable, and structured documentation through GitHub Pages.

## Current priorities

### Easier installation and discovery

- Publish a versioned Python package with a one-command MCP launch.
- Publish the server metadata to the official MCP Registry.
- Provide verified configuration examples for popular MCP clients.
- Create stable releases and upgrade notes.

### Reliability across Cookidoo changes

- Expand sanitized response fixtures for API edge cases.
- Keep live mutation tests small, reversible, and serialized.
- Improve regression reports so endpoint, status, and shape changes are easy to
  diagnose without exposing account data.
- Track compatibility with supported Python and `cookidoo-api` versions.

### Clearer first-run experience

- Make country and language selection configurable and validate supported
  locale pairs.
- Improve actionable authentication and reconnect errors.
- Add task-based guides for translation, guided cooking, planning, and
  shopping-list workflows.

## Later explorations

- More reusable guided-recipe examples and validation diagnostics.
- Import helpers for user-owned recipe sources.
- Safer preview or dry-run output before multi-step account mutations.
- Additional accessibility and localization for the documentation site.
- Community-contributed adapters that remain separate from the core Cookidoo
  contract.

## Explicit non-goals

- Pretending to be an official Cookidoo, Vorwerk, or Thermomix integration.
- Bypassing account permissions, subscriptions, or platform safeguards.
- Storing user credentials in the repository or a hosted service.
- Ordering products from grocery stores inside this MCP; that belongs in a
  separate store-specific integration.
- Fully unattended destructive changes to a Cookidoo account.

## Influence the roadmap

Start an [Ideas
Discussion](https://github.com/vitaliemiron/cookidoo-mcp/discussions/categories/ideas)
to describe the problem and desired outcome, or open a focused
[feature request](https://github.com/vitaliemiron/cookidoo-mcp/issues/new?template=feature-request.yml).
Contributions are welcome through [`CONTRIBUTING.md`](CONTRIBUTING.md).
