import hashlib
import logging
import random
import time

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config.settings import settings

logger = logging.getLogger(__name__)

UPSERT_BATCH_SIZE = 100
MAX_SEARCH_LIMIT = 100


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.vectordb.host,
            port=settings.vectordb.port,
        )
        self.collection = settings.vectordb.collection_name

    @staticmethod
    def _spotify_id_to_point_id(spotify_id: str) -> int:
        """Deterministic uint64 from Spotify track ID."""
        h = hashlib.sha256(spotify_id.encode()).digest()
        return int.from_bytes(h[:8], "big") >> 1  # positive int64

    def create_collection(self):
        """Create the vector collection if it doesn't exist."""
        try:
            existing = [c.name for c in self.client.get_collections().collections]
            if self.collection in existing:
                logger.info(f"Collection '{self.collection}' already exists, skipping creation")
                return
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=settings.vectordb.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created collection '{self.collection}'")
        except Exception as e:
            logger.warning(f"create_collection error (non-fatal): {e}")

    def upsert_tracks(self, tracks: list[dict], embeddings: list[list[float]]):
        """Store track embeddings with metadata in batches."""
        points = []
        for track, embedding in zip(tracks, embeddings):
            point_id = self._spotify_id_to_point_id(track["id"])
            payload = {
                "spotify_id": track["id"],
                "name": track["name"],
                "artist": track["artist"],
                "album": track["album"],
                "image_url": track.get("image_url", ""),
                "preview_url": track.get("preview_url") or "",
                "popularity": track.get("popularity", 0),
                "duration_ms": track.get("duration_ms", 0),
                "release_date": track.get("release_date", ""),
                "genres": track.get("genres", []),
            }
            if "audio_features" in track:
                payload["audio_features"] = track["audio_features"]

            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            ))

        # batch upsert to avoid gRPC message size limits
        for i in range(0, len(points), UPSERT_BATCH_SIZE):
            batch = points[i:i + UPSERT_BATCH_SIZE]
            self._retry(
                "qdrant.upsert",
                lambda b=batch: self.client.upsert(
                    collection_name=self.collection,
                    points=b,
                ),
            )

        logger.info(f"Upserted {len(points)} tracks to '{self.collection}'")

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> list[dict]:
        """Search for similar tracks by vector with optional score filtering."""
        limit = min(limit, MAX_SEARCH_LIMIT)

        results = self._retry(
            "qdrant.search",
            lambda: self.client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            ),
        )
        return [
            {"score": r.score, **r.payload}
            for r in results
        ]

    def get_by_ids(self, spotify_ids: list[str]) -> list[dict]:
        """Fetch tracks by their Spotify IDs directly from Qdrant."""
        if not spotify_ids:
            return []
        point_ids = [self._spotify_id_to_point_id(sid) for sid in spotify_ids]
        try:
            results = self.client.retrieve(
                collection_name=self.collection,
                ids=point_ids,
                with_payload=True,
            )
            return [r.payload for r in results if r.payload]
        except Exception as e:
            logger.warning(f"Failed to retrieve tracks by IDs: {e}")
            return []

    def _retry(self, operation_name: str, func):
        retries = settings.vectordb.retry_count
        backoff = settings.vectordb.retry_backoff_seconds
        max_backoff = settings.vectordb.retry_max_backoff_seconds
        jitter_ratio = settings.vectordb.retry_jitter_ratio
        last_exc = None
        for attempt in range(retries + 1):
            try:
                return func()
            except Exception as e:
                last_exc = e
                if attempt >= retries:
                    break
                sleep_s = min(backoff * (2 ** attempt), max_backoff)
                jitter = sleep_s * jitter_ratio * random.uniform(-1.0, 1.0)
                sleep_s = max(0.0, sleep_s + jitter)
                logger.warning(f"{operation_name} failed, retrying in {sleep_s:.2f}s: {e}")
                time.sleep(sleep_s)
        raise last_exc
