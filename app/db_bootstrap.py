"""Wait for the configured MySQL database before schema creation."""

import os
import time

import pymysql

from app.config import Config


def ensure_database():
  """Wait until Railway's existing database is reachable."""
  attempts = int(os.getenv("DB_BOOTSTRAP_ATTEMPTS", "30"))
  delay = float(os.getenv("DB_BOOTSTRAP_RETRY_SECONDS", "2"))
  last_error = None

  for attempt in range(1, attempts + 1):
    try:
      connection = pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        connect_timeout=10,
      )
      connection.close()
      print(f"[schema] MySQL database '{Config.DB_NAME}' is reachable", flush=True)
      return
    except pymysql.MySQLError as exc:
      last_error = exc
      print(
        f"[schema] MySQL unavailable at {Config.DB_HOST}:{Config.DB_PORT} "
        f"(attempt {attempt}/{attempts}): {exc}",
        flush=True,
      )
      if attempt < attempts:
        time.sleep(delay)

  raise RuntimeError(
    f"Could not connect to MySQL database '{Config.DB_NAME}' after {attempts} attempts"
  ) from last_error
