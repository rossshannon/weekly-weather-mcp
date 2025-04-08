# weather_mcp_server.py
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import requests
from datetime import datetime, timedelta, timezone
import os

# Create MCP server instance
mcp = FastMCP(
    name="WeatherForecastServer",
    description="Provides global weather forecasts and current weather conditions",
    version="1.2.0"
)

# Define data models
class WindInfo(BaseModel):
    speed: str = Field(..., description="Wind speed in meters per second")
    direction: str = Field(..., description="Wind direction in degrees")

class WeatherEntry(BaseModel):
    time: str = Field(..., description="Time of the weather data")
    temperature: str = Field(..., description="Temperature in Celsius")
    feels_like: str = Field(..., description="Feels like temperature in Celsius")
    temp_min: str = Field(..., description="Minimum temperature in Celsius")
    temp_max: str = Field(..., description="Maximum temperature in Celsius")
    weather_condition: str = Field(..., description="Weather condition description")
    humidity: str = Field(..., description="Humidity percentage")
    wind: WindInfo = Field(..., description="Wind speed and direction information")
    rain: str = Field(..., description="Rainfall amount")
    clouds: str = Field(..., description="Cloud coverage percentage")
    pop: Optional[str] = Field(None, description="Probability of precipitation")

class DailyForecast(BaseModel):
    date: str = Field(..., description="Date of the forecast in YYYY-MM-DD format")
    entries: List[WeatherEntry] = Field(..., description="Weather entries for this day")
    summary: Optional[str] = Field(None, description="Summary of the day's weather")

class WeatherForecast(BaseModel):
    daily_forecasts: List[DailyForecast] = Field(..., description="Weather forecasts for up to 8 days, including today")
    current: WeatherEntry = Field(..., description="Current weather information")

# Helper function to get API key
def get_api_key(provided_key: Optional[str] = None) -> str:
    """
    Get API key, prioritizing provided key, then trying to read from environment variables
    
    Parameters:
        provided_key: User-provided API key (optional)
    
    Returns:
        API key string
    """
    if provided_key:
        return provided_key
    
    env_key = os.environ.get("OPENWEATHER_API_KEY")
    if env_key:
        return env_key
    
    raise ValueError("No API key provided and no OPENWEATHER_API_KEY found in environment variables")

# Function to get location coordinates using Geocoding API
def get_coordinates(location, api_key):
    """
    Get geographic coordinates for a location name using Geocoding API
    
    Parameters:
        location: Location name as string
        api_key: OpenWeatherMap API key
        
    Returns:
        Tuple of (latitude, longitude)
    """
    try:
        # First try the Geocoding API
        geocode_url = f"https://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={api_key}"
        response = requests.get(geocode_url)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            return data[0]['lat'], data[0]['lon']
            
        # Fallback to current weather API if geocoding fails
        print("Geocoding API failed, falling back to current weather API for coordinates")
        fallback_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(fallback_url)
        response.raise_for_status()
        data = response.json()
        
        return data['coord']['lat'], data['coord']['lon']
    except Exception as e:
        print(f"Error getting coordinates: {str(e)}")
        raise

# Function to format timestamp to human-readable time
def format_timestamp(ts, tz_offset):
    """
    Convert Unix timestamp to human-readable time
    
    Parameters:
        ts: Unix timestamp
        tz_offset: Timezone offset in hours
        
    Returns:
        Formatted time string
    """
    tz = timezone(timedelta(hours=tz_offset))
    dt = datetime.fromtimestamp(ts, tz)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# Core weather forecast function using One Call API 3.0
