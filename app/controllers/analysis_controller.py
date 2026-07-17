from flask import request
from flask_jwt_extended import current_user

from app.extensions import db
from app.helpers.response import error_response, success_response
from app.models.report_analysis_model import ReportAnalysis
from app.models.report_model import Report
from app.services.ai_analysis_service import AIAnalysisService
from app.validations.analysis_validation import validate_analysis


def analyze_report():
  data = request.get_json(silent=True)
  errors = validate_analysis(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  report_text = data.get("report_text")
  report_id = data.get("report_id")

  if report_id:
    report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
    if not report:
      return error_response("Report not found.", 404)
    report_text = report.extracted_text or report_text
    if not report_text:
      return error_response("No text available for analysis. Extract text first.", 400)

  try:
    analysis_data = AIAnalysisService.analyze_report(report_text)
  except Exception as exc:
    return error_response(f"AI analysis failed: {exc}", 500)

  record = ReportAnalysis(
    user_id=current_user.id,
    report_id=report_id,
    report_text=report_text,
    simple_explanation=analysis_data.get("simple_explanation"),
    abnormal_values=analysis_data.get("abnormal_values"),
    possible_diseases=analysis_data.get("possible_diseases"),
    medical_terms=analysis_data.get("medical_terms"),
    learning_topics=analysis_data.get("learning_topics"),
    full_response=analysis_data,
  )
  db.session.add(record)
  db.session.commit()

  return success_response("Analysis completed.", {"analysis": record.to_dict()}, 201)


def get_analysis(analysis_id):
  record = ReportAnalysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
  if not record:
    return error_response("Analysis not found.", 404)
  return success_response("Analysis retrieved.", {"analysis": record.to_dict()})


def list_analyses():
  records = ReportAnalysis.query.filter_by(user_id=current_user.id).order_by(
    ReportAnalysis.created_at.desc()
  ).all()
  return success_response("Analysis history retrieved.", {
    "analyses": [r.to_dict() for r in records],
    "total": len(records),
  })


def delete_analysis(analysis_id):
  record = ReportAnalysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
  if not record:
    return error_response("Analysis not found.", 404)
  db.session.delete(record)
  db.session.commit()
  return success_response("Analysis deleted.")
