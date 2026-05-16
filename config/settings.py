import os
from dataclasses import dataclass


def _optional_float(value: str, default: float | None) -> float | None:
    if value == "" or value.lower() == "none":
        return None
    try:
        return float(value)
    except ValueError:
        return default


def _optional_int(value: str, default: int | None) -> int | None:
    if value == "" or value.lower() == "none":
        return None
    try:
        return int(value)
    except ValueError:
        return default


@dataclass
class SpotifyConfig:
    client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    retry_count: int = int(os.getenv("SPOTIFY_RETRY_COUNT", "3"))
    retry_backoff_seconds: float = _optional_float(
        os.getenv("SPOTIFY_RETRY_BACKOFF", "0.5"),
        0.5,
    ) or 0.5
    retry_max_backoff_seconds: float = _optional_float(
        os.getenv("SPOTIFY_RETRY_MAX_BACKOFF", "4.0"),
        4.0,
    ) or 4.0
    retry_jitter_ratio: float = _optional_float(
        os.getenv("SPOTIFY_RETRY_JITTER", "0.2"),
        0.2,
    ) or 0.2


@dataclass
class EmbeddingConfig:
    model_name: str = "BAAI/bge-m3"
    batch_size: int = 32


@dataclass
class VectorDBConfig:
    host: str = os.getenv("QDRANT_HOST", "localhost")
    port: int = int(os.getenv("QDRANT_PORT", "6333"))  # Qdrant default
    collection_name: str = "aria_tracks"
    vector_size: int = 1024  # bge-m3 output dim
    retry_count: int = int(os.getenv("QDRANT_RETRY_COUNT", "2"))
    retry_backoff_seconds: float = _optional_float(
        os.getenv("QDRANT_RETRY_BACKOFF", "0.5"),
        0.5,
    ) or 0.5
    retry_max_backoff_seconds: float = _optional_float(
        os.getenv("QDRANT_RETRY_MAX_BACKOFF", "4.0"),
        4.0,
    ) or 4.0
    retry_jitter_ratio: float = _optional_float(
        os.getenv("QDRANT_RETRY_JITTER", "0.2"),
        0.2,
    ) or 0.2


@dataclass
class LLMConfig:
    model_path: str = os.getenv("QWEN_MODEL_PATH", "Qwen/Qwen2.5-1.5B-Instruct-GGUF")
    model_file: str = os.getenv("QWEN_MODEL_FILE", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
    transformers_model_id: str = os.getenv("QWEN_TRANSFORMERS_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
    n_ctx: int = 4096
    n_gpu_layers: int = int(os.getenv("QWEN_GPU_LAYERS", "-1"))
    max_tokens: int = 512
    temperature: float = 0.7
    reprompt_on_fail: bool = os.getenv("LLM_REPROMPT_ON_FAIL", "true").lower() == "true"
    reprompt_max_retries: int = int(os.getenv("LLM_REPROMPT_MAX_RETRIES", "1"))


@dataclass
class RAGConfig:
    top_k_retrieval: int = 20
    top_k_final: int = 10
    fallback_on_error: bool = True
    score_threshold: float | None = _optional_float(
        os.getenv("RAG_SCORE_THRESHOLD", "0.2"),
        0.2,
    )
    enable_reranker: bool = os.getenv("RAG_ENABLE_RERANKER", "true").lower() == "true"
    reranker_model_name: str = os.getenv("RAG_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    max_tracks_per_artist: int | None = _optional_int(
        os.getenv("RAG_MAX_TRACKS_PER_ARTIST", "2"),
        2,
    )


@dataclass
class CollaborativeConfig:
    enable: bool = os.getenv("COLLAB_ENABLE", "true").lower() == "true"
    boost_factor: float = float(os.getenv("COLLAB_BOOST_FACTOR", "0.15"))
    max_collab_inject: int = int(os.getenv("COLLAB_MAX_INJECT", "5"))


@dataclass
class Settings:
    spotify: SpotifyConfig = None
    embedding: EmbeddingConfig = None
    vectordb: VectorDBConfig = None
    llm: LLMConfig = None
    rag: RAGConfig = None
    collaborative: CollaborativeConfig = None

    def __post_init__(self):
        self.spotify = self.spotify or SpotifyConfig()
        self.embedding = self.embedding or EmbeddingConfig()
        self.vectordb = self.vectordb or VectorDBConfig()
        self.llm = self.llm or LLMConfig()
        self.rag = self.rag or RAGConfig()
        self.collaborative = self.collaborative or CollaborativeConfig()


settings = Settings()
