import calendar
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import urllib.parse
import requests

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "WikipediaTrendAnalyzerBot/1.0 (https://example.org/bot; bot@example.org)"

def find_wikipedia_candidates(
        query: str,
        lang: str = "en",
        limit: int = 5,
        user_agent: str = DEFAULT_USER_AGENT
) -> List[Dict[str, str]]:
    """
    Standalone function to search for candidate Wikipedia articles.
    Returns article titles and text snippets for selection by the Agent.
    """
    url = f"https://{lang}.wikipedia.org/w/api.php"
    headers = {"User-Agent": user_agent}
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
        "srprop": "snippet"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        search_results = data.get("query", {}).get("search", [])

        candidates = []
        for item in search_results:
            # Clean HTML tags used for search highlighting (<span class="searchmatch">)
            snippet = item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
            candidates.append({
                "title": item["title"],
                "snippet": snippet
            })

        if not candidates:
            logger.warning(f"No articles found for query '{query}' in {lang}.wikipedia")

        return candidates

    except Exception as e:
        logger.error(f"Error searching articles for query '{query}' on [{lang}]: {e}")
        return []


class WikipediaTrendAnalyzer:
    """
    Class for analyzing Wikipedia article pageviews with optional normalization support (PPM).
    """

    def __init__(self, user_agent: Optional[str] = None):
        self.headers = {
            "User-Agent": user_agent or DEFAULT_USER_AGENT
        }

    def _parse_date(self, date_str: str) -> datetime:
        clean_str = str(date_str).split(" ")[0]
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y%m"):
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                pass
        raise ValueError(f"Unsupported date format: '{date_str}'")

    def _format_date(self, date_input: str, is_end_date: bool = False, include_hours: bool = True) -> str:
        dt = self._parse_date(date_input)

        if is_end_date:
            clean_str = str(date_input).split(" ")[0].replace("-", "").replace("/", "")
            if len(clean_str) == 6:
                last_day = calendar.monthrange(dt.year, dt.month)[1]
                dt = dt.replace(day=last_day)

        date_str = dt.strftime("%Y%m%d")
        return f"{date_str}00" if include_hours else date_str

    def get_total_language_pageviews_map(
            self,
            lang: str,
            start_date: str,
            end_date: str,
            granularity: str
    ) -> Dict[str, int]:
        """
        Returns a dictionary mapping 'YYYYMMDD00' to total_views for each time interval,
        allowing individual data points on the plot to be normalized.
        """
        api_start = self._format_date(start_date, is_end_date=False, include_hours=False)
        api_end = self._format_date(end_date, is_end_date=True, include_hours=False)

        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/"
            f"{lang}.wikipedia/all-access/user/{granularity}/{api_start}/{api_end}"
        )
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # Build a mapping of "timestamp -> total views"
                return {item["timestamp"]: item["views"] for item in data.get("items", [])}
            return {}
        except Exception as e:
            logger.error(f"Error fetching aggregate traffic for [{lang}]: {e}")
            return {}

    def get_interlanguage_links(self, title: str, source_lang: str = "en") -> Dict[str, str]:
        url = f"https://{source_lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": title,
            "prop": "langlinks",
            "lllimit": 500,
            "format": "json",
            "redirects": 1
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            lang_map = {}

            for page_id, page_data in pages.items():
                if "langlinks" in page_data:
                    for item in page_data["langlinks"]:
                        lang_map[item["lang"]] = item["*"]

            return lang_map
        except Exception as e:
            logger.error(f"Error fetching interlanguage links for '{title}' [{source_lang}]: {e}")
            return {}

    def get_pageviews(
            self,
            article_title: str,
            lang: str,
            start_date: str,
            end_date: str,
            normalize: bool = False  # <--- NORMALIZATION PARAMETER
    ) -> Dict[str, Any]:
        """
        Requests pageview data for a specific article.
        When normalize=True, data points in views_breakdown are converted to PPM (Parts Per Million).
        """
        dt_start = self._parse_date(start_date)
        dt_end = self._parse_date(end_date)
        days_diff = (dt_end - dt_start).days

        granularity = "daily" if days_diff < 60 else "monthly"

        api_start = self._format_date(start_date, is_end_date=False, include_hours=True)
        api_end = self._format_date(end_date, is_end_date=True, include_hours=True)

        encoded_title = urllib.parse.quote(article_title.replace(" ", "_"), safe="")

        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"{lang}.wikipedia/all-access/user/{encoded_title}/{granularity}/{api_start}/{api_end}"
        )

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 404:
                return {
                    "language": lang,
                    "article_title": article_title,
                    "status": "not_found",
                    "activity_status": "no_data",
                    "normalized": normalize,
                    "total_views": 0,
                    "granularity": granularity,
                    "views_breakdown": [],
                    "message": "Article not found or no data available for the period."
                }

            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            total_views = sum(item["views"] for item in items)

            # If normalization is requested, fetch aggregate language traffic for timestamps
            total_lang_views_map = {}
            if normalize:
                total_lang_views_map = self.get_total_language_pageviews_map(
                    lang=lang,
                    start_date=start_date,
                    end_date=end_date,
                    granularity=granularity
                )

            views_breakdown = []
            for item in items:
                ts = item["timestamp"]
                raw_views = item["views"]

                if normalize:
                    # Look up total language traffic for this month/day
                    # (Strip trailing '00' if aggregate API doesn't return hours)
                    ts_key = ts[:8] if len(ts) == 10 else ts
                    tot_views = total_lang_views_map.get(ts_key) or total_lang_views_map.get(ts, 0)

                    val = round((raw_views / tot_views) * 1_000_000, 2) if tot_views > 0 else 0.0
                else:
                    val = raw_views

                views_breakdown.append({"timestamp": ts, "views": val})

            try:
                from scripts.analysis import calculate_growth_trend
                growth_trend = calculate_growth_trend(views_breakdown, granularity=granularity)
            except ImportError:
                growth_trend = None

            activity_status = "active" if total_views > 100 else "low_activity"

            return {
                "language": lang,
                "article_title": article_title,
                "status": "success",
                "activity_status": activity_status,
                "normalized": normalize,  # Flag: whether data is normalized
                "metric_unit": "PPM" if normalize else "Views",  # Measurement unit for charting
                "total_views": total_views,  # Total absolute pageviews
                "growth_trend_percent": growth_trend,
                "granularity": granularity,
                "views_breakdown": views_breakdown,
                "monthly_breakdown": views_breakdown,
                "message": "Data retrieved successfully."
            }

        except Exception as e:
            logger.error(f"Error requesting pageviews for [{lang}] '{article_title}': {e}")
            return {
                "language": lang,
                "article_title": article_title,
                "status": "error",
                "activity_status": "error",
                "normalized": normalize,
                "total_views": 0,
                "views_breakdown": [],
                "message": str(e)
            }

    def analyze_trends_by_title(
            self,
            source_title: str,
            target_languages: List[str],
            start_date: str,
            end_date: str,
            source_lang: str = "en",
            normalize: bool = False  # <--- PARAMETER PASSED HERE
    ) -> Dict[str, Any]:
        """
        Main entry point for trend analysis.
        """
        logger.info(f"Analyzing article: '{source_title}' (Normalize={normalize})...")
        lang_links = self.get_interlanguage_links(source_title, source_lang=source_lang)

        all_langs = list(dict.fromkeys([source_lang] + target_languages))
        results = []

        for lang in all_langs:
            article_title = source_title if lang == source_lang else lang_links.get(lang)

            if not article_title:
                results.append({
                    "language": lang,
                    "article_title": None,
                    "status": "missing_translation",
                    "activity_status": "untranslated",
                    "total_views": 0,
                    "views_breakdown": []
                })
                continue

            pageview_data = self.get_pageviews(
                article_title=article_title,
                lang=lang,
                start_date=start_date,
                end_date=end_date,
                normalize=normalize  # Call with the selected mode
            )
            results.append(pageview_data)

        return {
            "resolved_source_title": source_title,
            "source_language": source_lang,
            "normalized": normalize,
            "start_date": start_date,
            "end_date": end_date,
            "results": results
        }