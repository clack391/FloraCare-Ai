import sys
from pathlib import Path


# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.rag.pipeline import RAGPipeline

def diagnose_plant(image_path: str, user_query: str = "", location: str = "London,UK", plant_name: str = "My Plant"):
    pipeline = RAGPipeline()
    workflow = pipeline.build_graph()
    
    print(f"Starting diagnosis for: {image_path} (Location: {location})")
    
    # Initialize state
    initial_state = {
        "image_path": image_path,
        "user_query": user_query,
        "location": location,
        "plant_name": plant_name,
        "plant_id": None,
        "analysis": None,
        "retrieved_context": [],
        "weather": None,
        "history_summary": [],
        "final_report": None
    }
    
    # Run the graph
    result = workflow.invoke(initial_state)
    
    report = result.get('final_report')
    if report:
        print("\n=== DIAGNOSIS REPORT ===")
        print(f"Plant: {report.analysis.plant_type}")
        print(f"Condition: {report.diagnosis}")
        
        if report.weather_context:
            print(f"Weather Context: {report.weather_context.condition}, {report.weather_context.temperature}C")
            
        print("\n--- Visual Symptoms ---")
        for symptom in report.analysis.visual_symptoms:
            print(f"- {symptom}")
        
        print("\n--- Treatment Plan ---")
        for step in report.treatment_plan:
            print(f"- {step}")
            
        print("\n--- Sources ---")
        for ref in report.relevant_knowledge:
            print(f"> {ref[:100]}...") # Truncate for display
    else:
        print("Diagnosis failed to generate report.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FloraCare Diagnosis")
    parser.add_argument("image_path", help="Path to plant image")
    parser.add_argument("query", nargs="?", default="", help="User query")
    parser.add_argument("--location", default="London,UK", help="Location for weather context")
    parser.add_argument("--plant-name", default="My Plant", help="Name of plant for history tracking")
    
    args = parser.parse_args()
    
    diagnose_plant(args.image_path, args.query, args.location, args.plant_name)
