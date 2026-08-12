"""Database configuration and Railway startup tests."""

from app.config import _database_settings


def test_database_url_populates_mysql_settings(monkeypatch):
  for name in (
    "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME",
    "MYSQLUSER", "MYSQLPASSWORD", "MYSQLHOST", "MYSQLPORT", "MYSQLDATABASE",
    "MYSQL_URL", "MYSQL_PUBLIC_URL",
  ):
    monkeypatch.delenv(name, raising=False)
  monkeypatch.setenv("DATABASE_URL", "mysql://railway:p%40ss@mysql.railway.internal:3307/railway")

  assert _database_settings() == {
    "user": "railway", "password": "p@ss", "host": "mysql.railway.internal",
    "port": "3307", "name": "railway",
  }


def test_explicit_database_settings_override_connection_url(monkeypatch):
  monkeypatch.setenv("DATABASE_URL", "mysql://url-user:url-pass@url-host:3306/url-db")
  monkeypatch.setenv("DB_HOST", "private-mysql")
  monkeypatch.setenv("DB_NAME", "app_db")

  settings = _database_settings()

  assert settings["host"] == "private-mysql"
  assert settings["name"] == "app_db"

def test_database_bootstrap_connects_to_provisioned_database(monkeypatch):
  from app import db_bootstrap

  calls = []

  class Connection:
    def close(self):
      calls.append("closed")

  def connect(**kwargs):
    calls.append(kwargs)
    return Connection()

  monkeypatch.setattr(db_bootstrap.pymysql, "connect", connect)
  monkeypatch.setattr(db_bootstrap.Config, "DB_HOST", "mysql.internal")
  monkeypatch.setattr(db_bootstrap.Config, "DB_PORT", "3306")
  monkeypatch.setattr(db_bootstrap.Config, "DB_USER", "railway")
  monkeypatch.setattr(db_bootstrap.Config, "DB_PASSWORD", "secret")
  monkeypatch.setattr(db_bootstrap.Config, "DB_NAME", "railway")

  db_bootstrap.ensure_database()

  assert calls[0]["database"] == "railway"
  assert calls[0]["host"] == "mysql.internal"
  assert calls[1] == "closed"