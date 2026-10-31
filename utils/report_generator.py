
"""
PDF report generator using ReportLab.
Supports English, Hindi and Kannada.
"""

import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from utils.i18n import (
    t,
    tr_risk,
    tr_gender,
    tr_recommendation,
    tr_precautions,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "assets", "fonts")

FONT_FILES = {
    "en": ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
    "hi": (
        "NotoSansDevanagari-Regular.ttf",
        "NotoSansDevanagari-Bold.ttf",
    ),
    "kn": (
        "NotoSansKannada-Regular.ttf",
        "NotoSansKannada-Bold.ttf",
    ),
}

INK = colors.HexColor("#0B3D59")
GRID = colors.HexColor("#D6E4EA")
LABEL_BG = colors.HexColor("#EEF5F8")
GREY = colors.HexColor("#666666")

RISK_COLORS = {
    "Low": colors.HexColor("#2E9F5A"),
    "Medium": colors.HexColor("#D6820A"),
    "High": colors.HexColor("#D63C2D"),
}


def _register_fonts(lang):
    """Register the selected Unicode font and its bold version."""

    regular_file, bold_file = FONT_FILES.get(lang, FONT_FILES["en"])

    regular_path = os.path.join(FONTS_DIR, regular_file)
    bold_path = os.path.join(FONTS_DIR, bold_file)

    if not os.path.isfile(regular_path):
        raise FileNotFoundError(f"Font not found: {regular_path}")

    if not os.path.isfile(bold_path):
        raise FileNotFoundError(f"Font not found: {bold_path}")

    regular_name = f"ReportFont_{lang}"
    bold_name = f"ReportFontBold_{lang}"

    if regular_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(regular_name, regular_path))

    if bold_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(bold_name, bold_path))

    return regular_name, bold_name


def _make_styles(regular, bold):
    """Create paragraph styles with complex-script shaping enabled."""

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            fontName=bold,
            fontSize=19,
            leading=25,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=5,
            shaping=1,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            fontName=regular,
            fontSize=9,
            leading=14,
            textColor=GREY,
            shaping=1,
        ),
        "heading": ParagraphStyle(
            "SectionHeading",
            fontName=bold,
            fontSize=13,
            leading=19,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=6,
            shaping=1,
        ),
        "body": ParagraphStyle(
            "BodyTextCustom",
            fontName=regular,
            fontSize=9,
            leading=14,
            textColor=colors.black,
            shaping=1,
        ),
        "bold": ParagraphStyle(
            "BoldTextCustom",
            fontName=bold,
            fontSize=9,
            leading=14,
            textColor=colors.black,
            shaping=1,
        ),
        "small": ParagraphStyle(
            "SmallTextCustom",
            fontName=regular,
            fontSize=8,
            leading=12,
            textColor=GREY,
            shaping=1,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName=bold,
            fontSize=9,
            leading=13,
            textColor=colors.white,
            alignment=TA_CENTER,
            shaping=1,
        ),
        "center": ParagraphStyle(
            "CenteredText",
            fontName=regular,
            fontSize=9,
            leading=14,
            alignment=TA_CENTER,
            shaping=1,
        ),
    }


def _p(value, style):
    """Create a safely escaped paragraph."""

    return Paragraph(escape(str(value)), style)


def _heading(text, styles):
    return Paragraph(escape(str(text)), styles["heading"])


def _make_table(data, widths, header=False):
    """Create a styled PDF table."""

    table = Table(
        data,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )

    commands = [
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]

    if header:
        commands.append(
            ("BACKGROUND", (0, 0), (-1, 0), INK)
        )
    else:
        commands.append(
            ("BACKGROUND", (0, 0), (0, -1), LABEL_BG)
        )

    table.setStyle(TableStyle(commands))
    return table


