"""Server-side PDF generation for analysis reports using ReportLab."""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
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

_RISK_COLORS = {
    "high":   colors.HexColor("#c0392b"),
    "medium": colors.HexColor("#d35400"),
    "low":    colors.HexColor("#27ae60"),
}
_ACCENT = colors.HexColor("#1a1a2e")
_MUTED  = colors.HexColor("#666666")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("VTitle", parent=base["Normal"],
                                fontName="Helvetica-Bold", fontSize=18,
                                textColor=_ACCENT, spaceAfter=2*mm),
        "meta":  ParagraphStyle("VMeta",  parent=base["Normal"],
                                fontName="Helvetica", fontSize=9,
                                textColor=_MUTED, spaceAfter=1*mm),
        "h2":    ParagraphStyle("VH2",    parent=base["Normal"],
                                fontName="Helvetica-Bold", fontSize=12,
                                textColor=_ACCENT, spaceBefore=4*mm, spaceAfter=2*mm),
        "body":  ParagraphStyle("VBody",  parent=base["Normal"],
                                fontName="Helvetica", fontSize=9,
                                leading=13, spaceAfter=1.5*mm),
        "small": ParagraphStyle("VSmall", parent=base["Normal"],
                                fontName="Helvetica-Oblique", fontSize=8,
                                textColor=_MUTED, spaceAfter=1*mm),
        "redline": ParagraphStyle("VRedline", parent=base["Normal"],
                                  fontName="Helvetica", fontSize=9,
                                  textColor=colors.HexColor("#1a6b1a"),
                                  spaceAfter=1*mm),
        "statute": ParagraphStyle("VStatute", parent=base["Normal"],
                                  fontName="Helvetica-Oblique", fontSize=8,
                                  textColor=colors.HexColor("#34495e"),
                                  spaceAfter=3*mm),
    }


def build_pdf(report: dict) -> bytes:
    """Generate a PDF from an AnalysisReport dict. Returns raw PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    S = _styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("VERITAS — Contract Risk Analysis", S["title"]))
    story.append(Paragraph(
        f"Profile: {report.get('profile', '—')}  ·  Date: {report.get('date', '—')}",
        S["meta"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=_ACCENT, spaceAfter=4*mm))

    # ── Summary table ─────────────────────────────────────────────────────────
    summary = report.get("summary", {})
    summary_data = [
        [Paragraph("<b>Risk tier</b>", S["body"]), Paragraph("<b>Findings</b>", S["body"])],
        [Paragraph('<font color="#c0392b">HIGH</font>',   S["body"]), str(summary.get("high",   0))],
        [Paragraph('<font color="#d35400">MEDIUM</font>', S["body"]), str(summary.get("medium", 0))],
        [Paragraph('<font color="#27ae60">LOW</font>',    S["body"]), str(summary.get("low",    0))],
        [Paragraph("<b>Total</b>", S["body"]),                        str(summary.get("total",  0))],
    ]
    tbl = Table(summary_data, colWidths=[55*mm, 25*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), _ACCENT),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#f7f7f7"), colors.white]),
        ("BACKGROUND",   (0, -1), (-1, -1), colors.HexColor("#ececec")),
        ("FONTNAME",     (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 5*mm))

    # ── Rate benchmark ────────────────────────────────────────────────────────
    bench = report.get("rate_benchmark")
    if bench:
        story.append(Paragraph("Rate Benchmark", S["h2"]))
        offered = bench.get("offered", 0)
        p25     = bench.get("p25", 0)
        median  = bench.get("median", 0)
        p75     = bench.get("p75", 0)
        skill   = bench.get("skill_category", "")
        exp     = bench.get("experience", "")
        source  = bench.get("source", "")
        story.append(Paragraph(
            f"Offered: <b>€{offered:.0f}/h</b>  ·  p25: €{p25}  ·  "
            f"Median: €{median}  ·  p75: €{p75}  ·  "
            f"{skill} / {exp}  ({source})",
            S["body"],
        ))
        story.append(Spacer(1, 3*mm))

    # ── Findings ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Findings", S["h2"]))
    findings = report.get("findings", [])
    if not findings:
        story.append(Paragraph("No findings.", S["body"]))
    for i, f in enumerate(findings, start=1):
        risk = (f.get("risk") or "low").lower()
        rc   = _RISK_COLORS.get(risk, colors.grey)

        header_style = ParagraphStyle(
            f"FH{i}", parent=S["body"],
            fontName="Helvetica-Bold", fontSize=10,
            textColor=rc, spaceAfter=1.5*mm,
        )
        story.append(Paragraph(
            f"{i}. {f.get('title', '')}  [{risk.upper()}]", header_style
        ))

        body = f.get("body", "")
        if body:
            story.append(Paragraph(body, S["body"]))

        clause = f.get("clause", "")
        if clause:
            snippet = clause[:220].rstrip() + ("…" if len(clause) > 220 else "")
            story.append(Paragraph(f'Original: "{snippet}"', S["small"]))

        redline = f.get("redline")
        if redline and redline.strip("—– "):
            story.append(Paragraph(f"Suggested redline: {redline}", S["redline"]))

        action = f.get("action")
        if action:
            story.append(Paragraph(f"Action: {action}", S["statute"]))

        statute = f.get("statute")
        if statute:
            story.append(Paragraph(f"Statute: {statute}", S["statute"]))

        story.append(HRFlowable(
            width="100%", thickness=0.3,
            color=colors.HexColor("#dddddd"), spaceAfter=2*mm,
        ))

    # ── Negotiation brief ─────────────────────────────────────────────────────
    brief = report.get("brief", "")
    if brief:
        story.append(Paragraph("Negotiation Brief", S["h2"]))
        for line in brief.split("\n"):
            stripped = line.strip()
            if stripped:
                story.append(Paragraph(stripped, S["body"]))
            else:
                story.append(Spacer(1, 2*mm))

    doc.build(story)
    return buf.getvalue()
