from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.embedding.embedder import TrackEmbedder
from src.vectordb.store import VectorStore
from src.llm.generator import QwenGenerator
from src.llm.prompts import MOOD_DESCRIPTIONS
from src.rag.chain import RAGChain

router = APIRouter()

# Lazy-loaded singletons
_embedder: TrackEmbedder | None = None
_store: VectorStore | None = None
_generator: QwenGenerator | None = None
_rag_chain: RAGChain | None = None


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


def get_generator() -> QwenGenerator:
    global _generator
    if _generator is None:
        _generator = QwenGenerator()
    return _generator


def get_rag_chain() -> RAGChain:
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain(
            embedder=get_embedder(),
            store=get_store(),
            generator=get_generator(),
        )
    return _rag_chain


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


class RecommendResponse(BaseModel):
    tracks: list[TrackResponse]
    explanation: str = ""
    rag_used: bool = False


@router.post("/recommend", response_model=RecommendResponse)
def recommend_by_mood(req: MoodRequest):
    """Get music recommendations based on mood using RAG pipeline."""
    chain = get_rag_chain()
    result = chain.recommend(req.mood, limit=req.limit)

    tracks = [
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
        for r in result.tracks
    ]

    return RecommendResponse(
        tracks=tracks,
        explanation=result.explanation,
        rag_used=result.rag_used,
    )


@router.get("/search")
def search_by_text(q: str = Query(..., description="Free text query"), limit: int = 10):
    """Search tracks by free text."""
    embedder = get_embedder()
    query_vector = embedder.embed_query(q)

    store = get_store()
    return store.search(query_vector, limit=limit)


@router.get("/moods")
def list_moods():
    """List available mood options."""
    return list(MOOD_DESCRIPTIONS.keys())
