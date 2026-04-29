from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.rag.chain import RAGResponse

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_moods():
    response = client.get("/api/v1/moods")
    assert response.status_code == 200
    moods = response.json()
    assert "happy" in moods
    assert "sad" in moods
    assert len(moods) >= 3


@patch("src.api.routes.get_rag_chain")
def test_recommend(mock_chain):
    mock_rag = MagicMock()
    mock_rag.recommend.return_value = RAGResponse(
        tracks=[
            {
                "spotify_id": "abc123",
                "name": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "image_url": "http://img.url",
                "preview_url": "http://preview.url",
                "popularity": 80,
                "genres": ["pop"],
                "score": 0.95,
            }
        ],
        explanation="Harika bir şarkı",
        rag_used=True,
        retrieval_count=20,
    )
    mock_chain.return_value = mock_rag

    response = client.post("/api/v1/recommend", json={"mood": "happy", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["rag_used"] is True
    assert data["explanation"] == "Harika bir şarkı"
    assert len(data["tracks"]) == 1
    assert data["tracks"][0]["name"] == "Test Song"