def get_weather_forecast(present_location, time_zone_offset, api_key=None):
    # Get API key
    try:
        api_key = get_api_key(api_key)
    except ValueError as e:
        return {'error': str(e)}
    
    try:
        # Get geographic coordinates
        lat, lon = get_coordinates(present_location, api_key)
        
        # Call One Call API 3.0
        onecall_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        response = requests.get(onecall_url)
        response.raise_for_status()
        data = response.json()
        
        # Set timezone
        tz = timezone(timedelta(hours=time_zone_offset))
        
        # Process current weather
        current = data.get('current', {})
        current_weather = {
            'time': format_timestamp(current.get('dt', 0), time_zone_offset),
            'temperature': f"{current.get('temp', 0)} °C",
            'feels_like': f"{current.get('feels_like', 0)} °C",
            'temp_min': "N/A",  # One Call doesn't provide min/max in current
            'temp_max': "N/A",
            'weather_condition': current.get('weather', [{}])[0].get('description', 'Unknown'),
            'humidity': f"{current.get('humidity', 0)}%",
            'wind': {
                'speed': f"{current.get('wind_speed', 0)} m/s",
                'direction': f"{current.get('wind_deg', 0)} degrees"
            },
            'rain': f"{current.get('rain', {}).get('1h', 0)} mm/h" if 'rain' in current else 'No rain',
            'clouds': f"{current.get('clouds', 0)}%",
            'pop': "N/A"  # One Call doesn't provide precipitation probability in current
        }
        
        # Process daily forecasts
        forecasts_by_date = {}
        
        for day in data.get('daily', []):
            dt = datetime.fromtimestamp(day.get('dt', 0), tz)
            date_str = dt.date().strftime('%Y-%m-%d')
            
            # Initialize this date in the dictionary if needed
            if date_str not in forecasts_by_date:
                forecasts_by_date[date_str] = {
                    'entries': [],
                    'summary': day.get('summary', '')
                }
                    
            # Create a forecast entry for this day
            forecast_entry = {
                'time': format_timestamp(day.get('dt', 0), time_zone_offset),
                'temperature': f"{day.get('temp', {}).get('day', 0)} °C",
                'feels_like': f"{day.get('feels_like', {}).get('day', 0)} °C",
                'temp_min': f"{day.get('temp', {}).get('min', 0)} °C",
                'temp_max': f"{day.get('temp', {}).get('max', 0)} °C",
                'weather_condition': day.get('weather', [{}])[0].get('description', 'Unknown'),
                'humidity': f"{day.get('humidity', 0)}%",
                'wind': {
                    'speed': f"{day.get('wind_speed', 0)} m/s",
                    'direction': f"{day.get('wind_deg', 0)} degrees"
                },
                'rain': f"{day.get('rain', 0)} mm" if 'rain' in day else 'No rain',
                'clouds': f"{day.get('clouds', 0)}%",
                'pop': f"{day.get('pop', 0) * 100}%"  # Convert to percentage
            }
            
            forecasts_by_date[date_str]['entries'].append(forecast_entry)
            
            # Add morning, afternoon, evening entries for richer data
            # These entries help with use cases like "when should I mow my lawn"
            day_temps = day.get('temp', {})
            feels_like = day.get('feels_like', {})
            
            # Morning entry (9 AM)
            morning_time = dt.replace(hour=9, minute=0, second=0)
            forecasts_by_date[date_str]['entries'].append({
                'time': morning_time.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': f"{day_temps.get('morn', 0)} °C",
                'feels_like': f"{feels_like.get('morn', 0)} °C",
                'temp_min': f"{day_temps.get('min', 0)} °C",
                'temp_max': f"{day_temps.get('max', 0)} °C",
                'weather_condition': day.get('weather', [{}])[0].get('description', 'Unknown'),
                'humidity': f"{day.get('humidity', 0)}%",
                'wind': {
                    'speed': f"{day.get('wind_speed', 0)} m/s",
                    'direction': f"{day.get('wind_deg', 0)} degrees"
                },
                'rain': f"{day.get('rain', 0)} mm" if 'rain' in day else 'No rain',
                'clouds': f"{day.get('clouds', 0)}%",
                'pop': f"{day.get('pop', 0) * 100}%"
            })
            
            # Afternoon entry (15 PM)
            afternoon_time = dt.replace(hour=15, minute=0, second=0)
            forecasts_by_date[date_str]['entries'].append({
                'time': afternoon_time.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': f"{day_temps.get('day', 0)} °C",
                'feels_like': f"{feels_like.get('day', 0)} °C",
                'temp_min': f"{day_temps.get('min', 0)} °C",
                'temp_max': f"{day_temps.get('max', 0)} °C",
                'weather_condition': day.get('weather', [{}])[0].get('description', 'Unknown'),
                'humidity': f"{day.get('humidity', 0)}%",
                'wind': {
                    'speed': f"{day.get('wind_speed', 0)} m/s",
                    'direction': f"{day.get('wind_deg', 0)} degrees"
                },
                'rain': f"{day.get('rain', 0)} mm" if 'rain' in day else 'No rain',
                'clouds': f"{day.get('clouds', 0)}%",
                'pop': f"{day.get('pop', 0) * 100}%"
            })
            
            # Evening entry (20 PM)
            evening_time = dt.replace(hour=20, minute=0, second=0)
            forecasts_by_date[date_str]['entries'].append({
                'time': evening_time.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': f"{day_temps.get('eve', 0)} °C",
                'feels_like': f"{feels_like.get('eve', 0)} °C",
                'temp_min': f"{day_temps.get('min', 0)} °C",
                'temp_max': f"{day_temps.get('max', 0)} °C",
                'weather_condition': day.get('weather', [{}])[0].get('description', 'Unknown'),
                'humidity': f"{day.get('humidity', 0)}%",
                'wind': {
                    'speed': f"{day.get('wind_speed', 0)} m/s",
                    'direction': f"{day.get('wind_deg', 0)} degrees"
                },
                'rain': f"{day.get('rain', 0)} mm" if 'rain' in day else 'No rain',
                'clouds': f"{day.get('clouds', 0)}%",
                'pop': f"{day.get('pop', 0) * 100}%"
            })
        
        # Process hourly forecasts and add to appropriate days
        for hour in data.get('hourly', []):
            dt = datetime.fromtimestamp(hour.get('dt', 0), tz)
            date_str = dt.date().strftime('%Y-%m-%d')
            
            # Skip if we don't have this date (shouldn't happen but just in case)
            if date_str not in forecasts_by_date:
                continue
                
            # Add the hourly forecast to the appropriate day
            hourly_entry = {
                'time': format_timestamp(hour.get('dt', 0), time_zone_offset),
                'temperature': f"{hour.get('temp', 0)} °C",
                'feels_like': f"{hour.get('feels_like', 0)} °C",
                'temp_min': "N/A",  # Hourly doesn't have min/max
                'temp_max': "N/A",
                'weather_condition': hour.get('weather', [{}])[0].get('description', 'Unknown'),
                'humidity': f"{hour.get('humidity', 0)}%",
                'wind': {
                    'speed': f"{hour.get('wind_speed', 0)} m/s",
                    'direction': f"{hour.get('wind_deg', 0)} degrees"
                },
                'rain': f"{hour.get('rain', {}).get('1h', 0)} mm/h" if 'rain' in hour else 'No rain',
                'clouds': f"{hour.get('clouds', 0)}%",
                'pop': f"{hour.get('pop', 0) * 100}%"  # Convert to percentage
            }
            
            # Only add hourly entries for the first 48 hours (to keep the response size reasonable)
            current_time = datetime.now(tz)
            if (dt - current_time).total_seconds() <= 48 * 3600:  # 48 hours in seconds
                forecasts_by_date[date_str]['entries'].append(hourly_entry)
        
        # Convert dictionary to list of daily forecasts
        daily_forecasts = []
        for date_str, forecast in sorted(forecasts_by_date.items()):
            daily_forecasts.append({
                'date': date_str,
                'entries': forecast['entries'],
                'summary': forecast.get('summary', '')
            })
        
        # Return structured forecast data
        return {
            'daily_forecasts': daily_forecasts,
            'current': current_weather
        }
    except requests.RequestException as e:
        return {'error': f"Request error: {str(e)}"}
    except ValueError as e:
        return {'error': f"JSON parsing error: {str(e)}"}
    except KeyError as e:
        return {'error': f"Data structure error: Missing key {str(e)}"}
    except Exception as e:
        return {'error': f"Unexpected error: {str(e)}"}

