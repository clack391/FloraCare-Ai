# FloraCare AI - Phase 2 Specification: Context & Memory

## 1. Overview
**Goal**: Integrate real-time weather data and historical memory into the FloraCare diagnosis pipeline.
**Outcome**: The system will provide context-aware diagnoses (e.g., "High humidity suggests fungal risk") and track plant health over time.

## 2. Infrastructure Updates

### 2.1 Database Schema (SQLite)
File: `floracare.db` (managed by `src/infrastructure/database.py`)

**Table: `plants`**
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | TEXT (UUID) | Primary Key |
| `name` | TEXT | User-friendly name (e.g., "Backyard Tomato") |
| `species` | TEXT | Botanical classification |
| `created_at` | REAL | Timestamp |

**Table: `diagnosis_logs`**
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | TEXT (UUID) | Primary Key |
| `plant_id` | TEXT | Foreign Key -> plants.id |
| `timestamp` | REAL | Time of diagnosis |
| `image_path` | TEXT | Path to the analyzed image |
| `visual_diagnosis` | TEXT (JSON) | Raw findings from Vision LLM |
| `final_diagnosis` | TEXT | The final output string |

**Table: `weather_snapshots`**
| Column | Type | Description |
| :--- | :--- | :--- |
| `log_id` | TEXT | Foreign Key -> diagnosis_logs.id |
| `temp_c` | REAL | Temperature in Celsius |
| `humidity` | INTEGER | Humidity percentage |
| `condition` | TEXT | Short description (e.g., "Rain") |

### 2.2 Weather Service (`src/services/weather.py`)
*   **API**: OpenWeatherMap Current Weather Data (`https://api.openweathermap.org/data/2.5/weather`)
*   **Interface**:
    ```python
    def get_current_weather(location: str) -> WeatherData:
        # Returns WeatherData object or raises detailed error
    ```

## 3. Pipeline Logic Updates (`src/rag/pipeline.py`)

### 3.1 New State Definition
```python
class DiagnosisState(TypedDict):
    # ... existing fields ...
    weather: Optional[WeatherData]
    history_summary: str
```

### 3.2 New Node: `fetch_context_node`
Is inserted *after* `analyze_image` and *before* `generate_diagnosis`.
1.  **Input**: Image analysis + User location (default config or input).
2.  **Action**:
    *   Calls `WeatherService.get_current_weather`.
    *   Calls `Database.get_recent_history(plant_id)`.
3.  **Output**: Updates `state['weather']` and `state['history_summary']`.

### 3.3 Updated Node: `diagnose_node`
The prompt will be augmented:
> "Weather Context: Safe levels (25C, 40% Humidity). No recent issues."
> OR
> "Weather Context: DANGER - High Humidity (90%) and rain. Previous history: Treated for Black Spot 2 weeks ago."

## 4. Verification
*   **Mocking**: Automated tests for `WeatherService` will use `unittest.mock` to simulate JSON responses.
*   **Live**: `scripts/diagnose.py` will accept an optional `--location` flag to trigger the real API call.
