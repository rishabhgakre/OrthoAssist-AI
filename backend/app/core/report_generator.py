"""
Explainable AI Report Generator — produces the doctor-facing PDF summarizing
a patient's full recovery assessment: structural (X-ray) findings, functional
(gait) findings, and the combined CORI score with plain-language explanation.

This is the tangible output of your project's "Explainable AI" objective —
a doctor should be able to read this PDF alone and understand not just the
score, but why the AI arrived at it.
"""

import os
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable, PageBreak, 
)

# ---- Brand palette — mirrors the OrthoAssist AI web app exactly, so a
# printed report and the on-screen dashboard read as the same product. ----
COLOR_PRIMARY = colors.HexColor("#031A07")     # brand ink — rgb(3, 26, 7)
COLOR_PRIMARY_2 = colors.HexColor("#0C3014")   # slightly lifted ink, for grad -> flat fallback
COLOR_GOLD = colors.HexColor("#C9A66B")        # structural pillar accent
COLOR_GOLD_BRIGHT = colors.HexColor("#DCC28F")
COLOR_PURPLE = colors.HexColor("#6B4C9A")      # functional pillar accent
COLOR_PURPLE_BRIGHT = colors.HexColor("#9B7FC4")
COLOR_ACCENT = COLOR_GOLD                      # kept for any legacy references below
COLOR_SUCCESS = colors.HexColor("#1E7A5C")     # malachite — good/excellent scores
COLOR_WARNING = colors.HexColor("#A8752E")     # topaz — moderate scores
COLOR_DANGER = colors.HexColor("#8B2635")      # garnet — low / needs-attention scores
COLOR_LIGHT_BG = colors.HexColor("#F2F0EA")    # section background (pearl, matches app page bg)
COLOR_CARD_BG = colors.HexColor("#FAF8F4")     # card background (matches app card bg)
COLOR_TEXT = colors.HexColor("#1C231F")
COLOR_MUTED = colors.HexColor("#8A8478")
COLOR_BORDER = colors.HexColor("#E2DED2")


def _stage_color(stage: str):
    if "Excellent" in stage:
        return COLOR_SUCCESS
    elif "Good" in stage:
        return COLOR_ACCENT
    elif "Moderate" in stage:
        return COLOR_WARNING
    return COLOR_DANGER


def _score_color(score: Optional[float]):
    if score is None:
        return COLOR_MUTED
    if score >= 85:
        return COLOR_SUCCESS
    elif score >= 70:
        return COLOR_ACCENT
    elif score >= 50:
        return COLOR_WARNING
    return COLOR_DANGER


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle", fontSize=20, leading=24, textColor=colors.white,
        alignment=TA_LEFT, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", fontSize=10.5, leading=14, textColor=colors.white,
        alignment=TA_LEFT, fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=13.5, leading=16, textColor=COLOR_PRIMARY,
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SubHeading", fontSize=10.5, leading=13, textColor=COLOR_PRIMARY,
        fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="BodyTextCustom", fontSize=9.5, leading=14, textColor=COLOR_TEXT,
        fontName="Helvetica", alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="MutedNote", fontSize=8, leading=11, textColor=COLOR_MUTED,
        fontName="Helvetica-Oblique",
    ))
    styles.add(ParagraphStyle(
        name="BigScore", fontSize=34, leading=38, textColor=COLOR_PRIMARY,
        fontName="Helvetica-Bold", alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="StageLabel", fontSize=12, leading=15, fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="FlagText", fontSize=9, leading=13, textColor=COLOR_TEXT,
        fontName="Helvetica", leftIndent=8,
    ))
    return styles


