#!/usr/bin/env python3
"""
Integration tests for the Weather MCP Server
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Try to import weather_mcp_server, but if mcp package is missing, mock it
try:
    import weather_mcp_server
except ModuleNotFoundError:
    # Create a mock for the FastMCP class
    sys.modules['mcp'] = MagicMock()
    sys.modules['mcp.server'] = MagicMock()
    sys.modules['mcp.server.fastmcp'] = MagicMock()
    sys.modules['mcp.server.fastmcp'].FastMCP = MagicMock()

    # Now import should work
    import weather_mcp_server


class TestMCPIntegration(unittest.TestCase):
    """Test the MCP server integration functionality"""

    def setUp(self):
        """Set up test environment"""
        # Clear environment variable to ensure tests control it
        if "OPENWEATHER_API_KEY" in os.environ:
            self.original_api_key = os.environ["OPENWEATHER_API_KEY"]
            del os.environ["OPENWEATHER_API_KEY"]
        else:
            self.original_api_key = None

        # Sample test data
        self.test_location = "New York"
        self.test_api_key = "test_api_key_123"
        self.test_timezone_offset = -4

        # Load sample response data
        with open("test_weather_response.json") as f:
            self.sample_onecall_data = json.load(f)

    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment if it existed
        if self.original_api_key is not None:
            os.environ["OPENWEATHER_API_KEY"] = self.original_api_key
        elif "OPENWEATHER_API_KEY" in os.environ:
            del os.environ["OPENWEATHER_API_KEY"]

    @patch('requests.get')
    def test_mcp_get_weather_tool(self, mock_get):
        """Test the MCP get_weather tool with a simulated API response"""
        # Sample locations response
        locations_response = MagicMock()
        locations_response.status_code = 200
        locations_response.json.return_value = {
            "coord": {"lon": -74.006, "lat": 40.7128},
            "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
            "main": {
                "temp": 5.46, "feels_like": 0.42, "temp_min": 4.0, "temp_max": 6.5,
                "pressure": 1006, "humidity": 36
            },
            "wind": {"speed": 9.17, "deg": 298},
            "clouds": {"all": 20},
            "name": "New York"
        }

        # Sample forecast response
        forecast_response = MagicMock()
        forecast_response.status_code = 200
        forecast_response.json.return_value = {
            "list": [
                # Today's forecast entries
                {
                    "dt": 1744128000,  # Today
                    "main": {
                        "temp": 5.0, "feels_like": 2.0, "temp_min": 4.0, "temp_max": 6.0,
                        "humidity": 40, "pressure": 1006
                    },
                    "weather": [{"description": "clear sky"}],
                    "clouds": {"all": 10},
                    "wind": {"speed": 5.0, "deg": 270}
                },
                # Tomorrow's forecast entries
                {
                    "dt": 1744214400,  # Tomorrow
                    "main": {
                        "temp": 6.0, "feels_like": 3.0, "temp_min": 5.0, "temp_max": 7.0,
                        "humidity": 45, "pressure": 1008
                    },
                    "weather": [{"description": "scattered clouds"}],
                    "clouds": {"all": 30},
                    "wind": {"speed": 4.5, "deg": 280}
                }
            ],
            "city": {"name": "New York"}
        }

        # Mock the geocoding API response
        geocoding_response = MagicMock()
        geocoding_response.status_code = 200
        geocoding_response.json.return_value = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060}
        ]

        # Mock the One Call API response
        onecall_response = MagicMock()
        onecall_response.status_code = 200
        onecall_response.json.return_value = {
            "lat": 40.7128,
            "lon": -74.0060,
            "timezone": "America/New_York",
            "timezone_offset": -14400,
            "current": {
                "dt": 1617979000,
                "temp": 15.2,
                "feels_like": 14.3,
                "humidity": 76,
                "wind_speed": 2.06,
                "wind_deg": 210,
                "weather": [{"description": "clear sky"}],
                "clouds": 1
            },
            "daily": [
                {
                    "dt": 1617979000,
                    "temp": {"day": 15.0, "min": 9.0, "max": 17.0, "eve": 13.0, "morn": 10.0},
                    "feels_like": {"day": 14.3, "night": 8.5, "eve": 12.5, "morn": 9.5},
                    "humidity": 76,
                    "wind_speed": 2.06,
                    "wind_deg": 210,
                    "weather": [{"description": "clear sky"}],
                    "clouds": 1,
                    "pop": 0.2,
                    "summary": "Nice day"
                }
            ],
            "hourly": [
                {
                    "dt": 1617979000,
                    "temp": 15.2,
                    "feels_like": 14.3,
                    "humidity": 76,
                    "wind_speed": 2.06,
                    "wind_deg": 210,
                    "weather": [{"description": "clear sky"}],
                    "clouds": 1,
                    "pop": 0.2
                }
            ]
        }

        # Configure the mock to return different responses for different URLs
        def side_effect(url, *args, **kwargs):
            if "onecall" in url:
                return onecall_response
            elif "geo" in url:
                return geocoding_response
            else:
                return geocoding_response

        mock_get.side_effect = side_effect

        # Set up the API key in environment
        os.environ["OPENWEATHER_API_KEY"] = self.test_api_key

        # Call the MCP tool function
        result = weather_mcp_server.get_weather(
            location=self.test_location,
            timezone_offset=self.test_timezone_offset
        )

        # Verify the result structure
        self.assertIn('daily_forecasts', result)
        self.assertIn('current', result)
        self.assertTrue(len(result['daily_forecasts']) > 0)

        # Check current weather info
        current = result['current']
        self.assertIn('temperature', current)
        self.assertIn('feels_like', current)
        self.assertIn('weather_condition', current)
        self.assertIn('humidity', current)
        self.assertIn('wind', current)

    @patch('requests.get')
    def test_mcp_get_current_weather_tool(self, mock_get):
        """Test the MCP get_current_weather tool with a simulated API response"""
        # Mock the geocoding API response
        geocoding_response = MagicMock()
        geocoding_response.status_code = 200
        geocoding_response.json.return_value = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060}
        ]

        # Mock the One Call API response
        onecall_response = MagicMock()
        onecall_response.status_code = 200
        onecall_response.json.return_value = {
            "lat": 40.7128,
            "lon": -74.0060,
            "timezone": "America/New_York",
            "timezone_offset": -14400,
            "current": {
                "dt": 1617979000,
                "temp": 15.2,
                "feels_like": 14.3,
                "humidity": 76,
                "wind_speed": 2.06,
                "wind_deg": 210,
                "weather": [{"description": "clear sky"}],
                "clouds": 1
            },
            "daily": [],
            "hourly": []
        }

        # Configure the mock to return different responses for different URLs
        def side_effect(url, *args, **kwargs):
            if "onecall" in url:
                return onecall_response
            elif "geo" in url:
                return geocoding_response
            else:
                return geocoding_response

        mock_get.side_effect = side_effect

        # Set up the API key in environment
        os.environ["OPENWEATHER_API_KEY"] = self.test_api_key

        # Call the MCP tool function
        result = weather_mcp_server.get_current_weather(
            location=self.test_location,
            timezone_offset=self.test_timezone_offset
        )

        # Verify the result is just the current weather
        self.assertIn('temperature', result)
        self.assertIn('feels_like', result)
        self.assertIn('weather_condition', result)
        self.assertIn('humidity', result)
        self.assertIn('wind', result)

    @patch('requests.get')
    def test_api_key_parameter_overrides_env(self, mock_get):
        """Test that API key provided as parameter overrides the environment variable"""
        # Mock geocoding response
        mock_geocoding = MagicMock()
        mock_geocoding.status_code = 200
        mock_geocoding.json.return_value = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060}
        ]

        # Mock One Call API response
        mock_onecall = MagicMock()
        mock_onecall.status_code = 200
        mock_onecall.json.return_value = {
            "lat": 40.7128,
            "lon": -74.0060,
            "current": {"temp": 15, "feels_like": 14, "humidity": 70,
                       "weather": [{"description": "clear"}], "wind_speed": 5, "wind_deg": 270}
        }

        # Track which API key was used
        param_api_key_used = [False]
        env_api_key_used = [False]

        # Configure the side effect to return the appropriate mock based on the URL
        def side_effect(url, *args, **kwargs):
            if "param_api_key" in url:
                param_api_key_used[0] = True
            if "env_api_key" in url:
                env_api_key_used[0] = True

            if "geo/1.0/direct" in url or "geo" in url:
                return mock_geocoding
            else:
                return mock_onecall

        mock_get.side_effect = side_effect

        # Set up environment API key
        os.environ["OPENWEATHER_API_KEY"] = "env_api_key"

        # Call the function with a different API key parameter
        weather_mcp_server.get_current_weather(
            location=self.test_location,
            api_key="param_api_key",
            timezone_offset=self.test_timezone_offset
        )

        # Check that the parameter API key was used in the request
        self.assertTrue(param_api_key_used[0], "Parameter API key wasn't used")
        self.assertFalse(env_api_key_used[0], "Environment API key was incorrectly used")


if __name__ == '__main__':
    unittest.main()
