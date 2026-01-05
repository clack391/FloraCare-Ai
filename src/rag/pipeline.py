from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
import json
import google.generativeai as genai

from src.models.schemas import PlantImageAnalysis, DiagnosisReport, KnowledgeChunk, WeatherData
from src.llm.gemini_client import GeminiClient
from src.vector_store.chroma_store import BotanicalKnowledgeBase
from src.services.weather import WeatherService

# Define the state
class DiagnosisState(TypedDict):
    image_path: str
    user_query: str
    location: str
    # plant_name/id removed
    analysis: PlantImageAnalysis
    retrieved_context: List[KnowledgeChunk]
    weather: Optional[WeatherData]
    # history_summary removed
    final_report: DiagnosisReport

class RAGPipeline:
    def __init__(self):
        self.gemini = GeminiClient()
        self.kb = BotanicalKnowledgeBase()
        self.weather_service = WeatherService()
        self.reasoning_model = genai.GenerativeModel("gemini-2.5-flash") 

    def analyze_node(self, state: DiagnosisState):
        print("--- Node: Analyze Image ---")
        # [OPTIMIZATION] The image is sent to Gemini here ONCE. 
        # The result (analysis) is text. 
        # Subsequent nodes will ONLY use the text analysis, saving tokens.
        analysis = self.gemini.analyze_image(state['image_path'])
        return {"analysis": analysis}

    def fetch_context_node(self, state: DiagnosisState):
        print("--- Node: Fetch Context (Weather Only) ---")
        location = state.get('location', 'London,UK')
        
        # Fetch Weather
        weather = self.weather_service.get_current_weather(location)
        
        # History Removed
            
        return {"weather": weather}

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
        user_query = state.get("user_query", "")

        context_text = "\n".join([f"- {c.content} (Source: {c.source})" for c in context])
        
        weather_text = "Not available"
        if weather:
            # [OPTIMIZATION] Passing only key metrics, not raw JSON
            weather_text = f"{weather.temperature}°C, {weather.humidity}% hum, {weather.condition}"

        if user_query and user_query.strip():
            query_section = f"User Query: {user_query}"
            query_instructions = f"""
        IF USER QUERY EXISTS ("{user_query}"):
        - Provide a direct, concise answer in "user_query_answer".
        - Base this answer on your diagnosis (e.g. "Yes, it is curable...").
        - If the query is unrelated, politely state that.
            """
        else:
            query_section = "User Query: None"
            query_instructions = """
        NO USER QUERY PROVIDED:
        - Set "user_query_answer" to null.
        - Do NOT hallucinate a question.
            """

        prompt = f"""
        Act as a master botanist.
        
        Patient Plant Analysis:
        - Type: {analysis.plant_type}
        - Symptoms: {', '.join(analysis.visual_symptoms)}
        - Visual Description: {analysis.description}
        
        Context Awareness:
        - Current Weather: {weather_text}
        
        Relevant Knowledge Base:
        {context_text}
        
        {query_section}
        
        Task: Provide a diagnosis. 
        CRITICAL: Explicitly reference the Weather if relevant to the diagnosis.
        
        {query_instructions}
        
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
            
            # DB Logging Removed
            
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
