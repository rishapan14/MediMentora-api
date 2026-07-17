import os

from flask import current_app, request, send_file
from flask_jwt_extended import current_user

from app.constants import REPORT_TYPE_IMAGE, REPORT_TYPE_PDF
from app.extensions import db
from app.helpers.response import error_response, success_response
from app.models.report_model import Report
from app.services.report_extraction_service import ReportExtractionService
from app.utils import save_upload_file
from app.validations.report_validation import validate_save_report


PDF_EXTENSIONS = {"pdf"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"}


def upload_pdf():
  file = request.files.get("file")
  title = request.form.get("title", "Medical Report")

  file_path = save_upload_file(file, current_app.config["REPORT_UPLOAD_FOLDER"], PDF_EXTENSIONS)
  if not file_path:
    return error_response("Valid PDF file is required.", 400)

  report = Report(
    user_id=current_user.id,
    title=title,
    file_path=file_path,
    file_type=REPORT_TYPE_PDF,
    status="uploaded",
  )
  db.session.add(report)
  db.session.commit()
  return success_response("PDF uploaded successfully.", {"report": report.to_dict()}, 201)


def upload_image():
  file = request.files.get("file")
  title = request.form.get("title", "Medical Report Image")

  file_path = save_upload_file(file, current_app.config["REPORT_UPLOAD_FOLDER"], IMAGE_EXTENSIONS)
  if not file_path:
    return error_response("Valid image file is required.", 400)

  report = Report(
    user_id=current_user.id,
    title=title,
    file_path=file_path,
    file_type=REPORT_TYPE_IMAGE,
    status="uploaded",
  )
  db.session.add(report)
  db.session.commit()
  return success_response("Image uploaded successfully.", {"report": report.to_dict()}, 201)


def save_report():
  data = request.get_json(silent=True)
  errors = validate_save_report(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  report = Report(
    user_id=current_user.id,
    title=data["title"],
    file_path=data.get("file_path"),
    file_type=data.get("file_type", REPORT_TYPE_PDF),
    extracted_text=data.get("extracted_text"),
    status=data.get("status", "uploaded"),
  )
  db.session.add(report)
  db.session.commit()
  return success_response("Report saved.", {"report": report.to_dict()}, 201)


def extract_text(report_id):
  report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
  if not report:
    return error_response("Report not found.", 404)
  if not report.file_path:
    return error_response("Report has no file to extract text from.", 400)

  try:
    text = ReportExtractionService.extract_text(report.file_path, report.file_type)
    report.extracted_text = text
    report.status = "processed"
    db.session.commit()
    return success_response("Text extracted successfully.", {"report": report.to_dict()})
  except Exception as exc:
    report.status = "failed"
    db.session.commit()
    return error_response(f"Text extraction failed: {exc}", 500)


def list_reports():
  reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
  return success_response("Reports retrieved.", {"reports": [r.to_dict() for r in reports]})


def get_report(report_id):
  report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
  if not report:
    return error_response("Report not found.", 404)
  return success_response("Report retrieved.", {"report": report.to_dict()})


def delete_report(report_id):
  report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
  if not report:
    return error_response("Report not found.", 404)

  if report.file_path and os.path.exists(report.file_path):
    try:
      os.remove(report.file_path)
    except OSError:
      pass

  db.session.delete(report)
  db.session.commit()
  return success_response("Report deleted.")


def report_history():
  reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
  return success_response("Report history retrieved.", {
    "history": [r.to_dict() for r in reports],
    "total": len(reports),
  })
