from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
import json
import google.generativeai as genai

from src.models.schemas import PlantImageAnalysis, DiagnosisReport, KnowledgeChunk, WeatherData
from src.llm.gemini_client import GeminiClient
from src.vector_store.chroma_store import BotanicalKnowledgeBase
from src.services.weather import WeatherService
from src.infrastructure.database import Database

# Define the state
class DiagnosisState(TypedDict):
    image_path: str
    user_query: str
    location: str
    plant_name: Optional[str]
    plant_id: Optional[str]
    analysis: PlantImageAnalysis
    retrieved_context: List[KnowledgeChunk]
    weather: Optional[WeatherData]
    history_summary: List[str]
    final_report: DiagnosisReport

class RAGPipeline:
    def __init__(self):
        self.gemini = GeminiClient()
        self.kb = BotanicalKnowledgeBase()
        self.weather_service = WeatherService()
        self.db = Database()
        self.reasoning_model = genai.GenerativeModel("gemini-2.5-flash") 

    def analyze_node(self, state: DiagnosisState):
        print("--- Node: Analyze Image ---")
        # [OPTIMIZATION] The image is sent to Gemini here ONCE. 
        # The result (analysis) is text. 
        # Subsequent nodes will ONLY use the text analysis, saving tokens.
        analysis = self.gemini.analyze_image(state['image_path'])
        return {"analysis": analysis}

    def fetch_context_node(self, state: DiagnosisState):
        print("--- Node: Fetch Context (Weather & History) ---")
        location = state.get('location', 'London,UK')
        plant_name = state.get('plant_name')
        
        # Fetch Weather
        weather = self.weather_service.get_current_weather(location)
        
        # Fetch History
        history = []
        plant_id = None
        if plant_name:
            plant_id = self.db.get_plant_by_name(plant_name)
            if not plant_id:
                # Create if not exists for this MVP flow
                plant_id = self.db.create_plant(plant_name, "Unknown")
            history = self.db.get_recent_history(plant_id)
            
        return {"weather": weather, "history_summary": history, "plant_id": plant_id}

    def retrieve_node(self, state: DiagnosisState):
        print("--- Node: Retrieve Knowledge ---")
        analysis: PlantImageAnalysis = state['analysis']
        query = f"{analysis.plant_type} with {', '.join(analysis.visual_symptoms)}"
        context = self.kb.query(query, n_results=3)
        return {"retrieved_context": context}

    def diagnose_node(self, state: DiagnosisState):
        print("--- Node: Diagnose ---")
        analysis = state['analysis']
        context = state['retrieved_context']
        weather = state.get('weather')
        history = state.get('history_summary', [])
        user_query = state.get("user_query", "")

        context_text = "\n".join([f"- {c.content} (Source: {c.source})" for c in context])
        
        weather_text = "Not available"
        if weather:
            # [OPTIMIZATION] Passing only key metrics, not raw JSON
            weather_text = f"{weather.temperature}°C, {weather.humidity}% hum, {weather.condition}"

        history_text = "No previous history."
        if history:
            history_text = "\n".join(history)

        previous_diagnosis = "None"
        if history:
            # history[0] is the most recent due to ORDER BY DESC in database.py
            previous_diagnosis = history[0]

        prompt = f"""
        Act as a master botanist.
        
        ANCHOR CONTEXT (Previous Diagnosis):
        {previous_diagnosis}
        
        Patient Plant Analysis:
        - Type: {analysis.plant_type}
        - Symptoms: {', '.join(analysis.visual_symptoms)}
        - Visual Description: {analysis.description}
        
        Context Awareness:
        - Current Weather: {weather_text}
        - Plant History: {history_text}
        
        Relevant Knowledge Base:
        {context_text}
        
        User Query: {user_query}
        
        Task: Provide a diagnosis. 
        CRITICAL: Explicitly reference the Weather and History if they are relevant to the diagnosis.
        
        IF USER QUERY EXISTS ("{user_query}"):
        - Provide a direct, concise answer in "user_query_answer".
        - Base this answer on your diagnosis (e.g. "Yes, it is curable...").
        - If the query is unrelated, politely state that.

        INSTRUCTIONS FOR STABILITY:
        1. Review the 'ANCHOR CONTEXT'.
        2. Compare current visual symptoms to this baseline.
        3. CONSTRAINT: Do NOT change the diagnosis type (e.g. from 'Fungus' to 'Bacteria') unless visual evidence is overwhelming (>85% sure).
        4. Focus on PROGRESSION (improving/worsening) rather than re-identifying the disease if it matches the anchor.
        
        Return the response strictly as JSON matching the Schema:
        {{
            "analysis": ... (pass through),
            "diagnosis": "str",
            "treatment_plan": ["str"],
            "user_query_answer": "str or null",
            "relevant_knowledge": ["str"]
        }}
        """
        
        response = self.reasoning_model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json", "temperature": 0.0}
        )
        
        try:
            data = json.loads(response.text)
            data['analysis'] = analysis.model_dump() 
            # Inject weather context into report for frontend/user visibility
            if weather:
                data['weather_context'] = weather.model_dump()
                
            report = DiagnosisReport(**data)
            
            # Save to DB
            if state.get('plant_id'):
                log_id = self.db.log_diagnosis(
                    state['plant_id'], 
                    state['image_path'], 
                    analysis.model_dump(), 
                    report.diagnosis
                )
                if weather:
                    self.db.log_weather(log_id, weather.temperature, weather.humidity, weather.condition)
                    
                # [FIX] Sync DB name with detected name so history lookup works
                detected_name = analysis.plant_type
                if detected_name and detected_name != "Unknown":
                    # Update only species, keep the user's chosen name stable
                    self.db.update_plant_details(state['plant_id'], species=detected_name)
            
            return {"final_report": report}
        except Exception as e:
             raise ValueError(f"Diagnosis generation failed: {e}")

    def build_graph(self):
        workflow = StateGraph(DiagnosisState)

        workflow.add_node("analyze_image", self.analyze_node)
        workflow.add_node("fetch_context", self.fetch_context_node)
        workflow.add_node("retrieve_context", self.retrieve_node)
        workflow.add_node("generate_diagnosis", self.diagnose_node)

        workflow.set_entry_point("analyze_image")
        workflow.add_edge("analyze_image", "fetch_context")
        workflow.add_edge("fetch_context", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_diagnosis")
        workflow.add_edge("generate_diagnosis", END)

        return workflow.compile()
