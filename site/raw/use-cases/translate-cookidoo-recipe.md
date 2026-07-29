# How to translate a Cookidoo recipe with AI

Last verified: 2026-07-29.

Copy the official recipe into the account's private recipes, translate the
final text, rebuild guided-cooking annotations against that text, validate,
then update ingredients and steps separately. Copying is necessary because the
official recipe-details response does not contain preparation instructions.

## Workflow

1. Connect and identify the exact Cookidoo recipe ID.
2. Call `copy_recipe_to_custom` to create an editable copy with full steps.
3. Read it with `get_custom_recipe_details`.
4. Translate ingredients and instructions while preserving quantities,
   servings, time, temperature, speed, direction, and supported modes.
5. Split weighing or adding ingredients from the machine action that follows.
6. Calculate every position against the final translated text with
   `calculate_annotation_position`.
7. Validate with `validate_guided_recipe_structure`.
8. Show the proposed change, PATCH ingredients and instructions separately,
   then read the recipe again.

Ingredient steps contain only `INGREDIENT` annotations. Chopping, mixing,
heating, kneading, or another machine step contains `TTS` or `MODE`, never
`INGREDIENT`.

Do not reuse an official stock-image URL on the private copy. Upload only a
local image the account owner may use. Do not overwrite an existing private
recipe unless the user identifies it and requests that exact change.

Human guide:
https://vitaliemiron.github.io/cookidoo-mcp/use-cases/translate-cookidoo-recipe/
