"""Google ADK weather agent backed by a local Streamable HTTP MCP server."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

logger.info("Initializing weather agent")
logger.info("MCP Server: %s", MCP_SERVER_URL)

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    timeout=30.0,
)

weather_tools = McpToolset(connection_params=connection_params)

root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description="Trợ lý thời tiết dùng các công cụ từ MCP server.",
    instruction=(
        "Bạn là trợ lý thời tiết. Luôn dùng công cụ MCP phù hợp trước khi trả lời "
        "câu hỏi về thời tiết. Trả lời ngắn gọn, rõ ràng bằng tiếng Việt và nói "
        "rõ khi kết quả đến từ dữ liệu demo."
    ),
    tools=[weather_tools],
)

logger.info("Weather agent configured with MCP tools")

