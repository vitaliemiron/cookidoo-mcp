# AGENTS.md

Notes for future agents (or humans) working on this project, covering what was explored/fixed in this session and what's still open.

## What this project is

A FastMCP server (`server.py` + `cookidoo_service.py`) exposing Cookidoo (Thermomix recipe platform) actions as MCP tools: connect/auth, fetch a recipe's details, generate/validate a custom recipe structure, and upload a custom recipe. It wraps the `cookidoo-api` PyPI package (https://github.com/miaucl/cookidoo-api) plus some direct calls to Cookidoo's undocumented `created-recipes` REST endpoint for things the library doesn't cover.

## Bugs fixed

- `server.py`'s `get_recipe_details`: was reading `ingredient.quantity` (doesn't exist) instead of `ingredient.description` (where the quantity/amount text actually lives on `CookidooIngredient`). Fixed, and also added `image`/`thumbnail` URLs to the output, which were previously fetched but never surfaced.
- `cookidoo_service.py` login locale: was hardcoded to `country="fr", language="fr-FR"`. Changed over the course of this session, ending at `country="ro", language="en"` (resolves to `cookidoo.international/foundation/en`). Change this call in `login()` if a different locale is needed — use `cookidoo_api.helpers.get_localization_options(country=..., language=...)` to check valid pairings first (not every country/language combo exists; `us` for example only has `en-US`, not plain `en`).
- `cookidoo_service.py` authentication headers: the service expected the old `Cookidoo.auth_data.access_token` interface. Installed `cookidoo-api` 0.17.2 authenticates through session cookies and no longer has `auth_data`. Custom-recipe POST/PATCH calls now reuse the authenticated API session and its normal headers.

**Caveat:** the MCP server runs as a long-lived subprocess with module-level state (`_cookidoo_api` in `server.py`). Editing `cookidoo_service.py`/`server.py` does NOT take effect in already-connected MCP tool calls — the server process needs to be restarted/reconnected for code changes to be picked up. During this session, verification of fixes was done by running the updated Python directly (`python3 -c "..."` against the venv), not through the live MCP tools.

## Known limitation: `get_recipe_details` / official recipe endpoint has no steps

The official recipe-details endpoint (`Cookidoo.get_recipe_details`, backing the `get_recipe_details` MCP tool) returns ingredients, difficulty, times, images, etc., but genuinely has **no step-by-step instructions field at all** (confirmed by inspecting the raw API response — no `steps`/`instructions` key exists on `CookidooShoppingRecipeDetails`). This isn't a bug in this codebase; the public "recipe details" endpoint just doesn't carry that data.

**Workaround that does work:** `Cookidoo.add_custom_recipe_from(recipe_id, serving_size)` — the same "copy to my recipes" action available in the Cookidoo UI — creates a private copy under the account's `created-recipes` and *does* return full `ingredients` (with quantities) and `instructions` (`CookidooCustomRecipe`). This is the recommended path whenever full recipe content (including steps) is needed: copy first, then read/edit the copy.

## Custom recipe editing: raw PATCH endpoint

Custom/created recipes are edited via `PATCH {base_url}/created-recipes/{locale}/{recipe_id}`. Creating a recipe still uses a complete object; `cookidoo_service.py`'s `create_custom_recipe` shows the base shape: `name`, `image`, `isImageOwnedByUser`, `tools`, `yield`, `prepTime`/`cookTime`/`totalTime` (seconds), `ingredients` (list of `{type: "INGREDIENT", text, annotations?}`), `instructions` (list of `{type: "STEP", text, annotations?}`), `hints`, `workStatus`, `recipeMetadata`.

The live web editor was inspected on 2026-07-23 (customer-recipes bundle `1.174.5`). It performs safe **partial** updates to the same endpoint:

- `{"instructions": [...]}` replaces only the preparation steps.
- `{"ingredients": [...]}` replaces only the ingredients.

`CookidooService.update_custom_recipe_steps` and `update_custom_recipe_ingredients` now use these partial forms so unrelated recipe fields are preserved.

### Image field

