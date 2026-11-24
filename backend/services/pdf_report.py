"""Build a downloadable PDF containing the generated pipeline results."""

import re
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _inline_markup(value: str) -> str:
    """Convert common inline Markdown marks into ReportLab-supported markup."""
    value = escape(value)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(r"\[(.+?)\]\([^)]+\)", r"\1", value)
    return value


def _markdown_flowables(markdown_text: str, styles) -> list:
    flowables = []
    lines = markdown_text.splitlines()
    index = 0
    in_code = False
    code_lines: list[str] = []

    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("```"):
            if in_code:
                code_text = "<br/>".join(escape(part) for part in code_lines)
                flowables.append(Paragraph(code_text or "&nbsp;", styles["CodeBlock"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not line:
            index += 1
            continue
        if re.fullmatch(r"[-*_]{3,}", line):
            flowables.append(HRFlowable(width="100%", color=colors.HexColor("#d7e2ea")))
            flowables.append(Spacer(1, 4))
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines) and "---" in lines[index + 1]:
            table_rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    table_rows.append(
                        [Paragraph(_inline_markup(cell), styles["TableCell"]) for cell in cells]
                    )
                index += 1
            if table_rows:
                column_count = max(len(row) for row in table_rows)
                normalized = [row + [Paragraph("", styles["TableCell"])] * (column_count - len(row)) for row in table_rows]
                table = Table(normalized, colWidths=[165 * mm / column_count] * column_count, repeatRows=1)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf2f5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#153b4a")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd7dd")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                flowables.extend([table, Spacer(1, 7)])
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = min(len(heading.group(1)), 3)
            flowables.append(Paragraph(_inline_markup(heading.group(2)), styles[f"MarkdownH{level}"]))
            index += 1
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", line)
        numbered = re.match(r"^\d+[.)]\s+(.+)$", line)
        if bullet or numbered:
            item_text = _inline_markup((bullet or numbered).group(1))
            flowables.append(Paragraph(f"&#8226; {item_text}", styles["ListItem"]))
            index += 1
            continue

        flowables.append(Paragraph(_inline_markup(line), styles["BodyText"]))
        index += 1

    if in_code and code_lines:
        flowables.append(Paragraph("<br/>".join(escape(part) for part in code_lines), styles["CodeBlock"]))
    return flowables


def create_result_pdf(user_requirement: str, specification: str, recommendation: str) -> bytes:
    """Return a compact, formatted PDF report for the displayed result."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Requirement Engineering Report",
        author="Requirement Engineering Pipeline",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=25, alignment=TA_CENTER,
        textColor=colors.HexColor("#153b4a"), spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="ReportSection", parent=styles["Heading1"], fontSize=15,
        leading=19, textColor=colors.HexColor("#087f70"), spaceBefore=10, spaceAfter=8,
    ))
    for level, size in ((1, 14), (2, 12), (3, 10.5)):
        styles.add(ParagraphStyle(
            name=f"MarkdownH{level}", parent=styles["Heading2"], fontSize=size,
            leading=size + 3, textColor=colors.HexColor("#153b4a"),
            spaceBefore=8, spaceAfter=4,
        ))
    styles.add(ParagraphStyle(
        name="ListItem", parent=styles["BodyText"], leftIndent=12,
        firstLineIndent=-9, spaceAfter=3, leading=14,
    ))
    styles.add(ParagraphStyle(
        name="TableCell", parent=styles["BodyText"], fontSize=8,
        leading=10, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="CodeBlock", parent=styles["Code"], fontSize=8,
        leading=11, backColor=colors.HexColor("#f2f5f6"),
        borderPadding=6, spaceBefore=4, spaceAfter=7,
    ))

    story = [Paragraph("Requirement Engineering Report", styles["ReportTitle"])]
    story.append(Paragraph("Project requirement", styles["ReportSection"]))
    story.extend(_markdown_flowables(user_requirement, styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Requirement specification", styles["ReportSection"]))
    story.extend(_markdown_flowables(specification, styles))
    story.append(PageBreak())
    story.append(Paragraph("SDLC recommendation", styles["ReportSection"]))
    story.extend(_markdown_flowables(recommendation, styles))

    def add_page_number(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#687984"))
        canvas.drawCentredString(A4[0] / 2, 10 * mm, f"Page {_doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return buffer.getvalue()
