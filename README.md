# Wikipedia Market Interest Analyzer

A skill for analyzing market interest and pageview trends across Wikipedia articles in different languages. Designed to help founders, product managers, and teams evaluate product localization, assess new course/topic launches, and explore demand trends with automated single-page PDF report generation.

---

## Key Features

* **Candidate Search & Article Resolution:** Automatically finds canonical Wikipedia article titles based on query keywords via `find_wikipedia_candidates`.
* **Cross-Language Comparative Analysis:** Maps article translations across target languages using the Wikipedia Interlanguage links API (`langlinks`).
* **Traffic Normalization (PPM):** Converts pageview counts into **Parts Per Million (PPM)** relative to total language section traffic, enabling fair interest comparisons across regions with vastly different internet population sizes.
* **Growth Trend Calculation:** Automatically measures percentage changes in traffic while smoothing out weekly seasonality (via moving averages for daily intervals).
* **Export & Reporting:** Generates trend visualizations (`matplotlib`), summary data structures (`pandas`), and fully formatted 1-page executive PDF reports (`reportlab`).

---

## 📁 Project Structure

```text
.
├── SKILL.md                     # Skill workflow definition and AI assistant guidelines
├── wikipedia_trend_analyzer.py  # Core WikipediaTrendAnalyzer class and API handler
├── scripts/
│   ├── fetcher.py              # Candidate searching and pageview metrics fetching
│   ├── analysis.py             # Growth trend algorithms and DataFrame / CSV exports
│   └── report.py               # Chart rendering and PDF report generation
└── assets/
    └── wikipedia_trend_report.pdf  # Generated executive PDF report output
```

## 📦 Requirements & Installation
Install the required Python dependencies:
pip install requests pandas matplotlib reportlab

## Quickstart & Example Usage
1. Candidate Article Search (Step 1)

```text
from scripts.fetcher import find_wikipedia_candidates

# Search for the canonical article title before requesting metrics
candidates = find_wikipedia_candidates(
    query="intermittent fasting",
    lang="en",
    limit=5
)

for candidate in candidates:
    print(f"Title: {candidate['title']}\nSnippet: {candidate['snippet']}\n---")
```

2. Trend Analysis

```text
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

3. PDF Report Generation

```text
from scripts.report import generate_pdf_report

# Generates PDF report with embedded chart and formatted metric tables
# result is produced in Step 2
generate_pdf_report(
    trend_results=result # Result dict/dataframe obtained in Step 2
)
```
## Normalization Rules (PPM vs Raw Pageviews)
normalize=True (PPM): Mandatory when comparing two or more language sections (e.g., Polish vs. Czech). This eliminates bias caused by differences in the total population or active Wikipedia user base per language.
normalize=False (Raw Pageviews): Use exclusively when analyzing absolute user demand within a single language section.

## Roadmap / Future Enhancements
1. Seasonality Adjustment: Incorporating STL decomposition or Prophet modeling to isolate true organic growth from recurring annual/monthly seasonal peaks.
2. Anomaly & Spike Detection: Automated detection and filtering of artificial traffic spikes caused by viral news events, pop culture mentions, or bot activity.
3. Data Reliability & Confidence Scoring: Calculating statistical confidence intervals and data quality flags to score the trustworthiness of demand signals.
4. Multi-Article Topic Aggregation: Grouping and analyzing clusters of related articles (e.g., combining "Keto diet", "Low-carb diet", and "Ketosis") to represent broader market topics.
5. API Response Caching: Implementing local SQLite or Redis caching to reduce redundant REST API calls and accelerate repeated analyses.
6. Bulk Wikipedia Dataset Integration: Adding support for offline processing of Wikimedia monthly dump files and Clickstream datasets for large-scale analysis.
7. Comprehensive Test Suite: Adding unit, integration, and API mocking tests using pytest to ensure robust coverage across all modules.