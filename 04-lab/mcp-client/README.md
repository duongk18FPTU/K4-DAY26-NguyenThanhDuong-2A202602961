# Weather Agent - Google ADK with MCP Server

AI agent built with **Google Agent Development Kit (ADK)** that uses tools from a local **MCP server** via Streamable HTTP transport.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   User Browser  │ ───> │  ADK Web UI      │ ───> │  Weather Agent      │
│   localhost:8000│      │  (Google ADK)    │      │  (Agent with MCP)   │
└─────────────────┘      └──────────────────┘      └─────────────────────┘
                                                             │
                                                             │ Streamable HTTP
                                                             ▼
                                                   ┌─────────────────────┐
                                                   │  MCP Server         │
                                                   │  localhost:8085/mcp │
                                                   │  FastMCP + Tools    │
                                                   └─────────────────────┘
                                                             │
                                                             ▼
                                                   ┌─────────────────────┐
                                                   │  WeatherAPI.com     │
                                                   └─────────────────────┘
```

## Features

- **Remote MCP Tools**: Connects to MCP server via Streamable HTTP
- **3 Weather Tools**:
  - `get_current_weather(city)` - Real-time weather conditions
  - `get_forecast(city, days)` - Weather forecast up to 3 days
  - `health_check()` - Server health verification
- **Web Interface**: UI via ADK web
- **Streaming Responses**: Real-time AI responses

## Quick Start

For Windows / PowerShell, see [SETUP-WINDOWS.md](../../SETUP-WINDOWS.md).

### 1. Start the MCP Server

```bash
cd ../mcp-server
export WEATHERAPI_KEY="your_weatherapi_key"
uv run python weather.py
```

### 2. Setup Environment

```bash
cd mcp-client

# Fill GOOGLE_API_KEY in .env (copy .env.example only if .env does not exist).
# Get free key from: https://aistudio.google.com/apikey
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Run the Agent

```bash
uv run adk web
```

### 5. Use the Agent

1. Open browser: http://localhost:8000
2. Select `weather_agent` from dropdown
3. Ask questions like:
   - "What's the weather in Brisbane?"
   - "Give me a 3-day forecast for Tokyo"
   - "How's the weather in New York?"

## Project Structure

```
mcp-client/
├── weather_agent/
│   ├── agent.py           # Main agent with MCP connection
│   └── __init__.py
├── pyproject.toml
├── .env                   # Environment variables (create this)
└── README.md
```

## Configuration

### Agent Configuration

In `weather_agent/agent.py`:

```python
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    timeout=30.0,
)

root_agent = Agent(
    name="weather_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    tools=[weather_tools],
)
```

## Troubleshooting

### Agent won't connect to MCP server

1. **404 errors from MCP**: Wrong MCP endpoint or port
   - Ensure the MCP server is running on port 8085
   - Check `MCP_SERVER_URL` (env var / `.env`, default `http://localhost:8085/mcp`)

2. **400/405/406 from a plain browser GET**: This does not validate MCP.
   - Run `uv run python verify_setup.py` to perform the actual MCP handshake.

3. **Timeout errors**: Server not started
   - Start the MCP server first, then the ADK client

### Gemini model errors

- Gemini 404 for `gemini-2.5-flash`: use `GEMINI_MODEL=gemini-3.5-flash-lite`.
  [Google restricts Gemini 2.5 access for new users](https://ai.google.dev/gemini-api/docs/deprecations/).
- Gemini 503: temporary model capacity issue; try again later or configure
  another available model in `GEMINI_MODEL`, then restart ADK web.
- Gemini 429: check the quota and rate limits of the API key's project.

The agent keeps its MCP toolset; connection failures are reported instead of
creating a tool-free agent that could invent weather data.

## Environment Variables

Create `.env` file:
```bash
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_GENAI_USE_VERTEXAI=FALSE
MCP_SERVER_URL=http://localhost:8085/mcp
GEMINI_MODEL=gemini-3.5-flash-lite
```

## Verification

```bash
uv run python verify_setup.py
uv run python verify_setup.py --live
```

`--live` exercises real WeatherAPI data and the Gemini tool-calling loop;
it uses API quota and prints the final Vietnamese answer.

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [WeatherAPI](https://www.weatherapi.com/)
