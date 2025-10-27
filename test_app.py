from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
import pytest

from app import app
from models import get_session


DATABASE_URL = "sqlite:///test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_string(client: TestClient):
    response = client.post("/strings", json={"value": "hello world"})
    data = response.json()
    assert response.status_code == 201
    assert data["value"] == "hello world"
    assert "properties" in data


def test_create_existing_string(client: TestClient):
    client.post("/strings", json={"value": "hello world"})
    response = client.post("/strings", json={"value": "hello world"})
    assert response.status_code == 409


def test_get_string(client: TestClient):
    client.post("/strings", json={"value": "hello world"})
    response = client.get("/strings/hello world")
    data = response.json()
    assert response.status_code == 200
    assert data["value"] == "hello world"


def test_get_non_existing_string(client: TestClient):
    response = client.get("/strings/goodbye world")
    assert response.status_code == 404


def test_get_all_strings(client: TestClient):
    client.post("/strings", json={"value": "hello world"})
    client.post("/strings", json={"value": "level"})
    response = client.get("/strings")
    data = response.json()
    assert response.status_code == 200
    assert len(data["data"]) == 2


def test_get_all_strings_with_filters(client: TestClient):
    client.post("/strings", json={"value": "hello world"})
    client.post("/strings", json={"value": "level"})
    response = client.get("/strings?is_palindrome=true")
    data = response.json()
    assert response.status_code == 200
    assert len(data["data"]) == 1
    assert data["data"][0]["value"] == "level"


def test_filter_by_natural_language(client: TestClient):
    client.post("/strings", json={"value": "hello world"})
    client.post("/strings", json={"value": "level"})
    response = client.get("/strings/filter-by-natural-language?query=all single word palindromic strings")
    data = response.json()
    assert response.status_code == 200
    assert len(data["data"]) == 1
    assert data["data"][0]["value"] == "level"


def test_delete_string(client: TestClient):
    client.post("/strings", json={"value": "hello world"})
    response = client.delete("/strings/hello world")
    assert response.status_code == 204


def test_delete_non_existing_string(client: TestClient):
    response = client.delete("/strings/goodbye world")
    assert response.status_code == 404