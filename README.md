# opendataloader-bench

## 1. About the Project
This repository benchmarks PDF-to-Markdown extraction engines using a shared corpus and harmonised evaluation pipeline. It normalises predictions into Markdown, compares them against curated ground-truth annotations, and reports quality metrics for reading order, table fidelity, and heading hierarchy. The tooling is modular so new engines, corpora, or scoring routines can be slotted in with minimal effort.

## 2. Benchmark Results
![Benchmark Chart](charts/benchmark.png)

Recent runs are summarised by the chart above.

Detailed JSON outputs live alongside each engine/version pair and capture the exact metric values used to render the plot:

- [prediction/opendataloader/evaluation.json](prediction/opendataloader/evaluation.json)
- [prediction/docling/evaluation.json](prediction/docling/evaluation.json)
- [prediction/pymupdf4llm/evaluation.json](prediction/pymupdf4llm/evaluation.json)
- [prediction/markitdown/evaluation.json](prediction/markitdown/evaluation.json)

### 2.1. Interpreting `evaluation.json`
- **Top-level keys**: `summary` (run metadata), `metrics` (corpus aggregates), and `documents` (per-file breakdowns).
- **`summary`** records engine name/version, hardware info, document count, total runtime, and measurement date.
- **`metrics.score`** lists the mean for each metric
    - `overall_mean` is the average of `nid_mean`, `teds_mean`, and `mhs_mean`.
    - `nid_mean` is the average NID, normalized indel distance score for reading order.
    - `nid_s_mean` is the average NID-S, normalized indel distance tables stripped score for reading order with tables stripped.
    - `teds_mean` is the average TEDS, table edit distance score for table structure and content
    - `teds_s_mean` is the average TEDS-S, table edit distance structure only score for table structure only.
    - `mhs_mean` is the average MHS, markdown heading-level score for headings and content.
    - `mhs_s_mean` is the average MHS-S, markdown heading-level structure only score for headings only.
- **`metrics.*_count`** entries show how many documents were eligible for each metric.
    - Some documents may lack tables or headings, making them ineligible for `teds` or `mhs` scoring respectively.
    - Metrics are averaged over the eligible subset
    - `missing_predictions` counts documents where no output was produced at all.
- **Each `documents` entry** contains `document_id`, per-metric `scores`, and a `prediction_available` flag to highlight missing outputs

## 3. Project Structure
```
├─ ground-truth/           # Markdown references and source annotations
├─ pdfs/                   # Input PDF corpus (200 sample documents by default)
├─ pdfs_thumbnail/         # WebP thumbnails produced from the first PDF page
├─ prediction/             # Engine outputs grouped by engine/version/markdown
├─ src/                    # Conversion, evaluation, and utility scripts
└─ requirements.txt        # Python dependencies for all scripts
```
Key scripts:
1. `src/run.py` provides a single entry point that runs conversion, evaluation, history archival, and chart generation sequentially.
2. `src/pdf_parser.py` drives batch conversion across registered engines and records timing metadata.
3. `src/evaluator.py` aggregates metric scores into `evaluation.json` for every engine/version pair.
4. `src/generate_benchmark_chart.py` renders benchmark charts for quick visual inspection from existing `evaluation.json` files.
5. `src/generate_history.py` archives the latest evaluation files into date-stamped folders under `history/`.
6. `src/powermetrics.sh` captures CPU/GPU/ANE power usage with macOS `powermetrics` while each engine runs (Apple Silicon).
7. `src/generate_powermetrics.py` converts raw `powermetrics.txt` logs into `powermetrics.json` with average power and total energy per engine.

## 4. Prerequisites

- Python 3.13 or higher.
- Git LFS

## 5. Getting Started

### Git LFS Setup

This repository uses Git LFS to manage large PDF files. Before cloning or working with the repository, ensure you have Git LFS installed and configured.

1.  **Install Git LFS**: Follow the instructions on the [Git LFS website](https://git-lfs.com/) to install it for your operating system.
2.  **Set up Git LFS for this repository**: Once installed, navigate to the repository's root directory in your terminal and run:
    ```sh
    git lfs install
    git lfs pull
    ```
    This will download the actual PDF files managed by Git LFS.

### Installation

1. (Strongly Recommended) create and activate a virtual environment.  
   > Always work inside a virtual environment (`venv`) to keep project dependencies isolated and prevent version conflicts with other Python projects on your system.
   > If you want to deactivate venv, run the `deactivate` command.

   Example:
   ```sh
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

### Running the Benchmark

You can either run the full pipeline with a single command or execute each stage manually.

#### Option A: One-shot pipeline (`src/run.py`)

`src/run.py` orchestrates conversion, evaluation, history archival, and benchmark chart generation end-to-end:

```sh
python src/run.py
```

#### Option B: Individual stages

1. **Run Conversions**: Use `src/pdf_parser.py` to convert PDFs to Markdown for all registered engines.

```sh
python src/pdf_parser.py
```

2. **Evaluate Predictions**: Use `src/evaluator.py` to evaluate the generated Markdown against the ground truth.

```sh
python src/evaluator.py
```

Each engine directory inside `prediction/` should follow the layout `prediction/<engine>/<version>/markdown/*.md`, accompanied by an automatically generated `summary.json` and `evaluation.json` once the scripts above are executed.

3. **(Optional) Generate Benchmark Charts**: Use `src/generate_benchmark_chart.py` for quick visual inspection of the PDFs.

```sh
python src/generate_benchmark_chart.py
```

Charts will be saved in the `charts/` directory.

4. **(Optional) Archiving evaluation history**: To archive existing evaluation outputs without re-running the full pipeline, use `src/generate_history.py`. It copies each `prediction/<engine>/evaluation.json` into `history/<yymmdd>/<engine>/evaluation.json`.

```sh
python src/generate_history.py
```

#### (Optional) Capture Power Usage (macOS powermetrics)

To record CPU/GPU/ANE power while each engine runs, use `src/powermetrics.sh` on Apple Silicon:

```sh
PYTHON=python3 sudo bash src/powermetrics.sh
```

- The script iterates over the engines listed in `ENGINES` (docling, markitdown, opendataloader by default), starts `powermetrics` sampling every 1s, runs `src/pdf_parser.py --engine <name>`, then stops sampling. Logs are saved to `prediction/<engine>/powermetrics.txt`.
- Once logs exist, aggregate them into JSON for charting/analysis:

```sh
python src/generate_powermetrics.py
```

This writes `prediction/<engine>/powermetrics.json` with average power and total energy figures that are picked up by `generate_benchmark_chart.py` (energy chart).


### Targeting Specific Engine or Document ID

By default, the conversion and evaluation scripts run on all available engines. To target a specific one, use the `--engine` and/or `--doc-id` flags.

```sh
# Example: Run conversion and evaluation for a specific engine
python src/pdf_parser.py --engine opendataloader-pdf
python src/evaluator.py --engine opendataloader-pdf
```

```sh
# Example: Run conversion and evaluation for a specific document ID
python src/pdf_parser.py --doc-id 01030000000001
python src/evaluator.py --doc-id 01030000000001
```

```sh
# Example: Run conversion and evaluation for a specific engine and document ID
python src/pdf_parser.py --engine opendataloader-pdf --doc-id 01030000000001
python src/evaluator.py --engine opendataloader-pdf --doc-id 01030000000001
```

## 6. Development and Testing

To contribute to this project, you'll need to set up a development environment that allows you to run the test suite.

### Setting up the Environment

1. (Strongly Recommended) create and activate a virtual environment.  
   > Always work inside a virtual environment (`venv`) to keep project dependencies isolated and prevent version conflicts with other Python projects on your system.
   > If you want to deactivate venv, run the `deactivate` command.

   Example:
   ```sh
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Install the project in editable mode for development: 
   ```sh
   pip install -e .
   ```
   This ensures that any changes in the src/ directory are immediately reflected without reinstalling the package.

4. (Optional) If you are using VS Code, you may need to restart Python Intellisense after installing the project in editable mode (`pip install -e .`)
   1. Open the Command Palette (`Ctrl+Shift+P` on Windows/Linux, `Cmd+Shift+P` on macOS).
   2. Search for **"Python: Restart Language Server"** and run it.
   3. Alternatively, restart VS Code entirely.

   Make sure the selected Python interpreter in the VS Code status bar points to the correct virtual environment (e.g., `.venv`) to ensure imports are recognized correctly.


### Running Tests

Once the project is installed in editable mode, you can run the full test suite with a single command:

```sh
pytest
```

This will automatically discover and run all tests.

## 7. Metrics
All scores are normalised to the `[0, 1]` range, where higher indicates a closer match to ground truth. Documents missing the artefacts required by a given metric yield `null` in per-document results and are excluded from aggregate means. The evaluator also computes an `overall_average`, defined as the arithmetic mean of the available metric scores for a document.

### 7.1. Reading Order Similarity (NID, NID-S)
The reading order is evaluated using two metrics based on Normalized Indel Distance (NID), which measures the similarity between the ground truth and predicted text. These metrics provide a score that is sensitive to text length.

$$
NID = 1 - \frac{\text{distance}}{\text{len(gt)} + \text{len(pred)}}
$$

- **`nid` (Normalized Indel Distance)**: This metric compares the full Markdown text of the prediction against the ground truth. It evaluates the overall similarity, including all content.

- **`nid_s` (Normalized Indel Distance - Stripped)**: This metric provides a more focused evaluation of the narrative reading order. Before comparison, tables (both HTML and Markdown formats) are stripped from both the ground truth and the prediction, and repeated whitespace is collapsed. This ensures that the score reflects the correctness of the body text flow, independent of table formatting.

### 7.2. Table Structure Similarity (TEDS, TEDS-S)
`evaluate_table` extracts the first table (preferring HTML markup, then falling back to Markdown heuristics) and evaluates it with the Tree Edit Distance Similarity (TEDS) proposed for table structure assessment. The table DOMs are converted into labelled trees and compared using the APTED algorithm with custom tokenization.

$$
{TEDS}(T_{\text{gt}}, T_{\text{pred}}) = 1 - \frac{{EditDist}(T_{\text{gt}}, T_{\text{pred}})}{\max(|T_{\text{gt}}|, |T_{\text{pred}}|, 1)}
$$

`TEDS` evaluates both structure and cell text. `TEDS-S` switches the rename cost to be structure-only, isolating layout fidelity when textual mismatches are considered acceptable (for example, OCR noise).

### 7.3. Markdown Heading-Level Similarity (MHS, MHS-S)
`evaluate_heading_level` parses Markdown into a flat list of heading nodes and associated content blocks while skipping detected tables. Both hierarchies are compared twice with APTED: once with content-aware rename penalties and once with pure structural penalties. The resulting Markdown Heading-Level Similarity (MHS) scores are defined as:

$$
{MHS}(H_{\text{gt}}, H_{\text{pred}}) = 1 - \frac{{EditDist}(H_{\text{gt}}, H_{\text{pred}})}{\max(|H_{\text{gt}}|, |H_{\text{pred}}|, 1)}
$$

`MHS` rewards both correctly positioned headings and well-aligned content blocks, while `MHS-S` isolates the heading topology to flag missing or mislevelled sections even when the surrounding prose overlaps.

### 7.4. Power Measurement Algorithm (`generate_powermetrics.py`)
- **Input**: `prediction/<engine>/powermetrics.txt` logs generated by `powermetrics.sh` with 1s sampling cadence.
- **Parsing**: Extract per-sample elapsed time plus CPU/GPU/ANE/Combined power (mW) via regex. If elapsed time is missing, assume 1000 ms. Each matched block becomes one sample.
- **Averaging**: Compute mean power for every metric present and round to two decimals (`avg_*_power_mw`).
- **Energy**: Convert each sample’s milliwatts to watts, multiply by its elapsed seconds, and sum to Joules (`total_*_energy_j`). Also report `power_sample_count` and `total_elapsed_seconds`.
- **Output**: Write the aggregated values to `prediction/<engine>/powermetrics.json`, which downstream charting reads to render the energy consumption bar.

### 7.5. References

- Z. Chen, Y. Liu, L. Shi, X. Chen, Y. Zhao, and F. Ren. "MDEval: Evaluating and Enhancing Markdown Awareness in Large Language Models." *arXiv preprint arXiv:2501.15000*, 2025. https://arxiv.org/abs/2501.15000
- J. He, M. Rungta, D. Koleczek, A. Sekhon, F. X. Wang, and S. Hasan. "Does Prompt Formatting Have Any Impact on LLM Performance?." *arXiv preprint arXiv:2411.10541*, 2024. https://arxiv.org/abs/2411.10541
- D. Min, N. Hu, R. Jin, N. Lin, J. Chen, Y. Chen, Y. Li, G. Qi, Y. Li, N. Li, and Q. Wang. "Exploring the Impact of Table-to-Text Methods on Augmenting LLM-based Question Answering with Domain Hybrid Data." *arXiv preprint arXiv:2402.12869*, 2024. https://arxiv.org/abs/2402.12869
- M. Pawlik and N. Augsten. "RTED: A Robust Algorithm for the Tree Edit Distance." *arXiv preprint arXiv:1201.0230*, 2011. https://arxiv.org/abs/1201.0230
- Upstage AI. "Document Parsing Benchmark (DP-Bench)." Hugging Face, 2024. https://huggingface.co/datasets/upstage/dp-bench
- X. Zhong, J. Tang, and A. J. Yepes. "Image-based Table Recognition: Data, Model, and Evaluation." *European Conference on Computer Vision Workshops*, 2020. https://arxiv.org/abs/1911.10683
- X. Zhong, J. Tang, and A. J. Yepes. "PubLayNet: largest dataset ever for document layout analysis." *International Conference on Document Analysis and Recognition*, 2019. https://huggingface.co/datasets/jordanparker6/publaynet
