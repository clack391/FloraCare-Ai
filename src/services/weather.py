import httpx
from typing import Optional
from pydantic import BaseModel
from src.core.config import settings

class WeatherData(BaseModel):
    temperature: float
    humidity: int
    condition: str
    location: str

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY

    def get_current_weather(self, location: str) -> Optional[WeatherData]:
        """
        Fetches current weather for a given location string (e.g., "London,UK").
        Returns None if API key is missing or request fails.
        """
        if not self.api_key:
            print("WARNING: OPENWEATHER_API_KEY not set.")
            return None

        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric" # Celsius
            }
            # Using synchronous request for simplicity in Phase 2 pipeline
            with httpx.Client(timeout=5.0) as client:
                response = client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                return WeatherData(
                    temperature=data["main"]["temp"],
                    humidity=data["main"]["humidity"],
                    condition=data["weather"][0]["description"],
                    location=data["name"]
                )
        except Exception as e:
            print(f"Weather fetch failed for {location}: {e}")
            return None
