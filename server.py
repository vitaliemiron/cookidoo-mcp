"""
Cookidoo MCP Server

Main server file containing MCP tool definitions for interacting with Cookidoo.
"""

from fastmcp import FastMCP
from cookidoo_service import CookidooService, load_cookidoo_credentials
from pydantic import TypeAdapter

from schemas import CustomRecipe, RecipeIngredient, RecipeStep, position_for
from datetime import date as CalendarDate
import json
import re
from typing import Any, Literal

MCP_INSTRUCTIONS = """
Always separate ingredient handling from machine actions. A step that weighs or
adds ingredients must contain only that ingredient action and INGREDIENT
annotations. Put chopping, mixing, cooking, kneading, or another Thermomix
operation in the following separate step with its TTS or MODE annotation. Never
combine INGREDIENT annotations with TTS or MODE annotations in one step. Apply
this rule when creating, translating, enhancing, validating, or updating every
recipe.

For grocery or cart workflows, use get_shopping_list_ingredients as the source
of truth. Preserve its recipe grouping and recipe IDs. By default, ingredients
marked as already owned are excluded; request include_owned only when the full
historical list is needed.

For meal-planning workflows, read the relevant week with get_meal_plan_week
before changing it. Official Cookidoo recipe IDs and custom/customer recipe IDs
use different API operations; the calendar tools infer the source when possible
and also accept an explicit recipe_source.

Before creating or changing recipes, images, or calendar entries, call the
mutation tool with dry_run=true. Show the returned preview to the user, then
apply the same validated inputs with dry_run=false only after the requested
change is clear. A dry run must never write to Cookidoo.
""".strip()

# Initialize FastMCP server
mcp = FastMCP("cookidoo-mcp-server", instructions=MCP_INSTRUCTIONS)

# Module-level state to store the authenticated session
_cookidoo_service: CookidooService | None = None
_cookidoo_api = None

_steps_adapter = TypeAdapter(list[str | RecipeStep])
_ingredients_adapter = TypeAdapter(list[str | RecipeIngredient])


def _parse_calendar_date(value: str) -> CalendarDate:
    """Parse the ISO date format used by Cookidoo's planning API."""

    try:
        return CalendarDate.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"Invalid date {value!r}: expected YYYY-MM-DD"
        ) from error


def _parse_recipe_ids(value: str) -> list[str]:
    """Parse comma, whitespace, or newline-separated recipe IDs."""

    recipe_ids = [
        recipe_id
        for recipe_id in re.split(r"[\s,]+", value.strip())
        if recipe_id
    ]
    if not recipe_ids:
        raise ValueError("At least one recipe ID is required")
    return recipe_ids


def _require_recipe_id(value: str) -> str:
    """Normalize one recipe ID and reject empty mutation targets."""

    recipe_id = value.strip()
    if not recipe_id:
        raise ValueError("recipe_id is required")
    return recipe_id


def _jsonable_recipe_items(
    values: list[str | RecipeIngredient | RecipeStep],
) -> list[str | dict[str, Any]]:
    """Convert validated recipe values into safe JSON preview content."""

    return [
        value
        if isinstance(value, str)
        else value.model_dump(mode="json", exclude_none=True)
        for value in values
    ]


def _dry_run_result(
    tool: str,
    operation: str,
    *,
    target: dict[str, Any],
    changes: dict[str, Any],
    notes: list[str] | None = None,
) -> str:
    """Return a consistent, machine-readable preview without mutating Cookidoo."""

    return json.dumps(
        {
            "dry_run": True,
            "will_mutate": False,
            "operation": operation,
            "target": target,
            "changes": changes,
            "notes": notes or [],
            "apply": {
                "tool": tool,
                "instruction": (
                    "Review this preview, then call the same tool with "
                    "dry_run=false to apply it."
                ),
            },
        },
        ensure_ascii=False,
        indent=2,
    )


def _meal_plan_sources(
    recipe_ids: list[str],
    recipe_source: str,
) -> dict[str, list[str]]:
    """Partition IDs exactly as the Cookidoo calendar mutation will."""

    result: dict[str, list[str]] = {"official": [], "custom": []}
    for recipe_id in dict.fromkeys(recipe_ids):
        source = CookidooService._meal_plan_recipe_source(
            recipe_id,
            recipe_source,
        )
        result[source].append(recipe_id)
    return result


