"""End-to-end smoke test for the local Weather MCP server."""

import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")


async def main() -> None:
    async with streamable_http_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("MCP tools:", ", ".join(tool.name for tool in tools.tools))

            health = await session.call_tool("health_check", {})
            print("Health:", health.content[0].text)

            current = await session.call_tool(
                "get_current_weather", {"city": "Hanoi"}
            )
            print("\nCurrent weather:\n", current.content[0].text)

            forecast = await session.call_tool(
                "get_forecast", {"city": "Danang", "days": 3}
            )
            print("\nForecast:\n", forecast.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
