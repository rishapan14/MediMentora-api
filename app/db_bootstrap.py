"""Ensure MySQL database exists before SQLAlchemy connects."""

import pymysql

from app.config import Config


def ensure_database():
  """Create the configured database if it does not exist."""
  connection = pymysql.connect(
    host=Config.DB_HOST,
    port=int(Config.DB_PORT),
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    charset="utf8mb4",
  )
  try:
    with connection.cursor() as cursor:
      cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
      )
    connection.commit()
  finally:
    connection.close()
