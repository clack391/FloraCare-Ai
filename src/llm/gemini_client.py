import google.generativeai as genai

import json
from pathlib import Path
from src.core.config import settings
from src.models.schemas import PlantImageAnalysis

# Configure the SDK
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)

class GeminiClient:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json", "temperature": 0.0}
        )

    def analyze_image(self, image_path: str) -> PlantImageAnalysis:
        """
        Analyzes an image using Gemini Vision capabilities and returns structured data.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")

        # Upload the file to Gemini
        # Note: For production, we might want to handle file cleanup or use inline data if small.
        # For this phase, we'll try uploading or using the PIL image approach if supported by the updated SDK.
        # But 'upload_file' is the standard way for the File API.
        
        try:
            sample_file = genai.upload_file(path=path, display_name="Plant Image")
            
            prompt = """
            Analyze this plant image. Identify the plant type, "visual_symptoms" (list of strings), 
            provide a "confidence" score (0.0-1.0), and a "description".
            
            METRICS: Estimate the "severity_score" (1-10, where 10 is dead) and "affected_area" (e.g. "15%").
            
            CRITICAL TASK: You MUST identify localized symptoms (e.g. "leaf spot", "yellowing") and return "detected_objects".
            For each object, provide "box_2d" as [ymin, xmin, ymax, xmax] normalized to 1000 (e.g. [100, 200, 300, 400]).
            If you see symptoms, you MUST return at least one detected object.
            LIMITATION: Return a MAXIMUM of 20 detected objects. If there are more, prioritize the largest or most severe ones.
            
            Return strictly JSON:
            {
                "plant_type": "str",
                "diagnosed_disease": "str",
                "visual_symptoms": ["str"],
                "confidence": float,
                "severity_score": float,
                "affected_area": "str",
                "description": "str",
                "detected_objects": [
                    {"name": "str", "box_2d": [int, int, int, int]}
                ]
            }
            """

            response = self.model.generate_content([sample_file, prompt])
            
            # Parse the JSON response
            response_json = json.loads(response.text)
            return PlantImageAnalysis(**response_json)
            
        except Exception as e:
            # Wrap errors or log them
            raise RuntimeError(f"Gemini analysis failed: {e}")

    def evaluate_prediction(self, expected: str, predicted: str, reasoning: str) -> bool:
        """
        Uses the LLM to judge if a predicted disease matches the expected disease,
        considering synonyms and context.
        """
        prompt = f"""
        You are an expert plant pathologist acting as a judge for an AI benchmark.
        
        Task: Determine if the PREDICTED diagnosis is correct given the EXPECTED diagnosis.
        
        Context:
        - EXPECTED: "{expected}"
        - PREDICTED: "{predicted}"
        - REASONING: "{reasoning}"
        
        Rules:
        1. Ignore minor spelling differences or capitalization.
        2. Accept synonyms (e.g., "Edge Burn" == "Environmental Stress" if context implies it).
        3. Accept if the expected disease is a specific type of the predicted category (e.g. "Pear Rust" is a type of "Rust").
        4. Be strict about completely different diseases (e.g. "Blight" != "Rust").
        
        Question: Is the prediction CORRECT?
        Return ONLY the JSON: {{"is_correct": boolean}}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get("is_correct", False)
        except Exception as e:
            print(f"Evaluation failed: {e}")
            return False
