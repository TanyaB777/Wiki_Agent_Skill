"""Module for data processing, analysis, and exporting trend metrics."""

import logging
from typing import Any, Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_growth_trend(monthly_breakdown: List[Dict[str, Any]]) -> Optional[float]:
    """Calculates the view growth percentage from the first to the last month."""
    if len(monthly_breakdown) >= 2:
        first_views = monthly_breakdown[0].get("views", 0)
        last_views = monthly_breakdown[-1].get("views", 0)
        if first_views > 0:
            return round(((last_views - first_views) / first_views) * 100, 2)
    return None


def export_to_dataframe(trend_results: Dict[str, Any]) -> pd.DataFrame:
    """Converts the trend_results payload into a flat Pandas DataFrame."""
    rows = []
    search_query = trend_results.get("query", "")
    resolved_title = trend_results.get("resolved_source_title", "")

    for lang_item in trend_results.get("results", []):
        lang = lang_item.get("language")
        status = lang_item.get("status")

        if status == "SUCCESS":
            article = lang_item.get("article_title")
            activity_status = lang_item.get("activity_status")
            growth_trend = lang_item.get("growth_trend_percent")
            breakdown = lang_item.get("monthly_breakdown", [])

            if breakdown:
                for month_item in breakdown:
                    rows.append({
                        "search_query": search_query,
                        "resolved_source_title": resolved_title,
                        "language": lang,
                        "article_title": article,
                        "timestamp": month_item.get("timestamp"),
                        "views": month_item.get("views"),
                        "activity_status": activity_status,
                        "growth_trend_percent": growth_trend,
                        "status": "SUCCESS",
                        "error_message": None,
                    })
            else:
                rows.append({
                    "search_query": search_query,
                    "resolved_source_title": resolved_title,
                    "language": lang,
                    "article_title": article,
                    "timestamp": None,
                    "views": 0,
                    "activity_status": activity_status,
                    "growth_trend_percent": growth_trend,
                    "status": "SUCCESS",
                    "error_message": None,
                })
        else:
            rows.append({
                "search_query": search_query,
                "resolved_source_title": resolved_title,
                "language": lang,
                "article_title": lang_item.get("article_title"),
                "timestamp": None,
                "views": None,
                "activity_status": None,
                "growth_trend_percent": None,
                "status": status,
                "error_message": lang_item.get("message"),
            })

    return pd.DataFrame(rows)


def export_to_csv(trend_results: Dict[str, Any], file_path: str) -> None:
    """Exports analysis results directly to a CSV file."""
    df = export_to_dataframe(trend_results)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")