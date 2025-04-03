# Blues Notehub MCP Server (Python)

This is a Model Context Protocol (MCP) server implementation that interacts with the Blues Notehub API using the official `notehub_py` SDK. It allows large language models to interface with your Blues Notehub projects, devices, and data.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. It standardizes how LLMs interact with external tools and services.

## Prerequisites

- Python 3.8 or higher
- A Blues Notehub account (https://notehub.io)
- Your Notehub account username (email) and password

## Installation

### Option 1: Using pip (recommended)

1. Clone or download this repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Using uv (faster alternative)

1. Install uv following the instructions at https://github.com/astral-sh/uv
2. Create the environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

## Running the Server

Start the server with:

```bash
python notehub.py
```

The MCP server will run using stdio as the transport layer, which is the standard transport for most MCP clients.

## Authentication Method

This server uses X-Session-Token authentication with the Notehub API. You will need to provide your Notehub username (email) and password when using the tools. The server will automatically:

1. Obtain a session token using the `/auth/login` endpoint
2. Cache the token for up to 29 minutes (tokens expire after 30 minutes)
3. Automatically handle token refreshing when needed

## Connecting to an MCP Client

### Claude for Desktop (macOS/Windows)

1. Install [Claude for Desktop](https://claude.ai/desktop)
2. Update your Claude Desktop configuration file:

For macOS:
```bash
mkdir -p ~/Library/Application\ Support/Claude/
```

Edit or create `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "notehub": {
      "command": "python",
      "args": ["/path/to/your/notehub.py"],
      "availableTo": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-5-sonnet-20240307", "claude-3-haiku-20240307"]
    }
  }
}
```

For Windows, the config file is located at:
`%APPDATA%\Claude\claude_desktop_config.json`

3. Restart Claude for Desktop

### Custom MCP Client

If you're building a custom MCP client, you'll need to:

1. Start this server as a child process
2. Communicate with it using stdin/stdout following the MCP protocol
3. Configure your client to discover the tools this server exposes

## Available Tools

This MCP server exposes the following tools:

1. `get-projects` - Get all accessible Notehub projects
2. `get-project-devices` - Get all devices for a specific project (with optional filtering)
3. `get-project-events` - Get all events for a specific project (with optional filtering)
4. `send-note` - Send a note to a specific device

## Usage Examples

When using with Claude for Desktop, you can ask questions like:

- "Can you show me all my Notehub projects? My username is example@email.com and my password is mypassword123"
- "Fetch all devices from my project app:12345 using my Notehub username (example@email.com) and password"
- "Get the last 10 events from device dev:12345 in project app:12345"
- "Send a note to device dev:12345 in project app:12345 with the following payload: {"message": "Hello from MCP"}"

## Security Considerations

- This server requires your Notehub username and password to function.
- Never share your configuration file containing paths or credentials.
- The MCP protocol runs locally, so your credentials are not sent to remote servers.
- The server implements token caching for better performance while maintaining security.
- If your Notehub account was created using "Sign in with GitHub", you'll need to set a password in the Account settings panel in Notehub.io first.

## Troubleshooting

If you encounter issues:

1. Check the logs for any error messages:
   - macOS: `~/Library/Logs/Claude/mcp-server-notehub.log`
   - Windows: `%APPDATA%\Claude\Logs\mcp-server-notehub.log`

2. Verify your Notehub credentials are correct.

3. If you signed up with GitHub, make sure you've set a password in your Notehub account settings.

4. Make sure the server is running with the correct Python version.

5. Ensure both `mcp` and `notehub_py` packages are properly installed.

## Extending the Server

To add more capabilities to this server:

1. Extend the functions with additional Notehub API features
2. Register new tools with `@mcp.tool()` decorator
3. Add more filtering options to existing tools
4. Implement additional error handling and reporting

## License

MIT