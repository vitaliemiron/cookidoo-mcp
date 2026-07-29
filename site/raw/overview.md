# Cookidoo MCP overview

Cookidoo MCP is an unofficial FastMCP server that lets an AI assistant work with a user's own Cookidoo account.

It was created to reduce the repetitive parts of meal planning without removing the personal parts: choosing food, adapting it to taste, cooking, and sharing it. The assistant can help copy and translate recipes, make instructions clearer, create guided Thermomix actions, organize My Week, and retrieve ingredients for shopping.

## What it can do

- Read official recipe metadata and ingredients.
- Copy an official recipe into private recipes to access its full steps.
- Create, translate, and update custom recipes.
- Upload user-owned recipe images.
- Structure weighing and Thermomix actions for guided cooking.
- Read the shopping list.
- Read and edit a rolling seven-day meal plan.

## What it does not promise

This is not an official Vorwerk integration. It relies on undocumented endpoints and can require maintenance after Cookidoo changes. Exact time savings depend on each person's planning and cooking workflow.

## Start

Python 3.12 or newer is required. With `uv` installed, keep credentials in a
private local file and start the published stdio server without cloning:

```bash
uvx cookidoo-mcp --env-file /absolute/path/to/cookidoo-mcp.env
```

Use the same command and arguments in an MCP client. Read the repository README
for source-development setup, then use the [tool reference](../docs/tools/) for
available operations.
