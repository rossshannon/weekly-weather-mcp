# OpenWeather MCP Server

English | [中文版](README_CN.md)

A simple weather forecast MCP (Model Control Protocol) server providing global weather forecasts and current weather conditions.

<img src="image.png" alt="Claude Desktop using the MCP Weather Service" width="600">

Screenshot of Claude Desktop using the MCP Weather Service

## Features

- No separate configuration file needed; API key can be passed directly through environment variables or parameters
- Support for querying weather conditions anywhere in the world
- Provides current weather and future forecasts
- Detailed weather information including temperature, humidity, wind speed, etc.
- Support for different time zones

## Installation Requirements

```
pip install mcp-server requests pydantic
```

## Usage

### 1. Get an OpenWeatherMap API Key

Visit [OpenWeatherMap](https://openweathermap.org/) and register an account to obtain an API key.

### 2. Run the Server

There are two ways to provide the API key:

#### Method 1: Using Environment Variables

```bash
# Set environment variables
export OPENWEATHER_API_KEY="your_api_key"  # Linux/Mac
set OPENWEATHER_API_KEY=your_api_key  # Windows

# Run the server
python weather_mcp_server.py
```

#### Method 2: Provide When Calling the Tool

Run directly without setting environment variables:

```bash
python weather_mcp_server.py
```

When calling the tool, you'll need to provide the `api_key` parameter.

### 3. Use in MCP Client Configuration

Add the following configuration to your MCP-supported client:

```json
{
  "weather_forecast": {
    "command": "python",
    "args": [
      "/full_path/weather_mcp_server.py"
    ],
    "env": {
      "OPENWEATHER_API_KEY": "your_openweathermap_key_here"
    },
    "disabled": false,
    "autoApprove": ["get_weather", "get_current_weather"]
  }
}
```

### 4. Available Tools

#### get_weather

Get current weather and forecast for a specified location.

Parameters:
- `location`: Location name, e.g., "Beijing", "New York", "Tokyo"
- `api_key`: OpenWeatherMap API key (optional, will read from environment variable if not provided)
- `timezone_offset`: Timezone offset in hours, e.g., 8 for Beijing, -4 for New York. Default is 0 (UTC time)

#### get_current_weather

Get current weather for a specified location.

Parameters:
- `location`: Location name, e.g., "Beijing", "New York", "Tokyo"
- `api_key`: OpenWeatherMap API key (optional, will read from environment variable if not provided)
- `timezone_offset`: Timezone offset in hours, e.g., 8 for Beijing, -4 for New York. Default is 0 (UTC time)

## Usage Example

AI assistant call example:

```
User: What's the weather like in New York right now?

AI: Let me check the current weather in New York for you.
[Calling get_current_weather("New York", timezone_offset=-4)]

Current weather in New York: 18°C, partly cloudy, humidity 65%, wind speed 3.5m/s.
```

## Troubleshooting

If you encounter a "No API key provided" error, make sure:
1. You have set the OPENWEATHER_API_KEY in environment variables, or
2. You are providing the api_key parameter when calling the tools

If the location name is incorrect, you might receive a "Location not found" error. Try using a more accurate city name or add a country code, e.g., "Beijing,CN" or "Paris,FR". 