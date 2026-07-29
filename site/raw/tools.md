# Cookidoo MCP tool reference

The server exposes 16 tools.

## Authentication

- `connect_to_cookidoo()` — authenticate using configured credentials.

## Recipes

- `get_recipe_details(recipe_id)` — public metadata and ingredients.
- `get_custom_recipe_details(recipe_id)` — private recipe ingredients and full steps.
- `copy_recipe_to_custom(recipe_id, servings=4, dry_run=false)` — preview or create an editable private copy.

## Authoring

- `generate_recipe_structure(...)` — create a starter payload.
- `validate_guided_recipe_structure(recipe_json)` — validate the structured recipe.
- `calculate_annotation_position(text, marker, occurrence=1)` — obtain UTF-16 ranges.
- `update_custom_recipe_steps(recipe_id, steps_json, dry_run=false)` — preview or apply a partial step update.
- `update_custom_recipe_ingredients(recipe_id, ingredients_json, dry_run=false)` — preview or apply a partial ingredient update.
- `upload_custom_recipe_image(recipe_id, image_path, dry_run=false)` — validate, preview, or attach a user-owned image.
- `upload_custom_recipe(recipe_json, dry_run=false)` — preview or create the recipe.

## Planning

- `get_meal_plan_week(date)` — read a seven-day window.
- `add_recipes_to_meal_plan(date, recipe_ids, recipe_source="auto", dry_run=false)`
- `remove_recipe_from_meal_plan(date, recipe_id, recipe_source="auto", dry_run=false)`
- `move_recipe_in_meal_plan(recipe_id, from_date, to_date, recipe_source="auto", dry_run=false)`

## Shopping

- `get_shopping_list_ingredients(recipe_id=None, include_owned=false, include_additional_items=true)`

Machine-readable descriptions and complete signatures are available in [`tools.json`](../tools.json).

## Preview changes safely

Every tool that creates or changes a recipe, image, or calendar entry accepts
`dry_run`. Call it with `dry_run=true` first. The response validates the input
and returns `will_mutate: false`, the exact target and planned changes, and
notes about the operation. Review that JSON, then repeat the same call with
`dry_run=false` to apply it.

Recipe and calendar previews do not need an active Cookidoo session. Image
previews read and normalize the local file in memory to validate its type and
size, but never upload it.
