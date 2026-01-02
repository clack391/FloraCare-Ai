import sqlite3
import pandas as pd
from src.infrastructure.database import DB_PATH

def check_db():
    print(f"Checking DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    print("\n--- Plants ---")
    try:
        df_plants = pd.read_sql_query("SELECT * FROM plants", conn)
        print(df_plants)
    except Exception as e:
        print(e)
        
    print("\n--- Diagnosis Logs ---")
    try:
        df_logs = pd.read_sql_query("SELECT id, plant_id, timestamp, final_diagnosis FROM diagnosis_logs", conn)
        print(df_logs)
    except Exception as e:
        print(e)

    print("\n--- Weather Snapshots ---")
    try:
        df_weather = pd.read_sql_query("SELECT * FROM weather_snapshots", conn)
        print(df_weather)
    except Exception as e:
        print(e)
    
    conn.close()

if __name__ == "__main__":
    check_db()
