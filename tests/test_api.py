from fastapi.testclient import TestClient

from app.main import app, items


client = TestClient(app)


def setup_function() -> None:
    items.clear()


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_item_accepts_valid_payload() -> None:
    response = client.post("/items", json={"name": "Notebook", "quantity": 2})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Notebook", "quantity": 2}


def test_create_item_rejects_invalid_payload() -> None:
    response = client.post("/items", json={"name": "", "quantity": 0})
    assert response.status_code == 422
    assert len(response.json()["detail"]) == 2


def test_create_item_rejects_unknown_types() -> None:
    response = client.post("/items", json={"name": "Notebook", "quantity": "many"})
    assert response.status_code == 422
