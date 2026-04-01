import os
from dataclasses import dataclass


@dataclass
class SpotifyConfig:
    client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")


@dataclass
class EmbeddingConfig:
    model_name: str = "BAAI/bge-m3"
    batch_size: int = 32


@dataclass
class VectorDBConfig:
    host: str = "localhost"
    port: int = 6333  # Qdrant default
    collection_name: str = "aria_tracks"
    vector_size: int = 1024  # bge-m3 output dim


@dataclass
class Settings:
    spotify: SpotifyConfig = None
    embedding: EmbeddingConfig = None
    vectordb: VectorDBConfig = None

    def __post_init__(self):
        self.spotify = self.spotify or SpotifyConfig()
        self.embedding = self.embedding or EmbeddingConfig()
        self.vectordb = self.vectordb or VectorDBConfig()


settings = Settings()
