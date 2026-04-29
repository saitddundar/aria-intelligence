import logging
from dataclasses import dataclass, field

from config.settings import settings
from src.embedding.embedder import TrackEmbedder
from src.vectordb.store import VectorStore
from src.llm.generator import QwenGenerator
from sentence_transformers import CrossEncoder

from src.llm.prompts import MOOD_DESCRIPTIONS, MOOD_EMBEDDING_HINTS, build_recommendation_prompt

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    tracks: list[dict] = field(default_factory=list)
    explanation: str = ""
    rag_used: bool = False
    retrieval_count: int = 0


class RAGChain:
    def __init__(
        self,
        embedder: TrackEmbedder,
        store: VectorStore,
        generator: QwenGenerator | None = None,
    ):
        self.embedder = embedder
        self.store = store
        self.generator = generator
        self._reranker: CrossEncoder | None = None

    def _get_reranker(self) -> CrossEncoder | None:
        if not settings.rag.enable_reranker:
            return None
        if self._reranker is not None:
            return self._reranker

        try:
            self._reranker = CrossEncoder(settings.rag.reranker_model_name)
        except Exception as e:
            logger.warning(f"Failed to load reranker model: {e}")
            self._reranker = None
        return self._reranker

    def _rerank_candidates(self, query_text: str, candidates: list[dict]) -> list[dict]:
        reranker = self._get_reranker()
        if not reranker:
            return candidates

        pairs = [(query_text, self.embedder.track_to_text(c)) for c in candidates]
        try:
            scores = reranker.predict(pairs)
        except Exception as e:
            logger.warning(f"Reranker failed, keeping vector order: {e}")
            return candidates

        scored = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored]

    @staticmethod
    def _apply_diversity(
        candidates: list[dict],
        max_per_artist: int | None,
        min_candidates: int,
    ) -> list[dict]:
        if not max_per_artist or max_per_artist < 1:
            return candidates

        counts: dict[str, int] = {}
        filtered: list[dict] = []
        for track in candidates:
            artist = (track.get("artist") or "").strip().lower()
            if not artist:
                filtered.append(track)
                continue
            count = counts.get(artist, 0)
            if count >= max_per_artist:
                continue
            counts[artist] = count + 1
            filtered.append(track)

        if len(filtered) < min_candidates:
            return candidates

        return filtered

    @staticmethod
    def _enforce_diversity(
        selected: list[dict],
        candidates: list[dict],
        max_per_artist: int | None,
        limit: int,
    ) -> list[dict]:
        if not max_per_artist or max_per_artist < 1:
            return selected[:limit]

        def _artist_key(track: dict) -> str:
            return (track.get("artist") or "").strip().lower()

        counts: dict[str, int] = {}
        filtered: list[dict] = []
        for track in selected:
            artist = _artist_key(track)
            if not artist:
                filtered.append(track)
                continue
            count = counts.get(artist, 0)
            if count >= max_per_artist:
                continue
            counts[artist] = count + 1
            filtered.append(track)

        if len(filtered) >= limit:
            return filtered[:limit]

        selected_ids = {t.get("spotify_id") for t in filtered}
        for candidate in candidates:
            if len(filtered) >= limit:
                break
            if candidate.get("spotify_id") in selected_ids:
                continue
            artist = _artist_key(candidate)
            if artist and counts.get(artist, 0) >= max_per_artist:
                continue
            if artist:
                counts[artist] = counts.get(artist, 0) + 1
            filtered.append(candidate)

        return filtered

    def recommend(self, mood: str, limit: int = 10) -> RAGResponse:
        # 1. Embed mood query
        mood_key = mood.strip().lower()
        mood_text = MOOD_EMBEDDING_HINTS.get(mood_key, mood)
        mood_label = mood
        mood_detail = MOOD_DESCRIPTIONS.get(mood_key, mood)
        query_vector = self.embedder.embed_query(mood_text)

        # 2. Retrieve candidates from Qdrant
        top_k = settings.rag.top_k_retrieval
        candidates = self.store.search(
            query_vector,
            limit=top_k,
            score_threshold=settings.rag.score_threshold,
        )

        candidates = self._rerank_candidates(mood_text, candidates)
        min_needed = min(limit, settings.rag.top_k_final)
        candidates = self._apply_diversity(
            candidates,
            settings.rag.max_tracks_per_artist,
            min_needed,
        )

        if not candidates:
            return RAGResponse()

        # 3. If generator available, use RAG to rerank and explain
        if self.generator and self.generator.is_available:
            try:
                return self._rag_recommend(mood_label, mood_detail, candidates, limit)
            except Exception as e:
                logger.warning(f"RAG generation failed, falling back: {e}")
                if not settings.rag.fallback_on_error:
                    raise

        # 4. Fallback: return top results from vector search directly
        return RAGResponse(
            tracks=candidates[:limit],
            explanation="",
            rag_used=False,
            retrieval_count=len(candidates),
        )

    def _rag_recommend(
        self, mood: str, mood_detail: str, candidates: list[dict], limit: int
    ) -> RAGResponse:
        top_k = min(limit, settings.rag.top_k_final)
        prompt = build_recommendation_prompt(
            mood=mood,
            mood_detail=mood_detail,
            tracks=candidates,
            top_k=top_k,
            max_per_artist=settings.rag.max_tracks_per_artist or top_k,
        )

        result = self.generator.generate_json(prompt)

        if not result or "selected_indices" not in result:
            logger.warning("LLM returned invalid JSON, using vector search fallback")
            return RAGResponse(
                tracks=candidates[:limit],
                explanation="",
                rag_used=False,
                retrieval_count=len(candidates),
            )

        # Map 1-based indices back to tracks
        selected = []
        selected_ids = set()
        for idx in result["selected_indices"]:
            if 1 <= idx <= len(candidates):
                track = candidates[idx - 1]
                sid = track.get("spotify_id")
                if sid in selected_ids:
                    continue
                selected_ids.add(sid)
                selected.append(track)

        # Guardrail: require exact count when possible
        if len(selected) != top_k:
            logger.warning(
                f"LLM selected {len(selected)} tracks, expected {top_k}; falling back"
            )
            return RAGResponse(
                tracks=candidates[:limit],
                explanation="",
                rag_used=False,
                retrieval_count=len(candidates),
            )

        # Fill remaining slots if LLM selected fewer than limit
        if len(selected) < limit:
            selected_set = {t.get("spotify_id") for t in selected}
            for c in candidates:
                if len(selected) >= limit:
                    break
                if c.get("spotify_id") not in selected_set:
                    selected.append(c)

        selected = self._enforce_diversity(
            selected,
            candidates,
            settings.rag.max_tracks_per_artist,
            limit,
        )

        return RAGResponse(
            tracks=selected,
            explanation=result.get("explanation", ""),
            rag_used=True,
            retrieval_count=len(candidates),
        )
