# Get Cookidoo shopping-list ingredients by recipe

Last verified: 2026-07-29.

Call `get_shopping_list_ingredients` with the exact recipe ID after that recipe
is present in the Cookidoo shopping list. By default, the tool excludes
ingredients marked as already owned.

The account's current Cookidoo shopping list is the source of truth. Filtering
does not synthesize ingredients from an arbitrary catalog recipe. If the
requested ID is absent, the tool reports the available recipe IDs.

## Workflow

1. Read the whole list first when the intended recipe ID is uncertain.
2. Filter by exact `recipe_id`.
3. Leave `include_owned=false` for items still needed.
4. Set `include_additional_items=false` when manual household items are not
   part of the task.
5. Preserve recipe ID, recipe name, ingredient description, quantity text, and
   ownership state during any downstream handoff.

The response contains recipe groups, a flat ingredient list retaining recipe
context, optional manual items, and summary counts. Cookidoo MCP does not
search retailer products or change a cart; use a separate store-specific MCP
and report unmatched or ambiguous products separately.

Human guide:
https://vitaliemiron.github.io/cookidoo-mcp/use-cases/cookidoo-shopping-list-by-recipe/