# Define MCP tools
@mcp.tool()
def get_weather(location: str, api_key: Optional[str] = None, timezone_offset: float = 0) -> Dict[str, Any]:
    """
    Get comprehensive weather data for a location including current weather and 8-day forecast with detailed information
    
    Parameters:
        location: Location name, e.g., "Beijing", "New York", "Tokyo"
        api_key: OpenWeatherMap API key (optional, will read from environment variable if not provided)
        timezone_offset: Timezone offset in hours, e.g., 8 for Beijing, -4 for New York. Default is 0 (UTC time)
    
    Returns:
        Dictionary containing current weather and detailed forecasts for 8 days (including today)
        with morning, afternoon, and evening data points for each day
    """
    # Call weather forecast function
    return get_weather_forecast(location, timezone_offset, api_key)

@mcp.tool()
def get_current_weather(location: str, api_key: Optional[str] = None, timezone_offset: float = 0) -> Dict[str, Any]:
    """
    Get current weather for a specified location
    
    Parameters:
        location: Location name, e.g., "Beijing", "New York", "Tokyo"
        api_key: OpenWeatherMap API key (optional, will read from environment variable if not provided)
        timezone_offset: Timezone offset in hours, e.g., 8 for Beijing, -4 for New York. Default is 0 (UTC time)
    
    Returns:
        Current weather information
    """
    # Get full weather information
    full_weather = get_weather(location, api_key, timezone_offset)
    
    # Check if an error occurred
    if 'error' in full_weather:
        return full_weather
    
    # Only return current weather
    if 'current' in full_weather:
        return full_weather['current']
    else:
        return {"error": "Unable to get current weather information"}

# Start server
if __name__ == "__main__":
    # Check if environment variable is set and print log information
    if os.environ.get("OPENWEATHER_API_KEY"):
        print("API key found in environment variables")
        print("API tools are ready, can be called without api_key parameter")
    else:
        print("No API key found in environment variables")
        print("API key parameter required when calling tools")
    
    print("Weather Forecast MCP Server running...")
    mcp.run(transport='stdio')