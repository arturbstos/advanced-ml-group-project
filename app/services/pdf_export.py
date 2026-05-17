"""Server-side PDF generation for analysis reports.

Formal academic / LaTeX-style layout: monochrome palette, Times Roman
serif body throughout, sans-serif bold section headings, hairline rules,
and risk indicated by bracketed labels rather than colour fills.
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ──────────────────────────────────────────────────────────────────────────────
# Monochrome palette
# ──────────────────────────────────────────────────────────────────────────────
_BLACK   = colors.HexColor("#000000")
_TEXT    = colors.HexColor("#1A1A1A")   # body text
_MUTED   = colors.HexColor("#666666")   # meta / disclaimers
_FAINT   = colors.HexColor("#999999")   # page numbers / fine print
_RULE    = colors.HexColor("#000000")   # hairlines

# Risk left-rule intensity (greyscale). Differentiates without colour.
_RULE_HIGH = colors.HexColor("#000000")
_RULE_MED  = colors.HexColor("#555555")
_RULE_LOW  = colors.HexColor("#BBBBBB")

_RISK_RULE  = {"high": _RULE_HIGH, "medium": _RULE_MED, "low": _RULE_LOW}
_RISK_LABEL = {"high": "HIGH", "medium": "MED", "low": "LOW"}

# ──────────────────────────────────────────────────────────────────────────────
# Page geometry
# ──────────────────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 25 * mm
T_MARGIN = 26 * mm
B_MARGIN = 24 * mm
CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN


# ──────────────────────────────────────────────────────────────────────────────
# Stylesheet — Times throughout (academic), Helvetica-Bold only for headings.
# ──────────────────────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    serif       = "Times-Roman"
    serif_bold  = "Times-Bold"
    serif_it    = "Times-Italic"
    sans_bold   = "Helvetica-Bold"
    mono        = "Courier"
    return {
        "wordmark":  ParagraphStyle("Wordmark",  parent=base["Normal"],
            fontName=sans_bold, fontSize=9, textColor=_TEXT,
            spaceAfter=2 * mm, leading=11),
        "title":     ParagraphStyle("Title", parent=base["Normal"],
            fontName=serif_bold, fontSize=20, textColor=_BLACK,
            spaceAfter=2 * mm, leading=24, alignment=TA_CENTER),
        "subtitle":  ParagraphStyle("Subtitle", parent=base["Normal"],
            fontName=serif_it, fontSize=10.5, textColor=_TEXT,
            spaceAfter=4 * mm, leading=14, alignment=TA_CENTER),
        "meta":      ParagraphStyle("Meta", parent=base["Normal"],
            fontName=serif, fontSize=10, textColor=_TEXT,
            spaceAfter=1 * mm, leading=13, alignment=TA_CENTER),

        "section":   ParagraphStyle("Section", parent=base["Normal"],
            fontName=serif_bold, fontSize=12, textColor=_BLACK,
            spaceBefore=6 * mm, spaceAfter=2 * mm, leading=15),

        "body":      ParagraphStyle("Body", parent=base["Normal"],
            fontName=serif, fontSize=10, textColor=_TEXT,
            leading=14, spaceAfter=2 * mm, alignment=TA_JUSTIFY),
        "finding_title": ParagraphStyle("FindingTitle", parent=base["Normal"],
            fontName=serif_bold, fontSize=10.5, textColor=_BLACK,
            spaceAfter=1.5 * mm, leading=14),
        "risk_tag":  ParagraphStyle("RiskTag", parent=base["Normal"],
            fontName=mono, fontSize=8.5, textColor=_TEXT,
            alignment=TA_LEFT, leading=11),

        "clause":    ParagraphStyle("Clause", parent=base["Normal"],
            fontName=serif_it, fontSize=9.5, textColor=_TEXT,
            leftIndent=5 * mm, rightIndent=3 * mm,
            leading=13, spaceBefore=1 * mm, spaceAfter=2 * mm,
            alignment=TA_JUSTIFY),

        "redline_label": ParagraphStyle("RedlineLabel", parent=base["Normal"],
            fontName=sans_bold, fontSize=8.5, textColor=_TEXT,
            spaceBefore=1 * mm, spaceAfter=0.5 * mm, leading=11),
        "redline":   ParagraphStyle("Redline", parent=base["Normal"],
            fontName=serif, fontSize=9.5, textColor=_BLACK,
            leftIndent=5 * mm, rightIndent=3 * mm,
            leading=13, spaceAfter=2 * mm, alignment=TA_JUSTIFY),

        "statute":   ParagraphStyle("Statute", parent=base["Normal"],
            fontName=mono, fontSize=8.5, textColor=_TEXT,
            spaceAfter=1 * mm, leading=11),
        "action":    ParagraphStyle("Action", parent=base["Normal"],
            fontName=serif_bold, fontSize=9.5, textColor=_BLACK,
            leading=13, spaceAfter=1 * mm),

        "tbl_hdr":   ParagraphStyle("TblHdr", parent=base["Normal"],
            fontName=sans_bold, fontSize=8.5, textColor=_BLACK,
            alignment=TA_CENTER, leading=11),
        "tbl_val":   ParagraphStyle("TblVal", parent=base["Normal"],
            fontName=serif, fontSize=10, textColor=_TEXT,
            leading=13, alignment=TA_CENTER),
        "tbl_num":   ParagraphStyle("TblNum", parent=base["Normal"],
            fontName=serif_bold, fontSize=12, textColor=_BLACK,
            alignment=TA_CENTER, leading=14),

        "footer":    ParagraphStyle("Footer", parent=base["Normal"],
            fontName=serif_it, fontSize=8, textColor=_MUTED,
            alignment=TA_CENTER, leading=11),
        "footer_pg": ParagraphStyle("FooterPg", parent=base["Normal"],
            fontName=serif, fontSize=8, textColor=_TEXT,
            alignment=TA_CENTER),
    }


def _rule(thickness=0.6, space_after=2):
    return HRFlowable(width="100%", thickness=thickness,
                      color=_RULE, spaceAfter=space_after * mm)


def _hairline(space_after=2):
    return HRFlowable(width="100%", thickness=0.3,
                      color=_RULE, spaceAfter=space_after * mm)


# ──────────────────────────────────────────────────────────────────────────────
# Page chrome
# ──────────────────────────────────────────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()

    if doc.page > 1:
        canvas.setStrokeColor(_RULE)
        canvas.setLineWidth(0.4)
        canvas.line(L_MARGIN, PAGE_H - 14 * mm,
                    PAGE_W - R_MARGIN, PAGE_H - 14 * mm)
        canvas.setFont("Times-Italic", 8.5)
        canvas.setFillColor(_MUTED)
        canvas.drawString(L_MARGIN, PAGE_H - 18 * mm,
                          "Veritas — Contract Risk Analysis")

    canvas.setStrokeColor(_RULE)
    canvas.setLineWidth(0.3)
    canvas.line(L_MARGIN, 16 * mm, PAGE_W - R_MARGIN, 16 * mm)

    canvas.setFillColor(_MUTED)
    canvas.setFont("Times-Italic", 8)
    canvas.drawCentredString(
        PAGE_W / 2, 11 * mm,
        "Informational analysis only — not a substitute for advice from "
        "a Fachanwalt für Arbeitsrecht.",
    )

    canvas.setFillColor(_TEXT)
    canvas.setFont("Times-Roman", 9)
    canvas.drawCentredString(PAGE_W / 2, 6 * mm, f"— {doc.page} —")

    canvas.restoreState()


# ──────────────────────────────────────────────────────────────────────────────
# Block builders
# ──────────────────────────────────────────────────────────────────────────────
def _title_block(report: dict, S: dict) -> list:
    flow = []
    flow.append(Paragraph("VERITAS", S["wordmark"]))
    flow.append(_hairline(space_after=3))
    flow.append(Paragraph("Contract Risk Analysis", S["title"]))
    flow.append(Paragraph(
        "AI-assisted review of a freelance contract — every finding cites "
        "a specific BGB, SGB IV, UrhG, or HGB paragraph from a curated "
        "reference table.",
        S["subtitle"],
    ))

    meta_parts = []
    if report.get("profile"):
        meta_parts.append(f"<b>Profile:</b> {report['profile']}")
    if report.get("date"):
        meta_parts.append(f"<b>Date:</b> {report['date']}")
    else:
        meta_parts.append(f"<b>Date:</b> {datetime.utcnow():%Y-%m-%d}")
    if meta_parts:
        flow.append(Paragraph("   ·   ".join(meta_parts), S["meta"]))

    flow.append(Spacer(1, 2 * mm))
    flow.append(_rule(thickness=0.6, space_after=4))
    return flow


def _summary_block(report: dict, S: dict) -> list:
    summary = report.get("summary", {}) or {}
    high   = int(summary.get("high",   0))
    medium = int(summary.get("medium", 0))
    low    = int(summary.get("low",    0))
    total  = int(summary.get("total",  high + medium + low))

    data = [
        [Paragraph("High", S["tbl_hdr"]),
         Paragraph("Medium", S["tbl_hdr"]),
         Paragraph("Low / within scope", S["tbl_hdr"]),
         Paragraph("Total", S["tbl_hdr"])],
        [Paragraph(str(high),   S["tbl_num"]),
         Paragraph(str(medium), S["tbl_num"]),
         Paragraph(str(low),    S["tbl_num"]),
         Paragraph(str(total),  S["tbl_num"])],
    ]
    col_w = CONTENT_W / 4
    tbl = Table(data, colWidths=[col_w] * 4)
    tbl.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0),  (-1, 0),  0.6, _RULE),
        ("LINEBELOW",     (0, 0),  (-1, 0),  0.3, _RULE),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.6, _RULE),
        ("TOPPADDING",    (0, 0),  (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 6),
        ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
    ]))
    return [
        Paragraph("Risk summary", S["section"]),
        tbl,
        Spacer(1, 4 * mm),
    ]


def _benchmark_block(report: dict, S: dict) -> list:
    bench = report.get("rate_benchmark") or {}
    if not bench or not bench.get("offered"):
        return []

    offered = float(bench.get("offered") or 0)
    p25     = float(bench.get("p25")     or 0)
    median  = float(bench.get("median")  or 0)
    p75     = float(bench.get("p75")     or 0)

    skill = bench.get("skill_category", "")
    exp   = bench.get("experience", "")
    below = "below market" if p25 and offered < p25 else "within market range"

    sentence = (
        f"Offered rate <b>€{offered:.0f}/h</b> for {skill or 'this profile'} "
        f"({exp or 'unspecified seniority'}) is <b>{below}</b>. "
        f"Market percentiles: p25 €{p25:.0f} · median €{median:.0f} "
        f"· p75 €{p75:.0f} (Freelancer-Kompass)."
    )
    return [
        Paragraph("Rate benchmark", S["section"]),
        Paragraph(sentence, S["body"]),
        Spacer(1, 2 * mm),
    ]


def _finding_card(idx: int, f: dict, S: dict) -> Table:
    """Render one finding as a left-ruled block — greyscale rule, no fills."""
    risk = (f.get("risk") or "low").lower()
    rule_color = _RISK_RULE.get(risk, _RULE_LOW)
    label = _RISK_LABEL.get(risk, "LOW")

    title_text = f.get("title", "(untitled)")
    header_para = Paragraph(
        f'<font name="Times-Bold">{str(idx).zfill(2)}.</font> '
        f'{title_text} '
        f'<font name="Courier" size="8.5">[{label}]</font>',
        S["finding_title"],
    )

    inner = [header_para]

    body = (f.get("body") or "").strip()
    if body:
        inner.append(Spacer(1, 0.5 * mm))
        safe_body = (body.replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;"))
        inner.append(Paragraph(safe_body, S["body"]))

    clause = (f.get("clause") or "").strip()
    if clause:
        snippet = clause[:320].rstrip() + ("…" if len(clause) > 320 else "")
        snippet = (snippet.replace("&", "&amp;")
                          .replace("<", "&lt;")
                          .replace(">", "&gt;"))
        inner.append(Paragraph(f'“{snippet}”', S["clause"]))

    redline = (f.get("redline") or "").strip("—– ")
    if redline:
        rl = (redline.replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;"))
        inner.append(Paragraph("Suggested redline", S["redline_label"]))
        inner.append(Paragraph(rl, S["redline"]))

    statute = (f.get("statute") or "").strip()
    if statute:
        inner.append(Paragraph(f"Statute: {statute}", S["statute"]))

    action = (f.get("action") or "").strip()
    if action:
        inner.append(Paragraph(f"→ {action}", S["action"]))

    card = Table([[inner]], colWidths=[CONTENT_W])
    card.setStyle(TableStyle([
        ("LINEBEFORE",    (0, 0), (0, -1),  1.2, rule_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return card


def _findings_block(report: dict, S: dict) -> list:
    findings = report.get("findings", []) or []
    flow = [Paragraph("Findings", S["section"])]
    if not findings:
        flow.append(Paragraph(
            "No risky clauses were identified in the supplied contract — "
            "every clause analysed sat within standard scope for German "
            "freelance practice.",
            S["body"],
        ))
        return flow

    for i, f in enumerate(findings, start=1):
        flow.append(KeepTogether(_finding_card(i, f, S)))
        flow.append(Spacer(1, 3 * mm))
    return flow


def _brief_block(report: dict, S: dict) -> list:
    brief = (report.get("brief") or "").strip()
    if not brief:
        return []
    flow = [Paragraph("Negotiation brief", S["section"])]
    for raw in brief.split("\n"):
        line = raw.strip()
        if not line:
            flow.append(Spacer(1, 1.5 * mm))
            continue
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        flow.append(Paragraph(safe, S["body"]))
    return flow


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point — unchanged signature.
# ──────────────────────────────────────────────────────────────────────────────
def build_pdf(report: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=L_MARGIN, rightMargin=R_MARGIN,
        topMargin=T_MARGIN, bottomMargin=B_MARGIN + 6 * mm,
        title="Veritas — Contract Risk Analysis",
        author="Veritas",
        subject="AI-assisted contract review",
    )
    S = _styles()
    story: list = []
    story.extend(_title_block(report, S))
    story.extend(_summary_block(report, S))
    story.extend(_benchmark_block(report, S))
    story.extend(_findings_block(report, S))
    story.extend(_brief_block(report, S))
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
