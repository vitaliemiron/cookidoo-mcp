# Cookidoo MCP setup

Cookidoo MCP is a local STDIO server. It runs through `uvx` and reads the
Cookidoo login from a private environment file. Python 3.12 or newer is
required by the package; `uv` can obtain a compatible Python runtime when
needed.

Interactive generator:
<https://vitaliemiron.github.io/cookidoo-mcp/setup/>

## 1. Install uv

The current commands from the official uv installation guide are:

macOS or Linux:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Package-manager alternatives are documented at
<https://docs.astral.sh/uv/getting-started/installation/>.

## 2. Create a private credential file

Use an absolute path. Do not keep this file in a repository or shared folder.

Example content:

```dotenv
COOKIDOO_EMAIL=your-login
COOKIDOO_PASSWORD=your-password
COOKIDOO_COUNTRY=ro
COOKIDOO_LANGUAGE=en
```

The login can be an email address or the phone-number login accepted by the
account. Do not put the real values in MCP client JSON, screenshots, issues, or
chat messages. The `ro`/`en` locale defaults preserve the project's existing
international setup. Change both locale values together only to a valid
Cookidoo country/language pairing for the account.

## 3. Connect a client

Replace `/absolute/path/to/cookidoo.env` with the absolute path created above.

### Codex

The Codex CLI, IDE extension, and desktop app share MCP configuration on the
same Codex host. Add the server with:

```sh
codex mcp add cookidoo -- uvx cookidoo-mcp --env-file /absolute/path/to/cookidoo.env
codex mcp list
```

In the Codex app or IDE extension, the same STDIO server can be added through
**Settings > MCP servers > Add server**. Use `uvx` as the command and these
arguments:

```text
cookidoo-mcp
--env-file
/absolute/path/to/cookidoo.env
```

Primary source:
<https://developers.openai.com/codex/mcp/>

### Claude Desktop

Open **Settings > Developer > Edit Config**. The file locations documented by
the official MCP guide are:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add:

```json
{
  "mcpServers": {
    "cookidoo": {
      "command": "uvx",
      "args": [
        "cookidoo-mcp",
        "--env-file",
        "/absolute/path/to/cookidoo.env"
      ]
    }
  }
}
```

Fully quit and reopen Claude Desktop after saving. The official desktop
application is documented for macOS and Windows, not Linux.

Primary source:
<https://modelcontextprotocol.io/docs/develop/connect-local-servers>

### VS Code

Run **MCP: Open User Configuration** from the Command Palette and add:

```json
{
  "servers": {
    "cookidoo": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "cookidoo-mcp",
        "--env-file",
        "/absolute/path/to/cookidoo.env"
      ]
    }
  }
}
```

Then run **MCP: List Servers**, start `cookidoo`, and use **Show Output** if the
connection reports an error. A user-profile server runs locally. If VS Code is
connected to WSL, SSH, or a container and the server should run there, use that
remote environment's MCP configuration instead.

Primary sources:

- <https://code.visualstudio.com/docs/agent-customization/mcp-servers>
- <https://code.visualstudio.com/docs/agents/reference/mcp-configuration>

## Windows verification boundary

The package installation, installed command, server import, and private
environment-file loading are tested on GitHub's real `windows-latest` runner
for every change. The PowerShell installer and Codex, Claude Desktop, and
VS Code configuration formats above are also checked against current primary
documentation.

Individual client screens and configuration locations can still move between
app versions. Describe the Windows package path as CI-verified, and the client
UI instructions as documentation-verified.

## Troubleshooting

1. Confirm `uvx` is on the same environment `PATH` used by the AI client.
2. Confirm the environment-file path is absolute and the file contains both
   variable names.
3. Restart the client after changing its MCP configuration.
4. Use the client's MCP list or output view to read the actual startup error.
5. Restart the MCP server after changing its configuration because the process
   keeps authenticated state in memory.
