# Testing and reliability

Cookidoo uses undocumented APIs, so automated checks are part of the product rather than an afterthought.

## Unit tests

Deterministic tests cover payload validation, UTF-16 annotation positions, recipe structure, service behavior, and documentation consistency.

## Live contracts

Five opt-in tests check real read-only or safely scoped Cookidoo behavior:

1. Authentication
2. Official recipe details
3. Shopping-list retrieval
4. Seven-day meal-plan retrieval
5. Custom-recipe access

## Daily monitoring

A scheduled GitHub Actions workflow runs the live contracts daily with encrypted repository secrets. When an undocumented endpoint changes, the failure identifies which contract drifted so it can be investigated before users discover it manually.

Credentials must never be committed. Live tests should avoid destructive account mutations by default.
