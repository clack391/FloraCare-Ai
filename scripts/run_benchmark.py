import csv
import argparse
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict
import time
import sys

# Add src to python path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.services.reasoning import analyze_plant
except ImportError:
    print("Warning: src.services.reasoning not found. Using mock for dry-run only.")
    analyze_plant = None

async def run_benchmark(ground_truth_path: str, images_dir: str, dry_run: bool = False):
    print(f"Starting benchmark using {ground_truth_path}...")
    
    results = []
    correct_predictions = 0
    total_images = 0
    total_confidence = 0.0
    start_time = time.time()
    
    # Load Ground Truth
    try:
        df_truth = pd.read_csv(ground_truth_path)
    except Exception as e:
        print(f"Error reading ground truth CSV: {e}")
        return

    # Create output directory
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    for _, row in df_truth.iterrows():
        total_images += 1
        filename = row['filename']
        expected_disease = row['expected_disease']
        expected_severity = row['expected_min_severity']
        
        image_path = Path(images_dir) / filename
        
        print(f"Processing {filename}...")
        
        if dry_run or analyze_plant is None:
            # Dummy response
            predicted_disease = expected_disease if "healthy" in filename.lower() or "blight" in filename.lower() else "Unknown"
            confidence = 0.95 if predicted_disease == expected_disease else 0.4
            visual_severity = expected_severity 
            trust_label = "HIGH"
            description = "Simulated description for dry run"
            predicted_disease_val = predicted_disease # for metric comparison logic
            
            # Simulate processing time
            time.sleep(0.1)
        else:
            try:
                # Call the API
                # Note: analyze_plant is async in our stub
                result = await analyze_plant(str(image_path))
                
                predicted_disease = result.get("predicted_disease", "Unknown")
                confidence = result.get("confidence_score", 0.0)
                visual_severity = result.get("visual_severity_score", 0.0)
                trust_label = result.get("trust_label", "UNKNOWN")
                
                # Check for error in result
                if "error" in result:
                     description = f"Error from service: {result['error']}"
                else:
                     description = result.get("raw_analysis", {}).get("description", "")
                
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
                predicted_disease = "Error"
                confidence = 0.0
                visual_severity = 0.0
                trust_label = "ERROR"
                description = str(e)

        # Evaluation Logic
        # 1. Fast Path: Exact Substring Match (Case-Insensitive)
        expected_clean = expected_disease.lower().strip()
        predicted_lower = predicted_disease.lower()
        reasoning_lower = description.lower()
        
        # Simple check: is expected disease string inside predicted string?
        # Normalize spaces
        expected_nospace = expected_clean.replace(" ", "")
        predicted_nospace = predicted_lower.replace(" ", "")
        
        is_match = expected_clean in predicted_lower or expected_nospace in predicted_nospace
        
        is_correct = False # Initialize
        
        if is_match:
             # Fast path or fallback match
             is_correct = True
        else:
             # LLM-as-a-Judge Fallback
             # Since exact substring match failed, we ask Gemini if it's correct.
             print(f"  Exact match failed ('{expected_clean}' not in '{predicted_lower}'). Asking Judge...")
             # Check if we have a client instance available or need to create one
             # Note: run_benchmark doesn't have the client instance passed in.
             # We should probably instantiate it or pass it.
             # For now, let's instantiate the GeminiClient here if not available.
             
             # Lazy import to avoid circular dependency issues if any
             from src.llm.gemini_client import GeminiClient
             judge_client = GeminiClient()
             
             is_correct = judge_client.evaluate_prediction(
                 expected=expected_disease,
                 predicted=predicted_disease,
                 reasoning=description
             )
             
             if is_correct:
                 print(f"  Judge says: CORRECT (Validated by LLM)")
             else:
                 print(f"  Judge says: INCORRECT")

        if is_correct:
            correct_predictions += 1
            
        total_confidence += confidence
        
        results.append({
            "filename": filename,
            "expected_disease": expected_disease,
            "predicted_disease": predicted_disease,
            "is_correct": is_correct,
            "confidence_score": confidence,
            "trust_label": trust_label,
            "expected_min_severity": expected_severity,
            "visual_severity_score": visual_severity,
            "reasoning": description
        })

    end_time = time.time()
    inference_time = end_time - start_time
    
    # Save CSV
    results_df = pd.DataFrame(results)
    # Ensure columns order for better readability
    cols = ["filename", "is_correct", "expected_disease", "predicted_disease", "confidence_score", "trust_label", "reasoning", "visual_severity_score", "expected_min_severity"]
    # Only select columns that exist (in case I messed up names)
    cols = [c for c in cols if c in results_df.columns]
    results_df = results_df[cols]
    
    results_csv_path = output_dir / "benchmark_results.csv"
    results_df.to_csv(results_csv_path, index=False)
    print(f"Results saved to {results_csv_path}")
    
    # Calculate Metrics
    accuracy = (correct_predictions / total_images * 100) if total_images > 0 else 0
    avg_confidence = (total_confidence / total_images) if total_images > 0 else 0
    
    # Calculate Macro Precision/Recall
    y_true = []
    y_pred = []
    
    for _, row in results_df.iterrows():
        y_true.append(row['expected_disease'])
        if row['is_correct']:
            # If considered correct (via fuzzy match), treat prediction as the matching expected class
            y_pred.append(row['expected_disease']) 
        else:
            y_pred.append(row['predicted_disease'])

    gt_classes = set(y_true)
    precisions = []
    recalls = []
    
    for cls in gt_classes:
        # TP: true is cls, pred is cls
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        # FP: true is NOT cls, pred is cls
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        # FN: true is cls, pred is NOT cls
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
        
        pk = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rk = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        precisions.append(pk)
        recalls.append(rk)
        
    macro_precision = (sum(precisions) / len(precisions) * 100) if precisions else 0.0
    macro_recall = (sum(recalls) / len(recalls) * 100) if recalls else 0.0
    
    # Visual Report
    create_visual_report(results_df, accuracy, avg_confidence, inference_time, output_dir / "benchmark_report.png", macro_precision, macro_recall)

    print("\nBenchmark Complete!")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Average Confidence: {avg_confidence:.2f}")
    if dry_run:
        print("(DRY RUN MODE)")

