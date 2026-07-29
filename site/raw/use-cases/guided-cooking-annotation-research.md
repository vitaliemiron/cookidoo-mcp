# How Cookidoo guided-cooking annotations were verified

Editor contract observed: 2026-07-23. Documentation rechecked: 2026-07-29.

Private Cookidoo recipe steps accept positioned `TTS`, `INGREDIENT`, and
`MODE` annotations. A temporary recipe round trip reconstructed ingredient
weighing, manual time/temperature/speed with reverse, and Dough mode in the
authenticated editor. The annotations survived a partial step PATCH and
reload.

## Method

1. Observe the authenticated customer-recipe editor and its network requests.
2. Capture exact annotation shapes, data fields, mode names, and positions.
3. Create an isolated temporary private recipe.
4. Write the structures through the authenticated customer-recipe API.
5. Reload and confirm the editor reconstructed ingredient, manual-setting, and
   mode elements.
6. Apply a partial instruction PATCH and reload again.
7. Delete the temporary recipe.

## Evidence

- A step `INGREDIENT` with nested `VOLUME` reconstructed amount and unit data.
- `TTS` with 30 seconds, 100 °C, speed 4, and `CCW` reconstructed the matching
  manual settings.
- `MODE` named `DOUGH` with 60 seconds reconstructed Dough mode.

Positions are JavaScript UTF-16 ranges, not ordinary Python string indexes.
Use `schemas.position_for` or `calculate_annotation_position`.

This remains an undocumented private contract. Feature flags can differ by
account, Cookidoo can change behavior without notice, and schema validity does
not guarantee culinary safety.

Human guide:
https://vitaliemiron.github.io/cookidoo-mcp/use-cases/guided-cooking-annotation-research/
