# Operational Insights AI

Repository name: `ops-insight-ai`

Operational Insights AI is a Python pipeline for extracting repeated operational keyphrases from Excel reports and classifying them into drilling-operation risk categories using Gemini.

The project reads report/log text from an Excel sheet, extracts noun-phrase keywords with spaCy, counts recurring issues, maps them back to file numbers, and optionally uses an LLM to generate a risk-ranked summary.

## Features

- Read operational report data from Excel
- Clean and normalize report text
- Extract keyphrases using spaCy noun chunks
- Count recurring phrases across records
- Map each phrase to related file numbers
- Generate analytics and summary JSON files
- Classify extracted phrases into risk categories with Gemini
- Retry Gemini requests when the model is temporarily overloaded
- Unit tests for aggregation, environment loading, and retry behavior

## Project Structure

```text
data/
  test data(2).xlsx
outputs/
  analytics.json
  summary.json
  final_risk_summary.json
src/
  aggregator.py
  cleaner.py
  excel_reader.py
  json_writer.py
  keyphrase_extractor.py
  llm_risk_analyzer.py
  summary_generator.py
tests/
  test_aggregator.py
  test_env_loader.py
  test_llm_risk_analyzer.py
main.py
risk_analysis.py
requirements.txt
```

## Input Format

Place the Excel file in the `data/` folder.

Current configured input:

```text
data/test data(2).xlsx
```

Expected Excel columns:

```text
Column A -> report/log text
Column B -> file number
```

## Setup

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

## Run Keyword Extraction

If the virtual environment is activated:

```bash
python main.py
```

Or run directly with the project interpreter:

```bash
./venv/bin/python main.py
```

This generates:

```text
outputs/analytics.json
outputs/summary.json
```

## Run Risk Analysis

Create a local `.env` file:

```bash
cp .env.example .env
```

Add your Gemini settings to `.env`:

```text
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

The real `.env` file is ignored by git, so your API key stays local.

Run the LLM risk analysis:

```bash
./venv/bin/python risk_analysis.py
```

This generates:

```text
outputs/final_risk_summary.json
```

Optional settings:

```bash
./venv/bin/python risk_analysis.py --chunk-size 25 --model gemini-2.5-flash
```

If Gemini returns `503 UNAVAILABLE` because the model is temporarily overloaded, use smaller chunks and more retries:

```bash
./venv/bin/python risk_analysis.py --chunk-size 10 --max-retries 6 --retry-delay 20
```

## Output Files

`outputs/analytics.json`

Contains extracted keyphrases, occurrence counts, and related file numbers.

`outputs/summary.json`

Contains total records processed, total keyphrases found, recurring issue count, and top repeated issues.

`outputs/final_risk_summary.json`

Contains LLM-classified risk items sorted from highest risk to lowest risk using risk level, risk score, and occurrence count.

## Pipeline

```text
Excel file
  -> read records
  -> clean text
  -> extract noun phrases with spaCy
  -> normalize phrases
  -> count recurring phrases
  -> map phrases to file numbers
  -> write analytics JSON
  -> classify risks with Gemini
  -> write final risk summary JSON
```

## Testing

Run the unit tests:

```bash
./venv/bin/python -m unittest discover -s tests -v
```

## Accuracy Notes

The system validates output structure and keeps scoring rules consistent, but true risk accuracy requires review against the original Excel context or a human-labeled answer file.

To calculate real accuracy, compare `outputs/final_risk_summary.json` against expert-reviewed labels for:

- risk vs not risk
- risk category
- risk level
- risk score

## Scalability Notes

The project uses memory-efficient data structures:

- `Counter` for phrase counts
- `defaultdict(set)` for phrase-to-file-number mapping
- one-record-at-a-time processing in the main loop

For larger datasets, the next improvement is to use spaCy `nlp.pipe()` batch processing.
