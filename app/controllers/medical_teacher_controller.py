"""HTTP controllers for AI Medical Teacher — Modules 1–2."""

from flask import current_app, request
from flask_jwt_extended import current_user

from app.helpers.response import error_response, success_response
from app.models.book_model import Chapter
from app.services.medical_teacher.book_parser import BookParser
from app.services.medical_teacher.document_service import DocumentService


def _collect_upload_files():
  files = []
  if "files" in request.files:
    files.extend(request.files.getlist("files"))
  if "files[]" in request.files:
    files.extend(request.files.getlist("files[]"))
  if "file" in request.files:
    files.append(request.files.get("file"))
  seen = set()
  unique = []
  for f in files:
    key = id(f)
    if key in seen:
      continue
    seen.add(key)
    unique.append(f)
  return unique


def upload_books():
  """Upload medical documents without extraction."""
  files = _collect_upload_files()
  title = request.form.get("title")
  result = DocumentService.upload_documents(current_user.id, files, title=title)
  if not result.success:
    return error_response(
      "Document upload validation failed.",
      400,
      {"errors": result.errors, **result.to_dict()},
    )
  return success_response("Documents uploaded.", result.to_dict(), 201)


def upload_and_extract():
  """Module 1 pipeline: upload → validate → extract → store."""
  files = _collect_upload_files()
  title = request.form.get("title")
  payload = DocumentService.upload_and_extract(current_user.id, files, title=title)
  upload = payload.get("upload") or {}
  if not upload.get("success"):
    return error_response(
      "Document upload validation failed.",
      400,
      {"errors": upload.get("errors", []), **payload},
    )

  extractions = payload.get("extractions") or []
  any_ok = any(e.get("success") for e in extractions)
  status_code = 201 if any_ok else 422
  message = (
    "Documents uploaded and text extracted."
    if any_ok
    else "Documents uploaded but text extraction failed."
  )
  return success_response(message, payload, status_code)


def extract_book(book_id: int):
  """Extract text from an already uploaded book."""
  try:
    book = DocumentService.extract_document(book_id, user_id=current_user.id)
  except LookupError:
    return error_response("Book not found.", 404)
  except FileNotFoundError as exc:
    return error_response(str(exc), 404)
  except RuntimeError as exc:
    failed = DocumentService.get_book(book_id, user_id=current_user.id)
    return error_response(
      str(exc),
      422,
      {"book": failed.to_dict() if failed else None},
    )

  return success_response(
    "Document text extracted.",
    {
      "book": book.to_dict(include_structure=True),
      "text_preview": (book.extracted_text or "")[:1000],
    },
  )


def parse_book(book_id: int):
  """Module 2: split chapters and analyze medical content."""
  use_ai_raw = request.args.get("use_ai")
  if use_ai_raw is None and request.is_json:
    use_ai_raw = (request.get_json(silent=True) or {}).get("use_ai")
  if use_ai_raw is None:
    use_ai = bool(current_app.config.get("TEACHER_USE_AI", True))
  else:
    use_ai = str(use_ai_raw).lower() in ("1", "true", "yes")

  result = BookParser.parse_book(book_id, user_id=current_user.id, use_ai=use_ai)
  if not result.success:
    status = 404 if result.error_code == "not_found" else 422
    return error_response(result.message, status, result.to_dict())
  return success_response(result.message, result.to_dict())


def list_chapters(book_id: int):
  book = DocumentService.get_book(book_id, user_id=current_user.id)
  if not book:
    return error_response("Book not found.", 404)
  chapters = Chapter.query.filter_by(book_id=book.id).order_by(Chapter.order_index).all()
  return success_response(
    "Chapters retrieved.",
    {
      "book_id": book.id,
      "chapters": [c.to_dict() for c in chapters],
      "total": len(chapters),
      "analysis": book.analysis_json,
      "parse_method": book.parse_method,
    },
  )


def get_chapter(book_id: int, chapter_id: int):
  book = DocumentService.get_book(book_id, user_id=current_user.id)
  if not book:
    return error_response("Book not found.", 404)
  chapter = Chapter.query.filter_by(id=chapter_id, book_id=book.id).first()
  if not chapter:
    return error_response("Chapter not found.", 404)
  include_content = (request.args.get("include_content") or "true").lower() in ("1", "true", "yes")
  return success_response(
    "Chapter retrieved.",
    {"chapter": chapter.to_dict(include_content=include_content)},
  )


def list_books():
  books = DocumentService.list_books(current_user.id)
  return success_response(
    "Books retrieved.",
    {"books": [b.to_dict() for b in books], "total": len(books)},
  )


def get_book(book_id: int):
  include_text = (request.args.get("include_text") or "").lower() in ("1", "true", "yes")
  include_structure = (request.args.get("include_structure") or "true").lower() in ("1", "true", "yes")
  include_analysis = (request.args.get("include_analysis") or "true").lower() in ("1", "true", "yes")
  include_chapters = (request.args.get("include_chapters") or "true").lower() in ("1", "true", "yes")
  book = DocumentService.get_book(book_id, user_id=current_user.id)
  if not book:
    return error_response("Book not found.", 404)
  return success_response(
    "Book retrieved.",
    {
      "book": book.to_dict(
        include_text=include_text,
        include_structure=include_structure,
        include_analysis=include_analysis,
        include_chapters=include_chapters,
      )
    },
  )


def delete_book(book_id: int):
  deleted = DocumentService.delete_book(book_id, current_user.id)
  if not deleted:
    return error_response("Book not found.", 404)
  return success_response("Book deleted.")
