from datetime import date, datetime
import logging
import re
from typing import Any, Dict, List, Optional
import requests

from scripts.analysis import calculate_growth_trend, export_to_dataframe, export_to_csv

logger = logging.getLogger(__name__)


class WikipediaTrendAnalyzer:
    USER_AGENT = "WikipediaTrendAnalyzerBot/1.0 (https://example.com/contact)"

    def _parse_to_api_date(self, date_input: Any) -> str:
        if isinstance(date_input, (date, datetime)):
            return date_input.strftime("%Y%m%d00")

        if isinstance(date_input, str):
            clean_str = re.sub(r"[^\d]", "", date_input)
            if len(clean_str) == 8:
                return f"{clean_str}00"
            if len(clean_str) == 10 and clean_str.endswith("00"):
                return clean_str

        raise ValueError(
            f"Invalid date format: {date_input}. Expected YYYY-MM-DD or YYYYMMDD."
        )

    def search_exact_title(self, query: str, lang: str = "en") -> Optional[str]:
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
        }
        headers = {"User-Agent": self.USER_AGENT}

        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                if search_results:
                    return search_results[0]["title"]
            return None
        except Exception as e:
            logger.error(
                f"Error searching exact title for '{query}' in '{lang}': {e}"
            )
            return None

    def get_sitelinks(
        self, source_title: str, source_lang: str, target_langs: List[str]
    ) -> Dict[str, Optional[str]]:
        url = f"https://{source_lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "langlinks",
            "titles": source_title,
            "lllimit": 500,
            "format": "json",
        }
        headers = {"User-Agent": self.USER_AGENT}
        sitelinks = {lang: None for lang in target_langs}

        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                for _, page_info in pages.items():
                    langlinks = page_info.get("langlinks", [])
                    for link in langlinks:
                        lang_code = link.get("lang")
                        if lang_code in sitelinks:
                            sitelinks[lang_code] = link.get("*")
        except Exception as e:
            logger.error(f"Error fetching sitelinks for '{source_title}': {e}")

        return sitelinks

    def get_pageviews(
        self,
        article_title: str,
        start_date: str,
        end_date: str,
        lang: str = "en",
    ) -> Dict[str, Any]:
        try:
            start_formatted = self._parse_to_api_date(start_date)
            end_formatted = self._parse_to_api_date(end_date)
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}

        encoded_title = requests.utils.quote(
            article_title.replace(" ", "_"), safe=""
        )
        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"{lang}.wikipedia/all-access/user/{encoded_title}/monthly/{start_formatted}/{end_formatted}"
        )
        headers = {"User-Agent": self.USER_AGENT}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                return {
                    "status": "error",
                    "error_type": "NOT_FOUND",
                    "message": "Article not found or no traffic data.",
                }
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Wikimedia API returned status code {response.status_code}",
                }

            items = response.json().get("items", [])
            if not items:
                return {
                    "status": "success",
                    "total_views": 0,
                    "growth_trend_percent": None,
                    "activity_status": "NO_TRAFFIC",
                    "monthly_breakdown": [],
                }

            total_views = sum(item.get("views", 0) for item in items)
            monthly_breakdown = [
                {
                    "timestamp": item["timestamp"][:6],
                    "views": item.get("views", 0),
                }
                for item in items
            ]

            growth_trend = calculate_growth_trend(monthly_breakdown)
            activity_status = "ACTIVE" if total_views > 0 else "NO_TRAFFIC"

            return {
                "status": "success",
                "total_views": total_views,
                "growth_trend_percent": growth_trend,
                "activity_status": activity_status,
                "monthly_breakdown": monthly_breakdown,
            }
        except Exception as e:
            return {"status": "error", "message": f"Request failed: {str(e)}"}

    def analyze_trends_by_keywords(
        self,
        query: str,
        target_languages: List[str],
        start_date: str,
        end_date: str,
        source_lang: str = "en",
    ) -> Dict[str, Any]:
        try:
            source_title = self.search_exact_title(
                query=query, lang=source_lang
            )
            if not source_title:
                return {
                    "query": query,
                    "status": "ERROR",
                    "error_type": "SOURCE_ARTICLE_NOT_FOUND",
                    "message": f"Could not resolve an exact Wikipedia page for query '{query}' in '{source_lang}'.",
                    "results": [],
                }

            all_languages = list(
                dict.fromkeys([source_lang] + target_languages)
            )
            target_langs_only = [
                lang for lang in all_languages if lang != source_lang
            ]

            sitelinks = {}
            if target_langs_only:
                sitelinks = self.get_sitelinks(
                    source_title=source_title,
                    source_lang=source_lang,
                    target_langs=target_langs_only,
                )
            sitelinks[source_lang] = source_title

            results: List[Dict[str, Any]] = []

            for lang in all_languages:
                article_title = sitelinks.get(lang)

                if not article_title:
                    results.append({
                        "language": lang,
                        "article_title": None,
                        "status": "NOT_FOUND",
                        "activity_status": None,
                        "total_views": 0,
                        "growth_trend_percent": None,
                        "monthly_breakdown": [],
                        "message": f"Article has no corresponding page on {lang}.wikipedia.org",
                    })
                    continue

                metrics = self.get_pageviews(
                    article_title=article_title,
                    start_date=start_date,
                    end_date=end_date,
                    lang=lang,
                )

                if metrics.get("status") == "success":
                    results.append({
                        "language": lang,
                        "article_title": article_title,
                        "status": "SUCCESS",
                        "activity_status": metrics.get("activity_status"),
                        "total_views": metrics.get("total_views", 0),
                        "growth_trend_percent": metrics.get(
                            "growth_trend_percent"
                        ),
                        "monthly_breakdown": metrics.get(
                            "monthly_breakdown", []
                        ),
                        "message": None,
                    })
                else:
                    results.append({
                        "language": lang,
                        "article_title": article_title,
                        "status": "ERROR",
                        "activity_status": None,
                        "total_views": 0,
                        "growth_trend_percent": None,
                        "monthly_breakdown": [],
                        "message": metrics.get(
                            "message", "Failed to retrieve pageview data."
                        ),
                    })

            return {
                "query": query,
                "resolved_source_title": source_title,
                "source_language": source_lang,
                "period": f"{start_date} to {end_date}",
                "status": "SUCCESS",
                "results": results,
            }

        except Exception as e:
            logger.exception("Unexpected error in analyze_trends_by_keywords")
            return {
                "query": query,
                "status": "ERROR",
                "error_type": "INTERNAL_ERROR",
                "message": f"An unexpected execution error occurred: {str(e)}",
                "results": [],
            }

    # Хелперы экспорта для обратной совместимости вызова из класса
    def export_to_dataframe(self, trend_results: Dict[str, Any]):
        return export_to_dataframe(trend_results)

    def export_to_csv(self, trend_results: Dict[str, Any], file_path: str) -> None:
        export_to_csv(trend_results, file_path)