import pytest
from unittest.mock import patch, MagicMock
from src.services.weather import WeatherService, WeatherData
from src.infrastructure.database import Database
import os

def test_weather_service_success():
    with patch("src.services.weather.httpx.Client") as MockClient:
        # User context manager mock
        mock_instance = MockClient.return_value.__enter__.return_value
        mock_instance.get.return_value.json.return_value = {
            "main": {"temp": 20.5, "humidity": 60},
            "weather": [{"description": "sunny"}],
            "name": "London"
        }
        mock_instance.get.return_value.status_code = 200

        service = WeatherService()
        # Mock setting api key if needed, or rely on env
        service.api_key = "test_key"
        
        weather = service.get_current_weather("London,UK")
        assert weather is not None
        assert weather.temperature == 20.5
        assert weather.humidity == 60
        assert weather.condition == "sunny"

def test_weather_service_failure():
    with patch("src.services.weather.httpx.Client") as MockClient:
        mock_instance = MockClient.return_value.__enter__.return_value
        mock_instance.get.side_effect = Exception("API Error")
        
        service = WeatherService()
        service.api_key = "test_key"
        weather = service.get_current_weather("Invalid")
        assert weather is None

def test_database_operations(tmp_path):
    # Use a temp db file
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Test Create Plant
    plant_id = db.create_plant("Tom", "Tomato")
    assert plant_id is not None
    
    # Test Get Plant
    found_id = db.get_plant_by_name("Tom")
    assert found_id == plant_id
    
    # Test Log Diagnosis
    log_id = db.log_diagnosis(plant_id, "path/img.jpg", {"symptom": "spots"}, "Blight")
    assert log_id is not None
    
    # Test Get History
    history = db.get_recent_history(plant_id)
    assert len(history) == 1
    assert "Blight" in history[0]

    # Test Log Weather
    db.log_weather(log_id, 25.0, 50, "Sunny")
