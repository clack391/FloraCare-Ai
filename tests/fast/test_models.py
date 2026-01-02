import pytest
from src.models.schemas import PlantImageAnalysis, DiagnosisReport

def test_plant_image_analysis_valid():
    data = {
        "plant_type": "Tomato",
        "visual_symptoms": ["Yellow leaves", "Dark spots"],
        "confidence_score": 0.95,
        "description": "The plant shows signs of early blight."
    }
    analysis = PlantImageAnalysis(**data)
    assert analysis.plant_type == "Tomato"
    assert len(analysis.visual_symptoms) == 2
    assert analysis.confidence_score == 0.95

def test_plant_image_analysis_invalid():
    data = {
        "plant_type": "Tomato",
        # Missing visual_symptoms
        "confidence_score": "high" # Invalid type
    }
    with pytest.raises(ValueError):
        PlantImageAnalysis(**data)

def test_diagnosis_report_valid():
    analysis = PlantImageAnalysis(
        plant_type="Rose",
        visual_symptoms=["Black spots"],
        confidence_score=0.9,
        description="Rose black spot detected."
    )
    report = DiagnosisReport(
        analysis=analysis,
        diagnosis="Rose Black Spot",
        treatment_plan=["Prune leaves", "Apply fungicide"],
        relevant_knowledge=["Black spot is fungal..."]
    )
    assert report.diagnosis == "Rose Black Spot"
    assert len(report.treatment_plan) == 2
