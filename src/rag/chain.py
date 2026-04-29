import logging
from dataclasses import dataclass, field

from config.settings import settings
from src.embedding.embedder import TrackEmbedder
from src.vectordb.store import VectorStore
from src.llm.generator import QwenGenerator
from src.llm.prompts import MOOD_DESCRIPTIONS, build_recommendation_prompt

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

    def recommend(self, mood: str, limit: int = 10) -> RAGResponse:
        # 1. Embed mood query
        mood_text = MOOD_DESCRIPTIONS.get(mood.lower(), mood)
        query_vector = self.embedder.embed_query(mood_text)

        # 2. Retrieve candidates from Qdrant
        top_k = settings.rag.top_k_retrieval
        candidates = self.store.search(query_vector, limit=top_k)

        if not candidates:
            return RAGResponse()

        # 3. If generator available, use RAG to rerank and explain
        if self.generator and self.generator.is_available:
            try:
                return self._rag_recommend(mood, candidates, limit)
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
        self, mood: str, candidates: list[dict], limit: int
    ) -> RAGResponse:
        top_k = min(limit, settings.rag.top_k_final)
        prompt = build_recommendation_prompt(mood, candidates, top_k)

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
        for idx in result["selected_indices"]:
            if 1 <= idx <= len(candidates):
                selected.append(candidates[idx - 1])

        # Fill remaining slots if LLM selected fewer than limit
        if len(selected) < limit:
            selected_set = {t.get("spotify_id") for t in selected}
            for c in candidates:
                if len(selected) >= limit:
                    break
                if c.get("spotify_id") not in selected_set:
                    selected.append(c)

        return RAGResponse(
            tracks=selected,
            explanation=result.get("explanation", ""),
            rag_used=True,
            retrieval_count=len(candidates),
        )
