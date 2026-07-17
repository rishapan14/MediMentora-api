from app import create_app
from app.db_bootstrap import ensure_database
from app.extensions import db

ensure_database()
app = create_app()

with app.app_context():
  db.create_all()

if __name__ == "__main__":
  app.run(
    debug=app.config["FLASK_DEBUG"],
    port=int(__import__("os").getenv("PORT", "5000")),
  )
