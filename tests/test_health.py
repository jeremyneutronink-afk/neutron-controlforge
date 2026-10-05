from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert (
        body["service"]
        == "neutron-controlforge-api"
    )
