# Benchmark Suite

This suite validates the output of the FloraCare AI Deterministic Scoring Engine against a set of ground truth images.

## Setup

1.  **Images**: Place your test images in `data/test_images/`. The filenames must match those in `tests/benchmark_ground_truth.csv`.
2.  **Ground Truth**: define expectations in `tests/benchmark_ground_truth.csv`.

## Running the Benchmark

Run the script from the project root:

```bash
python scripts/run_benchmark.py
```

### Options

*   `--dry-run`: Run the script without making actual API calls to Gemini. Useful for testing the pipeline and generating sample reports.
*   `--ground-truth`: Path to a custom CSV file (default: `tests/benchmark_ground_truth.csv`).
*   `--images-dir`: Path to the image directory (default: `data/test_images`).

## Outputs

*   **Console**: Summary of accuracy and confidence.
*   **`data/benchmark_results.csv`**: Detailed row-by-row results including predicted vs expected values.
*   **`data/benchmark_report.png`**: A visual report card summarizing the run.

## Troubleshooting

If you see "Warning: src.services.reasoning not found", ensure your environment is set up correctly. The script includes a mock fallback for dry runs.
