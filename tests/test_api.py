from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routes import get_rag_chain, get_embedder, get_store, get_generator
from src.rag.chain import RAGResponse


mock_store = MagicMock()
mock_store.client.get_collection.return_value = True
mock_store.collection = "aria_tracks"

mock_embedder = MagicMock()
mock_embedder.model = True

mock_generator = MagicMock()
mock_generator.is_available = True

app.state.store = mock_store
app.state.embedder = mock_embedder
app.state.generator = mock_generator
app.state.rag_chain = MagicMock()

client = TestClient(app, raise_server_exceptions=True)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ok", "degraded"}
    assert "components" in data


def test_list_moods():
    response = client.get("/api/v1/moods")
    assert response.status_code == 200
    moods = response.json()
    assert "happy" in moods
    assert "sad" in moods
    assert len(moods) >= 3


def test_recommend():
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

    app.dependency_overrides[get_rag_chain] = lambda: mock_rag

    response = client.post("/api/v1/recommend", json={"mood": "happy", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["rag_used"] is True
    assert data["explanation"] == "Harika bir şarkı"
    assert len(data["tracks"]) == 1
    assert data["tracks"][0]["name"] == "Test Song"

    app.dependency_overrides.clear()
