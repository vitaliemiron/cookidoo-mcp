# Cookidoo MCP Server

[![Unit tests](https://github.com/vitaliemiron/cookidoo-mcp/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/vitaliemiron/cookidoo-mcp/actions/workflows/unit-tests.yml)
[![Cookidoo live API](https://github.com/vitaliemiron/cookidoo-mcp/actions/workflows/live-api.yml/badge.svg)](https://github.com/vitaliemiron/cookidoo-mcp/actions/workflows/live-api.yml)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-f5b942)](https://vitaliemiron.github.io/cookidoo-mcp/)

An MCP (Model Context Protocol) server for interacting with the Thermomix Cookidoo platform, built with `fastmcp`.

> **Disclaimer:** This is an unofficial project. The developers are not affiliated with, endorsed by, or connected to Cookidoo, Vorwerk, Thermomix, or any of their subsidiaries or trademarks.

Explore the [documentation and project story](https://vitaliemiron.github.io/cookidoo-mcp/),
or jump directly to the [complete tool reference](https://vitaliemiron.github.io/cookidoo-mcp/docs/tools/).
AI clients can start with [`llms.txt`](https://vitaliemiron.github.io/cookidoo-mcp/llms.txt)
or the structured [`tools.json`](https://vitaliemiron.github.io/cookidoo-mcp/tools.json).

## Features

- **Authentication**: Connect to your Cookidoo account securely
- **Recipe Details**: Fetch detailed recipe information by ID
- **Shopping List**: Read needed ingredients grouped by their source recipe
- **Meal Planning**: Read complete weeks and add, remove, or move recipes on
  the Cookidoo calendar
- **Recipe Copying**: Copy official recipes to obtain their full instructions
- **Recipe Generation**: Structure new custom recipes
- **Recipe Upload**: Upload custom recipes to your Cookidoo account
- **Recipe Images**: Convert, upload, and attach local images to custom recipes
- **Guided Cooking**: Add time, temperature, speed, modes, and ingredient weighing
- **Clear Step Separation**: Keep ingredient weighing/adding separate from
  cooking, mixing, chopping, and kneading actions

## Setup

Python 3.12 or newer is required by the Cookidoo API dependency.

1. **Clone the repository and navigate to the project directory**

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your Cookidoo credentials
   ```

5. **Run the MCP server:**
   ```bash
   fastmcp run server.py
   ```

## Available Tools

- `connect_to_cookidoo` - Authenticate with Cookidoo
- `get_recipe_details` - Get detailed recipe by ID
- `get_custom_recipe_details` - Read full ingredients and steps from a custom recipe
- `get_shopping_list_ingredients` - Read shopping-list ingredients grouped by recipe, optionally filter by recipe ID, and include ownership state/manual items
- `get_meal_plan_week` - Read the complete seven-day window beginning on a requested date and resolve custom recipe IDs to full details
- `add_recipes_to_meal_plan` - Add one or more official and/or custom recipes to a calendar day
- `remove_recipe_from_meal_plan` - Remove an official or custom recipe from a calendar day
- `move_recipe_in_meal_plan` - Move a recipe between days with rollback if the source removal fails
- `copy_recipe_to_custom` - Copy an official recipe into custom recipes
- `generate_recipe_structure` - Structure a new recipe
- `validate_guided_recipe_structure` - Validate guided-cooking annotation JSON
- `calculate_annotation_position` - Calculate UTF-16 offsets for annotations
- `upload_custom_recipe` - Upload a recipe to Cookidoo
- `upload_custom_recipe_image` - Convert and attach a local image to a custom recipe
- `update_custom_recipe_steps` - Replace steps and guided-cooking annotations
- `update_custom_recipe_ingredients` - Replace ingredients and structured amounts

See [`examples/guided_recipe.json`](examples/guided_recipe.json) for a verified
ingredient-weighing, TTS, temperature, reverse-speed, and Dough mode payload.
The server requires ingredient annotations and machine-action annotations to be
placed in separate consecutive steps.

## Testing and API monitoring

Install the development dependencies and run the unit suite:

```bash
pip install -r requirements-dev.txt
pytest -m "not live"
```

The `Cookidoo live API` GitHub Actions workflow runs daily, after relevant
changes reach `main`, and on manual dispatch. It checks authenticated login,
official recipe details, the shopping list, meal planning, image-upload
signatures, and a temporary custom-recipe copy/PATCH/delete lifecycle.

Configure these GitHub Actions repository secrets:

- `COOKIDOO_EMAIL`
- `COOKIDOO_PASSWORD`

The write test always deletes its temporary custom recipe in a `finally`
cleanup. If a live run fails, the workflow opens or updates a
`Cookidoo live API regression` issue. It closes that issue automatically after
the API tests recover.

## Acknowledgments

This project is built on top of the [cookidoo-api](https://github.com/miaucl/cookidoo-api), which provides the Python interface to interact with the Cookidoo platform. Special thanks for making this integration possible!

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
