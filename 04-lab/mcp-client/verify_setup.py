#!/usr/bin/env python3
"""Verify setup; --live also calls WeatherAPI and Gemini through ADK."""

import argparse
import asyncio
import importlib
import logging
import os
from pathlib import Path
import sys
import uuid
from contextlib import aclosing

BASE_DIR = Path(__file__).resolve().parent
EXPECTED_TOOLS = {"get_current_weather", "get_forecast", "health_check"}


def check_dependencies():
    for package in ("dotenv", "google.adk", "google.genai", "mcp", "httpx"):
        try:
            importlib.import_module(package)
            print(f"PASS dependency: {package}")
        except ImportError:
            print(f"FAIL dependency: {package}; install dependencies with uv sync")
            return False
    return True


def load_configuration():
    from dotenv import dotenv_values, load_dotenv

    load_dotenv(BASE_DIR / ".env")
    server_values = dotenv_values(BASE_DIR.parent / "mcp-server" / ".env")
    keys = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "WEATHERAPI_KEY": os.getenv("WEATHERAPI_KEY") or server_values.get("WEATHERAPI_KEY"),
    }
    configured = True
    for name, value in keys.items():
        if not value or value.startswith("your_"):
            print(f"FAIL configuration: {name} is missing")
            configured = False
        else:
            print(f"PASS configuration: {name} is set")
    return configured, keys


def safe_error(error, keys):
    if isinstance(error, TimeoutError):
        return "Verification timed out. Check server connectivity and Gemini availability, then retry."
    message = str(error)
    for value in keys.values():
        if value:
            message = message.replace(value, "[REDACTED]")
    return message


async def verify_mcp(live):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    url = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            if names != EXPECTED_TOOLS:
                raise RuntimeError(f"Unexpected MCP tools: {sorted(names)}")
            print("PASS MCP handshake and discovery: " + ", ".join(sorted(names)))
            health = await session.call_tool("health_check", {})
            if health.isError:
                raise RuntimeError("MCP health_check failed")
            print("PASS MCP health_check")

            if live:
                for name, arguments, marker in (
                    ("get_current_weather", {"city": "Hanoi"}, "Current Weather for"),
                    ("get_forecast", {"city": "Tokyo", "days": 3}, "Weather Forecast for"),
                ):
                    result = await session.call_tool(name, arguments)
                    text = "\n".join(getattr(part, "text", "") for part in result.content)
                    if result.isError or marker not in text:
                        raise RuntimeError(f"{name} failed: {text}")
                    print(f"PASS WeatherAPI through MCP: {name}")

                # Invalid day counts must fail before making a WeatherAPI request.
                for days in (0, 4):
                    result = await session.call_tool("get_forecast", {"city": "Tokyo", "days": days})
                    if not result.isError:
                        raise RuntimeError(f"get_forecast accepted invalid days={days}")
                print("PASS forecast validation: days=0 and days=4 rejected")


async def verify_agent(live):
    from weather_agent import root_agent

    if len(root_agent.tools) != 1:
        raise RuntimeError("Weather agent must have its MCP toolset")
    toolset = root_agent.tools[0]
    runner = None
    try:
        names = {tool.name for tool in await toolset.get_tools()}
        if names != EXPECTED_TOOLS:
            raise RuntimeError(f"ADK discovered unexpected tools: {sorted(names)}")
        print(f"PASS ADK tool discovery; model={root_agent.model}")

        if not live:
            return

        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        sessions = InMemorySessionService()
        app_name = "weather_agent"
        user_id = "lab_verification"
        session_id = uuid.uuid4().hex
        await sessions.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        runner = Runner(agent=root_agent, app_name=app_name, session_service=sessions)
        prompt = (
            "Cho tôi thời tiết hiện tại ở Hà Nội và dự báo Tokyo trong 3 ngày tới. "
            "Hãy dùng cả get_current_weather và get_forecast, rồi tóm tắt bằng tiếng Việt."
        )
        calls = set()
        responses = set()
        final_text = ""
        events = runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        )
        model_error = None
        async with aclosing(events):
            async for event in events:
                if event.error_code:
                    model_error = f"Gemini/ADK error: {event.error_code}; {event.error_message}"
                for call in event.get_function_calls():
                    calls.add(call.name)
                    print(f"Gemini selected tool: {call.name}")
                for response in event.get_function_responses():
                    payload = response.response or {}
                    if payload.get("isError") or payload.get("error"):
                        raise RuntimeError(f"ADK tool failed: {response.name}")
                    responses.add(response.name)
                if event.is_final_response() and event.content:
                    final_text = "\n".join(part.text for part in event.content.parts if part.text)
        if model_error:
            raise RuntimeError(model_error)

        expected = {"get_current_weather", "get_forecast"}
        if not expected <= calls or not expected <= responses or not final_text:
            raise RuntimeError("ADK did not complete both weather tools and a final response")
        print("PASS Gemini -> ADK -> MCP -> WeatherAPI -> final response")
        print("\nAgent response:\n" + final_text)
    finally:
        if runner is not None:
            await runner.close()
        else:
            await toolset.close()


async def main(live):
    print("Weather Agent verification" + (" (live APIs)" if live else ""))
    if not check_dependencies():
        return 1
    configured, keys = load_configuration()
    if not configured:
        return 1
    try:
        await asyncio.wait_for(verify_mcp(live), timeout=120)
        await asyncio.wait_for(verify_agent(live), timeout=180)
    except Exception as error:
        print(f"FAIL: {safe_error(error, keys)}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Call real WeatherAPI and Gemini (uses API quota)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.CRITICAL)
    sys.exit(asyncio.run(main(args.live)))
