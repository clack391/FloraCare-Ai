import pytest
from pathlib import Path
from src.rag.pipeline import RAGPipeline
from src.vector_store.chroma_store import BotanicalKnowledgeBase

# Mark as slow integration test
@pytest.mark.skip(reason="Requires valid API Key and enviroment")
def test_pipeline_integration():
    """
    Tests the full pipeline. Requires GOOGLE_API_KEY and a test image.
    """
    pipeline = RAGPipeline()
    workflow = pipeline.build_graph()
    
    # Needs a real image path
    image_path = "test_images/sick_plant.jpg"
    if not Path(image_path).exists():
        pytest.skip("Test image not found")

    state = {
        "image_path": image_path,
        "user_query": "What is wrong?",
        "analysis": None,
        "retrieved_context": [],
        "final_report": None
    }
    
    result = workflow.invoke(state)
    report = result.get('final_report')
    
    assert report is not None
    assert report.analysis.plant_type != ""
    assert len(report.treatment_plan) > 0

@pytest.mark.skip(reason="Requires valid API Key")
def test_chroma_integration():
    kb = BotanicalKnowledgeBase()
    # Clean up or use test collection in real scenario
    kb.add_documents(
        documents=["Test content about plants."],
        metadatas=[{"source": "test"}],
        ids=["test_1"]
    )
    results = kb.query("plants", n_results=1)
    assert len(results) > 0
    assert results[0].content == "Test content about plants."