The `image` field only accepts `null` or a path matching `^((prod|nonprod)/img/customer-recipe/)?[A-Za-z0-9-_]{1,}.(bmp|jpe|jpeg|jpg|png)$` — i.e. an asset already uploaded to Cookidoo's own `customer-recipe` namespace. Setting it to an arbitrary external URL is rejected by server-side validation.

The upload flow is now implemented in
`CookidooService.upload_custom_recipe_image` and exposed as the
`upload_custom_recipe_image` MCP tool:

1. Read a local image and normalize it to JPEG with Pillow. This also makes
   WebP files accepted by Cookidoo.
2. Request a short-lived upload signature with
   `POST {base_url}/created-recipes/{locale}/image/signature` and
   `{"source": "uw", "timestamp": unix_seconds}`.
3. Upload the multipart file to
   `https://api-eu.cloudinary.com/v1_1/vorwerk-users-gc/image/upload` with the
   returned signature, API key `993585863591145`, source `uw`, and upload
   preset `prod-customer-recipe-signed`.
4. PATCH the recipe with the returned `{public_id}.{format}` key and
   `isImageOwnedByUser: true`.

Cookidoo documents a 10 MB limit. Only upload images the account owner has the
right to use.

### Step annotations (guided-cooking "cooking settings")

Plain step `text` displays fine on-device, but doesn't drive the Thermomix's automatic guided-cooking behavior (auto speed/time). That requires a structured `annotations` array on the instruction object. Confirmed schema for the "Cooking settings" (manual time/speed) feature, captured via one real browser session against the account's own recipe editor (DevTools-equivalent network capture, not blind guessing):

```json
{
  "type": "STEP",
  "text": "...30 сек/скорость 10.",
  "annotations": [
    {
      "type": "TTS",
      "data": { "speed": "10", "time": 30 },
      "position": { "offset": 65, "length": 18 }
    }
  ]
}
```

