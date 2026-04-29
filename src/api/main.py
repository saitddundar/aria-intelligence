import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.embedding.embedder import TrackEmbedder
from src.llm.generator import QwenGenerator
from src.rag.chain import RAGChain
from src.vectordb.store import VectorStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedder = TrackEmbedder()
    store = VectorStore()
    store.create_collection()
    generator = QwenGenerator()
    rag_chain = RAGChain(embedder=embedder, store=store, generator=generator)

    app.state.embedder = embedder
    app.state.store = store
    app.state.generator = generator
    app.state.rag_chain = rag_chain

    yield

app = FastAPI(title="Aria Intelligence", version="0.1.0", lifespan=lifespan)

raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
)
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]
ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

if "*" in ALLOWED_ORIGINS:
    if len(ALLOWED_ORIGINS) > 1:
        ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o != "*"]
    else:
        ALLOW_CREDENTIALS = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health(request: Request):
    components = {}
    store: VectorStore = request.app.state.store
    embedder: TrackEmbedder = request.app.state.embedder
    generator: QwenGenerator = request.app.state.generator

    try:
        store.client.get_collection(store.collection)
        components["vectordb"] = "ok"
    except Exception as e:
        logger.warning(f"Health check failed for vectordb: {e}")
        components["vectordb"] = "error"

    components["embedder"] = "ok" if getattr(embedder, "model", None) else "error"
    components["generator"] = "ok" if generator.is_available else "error"

    status = "ok" if all(v == "ok" for v in components.values()) else "degraded"
    return {"status": status, "components": components}
