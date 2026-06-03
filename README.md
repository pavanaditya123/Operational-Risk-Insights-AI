# Operational Keyword Extraction System

This project extracts repeated operational keyphrases from an Excel sheet and generates analytics summaries.

## Input Format

Place the Excel file in the `data/` folder.

Current configured file:

```text
data/test data(2).xlsx
```

Expected Excel format:

```text
Column A -> information/report/log text
Column B -> file number
```

## Output

The program generates:

```text
outputs/analytics.json
outputs/summary.json
```

`analytics.json` contains all extracted keyphrases, their counts, and related file numbers.

`summary.json` contains total records processed, total keyphrases found, recurring issue count, and top repeated issues.

## Installation

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Run

```bash
python main.py
```

## Pipeline

```text
Excel file
  -> read records
  -> clean text
  -> extract noun phrases with spaCy
  -> normalize phrases
  -> count repeated phrases
  -> map phrases to file numbers
  -> write JSON output
```

## Scalability Notes

The project uses memory-efficient data structures:

- `Counter` for phrase counts
- `defaultdict(set)` for phrase-to-file-number mapping
- one-record-at-a-time processing in the main loop

For larger datasets, the next improvement is to use spaCy `nlp.pipe()` batch processing.

## LLM Risk Analysis

After generating `outputs/analytics.json`, you can classify repeated keyphrases into operational risks using Gemini 2.5 Flash.

Set your API key:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

Run risk analysis:

```bash
python risk_analysis.py
```

Optional settings:

```bash
python risk_analysis.py --chunk-size 25 --model gemini-2.5-flash
```

This generates:

```text
outputs/final_risk_summary.json
```

The risk output is sorted from highest risk to lowest risk using risk level, risk score, and occurrence count.
# exceldocumentkeywordextractor
