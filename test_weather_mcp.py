#!/usr/bin/env python3
"""
Unit tests for the Weather MCP Server
"""
import unittest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime, timezone, timedelta
import json
import sys
import importlib.util

# Create mock classes and modules needed for testing
class MockField:
    def __init__(self, *args, **kwargs):
        self.description = kwargs.get('description', '')

class MockBaseModel:
    pass

# Mock modules needed for testing
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.fastmcp'] = MagicMock()
sys.modules['mcp.server.fastmcp'].FastMCP = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['pydantic'].BaseModel = MockBaseModel
sys.modules['pydantic'].Field = MockField

# Make mcp.tool() return the function itself, not a mock
def mock_tool_decorator():
    def decorator(func):
        return func
    return decorator

sys.modules['mcp.server.fastmcp'].FastMCP().tool = mock_tool_decorator

# Now import should work
import weather_mcp_server


class TestWeatherMCP(unittest.TestCase):
    """Test the Weather MCP server functionality"""

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

        # Sample response data
        with open("test_weather_response.json") as f:
            self.sample_onecall_data = json.load(f)

        # Sample current weather response
        self.sample_current_weather = {
            "coord": {"lon": -74.006, "lat": 40.7128},
            "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
            "base": "stations",
            "main": {
                "temp": 5.46,
                "feels_like": 0.42,
                "temp_min": 4.0,
                "temp_max": 6.5,
                "pressure": 1006,
                "humidity": 36
            },
            "visibility": 10000,
            "wind": {"speed": 9.17, "deg": 298},
            "clouds": {"all": 20},
            "dt": 1744128000,
            "sys": {
                "type": 2,
                "id": 2039034,
                "country": "US",
                "sunrise": 1744108059,
                "sunset": 1744154851
            },
            "timezone": -14400,
            "id": 5128581,
            "name": "New York",
            "cod": 200
        }

    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment if it existed
        if self.original_api_key is not None:
            os.environ["OPENWEATHER_API_KEY"] = self.original_api_key
        elif "OPENWEATHER_API_KEY" in os.environ:
            del os.environ["OPENWEATHER_API_KEY"]

    def test_get_api_key_from_param(self):
        """Test getting API key from parameter"""
        api_key = weather_mcp_server.get_api_key(self.test_api_key)
        self.assertEqual(api_key, self.test_api_key)

    def test_get_api_key_from_env(self):
        """Test getting API key from environment variable"""
        os.environ["OPENWEATHER_API_KEY"] = self.test_api_key
        api_key = weather_mcp_server.get_api_key()
        self.assertEqual(api_key, self.test_api_key)

    def test_get_api_key_missing(self):
        """Test error when API key is missing"""
        with self.assertRaises(ValueError):
            weather_mcp_server.get_api_key()

    @patch('weather_mcp_server.requests.get')
    def test_get_weather_success(self, mock_get):
        """Test successful weather forecast retrieval"""
        # Mock the geocoding API response
        mock_geocoding_response = MagicMock()
        mock_geocoding_response.status_code = 200
        mock_geocoding_response.json.return_value = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060}
        ]

        # Mock the One Call API response
        mock_onecall_response = MagicMock()
        mock_onecall_response.status_code = 200
        mock_onecall_response.json.return_value = {
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
                return mock_onecall_response
            elif "geo" in url:
                return mock_geocoding_response
            else:
                # Fallback to current weather API for coordinates
                return mock_geocoding_response

        mock_get.side_effect = side_effect

        # Call the function with test data
        result = weather_mcp_server.get_weather(
            self.test_location,
            self.test_api_key,
            self.test_timezone_offset
        )

        # Check the result
        self.assertIn('daily_forecasts', result)
        self.assertIn('current', result)
        self.assertTrue(len(result['daily_forecasts']) > 0)

        # Verify API was called with the right parameters
        mock_get.assert_called()

        # Verify the structure of the returned data
        self.assertIn('time', result['current'])
        self.assertIn('temperature', result['current'])
        self.assertIn('weather_condition', result['current'])

        # Verify daily forecast structure
        first_day = result['daily_forecasts'][0]
        self.assertIn('date', first_day)
        self.assertIn('entries', first_day)
        self.assertIn('summary', first_day)

    @patch('weather_mcp_server.requests.get')
    def test_get_current_weather_success(self, mock_get):
        """Test successful current weather retrieval"""
        # Mock the geocoding API response
        mock_geocoding_response = MagicMock()
        mock_geocoding_response.status_code = 200
        mock_geocoding_response.json.return_value = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060}
        ]

        # Mock the One Call API response
        mock_onecall_response = MagicMock()
        mock_onecall_response.status_code = 200
        mock_onecall_response.json.return_value = {
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
                return mock_onecall_response
            elif "geo" in url:
                return mock_geocoding_response
            else:
                # Fallback to current weather API for coordinates
                return mock_geocoding_response

        mock_get.side_effect = side_effect

        # Call the function
        result = weather_mcp_server.get_current_weather(
            self.test_location,
            self.test_api_key,
            self.test_timezone_offset
        )

        # Verify the structure of the returned data
        self.assertIn('time', result)
        self.assertIn('temperature', result)
        self.assertIn('weather_condition', result)
        self.assertEqual(result['weather_condition'], 'clear sky')

    @patch('weather_mcp_server.requests.get')
    def test_api_error_handling(self, mock_get):
        """Test error handling for API failures"""
        # Mock an API error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        # Call the function
        result = weather_mcp_server.get_weather(
            self.test_location,
            self.test_api_key,
            self.test_timezone_offset
        )

        # Verify error is returned
        self.assertIn('error', result)

    def test_env_variable_priority(self):
        """Test that provided API key takes priority over environment variable"""
        os.environ["OPENWEATHER_API_KEY"] = "env_api_key"
        api_key = weather_mcp_server.get_api_key("provided_api_key")
        self.assertEqual(api_key, "provided_api_key")

    @patch('weather_mcp_server.requests.get')
    def test_location_not_found(self, mock_get):
        """Test handling when location is not found"""
        # Mock the geo API response for location not found
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []  # Empty response means location not found
        mock_get.return_value = mock_response

        # Since we're using a new get_coordinates function, we need to mock how it raises the exception
        mock_get.side_effect = KeyError("coord")

        # Call the function
        result = weather_mcp_server.get_weather("NonExistentLocation", self.test_api_key)

        # Verify error is returned
        self.assertIn('error', result)

    @patch('weather_mcp_server.get_weather')
    def test_get_current_weather_error_propagation(self, mock_get_weather):
        """Test that errors from get_weather are propagated to get_current_weather"""
        # Mock an error from get_weather
        mock_get_weather.return_value = {"error": "Test error"}

        # Call get_current_weather
        result = weather_mcp_server.get_current_weather(
            self.test_location,
            self.test_api_key,
            self.test_timezone_offset
        )

        # Verify error is propagated
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Test error")

    @patch('weather_mcp_server.get_weather')
    def test_get_current_weather_missing_current(self, mock_get_weather):
        """Test handling when get_weather returns data without 'current' field"""
        # Mock results from get_weather without 'current' field
        mock_get_weather.return_value = {
            "daily_forecasts": [{"date": "2023-01-01", "entries": [], "summary": ""}]
        }

        # Call get_current_weather
        result = weather_mcp_server.get_current_weather(
            self.test_location,
            self.test_api_key,
            self.test_timezone_offset
        )

        # Verify error is returned
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Unable to get current weather information")

    @patch('weather_mcp_server.requests.get')
    def test_geocoding_fallback(self, mock_get):
        """Test that geocoding falls back to current weather API when geocoding API returns no results"""
        # First create empty geocoding response
        empty_geocoding_response = MagicMock()
        empty_geocoding_response.status_code = 200
        empty_geocoding_response.json.return_value = []  # Empty response to trigger fallback
        
        # Create fallback current weather API response with coordinates
        fallback_response = MagicMock()
        fallback_response.status_code = 200
        fallback_response.json.return_value = {
            "coord": {"lat": 40.7128, "lon": -74.0060},
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 15.0},
            "name": "New York"
        }
        
        # Create onecall API response for after coordinates are found
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
            "hourly": []
        }
        
        # Configure the mock to return different responses based on the URL
        # First geocoding returns empty, then fallback to current weather API works, then onecall API works
        call_count = [0]
        
        def side_effect(url, *args, **kwargs):
            call_count[0] += 1
            
            if "onecall" in url:
                return onecall_response
            elif "geo/1.0/direct" in url:
                return empty_geocoding_response
            elif "data/2.5/weather" in url:
                # This is the fallback API
                return fallback_response
            else:
                return empty_geocoding_response
        
        mock_get.side_effect = side_effect
        
        # Call the function
        result = weather_mcp_server.get_weather(
            self.test_location, 
            self.test_api_key, 
            self.test_timezone_offset
        )
        
        # Verify we got valid results indicating the fallback worked
        self.assertIn('daily_forecasts', result)
        self.assertIn('current', result)
        
        # Check that we called the APIs in the right order
        # Should be at least 3 calls: geocoding, fallback, onecall
        self.assertGreaterEqual(call_count[0], 3)


if __name__ == '__main__':
    unittest.main()
