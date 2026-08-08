from app.extensions import db
from app.utils import utc_now


class Quiz(db.Model):
  """Quiz for assessing medical knowledge (standalone or linked to course/lesson)."""

  __tablename__ = "quizzes"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  title = db.Column(db.String(200), nullable=False)
  description = db.Column(db.Text, nullable=True)
  difficulty = db.Column(db.String(20), default="medium")
  speciality = db.Column(db.String(100), nullable=True)
  time_limit_minutes = db.Column(db.Integer, default=30)
  is_published = db.Column(db.Boolean, default=True)
  quiz_type = db.Column(db.String(40), default="general")  # general | lesson | final_assessment
  course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
  lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)
  passing_score = db.Column(db.Float, default=70)
  created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  created_at = db.Column(db.DateTime, default=utc_now)
  updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

  creator = db.relationship("User", back_populates="quizzes_created")
  course = db.relationship("Course", back_populates="quizzes")
  lesson = db.relationship("Lesson", back_populates="quizzes")
  questions = db.relationship("Question", back_populates="quiz", lazy="dynamic", cascade="all, delete-orphan")
  results = db.relationship("Result", back_populates="quiz", lazy="dynamic", cascade="all, delete-orphan")

  def to_dict(self, include_questions=False):
    data = {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "difficulty": self.difficulty,
      "speciality": self.speciality,
      "time_limit_minutes": self.time_limit_minutes,
      "is_published": self.is_published,
      "quiz_type": self.quiz_type or "general",
      "course_id": self.course_id,
      "lesson_id": self.lesson_id,
      "passing_score": self.passing_score if self.passing_score is not None else 70,
      "question_count": self.questions.count(),
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
    if include_questions:
      data["questions"] = [q.to_dict(include_answer=False) for q in self.questions.order_by(Question.order_index)]
    return data


class Question(db.Model):
  """Individual quiz question."""

  __tablename__ = "questions"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)
  question_text = db.Column(db.Text, nullable=False)
  question_type = db.Column(db.String(40), default="multiple_choice")
  # multiple_choice | true_false | image_based | case_based
  options = db.Column(db.JSON, nullable=False)  # list of option strings (legacy + primary)
  correct_answer = db.Column(db.String(500), nullable=False)
  explanation = db.Column(db.Text, nullable=True)
  image_url = db.Column(db.String(500), nullable=True)
  points = db.Column(db.Integer, default=1)
  order_index = db.Column(db.Integer, default=0)
  created_at = db.Column(db.DateTime, default=utc_now)

  quiz = db.relationship("Quiz", back_populates="questions")
  answer_choices = db.relationship(
    "QuizAnswer",
    back_populates="question",
    lazy="dynamic",
    cascade="all, delete-orphan",
  )

  def to_dict(self, include_answer=False):
    data = {
      "id": self.id,
      "quiz_id": self.quiz_id,
      "question_text": self.question_text,
      "question_type": self.question_type or "multiple_choice",
      "options": self.options or [],
      "image_url": self.image_url,
      "points": self.points,
      "order_index": self.order_index or 0,
      "explanation": self.explanation if include_answer else None,
      "created_at": self.created_at.isoformat() if self.created_at else None,
    }
    if include_answer:
      data["correct_answer"] = self.correct_answer
      data["answer_choices"] = [a.to_dict() for a in self.answer_choices.order_by(QuizAnswer.order_index)]
    return data


class QuizAnswer(db.Model):
  """Normalized answer choice for a quiz question (optional; options JSON still supported)."""

  __tablename__ = "quiz_answers"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False, index=True)
  answer_text = db.Column(db.String(500), nullable=False)
  is_correct = db.Column(db.Boolean, default=False)
  order_index = db.Column(db.Integer, default=0)
  created_at = db.Column(db.DateTime, default=utc_now)

  question = db.relationship("Question", back_populates="answer_choices")

  def to_dict(self):
    return {
      "id": self.id,
      "question_id": self.question_id,
      "answer_text": self.answer_text,
      "is_correct": self.is_correct,
      "order_index": self.order_index,
    }


class Result(db.Model):
  """Quiz attempt result for a user."""

  __tablename__ = "results"

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)
  score = db.Column(db.Float, nullable=False, default=0)
  total_questions = db.Column(db.Integer, default=0)
  correct_answers = db.Column(db.Integer, default=0)
  answers = db.Column(db.JSON, nullable=True)  # {question_id: selected_answer}
  passed = db.Column(db.Boolean, nullable=True)
  attempt_number = db.Column(db.Integer, default=1)
  completed_at = db.Column(db.DateTime, default=utc_now)

  user = db.relationship("User", back_populates="quiz_results")
  quiz = db.relationship("Quiz", back_populates="results")

  def to_dict(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "quiz_id": self.quiz_id,
      "score": self.score,
      "total_questions": self.total_questions,
      "correct_answers": self.correct_answers,
      "answers": self.answers or {},
      "passed": self.passed,
      "attempt_number": self.attempt_number or 1,
      "quiz": self.quiz.to_dict() if self.quiz else None,
      "completed_at": self.completed_at.isoformat() if self.completed_at else None,
    }