@mcp.tool()
async def connect_to_cookidoo() -> str:
    """
    Authenticate with Cookidoo and store the session.

    This tool must be called before using other Cookidoo tools. It will:
    1. Load your Cookidoo credentials from the .env file
    2. Normalize and validate the optional COOKIDOO_COUNTRY and
       COOKIDOO_LANGUAGE values (default ro/en)
    3. Authenticate with the matching Cookidoo platform localization
    4. Store the authenticated session for use by other tools

    Returns:
        str: Success message confirming connection

    Raises:
        ValueError: If credentials are missing from .env file
        Exception: If authentication fails
    """
    global _cookidoo_service, _cookidoo_api

    try:
        # Load credentials from .env file
        email, password = load_cookidoo_credentials()

        # Create Cookidoo service instance
        _cookidoo_service = CookidooService(email, password)

        # Authenticate and get API client
        _cookidoo_api = await _cookidoo_service.login()

        return f"Successfully connected to Cookidoo as {email}"

    except ValueError as e:
        return (
            f"Configuration Error: {str(e)}\n\n"
            "Check COOKIDOO_EMAIL and COOKIDOO_PASSWORD. If you set "
            "COOKIDOO_COUNTRY or COOKIDOO_LANGUAGE, use a Cookidoo-supported "
            "pair."
        )

    except Exception as e:
        # Authentication or other errors
        return f"Connection Failed: {str(e)}\n\nPlease check your credentials and try again."


@mcp.tool()
async def get_recipe_details(recipe_id: str) -> str:
    """
    Get detailed information about a specific recipe by its ID.

    Use this tool to get full details about a recipe for inspiration before creating
    your own custom recipe. You must be connected first using connect_to_cookidoo.

    Args:
        recipe_id: The Cookidoo recipe ID (e.g., "r59322", "r907015")

    Returns:
        str: Detailed recipe information including ingredients, steps, cooking time, etc.

    Raises:
        Exception: If not connected or if the recipe is not found
    """
    global _cookidoo_api

    try:
        # Check if connected
        if not _cookidoo_api:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        # Get recipe details
        recipe = await _cookidoo_api.get_recipe_details(recipe_id)

        # Format the results
        result = "Recipe Details:\n\n"
        result += f"Name: {recipe.name}\n"
        result += f"ID: {recipe.id}\n\n"

        if hasattr(recipe, "serving_size"):
            result += f"Servings: {recipe.serving_size}\n"

        if hasattr(recipe, "total_time"):
            result += f"Total Time: {recipe.total_time} minutes\n"

        if hasattr(recipe, "difficulty"):
            result += f"Difficulty: {recipe.difficulty}\n"

        result += "\n"

        # Ingredients
        if hasattr(recipe, "ingredients") and recipe.ingredients:
            result += "Ingredients:\n"
            for ingredient in recipe.ingredients:
                if hasattr(ingredient, "name"):
                    result += f"  • {ingredient.name}"
                    if hasattr(ingredient, "description") and ingredient.description:
                        result += f" - {ingredient.description}"
                    result += "\n"
            result += "\n"

        # Note: Cookidoo's API does not expose step-by-step instructions
        # for this endpoint, so no "Steps" section can be populated here.

        # Images
        if hasattr(recipe, "image") and recipe.image:
            result += f"Image: {recipe.image}\n"
        if hasattr(recipe, "thumbnail") and recipe.thumbnail:
            result += f"Thumbnail: {recipe.thumbnail}\n"

        # URL if available
        if hasattr(recipe, "url") and recipe.url:
            result += f"URL: {recipe.url}\n"

        return result

    except Exception as e:
        return f"Failed to get recipe details: {str(e)}"


