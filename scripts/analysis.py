import logging
from typing import Any, Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_growth_trend(
        views_breakdown: List[Dict[str, Any]],
        granularity: str = "auto"
) -> Optional[float]:
    """
    Calculates the percentage change in traffic between the start and end of the period.

    :param views_breakdown: List of dictionaries [{'timestamp': '...', 'views': 123}, ...]
    :param granularity: 'daily', 'monthly', or 'auto'
    :return: Growth percentage (e.g., 15.5 or -10.2), or None if there is insufficient data.
    """
    if not views_breakdown or len(views_breakdown) < 2:
        return None

    views = [item.get("views", 0) for item in views_breakdown]

    # Auto-detect granularity by timestamp string length if not explicitly provided
    if granularity == "auto":
        sample_ts = str(views_breakdown[0].get("timestamp", ""))
        granularity = "daily" if len(sample_ts) == 8 else "monthly"

    if granularity == "daily" and len(views) >= 14:
        # For daily data (>14 days), compare the moving averages of the first and last weeks
        # to smooth out daily spikes and weekend dips
        start_avg = sum(views[:7]) / 7
        end_avg = sum(views[-7:]) / 7

        if start_avg == 0:
            return 100.0 if end_avg > 0 else 0.0

        trend = ((end_avg - start_avg) / start_avg) * 100
        return round(trend, 2)
    else:
        # For monthly data (or short daily ranges), compare the first and last data points
        start_views = views[0]
        end_views = views[-1]

        if start_views == 0:
            return 100.0 if end_views > 0 else 0.0

        trend = ((end_views - start_views) / start_views) * 100
        return round(trend, 2)


def export_to_summary_dataframe(trend_results: Dict[str, Any]) -> pd.DataFrame:
    """
    Creates a summary DataFrame (1 row = 1 language / language version of the article).
    Used to generate summary tables and final reports.
    """
    results = trend_results.get("results", [])
    if not results:
        return pd.DataFrame()

    summary_rows = []
    for item in results:
        summary_rows.append({
            "Query": trend_results.get("query"),
            "Source Article": trend_results.get("resolved_source_title"),
            "Language": item.get("language"),
            "Article Title": item.get("article_title"),
            "Status": item.get("status"),
            "Activity Status": item.get("activity_status"),
            "Total Views": item.get("total_views", 0),
            "Growth Trend (%)": item.get("growth_trend_percent"),
            "Granularity": item.get("granularity"),
            "Message": item.get("message")
        })

    return pd.DataFrame(summary_rows)


def export_to_dataframe(
        trend_results: Dict[str, Any],
        detailed: bool = True
) -> pd.DataFrame:
    """
    Converts WikipediaTrendAnalyzer analysis results into a Pandas DataFrame.

    :param trend_results: Dictionary containing the analysis results
    :param detailed: True for full temporal breakdown, False for a summary report by language
    """
    if not detailed:
        return export_to_summary_dataframe(trend_results)

    results = trend_results.get("results", [])
    if not results:
        return pd.DataFrame()

    rows = []
    for item in results:
        base_info = {
            "query": trend_results.get("query"),
            "resolved_source_title": trend_results.get("resolved_source_title"),
            "language": item.get("language"),
            "article_title": item.get("article_title"),
            "status": item.get("status"),
            "activity_status": item.get("activity_status"),
            "total_views": item.get("total_views", 0),
            "growth_trend_percent": item.get("growth_trend_percent"),
            "granularity": item.get("granularity"),
            "message": item.get("message")
        }

        # Support universal views_breakdown key with a fallback to monthly_breakdown
        breakdown = item.get("views_breakdown") or item.get("monthly_breakdown", [])

        if breakdown:
            for entry in breakdown:
                row = base_info.copy()
                row["timestamp"] = entry.get("timestamp")
                row["period_views"] = entry.get("views", 0)
                rows.append(row)
        else:
            row = base_info.copy()
            row["timestamp"] = None
            row["period_views"] = 0
            rows.append(row)

    return pd.DataFrame(rows)


def export_to_csv(
        trend_results: Dict[str, Any],
        file_path: str,
        detailed: bool = True
) -> None:
    """
    Saves analysis results to a CSV file.
    """
    df = export_to_dataframe(trend_results, detailed=detailed)
    if not df.empty:
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        logger.info(f"Results successfully exported to {file_path}")
    else:
        logger.warning(f"No data to export for query '{trend_results.get('query')}'")