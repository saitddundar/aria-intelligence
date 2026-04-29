from unittest.mock import MagicMock, patch

from src.rag.chain import RAGChain, RAGResponse


def _make_track(i: int) -> dict:
    return {
        "spotify_id": f"id_{i}",
        "name": f"Track {i}",
        "artist": f"Artist {i}",
        "album": f"Album {i}",
        "image_url": "",
        "preview_url": "",
        "popularity": 50,
        "genres": ["pop"],
        "score": 0.9 - i * 0.05,
    }


def test_recommend_fallback_without_generator():
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1] * 1024
    store = MagicMock()
    store.search.return_value = [_make_track(i) for i in range(5)]

    chain = RAGChain(embedder=embedder, store=store, generator=None)
    result = chain.recommend("happy", limit=3)

    assert isinstance(result, RAGResponse)
    assert len(result.tracks) == 3
    assert result.rag_used is False
    assert result.explanation == ""


def test_recommend_with_generator():
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1] * 1024
    store = MagicMock()
    candidates = [_make_track(i) for i in range(10)]
    store.search.return_value = candidates

    generator = MagicMock()
    generator.is_available = True
    generator.generate_json.return_value = {
        "selected_indices": [2, 5, 8],
        "explanation": "Bu şarkılar çok güzel",
    }

    chain = RAGChain(embedder=embedder, store=store, generator=generator)
    result = chain.recommend("happy", limit=3)

    assert result.rag_used is True
    assert result.explanation == "Bu şarkılar çok güzel"
    assert result.tracks[0]["spotify_id"] == "id_1"  # index 2 -> candidates[1]
    assert result.tracks[1]["spotify_id"] == "id_4"  # index 5 -> candidates[4]
    assert result.tracks[2]["spotify_id"] == "id_7"  # index 8 -> candidates[7]


def test_recommend_generator_returns_bad_json_falls_back():
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1] * 1024
    store = MagicMock()
    store.search.return_value = [_make_track(i) for i in range(5)]

    generator = MagicMock()
    generator.is_available = True
    generator.generate_json.return_value = None  # bad JSON

    chain = RAGChain(embedder=embedder, store=store, generator=generator)
    result = chain.recommend("sad", limit=3)

    assert result.rag_used is False
    assert len(result.tracks) == 3


def test_recommend_fills_remaining_slots():
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1] * 1024
    store = MagicMock()
    candidates = [_make_track(i) for i in range(10)]
    store.search.return_value = candidates

    generator = MagicMock()
    generator.is_available = True
    generator.generate_json.return_value = {
        "selected_indices": [1],  # only 1 selected, but limit=3
        "explanation": "test",
    }

    chain = RAGChain(embedder=embedder, store=store, generator=generator)
    result = chain.recommend("relaxed", limit=3)

    assert result.rag_used is True
    assert len(result.tracks) == 3
