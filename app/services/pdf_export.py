"""Server-side PDF generation for analysis reports using ReportLab."""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Palette matching the web UI
_BG       = colors.HexColor("#09090b")
_TEXT     = colors.HexColor("#fafafa")
_MUTED    = colors.HexColor("#888888")
_BORDER   = colors.HexColor("#27272a")
_RED      = colors.HexColor("#ef4444")
_AMBER    = colors.HexColor("#f59e0b")
_GREEN    = colors.HexColor("#22c55e")
_DIM_BG   = colors.HexColor("#18181b")
_RISK_COLORS = {"high": _RED, "medium": _AMBER, "low": _GREEN}
_RISK_BG  = {
    "high":   colors.HexColor("#2d0a0a"),
    "medium": colors.HexColor("#2d1b00"),
    "low":    colors.HexColor("#052015"),
}

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 20 * mm
T_MARGIN = B_MARGIN = 20 * mm
CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN


def _styles():
    base = getSampleStyleSheet()
    mono = "Courier"
    sans = "Helvetica"
    bold = "Helvetica-Bold"
    return {
        "brand":   ParagraphStyle("Brand",   parent=base["Normal"], fontName=mono,
                                  fontSize=10, textColor=_MUTED, spaceAfter=0),
        "title":   ParagraphStyle("Title",   parent=base["Normal"], fontName=bold,
                                  fontSize=22, textColor=_TEXT, spaceAfter=2*mm, leading=26),
        "meta":    ParagraphStyle("Meta",    parent=base["Normal"], fontName=mono,
                                  fontSize=8, textColor=_MUTED, spaceAfter=1*mm),
        "h2":      ParagraphStyle("H2",      parent=base["Normal"], fontName=bold,
                                  fontSize=11, textColor=_TEXT, spaceBefore=6*mm, spaceAfter=3*mm),
        "label":   ParagraphStyle("Label",   parent=base["Normal"], fontName=mono,
                                  fontSize=8, textColor=_MUTED, spaceAfter=1*mm,
                                  letterSpacing=1),
        "body":    ParagraphStyle("Body",    parent=base["Normal"], fontName=sans,
                                  fontSize=9, textColor=colors.HexColor("#d4d4d8"),
                                  leading=14, spaceAfter=2*mm),
        "small":   ParagraphStyle("Small",   parent=base["Normal"], fontName=mono,
                                  fontSize=8, textColor=_MUTED, spaceAfter=1.5*mm, leading=12),
        "redline": ParagraphStyle("Redline", parent=base["Normal"], fontName=sans,
                                  fontSize=9, textColor=_GREEN,
                                  spaceAfter=1.5*mm, leading=13),
        "statute": ParagraphStyle("Statute", parent=base["Normal"], fontName=mono,
                                  fontSize=8, textColor=colors.HexColor("#60a5fa"),
                                  spaceAfter=1*mm),
        "action":  ParagraphStyle("Action",  parent=base["Normal"], fontName=sans,
                                  fontSize=9, textColor=colors.HexColor("#a78bfa"),
                                  spaceAfter=2*mm, leading=13),
        "footer":  ParagraphStyle("Footer",  parent=base["Normal"], fontName=mono,
                                  fontSize=7, textColor=_MUTED, alignment=TA_CENTER),
        "tbl_hdr": ParagraphStyle("TblHdr",  parent=base["Normal"], fontName=bold,
                                  fontSize=8, textColor=_TEXT),
        "tbl_val": ParagraphStyle("TblVal",  parent=base["Normal"], fontName=sans,
                                  fontSize=9, textColor=colors.HexColor("#d4d4d8")),
    }


