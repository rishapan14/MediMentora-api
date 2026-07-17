"""Seed demo data for development and testing."""

from app.extensions import db
from app.models.course_model import Course, Lesson
from app.models.clinical_case_model import ClinicalCase
from app.models.quiz_model import Question, Quiz
from app.models.simulation_model import Simulation
from app.models.user_model import User
from app.constants import ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, ROLE_MEDICAL_STUDENT


def seed_all():
  if User.query.filter_by(email="admin@clinical.com").first():
    print("Seed data already exists. Skipping.")
    return

  # Users
  admin = User(email="admin@clinical.com", full_name="System Admin", role=ROLE_ADMIN)
  admin.set_password("admin123")

  doctor = User(email="doctor@clinical.com", full_name="Dr. Sarah Chen", role=ROLE_DOCTOR, speciality="Cardiology")
  doctor.set_password("doctor123")

  nurse = User(email="nurse@clinical.com", full_name="Nurse Emily", role=ROLE_NURSE, speciality="General Nursing")
  nurse.set_password("nurse123")

  student = User(email="student@clinical.com", full_name="Alex Student", role=ROLE_MEDICAL_STUDENT)
  student.set_password("student123")

  db.session.add_all([admin, doctor, nurse, student])
  db.session.flush()

  # Course & lessons
  course = Course(
    title="Fundamentals of Clinical Nursing",
    description="Core nursing concepts for beginners.",
    speciality="Nursing",
    difficulty="easy",
    duration_hours=10,
  )
  db.session.add(course)
  db.session.flush()

  lessons = [
    Lesson(course_id=course.id, title="Vital Signs Assessment", content="Learn to measure BP, pulse, respiration, temperature.", order_index=1),
    Lesson(course_id=course.id, title="CBC Interpretation", content="Understanding complete blood count results.", order_index=2),
    Lesson(course_id=course.id, title="Medication Administration", content="Safe medication practices for nurses.", order_index=3),
  ]
  db.session.add_all(lessons)

  # Clinical case
  case = ClinicalCase(
    created_by=doctor.id,
    title="Chest Pain in a 55-year-old Male",
    disease="Acute Coronary Syndrome",
    symptoms=["Chest pain", "Shortness of breath", "Diaphoresis"],
    diagnosis="STEMI suspected based on ECG changes",
    treatment="Aspirin, nitroglycerin, urgent cardiology referral",
    difficulty="medium",
    speciality="Cardiology",
    description="Patient presents with crushing chest pain radiating to left arm.",
  )
  db.session.add(case)

  # Quiz
  quiz = Quiz(
    title="Nursing Fundamentals Quiz",
    description="Test your basic nursing knowledge.",
    difficulty="easy",
    speciality="Nursing",
    created_by=doctor.id,
  )
  db.session.add(quiz)
  db.session.flush()

  questions = [
    Question(
      quiz_id=quiz.id,
      question_text="What is the normal adult resting heart rate range?",
      options=["40-60 bpm", "60-100 bpm", "100-140 bpm", "140-180 bpm"],
      correct_answer="60-100 bpm",
      explanation="Normal resting heart rate for adults is 60-100 beats per minute.",
    ),
    Question(
      quiz_id=quiz.id,
      question_text="Which vital sign is measured in mmHg?",
      options=["Temperature", "Blood Pressure", "Respiratory Rate", "Pulse"],
      correct_answer="Blood Pressure",
    ),
  ]
  db.session.add_all(questions)

  # Simulation
  sim = Simulation(
    title="Diabetic Patient with Hyperglycemia",
    scenario="A 62-year-old diabetic patient presents with polyuria, polydipsia, and blood glucose of 380 mg/dL.",
    patient_data={"age": 62, "glucose": 380, "history": "Type 2 Diabetes"},
    correct_diagnosis="Hyperglycemic crisis",
    correct_treatment="IV fluids, insulin therapy, electrolyte monitoring",
    diagnosis_options=["Hypoglycemia", "Hyperglycemic crisis", "DKA only", "UTI"],
    treatment_options=["Oral glucose", "IV fluids and insulin", "Antibiotics only", "Observation"],
    difficulty="medium",
    speciality="Endocrinology",
  )
  db.session.add(sim)

  db.session.commit()
  print("Seed data created successfully.")
  print("Demo accounts: admin@clinical.com / admin123, student@clinical.com / student123")
