from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_vague_query_clarifies():
    response = client.post("/chat", json={"messages": [{"role": "user", "content": "I need an assessment"}]})
    body = response.json()
    assert response.status_code == 200
    assert body["recommendations"] == []
    assert body["end_of_conversation"] is False


def test_java_backend_recommendations_are_schema_valid():
    response = client.post(
        "/chat",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "Senior Full-Stack Engineer with Core Java, Spring, SQL, AWS and Docker.",
                },
                {"role": "assistant", "content": "Is this backend or frontend leaning?"},
                {"role": "user", "content": "Backend leaning, senior IC."},
            ]
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert 1 <= len(body["recommendations"]) <= 10
    assert {"name", "url", "test_type"} <= set(body["recommendations"][0])

