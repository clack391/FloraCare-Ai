import google.generativeai as genai
from src.core.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Name: {m.name}")
