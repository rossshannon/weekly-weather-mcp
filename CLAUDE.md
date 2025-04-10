# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run server: `python3 weather_mcp_server.py`
- Install dependencies: `pip3 install mcp-server requests pydantic`
- Format code: `black weather_mcp_server.py`
- Typecheck: `mypy weather_mcp_server.py --strict`
- Manual test: `curl -X POST -H "Content-Type: application/json" -d '{"tool": "get_current_weather", "parameters": {"location": "New York"}}' http://localhost:8000`

## Style Guidelines
- **Python Version**: 3.6+
- **Code Style**: PEP 8 compliant
- **Imports**: Group standard library, third-party, and local imports with newlines between groups
- **Type Hints**: Use type annotations for all function parameters and return values
- **Error Handling**: Use try/except blocks with specific exception types
- **Docstrings**: Use triple-quoted docstrings for all functions and classes
- **Naming**: Use snake_case for variables and functions, PascalCase for classes
- **API Key Handling**: Never hardcode API keys; use environment variables or parameters

## Architecture Notes
- Single-file MCP server based on FastMCP for OpenWeatherMap API
- Pydantic models for data validation and serialization
- Functions handle API requests with proper error handling