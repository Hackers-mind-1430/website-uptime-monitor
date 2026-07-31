from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_check_interval():
    response = client.post(
        "/add",
        data={
            "name": "Invalid Interval",
            "url": "https://example.com",
            "expected_status": 200,
            "check_interval": 0,
            "email": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "Check+interval" in response.headers["location"]


def test_invalid_status_code():
    response = client.post(
        "/add",
        data={
            "name": "Invalid Status",
            "url": "https://example.com",
            "expected_status": 600,
            "check_interval": 5,
            "email": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "Invalid+HTTP+status+code" in response.headers["location"]


def test_invalid_url():
    response = client.post(
        "/add",
        data={
            "name": "Invalid URL",
            "url": "not-a-url",
            "expected_status": 200,
            "check_interval": 5,
            "email": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "valid+HTTP" in response.headers["location"]