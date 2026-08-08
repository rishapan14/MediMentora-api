import sys
from pathlib import Path

from app import create_app
from app.db_bootstrap import ensure_database
from app.extensions import db


def _print_ocr_startup_status() -> None:
  """Print OCR readiness so environment mismatches are obvious at boot."""
  python_path = Path(sys.executable)
  in_venv = ".venv" in str(python_path).lower() or hasattr(sys, "real_prefix") or (
    hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
  )
  env_label = ".venv" if ".venv" in str(python_path).lower() else ("venv" if in_venv else "global")

  engine_name = "none"
  version = "n/a"
  ready = False
  try:
    from app.services.report_analysis.ocr.engines.paddle_engine import PaddleOCREngine

    engine = PaddleOCREngine()
    ready = engine.is_available()
    if ready:
      engine_name = "RapidOCR (PaddleOCR ONNX)"
      try:
        import rapidocr_onnxruntime as rapid

        version = getattr(rapid, "__version__", "installed")
      except Exception:
        version = "installed"
  except Exception as exc:
    engine_name = f"error: {exc}"

  mark = "OK" if ready else "FAIL"
  print(f"[{mark}] OCR Engine : {engine_name}")
  print(f"[{mark}] Version    : {version}")
  print(f"[{mark}] Python     : {env_label} ({python_path})")
  print(f"[{mark}] Ready      : {ready}")
  if not ready:
    print(
      "HINT: Start the API with .venv so OCR packages resolve:\n"
      "  .\\.venv\\Scripts\\python.exe run.py\n"
      "  or .\\start-api.ps1"
    )


ensure_database()
app = create_app()

with app.app_context():
  db.create_all()
  from app.helpers.schema_patches import (
    ensure_body_systems_hub_schema,
    ensure_learning_schema,
    ensure_report_history_schema,
    ensure_xray_analysis_schema,
  )

  ensure_report_history_schema()
  ensure_xray_analysis_schema()
  ensure_learning_schema()
  ensure_body_systems_hub_schema()
  _print_ocr_startup_status()

if __name__ == "__main__":
  app.run(
    debug=app.config["FLASK_DEBUG"],
    port=int(__import__("os").getenv("PORT", "5000")),
  )
