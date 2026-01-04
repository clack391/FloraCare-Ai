from pydantic import BaseModel, Field
from typing import List, Optional

class DetectedObject(BaseModel):
    name: str
    box_2d: Optional[List[int]] = None # [ymin, xmin, ymax, xmax]

class PlantImageAnalysis(BaseModel):
    """Output from the Vision LLM analyzing the uploaded image."""
    plant_type: str = Field(..., description="Species of the plant")
    visual_symptoms: List[str] = Field(..., description="Observed issues")
    confidence: float = Field(..., ge=0, le=1)
    severity_score: Optional[float] = Field(None, ge=1, le=10, description="Severity of the condition (1-10)")
    affected_area: Optional[str] = Field(None, description="Percentage of plant affected (e.g. '15%')")
    description: str = Field(..., description="Detailed visual description of the plant condition")
    detected_objects: List[DetectedObject] = [] 

class KnowledgeChunk(BaseModel):
    """Schema for data stored in ChromaDB."""
    id: str
    content: str
    source: str
    metadata: dict

class WeatherData(BaseModel):
    temperature: float
    humidity: int
    condition: str
    location: str

class DiagnosisRequest(BaseModel):
    """Input payload for the system."""
    image_path: str
    user_query: Optional[str] = None
    location: Optional[str] = "London,UK" # Default logic location
    plant_name: Optional[str] = None # For history lookup

class DiagnosisReport(BaseModel):
    """Final output to the user."""
    analysis: PlantImageAnalysis
    diagnosis: str = Field(..., description="The medical/botanical diagnosis")
    treatment_plan: List[str] = Field(..., description="Steps to cure/mitigate")
    user_query_answer: Optional[str] = Field(None, description="Direct answer to the user's specific question")
    relevant_knowledge: List[str] = Field(..., description="Snippets from RAG used for reasoning")
    weather_context: Optional[WeatherData] = None

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    context: dict # The previous DiagnosisReport
    history: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str
