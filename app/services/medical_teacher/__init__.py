"""AI Medical Teacher package — document processing, book parsing, later teaching modules."""

from app.services.medical_teacher.book_parser import BookParser
from app.services.medical_teacher.document_service import DocumentService

__all__ = ["DocumentService", "BookParser"]