def generate_pdf_report(twin: dict, lang: str = "en") -> bytes:
    """
    Generate a PDF report from a Digital Twin dictionary.

    Args:
        twin: Digital Twin profile dictionary.
        lang: "en", "hi" or "kn".

    Returns:
        PDF content as bytes.
    """

    try:
        if lang not in FONT_FILES:
            lang = "en"

        regular, bold = _register_fonts(lang)
        styles = _make_styles(regular, bold)

        details = twin.get("patient_details") or {}
        allergy = twin.get("allergy_risk") or {}
        side_effect = twin.get("side_effect_risk") or {}
        overall_risk = twin.get("overall_risk_level", "N/A")
        recommendation = twin.get("recommendation", "N/A")
        rsv = twin.get("rsv_risk") or {}

        from io import BytesIO

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=str(t("pdf_title", lang)),
            author="Digital Twin Health Report",
        )

        story = []

        # Header
        story.append(
            Paragraph(
                escape(str(t("pdf_title", lang))),
                styles["title"],
            )
        )

        story.append(
            _p(t("pdf_subtitle", lang), styles["subtitle"])
        )

        generated = datetime.now().strftime("%d %b %Y, %I:%M %p")

        story.append(
            _p(
                f"{t('generated_on', lang)}: {generated}",
                styles["small"],
            )
        )

        story.append(Spacer(1, 8))

        # Patient details
        story.append(_heading(t("patient_details", lang), styles))

        patient_rows = [
            (t("name", lang), details.get("PatientName", "N/A")),
            (t("age", lang), details.get("Age", "N/A")),
            (
                t("gender", lang),
                tr_gender(details.get("Gender", "N/A"), lang),
            ),
            (
                f"{t('alt', lang)} (U/L)",
                details.get("ALT", "N/A"),
            ),
            (
                f"{t('ast', lang)} (U/L)",
                details.get("AST", "N/A"),
            ),
            (
                f"{t('creatinine', lang)} (mg/dL)",
                details.get("Creatinine", "N/A"),
            ),
            (
                f"{t('crp', lang)} (mg/L)",
                details.get("CRP", "N/A"),
            ),
        ]

        patient_data = [
            [_p(label, styles["bold"]), _p(value, styles["body"])]
            for label, value in patient_rows
        ]

        story.append(
            _make_table(
                patient_data,
                [65 * mm, 105 * mm],
            )
        )

        # Vaccine predictions
        story.append(
            _heading(t("vaccine_predictions", lang), styles)
        )

        prediction_data = [[
            _p(t("prediction_type", lang), styles["table_header"]),
            _p(t("risk_level_axis", lang), styles["table_header"]),
            _p(t("confidence", lang), styles["table_header"]),
        ]]

        def add_prediction(label, block):
            predicted_class = block.get("predicted_class", "N/A")
            probabilities = block.get("probabilities") or {}
            probability = probabilities.get(predicted_class, 0)

            prediction_data.append([
                _p(label, styles["body"]),
                _p(tr_risk(predicted_class, lang), styles["center"]),
                _p(f"{probability * 100:.1f}%", styles["center"]),
            ])

        add_prediction(t("allergy_risk", lang), allergy)
        add_prediction(t("side_effect_risk", lang), side_effect)

        story.append(
            _make_table(
                prediction_data,
                [60 * mm, 55 * mm, 55 * mm],
                header=True,
            )
        )

        # Overall risk
        story.append(Spacer(1, 8))

        risk_color = RISK_COLORS.get(
            overall_risk,
            colors.black,
        )

        risk_style = ParagraphStyle(
            "OverallRisk",
            parent=styles["body"],
            fontName=bold,
            textColor=risk_color,
            shaping=1,
        )

        story.append(
            Paragraph(
                f"<b>{escape(str(t('overall_risk_level', lang)))}</b>: "
                f'<font color="{risk_color.hexval()}">'
                f"{escape(str(tr_risk(overall_risk, lang)))}"
                f"</font>",
                risk_style,
            )
        )

        story.append(Spacer(1, 5))

        story.append(
            _p(
                f"{t('recommendation', lang)}: "
                f"{tr_recommendation(recommendation, lang)}",
                styles["body"],
            )
        )

        # RSV screening
        if rsv:
            story.append(_heading(t("rsv_title", lang), styles))

            risk_level = rsv.get("risk_level", "N/A")
            rsv_color = RISK_COLORS.get(risk_level, colors.black)

            story.append(
                Paragraph(
                    f"<b>{escape(str(t('rsv_risk_level', lang)))}</b>: "
                    f'<font color="{rsv_color.hexval()}">'
                    f"{escape(str(tr_risk(risk_level, lang)))}"
                    f"</font>",
                    styles["body"],
                )
            )

            story.append(Spacer(1, 5))

            story.append(
                _p(
                    f"{t('result', lang)}: "
                    f"{tr_recommendation(rsv.get('recommendation', 'N/A'), lang)}",
                    styles["body"],
                )
            )

            story.append(Spacer(1, 5))

            story.append(
                _p(
                    f"{t('risk_score', lang)}: "
                    f"{rsv.get('score', 0)} / "
                    f"{rsv.get('max_score', 8)} "
                    f"({t('based_on', lang)})",
                    styles["small"],
                )
            )

            precautions = tr_precautions(
                rsv.get("precautions") or [],
                lang,
            )

            if precautions:
                story.append(
                    _heading(t("precautions_title", lang), styles)
                )

                for step in precautions:
                    story.append(
                        _p(f"•  {step}", styles["body"])
                    )

        # Disclaimer
        story.append(Spacer(1, 15))
        story.append(
            _p(t("pdf_disclaimer", lang), styles["small"])
        )

        doc.build(story)

        return buffer.getvalue()

    except Exception as e:
        raise RuntimeError(
            f"Error generating PDF report: {e}"
        ) from e
