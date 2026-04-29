import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from src.embedding.embedder import TrackEmbedder
from src.vectordb.store import VectorStore
from src.llm.generator import QwenGenerator
from src.llm.prompts import MOOD_DESCRIPTIONS
from src.rag.chain import RAGChain

logger = logging.getLogger(__name__)

router = APIRouter()


def get_embedder(request: Request) -> TrackEmbedder:
    return request.app.state.embedder


def get_store(request: Request) -> VectorStore:
    return request.app.state.store


def get_generator(request: Request) -> QwenGenerator:
    return request.app.state.generator


def get_rag_chain(request: Request) -> RAGChain:
    return request.app.state.rag_chain


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
def recommend_by_mood(
    req: MoodRequest,
    chain: RAGChain = Depends(get_rag_chain),
):
    """Get music recommendations based on mood using RAG pipeline."""
    try:
        result = chain.recommend(req.mood, limit=req.limit)
    except Exception as e:
        logger.exception(f"Recommendation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation service unavailable",
        )

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
def search_by_text(
    q: str = Query(..., description="Free text query"),
    limit: int = 10,
    embedder: TrackEmbedder = Depends(get_embedder),
    store: VectorStore = Depends(get_store),
):
    """Search tracks by free text."""
    try:
        query_vector = embedder.embed_query(q)
        return store.search(query_vector, limit=limit)
    except Exception as e:
        logger.exception(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service unavailable",
        )


@router.get("/moods")
def list_moods():
    """List available mood options."""
    return list(MOOD_DESCRIPTIONS.keys())