def _header_footer(canvas, doc):
    """Draw dark header bar and footer on every page."""
    canvas.saveState()
    # Header bar
    canvas.setFillColor(_BG)
    canvas.rect(0, PAGE_H - 14*mm, PAGE_W, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(_MUTED)
    canvas.setFont("Courier", 8)
    canvas.drawString(L_MARGIN, PAGE_H - 9*mm, "// veritas — contract risk analysis")
    canvas.setFont("Courier", 8)
    canvas.drawRightString(PAGE_W - R_MARGIN, PAGE_H - 9*mm,
                           f"page {doc.page}")
    # Header border
    canvas.setStrokeColor(_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0, PAGE_H - 14*mm, PAGE_W, PAGE_H - 14*mm)
    # Footer
    canvas.setFillColor(_MUTED)
    canvas.setFont("Courier", 7)
    canvas.drawCentredString(PAGE_W / 2, 10*mm,
        "Not legal advice — consult a Fachanwalt für Arbeitsrecht for binding guidance.")
    canvas.setStrokeColor(_BORDER)
    canvas.line(L_MARGIN, 14*mm, PAGE_W - R_MARGIN, 14*mm)
    canvas.restoreState()


def build_pdf(report: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=L_MARGIN, rightMargin=R_MARGIN,
        topMargin=T_MARGIN + 14*mm,
        bottomMargin=B_MARGIN + 10*mm,
        title="Veritas Contract Risk Analysis",
        author="Veritas",
    )
    S = _styles()
    story = []

    # ── Cover block ───────────────────────────────────────────────────────────
    story.append(Paragraph("// veritas", S["brand"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("Contract Risk Analysis", S["title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=4*mm))

    meta_parts = []
    if report.get("profile"):
        meta_parts.append(f"Profile: {report['profile']}")
    if report.get("date"):
        meta_parts.append(f"Date: {report['date']}")
    if meta_parts:
        story.append(Paragraph("  ·  ".join(meta_parts), S["meta"]))
    story.append(Spacer(1, 3*mm))

    # ── Risk summary table ────────────────────────────────────────────────────
    story.append(Paragraph("// summary", S["label"]))
    summary = report.get("summary", {})

    def _risk_pill(label, color):
        return Paragraph(f'<font color="#{color[1:]}">{label}</font>', S["tbl_hdr"])

    summary_data = [
        [Paragraph("Risk tier", S["tbl_hdr"]), Paragraph("Findings", S["tbl_hdr"])],
        [_risk_pill("HIGH",   "#ef4444"), str(summary.get("high",   0))],
        [_risk_pill("MEDIUM", "#f59e0b"), str(summary.get("medium", 0))],
        [_risk_pill("LOW",    "#22c55e"), str(summary.get("low",    0))],
        [Paragraph("Total", S["tbl_hdr"]),  str(summary.get("total",  0))],
    ]
    tbl = Table(summary_data, colWidths=[50*mm, 20*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  _DIM_BG),
        ("BACKGROUND",    (0, 1), (-1, -2), colors.HexColor("#111113")),
        ("BACKGROUND",    (0, -1), (-1, -1), _DIM_BG),
        ("TEXTCOLOR",     (1, 1), (1, -1),  _TEXT),
        ("FONTNAME",      (1, 1), (1, -1),  "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("GRID",          (0, 0), (-1, -1), 0.3, _BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#111113"), colors.HexColor("#18181b")]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6*mm))

    # ── Rate benchmark ────────────────────────────────────────────────────────
    bench = report.get("rate_benchmark")
    if bench and bench.get("offered", 0) > 0:
        story.append(Paragraph("// rate benchmark", S["label"]))
        story.append(Paragraph(
            f"Offered <b>€{bench.get('offered', 0):.0f}/h</b> · "
            f"p25 €{bench.get('p25', 0)} · "
            f"Median €{bench.get('median', 0)} · "
            f"p75 €{bench.get('p75', 0)} · "
            f"{bench.get('skill_category', '')} / {bench.get('experience', '')}",
            S["body"],
        ))
        story.append(Spacer(1, 3*mm))

    # ── Findings ──────────────────────────────────────────────────────────────
    story.append(Paragraph("// findings", S["label"]))
    findings = report.get("findings", [])
    if not findings:
        story.append(Paragraph("No findings.", S["body"]))

    for i, f in enumerate(findings, start=1):
        risk = (f.get("risk") or "low").lower()
        rc   = _RISK_COLORS.get(risk, _MUTED)
        rbg  = _RISK_BG.get(risk, _DIM_BG)

        # Risk badge row
        num_str   = str(i).zfill(2)
        badge_txt = risk.upper()
        badge_row = Table(
            [[Paragraph(f'<font color="#888">{num_str}</font>  {f.get("title", "")}', S["tbl_val"]),
              Paragraph(f'<font color="#{rc.hexval()[2:]}">{badge_txt}</font>', S["tbl_hdr"])]],
            colWidths=[CONTENT_W - 24*mm, 20*mm],
        )
        badge_row.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), rbg),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (0, -1),  6),
            ("RIGHTPADDING",  (-1, 0), (-1, -1), 6),
            ("ALIGN",         (1, 0), (1, -1),   "RIGHT"),
            ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
        ]))
        story.append(badge_row)

        body = f.get("body", "")
        if body:
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph(body, S["body"]))

        clause = f.get("clause", "")
        if clause:
            snippet = clause[:240].rstrip() + ("…" if len(clause) > 240 else "")
            story.append(Paragraph(f'Original: "{snippet}"', S["small"]))

        statute = f.get("statute")
        if statute:
            story.append(Paragraph(f"§ {statute}", S["statute"]))

        redline = f.get("redline")
        if redline and redline.strip("—– "):
            story.append(Paragraph(f"→ Redline: {redline}", S["redline"]))

        action = f.get("action")
        if action:
            story.append(Paragraph(f"↗ {action}", S["action"]))

        story.append(HRFlowable(width="100%", thickness=0.3, color=_BORDER, spaceAfter=4*mm))

    # ── Negotiation brief ─────────────────────────────────────────────────────
    brief = report.get("brief", "")
    if brief:
        story.append(Paragraph("// negotiation brief", S["label"]))
        for line in brief.split("\n"):
            stripped = line.strip()
            if stripped:
                story.append(Paragraph(stripped, S["body"]))
            else:
                story.append(Spacer(1, 2*mm))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
