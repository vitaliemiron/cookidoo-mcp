# Security policy

Cookidoo MCP connects AI clients to authenticated Cookidoo accounts. Security
reports are taken seriously, especially when they involve credentials,
sessions, unintended account mutations, or exposure of private recipes and
planning data.

## Supported versions

Security fixes target the `main` branch and the latest tagged release when one
exists. Older revisions may not receive fixes.

## Report a vulnerability privately

Please use GitHub's
[private vulnerability reporting form](https://github.com/vitaliemiron/cookidoo-mcp/security/advisories/new).
Do not open a public issue for a suspected vulnerability.

Include, where possible:

- the affected version, commit, MCP tool, or endpoint;
- the security impact and who could be affected;
- minimal reproduction steps or a proof of concept;
- suggested mitigations;
- whether the report contains details that should remain confidential.

Never include real Cookidoo credentials, cookies, access tokens, upload
signatures, private recipe contents, or account identifiers. Use placeholders
and redact logs before attaching them.

The maintainer will try to acknowledge a report within seven days. Disclosure
timing will be coordinated around a validated fix when practical.

## What belongs in a normal issue

Use the public
[API regression form](https://github.com/vitaliemiron/cookidoo-mcp/issues/new?template=api-regression.yml)
for ordinary Cookidoo outages, changed response shapes, authentication
breakage, or parser failures that do not expose sensitive data or enable
unauthorized actions.

## Security expectations for contributors

- Never commit `.env`, cookies, session data, account identifiers, or secrets.
- Do not print `COOKIDOO_EMAIL` or `COOKIDOO_PASSWORD` in test output.
- Do not expose repository secrets to pull requests or forks.
- Keep live mutations reversible and guarantee cleanup in a `finally` block.
- Reuse the authenticated Cookidoo session; do not invent weaker credential
  storage.
- Upload only images the account owner has the right to use.

Cookidoo MCP uses undocumented third-party endpoints. A service change or
outage is not automatically a security vulnerability, but behavior that could
leak data or mutate the wrong account should be reported privately.
