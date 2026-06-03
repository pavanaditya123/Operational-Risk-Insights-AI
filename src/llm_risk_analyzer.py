import json
import os
import time
from pathlib import Path


SYSTEM_PROMPT = """
You are an operational risk classification assistant specializing in oil and gas drilling operations.

Your task is to classify extracted drilling-operation keyphrases into operational risk categories using deterministic scoring rules.

STRICT OUTPUT RULES
Return ONLY a valid JSON array.
Do not output markdown.
Do not output explanations.
Do not output code fences.
Do not output any text before or after the JSON.

Each input item MUST map to exactly one output object.

OUTPUT SCHEMA
[
  {
    "keyword": string,
    "count": integer,
    "file_numbers": array,
    "is_risk": boolean,
    "risk_level": string,
    "risk_score": integer,
    "category": string,
    "reasoning": string
  }
]

FIELD RULES
1. keyword:
   - Copy EXACTLY from input.
   - Never modify spelling, capitalization, or spacing.

2. count:
   - Copy EXACTLY from input.

3. file_numbers:
   - Copy EXACTLY from input.

4. is_risk:
   - true if operational hazard/failure/degraded condition exists.
   - false otherwise.

5. risk_level:
   Allowed values ONLY:
   [
     "High",
     "Medium",
     "Low",
     "Not Risk"
   ]

6. category:
   Allowed values ONLY:
   [
     "Wellbore Stability Risk",
     "Drilling Performance Risk",
     "Equipment Risk",
     "Hydraulic Risk",
     "Survey Risk",
     "Safety Risk",
     "Not Risk"
   ]

7. reasoning:
   - Maximum 25 words.
   - One sentence only.
   - Must reference the operational hazard OR explain why not a risk.
   - No line breaks.

RISK LEVEL DEFINITIONS
High:
  score 70-100
  Immediate threat to well integrity, personnel safety,
  equipment, or operational continuity.

Medium:
  score 40-69
  Elevated hazard or degraded performance requiring mitigation.

Low:
  score 10-39
  Minor operational issue or early warning condition.

Not Risk:
  score 0-9
  Administrative, informational, generic, or non-operational phrase.

APPROVED CATEGORIES
"Wellbore Stability Risk"
  stuck pipe, tight hole, washout, collapse, cavings

"Drilling Performance Risk"
  low ROP, vibration, bit wear, WOB issues

"Equipment Risk"
  BOP failure, pump failure, top drive issues, MWD/LWD faults

"Hydraulic Risk"
  ECD issues, lost circulation, influx, kick, ballooning

"Survey Risk"
  gyro issues, magnetic interference, depth uncertainty

"Safety Risk"
  H2S, fire, dropped object, blowout, well control events

"Not Risk"
  administrative, informational, generic, unclear phrases

CATEGORY PRIORITY ORDER
If multiple categories apply, choose in this order:

1. Safety Risk
2. Hydraulic Risk
3. Wellbore Stability Risk
4. Equipment Risk
5. Survey Risk
6. Drilling Performance Risk
7. Not Risk

MANDATORY SCORING ALGORITHM
Compute score deterministically.

Initialize:
score = 0

Add points:

+40
  Direct threat to well control or personnel safety

+25
  count >= 5

+5
  count between 2 and 4

+20
  Equipment or tool failure mentioned

+15
  Non-retrievable downhole equipment risk

+10
  Causes or implies NPT (non-productive time)

Subtract points:

-20
  Generic or administrative phrase

-10
  Routine operational procedure with no failure mode

Finalization:
- Clamp minimum score to 0
- Clamp maximum score to 100

RISK LEVEL MAPPING
70-100 -> "High"
40-69  -> "Medium"
10-39  -> "Low"
0-9    -> "Not Risk"

CLASSIFICATION RULES
1. Process EACH keyword independently.
2. Never let nearby keywords influence classification.
3. Use ONLY information present in the keyword itself.
4. Never invent operational context.
5. If uncertain, choose LOWER risk.
6. Never invent categories.
7. Never invent scores outside scoring rules.
8. Never omit fields.
9. Always return valid parseable JSON.
10. Output length MUST equal input length.

NOT RISK CONDITIONS
Classify as "Not Risk" when phrase is:

- Person name
- Job title
- Date or time reference
- Location reference
- Generic action verb
- Administrative activity
- Routine meeting
- Reporting activity
- Unclear/truncated phrase
- Routine operation without failure condition

Examples:
- "daily report"
- "morning meeting"
- "night shift"
- "reviewed parameters"
- "updated report"

AMBIGUOUS OR UNKNOWN PHRASES
If phrase lacks sufficient operational meaning:

- is_risk = false
- risk_level = "Not Risk"
- risk_score = 0
- category = "Not Risk"

Reasoning:
"Phrase lacks sufficient operational context to determine a risk."

EXAMPLES

Input:
{
  "keyword": "lost circulation",
  "count": 8,
  "file_numbers": [101,104,107]
}

Output:
{
  "keyword": "lost circulation",
  "count": 8,
  "file_numbers": [101,104,107],
  "is_risk": true,
  "risk_level": "High",
  "risk_score": 75,
  "category": "Hydraulic Risk",
  "reasoning": "Repeated fluid-loss event threatening well control."
}

---

Input:
{
  "keyword": "morning briefing",
  "count": 3,
  "file_numbers": [102,105,109]
}

Output:
{
  "keyword": "morning briefing",
  "count": 3,
  "file_numbers": [102,105,109],
  "is_risk": false,
  "risk_level": "Not Risk",
  "risk_score": 0,
  "category": "Not Risk",
  "reasoning": "Routine administrative activity with no operational hazard."
}

---

Input:
{
  "keyword": "tight hole on connections",
  "count": 4,
  "file_numbers": [103,106,108,110]
}

Output:
{
  "keyword": "tight hole on connections",
  "count": 4,
  "file_numbers": [103,106,108,110],
  "is_risk": true,
  "risk_level": "Medium",
  "risk_score": 55,
  "category": "Wellbore Stability Risk",
  "reasoning": "Recurring tight hole indicates possible wellbore instability."
}

FINAL VALIDATION
Before output:

- Ensure JSON is valid.
- Ensure array length matches input length.
- Ensure every item contains all required fields.
- Ensure keyword/count/file_numbers are unchanged.
- Ensure category values match approved categories exactly.
- Ensure risk_level matches score range exactly.
- Ensure reasoning is <= 25 words.
- Ensure no markdown or extra text exists.

Output ONLY the JSON array.
"""


