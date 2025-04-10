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
        import traceback
        traceback.print_exc()
    
    print(f"\nTesting get_weather (8-day forecast) for {location}...")
    try:
        result = get_weather(location, api_key, timezone_offset)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print("\nWeather Forecast Summary:")
            print(f"Current Temperature: {result['current']['temperature']}")
            print(f"Current Conditions: {result['current']['weather_condition']}")
            print(f"\nForecasted Days: {len(result['daily_forecasts'])}")
            
            # Print a summary of each day's forecast
            print("\nDaily Forecasts:")
            for i, day in enumerate(result['daily_forecasts']):
                print(f"Day {i+1} ({day['date']}): {day['summary']}")
                
                # Find the afternoon entry for a temperature estimate
                afternoon_entries = [entry for entry in day['entries'] 
                                    if '15:00:00' in entry['time']]
                if afternoon_entries:
                    temp = afternoon_entries[0]['temperature']
                    condition = afternoon_entries[0]['weather_condition']
                    pop = afternoon_entries[0].get('pop', 'N/A')
                    print(f"  Afternoon: {temp}, {condition}, Precip: {pop}")
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\nTest complete")

if __name__ == "__main__":
    main()