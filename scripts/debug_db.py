import sqlite3
import pandas as pd

DB_PATH = "floracare.db"

def inspect_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        
        print("--- Table: Plants ---")
        plants = pd.read_sql_query("SELECT id, name, species FROM plants", conn)
        print(plants)
        
        print("\n--- Table: Diagnosis Logs ---")
        logs = pd.read_sql_query("SELECT * FROM diagnosis_logs", conn)
        # Truncate large columns for display
        if 'visual_diagnosis' in logs.columns:
            logs['visual_diagnosis'] = logs['visual_diagnosis'].str[:50] + "..."
        print(logs)
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