ALLOWED_RISK_LEVELS = {"High", "Medium", "Low", "Not Risk"}
ALLOWED_CATEGORIES = {
    "Wellbore Stability Risk",
    "Drilling Performance Risk",
    "Equipment Risk",
    "Hydraulic Risk",
    "Survey Risk",
    "Safety Risk",
    "Not Risk",
}
TRANSIENT_GEMINI_STATUS_CODES = {429, 500, 502, 503, 504}

RISK_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "keyword": {"type": "string"},
        "count": {"type": "integer"},
        "file_numbers": {
            "type": "array",
            "items": {"type": "string"},
        },
        "is_risk": {"type": "boolean"},
        "risk_level": {
            "type": "string",
            "enum": ["High", "Medium", "Low", "Not Risk"],
        },
        "risk_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        },
        "category": {
            "type": "string",
            "enum": [
                "Wellbore Stability Risk",
                "Drilling Performance Risk",
                "Equipment Risk",
                "Hydraulic Risk",
                "Survey Risk",
                "Safety Risk",
                "Not Risk",
            ],
        },
        "reasoning": {"type": "string"},
    },
    "required": [
        "keyword",
        "count",
        "file_numbers",
        "is_risk",
        "risk_level",
        "risk_score",
        "category",
        "reasoning",
    ],
    "additionalProperties": False,
}

