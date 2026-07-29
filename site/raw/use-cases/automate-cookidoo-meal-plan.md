# Automate Cookidoo My Week with AI

Last verified: 2026-07-29.

Read the current seven-day plan first, identify an exact recipe ID and ISO
date, make one scoped add, move, or remove operation, then read the plan again.

`get_meal_plan_week("2026-07-29")` returns seven consecutive dates beginning
on 2026-07-29. It is a rolling window, not automatically Monday through Sunday.
Empty days are filled by the service.

## Safe workflow

1. Connect to Cookidoo.
2. Read the relevant seven-day window.
3. Resolve the exact recipe ID, source date, and target date.
4. Call the mutation with `dry_run=true` and show its validated preview.
5. Repeat the same scoped operation with `dry_run=false`.
6. Read the window again and confirm the result.

Available operations:

- `get_meal_plan_week`
- `add_recipes_to_meal_plan`
- `remove_recipe_from_meal_plan`
- `move_recipe_in_meal_plan`

Official recipe IDs normally begin with `r`; private recipe IDs are
26-character ULIDs. Use `recipe_source="auto"` unless the source cannot be
inferred. Moving adds to the target first and rolls back the new target entry
if source removal fails.

Human guide:
https://vitaliemiron.github.io/cookidoo-mcp/use-cases/automate-cookidoo-meal-plan/
