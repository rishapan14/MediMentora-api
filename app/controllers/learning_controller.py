from flask import request
from flask_jwt_extended import current_user

from app.extensions import db
from app.helpers.response import error_response, success_response
from app.models.course_model import CompletedLesson, Course, Lesson, LessonBookmark
from app.models.recommendation_model import Recommendation
from app.services.learning_service import LearningService
from app.validations.learning_validation import validate_course, validate_lesson


# --- Courses ---

def list_courses():
  speciality = request.args.get("speciality")
  difficulty = request.args.get("difficulty")
  query = Course.query.filter_by(is_published=True)
  if speciality:
    query = query.filter_by(speciality=speciality)
  if difficulty:
    query = query.filter_by(difficulty=difficulty)
  courses = query.order_by(Course.created_at.desc()).all()
  return success_response("Courses retrieved.", {"courses": [c.to_dict() for c in courses]})


def get_course(course_id):
  course = Course.query.get(course_id)
  if not course:
    return error_response("Course not found.", 404)
  return success_response("Course retrieved.", {"course": course.to_dict(include_lessons=True)})


def create_course():
  data = request.get_json(silent=True)
  errors = validate_course(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  course = Course(
    title=data["title"],
    description=data.get("description"),
    speciality=data.get("speciality"),
    difficulty=data.get("difficulty", "medium"),
    duration_hours=data.get("duration_hours", 0),
    is_published=data.get("is_published", True),
  )
  db.session.add(course)
  db.session.commit()
  return success_response("Course created.", {"course": course.to_dict()}, 201)


def update_course(course_id):
  course = Course.query.get(course_id)
  if not course:
    return error_response("Course not found.", 404)

  data = request.get_json(silent=True) or {}
  errors = validate_course(data, partial=True)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  for field in ("title", "description", "speciality", "difficulty", "duration_hours", "is_published"):
    if field in data:
      setattr(course, field, data[field])
  db.session.commit()
  return success_response("Course updated.", {"course": course.to_dict()})


def delete_course(course_id):
  course = Course.query.get(course_id)
  if not course:
    return error_response("Course not found.", 404)
  db.session.delete(course)
  db.session.commit()
  return success_response("Course deleted.")


# --- Lessons ---

def list_lessons(course_id):
  lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
  return success_response("Lessons retrieved.", {"lessons": [l.to_dict() for l in lessons]})


def create_lesson():
  data = request.get_json(silent=True)
  errors = validate_lesson(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  if not Course.query.get(data["course_id"]):
    return error_response("Course not found.", 404)

  lesson = Lesson(
    course_id=data["course_id"],
    title=data["title"],
    content=data.get("content"),
    order_index=data.get("order_index", 0),
    duration_minutes=data.get("duration_minutes", 15),
    topic_tags=data.get("topic_tags"),
  )
  db.session.add(lesson)
  db.session.commit()
  return success_response("Lesson created.", {"lesson": lesson.to_dict()}, 201)


def update_lesson(lesson_id):
  lesson = Lesson.query.get(lesson_id)
  if not lesson:
    return error_response("Lesson not found.", 404)

  data = request.get_json(silent=True) or {}
  for field in ("title", "content", "order_index", "duration_minutes", "topic_tags", "course_id"):
    if field in data:
      setattr(lesson, field, data[field])
  db.session.commit()
  return success_response("Lesson updated.", {"lesson": lesson.to_dict()})


def delete_lesson(lesson_id):
  lesson = Lesson.query.get(lesson_id)
  if not lesson:
    return error_response("Lesson not found.", 404)
  db.session.delete(lesson)
  db.session.commit()
  return success_response("Lesson deleted.")


# --- Bookmarks ---

def add_bookmark(lesson_id):
  if not Lesson.query.get(lesson_id):
    return error_response("Lesson not found.", 404)

  existing = LessonBookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
  if existing:
    return success_response("Already bookmarked.", {"bookmark": existing.to_dict()})

  bookmark = LessonBookmark(user_id=current_user.id, lesson_id=lesson_id)
  db.session.add(bookmark)
  db.session.commit()
  return success_response("Lesson bookmarked.", {"bookmark": bookmark.to_dict()}, 201)


def remove_bookmark(lesson_id):
  bookmark = LessonBookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
  if not bookmark:
    return error_response("Bookmark not found.", 404)
  db.session.delete(bookmark)
  db.session.commit()
  return success_response("Bookmark removed.")


def list_bookmarks():
  bookmarks = LessonBookmark.query.filter_by(user_id=current_user.id).all()
  return success_response("Bookmarks retrieved.", {"bookmarks": [b.to_dict() for b in bookmarks]})


# --- Completed lessons ---

def complete_lesson(lesson_id):
  lesson = Lesson.query.get(lesson_id)
  if not lesson:
    return error_response("Lesson not found.", 404)

  existing = CompletedLesson.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
  if not existing:
    record = CompletedLesson(user_id=current_user.id, lesson_id=lesson_id)
    db.session.add(record)
    db.session.commit()

  progress = LearningService.update_learning_progress(current_user.id)
  return success_response("Lesson marked complete.", {"progress": progress.to_dict()})


def list_completed_lessons():
  records = CompletedLesson.query.filter_by(user_id=current_user.id).all()
  return success_response("Completed lessons retrieved.", {
    "completed_lessons": [r.to_dict() for r in records],
  })


# --- Recommendations ---

def list_recommendations():
  newly_created = LearningService.generate_recommendations(current_user.id)
  all_recs = Recommendation.query.filter_by(user_id=current_user.id).order_by(
    Recommendation.created_at.desc()
  ).all()
  return success_response("Recommendations retrieved.", {
    "recommendations": [r.to_dict() for r in all_recs],
    "newly_created": len(newly_created),
  })


def weak_topics():
  topics = LearningService.detect_weak_topics(current_user.id)
  return success_response("Weak topics detected.", {"weak_topics": topics})
