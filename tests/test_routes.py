from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_loads():
    response = client.get("/")

    assert response.status_code == 200


def test_add_page_loads():
    response = client.get("/add")

    assert response.status_code == 200


def test_alerts_page_loads():
    response = client.get("/alerts")

    assert response.status_code == 200


def test_status_api_loads():
    response = client.get("/api/status")

    assert response.status_code == 200


def test_analytics_api_loads():
    response = client.get("/api/analytics")

    assert response.status_code == 200