def _header_bar(patient_name: str, styles):
    """Deep-blue title bar at the top of the report."""
    title = Paragraph("OrthoAssist AI — Recovery Assessment Report", styles["ReportTitle"])
    subtitle = Paragraph(
        f"Patient: <b>{patient_name}</b> &nbsp;|&nbsp; "
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        styles["ReportSubtitle"],
    )
    header_table = Table(
        [[title], [subtitle]],
        colWidths=[170 * mm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return header_table


def _patient_info_table(patient, styles):
    data = [
        ["Name", patient.name, "Age", str(patient.age)],
        ["Gender", patient.gender or "—", "Bone Type", patient.bone_type or "—"],
    ]
    table = Table(data, colWidths=[28 * mm, 55 * mm, 28 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COLOR_LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), COLOR_LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_TEXT),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _score_metric_table(rows, styles):
    """
    rows: list of (label, pre_value, post_value, improvement) tuples.
    Renders as a clean comparison table with color-coded improvement column.
    """
    header = ["Metric", "Pre-Op", "Post-Op", "Improvement"]
    table_data = [header]
    for label, pre, post, improvement in rows:
        table_data.append([label, pre, post, improvement])

    table = Table(table_data, colWidths=[55 * mm, 30 * mm, 30 * mm, 40 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6B4E1E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
    ]
    table.setStyle(TableStyle(style))
    return table


def _xray_image_pair(pre_path: str, post_path: str, styles):
    """
    Renders the pre/post X-ray images side by side. Falls back to a
    placeholder note if either file is missing (e.g. deleted, or a demo
    record without real uploads) rather than crashing report generation.
    """
    max_w, max_h = 78 * mm, 78 * mm

    def _cell(path, label):
        if path and os.path.exists(path):
            img = RLImage(path)
            ratio = min(max_w / img.imageWidth, max_h / img.imageHeight)
            img.drawWidth = img.imageWidth * ratio
            img.drawHeight = img.imageHeight * ratio
            return [img, Paragraph(label, styles["MutedNote"])]
        return [Paragraph(f"[{label} image not available]", styles["MutedNote"])]

    data = [[_cell(pre_path, "Pre-Operative"), _cell(post_path, "Post-Operative")]]
    table = Table(data, colWidths=[85 * mm, 85 * mm])
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _cori_score_block(cori_score: float, recovery_stage: str, styles):
    color = _stage_color(recovery_stage)
    score_para = Paragraph(f"{cori_score}%", styles["BigScore"])
    stage_style = ParagraphStyle(
        "StageColored", parent=styles["StageLabel"], textColor=color,
    )
    stage_para = Paragraph(recovery_stage, stage_style)

    block = Table([[score_para], [stage_para]], colWidths=[170 * mm])
    block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1, color),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 14),
    ]))
    return block


