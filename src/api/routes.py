import logging
import time
from typing import Union

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


# ---------------------------------------------------------------------------
# /analyze — Sentiment Analysis (Go contract)
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str
    user_id: int = 0
    language_hint: str = ""


class AnalyzeResponse(BaseModel):
    sentiment_label: str
    dominant_emotion: str
    valence: float
    arousal: float
    energy: float
    emotion_scores: dict[str, float] = {}
    language: str = ""
    model_version: str = ""
    processing_ms: int = 0


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_mood(req: AnalyzeRequest, request: Request):
    """Analyze user text for sentiment and emotions."""
    analyzer = request.app.state.analyzer
    try:
        result = analyzer.analyze(req.text, req.language_hint)
        return AnalyzeResponse(**result)
    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sentiment analysis failed",
        )


# ---------------------------------------------------------------------------
# /recommend — RAG Music Recommendation (Go contract compatible)
# ---------------------------------------------------------------------------

class MoodSnapshot(BaseModel):
    sentiment_label: str = ""
    dominant_emotion: str = ""
    valence: float = 0.0
    arousal: float = 0.0
    energy: float = 0.0


class RecommendContext(BaseModel):
    preferred_genres: list[str] = []
    exclude_track_ids: list[str] = []
    language: str = ""
    liked_track_ids: list[str] = []
    collab_track_ids: list[str] = []


# Contrasting moods for "shift" mode
_SHIFT_MOOD = {
    "sad": "happy",
    "angry": "relaxed",
    "energetic": "relaxed",
    "relaxed": "energetic",
    "nostalgic": "happy",
    "happy": "energetic",
    "focused": "happy",
    "romantic": "energetic",
}


class RecommendRequest(BaseModel):
    """Accepts both old format (mood as string) and Go contract (mood as object)."""
    mood: Union[str, MoodSnapshot]
    user_id: int = 0
    mood_id: int = 0
    limit: int = 10
    mode: str = "match"   # "match" = stay in mood | "shift" = change mood
    context: RecommendContext | None = None


class TrackSuggestionResponse(BaseModel):
    spotify_track_id: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    preview_url: str = ""
    external_url: str = ""
    duration_ms: int = 0
    relevance_score: float = 0.0
    reason: str = ""


class RecommendResponse(BaseModel):
    model_version: str = ""
    rag_context: str = ""
    processing_ms: int = 0
    tracks: list[TrackSuggestionResponse] = []


# Mood mapping for Go contract's sentiment/emotion → mood key
_EMOTION_TO_MOOD = {
    "joy": "happy", "happiness": "happy", "contentment": "happy",
    "sadness": "sad", "grief": "sad", "sorrow": "sad",
    "anger": "angry", "frustration": "angry", "rage": "angry",
    "calm": "relaxed", "peace": "relaxed", "serenity": "relaxed",
    "excitement": "energetic", "thrill": "energetic",
    "love": "romantic", "tenderness": "romantic", "affection": "romantic",
    "nostalgia": "nostalgic", "longing": "nostalgic",
    "focus": "focused", "concentration": "focused",
}

_SENTIMENT_TO_MOOD = {
    "positive": "happy",
    "negative": "sad",
    "neutral": "focused",
    "mixed": "nostalgic",
    "bittersweet": "nostalgic",
}


def _resolve_mood_key(mood: Union[str, MoodSnapshot]) -> str:
    """Resolve mood input to one of 8 canonical mood keys."""
    if isinstance(mood, str):
        key = mood.strip().lower()
        if key in MOOD_DESCRIPTIONS:
            return key
        return "relaxed"

    # MoodSnapshot object from Go backend
    snap = mood

    # Try dominant_emotion first
    if snap.dominant_emotion:
        key = _EMOTION_TO_MOOD.get(snap.dominant_emotion.lower())
        if key:
            return key

    # Try sentiment_label
    if snap.sentiment_label:
        key = _SENTIMENT_TO_MOOD.get(snap.sentiment_label.lower())
        if key:
            # Refine with energy/valence
            if key == "happy" and snap.energy > 0.7:
                return "energetic"
            return key

    # Fallback: guess from valence/energy
    if snap.valence > 0.5 and snap.energy > 0.6:
        return "energetic"
    if snap.valence > 0.3 and snap.energy < 0.4:
        return "relaxed"
    if snap.valence < -0.3:
        return "sad"
    return "relaxed"


@router.post("/recommend", response_model=RecommendResponse)
def recommend_by_mood(
    req: RecommendRequest,
    chain: RAGChain = Depends(get_rag_chain),
):
    """Get music recommendations based on mood using RAG pipeline."""
    start = time.time()

    mood_key = _resolve_mood_key(req.mood)

    # Shift mode: recommend contrasting mood to change the user's state
    if req.mode == "shift":
        mood_key = _SHIFT_MOOD.get(mood_key, "happy")
        logger.info(f"Shift mode active → redirected to mood: {mood_key}")

    context = None
    if req.context:
        context = {
            "exclude_track_ids": req.context.exclude_track_ids,
            "liked_track_ids": req.context.liked_track_ids,
            "collab_track_ids": req.context.collab_track_ids,
        }

    try:
        result = chain.recommend(mood_key, limit=req.limit, context=context)
    except Exception as e:
        logger.exception(f"Recommendation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation service unavailable",
        )

    elapsed_ms = int((time.time() - start) * 1000)

    tracks = []
    for r in result.tracks:
        spotify_id = r.get("spotify_id", "")
        external_url = ""
        if spotify_id:
            external_url = f"https://open.spotify.com/track/{spotify_id}"

        tracks.append(TrackSuggestionResponse(
            spotify_track_id=spotify_id,
            title=r.get("name", ""),
            artist=r.get("artist", ""),
            album=r.get("album", ""),
            preview_url=r.get("preview_url", ""),
            external_url=external_url,
            duration_ms=r.get("duration_ms", 0),
            relevance_score=r.get("score", 0.0),
            reason=r.get("reason", ""),
        ))

    return RecommendResponse(
        model_version="aria-rag-v1.0.0",
        rag_context=result.explanation,
        processing_ms=elapsed_ms,
        tracks=tracks,
    )


# ---------------------------------------------------------------------------
# /search & /moods — unchanged
# ---------------------------------------------------------------------------

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
