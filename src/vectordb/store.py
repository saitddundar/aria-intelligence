import hashlib
import logging
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
            self._retry(
                "qdrant.create_collection",
                lambda: self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=VectorParams(
                        size=settings.vectordb.vector_size,
                        distance=Distance.COSINE,
                    ),
                ),
            )
            logger.info(f"Created collection '{self.collection}'")
        except Exception:
            # collection already exists — safe to ignore
            pass

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
                lambda: self.client.upsert(
                    collection_name=self.collection,
                    points=batch,
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
            "qdrant.query_points",
            lambda: self.client.query_points(
                collection_name=self.collection,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            ),
        )
        return [
            {"score": r.score, **r.payload}
            for r in results.points
        ]

    def _retry(self, operation_name: str, func):
        retries = settings.vectordb.retry_count
        backoff = settings.vectordb.retry_backoff_seconds
        max_backoff = settings.vectordb.retry_max_backoff_seconds
        last_exc = None
        for attempt in range(retries + 1):
            try:
                return func()
            except Exception as e:
                last_exc = e
                if attempt >= retries:
                    break
                sleep_s = min(backoff * (2 ** attempt), max_backoff)
                logger.warning(f"{operation_name} failed, retrying in {sleep_s:.2f}s: {e}")
                time.sleep(sleep_s)
        raise last_exc
