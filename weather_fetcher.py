"""
Weather Fetcher Module for Jarvis HR Agent
Uses OpenWeatherMap API for current weather and 5-day forecast.
"""

import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class WeatherFetcher:
    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("OpenWeatherMap API key is required.")
        self.api_key = api_key.strip()
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def fetch_current_weather(self, city: str):
        """
        Fetch current weather for a city.
        Returns: (weather_data dict, error_message str) — one will be None.
        """
        params = {"q": city, "appid": self.api_key, "units": "metric"}
        try:
            response = requests.get(f"{self.base_url}/weather", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["description"],
                "wind_speed": round(data["wind"]["speed"] * 3.6),
                "pressure": data["main"]["pressure"],
            }, None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None, f"City '{city}' not found."
            return None, f"HTTP error: {e}"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {e}"

    def fetch_forecast(self, city: str, days: int = 5):
        """
        Fetch weather forecast for a city.
        Returns: (forecast_list, error_message) — one will be None.
        """
        days = min(max(days, 3), 5)
        params = {"q": city, "appid": self.api_key, "units": "metric"}
        try:
            response = requests.get(f"{self.base_url}/forecast", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            daily_forecasts = {}
            for item in data["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                date_key = dt.strftime("%Y-%m-%d")
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        "date": dt.strftime("%A, %B %d"),
                        "temp_min": item["main"]["temp_min"],
                        "temp_max": item["main"]["temp_max"],
                        "condition": item["weather"][0]["description"],
                        "humidity": item["main"]["humidity"],
                    }
                else:
                    daily_forecasts[date_key]["temp_min"] = min(
                        daily_forecasts[date_key]["temp_min"], item["main"]["temp_min"]
                    )
                    daily_forecasts[date_key]["temp_max"] = max(
                        daily_forecasts[date_key]["temp_max"], item["main"]["temp_max"]
                    )

            forecast_list = []
            for date_key in sorted(daily_forecasts.keys())[:days]:
                f = daily_forecasts[date_key]
                f["temp_min"] = round(f["temp_min"])
                f["temp_max"] = round(f["temp_max"])
                forecast_list.append(f)

            return forecast_list, None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None, f"City '{city}' not found."
            return None, f"HTTP error: {e}"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {e}"

    def format_current_weather(self, weather_data: dict) -> str:
        if not weather_data:
            return "Unable to fetch weather data."
        return (
            f"Weather in {weather_data['city']}, {weather_data['country']}:\n"
            f"Temperature: {weather_data['temperature']}°C (Feels like {weather_data['feels_like']}°C)\n"
            f"Condition: {weather_data['condition'].capitalize()}\n"
            f"Humidity: {weather_data['humidity']}%\n"
            f"Wind Speed: {weather_data['wind_speed']} km/h\n"
            f"Pressure: {weather_data['pressure']} hPa"
        )

    def format_forecast(self, forecast_data: list) -> str:
        if not forecast_data:
            return "Unable to fetch forecast data."
        lines = [f"\n{len(forecast_data)}-Day Weather Forecast:"]
        for f in forecast_data:
            lines.append(
                f"\n{f['date']}:\n"
                f"  Temperature: {f['temp_min']}°C to {f['temp_max']}°C\n"
                f"  Condition: {f['condition'].capitalize()}\n"
                f"  Humidity: {f['humidity']}%"
            )
        return "\n".join(lines)
