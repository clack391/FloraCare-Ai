from src.llm.gemini_client import GeminiClient
import os
import io
import PIL.Image
from src.services.vision_enhancer import enhance_image_for_ai

async def analyze_plant(image_path: str):
    """
    Analyzes a plant image using the Gemini client and adds deterministic scoring fields.
    """
    client = GeminiClient()
    
    try:
        # We need to run the blocking Gemini call in a threadpool since this function is async
        # but GeminiClient is likely synchronous (based on mypy reading, or standard usage)
        # However, for simplicity in this script, we'll just call it directly.
        # If GeminiClient.analyze_image is blocking, it will block the event loop, 
        # but for a benchmark script running sequentially, this is acceptable.
        
        # 1. Read File Bytes
        with open(image_path, "rb") as f:
            raw_bytes = f.read()
            
        # 2. Enhance
        try:
             enhanced_bytes = enhance_image_for_ai(raw_bytes)
             # Convert back to PIL for client
             img = PIL.Image.open(io.BytesIO(enhanced_bytes))
        except Exception as e:
             print(f"Benchmark Enhancement failed: {e}")
             img = PIL.Image.open(image_path)

        analysis = client.analyze_image(img)
        
        # Deterministic Scoring Logic
        # 1. Trust Label
        trust_label = "LOW"
        if analysis.confidence > 0.85:
            trust_label = "HIGH"
        elif analysis.confidence > 0.6:
            trust_label = "MEDIUM"
            
        # 2. Disease Normalization (Simple string matching for now)
        predicted_disease = "Unknown"
        if analysis.plant_type and "plant" not in analysis.plant_type.lower():
             # Relaxed check: many specific plant names don't contain "plant"
             # predicted_disease = "Not a Plant"
             # trust_label = "LOW"
             pass
        if analysis.diagnosed_disease:
             # Primary Check: Use the explicit diagnosis if available
             predicted_disease = analysis.diagnosed_disease
        
        if predicted_disease == "Unknown" and analysis.visual_symptoms:
             # Fallback: Take the first symptom as the primary disease prediction
             predicted_disease = analysis.visual_symptoms[0]
        
        return {
            "predicted_disease": predicted_disease,
            "confidence_score": analysis.confidence,
            "visual_severity_score": analysis.severity_score,
            "trust_label": trust_label,
            "raw_analysis": analysis.dict()
        }

    except Exception as e:
        return {
            "predicted_disease": "Error",
            "confidence_score": 0.0,
            "visual_severity_score": 0.0,
            "trust_label": "ERROR",
            "error": str(e)
        }
