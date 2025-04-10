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
        with open("weather_response.json") as f:
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
        
        # Configure the mock to return different responses for different URLs
        def side_effect(url, *args, **kwargs):
            if "forecast" in url:
                return forecast_response
            else:
                return locations_response
        
        mock_get.side_effect = side_effect
        
        # Set up the API key in environment
        os.environ["OPENWEATHER_API_KEY"] = self.test_api_key
        
        # Call the MCP tool function
        result = weather_mcp_server.get_weather(
            location=self.test_location,
            timezone_offset=self.test_timezone_offset
        )
        
        # Verify the result structure
        self.assertIn('today', result)
        self.assertIn('tomorrow', result)
        self.assertTrue(len(result['today']) > 0)
        self.assertTrue(len(result['tomorrow']) > 0)
        
        # Check current weather info
        current = result['today'][0]
        self.assertIn('temperature', current)
        self.assertIn('feels_like', current)
        self.assertIn('weather_condition', current)
        self.assertIn('humidity', current)
        self.assertIn('wind', current)

    @patch('requests.get')
    def test_mcp_get_current_weather_tool(self, mock_get):
        """Test the MCP get_current_weather tool with a simulated API response"""
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
                {
                    "dt": 1744128000,
                    "main": {
                        "temp": 5.0, "feels_like": 2.0, "temp_min": 4.0, "temp_max": 6.0,
                        "humidity": 40, "pressure": 1006
                    },
                    "weather": [{"description": "clear sky"}],
                    "clouds": {"all": 10},
                    "wind": {"speed": 5.0, "deg": 270}
                }
            ],
            "city": {"name": "New York"}
        }
        
        # Configure the mock to return different responses for different URLs
        def side_effect(url, *args, **kwargs):
            if "forecast" in url:
                return forecast_response
            else:
                return locations_response
        
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
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "coord": {"lon": -74.006, "lat": 40.7128},
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 5.0, "feels_like": 2.0},
            "wind": {"speed": 5.0, "deg": 270}
        }
        mock_get.return_value = mock_response
        
        # Set up environment API key
        os.environ["OPENWEATHER_API_KEY"] = "env_api_key"
        
        # Call the function with a different API key parameter
        weather_mcp_server.get_current_weather(
            location=self.test_location,
            api_key="param_api_key",
            timezone_offset=self.test_timezone_offset
        )
        
        # Check that the parameter API key was used in the request
        call_args = mock_get.call_args_list[0][0][0]
        self.assertIn("param_api_key", call_args)
        self.assertNotIn("env_api_key", call_args)


if __name__ == '__main__':
    unittest.main()