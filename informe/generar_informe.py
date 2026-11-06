"""Genera informe_ejecutivo.pdf a partir de informe_ejecutivo.md."""

import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

BASE = Path(__file__).resolve().parent
MD_PATH = BASE / "informe_ejecutivo.md"
PDF_PATH = BASE / "informe_ejecutivo.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="Titulo", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=16, leading=19, textColor=colors.HexColor("#1f3864"), spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="Subtitulo", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10.5, leading=13, textColor=colors.HexColor("#444444"),
    alignment=TA_CENTER, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Seccion", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11.3, leading=13.5, textColor=colors.HexColor("#1f3864"),
    spaceBefore=5, spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="Subseccion", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=10, leading=12, textColor=colors.HexColor("#2e5597"),
    spaceBefore=4, spaceAfter=1.5,
))
styles.add(ParagraphStyle(
    name="Cuerpo", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.6, leading=10.6, alignment=TA_JUSTIFY, spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="Vineta", parent=styles["Cuerpo"], leftIndent=10, bulletIndent=2,
    spaceAfter=1,
))
styles.add(ParagraphStyle(
    name="Pie", parent=styles["Normal"], fontName="Helvetica-Oblique",
    fontSize=7.8, leading=9.5, alignment=TA_CENTER,
    textColor=colors.HexColor("#555555"), spaceBefore=1, spaceAfter=5,
))


def inline(text: str) -> str:
    text = text.replace("≈", "~")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text.replace("`", "")


def image_flowable(alt: str, rel_path: str):
    path = (BASE / rel_path).resolve()
    with PILImage.open(path) as img:
        w, h = img.size
    width = 14.6 * cm
    height = width * h / w
    if height > 6.4 * cm:
        height = 6.4 * cm
        width = height * w / h
    return [
        Image(str(path), width=width, height=height),
        Paragraph(inline(alt), styles["Pie"]),
    ]


def build():
    lines = MD_PATH.read_text(encoding="utf-8").splitlines()
    flow = []
    paragraph = []
    first_h1 = True
    first_h2 = True

    def flush_paragraph():
        if paragraph:
            flow.append(Paragraph(inline(" ".join(paragraph).strip()), styles["Cuerpo"]))
            paragraph.clear()

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_paragraph()
            continue
        if line.startswith("!["):
            flush_paragraph()
            m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            if m:
                flow.extend(image_flowable(m.group(1), m.group(2)))
            continue
        if line.startswith("# "):
            flush_paragraph()
            text = line[2:].strip()
            if first_h1:
                flow.append(Paragraph(inline(text), styles["Titulo"]))
                first_h1 = False
            else:
                flow.append(Paragraph(inline(text), styles["Seccion"]))
            continue
        if line.startswith("## "):
            flush_paragraph()
            if first_h2:
                flow.append(Paragraph(inline(line[3:].strip()), styles["Subtitulo"]))
                first_h2 = False
            else:
                flow.append(Paragraph(inline(line[3:].strip()), styles["Seccion"]))
            continue
        if line.startswith("### "):
            flush_paragraph()
            flow.append(Paragraph(inline(line[4:].strip()), styles["Subseccion"]))
            continue
        if line.startswith("- "):
            flush_paragraph()
            flow.append(Paragraph(inline(line[2:].strip()), styles["Vineta"], bulletText="•"))
            continue
        paragraph.append(line)
    flush_paragraph()

    doc = SimpleDocTemplate(
        str(PDF_PATH), pagesize=A4,
        leftMargin=1.7 * cm, rightMargin=1.7 * cm,
        topMargin=1.3 * cm, bottomMargin=1.3 * cm,
        title="Informe ejecutivo · COVID-19 en Estados Unidos",
        author="Elena Almansa Campos",
    )
    doc.build(flow)
    print(f"PDF generado: {PDF_PATH}")


if __name__ == "__main__":
    build()