def _recommendation_box(recommendation: str, styles):
    para = Paragraph(f"<b>Recommendation:</b> {recommendation}", styles["BodyTextCustom"])
    box = Table([[para]], colWidths=[170 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF3E1")),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return box


def _footer_disclaimer(styles):
    text = (
        "This report was generated by an AI-assisted clinical decision support system. "
        "It is intended to support, not replace, clinical judgment. All findings should "
        "be reviewed and confirmed by a qualified medical professional before use in "
        "treatment decisions."
    )
    return Paragraph(text, styles["MutedNote"])


def generate_recovery_report(
    output_path: str,
    patient,
    xray_record,
    gait_record,
    cori_result,
) -> str:
    """
    Builds the full PDF report and writes it to output_path.

    patient: Patient model instance
    xray_record: XrayRecord model instance (may be None)
    gait_record: GaitRecord model instance (may be None)
    cori_result: CoriResult from cori_engine.compute_cori()

    Returns the output_path on success.
    """
    styles = _build_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=0, bottomMargin=18 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )

    story = []

    # ---- Header ----
    story.append(_header_bar(patient.name, styles))
    story.append(Spacer(1, 14))

    # ---- Patient Info ----
    story.append(Paragraph("Patient Information", styles["SectionHeading"]))
    story.append(_patient_info_table(patient, styles))
    story.append(Spacer(1, 10))

    # ---- CORI Summary (headline result, shown early) ----
    story.append(Paragraph("Composite Orthopedic Recovery Index (CORI)", styles["SectionHeading"]))
    story.append(_cori_score_block(cori_result.cori_score, cori_result.recovery_stage, styles))
    story.append(Spacer(1, 8))
    story.append(Paragraph(cori_result.summary, styles["BodyTextCustom"]))
    story.append(Spacer(1, 8))

    if cori_result.flags:
        story.append(Paragraph("Key Observations", styles["SubHeading"]))
        for flag in cori_result.flags:
            story.append(Paragraph(f"• {flag}", styles["FlagText"]))
        story.append(Spacer(1, 6))

    story.append(_recommendation_box(cori_result.recommendation, styles))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Weighting used: {int(cori_result.weight_structural * 100)}% Structural / "
        f"{int(cori_result.weight_functional * 100)}% Functional",
        styles["MutedNote"],
    ))

    story.append(PageBreak())

    # ---- Structural (X-ray) Section ----
    structural_heading_style = ParagraphStyle(
        "StructuralHeading", parent=styles["SectionHeading"], textColor=colors.HexColor("#8C6B2E"),
    )
    story.append(Paragraph("Structural Recovery Analysis (X-ray)", structural_heading_style))
    if xray_record:
        story.append(_xray_image_pair(
            xray_record.pre_image_path, xray_record.post_image_path, styles
        ))
        story.append(Spacer(1, 10))

        rows = [
            ("Fracture Gap", f"{xray_record.pre_gap_mm} mm", f"{xray_record.post_gap_mm} mm",
             f"{xray_record.gap_improvement_pct}%"),
            ("Alignment", f"{xray_record.pre_alignment_pct}%", f"{xray_record.post_alignment_pct}%",
             f"{xray_record.alignment_improvement_pct}%"),
            ("Continuity", f"{xray_record.pre_continuity_pct}%", f"{xray_record.post_continuity_pct}%",
             f"{xray_record.continuity_improvement_pct}%"),
        ]
        story.append(_score_metric_table(rows, styles))
        story.append(Spacer(1, 8))

        score_color = _score_color(xray_record.structural_recovery_score)
        score_style = ParagraphStyle("SRSScore", parent=styles["SubHeading"], textColor=score_color)
        story.append(Paragraph(
            f"Structural Recovery Score: {xray_record.structural_recovery_score}%", score_style
        ))
        if cori_result.structural_detail:
            story.append(Paragraph(cori_result.structural_detail, styles["BodyTextCustom"]))
    else:
        story.append(Paragraph("No X-ray analysis available for this assessment.", styles["MutedNote"]))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", color=COLOR_BORDER, thickness=0.75))
    story.append(Spacer(1, 12))

    # ---- Functional (Gait) Section ----
    functional_heading_style = ParagraphStyle(
        "FunctionalHeading", parent=styles["SectionHeading"], textColor=COLOR_PURPLE,
    )
    story.append(Paragraph("Functional Recovery Analysis (Gait)", functional_heading_style))
    if gait_record:
        rows = [
            ("Walking Speed", f"{gait_record.walking_speed} m/s", "—", "—"),
            ("Cadence", f"{gait_record.cadence} steps/min", "—", "—"),
            ("Stride Length", f"{gait_record.stride_length} m", "—", "—"),
            ("Step Symmetry", f"{gait_record.step_symmetry}%", "—", "—"),
            ("Knee Flexion", f"{gait_record.knee_flexion}°", "—", "—"),
            ("Balance Score", f"{gait_record.balance_score}%", "—", "—"),
        ]
        # Functional metrics are single-visit measurements (not pre/post
        # pairs like structural), so we relabel the table header accordingly.
        header = ["Metric", "Measured Value"]
        table_data = [header] + [[r[0], r[1]] for r in rows]
        table = Table(table_data, colWidths=[75 * mm, 95 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PURPLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ]))
        story.append(table)
        story.append(Spacer(1, 8))

        score_color = _score_color(gait_record.functional_recovery_score)
        score_style = ParagraphStyle("FRSScore", parent=styles["SubHeading"], textColor=score_color)
        story.append(Paragraph(
            f"Functional Recovery Score: {gait_record.functional_recovery_score}%", score_style
        ))
        if cori_result.functional_detail:
            story.append(Paragraph(cori_result.functional_detail, styles["BodyTextCustom"]))
    else:
        story.append(Paragraph("No gait analysis available for this assessment.", styles["MutedNote"]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=COLOR_BORDER, thickness=0.75))
    story.append(Spacer(1, 8))
    story.append(_footer_disclaimer(styles))

    doc.build(story)
    return output_path