- `type: "TTS"` = Time/Temperature/Speed (not text-to-speech, despite the UI's CSS class name).
- `data.speed` is a string (e.g. `"10"`), `data.time` is an integer in **seconds**.
- `data.direction` is `"CCW"` for reverse. Normal clockwise (`"CW"`) is omitted by the manual-settings editor.
- `data.temperature` is either omitted or `{"value": "100", "unit": "C"}`. The value is a string; the unit is `"C"` or `"F"`.
- `position.offset`/`length` is a **JavaScript UTF-16** character range into the step's own `text`, pointing at the human-readable substring (e.g. `"30 сек/скорость 10"`) that the UI expects to find there. This matters when emoji appear before the annotation because Python's normal string indexes differ. Use the `calculate_annotation_position` MCP tool or `schemas.position_for`; do not calculate offsets with plain `len()`/`.index()`.

### Step annotations (ingredient linking / auto-weigh)

The editor's scale/ingredient annotation uses this shape:

```json
{
  "type": "INGREDIENT",
  "data": {
    "description": {
      "text": "75 г сахара",
      "annotations": [
        {
          "type": "VOLUME",
          "data": {
            "amount": 75,
            "unit": "gram",
            "unitText": "г"
          },
          "position": { "offset": 0, "length": 4 }
        }
      ]
    }
  },
  "position": { "offset": 9, "length": 11 }
}
```

- The outer position points into the step text and identifies the ingredient phrase.
- The nested `VOLUME` position points into `description.text` and identifies the amount text.
- `amountMax` is available for ranges.
- `description` may also be a plain string when structured amount data is unavailable.
- The deployed editor contains support for the same `VOLUME` annotation directly on ingredient-list entries. The current account did not have the `structured-ingredients` feature flag enabled during verification, so the API accepted but stripped that top-level annotation. The nested `VOLUME` inside a step's `INGREDIENT` link was preserved and reconstructed correctly, which is the part needed for on-device weighing.

### Smart-function mode annotations

Modes use `type: "MODE"`, an uppercase `name`, a mode-specific `data` object, and the normal step-text `position`.

Confirmed mode names and data:

- `DOUGH`: `{"time": seconds}` (1–1200)
- `BLEND`: `{"time": seconds, "speed": "6"..."8"}` (10–300 seconds)
- `TURBO`: `{"time": 0.5|1|2, "pulseCount": n?}`
- `WARM_UP`: `{"temperature": {"value": "...", "unit": "C"}, "speed": "soft"|"1"|"2"}`
- `RICE_COOKER`: `{}`
- `STEAMING`: `{"time": seconds, "speed": "...", "direction": "CW"|"CCW", "accessory": "Varoma"|"SimmeringBasket"|"VaromaAndSimmeringBasket"}`
- `BROWNING`: `{"time": seconds, "temperature": {"value": "...", "unit": "C"}, "power": "Gentle"|"Intense"}`

Cookidoo currently exposes speed values as strings: `"soft"`, `"0.5"`, `"1"`, ... `"10"`. Temperature and speed combinations are constrained by the editor (for example, manual temperatures cannot be combined with speeds above 6).

## MCP tools added for full custom-recipe workflows

- `get_custom_recipe_details`
- `copy_recipe_to_custom`
- `validate_guided_recipe_structure`
- `calculate_annotation_position`
- `update_custom_recipe_steps`
- `update_custom_recipe_ingredients`

The Pydantic models in `schemas.py` validate annotation types and ensure every offset/length stays within its enclosing text.

End-to-end verification created a temporary private recipe through the service, loaded it in the authenticated browser editor, and confirmed that Cookidoo reconstructed:

- `<cr-ingredient>` with amount/unit data for on-device weighing
- `<cr-tts>` with time, `100°C`, speed `4`, and reverse direction `CCW`
- `<cr-mode name="dough">` with a 60-second mode duration

The same annotations survived a partial step PATCH and a browser reload. The temporary recipe was deleted after verification.

## Meal-planning/calendar API

Cookidoo's meal planner is available through the installed `cookidoo-api`
package and is exposed by these MCP tools:

- `get_meal_plan_week`
- `add_recipes_to_meal_plan`
- `remove_recipe_from_meal_plan`
- `move_recipe_in_meal_plan`

The underlying endpoints are:

- `GET planning/{language}/api/my-week/{YYYY-MM-DD}`
- `PUT planning/{language}/api/my-day`
- `DELETE planning/{language}/api/my-day/{day}/recipes/{recipe}`

Official recipes use `{"recipeIds": [...], "dayKey": "..."}`. Customer recipes
use the same payload plus `"recipeSource": "CUSTOMER"`; deletion uses the
`recipeSource=CUSTOMER` query parameter.

The week endpoint is actually a rolling seven-day window beginning on the date
in the path (the same date shown in the web planner's `?date=...` query), not a
fixed Monday-Sunday week. It omits empty days and can return customer recipes
only in `customerRecipeIds`, without names or images.
`CookidooService.get_meal_plan_week` therefore fills all seven days beginning
on the requested date and resolves each customer ID through
`get_custom_recipe`. The add tool can split a mixed list of official `r...` IDs
and custom ULIDs into the correct API calls. Moving adds to the target before
removing from the source and rolls back a newly added target entry if source
removal fails.

Deleting the final recipe from a day returns HTTP 200 with `content: null`.
`cookidoo-api` incorrectly tries to parse that null content as a calendar day
and raises after the deletion already succeeded. Calendar removal therefore
uses a small direct DELETE wrapper and refreshes the day afterward.

## General approach used for translating a recipe end-to-end

1. `add_custom_recipe_from(original_id, servings)` to get a private copy with full ingredients + instructions.
2. Translate `name`, ingredient `text`s, and instruction `text`s.
3. PATCH the copy with translated text, preserving `tools`/`yield`/`prepTime`/`totalTime` from the copy, `image: null` (see above), and add TTS annotations per step if guided-cooking behavior is wanted (recompute `position.offset`/`length` against the *translated* text, not the original).
4. Optionally set `hints` to link back to the original recipe (e.g. for its photo, since the translated copy won't have one).

## Required step separation

Always separate ingredient handling from machine actions in every created,
translated, or enhanced recipe:

1. Use one step only for weighing and/or adding ingredients, with `INGREDIENT`
   annotations.
2. Use the following step for chopping, mixing, cooking, kneading, or another
   Thermomix action, with its `TTS` or `MODE` annotation.

Never combine `INGREDIENT` with `TTS` or `MODE` annotations in the same step.
`RecipeStep` validation enforces this for structured guided-cooking payloads,
and the FastMCP server instructions apply the rule to all tool workflows.
