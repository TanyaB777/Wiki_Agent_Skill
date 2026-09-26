---
name: wikipedia-market-analyzer
description: Analyzes market interest trends across different languages using Wikipedia pageview metrics. Use this skill when founders or product teams need to evaluate expanding into new topics or localizing products into new languages, generate comparison trend charts, and export single-page PDF reports.
license: Apache-2.0
metadata:
  author: Tetiana Bilka
  version: "1.0"
---

# Wikipedia Market Interest Analyzer

Use this skill to guide B2C product strategy decisions (e.g., launching new courses, adding topics, or localizing apps into new languages) by analyzing Wikipedia pageview dynamics.

## Workflow Execution Steps

Follow this explicit 4-step sequence when handling user requests:

### Step 1: Candidate Search & Title Resolution

Before fetching any pageview metrics, analyze the user's request to identify the target language code and the primary topic/concept. Never guess or assume exact Wikipedia article titles.

1. Language & Topic Extraction Rules
Language Detection: Identify the target Wikipedia language section (e.g., uk for Ukrainian, en for English, pl for Polish). If unspecified, default to en or ask the user.

Topic Extraction: Extract the primary concept/keyword from the prompt in the target language (e.g., "intermittent fasting" for English).

2. Candidate Search
Execute scripts/fetcher.py to retrieve exact article candidates for the target language and topic:

```python
from scripts.fetcher import find_wikipedia_candidates

candidates = find_wikipedia_candidates(
    query="intermittent fasting",
    lang="en",
    limit=5
)
```

3. Title Resolution & Decision Logic
Single Clear Match: If the top result accurately matches the intended topic, select its exact canonical title and proceed to Step 2.

Ambiguous Matches: If multiple relevant candidates exist or the query hits a disambiguation page, list the top candidate titles/snippets and ask the user to select the correct one.

No Results Found: If no candidates are returned, suggest alternative keywords or ask the user to refine the topic.

4. Output Parameters
Store the resolved tuple (lang, exact_title) to pass cleanly into the data fetching phase (Step 2).

### Step 2: Historical Pageview & Trend Analysis

1. Use the primary canonical title and language code resolved in Step 1, extract target languages and date ranges from the prompt, and retrieve historical traffic metrics using `scripts/fetcher.py`.

2. Parameter Extraction & Normalization Rules

* **Source Title & Source Language (`source_title`, `source_lang`):**
  Pass the exact canonical title and language code obtained from Step 1 (e.g., `source_title="Intermittent fasting"`, `source_lang="en"`).
* **Target Languages (`target_languages`):**
  Extract all additional language codes requested by the user (e.g., `["pl", "cs"]`).
  - If the user explicitly asks for cross-language comparison, include the requested languages.
  - If no additional target languages are specified, pass `target_languages=None` (or an empty list) to analyze only the primary language.
* **Date Range (`start_date`, `end_date`):**
  - Parse relative date mentions (e.g., "for the last two years" → calculate `start_date` as 24 months prior to current date, `end_date` as today/current month).
  - Use format `YYYY-MM-DD`.
  - **Missing Timeframe Clarification:** If the timeframe/period is completely missing from the user's prompt and cannot be inferred, ask the user to clarify the desired analysis period before proceeding, or suggest standard presets (e.g., last 6, 12, or 24 months).
  - **Date Resolution:** Always determine the current date dynamically at execution time. Never rely on hardcoded dates.
  - Never hardcode dates from examples. Always evaluate end_date as the current date ($T$) and start_date as $T - \text{requested timeframe}$ (default: $T - 24\ \text{months}$).
* **Normalization Mode (`normalize`):**
  - **`normalize=True` (PPM - Parts Per Million):** MUST be set when comparing two or more different language sections (e.g., Polish vs. Czech) to reduce the effect of differences in the absolute size of Wikipedia language sections.
  - **`normalize=False` (Raw Pageviews):** Use ONLY when analyzing absolute demand within a single language section.

```python
from scripts.fetcher import WikipediaTrendAnalyzer

analyzer = WikipediaTrendAnalyzer()

# Execute analysis with resolved and extracted parameters
result = analyzer.analyze_trends_by_title(
    source_title="Intermittent fasting",  # Passed from Step 1
    source_lang="en",                      # Passed from Step 1
    target_languages=["pl", "cs"],          # Parsed from user prompt
    start_date="2024-09-01",               # Calculated dynamically
    end_date="2026-09-01",                 # Calculated dynamically
    normalize=True                         # True for multi-language comparison
)
```

3. Output Requirements
The analysis result must include:
Raw and Normalized Metrics: Total views, average monthly views, and growth rates.

Note: Target language page titles are automatically resolved via Wikipedia's langlinks API for source_title.

### Step 3: Visualization & PDF Report Generation

Generate trend charts and compile a single-page executive PDF report:

```python
from scripts.report import generate_pdf_report

# Generates PDF report with embedded chart and formatted metric tables
# result is produced in Step 2
generate_pdf_report(
    trend_results=result # Result dict/dataframe obtained in Step 2
)
```

Output to User

1. Confirm that the full executive report has been saved and is available at: assets/wikipedia_trend_report.pdf
2. If PDF generation fails, present the findings and chart image directly in the chat, informing the user about the PDF error.
3. **Deliver the File:** Immediately upload/attach the generated `assets/wikipedia_trend_report.pdf` file directly to the chat interface so the user can download and view it.
4. **Delivery Confirmation:** Confirm the file submission in your text response:
   *"Here is your 1-page executive PDF report containing the trend chart, metrics table, and data reliability notes."*

### Step 4: Analytical Synthesis & Product Recommendations

Present a concise summary to the user:
Key Findings: Growth trends (%), absolute vs normalized (PPM) traction.
Data Reliability & Caveats: Highlight missing translations, low-activity status, or artificial spikes (refer to references/INTERPRETATION.md).
Actionable Product Advice: Explicit recommendation on whether to pursue the topic/market.

Synthesize the data into actionable business intelligence. Translate raw growth numbers and traffic graphs into clear strategic decisions while remaining transparent about assumptions and limitations.