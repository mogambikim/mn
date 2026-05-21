from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def png_to_pdf(png_path: str | Path, pdf_path: str | Path) -> Path:
    png = Path(png_path)
    pdf = Path(pdf_path)
    image = Image.open(png)
    width, height = image.size

    doc = canvas.Canvas(str(pdf), pagesize=(width, height))
    doc.drawImage(ImageReader(image), 0, 0, width=width, height=height)
    doc.showPage()
    doc.save()
    return pdf
