import logging
from scripts.client import WikipediaTrendAnalyzer, find_wikipedia_candidates
from scripts.reporting import generate_pdf_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    analyzer = WikipediaTrendAnalyzer()

    # result = analyzer.analyze_trends_by_keywords(
    #     query="Artificial Intelligence",
    #     target_languages=["es", "de", "uk"],
    #     start_date="2023-01-01",
    #     end_date="2023-06-30",
    #     source_lang="en",
    # )

    selected_title = "Python"

    candidates = find_wikipedia_candidates(selected_title, lang="en", limit=3)
    print(candidates)
    selected_title = candidates[0]["title"]

    result = analyzer.analyze_trends_by_title(
        source_title=selected_title,
        target_languages=["pl", "de", "uk"],
        start_date="2026-08-01",
        end_date="2026-09-24",
        normalize=True,
        source_lang="en"
    )

    result['query'] = selected_title

    generate_pdf_report(result, "assets/wikipedia_trend_report.pdf")

if __name__ == "__main__":
    main()