from fastapi.testclient import TestClient

from app.main import app, items


client = TestClient(app)


def setup_function() -> None:
    items.clear()


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_check(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_database_connection", lambda: True)
    response = client.get("/db/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "postgresql"}


def test_database_health_check_returns_unavailable(monkeypatch) -> None:
    def database_down() -> bool:
        raise ConnectionError("database down")

    monkeypatch.setattr("app.main.check_database_connection", database_down)
    response = client.get("/db/health")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


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


def test_generate_returns_ollama_response(monkeypatch) -> None:
    async def fake_generate(prompt: str) -> str:
        assert prompt == "Say hello"
        return "Hello!"

    monkeypatch.setattr("app.main.generate_response", fake_generate)
    response = client.post("/generate", json={"prompt": "Say hello"})

    assert response.status_code == 200
    assert response.json() == {"model": "qwen2.5:1.5", "response": "Hello!"}


def test_generate_rejects_blank_prompt() -> None:
    response = client.post("/generate", json={"prompt": " "})
    assert response.status_code == 422


def test_generate_returns_service_unavailable_when_ollama_is_down(monkeypatch) -> None:
    async def fake_generate(_: str) -> str:
        raise ConnectionError("Could not connect to Ollama")

    monkeypatch.setattr("app.main.generate_response", fake_generate)
    response = client.post("/generate", json={"prompt": "Say hello"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not connect to Ollama"
