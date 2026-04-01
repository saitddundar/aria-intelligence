from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config.settings import settings


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.vectordb.host,
            port=settings.vectordb.port,
        )
        self.collection = settings.vectordb.collection_name

    def create_collection(self):
        """Create the vector collection if it doesn't exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=settings.vectordb.vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_tracks(self, tracks: list[dict], embeddings: list[list[float]]):
        """Store track embeddings with metadata."""
        points = []
        for i, (track, embedding) in enumerate(zip(tracks, embeddings)):
            payload = {
                "spotify_id": track["id"],
                "name": track["name"],
                "artist": track["artist"],
                "album": track["album"],
                "image_url": track.get("image_url", ""),
                "preview_url": track.get("preview_url", ""),
                "popularity": track.get("popularity", 0),
                "duration_ms": track.get("duration_ms", 0),
                "release_date": track.get("release_date", ""),
                "genres": track.get("genres", []),
            }
            if "audio_features" in track:
                payload["audio_features"] = track["audio_features"]

            points.append(PointStruct(
                id=i,
                vector=embedding,
                payload=payload,
            ))

        self.client.upsert(
            collection_name=self.collection,
            points=points,
        )

    def search(self, query_vector: list[float], limit: int = 10) -> list[dict]:
        """Search for similar tracks by vector."""
        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=limit,
        )
        return [
            {"score": r.score, **r.payload}
            for r in results.points
        ]
