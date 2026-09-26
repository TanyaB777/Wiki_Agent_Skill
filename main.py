from scripts.fetcher import WikipediaTrendAnalyzer, find_wikipedia_candidates
from scripts.report import generate_pdf_report

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    analyzer = WikipediaTrendAnalyzer()

    query = "Python"

    # Step 1: Find Wikipedia candidates
    candidates = find_wikipedia_candidates(query, lang="en", limit=5)
    selected_title = candidates[0]["title"]

    # Step 2: Analyze pageviews
    result = analyzer.analyze_trends_by_title(
        source_title=selected_title,
        target_languages=["pl", "de", "uk"],
        start_date="2026-08-01",
        end_date="2026-09-24",
        normalize=True,
        source_lang="en"
    )

    # Step 3: Generate PDF report
    generate_pdf_report(query, result)

if __name__ == "__main__":
    main()