import logging
from scripts.client import WikipediaTrendAnalyzer
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

    result = analyzer.analyze_trends_by_keywords(
        query="ai",
        target_languages=["pl", "de", "uk"],
        start_date="2024-01-01",
        end_date="2026-09-24",
        source_lang="en",
    )

    generate_pdf_report(result)


if __name__ == "__main__":
    main()