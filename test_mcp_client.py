#!/usr/bin/env python3
"""
Simple test script for the Weather MCP Server

This script directly imports the functions from the weather_mcp_server.py
file and tests them without going through the MCP server protocol.
"""
import os
import sys
from weather_mcp_server import get_current_weather, get_weather

def main():
    """Test the weather server functions directly"""
    # Check if API key is set
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        print("Error: OPENWEATHER_API_KEY environment variable not set")
        print("Please set the environment variable and try again:")
        print("  export OPENWEATHER_API_KEY=your_key_here")
        return
    print("Using API key from environment variables")

    # Location to test
    location = "New York"
    timezone_offset = -4
    
    print(f"\nTesting get_current_weather for {location}...")
    try:
        result = get_current_weather(location, api_key, timezone_offset)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print("\nCurrent Weather:")
            print(f"Temperature: {result['temperature']}")
            print(f"Conditions: {result['weather_condition']}")
            print(f"Humidity: {result['humidity']}")
            print(f"Wind: {result['wind']['speed']} at {result['wind']['direction']}")
    except Exception as e:
        print(f"Error during execution: {str(e)}")
    
    print("\nTest complete")

if __name__ == "__main__":
    main()