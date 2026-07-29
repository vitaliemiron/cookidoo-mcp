# Cookidoo MCP vs browser automation

Last verified: 2026-07-29.

Prefer Cookidoo MCP whenever a supported tool exists. Its inputs, outputs,
validation, error handling, and tests are designed for the operation. Use an
authenticated browser to investigate an unsupported operation or a changed API
contract, then move repeatable work into the tested service.

## Decision rule

1. Use an existing MCP tool for a known operation.
2. If it fails, inspect the error and contract tests.
3. Use a browser only when the operation is unsupported or the real request has
   changed.
4. Capture the exact authenticated request.
5. Implement it in `cookidoo_service.py`, expose a small tool, and add tests.
6. Return to the MCP for normal use.

A purpose-built tool is not automatic permission for a broad write. Resolve
the exact target, read current state, show the intended change, apply the
smallest mutation, and verify the result.

Human guide:
https://vitaliemiron.github.io/cookidoo-mcp/use-cases/mcp-vs-browser-automation/