@mcp.tool()
async def get_custom_recipe_details(recipe_id: str) -> str:
    """
    Get the full text content of a recipe in the account's custom recipes.

    Unlike get_recipe_details, this endpoint includes preparation instructions.
    It returns plain ingredient and instruction text; use the update tools to add
    or replace guided-cooking annotations.
    """
    global _cookidoo_api

    try:
        if not _cookidoo_api:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        recipe = await _cookidoo_api.get_custom_recipe(recipe_id)
        result = {
            "id": recipe.id,
            "name": recipe.name,
            "ingredients": recipe.ingredients,
            "steps": recipe.instructions,
            "tools": recipe.tools,
            "servings": recipe.serving_size,
            "prep_time_seconds": recipe.active_time,
            "total_time_seconds": recipe.total_time,
            "image": recipe.image,
            "thumbnail": recipe.thumbnail,
            "url": recipe.url,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Failed to get custom recipe details: {str(e)}"


@mcp.tool()
async def get_shopping_list_ingredients(
    recipe_id: str | None = None,
    include_owned: bool = False,
    include_additional_items: bool = True,
) -> str:
    """
    Get Cookidoo shopping-list ingredients grouped by recipe.

    Args:
        recipe_id: Optional exact recipe ID from the shopping list. Omit it to
            return every recipe.
        include_owned: Include ingredients already marked as owned. Defaults to
            false so grocery workflows receive only products still needed.
        include_additional_items: Include manually added shopping-list items.

    Returns:
        JSON with `recipes` (each containing its own ingredients), a convenient
        flat `ingredients` list carrying recipe_id/recipe_name, manual
        `additional_items`, and summary counts.
    """
    global _cookidoo_service

    try:
        if not _cookidoo_service:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        result = await _cookidoo_service.get_shopping_list_ingredients(
            recipe_id=recipe_id,
            include_owned=include_owned,
            include_additional_items=include_additional_items,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Failed to get shopping-list ingredients: {str(e)}"


@mcp.tool()
async def get_meal_plan_week(date: str) -> str:
    """
    Get Cookidoo's complete seven-day meal-plan window.

    Cookidoo normally omits empty days and returns custom recipes as bare IDs.
    This tool fills all seven days starting with the requested date and resolves
    custom recipe IDs to names, images, durations, and links. This matches the
    `?date=YYYY-MM-DD` parameter used by Cookidoo's web planner.

    Args:
        date: First day of the seven-day window, formatted YYYY-MM-DD.
    """
    global _cookidoo_service

    try:
        if not _cookidoo_service:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        result = await _cookidoo_service.get_meal_plan_week(
            _parse_calendar_date(date)
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Failed to get meal-plan week: {str(e)}"


@mcp.tool()
async def add_recipes_to_meal_plan(
    date: str,
    recipe_ids: str,
    recipe_source: Literal["auto", "official", "custom"] = "auto",
    dry_run: bool = False,
) -> str:
    """
    Add one or more recipes to a Cookidoo meal-plan day.

    Mixed official IDs (for example r460132) and custom recipe ULIDs are
    supported when recipe_source is auto. Separate IDs with commas, spaces, or
    newlines. The updated day is returned after Cookidoo confirms the change.

    Args:
        date: Target day in YYYY-MM-DD format.
        recipe_ids: One or more Cookidoo recipe IDs.
        recipe_source: auto, official, or custom.
        dry_run: Validate and preview the exact calendar change without
            sending it to Cookidoo.
    """
    global _cookidoo_service

    try:
        parsed_date = _parse_calendar_date(date)
        parsed_recipe_ids = _parse_recipe_ids(recipe_ids)
        sources = _meal_plan_sources(parsed_recipe_ids, recipe_source)
        if dry_run:
            return _dry_run_result(
                "add_recipes_to_meal_plan",
                "add recipes to meal plan",
                target={"date": parsed_date.isoformat()},
                changes={
                    "official_recipe_ids": sources["official"],
                    "custom_recipe_ids": sources["custom"],
                },
            )

        if not _cookidoo_service:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        result = await _cookidoo_service.add_meal_plan_recipes(
            parsed_date,
            parsed_recipe_ids,
            recipe_source,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Failed to add recipes to meal plan: {str(e)}"


@mcp.tool()
async def remove_recipe_from_meal_plan(
    date: str,
    recipe_id: str,
    recipe_source: Literal["auto", "official", "custom"] = "auto",
    dry_run: bool = False,
) -> str:
    """
    Remove one recipe from a Cookidoo meal-plan day.

    Args:
        date: Calendar day in YYYY-MM-DD format.
        recipe_id: Official or custom Cookidoo recipe ID.
        recipe_source: auto, official, or custom.
        dry_run: Validate and preview the removal without sending it to
            Cookidoo.
    """
    global _cookidoo_service

    try:
        parsed_date = _parse_calendar_date(date)
        normalized_recipe_id = _require_recipe_id(recipe_id)
        source = CookidooService._meal_plan_recipe_source(
            normalized_recipe_id,
            recipe_source,
        )
        if dry_run:
            return _dry_run_result(
                "remove_recipe_from_meal_plan",
                "remove recipe from meal plan",
                target={
                    "date": parsed_date.isoformat(),
                    "recipe_id": normalized_recipe_id,
                    "recipe_source": source,
                },
                changes={"remove": True},
                notes=[
                    "The recipe itself will remain in Cookidoo; only this "
                    "calendar entry will be removed."
                ],
            )

        if not _cookidoo_service:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        result = await _cookidoo_service.remove_meal_plan_recipe(
            parsed_date,
            normalized_recipe_id,
            recipe_source,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Failed to remove recipe from meal plan: {str(e)}"


@mcp.tool()
async def move_recipe_in_meal_plan(
    recipe_id: str,
    from_date: str,
    to_date: str,
    recipe_source: Literal["auto", "official", "custom"] = "auto",
    dry_run: bool = False,
) -> str:
    """
    Move one recipe from one Cookidoo calendar day to another.

    The recipe is added to the target first and then removed from the source.
    If removal fails, a newly-added target entry is rolled back.

    Args:
        recipe_id: Official or custom Cookidoo recipe ID.
        from_date: Existing day in YYYY-MM-DD format.
        to_date: New day in YYYY-MM-DD format.
        recipe_source: auto, official, or custom.
        dry_run: Validate and preview both calendar operations without sending
            either one to Cookidoo.
    """
    global _cookidoo_service

    try:
        normalized_recipe_id = _require_recipe_id(recipe_id)
        parsed_from_date = _parse_calendar_date(from_date)
        parsed_to_date = _parse_calendar_date(to_date)
        source = CookidooService._meal_plan_recipe_source(
            normalized_recipe_id,
            recipe_source,
        )
        if dry_run:
            is_same_day = parsed_from_date == parsed_to_date
            return _dry_run_result(
                "move_recipe_in_meal_plan",
                (
                    "leave recipe on the same meal-plan day"
                    if is_same_day
                    else "move recipe between meal-plan days"
                ),
                target={
                    "recipe_id": normalized_recipe_id,
                    "recipe_source": source,
                },
                changes={
                    "from_date": parsed_from_date.isoformat(),
                    "to_date": parsed_to_date.isoformat(),
                    "add_to_target_first": not is_same_day,
                    "remove_from_source_after_add": not is_same_day,
                },
                notes=(
                    ["No calendar change is needed because both dates match."]
                    if is_same_day
                    else [
                        "If source removal fails after the target addition, "
                        "the service attempts to roll back the target entry."
                    ]
                ),
            )

        if not _cookidoo_service:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        result = await _cookidoo_service.move_meal_plan_recipe(
            normalized_recipe_id,
            parsed_from_date,
            parsed_to_date,
            recipe_source,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Failed to move recipe in meal plan: {str(e)}"


@mcp.tool()
async def copy_recipe_to_custom(
    recipe_id: str,
    servings: int = 4,
    dry_run: bool = False,
) -> str:
    """
    Copy an official Cookidoo recipe into the account's custom recipes.

    This is the supported way to obtain the full ingredients and instructions of
    an official recipe before translating or editing it.

    Set dry_run to true to validate and preview creation of the private copy
    without changing the account.
    """
    global _cookidoo_api

    try:
        normalized_recipe_id = _require_recipe_id(recipe_id)
        if servings < 1 or servings > 20:
            return "Invalid servings: expected a value from 1 to 20."
        if dry_run:
            return _dry_run_result(
                "copy_recipe_to_custom",
                "create private custom-recipe copy",
                target={"official_recipe_id": normalized_recipe_id},
                changes={
                    "create_custom_recipe": True,
                    "servings": servings,
                    "copy_full_ingredients_and_instructions": True,
                },
                notes=[
                    "This creates a new private recipe; it does not modify the "
                    "official Cookidoo recipe."
                ],
            )
        if not _cookidoo_api:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        recipe = await _cookidoo_api.add_custom_recipe_from(
            normalized_recipe_id,
            servings,
        )
        result = {
            "id": recipe.id,
            "name": recipe.name,
            "ingredients": recipe.ingredients,
            "steps": recipe.instructions,
            "tools": recipe.tools,
            "servings": recipe.serving_size,
            "prep_time_seconds": recipe.active_time,
            "total_time_seconds": recipe.total_time,
            "image": recipe.image,
            "thumbnail": recipe.thumbnail,
            "url": recipe.url,
        }
        return (
            "Recipe copied to custom recipes successfully!\n\n"
            f"{json.dumps(result, ensure_ascii=False, indent=2)}"
        )
    except Exception as e:
        return f"Failed to copy recipe: {str(e)}"


@mcp.tool()
async def generate_recipe_structure(
    name: str,
    ingredients: str,
    steps: str,
    servings: int = 4,
    prep_time: int = 30,
    total_time: int = 60,
    hints: str = "",
) -> str:
    """
    Generate and validate a recipe structure ready for upload to Cookidoo.

    This tool helps you structure your recipe data properly before uploading.
    It validates all fields and returns a JSON structure that can be used with
    the upload_custom_recipe tool.

    Always put weighing/adding ingredients in one step and the subsequent
    chopping, mixing, cooking, or kneading action in a separate step.

    Args:
        name: Recipe name (required)
        ingredients: Ingredients list, one per line or comma-separated
        steps: Cooking steps, one per line or numbered. Ingredient additions
            and machine actions must be on separate lines.
        servings: Number of servings (default: 4, range: 1-20)
        prep_time: Preparation time in minutes (default: 30)
        total_time: Total cooking time in minutes (default: 60)
        hints: Optional cooking tips, one per line or comma-separated

    Returns:
        str: Validated recipe structure in JSON format, ready for upload
    """
    try:
        # Parse ingredients (split by newlines or commas)
        ingredients_list = [
            ing.strip()
            for ing in (
                ingredients.split("\n")
                if "\n" in ingredients
                else ingredients.split(",")
            )
            if ing.strip()
        ]

        # Parse steps (split by newlines or numbered steps)
        steps_list = [
            step.strip().lstrip("0123456789.)-• ")
            for step in steps.split("\n")
            if step.strip()
        ]

        # Parse hints if provided
        hints_list = None
        if hints:
            hints_list = [
                hint.strip()
                for hint in (hints.split("\n") if "\n" in hints else hints.split(","))
                if hint.strip()
            ]

        # Create and validate the recipe using Pydantic
        recipe = CustomRecipe(
            name=name,
            ingredients=ingredients_list,
            steps=steps_list,
            servings=servings,
            prep_time=prep_time,
            total_time=total_time,
            hints=hints_list,
        )

        # Return formatted JSON
        recipe_json = recipe.model_dump_json(indent=2)

        return f"Recipe structure validated successfully!\n\n{recipe_json}\n\nYou can now use this with 'upload_custom_recipe'."

    except Exception as e:
        return f"Validation failed: {str(e)}\n\nPlease check your recipe data and try again."


@mcp.tool()
async def validate_guided_recipe_structure(recipe_json: str) -> str:
    """
    Validate a complete custom recipe, including guided-cooking annotations.

    Step annotations use Cookidoo's exact request schema:
    - TTS: manual time, temperature, speed, and direction
    - MODE: Dough, Blend, Turbo, Warm Up, Rice Cooker, Steaming, or Browning
    - INGREDIENT: a linked ingredient for on-device weighing

    INGREDIENT annotations must be in ingredient-only steps. TTS and MODE
    annotations belong in following, separate machine-action steps.

    Every annotation position is a zero-based JavaScript UTF-16 range into its
    enclosing step text. VOLUME positions use their enclosing ingredient text.
    Use calculate_annotation_position instead of normal Python string indexes.
    """
    try:
        recipe_data = json.loads(recipe_json)
        recipe = CustomRecipe(**recipe_data)
        return (
            "Guided recipe structure validated successfully!\n\n"
            f"{recipe.model_dump_json(indent=2, exclude_none=True)}"
        )
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"
    except Exception as e:
        return f"Validation failed: {str(e)}"


@mcp.tool()
async def calculate_annotation_position(
    text: str,
    marker: str,
    occurrence: int = 1,
) -> str:
    """
    Calculate Cookidoo's offset and length for text inside a recipe step.

    Cookidoo uses JavaScript UTF-16 character positions, which differ from normal
    Python string indexes when text before the marker contains emoji. Use this
    tool for every TTS, MODE, INGREDIENT, and VOLUME annotation.
    """
    try:
        position = position_for(text, marker, occurrence)
        return position.model_dump_json()
    except Exception as e:
        return f"Failed to calculate annotation position: {str(e)}"


@mcp.tool()
async def update_custom_recipe_steps(
    recipe_id: str,
    steps_json: str,
    dry_run: bool = False,
) -> str:
    """
    Replace a custom recipe's preparation steps.

    steps_json must be a JSON array. Each item may be plain step text or a STEP
    object containing TTS, MODE, and/or INGREDIENT annotations. This partial
    update preserves the recipe's other fields.

    Always use separate steps for weighing/adding ingredients and for the
    following cooking, mixing, chopping, or kneading action. A single step
    cannot contain both INGREDIENT and TTS/MODE annotations.

    Set dry_run to true to validate and return the full replacement step list
    without patching Cookidoo.
    """
    global _cookidoo_service, _cookidoo_api

    try:
        normalized_recipe_id = _require_recipe_id(recipe_id)
        steps = _steps_adapter.validate_python(json.loads(steps_json))
        if not steps:
            return "Invalid steps: at least one step is required."
        if dry_run:
            return _dry_run_result(
                "update_custom_recipe_steps",
                "replace custom recipe steps",
                target={"custom_recipe_id": normalized_recipe_id},
                changes={
                    "replace_all_steps": True,
                    "step_count": len(steps),
                    "steps": _jsonable_recipe_items(steps),
                },
                notes=[
                    "Ingredients and all other recipe fields will be preserved."
                ],
            )
        if not _cookidoo_service or not _cookidoo_api:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        await _cookidoo_service.update_custom_recipe_steps(
            normalized_recipe_id,
            steps,
        )
        return (
            f"Custom recipe {normalized_recipe_id} steps updated successfully."
        )
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"
    except Exception as e:
        return f"Failed to update custom recipe steps: {str(e)}"


@mcp.tool()
async def update_custom_recipe_ingredients(
    recipe_id: str,
    ingredients_json: str,
    dry_run: bool = False,
) -> str:
    """
    Replace a custom recipe's ingredients.

    ingredients_json must be a JSON array. Each item may be plain ingredient text
    or an INGREDIENT object containing a VOLUME annotation. This partial update
    preserves the recipe's other fields.

    Set dry_run to true to validate and return the full replacement ingredient
    list without patching Cookidoo.
    """
    global _cookidoo_service, _cookidoo_api

    try:
        normalized_recipe_id = _require_recipe_id(recipe_id)
        ingredients = _ingredients_adapter.validate_python(json.loads(ingredients_json))
        if not ingredients:
            return "Invalid ingredients: at least one ingredient is required."
        if dry_run:
            return _dry_run_result(
                "update_custom_recipe_ingredients",
                "replace custom recipe ingredients",
                target={"custom_recipe_id": normalized_recipe_id},
                changes={
                    "replace_all_ingredients": True,
                    "ingredient_count": len(ingredients),
                    "ingredients": _jsonable_recipe_items(ingredients),
                },
                notes=[
                    "Preparation steps and all other recipe fields will be "
                    "preserved."
                ],
            )
        if not _cookidoo_service or not _cookidoo_api:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        await _cookidoo_service.update_custom_recipe_ingredients(
            normalized_recipe_id,
            ingredients,
        )
        return (
            f"Custom recipe {normalized_recipe_id} ingredients updated "
            "successfully."
        )
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"
    except Exception as e:
        return f"Failed to update custom recipe ingredients: {str(e)}"


@mcp.tool()
async def upload_custom_recipe_image(
    recipe_id: str,
    image_path: str,
    dry_run: bool = False,
) -> str:
    """
    Upload a local image and attach it to a custom Cookidoo recipe.

    The file is converted to JPEG when necessary (including WebP), uploaded
    through Cookidoo's signed customer-recipe image flow, and attached with
    isImageOwnedByUser enabled. Cookidoo accepts images up to 10 MB.

    Args:
        recipe_id: The custom Cookidoo recipe ID.
        image_path: Absolute or user-relative path to a local image file.
        dry_run: Read and validate the local image, then preview the upload and
            recipe attachment without sending either request.
    """
    global _cookidoo_service, _cookidoo_api

    try:
        normalized_recipe_id = _require_recipe_id(recipe_id)
        if dry_run:
            image_bytes, content_type, filename = (
                CookidooService._prepare_custom_recipe_image(image_path)
            )
            return _dry_run_result(
                "upload_custom_recipe_image",
                "upload and attach custom recipe image",
                target={"custom_recipe_id": normalized_recipe_id},
                changes={
                    "source_path": image_path,
                    "normalized_filename": filename,
                    "content_type": content_type,
                    "normalized_size_bytes": len(image_bytes),
                    "upload_to_customer_recipe_storage": True,
                    "attach_as_user_owned_image": True,
                },
                notes=[
                    "The preview reads and converts the local file in memory "
                    "but does not upload it or patch the recipe."
                ],
            )
        if not _cookidoo_service or not _cookidoo_api:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        result = await _cookidoo_service.upload_custom_recipe_image(
            normalized_recipe_id,
            image_path,
        )
        return (
            "Custom recipe image uploaded successfully!\n\n"
            f"{json.dumps(result, ensure_ascii=False, indent=2)}"
        )
    except Exception as e:
        return f"Failed to upload custom recipe image: {str(e)}"


@mcp.tool()
async def upload_custom_recipe(
    recipe_json: str,
    dry_run: bool = False,
) -> str:
    """
    Upload a custom recipe to your Cookidoo account.

    This tool creates a brand new recipe from scratch on your Cookidoo account.
    Use 'generate_recipe_structure' first to validate your recipe data, then
    pass the resulting JSON to this tool.

    Args:
        recipe_json: The validated recipe JSON from generate_recipe_structure
        dry_run: Validate and preview the complete new recipe without creating
            it in Cookidoo.

    Returns:
        str: Success message with the created recipe ID
    """
    global _cookidoo_service, _cookidoo_api

    try:
        # Parse and validate the recipe JSON
        try:
            recipe_data = json.loads(recipe_json)
            recipe = CustomRecipe(**recipe_data)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}"
        except Exception as e:
            return f"Invalid recipe data: {str(e)}"

        if dry_run:
            return _dry_run_result(
                "upload_custom_recipe",
                "create private custom recipe",
                target={"collection": "Cookidoo custom recipes"},
                changes={
                    "create_custom_recipe": True,
                    "recipe": recipe.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                },
                notes=[
                    "A successful apply creates a new private recipe and does "
                    "not modify an existing recipe."
                ],
            )

        # Check if connected only when applying the validated mutation.
        if not _cookidoo_service or not _cookidoo_api:
            return "Not connected. Please run 'connect_to_cookidoo' first."

        # Create the recipe using our custom service method
        recipe_id = await _cookidoo_service.create_custom_recipe(
            name=recipe.name,
            ingredients=recipe.ingredients,
            steps=recipe.steps,
            servings=recipe.servings,
            prep_time=recipe.prep_time,
            total_time=recipe.total_time,
            hints=recipe.hints,
        )

        # Get localization for URL
        localization = _cookidoo_api.localization
        recipe_url = f"https://{localization.url}/recipes/custom-recipes/{recipe_id}"

        return f"Recipe '{recipe.name}' created successfully!\n\nRecipe ID: {recipe_id}\nURL: {recipe_url}\n\nYour recipe is now saved in your Cookidoo account!"

    except Exception as e:
        return f"Upload failed: {str(e)}"