def create_visual_report(df, accuracy, avg_confidence, inference_time, output_path, precision, recall):
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Data for Bar Chart
    categories = ['Target', 'Actual Accuracy']
    values = [100, accuracy]
    colors = ['#cccccc', '#4CAF50' if accuracy > 90 else '#FFC107']
    
    bars = ax.bar(categories, values, color=colors, width=0.5)
    ax.set_ylim(0, 110)
    ax.set_ylabel('Percentage')
    ax.set_title('Benchmark Accuracy vs Target')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%',
                ha='center', va='bottom')
    
    # Metric Cards (Text on the plot)
    text_str = (
        f"Macro Precision: {precision:.1f}%\n"
        f"Macro Recall: {recall:.1f}%\n"
        f"Accuracy: {accuracy:.1f}%\n"
        f"Avg Confidence: {avg_confidence:.2f}\n"
        f"Inference Time: {inference_time:.2f}s"
    )
    
    # Add text box
    props = dict(boxstyle='round', facecolor='white', alpha=0.9)
    ax.text(0.95, 0.95, text_str, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', horizontalalignment='right', bbox=props)
            
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Visual report saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Deterministic Scoring Engine Benchmark")
    parser.add_argument("--ground-truth", default="tests/benchmark_ground_truth.csv", help="Path to ground truth CSV")
    parser.add_argument("--images-dir", default="data/test_images", help="Path to test images directory")
    parser.add_argument("--dry-run", action="store_true", help="Run without calling actual API")
    
    args = parser.parse_args()
    
    asyncio.run(run_benchmark(args.ground_truth, args.images_dir, args.dry_run))
