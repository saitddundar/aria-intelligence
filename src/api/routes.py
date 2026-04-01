from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.embedding.embedder import TrackEmbedder
from src.vectordb.store import VectorStore

router = APIRouter()

# Lazy-loaded singletons
_embedder: TrackEmbedder | None = None
_store: VectorStore | None = None


def get_embedder() -> TrackEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = TrackEmbedder()
    return _embedder


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


MOOD_DESCRIPTIONS = {
    "happy": "happy joyful upbeat positive cheerful bright major energetic",
    "sad": "sad melancholic somber depressed heartbroken dark minor slow",
    "angry": "angry aggressive intense powerful loud heavy distorted",
    "relaxed": "relaxed calm peaceful gentle soft acoustic soothing",
    "energetic": "energetic hype powerful fast intense danceable groovy",
    "romantic": "romantic love tender warm intimate soft emotional",
    "nostalgic": "nostalgic memories retro classic old school vintage",
    "focused": "focused ambient minimal instrumental concentration study",
}


class MoodRequest(BaseModel):
    mood: str
    limit: int = 10


class TrackResponse(BaseModel):
    spotify_id: str
    name: str
    artist: str
    album: str
    image_url: str
    preview_url: str
    popularity: int
    genres: list[str]
    score: float


@router.post("/recommend", response_model=list[TrackResponse])
def recommend_by_mood(req: MoodRequest):
    """Get music recommendations based on mood."""
    mood_text = MOOD_DESCRIPTIONS.get(req.mood.lower(), req.mood)

    embedder = get_embedder()
    query_vector = embedder.embed_query(mood_text)

    store = get_store()
    results = store.search(query_vector, limit=req.limit)

    return [
        TrackResponse(
            spotify_id=r.get("spotify_id", ""),
            name=r.get("name", ""),
            artist=r.get("artist", ""),
            album=r.get("album", ""),
            image_url=r.get("image_url", ""),
            preview_url=r.get("preview_url", ""),
            popularity=r.get("popularity", 0),
            genres=r.get("genres", []),
            score=r.get("score", 0.0),
        )
        for r in results
    ]


@router.get("/search")
def search_by_text(q: str = Query(..., description="Free text query"), limit: int = 10):
    """Search tracks by free text (fallback for custom queries)."""
    embedder = get_embedder()
    query_vector = embedder.embed_query(q)

    store = get_store()
    return store.search(query_vector, limit=limit)


@router.get("/moods")
def list_moods():
    """List available mood options."""
    return list(MOOD_DESCRIPTIONS.keys())
