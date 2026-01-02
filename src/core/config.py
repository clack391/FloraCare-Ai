import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    EMBEDDING_MODEL = "models/embedding-001" # Using Gemini embeddings for consistency

settings = Settings()

if not settings.GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY is not set in environment variables.")