RISK_SCHEMA = {
    "type": "array",
    "items": RISK_ITEM_SCHEMA,
}


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def load_env_file(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")

            if key and key not in os.environ:
                os.environ[key] = value


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def chunk_items(items, chunk_size):
    for index in range(0, len(items), chunk_size):
        yield items[index:index + chunk_size]


def build_user_prompt(chunk):
    return (
        "Analyze this JSON array of repeated operational keyphrases. "
        "Return exactly one classification for every input item.\n\n"
        f"Input JSON:\n{json.dumps(chunk, ensure_ascii=False)}"
    )


def is_retryable_gemini_error(error):
    return getattr(error, "code", None) in TRANSIENT_GEMINI_STATUS_CODES


def call_gemini_for_chunk(chunk, model, max_retries=3, retry_delay=10):
    try:
        from google import genai
        from google.genai import errors as genai_errors
    except ImportError as exc:
        raise RuntimeError(
            "Google GenAI package is not installed. Run: python -m pip install google-genai"
        ) from exc

    load_env_file()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to .env or export it in your shell."
        )

    client = genai.Client(api_key=api_key)

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=build_user_prompt(chunk),
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "response_json_schema": RISK_SCHEMA,
                },
            )
            break
        except genai_errors.APIError as exc:
            if not is_retryable_gemini_error(exc) or attempt >= max_retries:
                raise RuntimeError(
                    "Gemini request failed. If the error is 503 UNAVAILABLE, "
                    "the model is temporarily overloaded; try again later or "
                    "increase --max-retries."
                ) from exc

            wait_seconds = retry_delay * (2 ** attempt)
            print(
                "Gemini temporary error "
                f"{exc.code}; retrying in {wait_seconds}s "
                f"({attempt + 1}/{max_retries})"
            )
            time.sleep(wait_seconds)

    parsed = json.loads(response.text)
    if isinstance(parsed, list):
        return parsed

    return parsed.get("risks", [])


def normalize_keyword(keyword):
    return " ".join(str(keyword).lower().split())


def validate_and_repair_risk_items(risk_items, source_items):
    risk_by_keyword = {
        normalize_keyword(item.get("keyword", "")): item
        for item in risk_items
        if item.get("keyword")
    }
    repaired = []

    for source in source_items:
        item = risk_by_keyword.get(normalize_keyword(source["keyword"]), {})
        repaired.append(repair_risk_item(item, source))

    return repaired


def repair_risk_item(item, source):
    risk_score = coerce_risk_score(item.get("risk_score", 0))
    risk_level = score_to_level(risk_score)
    category = item.get("category", "Not Risk")
    is_risk = bool(item.get("is_risk", False))

    if category not in ALLOWED_CATEGORIES:
        category = "Not Risk"

    if risk_level == "Not Risk" or category == "Not Risk":
        is_risk = False
        category = "Not Risk"
        if risk_score > 9:
            risk_score = 0
        risk_level = score_to_level(risk_score)

    reasoning = clean_reasoning(item.get("reasoning", ""))
    if not reasoning:
        reasoning = "Phrase lacks sufficient operational context to determine a risk."

    return {
        "keyword": source["keyword"],
        "count": int(source["count"]),
        "file_numbers": list(source["file_numbers"]),
        "is_risk": is_risk,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "category": category,
        "reasoning": reasoning,
    }


def coerce_risk_score(score):
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0

    return max(0, min(100, score))


def clean_reasoning(reasoning):
    reasoning = " ".join(str(reasoning).split())
    words = reasoning.split()

    if len(words) > 25:
        reasoning = " ".join(words[:25]).rstrip(".,;:") + "."

    return reasoning


def score_to_level(score):
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    if score >= 10:
        return "Low"
    return "Not Risk"


def sort_risks(risk_items):
    level_rank = {"High": 3, "Medium": 2, "Low": 1, "Not Risk": 0}
    return sorted(
        risk_items,
        key=lambda item: (
            level_rank.get(item["risk_level"], 0),
            item["risk_score"],
            item["count"],
            item["keyword"].lower(),
        ),
        reverse=True,
    )


def analyze_risks(
    analytics,
    chunk_size=25,
    model=None,
    include_not_risk=False,
    max_retries=3,
    retry_delay=10,
):
    load_env_file()
    model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    all_risks = []

    for chunk_number, chunk in enumerate(chunk_items(analytics, chunk_size), start=1):
        print(f"Analyzing risk chunk {chunk_number} ({len(chunk)} items)")
        chunk_risks = call_gemini_for_chunk(
            chunk,
            model=model,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        all_risks.extend(validate_and_repair_risk_items(chunk_risks, chunk))

    if not include_not_risk:
        all_risks = [item for item in all_risks if item["is_risk"]]

    return sort_risks(all_risks)
