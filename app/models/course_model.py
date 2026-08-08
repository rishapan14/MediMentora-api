"""Learning / LMS models — courses, modules, lessons, media, progress, reviews."""

from __future__ import annotations

from app.extensions import db
from app.utils import utc_now


class CourseCategory(db.Model):
  """Medical learning category (Anatomy, Cardiology, Nursing, etc.)."""

  __tablename__ = "course_categories"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String(120), nullable=False, unique=True, index=True)
  slug = db.Column(db.String(140), nullable=False, unique=True, index=True)
  description = db.Column(db.Text, nullable=True)
  icon = db.Column(db.String(80), nullable=True)
  sort_order = db.Column(db.Integer, default=0)
  is_active = db.Column(db.Boolean, default=True)
  created_at = db.Column(db.DateTime, default=utc_now)

  courses = db.relationship("Course", back_populates="category", lazy="dynamic")

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "slug": self.slug,
      "description": self.description,
      "icon": self.icon,
      "sort_order": self.sort_order,
      "is_active": self.is_active,
      "course_count": self.courses.filter(
        db.or_(Course.is_published.is_(True), Course.is_published.is_(None))
      ).count(),
    }


class Course(db.Model):
  """Learning course for nursing and medical education."""

  __tablename__ = "courses"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  title = db.Column(db.String(200), nullable=False)
  description = db.Column(db.Text, nullable=True)
  speciality = db.Column(db.String(100), nullable=True)  # legacy free-text; prefer category_id
  category_id = db.Column(db.Integer, db.ForeignKey("course_categories.id"), nullable=True, index=True)
  difficulty = db.Column(db.String(20), default="medium")  # beginner|intermediate|advanced mapped later
  duration_hours = db.Column(db.Float, default=0)
  instructor_name = db.Column(db.String(150), nullable=True)
  instructor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  thumbnail_url = db.Column(db.String(500), nullable=True)
  banner_url = db.Column(db.String(500), nullable=True)
  learning_objectives = db.Column(db.JSON, nullable=True)  # list[str]
  prerequisites = db.Column(db.JSON, nullable=True)  # list[str]
  rating_avg = db.Column(db.Float, default=0)
  rating_count = db.Column(db.Integer, default=0)
  enrollment_count = db.Column(db.Integer, default=0)
  certificate_eligible = db.Column(db.Boolean, default=True)
  is_published = db.Column(db.Boolean, default=True)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  category = db.relationship("CourseCategory", back_populates="courses")
  instructor = db.relationship("User", foreign_keys=[instructor_id])
  modules = db.relationship(
    "CourseModule",
    back_populates="course",
    lazy="dynamic",
    cascade="all, delete-orphan",
    order_by="CourseModule.order_index",
  )
  lessons = db.relationship("Lesson", back_populates="course", lazy="dynamic", cascade="all, delete-orphan")
  recommendations = db.relationship("Recommendation", back_populates="course", lazy="dynamic")
  certificates = db.relationship("Certificate", back_populates="course", lazy="dynamic")
  progress_records = db.relationship("CourseProgress", back_populates="course", lazy="dynamic", cascade="all, delete-orphan")
  reviews = db.relationship("CourseReview", back_populates="course", lazy="dynamic", cascade="all, delete-orphan")
  bookmarks = db.relationship("CourseBookmark", back_populates="course", lazy="dynamic", cascade="all, delete-orphan")
  quizzes = db.relationship("Quiz", back_populates="course", lazy="dynamic")

  def to_dict(self, include_lessons=False, include_modules=False):
    data = {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "speciality": self.speciality,
      "category_id": self.category_id,
      "category": self.category.name if self.category else self.speciality,
      "difficulty": self.difficulty,
      "duration_hours": self.duration_hours,
      "instructor_name": self.instructor_name,
      "instructor_id": self.instructor_id,
      "thumbnail_url": self.thumbnail_url,
      "banner_url": self.banner_url,
      "learning_objectives": self.learning_objectives or [],
      "prerequisites": self.prerequisites or [],
      "rating_avg": self.rating_avg or 0,
      "rating_count": self.rating_count or 0,
      "enrollment_count": self.enrollment_count or 0,
      "certificate_eligible": True if self.certificate_eligible is None else bool(self.certificate_eligible),
      "is_published": True if self.is_published is None else bool(self.is_published),
      "lesson_count": self.lessons.count(),
      "module_count": self.modules.count() if self.modules else 0,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
    if include_lessons:
      data["lessons"] = [lesson.to_dict() for lesson in self.lessons.order_by(Lesson.order_index)]
    if include_modules:
      data["modules"] = [m.to_dict(include_lessons=True) for m in self.modules.order_by(CourseModule.order_index)]
    return data


class CourseModule(db.Model):
  """Ordered module grouping lessons within a course."""

  __tablename__ = "course_modules"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
  title = db.Column(db.String(200), nullable=False)
  description = db.Column(db.Text, nullable=True)
  order_index = db.Column(db.Integer, default=0)
  created_at = db.Column(db.DateTime, default=utc_now)

  course = db.relationship("Course", back_populates="modules")
  lessons = db.relationship(
    "Lesson",
    back_populates="module",
    lazy="dynamic",
    foreign_keys="Lesson.module_id",
  )

  def to_dict(self, include_lessons=False):
    data = {
      "id": self.id,
      "course_id": self.course_id,
      "title": self.title,
      "description": self.description,
      "order_index": self.order_index,
      "lesson_count": self.lessons.count(),
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }
    if include_lessons:
      data["lessons"] = [l.to_dict() for l in self.lessons.order_by(Lesson.order_index)]
    return data


class Lesson(db.Model):
  """Individual lesson within a course (optionally under a module)."""

  __tablename__ = "lessons"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
  module_id = db.Column(db.Integer, db.ForeignKey("course_modules.id"), nullable=True, index=True)
  title = db.Column(db.String(200), nullable=False)
  content = db.Column(db.Text, nullable=True)
  summary = db.Column(db.Text, nullable=True)
  order_index = db.Column(db.Integer, default=0)
  duration_minutes = db.Column(db.Integer, default=15)
  topic_tags = db.Column(db.JSON, nullable=True)
  is_published = db.Column(db.Boolean, default=True)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  course = db.relationship("Course", back_populates="lessons")
  module = db.relationship("CourseModule", back_populates="lessons")
  bookmarks = db.relationship("LessonBookmark", back_populates="lesson", lazy="dynamic", cascade="all, delete-orphan")
  completions = db.relationship("CompletedLesson", back_populates="lesson", lazy="dynamic", cascade="all, delete-orphan")
  resources = db.relationship("LessonResource", back_populates="lesson", lazy="dynamic", cascade="all, delete-orphan")
  videos = db.relationship("LessonVideo", back_populates="lesson", lazy="dynamic", cascade="all, delete-orphan")
  quizzes = db.relationship("Quiz", back_populates="lesson", lazy="dynamic")

  def to_dict(self, include_media=False):
    data = {
      "id": self.id,
      "course_id": self.course_id,
      "module_id": self.module_id,
      "title": self.title,
      "content": self.content,
      "summary": self.summary,
      "order_index": self.order_index,
      "duration_minutes": self.duration_minutes,
      "topic_tags": self.topic_tags,
      "is_published": self.is_published if self.is_published is not None else True,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
    if include_media:
      data["resources"] = [r.to_dict() for r in self.resources.order_by(LessonResource.order_index)]
      data["videos"] = [v.to_dict() for v in self.videos.order_by(LessonVideo.order_index)]
    return data


class LessonResource(db.Model):
  """Downloadable or linked lesson resource (PDF, notes, images)."""

  __tablename__ = "lesson_resources"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False, index=True)
  title = db.Column(db.String(200), nullable=False)
  resource_type = db.Column(db.String(40), default="pdf")  # pdf | image | link | notes
  file_path = db.Column(db.String(500), nullable=True)
  external_url = db.Column(db.String(500), nullable=True)
  file_size = db.Column(db.Integer, nullable=True)
  order_index = db.Column(db.Integer, default=0)
  created_at = db.Column(db.DateTime, default=utc_now)

  lesson = db.relationship("Lesson", back_populates="resources")

  def to_dict(self):
    return {
      "id": self.id,
      "lesson_id": self.lesson_id,
      "title": self.title,
      "resource_type": self.resource_type,
      "file_path": self.file_path,
      "external_url": self.external_url,
      "file_size": self.file_size,
      "order_index": self.order_index,
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }


class LessonVideo(db.Model):
  """Video asset for a lesson."""

  __tablename__ = "lesson_videos"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False, index=True)
  title = db.Column(db.String(200), nullable=False)
  video_url = db.Column(db.String(500), nullable=True)
  file_path = db.Column(db.String(500), nullable=True)
  duration_seconds = db.Column(db.Integer, nullable=True)
  thumbnail_url = db.Column(db.String(500), nullable=True)
  order_index = db.Column(db.Integer, default=0)
  created_at = db.Column(db.DateTime, default=utc_now)

  lesson = db.relationship("Lesson", back_populates="videos")

  def to_dict(self):
    return {
      "id": self.id,
      "lesson_id": self.lesson_id,
      "title": self.title,
      "video_url": self.video_url,
      "file_path": self.file_path,
      "duration_seconds": self.duration_seconds,
      "thumbnail_url": self.thumbnail_url,
      "order_index": self.order_index,
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


class CourseProgress(db.Model):
  """Per-course learning progress for a user."""

  __tablename__ = "course_progress"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
  status = db.Column(db.String(30), default="enrolled")  # enrolled | in_progress | completed
  progress_percent = db.Column(db.Float, default=0)
  lessons_completed = db.Column(db.Integer, default=0)
  lessons_total = db.Column(db.Integer, default=0)
  last_lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
  study_minutes = db.Column(db.Integer, default=0)
  enrolled_at = db.Column(db.DateTime, default=utc_now)
  completed_at = db.Column(db.DateTime, nullable=True)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  user = db.relationship("User", back_populates="course_progress")
  course = db.relationship("Course", back_populates="progress_records")
  last_lesson = db.relationship("Lesson", foreign_keys=[last_lesson_id])

  __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_user_course_progress"),)

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "course_id": self.course_id,
      "status": self.status,
      "progress_percent": self.progress_percent or 0,
      "lessons_completed": self.lessons_completed or 0,
      "lessons_total": self.lessons_total or 0,
      "last_lesson_id": self.last_lesson_id,
      "study_minutes": self.study_minutes or 0,
      "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
      "completed_at": self.completed_at.isoformat() if self.completed_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
      "course": self.course.to_dict() if self.course else None,
    }


class CourseBookmark(db.Model):
  """User bookmark for an entire course."""

  __tablename__ = "course_bookmarks"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
  created_at = db.Column(db.DateTime, default=utc_now)

  user = db.relationship("User", back_populates="course_bookmarks")
  course = db.relationship("Course", back_populates="bookmarks")

  __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_user_course_bookmark"),)

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "course_id": self.course_id,
      "course": self.course.to_dict() if self.course else None,
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }


class CourseReview(db.Model):
  """Student rating and review for a course."""

  __tablename__ = "course_reviews"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
  rating = db.Column(db.Integer, nullable=False)  # 1–5
  review_text = db.Column(db.Text, nullable=True)
  is_published = db.Column(db.Boolean, default=True)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  user = db.relationship("User", back_populates="course_reviews")
  course = db.relationship("Course", back_populates="reviews")

  __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_user_course_review"),)

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "course_id": self.course_id,
      "rating": self.rating,
      "review_text": self.review_text,
      "is_published": self.is_published,
      "reviewer_name": self.user.full_name if self.user else None,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
