"""Module for generating aggregated summary reports, data tables, and charts."""

import logging
import os
from typing import Any, Dict, Optional

import pandas as pd
from matplotlib import pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from scripts.analysis import export_to_dataframe


logger = logging.getLogger(__name__)

ASSETS_DIR = "assets"

import matplotlib.font_manager as fm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Используем FontProperties для гибкого поиска стилей шрифта
dejavu_regular = fm.findfont(fm.FontProperties(family='DejaVu Sans', weight='normal'))
dejavu_bold = fm.findfont(fm.FontProperties(family='DejaVu Sans', weight='bold'))

pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_regular))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold))


def generate_pdf_report(
    trend_results: Dict[str, Any]
) -> None:
    """Generates a polished 1-page PDF report containing summary text, data table, and trend chart."""
    if trend_results.get("status") != "SUCCESS":
        logger.error("Cannot generate PDF report for failed trend results.")
        return

    os.makedirs(ASSETS_DIR, exist_ok=True)
    output_pdf_path = os.path.join(ASSETS_DIR, "wikipedia_trend_report.pdf")

    # 1. Temporary chart generation
    chart_image_path = os.path.join(ASSETS_DIR, "_temp_report_chart.png")
    plot_trend_chart(trend_results, output_filepath=chart_image_path)

    # 2. Setup PDF document
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []
    styles = getSampleStyleSheet()

    # Custom styles с явным указанием шрифтов DejaVu
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="DejaVuSans-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        alignment=0,
        spaceAfter=10,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="DejaVuSans",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=body_style,
        fontName="DejaVuSans-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.whitesmoke,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=body_style,
        fontName="DejaVuSans",
        fontSize=9,
        leading=11,
    )

    # 3. Header Section
    query = trend_results.get("query", "N/A")
    resolved_title = trend_results.get("resolved_source_title", "N/A")
    period = trend_results.get("period", "N/A")

    story.append(Paragraph(f"Wikipedia Trend Analytics: {query}", title_style))
    story.append(
        Paragraph(
            f"<b>Article Title:</b> {resolved_title} | <b>Period:</b> {period}",
            body_style,
        )
    )
    story.append(Spacer(1, 15))

    # 4. Summary Table Generation (Строки обернуты в Paragraph для переноса)
    table_data = [[
        Paragraph("Language", table_header_style),
        Paragraph("Article Title", table_header_style),
        Paragraph("Total Views", table_header_style),
        Paragraph("Growth (%)", table_header_style)
    ]]

    for item in trend_results.get("results", []):
        if item.get("status") == "SUCCESS":
            lang = item.get("language", "").upper()
            title = item.get("article_title", "N/A")
            views = f"{item.get('total_views', 0):,}"
            growth = item.get("growth_trend_percent")
            growth_str = f"{growth:+.1f}%" if isinstance(growth, (int, float)) else "N/A"

            table_data.append([
                Paragraph(lang, table_cell_style),
                Paragraph(title, table_cell_style),
                Paragraph(views, table_cell_style),
                Paragraph(growth_str, table_cell_style),
            ])

    t = Table(table_data, colWidths=[60, 240, 110, 90])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(t)
    story.append(Spacer(1, 15))

    # 5. Attach Chart
    if os.path.exists(chart_image_path):
        story.append(Image(chart_image_path, width=520, height=260))

    # Build Document
    doc.build(story)

    # Clean up temporary image
    if os.path.exists(chart_image_path):
        os.remove(chart_image_path)

    # Clean up temporary image
    if os.path.exists(chart_image_path):
        os.remove(chart_image_path)

    logger.info(f"PDF Report successfully generated at: {output_pdf_path}")


def generate_summary_text(trend_results: Dict[str, Any]) -> str:
    """Generates a concise textual summary of the trend analysis results."""
    if trend_results.get("status") != "SUCCESS":
        return f"Analysis Error: {trend_results.get('message', 'Unknown error')}"

    query = trend_results.get("query")
    resolved_title = trend_results.get("resolved_source_title")
    period = trend_results.get("period")
    results = trend_results.get("results", [])

    lines = [
        f"📊 **Report for Query:** '{query}' (Wikipedia Article: '{resolved_title}')",
        f"📅 **Period:** {period}",
        f"🌍 **Language Breakdown ({len(results)} total):**",
        "-" * 40
    ]

    total_all_views = 0

    for item in results:
        lang = item.get("language", "").upper()
        status = item.get("status")

        if status == "SUCCESS":
            views = item.get("total_views", 0)
            total_all_views += views
            growth = item.get("growth_trend_percent")
            growth_str = f"{growth:+.1f}%" if isinstance(growth, (int, float)) else "N/A"
            title = item.get("article_title")

            lines.append(
                f"• [{lang}] '{title}': {views:,} views | Growth: {growth_str}"
            )
        else:
            msg = item.get("message", "No data available")
            lines.append(f"• [{lang}] ❌ Data unavailable ({msg})")

    lines.append("-" * 40)
    lines.append(f"📈 **Total Traffic Across All Languages:** {total_all_views:,} views")

    return "\n".join(lines)


def generate_pivoted_summary(trend_results: Dict[str, Any]) -> pd.DataFrame:
    """Creates a pivot table of pageviews broken down by month and language."""
    df = export_to_dataframe(trend_results)

    if df.empty or "status" not in df.columns:
        return pd.DataFrame()

    valid_df = df[df["status"] == "SUCCESS"].dropna(subset=["timestamp"])

    if valid_df.empty:
        return pd.DataFrame()

    pivot = valid_df.pivot(
        index="timestamp",
        columns="language",
        values="views"
    ).fillna(0).astype(int)

    return pivot


def plot_trend_chart(
        trend_results: Dict[str, Any],
        output_filepath: Optional[str] = None
) -> None:
    """Generates and displays/saves a line chart showing monthly pageview trends."""
    pivot_df = generate_pivoted_summary(trend_results)

    if pivot_df.empty:
        logger.warning("No data available to generate plot.")
        return

    # Преобразование индекса с приведением к строке
    pivot_df.index = pd.to_datetime(pivot_df.index.astype(str), format="%Y%m")

    plt.figure(figsize=(10, 5))

    for col in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[col], marker="o", linewidth=2, label=col.upper())

    query = trend_results.get("query", "Trend")
    plt.title(f"Wikipedia Pageview Trends: {query}", fontsize=14, fontweight="bold")
    plt.xlabel("Month", fontsize=11)
    plt.ylabel("Pageviews", fontsize=11)

    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %Y"))
    plt.gcf().autofmt_xdate()

    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(title="Language")
    plt.tight_layout()

    if output_filepath:
        plt.savefig(output_filepath, dpi=300)
        logger.info(f"Chart successfully saved to {output_filepath}")
        plt.close()
    else:
        plt.show()