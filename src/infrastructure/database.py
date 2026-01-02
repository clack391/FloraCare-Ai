import sqlite3
import json
import uuid
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

DB_PATH = "floracare.db"

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Plants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plants (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    name TEXT,
                    species TEXT,
                    created_at REAL
                )
            """)

            # Diagnosis Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diagnosis_logs (
                    id TEXT PRIMARY KEY,
                    plant_id TEXT,
                    timestamp REAL,
                    image_path TEXT,
                    visual_diagnosis TEXT, -- JSON stored as text
                    final_diagnosis TEXT,
                    FOREIGN KEY(plant_id) REFERENCES plants(id)
                )
            """)

            # Weather Snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_snapshots (
                    log_id TEXT,
                    temp_c REAL,
                    humidity INTEGER,
                    condition TEXT,
                    FOREIGN KEY(log_id) REFERENCES diagnosis_logs(id)
                )
            """)
            conn.commit()

    def create_plant(self, name: str, species: str, user_id: str = "default_user") -> str:
        plant_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO plants (id, user_id, name, species, created_at) VALUES (?, ?, ?, ?, ?)",
                (plant_id, user_id, name, species, time.time())
            )
        return plant_id
    
    def get_all_plants(self) -> List[str]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT DISTINCT name FROM plants ORDER BY created_at DESC")
            return [row[0] for row in cursor.fetchall()]

    def get_plant_by_name(self, name: str) -> Optional[str]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT id FROM plants WHERE name = ?", (name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def update_plant_details(self, plant_id: str, new_name: str, species: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE plants SET name = ?, species = ? WHERE id = ?", (new_name, species, plant_id))
            conn.commit()

    def log_diagnosis(self, plant_id: str, image_path: str, visual_diagnosis: Dict[str, Any], final_diagnosis: str) -> str:
        log_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO diagnosis_logs 
                   (id, plant_id, timestamp, image_path, visual_diagnosis, final_diagnosis) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (log_id, plant_id, time.time(), image_path, json.dumps(visual_diagnosis), final_diagnosis)
            )
        return log_id

    def log_weather(self, log_id: str, temp: float, humidity: int, condition: str):
         with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO weather_snapshots (log_id, temp_c, humidity, condition) VALUES (?, ?, ?, ?)",
                (log_id, temp, humidity, condition)
            )

    def get_recent_history(self, plant_id: str, limit: int = 3) -> List[str]:
        """Returns a list of recent diagnosis summaries for context."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT timestamp, final_diagnosis FROM diagnosis_logs WHERE plant_id = ? ORDER BY timestamp DESC LIMIT ?",
                (plant_id, limit)
            )
            rows = cursor.fetchall()
            
        history = []
        for ts, diag in rows:
            date_str = time.strftime('%Y-%m-%d', time.localtime(ts))
            history.append(f"[{date_str}] {diag}")
        return history

    def delete_plant_history(self, plant_id: str):
        """Deletes all history for a specific plant."""
        with self._get_conn() as conn:
            # First delete related weather snapshots (cascade simulation)
            conn.execute(
                "DELETE FROM weather_snapshots WHERE log_id IN (SELECT id FROM diagnosis_logs WHERE plant_id = ?)",
                (plant_id,)
            )
            # Then delete diagnosis logs
            conn.execute("DELETE FROM diagnosis_logs WHERE plant_id = ?", (plant_id,))
            conn.commit()
