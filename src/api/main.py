from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from contextlib import asynccontextmanager
import shutil
import os
import uuid
from typing import List

from src.models.schemas import DiagnosisReport, ChatRequest, ChatResponse
from src.rag.pipeline import RAGPipeline
from src.infrastructure.database import Database

# --- Lifecycle & App ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure Directories
    os.makedirs("temp_uploads", exist_ok=True)
    yield
    # Shutdown: Clean temp if needed
    pass

app = FastAPI(title="FloraCare AI API", lifespan=lifespan)

# --- Init Components (Global for now for persistent caching if needed) ---
# In a real app we might use Dependency Injection, but for MVP this is fine.
# We init pipeline per request or global? Pipeline loads heavy models 
# (SentenceTransformer, GenAI). Global is better.
pipeline_instance = None 
database = Database()

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        print("Initializing Global RAG Pipeline...")
        p = RAGPipeline()
        pipeline_instance = p.build_graph()
    return pipeline_instance

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FloraCare AI"}

@app.post("/diagnose", response_model=DiagnosisReport)
async def diagnose_plant(
    file: UploadFile = File(...),
    location: str = Form("London,UK"),
    plant_name: str = Form("My Plant"),
    user_query: str = Form(None)
):
    try:
        # 1. Save File to Disk (Temp)
        file_ext = file.filename.split('.')[-1]
        unique_name = f"{uuid.uuid4()}.{file_ext}"
        temp_path = os.path.join("temp_uploads", unique_name)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Invoke Pipeline
        workflow = get_pipeline()
        
        initial_state = {
            "image_path": temp_path,
            "user_query": user_query if user_query else "",
            "location": location,
            "plant_name": plant_name,
            "plant_id": None,
            "analysis": None,
            "retrieved_context": [],
            "weather": None,
            "history_summary": [],
            "final_report": None
        }
        
        result = await workflow.ainvoke(initial_state)
        report = result.get('final_report')
        
        if not report:
             raise HTTPException(status_code=500, detail="Diagnosis failed to generate report")
             
        # Cleanup (Optional: Keep for debug?)
        # os.remove(temp_path) 
        
        return report

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{plant_name}", response_model=List[str])
def get_history(plant_name: str):
    plant_id = database.get_plant_by_name(plant_name)
    if not plant_id:
        return []
    return database.get_recent_history(plant_id, limit=5)

@app.post("/chat", response_model=ChatResponse)
async def chat_with_context(request: ChatRequest):
    import google.generativeai as genai
    from src.core.config import settings

    try:
        # Construct Prompt
        # Convert previous messages to string
        history_text = ""
        for msg in request.history:
            history_text += f"{msg.role.upper()}: {msg.content}\n"
            
        context_str = str(request.context) # JSON dump of the diagnosis
        
        prompt = f"""
        You are an expert botanist assistant.
        
        CONTEXT (Diagnosis Report):
        {context_str}
        
        CONVERSATION HISTORY:
        {history_text}
        
        USER: {request.message}
        
        ASSISTANT:
        """
        
        # We use a lightweight model for chat to be snappy
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        return {"response": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/history/{plant_name}")
def delete_history(plant_name: str):
    plant_id = database.get_plant_by_name(plant_name)
    if not plant_id:
        # If plant doesn't exist, history is conceptually empty/deleted
        return {"status": "deleted", "plant_name": plant_name}
    
    database.delete_plant_history(plant_id)
    return {"status": "deleted", "plant_name": plant_name}

@app.get("/plants", response_model=List[str])
def list_plants():
    return database.get_all_plants()

@app.delete("/plants")
def reset_database():
    database.delete_all_plants()
    return {"status": "all_data_wiped"}
