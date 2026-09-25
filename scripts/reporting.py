import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from scripts.analysis import export_to_summary_dataframe, export_to_dataframe

logger = logging.getLogger(__name__)


def _register_cyrillic_font() -> str:
    """Registers a font with Cyrillic character support."""
    try:
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            return "Arial"
    except Exception as e:
        logger.warning(f"Could not load system Arial font: {e}")

    return "Helvetica"


def _format_status_badge(status_str: str, font_name: str, normal_style: ParagraphStyle) -> Paragraph:
    """
    Converts a technical status name (e.g., low_activity) into a formatted, human-readable styled badge.
    """
    status_clean = str(status_str).replace("_", " ").title()

    bg_colors = {
        "Active": "#E8F8F5",
        "Low Activity": "#FEF9E7",
        "Untranslated": "#FADBD8",
        "No Data": "#EAECEE"
    }

    text_colors = {
        "Active": "#117864",
        "Low Activity": "#B7950B",
        "Untranslated": "#78281F",
        "No Data": "#5D6D7E"
    }

    tc = text_colors.get(status_clean, "#2C3E50")

    badge_style = ParagraphStyle(
        'StatusBadge',
        parent=normal_style,
        fontName=font_name,
        fontSize=8,
        textColor=colors.HexColor(tc),
        alignment=1
    )

    return Paragraph(f"<b>{status_clean}</b>", badge_style)


def _generate_trend_chart(report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generates and saves a Wikipedia pageview trends chart.
    """
    is_normalized = report_data.get("normalized", False)
    results = report_data.get("results", [])

    plt.figure(figsize=(10, 5), dpi=300)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    for lang_data in results:
        lang = lang_data.get("language")
        breakdown = lang_data.get("views_breakdown", [])

        if not breakdown:
            continue

        dates = [datetime.strptime(item["timestamp"][:8], "%Y%m%d") for item in breakdown]
        values = [item["views"] for item in breakdown]

        plt.plot(dates, values, marker='o', markersize=3, label=lang, linewidth=1.5)

    plt.title("Pageview Trends", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Date", fontsize=10, labelpad=10)

    if is_normalized:
        plt.ylabel("Share of Traffic (PPM)", fontsize=10, labelpad=10)
        plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    else:
        plt.ylabel("Views", fontsize=10, labelpad=10)
        plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))

    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(title="Language", loc="upper left")
    plt.tight_layout()

    save_path = output_path or f"trend_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()

    return save_path


def generate_pdf_report(
        trend_results: Dict[str, Any],
        file_path: str = "assets/wikipedia_trend_report.pdf"
) -> None:
    """Generates an aesthetic business PDF report."""
    font_name = _register_cyrillic_font()

    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    story = []

    normal_style = ParagraphStyle(
        'CyrillicNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9.5,
        leading=13
    )
    title_style = ParagraphStyle(
        'CyrillicTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        textColor=colors.HexColor('#1A252C'),
        spaceAfter=10
    )
    heading2_style = ParagraphStyle(
        'CyrillicHeading2',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=8
    )

    # 1. Header & Metadata
    query_name = trend_results.get('query', 'N/A')
    story.append(Paragraph(f"Wikipedia Trend Report: {query_name.upper()}", title_style))

    start_date = trend_results.get('start_date', '')
    end_date = trend_results.get('end_date', '')
    period_str = f"{start_date} — {end_date}" if start_date and end_date else "N/A"

    meta_text = (
        f"<b>Source Article:</b> {trend_results.get('resolved_source_title', 'N/A')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Period:</b> {period_str} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Source Language:</b> {trend_results.get('source_language', 'en').upper()}"
    )
    story.append(Paragraph(meta_text, normal_style))
    story.append(Spacer(1, 12))

    # 2. Chart
    chart_buffer = _generate_trend_chart(trend_results)
    story.append(Image(chart_buffer, width=540, height=252))
    story.append(Spacer(1, 15))

    # 3. Summary Table
    story.append(Paragraph("Summary Breakdown", heading2_style))
    story.append(Spacer(1, 6))

    summary_df = export_to_summary_dataframe(trend_results)

    if not summary_df.empty:
        table_data = [["Lang", "Article Title", "Total Views", "Trend (%)", "Status"]]

        for _, row in summary_df.iterrows():
            # Format trend percentage (e.g., +15.4% or -10.2%)
            raw_trend = row.get('Growth Trend (%)')
            if pd.notnull(raw_trend):
                try:
                    trend_val = float(raw_trend)
                    trend_str = f"+{trend_val:.1f}%" if trend_val > 0 else f"{trend_val:.1f}%"
                    trend_color = "#27AE60" if trend_val > 0 else ("#C0392B" if trend_val < 0 else "#2C3E50")
                except (ValueError, TypeError):
                    trend_str = "N/A"
                    trend_color = "#7F8C8D"
            else:
                trend_str = "N/A"
                trend_color = "#7F8C8D"

            trend_style = ParagraphStyle(
                'TrendStyle',
                parent=normal_style,
                textColor=colors.HexColor(trend_color)
            )

            title_str = str(row.get('Article Title', 'N/A'))
            short_title = title_str[:32] + "..." if len(title_str) > 32 else title_str

            # Safe formatting for pageviews
            raw_views = row.get('Total Views', 0)
            try:
                formatted_views = f"{int(raw_views):,}"
            except (ValueError, TypeError):
                formatted_views = "N/A"

            # Convert status into a styled badge
            status_badge = _format_status_badge(row.get('Activity Status', 'No Data'), font_name, normal_style)

            table_data.append([
                Paragraph(f"<b>{str(row.get('Language', '')).upper()}</b>", normal_style),
                Paragraph(short_title, normal_style),
                Paragraph(formatted_views, normal_style),
                Paragraph(f"<b>{trend_str}</b>", trend_style),
                status_badge
            ])

        t = Table(table_data, colWidths=[45, 220, 95, 80, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E8E8')),
        ]))
        story.append(t)

        # 4. English Status Legend
        story.append(Spacer(1, 12))
        caption_style = ParagraphStyle(
            'StatusLegend',
            parent=normal_style,
            fontSize=8,
            textColor=colors.HexColor('#566573'),
            leading=11
        )

        legend_text = (
            "<b>Status Legend:</b><br/>"
            "• <b>Active</b>: Article exists and has accumulated over 100 total views during the analyzed period.<br/>"
            "• <b>Low Activity</b>: Article exists, but has 100 or fewer total views.<br/>"
            "• <b>Untranslated</b>: No corresponding article exists in this target language.<br/>"
            "• <b>No Data</b>: Page not found or API returned no statistics for the requested period."
        )
        story.append(Paragraph(legend_text, caption_style))

    else:
        story.append(Paragraph("No summary data to display.", normal_style))

    doc.build(story)
    logger.info(f"PDF report generated successfully at: {file_path}")

    # Remove the temporary chart file after compiling the PDF
    if os.path.exists(chart_buffer):
        try:
            os.remove(chart_buffer)
        except OSError as e:
            logger.warning(f"Could not remove temporary chart file: {e}")