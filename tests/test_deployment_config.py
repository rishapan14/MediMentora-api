"""Production networking contract tests."""


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
