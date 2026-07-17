"""Learning progress, weak topics, and recommendations."""

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.course_model import CompletedLesson, Course, Lesson
from app.models.progress_model import Progress
from app.models.quiz_model import Result
from app.models.recommendation_model import Recommendation


class LearningService:
  @staticmethod
  def get_or_create_progress(user_id):
    progress = Progress.query.filter_by(user_id=user_id).first()
    if progress:
      return progress

    progress = Progress(user_id=user_id)
    db.session.add(progress)
    try:
      db.session.commit()
    except IntegrityError:
      db.session.rollback()
      progress = Progress.query.filter_by(user_id=user_id).first()
      if not progress:
        raise
    return progress

  @staticmethod
  def update_learning_progress(user_id):
    progress = LearningService.get_or_create_progress(user_id)
    total_lessons = Lesson.query.count()
    completed = CompletedLesson.query.filter_by(user_id=user_id).count()

    if total_lessons > 0:
      progress.learning_progress = round((completed / total_lessons) * 100, 2)
    else:
      progress.learning_progress = 0.0

    db.session.commit()
    return progress

  @staticmethod
  def detect_weak_topics(user_id):
    """Identify weak topics from low quiz scores."""
    results = Result.query.filter_by(user_id=user_id).order_by(Result.completed_at.desc()).limit(20).all()
    weak = []
    for result in results:
      if result.score < 60 and result.quiz:
        weak.append({
          "quiz_id": result.quiz_id,
          "quiz_title": result.quiz.title,
          "score": result.score,
          "speciality": result.quiz.speciality,
        })

    progress = LearningService.get_or_create_progress(user_id)
    progress.weak_topics = weak
    db.session.commit()
    return weak

  @staticmethod
  def generate_recommendations(user_id):
    """Create course recommendations based on weak topics."""
    weak_topics = LearningService.detect_weak_topics(user_id)
    created = []

    for item in weak_topics[:5]:
      speciality = item.get("speciality")
      course = None
      if speciality:
        course = Course.query.filter_by(speciality=speciality, is_published=True).first()
      if not course:
        course = Course.query.filter_by(is_published=True).first()
      if not course:
        continue

      existing = Recommendation.query.filter_by(
        user_id=user_id, course_id=course.id, weak_topic=item.get("quiz_title")
      ).first()
      if existing:
        continue

      rec = Recommendation(
        user_id=user_id,
        course_id=course.id,
        weak_topic=item.get("quiz_title"),
        reason=f"Low quiz score ({item.get('score')}%). Review {course.title}.",
        priority=1,
      )
      db.session.add(rec)
      created.append(rec)

    db.session.commit()
    return created

  @staticmethod
  def record_quiz_score(user_id, quiz_id, score):
    progress = LearningService.get_or_create_progress(user_id)
    scores = progress.quiz_scores or {}
    scores[str(quiz_id)] = score
    progress.quiz_scores = scores

    achievements = progress.achievements or []
    if score >= 90 and "quiz_master" not in achievements:
      achievements.append("quiz_master")
    if score == 100 and "perfect_score" not in achievements:
      achievements.append("perfect_score")
    progress.achievements = achievements

    db.session.commit()
    return progress

  @staticmethod
  def record_simulation_score(user_id, simulation_id, score):
    progress = LearningService.get_or_create_progress(user_id)
    scores = progress.simulation_scores or {}
    scores[str(simulation_id)] = score
    progress.simulation_scores = scores

    achievements = progress.achievements or []
    if score >= 80 and "simulation_expert" not in achievements:
      achievements.append("simulation_expert")
    progress.achievements = achievements

    db.session.commit()
    return progress
