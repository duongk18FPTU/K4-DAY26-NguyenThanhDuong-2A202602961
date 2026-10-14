from typing import Any
import argparse
import logging
from pathlib import Path
import httpx
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).with_name(".env"))
logger = logging.getLogger(__name__)

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather", host="0.0.0.0", port=port)
# Apply this on import too: callers may use the tools without running __main__.
logging.getLogger("httpx").setLevel(logging.WARNING)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
    """Make a request to the WeatherAPI with proper error handling."""
    # Check if API key is set
    if not API_KEY:
        raise RuntimeError("WeatherAPI key not configured. Set WEATHERAPI_KEY in mcp-server/.env.")
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    request_params = {**params, "key": API_KEY}
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=request_params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Do not log the request URL: its query string contains the API key.
            status = e.response.status_code
            logger.warning("WeatherAPI returned HTTP %s", status)
            raise RuntimeError(f"WeatherAPI returned HTTP {status}. Check the city, API key and plan.") from None
        except httpx.RequestError as e:
            logger.warning("WeatherAPI connection failed (%s)", type(e).__name__)
            raise RuntimeError("Cannot connect to WeatherAPI. Check the network and try again.") from None
        except ValueError:
            raise RuntimeError("WeatherAPI returned an invalid JSON response.") from None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast, from 1 to 3.
    """
    if not 1 <= days <= 3:
        raise ValueError("days must be between 1 and 3.")
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather MCP server")
    parser.add_argument("--transport", choices=["streamable-http", "stdio"], default="streamable-http")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Weather MCP server (%s), port %s", args.transport, port)
    mcp.run(transport=args.transport)
