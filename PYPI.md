# Cookidoo MCP

Connect an AI assistant to Cookidoo for recipe creation and translation,
guided Thermomix settings, customer-recipe images, shopping lists, and weekly
meal planning.

> This is an unofficial community project. It is not affiliated with Vorwerk,
> Thermomix, or Cookidoo.

## Run it

Python 3.12 or newer is required. Provide your Cookidoo login through the
`COOKIDOO_EMAIL` and `COOKIDOO_PASSWORD` environment variables, then run:

```bash
uvx cookidoo-mcp
```

To keep credentials out of an MCP client's JSON configuration, point the
launcher at a local file containing `COOKIDOO_EMAIL` and
`COOKIDOO_PASSWORD`. You may also set `COOKIDOO_COUNTRY` and
`COOKIDOO_LANGUAGE`; they default to Cookidoo International English
(`ro` + `en`):

```bash
uvx cookidoo-mcp --env-file /absolute/path/to/.env
```

The command starts a local MCP server over stdio. Recipe, image, and calendar
mutations support a `dry_run` preview so an assistant can show the exact planned
change before applying it. See the
[guided setup wizard](https://vitaliemiron.github.io/cookidoo-mcp/setup/), the
[friendly setup guide](https://vitaliemiron.github.io/cookidoo-mcp/docs/), or
the [source repository](https://github.com/vitaliemiron/cookidoo-mcp) for
client configuration, security notes, examples, and the complete tool
reference.

<!-- mcp-name: io.github.vitaliemiron/cookidoo-mcp -->
