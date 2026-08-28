from datetime import date, timedelta
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather", host="0.0.0.0", port=port)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")
DATA_MODE = os.getenv("WEATHER_DATA_MODE", "auto").lower()

if DATA_MODE not in {"auto", "live", "mock"}:
    raise ValueError("WEATHER_DATA_MODE must be one of: auto, live, mock")

USE_LIVE_API = DATA_MODE == "live" or (DATA_MODE == "auto" and bool(API_KEY))
DATA_SOURCE = "WeatherAPI.com" if USE_LIVE_API else "demo data"

_MOCK_WEATHER = {
    "hanoi": {
        "name": "Hanoi", "region": "Hanoi", "country": "Vietnam",
        "temp_c": 29, "condition": "Light rain", "humidity": 82, "wind_kph": 12,
    },
    "haiphong": {
        "name": "Haiphong", "region": "Hai Phong", "country": "Vietnam",
        "temp_c": 31, "condition": "Rain showers", "humidity": 80, "wind_kph": 15,
    },
    "danang": {
        "name": "Da Nang", "region": "Da Nang", "country": "Vietnam",
        "temp_c": 30, "condition": "Partly cloudy", "humidity": 78, "wind_kph": 10,
    },
    "da nang": {
        "name": "Da Nang", "region": "Da Nang", "country": "Vietnam",
        "temp_c": 30, "condition": "Partly cloudy", "humidity": 78, "wind_kph": 10,
    },
    "ho chi minh": {
        "name": "Ho Chi Minh City", "region": "Ho Chi Minh", "country": "Vietnam",
        "temp_c": 33, "condition": "Rain showers", "humidity": 75, "wind_kph": 14,
    },
}


def _mock_response(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
    """Build a WeatherAPI-shaped response for an offline classroom demo."""
    query = params.get("q", "Hanoi")
    item = _MOCK_WEATHER.get(query.strip().lower())
    if item is None:
        item = {
            "name": query,
            "region": "Demo region",
            "country": "Demo",
            "temp_c": 28,
            "condition": "No detailed demo data",
            "humidity": 70,
            "wind_kph": 8,
        }

    temp_c = item["temp_c"]
    location = {
        "name": item["name"],
        "region": item["region"],
        "country": item["country"],
    }
    current = {
        "temp_c": temp_c,
        "temp_f": round(temp_c * 9 / 5 + 32, 1),
        "feelslike_c": temp_c + 1,
        "feelslike_f": round((temp_c + 1) * 9 / 5 + 32, 1),
        "condition": {"text": item["condition"]},
        "humidity": item["humidity"],
        "wind_kph": item["wind_kph"],
        "wind_mph": round(item["wind_kph"] / 1.609, 1),
        "wind_dir": "SE",
        "pressure_mb": 1009,
        "uv": 5,
        "vis_km": 10,
        "last_updated": "demo data",
    }

    if endpoint == "current.json":
        return {"location": location, "current": current}

    days = max(1, min(int(params.get("days", "3")), 3))
    forecast_days = []
    conditions = [item["condition"], "Partly cloudy", "Light rain"]
    for offset in range(days):
        condition = conditions[offset]
        forecast_days.append(
            {
                "date": (date.today() + timedelta(days=offset)).isoformat(),
                "day": {
                    "maxtemp_c": temp_c + 2,
                    "maxtemp_f": round((temp_c + 2) * 9 / 5 + 32, 1),
                    "mintemp_c": temp_c - 3,
                    "mintemp_f": round((temp_c - 3) * 9 / 5 + 32, 1),
                    "condition": {"text": condition},
                    "daily_chance_of_rain": 70 if "rain" in condition.lower() else 25,
                    "maxwind_kph": item["wind_kph"] + 3,
                    "uv": 5,
                },
            }
        )
    return {"location": location, "forecast": {"forecastday": forecast_days}}

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    if not USE_LIVE_API:
        return _mock_response(endpoint, params)

    if not API_KEY:
        print("ERROR: WEATHER_DATA_MODE=live requires WEATHERAPI_KEY.")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    params["key"] = API_KEY
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

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

    if not data:
        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Data source: {DATA_SOURCE}

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
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    # Limit days to 3 for free tier
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    forecasts.append(f"Data source: {DATA_SOURCE}")
    
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
    return f"✅ Weather MCP Server is running in {DATA_SOURCE} mode."

print("✅ MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools: get_current_weather, get_forecast, health_check")
print(f"📊 Data source: {DATA_SOURCE}")

if __name__ == "__main__":
    import sys
    
    is_cloud_run = bool(os.getenv("PORT"))
    is_standalone = len(sys.argv) == 1 and sys.stdin.isatty()
    
    if is_cloud_run or is_standalone:
        print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
        mcp.run(transport="streamable-http")
    else:
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()
