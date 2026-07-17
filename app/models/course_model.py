from app.extensions import db
from app.utils import utc_now


class Course(db.Model):
  """Learning course for nursing and medical education."""

  __tablename__ = "courses"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  title = db.Column(db.String(200), nullable=False)
  description = db.Column(db.Text, nullable=True)
  speciality = db.Column(db.String(100), nullable=True)
  difficulty = db.Column(db.String(20), default="medium")
  duration_hours = db.Column(db.Float, default=0)
  is_published = db.Column(db.Boolean, default=True)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  lessons = db.relationship("Lesson", back_populates="course", lazy="dynamic", cascade="all, delete-orphan")
  recommendations = db.relationship("Recommendation", back_populates="course", lazy="dynamic")
  certificates = db.relationship("Certificate", back_populates="course", lazy="dynamic")

  def to_dict(self, include_lessons=False):
    data = {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "speciality": self.speciality,
      "difficulty": self.difficulty,
      "duration_hours": self.duration_hours,
      "is_published": self.is_published,
      "lesson_count": self.lessons.count(),
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
    if include_lessons:
      data["lessons"] = [lesson.to_dict() for lesson in self.lessons.order_by(Lesson.order_index)]
    return data


class Lesson(db.Model):
  """Individual lesson within a course."""

  __tablename__ = "lessons"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
  title = db.Column(db.String(200), nullable=False)
  content = db.Column(db.Text, nullable=True)
  order_index = db.Column(db.Integer, default=0)
  duration_minutes = db.Column(db.Integer, default=15)
  topic_tags = db.Column(db.JSON, nullable=True)
  created_at = db.Column(db.DateTime, default=utc_now)

  course = db.relationship("Course", back_populates="lessons")
  bookmarks = db.relationship("LessonBookmark", back_populates="lesson", lazy="dynamic", cascade="all, delete-orphan")
  completions = db.relationship("CompletedLesson", back_populates="lesson", lazy="dynamic", cascade="all, delete-orphan")

  def to_dict(self):
    return {
      "id": self.id,
      "course_id": self.course_id,
      "title": self.title,
      "content": self.content,
      "order_index": self.order_index,
      "duration_minutes": self.duration_minutes,
      "topic_tags": self.topic_tags,
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }


class LessonBookmark(db.Model):
  """User bookmark for a lesson."""

  __tablename__ = "lesson_bookmarks"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False, index=True)
  created_at = db.Column(db.DateTime, default=utc_now)

  user = db.relationship("User", back_populates="bookmarks")
  lesson = db.relationship("Lesson", back_populates="bookmarks")

  __table_args__ = (db.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_bookmark"),)

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "lesson_id": self.lesson_id,
      "lesson": self.lesson.to_dict() if self.lesson else None,
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }


class CompletedLesson(db.Model):
  """Tracks lessons completed by a user."""

  __tablename__ = "completed_lessons"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False, index=True)
  completed_at = db.Column(db.DateTime, default=utc_now)

  user = db.relationship("User", back_populates="completed_lessons")
  lesson = db.relationship("Lesson", back_populates="completions")

  __table_args__ = (db.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_completed"),)

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "lesson_id": self.lesson_id,
      "lesson": self.lesson.to_dict() if self.lesson else None,
      "completed_at": self.completed_at.isoformat() if self.completed_at else None,
    }
