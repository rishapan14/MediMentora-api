"""Document Service — AI Medical Teacher Module 1.

Orchestrates: validate → store file → extract text → persist results.
No chapter/module AI generation here (those are later modules).
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.book_model import (
  BOOK_STATUS_EXTRACTED,
  BOOK_STATUS_FAILED,
  BOOK_STATUS_PROCESSING,
  BOOK_STATUS_UPLOADED,
  Book,
)
from app.services.medical_teacher.document_extractor import DocumentExtractor
from app.services.medical_teacher.document_validator import TeacherDocumentValidator, ValidatedDocument
from app.utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class BookUploadItem:
  book_id: int
  original_filename: str
  file_type: str
  file_size: int
  status: str

  def to_dict(self) -> dict:
    return {
      "book_id": self.book_id,
      "original_filename": self.original_filename,
      "file_type": self.file_type,
      "file_size": self.file_size,
      "status": self.status,
    }


@dataclass
class BookUploadResult:
  success: bool
  books: list[BookUploadItem] = field(default_factory=list)
  errors: list[str] = field(default_factory=list)
  files_received: int = 0
  files_saved: int = 0

  def to_dict(self) -> dict:
    return {
      "success": self.success,
      "files_received": self.files_received,
      "files_saved": self.files_saved,
      "books": [b.to_dict() for b in self.books],
      "errors": self.errors,
    }


class DocumentService:
  """Upload and extract medical teaching documents."""

  @classmethod
  def upload_documents(
    cls,
    user_id: int,
    files: list[FileStorage],
    title: str | None = None,
  ) -> BookUploadResult:
    """Validate and persist one or more documents (status=uploaded)."""
    cfg = current_app.config
    validator = TeacherDocumentValidator(
      max_files=int(cfg.get("TEACHER_MAX_FILES", 5)),
      max_total_bytes=int(cfg.get("TEACHER_MAX_TOTAL_BYTES", 200 * 1024 * 1024)),
      max_file_bytes=int(cfg.get("TEACHER_MAX_FILE_BYTES", 100 * 1024 * 1024)),
    )
    validation = validator.validate(files)
    result = BookUploadResult(success=False, files_received=len([f for f in files if f]))

    if not validation.ok:
      result.errors = validation.error_messages()
      return result

    upload_dir = cfg["TEACHER_UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    saved_paths: list[str] = []

    try:
      for validated in validation.files:
        book = cls._persist_one(user_id, validated, upload_dir, title)
        saved_paths.append(book.file_path)
        result.books.append(
          BookUploadItem(
            book_id=book.id,
            original_filename=book.original_filename,
            file_type=book.file_type,
            file_size=book.file_size or 0,
            status=book.status,
          )
        )
      db.session.commit()
      result.success = True
      result.files_saved = len(result.books)
      return result
    except Exception:
      db.session.rollback()
      for path in saved_paths:
        try:
          if os.path.isfile(path):
            os.remove(path)
        except OSError:
          pass
      logger.exception("Failed to upload medical teacher documents")
      result.errors.append("Failed to save uploaded documents.")
      result.books = []
      return result

  @classmethod
  def _persist_one(
    cls,
    user_id: int,
    validated: ValidatedDocument,
    upload_dir: str,
    title: str | None,
  ) -> Book:
    safe_name = secure_filename(validated.filename) or f"document.{validated.extension}"
    stored = f"{uuid.uuid4().hex}_{safe_name}"
    dest = os.path.join(upload_dir, stored)
    validated.storage.save(dest)

    display_title = (title or "").strip() or cls._title_from_filename(validated.filename)
    book = Book(
      user_id=user_id,
      title=display_title[:300],
      original_filename=validated.filename[:255],
      stored_filename=stored[:255],
      file_path=dest,
      file_type=validated.file_type,
      mime_type=validated.mime_type,
      file_size=validated.size_bytes,
      content_hash=validated.content_hash,
      status=BOOK_STATUS_UPLOADED,
    )
    db.session.add(book)
    db.session.flush()
    return book

  @classmethod
  def extract_document(cls, book_id: int, user_id: int | None = None) -> Book:
    """Run text extraction for a stored book and update DB fields."""
    query = Book.query.filter_by(id=book_id)
    if user_id is not None:
      query = query.filter_by(user_id=user_id)
    book = query.first()
    if not book:
      raise LookupError("Book not found.")

    if not book.file_path or not os.path.isfile(book.file_path):
      book.status = BOOK_STATUS_FAILED
      book.error_message = "Stored file is missing from disk."
      db.session.commit()
      raise FileNotFoundError(book.error_message)

    book.status = BOOK_STATUS_PROCESSING
    book.error_message = None
    book.updated_at = utc_now()
    db.session.commit()

    extraction = DocumentExtractor.extract(book.file_path, book.file_type)
    if not extraction.success:
      book.status = BOOK_STATUS_FAILED
      book.error_message = extraction.message
      book.extraction_method = extraction.method
      book.updated_at = utc_now()
      db.session.commit()
      raise RuntimeError(extraction.message)

    book.extracted_text = extraction.text
    book.extraction_method = extraction.method
    book.page_count = extraction.page_count
    book.char_count = extraction.char_count
    book.word_count = extraction.word_count
    book.ocr_confidence = extraction.confidence
    book.structure_json = extraction.structure_dict()
    book.status = BOOK_STATUS_EXTRACTED
    book.error_message = None
    book.updated_at = utc_now()
    db.session.commit()
    return book

  @classmethod
  def upload_and_extract(
    cls,
    user_id: int,
    files: list[FileStorage],
    title: str | None = None,
  ) -> dict:
    """Convenience: upload then extract each file (Module 1 pipeline)."""
    upload = cls.upload_documents(user_id, files, title=title)
    if not upload.success:
      return {"upload": upload.to_dict(), "extractions": []}

    extractions = []
    for item in upload.books:
      try:
        book = cls.extract_document(item.book_id, user_id=user_id)
        extractions.append(
          {
            "book_id": book.id,
            "success": True,
            "status": book.status,
            "extraction_method": book.extraction_method,
            "page_count": book.page_count,
            "char_count": book.char_count,
            "word_count": book.word_count,
            "ocr_confidence": book.ocr_confidence,
            "structure": book.structure_json,
            "text_preview": (book.extracted_text or "")[:500],
          }
        )
      except Exception as exc:
        extractions.append(
          {
            "book_id": item.book_id,
            "success": False,
            "status": BOOK_STATUS_FAILED,
            "error": str(exc),
          }
        )

    return {"upload": upload.to_dict(), "extractions": extractions}

  @staticmethod
  def get_book(book_id: int, user_id: int | None = None) -> Book | None:
    query = Book.query.filter_by(id=book_id)
    if user_id is not None:
      query = query.filter_by(user_id=user_id)
    return query.first()

  @staticmethod
  def list_books(user_id: int) -> list[Book]:
    return Book.query.filter_by(user_id=user_id).order_by(Book.created_at.desc()).all()

  @classmethod
  def delete_book(cls, book_id: int, user_id: int) -> bool:
    book = cls.get_book(book_id, user_id=user_id)
    if not book:
      return False
    path = book.file_path
    db.session.delete(book)
    db.session.commit()
    if path and os.path.isfile(path):
      try:
        os.remove(path)
      except OSError:
        logger.warning("Could not delete book file %s", path)
    return True

  @staticmethod
  def _title_from_filename(filename: str) -> str:
    base = filename.rsplit(".", 1)[0] if "." in filename else filename
    cleaned = base.replace("_", " ").replace("-", " ").strip()
    return cleaned[:300] or "Untitled Medical Document"
