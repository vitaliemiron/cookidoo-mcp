## What does this change?

Describe the user problem and the result of this pull request.

## Why this approach?

Explain the important design or API-contract decisions and alternatives
considered.

## Related work

Closes #

## Validation

- [ ] `venv/bin/ruff check cookidoo_service.py schemas.py server.py tests`
- [ ] `venv/bin/python -m pytest -m "not live" --strict-markers -q`
- [ ] Relevant live contract test, when safe and necessary
- [ ] Temporary Cookidoo data was removed in `finally`
- [ ] Documentation and tool catalogs were updated when behavior changed

Add commands, results, screenshots, or a short explanation for checks that do
not apply.

## Safety and account-data review

- [ ] No credentials, cookies, signatures, account IDs, private recipes, or
      other sensitive data are committed or logged
- [ ] Ingredient handling and Thermomix machine actions remain separate
- [ ] Annotation positions use JavaScript UTF-16 offsets
- [ ] Mutations preserve unrelated user data and require appropriate user
      authorization
- [ ] Uploaded images are owned or licensed by the account owner
- [ ] Pull-request workflows do not receive Cookidoo repository secrets

## Reviewer notes

Call out undocumented endpoint assumptions, compatibility risks, or areas that
need especially careful review.
