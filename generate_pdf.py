"""Build the classic PDF resume from content.json."""

import json
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "content.json").read_text(encoding="utf-8-sig"))
OUTPUT = ROOT / "assets" / "resume.pdf"

pdfmetrics.registerFont(TTFont("Malgun", "C:/Windows/Fonts/malgun.ttf"))
pdfmetrics.registerFont(TTFont("Malgun-Bold", "C:/Windows/Fonts/malgunbd.ttf"))
pdfmetrics.registerFontFamily("Malgun", normal="Malgun", bold="Malgun-Bold")

INK = colors.HexColor("#202b3b")
BODY = colors.HexColor("#526278")
ACCENT = colors.HexColor("#4c6e96")
BORDER = colors.HexColor("#d7e0eb")
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 54
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


def style(name, **kwargs):
    options = dict(
        fontName="Malgun", fontSize=9, leading=14,
        textColor=BODY, alignment=TA_LEFT, wordWrap="CJK",
    )
    options.update(kwargs)
    return ParagraphStyle(name, **options)


STYLES = {
    "name": style("name", fontName="Malgun-Bold", fontSize=28, leading=35, textColor=INK, spaceAfter=1),
    "handle": style("handle", fontSize=10, leading=15, textColor=ACCENT, spaceAfter=13),
    "role": style("role", fontName="Malgun-Bold", fontSize=10.5, leading=16, textColor=INK, spaceAfter=7),
    "intro": style("intro", fontSize=9, leading=14, spaceAfter=8),
    "highlight": style("highlight", fontSize=8.7, leading=13, leftIndent=10),
    "section_number": style("section_number", fontSize=8.4, leading=16, textColor=ACCENT),
    "section": style("section", fontName="Malgun-Bold", fontSize=13.5, leading=18, textColor=INK),
    "date": style("date", fontSize=8.2, leading=13, textColor=ACCENT),
    "entry_title": style("entry_title", fontSize=9.3, leading=14, textColor=INK),
    "entry_subtitle": style("entry_subtitle", fontSize=8.6, leading=12.5),
    "entry_description": style("entry_description", fontSize=8.2, leading=12.5, spaceBefore=3),
}


def para(value, style_name):
    return Paragraph(escape(str(value)), STYLES[style_name])


def draw_page(canvas, doc):
    canvas.saveState()
    canvas.setTitle(f"{DATA['profile'].get('name', 'Resume')} Resume")
    canvas.setAuthor(DATA["profile"].get("name", ""))
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 45, PAGE_WIDTH - MARGIN, 45)
    canvas.setFont("Malgun", 7.5)
    canvas.setFillColor(ACCENT)
    canvas.drawString(MARGIN, PAGE_HEIGHT - 37, "SECURITY PROFILE")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 37, "RESUME")
    canvas.setFillColor(BODY)
    canvas.drawString(MARGIN, 30, f"Updated {DATA.get('updatedAt', '')}")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 30, str(doc.page))
    canvas.restoreState()


def section_flowables(section, number):
    heading = Table(
        [[para(f"{number:02d}", "section_number"), para(section.get("title", ""), "section")]],
        colWidths=[88, CONTENT_WIDTH - 88], hAlign="LEFT",
    )
    heading.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("LINEABOVE", (0, 0), (-1, 0), 0.7, INK),
    ]))
    entries = []
    for item in section.get("items", []):
        title = f"<b>{escape(str(item.get('title', '')))}</b>"
        tags = item.get("tags") or []
        if tags:
            label = " / ".join(escape(str(tag)) for tag in tags)
            title += f' <font color="#4c6e96" size="8.2">|  {label}</font>'
        body = [Paragraph(title, STYLES["entry_title"])]
        if item.get("subtitle"):
            body.append(para(item["subtitle"], "entry_subtitle"))
        if item.get("description"):
            body.append(para(item["description"], "entry_description"))
        entry = Table(
            [[para(item.get("date", ""), "date"), body]],
            colWidths=[88, CONTENT_WIDTH - 88], hAlign="LEFT",
        )
        entry.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, -1), 0.35, BORDER),
        ]))
        entries.append(entry)
    if entries:
        return [KeepTogether([heading, entries[0]]), *entries[1:]]
    return [heading]


def main():
    profile = DATA["profile"]
    story = [
        para(profile.get("name", ""), "name"),
        para(profile.get("handle", ""), "handle"),
        para(profile.get("role", ""), "role"),
        para(profile.get("intro", ""), "intro"),
    ]
    for highlight in profile.get("highlights", []):
        story.append(Paragraph("-  " + escape(str(highlight)), STYLES["highlight"]))
    story.append(Spacer(1, 18))
    for number, section in enumerate(DATA.get("sections", []), 1):
        story.extend(section_flowables(section, number))
        story.append(Spacer(1, 18))

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=65, bottomMargin=56, title=f"{profile.get('name', 'Resume')} Resume",
        author=profile.get("name", ""),
    )
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(OUTPUT)


if __name__ == "__main__":
    main()
