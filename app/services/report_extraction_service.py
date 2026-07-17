"""Text extraction from PDF and images (OCR)."""

import os


class ReportExtractionService:
  """Extract text from uploaded medical reports."""

  @staticmethod
  def extract_from_pdf(file_path):
    try:
      from pypdf import PdfReader
    except ImportError:
      raise RuntimeError("pypdf is required for PDF extraction.")

    if not os.path.exists(file_path):
      raise FileNotFoundError("PDF file not found.")

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
      text = page.extract_text() or ""
      pages.append(text)
    return "\n".join(pages).strip()

  @staticmethod
  def extract_from_image(file_path):
    try:
      from PIL import Image
      import pytesseract
    except ImportError:
      raise RuntimeError("Pillow and pytesseract are required for OCR.")

    if not os.path.exists(file_path):
      raise FileNotFoundError("Image file not found.")

    image = Image.open(file_path)
    return pytesseract.image_to_string(image).strip()

  @classmethod
  def extract_text(cls, file_path, file_type):
    if file_type == "pdf":
      return cls.extract_from_pdf(file_path)
    if file_type == "image":
      return cls.extract_from_image(file_path)
    raise ValueError("Unsupported file type for extraction.")
