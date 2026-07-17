"""Import all models so SQLAlchemy registers them with the metadata."""

from app.models.user_model import User
from app.models.report_model import Report
from app.models.report_analysis_model import ReportAnalysis
from app.models.course_model import Course, Lesson, LessonBookmark, CompletedLesson
from app.models.recommendation_model import Recommendation
from app.models.progress_model import Progress
from app.models.clinical_case_model import ClinicalCase, CaseFavorite
from app.models.simulation_model import Simulation, SimulationAttempt
from app.models.quiz_model import Quiz, Question, Result
from app.models.certificate_model import Certificate
from app.models.discussion_model import Discussion, Comment, DiscussionLike, CommentLike
from app.models.notification_model import Notification

__all__ = [
  "User",
  "Report",
  "ReportAnalysis",
  "Course",
  "Lesson",
  "LessonBookmark",
  "CompletedLesson",
  "Recommendation",
  "Progress",
  "ClinicalCase",
  "CaseFavorite",
  "Simulation",
  "SimulationAttempt",
  "Quiz",
  "Question",
  "Result",
  "Certificate",
  "Discussion",
  "Comment",
  "DiscussionLike",
  "CommentLike",
  "Notification",
]
