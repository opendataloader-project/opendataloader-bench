# opendataloader-bench

## 1. About the Project

PDF documents are everywhere, but LLMs can't read them directly. Converting PDFs to Markdown preserves structure (headings, tables, reading order) that helps LLMs understand and answer questions accurately.

This benchmark compares open-source PDF-to-Markdown engines to help you choose the right tool for your RAG pipeline or document processing workflow.

**What we measure:**
- **Reading Order** — Is the text extracted in the correct sequence?
- **Table Fidelity** — Are tables accurately reconstructed?
- **Heading Hierarchy** — Is the document structure preserved?

The evaluation pipeline is modular—add new engines, corpora, or metrics with minimal effort.

## 2. Benchmark Results

### Quick Comparison

| Engine | Accuracy | | Speed (s/page) | | Reading Order | | Table | | Heading | |
|--------|----------|---|----------------|---|---------------|---|-------|---|---------|---|
| [opendataloader](https://pypi.org/project/opendataloader-pdf/) | 0.82 | #2 | **0.05** | #1 | **0.91** | #1 | 0.49 | #2 | 0.65 | #2 |
| [docling](https://pypi.org/project/docling/) | **0.88** | #1 | 0.73 | #4 | 0.90 | #2 | **0.89** | #1 | **0.80** | #1 |
| [pymupdf4llm](https://pypi.org/project/pymupdf4llm/) | 0.73 | #3 | 0.09 | #2 | 0.89 | #3 | 0.40 | #3 | 0.41 | #3 |
| [markitdown](https://pypi.org/project/markitdown/) | 0.58 | #4 | 0.04 | #1 | 0.88 | #4 | 0.00 | #4 | 0.00 | #4 |

> **Note**: Scores are normalized to [0, 1]. Higher is better for accuracy metrics; lower is better for speed. Bold indicates best performance.

### When to Use Each Engine

| Use Case | Recommended Engine | Why |
|----------|-------------------|-----|
| **Best overall balance** | opendataloader | Fast (0.05s/page) with high reading order accuracy |
| **Maximum accuracy** | docling | Highest scores for tables and headings, but 16x slower |
| **Speed-critical pipelines** | markitdown | Fastest, but no table/heading extraction |
| **PyMuPDF ecosystem** | pymupdf4llm | Good balance if already using PyMuPDF |

### Visual Comparison

![Benchmark Chart](charts/benchmark.png)

Detailed JSON outputs live alongside each engine and capture the exact metric values:

- [prediction/opendataloader/evaluation.json](prediction/opendataloader/evaluation.json)
- [prediction/docling/evaluation.json](prediction/docling/evaluation.json)
- [prediction/pymupdf4llm/evaluation.json](prediction/pymupdf4llm/evaluation.json)
- [prediction/markitdown/evaluation.json](prediction/markitdown/evaluation.json)

## 3. Metrics

All scores are normalised to the `[0, 1]` range, where higher indicates a closer match to ground truth. Documents missing the artefacts required by a given metric yield `null` in per-document results and are excluded from aggregate means.

### 3.1. Reading Order Similarity (NID, NID-S)

The reading order is evaluated using Normalized Indel Distance (NID), which measures the similarity between the ground truth and predicted text.

$$
NID = 1 - \frac{\text{distance}}{\text{len(gt)} + \text{len(pred)}}
$$

- **NID**: Compares the full Markdown text of the prediction against the ground truth.
- **NID-S**: Strips tables before comparison to focus on narrative reading order.

### 3.2. Table Structure Similarity (TEDS, TEDS-S)

Tables are evaluated using Tree Edit Distance Similarity (TEDS), comparing DOM structures with the APTED algorithm.

$$
{TEDS}(T_{\text{gt}}, T_{\text{pred}}) = 1 - \frac{{EditDist}(T_{\text{gt}}, T_{\text{pred}})}{\max(|T_{\text{gt}}|, |T_{\text{pred}}|, 1)}
$$

- **TEDS**: Evaluates both structure and cell text.
- **TEDS-S**: Structure-only, ignoring textual differences (e.g., OCR noise).

### 3.3. Markdown Heading-Level Similarity (MHS, MHS-S)

Headings are parsed into a flat list and compared using APTED.

$$
{MHS}(H_{\text{gt}}, H_{\text{pred}}) = 1 - \frac{{EditDist}(H_{\text{gt}}, H_{\text{pred}})}{\max(|H_{\text{gt}}|, |H_{\text{pred}}|, 1)}
$$

- **MHS**: Rewards correctly positioned headings and aligned content blocks.
- **MHS-S**: Structure-only, isolating heading topology.

### 3.4. References

- Z. Chen et al. "MDEval: Evaluating and Enhancing Markdown Awareness in Large Language Models." *arXiv:2501.15000*, 2025.
- X. Zhong et al. "Image-based Table Recognition: Data, Model, and Evaluation." *ECCV Workshops*, 2020.
- M. Pawlik and N. Augsten. "RTED: A Robust Algorithm for the Tree Edit Distance." *arXiv:1201.0230*, 2011.
- Upstage AI. "Document Parsing Benchmark (DP-Bench)." Hugging Face, 2024.

---

## 4. Reproduce the Benchmark

Want to run this benchmark yourself or add a new engine? Follow the steps below.

### Prerequisites

- Python 3.13 or higher
- Git LFS (for PDF files)

### Installation

1. **Clone and set up Git LFS**:
   ```sh
   git clone https://github.com/anthropics/opendataloader-bench.git
   cd opendataloader-bench
   git lfs install
   git lfs pull
   ```

2. **Create a virtual environment** (recommended):
   ```sh
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or: .\venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

### Running the Benchmark

#### Option A: One-shot pipeline

```sh
python src/run.py
```

This runs conversion, evaluation, history archival, and chart generation end-to-end.

#### Option B: Individual stages

```sh
# 1. Convert PDFs to Markdown
python src/pdf_parser.py

# 2. Evaluate predictions
python src/evaluator.py

# 3. (Optional) Generate charts
python src/generate_benchmark_chart.py

# 4. (Optional) Archive results
python src/generate_history.py
```

#### Targeting Specific Engines or Documents

```sh
# Single engine
python src/pdf_parser.py --engine opendataloader
python src/evaluator.py --engine opendataloader

# Single document
python src/pdf_parser.py --doc-id 01030000000001

# Both
python src/pdf_parser.py --engine opendataloader --doc-id 01030000000001
```

### Project Structure

```
├─ charts/                 # Generated benchmark charts
├─ ground-truth/           # Markdown references and source annotations
├─ history/                # Archived evaluation results by date
├─ pdfs/                   # Input PDF corpus (200 sample documents)
├─ prediction/             # Engine outputs grouped by engine/markdown
├─ src/                    # Conversion, evaluation, and utility scripts
└─ requirements.txt        # Python dependencies
```

## 5. Contributing

### Development Setup

```sh
# After following the installation steps above:
pip install -e .
```

This installs the project in editable mode so changes in `src/` are immediately reflected.

### Running Tests

```sh
pytest
```

### Interpreting `evaluation.json`

Each engine produces an `evaluation.json` with:

- **`summary`**: Engine name/version, hardware info, document count, runtime, date.
- **`metrics.score`**: Mean scores (`overall_mean`, `nid_mean`, `teds_mean`, `mhs_mean`, etc.)
- **`metrics.*_count`**: Number of documents eligible for each metric.
- **`documents`**: Per-document scores and availability flags.

## 6. References

- Z. Chen, Y. Liu, L. Shi, X. Chen, Y. Zhao, and F. Ren. "MDEval: Evaluating and Enhancing Markdown Awareness in Large Language Models." *arXiv preprint arXiv:2501.15000*, 2025. https://arxiv.org/abs/2501.15000
- J. He, M. Rungta, D. Koleczek, A. Sekhon, F. X. Wang, and S. Hasan. "Does Prompt Formatting Have Any Impact on LLM Performance?." *arXiv preprint arXiv:2411.10541*, 2024. https://arxiv.org/abs/2411.10541
- D. Min, N. Hu, R. Jin, N. Lin, J. Chen, Y. Chen, Y. Li, G. Qi, Y. Li, N. Li, and Q. Wang. "Exploring the Impact of Table-to-Text Methods on Augmenting LLM-based Question Answering with Domain Hybrid Data." *arXiv preprint arXiv:2402.12869*, 2024. https://arxiv.org/abs/2402.12869
- M. Pawlik and N. Augsten. "RTED: A Robust Algorithm for the Tree Edit Distance." *arXiv preprint arXiv:1201.0230*, 2011. https://arxiv.org/abs/1201.0230
- Upstage AI. "Document Parsing Benchmark (DP-Bench)." Hugging Face, 2024. https://huggingface.co/datasets/upstage/dp-bench
- X. Zhong, J. Tang, and A. J. Yepes. "Image-based Table Recognition: Data, Model, and Evaluation." *European Conference on Computer Vision Workshops*, 2020. https://arxiv.org/abs/1911.10683
- X. Zhong, J. Tang, and A. J. Yepes. "PubLayNet: largest dataset ever for document layout analysis." *International Conference on Document Analysis and Recognition*, 2019. https://huggingface.co/datasets/jordanparker6/publaynet
