"""Production networking contract tests."""

import json
from pathlib import Path


def test_health_is_public_and_database_independent(client):
  response = client.get("/health")

  assert response.status_code == 200
  assert response.get_json() == {
    "status": "ok",
    "service": "medimentora-api",
  }


def test_cors_allows_known_vercel_frontend(client):
  response = client.options(
    "/api/auth/login",
    headers={
      "Origin": "https://medimentora-client.vercel.app",
      "Access-Control-Request-Method": "POST",
      "Access-Control-Request-Headers": "Authorization, Content-Type",
    },
  )

  assert response.headers.get("Access-Control-Allow-Origin") == (
    "https://medimentora-client.vercel.app"
  )
  assert "Authorization" in response.headers.get("Access-Control-Allow-Headers", "")


def test_cors_does_not_reflect_unknown_origins(client):
  response = client.options(
    "/api/auth/login",
    headers={
      "Origin": "https://untrusted.example",
      "Access-Control-Request-Method": "POST",
    },
  )

  assert response.headers.get("Access-Control-Allow-Origin") is None


def test_railway_web_start_is_health_first_and_memory_bounded():
  root = Path(__file__).resolve().parents[1]
  start_script = (root / "start.sh").read_text(encoding="utf-8")
  railway = json.loads((root / "railway.json").read_text(encoding="utf-8"))

  assert "python -m app.schema_bootstrap" in start_script
  assert "python -m app.schema_bootstrap &" not in start_script
  assert '${RUN_LEARNING_WORKER:-false}' in start_script
  assert '${MEDIMENTORA_WEB_WORKERS:-1}' in start_script
  assert '--worker-class gthread' in start_script
  assert '${MEDIMENTORA_WEB_THREADS:-2}' in start_script
  assert start_script.index("python -m app.schema_bootstrap") < start_script.index("exec gunicorn")
  assert railway["build"]["builder"] == "DOCKERFILE"
  assert railway["deploy"]["healthcheckPath"] == "/health"
  assert railway["deploy"]["restartPolicyType"] == "ON_FAILURE"
