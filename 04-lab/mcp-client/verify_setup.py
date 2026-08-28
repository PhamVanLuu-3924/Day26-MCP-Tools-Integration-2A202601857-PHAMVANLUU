#!/usr/bin/env python3
"""
Verification script for Weather Agent setup
Checks if all components are configured correctly
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

def check_environment():
    """Check if .env file exists and is configured"""
    print("🔍 Checking environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Run: echo 'GOOGLE_API_KEY=your_key' > .env")
        return False
    
    # Check if GOOGLE_API_KEY is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print("❌ GOOGLE_API_KEY not configured in .env")
        print("   Get key from: https://aistudio.google.com/apikey")
        return False
    
    print("✅ GOOGLE_API_KEY configured (value hidden)")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        ("google.adk", "Google ADK"),
        ("google.genai", "Google Gen AI SDK"),
        ("mcp", "MCP"),
        ("fastmcp", "FastMCP"),
        ("dotenv", "python-dotenv"),
        ("httpx", "httpx"),
    ]
    
    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_installed = False
    
    if not all_installed:
        print("\n   Install with: uv sync")
        print("   Or: pip install google-adk google-generativeai mcp fastmcp python-dotenv httpx")
    
    return all_installed

def check_agent_structure():
    """Check if agent directory structure is correct"""
    print("\n🔍 Checking agent structure...")
    
    required_files = [
        "weather_agent/agent.py",
        "weather_agent/__init__.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False
    
    return all_exist

async def _list_mcp_tools():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.list_tools()


def check_mcp_server():
    """Check if MCP server is accessible"""
    print("\n🔍 Checking MCP server connectivity...")
    
    try:
        tools = asyncio.run(_list_mcp_tools())
        names = [tool.name for tool in tools.tools]
        expected = {"get_current_weather", "get_forecast", "health_check"}
        missing = expected.difference(names)
        if missing:
            print(f"❌ MCP server is missing tools: {sorted(missing)}")
            return False
        print(f"✅ MCP server connected at {MCP_SERVER_URL}")
        print(f"   Tools: {', '.join(names)}")
        return True
    except Exception as e:
        print(f"❌ Cannot reach MCP server: {e}")
        print("   Start it first: cd ../mcp-server; uv run python weather.py")
        return False

def check_agent_import():
    """Try to import the agent"""
    print("\n🔍 Checking agent import...")
    
    try:
        # Suppress warnings during import
        import warnings
        warnings.filterwarnings("ignore")
        
        from weather_agent import root_agent
        print(f"✅ Agent imported successfully: {root_agent.name}")
        print(f"   Model: {root_agent.model}")
        return True
    except Exception as e:
        print(f"❌ Failed to import agent: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Weather Agent Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        check_environment(),
        check_dependencies(),
        check_agent_structure(),
        check_mcp_server(),
        check_agent_import(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed!")
        print("\n🚀 Ready to start!")
        print("   Run: uv run adk web")
        print("\n📍 Then open: http://localhost:8000")
        return 0
    else:
        print("❌ Some checks failed")
        print("\n⚠️  Fix the issues above and run this script again")
        return 1

if __name__ == "__main__":
    sys.exit(main())

