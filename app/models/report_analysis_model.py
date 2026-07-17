from app.extensions import db
from app.utils import utc_now


class ReportAnalysis(db.Model):
  """AI-generated analysis of a medical report."""

  __tablename__ = "report_analysis"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=True, index=True)
  report_text = db.Column(db.Text, nullable=True)
  simple_explanation = db.Column(db.Text, nullable=True)
  abnormal_values = db.Column(db.JSON, nullable=True)
  possible_diseases = db.Column(db.JSON, nullable=True)
  medical_terms = db.Column(db.JSON, nullable=True)
  learning_topics = db.Column(db.JSON, nullable=True)
  full_response = db.Column(db.JSON, nullable=True)
  created_at = db.Column(db.DateTime, default=utc_now)

  user = db.relationship("User", back_populates="report_analyses")
  report = db.relationship("Report", back_populates="analyses")

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "report_id": self.report_id,
      "report_text": self.report_text,
      "simple_explanation": self.simple_explanation,
      "abnormal_values": self.abnormal_values,
      "possible_diseases": self.possible_diseases,
      "medical_terms": self.medical_terms,
      "learning_topics": self.learning_topics,
      "full_response": self.full_response,
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }
