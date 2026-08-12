"""Run database schema setup once, before starting application workers."""

from sqlalchemy import inspect, text

from app import create_app
from app.db_bootstrap import ensure_database
from app.extensions import db


LOCK_NAME = "medimentora_schema_bootstrap"
LOCK_TIMEOUT_SECONDS = 120


def bootstrap_schema(app=None) -> None:
  """Create and patch the schema while holding a cross-process MySQL lock."""
  print("[schema] Starting database schema bootstrap", flush=True)
  ensure_database()
  app = app or create_app()

  with app.app_context():
    with db.engine.connect() as connection:
      acquired = connection.execute(
        text("SELECT GET_LOCK(:name, :timeout)"),
        {"name": LOCK_NAME, "timeout": LOCK_TIMEOUT_SECONDS},
      ).scalar()
      if acquired != 1:
        raise RuntimeError("Timed out waiting for the database schema lock")

      try:
        db.create_all()

        from app.helpers.schema_patches import (
          ensure_body_systems_hub_schema,
          ensure_learning_schema,
          ensure_medical_teacher_schema,
          ensure_platform_settings_schema,
          ensure_report_history_schema,
          ensure_user_previous_role_schema,
          ensure_xray_analysis_schema,
          ensure_xray_reference_library_schema,
        )

        ensure_report_history_schema()
        ensure_xray_analysis_schema()
        ensure_xray_reference_library_schema()
        ensure_learning_schema()
        ensure_body_systems_hub_schema()
        ensure_medical_teacher_schema()
        ensure_platform_settings_schema()
        ensure_user_previous_role_schema()

        table_names = inspect(db.engine).get_table_names()
        if not table_names:
          raise RuntimeError(
            f"Schema bootstrap created zero tables in database '{app.config['DB_NAME']}'"
          )
        print(
          f"[schema] Database '{app.config['DB_NAME']}' contains "
          f"{len(table_names)} tables: {', '.join(sorted(table_names))}",
          flush=True,
        )
        print("[schema] Database schema bootstrap completed", flush=True)
      finally:
        connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": LOCK_NAME})


if __name__ == "__main__":
  bootstrap_schema()
