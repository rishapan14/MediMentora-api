from app.extensions import db
from app.utils import utc_now


class Report(db.Model):
  """Uploaded medical report (PDF or image)."""

  __tablename__ = "reports"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  title = db.Column(db.String(200), nullable=False)
  file_path = db.Column(db.String(500), nullable=True)
  file_type = db.Column(db.String(20), nullable=False)  # pdf | image
  extracted_text = db.Column(db.Text, nullable=True)
  status = db.Column(db.String(30), default="uploaded")  # uploaded | processed | failed
  created_at = db.Column(db.DateTime, default=utc_now)

  user = db.relationship("User", back_populates="reports")
  analyses = db.relationship("ReportAnalysis", back_populates="report", lazy="dynamic", cascade="all, delete-orphan")

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "title": self.title,
      "file_path": self.file_path,
      "file_type": self.file_type,
      "extracted_text": self.extracted_text,
      "status": self.status,
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }
