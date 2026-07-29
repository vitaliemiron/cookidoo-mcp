# Planning and shopping automation

## Meal planning

`get_meal_plan_week(date)` reads the seven-day Cookidoo planning window containing an ISO date. Recipes can be added, removed, or moved using official or custom recipe IDs.

Use this safe sequence:

1. Read the current week.
2. Identify the exact date and recipe occurrence.
3. Call the mutation with `dry_run=true` and review the exact JSON preview.
4. Repeat the same scoped call with `dry_run=false`.
5. Read the week again and verify it.

Use `recipe_source="auto"` unless there is a reason to force `official` or `custom`.
A dry run validates dates, IDs, source inference, and operation order without
changing the calendar.

## Shopping list

`get_shopping_list_ingredients` returns structured ingredients for either the full Cookidoo list or a single recipe. Owned items and user-added items can be included or excluded.

This output is suitable for handing to another grocery-search or cart integration. Cookidoo MCP does not choose store products or place purchases itself.
