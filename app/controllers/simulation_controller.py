from flask import request
from flask_jwt_extended import current_user

from app.extensions import db
from app.helpers.response import error_response, success_response
from app.models.simulation_model import Simulation, SimulationAttempt
from app.services.ai_analysis_service import AIAnalysisService
from app.services.learning_service import LearningService
from app.validations.simulation_validation import validate_simulation, validate_simulation_attempt


def list_simulations():
  query = Simulation.query.filter_by(is_active=True)
  if request.args.get("speciality"):
    query = query.filter_by(speciality=request.args.get("speciality"))
  if request.args.get("difficulty"):
    query = query.filter_by(difficulty=request.args.get("difficulty"))
  sims = query.order_by(Simulation.created_at.desc()).all()
  return success_response("Simulations retrieved.", {
    "simulations": [s.to_dict() for s in sims],
  })


def get_simulation(simulation_id):
  sim = Simulation.query.get(simulation_id)
  if not sim:
    return error_response("Simulation not found.", 404)
  return success_response("Simulation retrieved.", {"simulation": sim.to_dict()})


def create_simulation():
  data = request.get_json(silent=True)
  errors = validate_simulation(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  sim = Simulation(
    title=data["title"],
    scenario=data["scenario"],
    patient_data=data.get("patient_data"),
    correct_diagnosis=data["correct_diagnosis"],
    correct_treatment=data["correct_treatment"],
    diagnosis_options=data.get("diagnosis_options", []),
    treatment_options=data.get("treatment_options", []),
    difficulty=data.get("difficulty", "medium"),
    speciality=data.get("speciality"),
    max_score=data.get("max_score", 100),
  )
  db.session.add(sim)
  db.session.commit()
  return success_response("Simulation created.", {"simulation": sim.to_dict()}, 201)


def update_simulation(simulation_id):
  sim = Simulation.query.get(simulation_id)
  if not sim:
    return error_response("Simulation not found.", 404)

  data = request.get_json(silent=True) or {}
  errors = validate_simulation(data, partial=True)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  for field in (
    "title", "scenario", "patient_data", "correct_diagnosis", "correct_treatment",
    "diagnosis_options", "treatment_options", "difficulty", "speciality", "max_score", "is_active",
  ):
    if field in data:
      setattr(sim, field, data[field])
  db.session.commit()
  return success_response("Simulation updated.", {"simulation": sim.to_dict()})


def delete_simulation(simulation_id):
  sim = Simulation.query.get(simulation_id)
  if not sim:
    return error_response("Simulation not found.", 404)
  db.session.delete(sim)
  db.session.commit()
  return success_response("Simulation deleted.")


def submit_attempt(simulation_id):
  sim = Simulation.query.get(simulation_id)
  if not sim:
    return error_response("Simulation not found.", 404)

  data = request.get_json(silent=True)
  errors = validate_simulation_attempt(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  try:
    result = AIAnalysisService.simulation_feedback(
      sim.scenario,
      data["diagnosis_selected"],
      data["treatment_selected"],
      sim.correct_diagnosis,
      sim.correct_treatment,
    )
  except Exception as exc:
    return error_response(f"Feedback generation failed: {exc}", 500)

  score = min(int(result.get("score", 0)), sim.max_score)
  attempt = SimulationAttempt(
    user_id=current_user.id,
    simulation_id=simulation_id,
    diagnosis_selected=data["diagnosis_selected"],
    treatment_selected=data["treatment_selected"],
    ai_feedback=result.get("feedback"),
    score=score,
  )
  db.session.add(attempt)
  db.session.commit()

  LearningService.record_simulation_score(current_user.id, simulation_id, score)

  return success_response("Simulation attempt saved.", {
    "attempt": attempt.to_dict(),
    "feedback": result.get("feedback"),
    "score": score,
  }, 201)


def attempt_history():
  attempts = SimulationAttempt.query.filter_by(user_id=current_user.id).order_by(
    SimulationAttempt.created_at.desc()
  ).all()
  return success_response("Simulation history retrieved.", {
    "attempts": [a.to_dict() for a in attempts],
  })
