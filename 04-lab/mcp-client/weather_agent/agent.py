"""Google ADK weather agent using a remote MCP server."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

weather_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,
    ),
)

root_agent = Agent(
    name="weather_agent",
    model=GEMINI_MODEL,
    description="Trợ lý thời tiết: điều kiện hiện tại và dự báo qua WeatherAPI/MCP.",
    instruction=(
        "Bạn là trợ lý thời tiết, mặc định trả lời bằng tiếng Việt. "
        "Luôn gọi get_current_weather để lấy thời tiết hiện tại và get_forecast "
        "để lấy dự báo. Không tự đoán hoặc tạo dữ liệu thời tiết. "
        "Dùng tên thành phố rõ ràng trong tool; hỏi lại nếu địa điểm không rõ. "
        "Dự báo hỗ trợ từ 1 đến 3 ngày; nếu người dùng yêu cầu dài hơn, "
        "giải thích giới hạn và chỉ lấy 3 ngày. Dùng độ C và km/h. "
        "Nêu địa điểm, thời điểm cập nhật khi có, nhiệt độ, tình trạng thời tiết "
        "và lời khuyên ngắn dựa trên dữ liệu tool. "
        "Nếu tool hoặc API lỗi, nói rõ chưa lấy được dữ liệu, không bịa kết quả. "
        "health_check chỉ xác nhận MCP server hoạt động, không xác nhận API key hợp lệ."
    ),
    tools=[weather_tools],
)

# McpToolset connects lazily when tools are discovered; construction is not a health check.
logger.info("Weather agent configured: model=%s, MCP=%s", GEMINI_MODEL, MCP_SERVER_URL)
