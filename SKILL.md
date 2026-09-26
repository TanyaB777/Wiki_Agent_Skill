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

Do not guess article titles. First search Wikipedia to get exact titles and snippets

```python
from scripts.fetcher import find_wikipedia_candidates

candidates = find_wikipedia_candidates(
    query="intermittent fasting",
    lang="en",
    limit=5
)
```

Choose the best-matching title if there is no obvious ambiguity, or ask the user if there are multiple relevant candidates.

### Step 2: Historical Pageview & Trend Analysis

Initialize the analyzer and calculate traffic metrics for target languages.
Set normalize=True when comparing languages with vastly different population/traffic sizes (calculates PPM - Parts Per Million).
Set normalize=False when analyzing raw demand in a single language.

```python
from scripts.fetcher import WikipediaTrendAnalyzer

analyzer = WikipediaTrendAnalyzer()
result = analyzer.analyze_trends_by_title(
    source_title="Intermittent fasting",
    source_lang="en",
    target_languages=["pl", "cs", "uk"],
    start_date="2024-01-01",
    end_date="2026-09-01",
    normalize=True
)
```

### Step 3: Visualization & PDF Report Generation

Generate trend charts and compile a single-page executive PDF report:

```python
from scripts.report import generate_pdf_report

# Generates PDF report with embedded chart and formatted metric tables
# result is produced in Step 2
generate_pdf_report(
    trend_results=result,
    file_path="assets/wikipedia_trend_report.pdf"
)
```

### Step 4: Analytical Synthesis & Product Recommendations

Present a concise summary to the user:
Key Findings: Growth trends (%), absolute vs normalized (PPM) traction.
Data Reliability & Caveats: Highlight missing translations, low-activity status, or artificial spikes (refer to references/INTERPRETATION.md).
Actionable Product Advice: Explicit recommendation on whether to pursue the topic/market.