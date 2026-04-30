# Aria Intelligence

Emotion-driven music recommendation system powered by RAG (Retrieval-Augmented Generation). Users select their current mood, and Aria suggests music that matches — using vector similarity search over a Spotify-sourced catalog and a local LLM for personalized explanations.

## Architecture

```
React UI  -->  Go Backend API  -->  Python ML Service (this repo)
                                        |-- Spotify Client
                                        |-- Embedding Pipeline (bge-m3)
                                        |-- Vector DB (Qdrant)
                                        |-- Reranker (bge-reranker-v2-m3)
                                        |-- LLM Generator (Qwen 2.5)
                                        '-- RAG Chain
```

This repo is the **Python ML/RAG service**. The Go backend and React frontend live in separate repos.

## Pipeline Flow

```
1. User selects mood (e.g. "happy")
                |
2. Mood string --> embed_query() --> 1024-dim vector
                |
3. Cosine similarity search in Qdrant --> top-20 candidates
                |
4. CrossEncoder reranking (optional, bge-reranker-v2-m3)
                |
5. Diversity filter (max N tracks per artist)
                |
6. Qwen selects final top-K + generates explanation in Turkish
                |
7. Response: tracks[] + explanation + rag_used flag
```

If the LLM is unavailable or returns invalid output, the system falls back to raw vector search results.

## Project Structure

```
config/
  settings.py             # Dataclass-based configuration (env vars)
src/
  pipeline.py             # CLI for batch embedding (playlist/genre)
  api/
    main.py               # FastAPI app, lifespan, CORS, health check
    routes.py             # /recommend, /search, /moods endpoints
  spotify/
    client.py             # Spotify API client with retry & backoff
  embedding/
    embedder.py           # TrackEmbedder (sentence-transformers, bge-m3)
  vectordb/
    store.py              # Qdrant vector store with batch upsert
  rag/
    chain.py              # RAGChain: retrieval + rerank + generate
  llm/
    generator.py          # QwenGenerator (llama-cpp-python, GGUF)
    prompts.py            # Mood descriptions & recommendation prompt
tests/
  test_api.py             # API endpoint tests
  test_rag_chain.py       # RAG pipeline tests
  test_generator.py       # LLM JSON parsing tests
  test_prompts.py         # Prompt formatting tests
docs/
  sprint-roadmap.md       # Sprint plan
  user-stories.md         # User stories & requirements
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Embedding Model | [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) (1024-dim) |
| Reranker | [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) |
| Generation Model | [Qwen 2.5 1.5B Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF) (Q4_K_M quantized) |
| LLM Runtime | llama-cpp-python |
| Vector Database | Qdrant |
| Music Data | Spotify Web API |
| Web Framework | FastAPI + Uvicorn |
| Data Validation | Pydantic v2 |

## Setup

### Prerequisites

- Python 3.11+
- [Qdrant](https://qdrant.tech/) running on `localhost:6333`
- Spotify Developer credentials ([dashboard](https://developer.spotify.com/dashboard))

### Installation

```bash
# Clone & enter
git clone <repo-url>
cd aria-intelligence

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Install dependencies (pick one)
pip install -r requirements-cpu.txt    # CPU-only PyTorch
pip install -r requirements-gpu.txt    # GPU PyTorch (CUDA 12.1)
pip install -r requirements-dev.txt    # Dev tools (pytest, httpx)

# Configure environment
cp .env.example .env
# Edit .env with your Spotify credentials
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPOTIFY_CLIENT_ID` | Yes | — | Spotify API client ID |
| `SPOTIFY_CLIENT_SECRET` | Yes | — | Spotify API client secret |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:5173` | Allowed CORS origins |
| `QWEN_MODEL_PATH` | No | `Qwen/Qwen2.5-1.5B-Instruct-GGUF` | HuggingFace model repo |
| `QWEN_MODEL_FILE` | No | `qwen2.5-1.5b-instruct-q4_k_m.gguf` | GGUF model filename |
| `QWEN_GPU_LAYERS` | No | `-1` | GPU layers (-1 = all) |
| `RAG_SCORE_THRESHOLD` | No | `0.2` | Minimum cosine similarity |
| `RAG_ENABLE_RERANKER` | No | `true` | Enable CrossEncoder reranking |
| `RAG_MAX_TRACKS_PER_ARTIST` | No | `2` | Max tracks per artist in results |
| `LLM_REPROMPT_ON_FAIL` | No | `true` | Retry on invalid LLM JSON |
| `LLM_REPROMPT_MAX_RETRIES` | No | `1` | Max reprompt attempts |

See [.env.example](.env.example) for the full list including retry/backoff settings.

## Usage

### Start the API server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The server starts at `http://localhost:8000`. Interactive docs available at `/docs` (Swagger) and `/redoc`.

### Batch embed tracks

Before the API can recommend music, you need to populate the vector database:

```bash
# From a Spotify playlist
python -m src.pipeline --playlist <playlist_id>

# From a genre search
python -m src.pipeline --genre "turkish pop" --limit 50
```

## API Endpoints

### `GET /health`

Health check with component status.

```json
{
  "status": "ok",
  "components": {
    "vectordb": "ok",
    "embedder": "ok",
    "generator": "ok"
  }
}
```

### `GET /api/v1/moods`

List available mood options.

```json
["happy", "sad", "angry", "relaxed", "energetic", "romantic", "nostalgic", "focused"]
```

### `POST /api/v1/recommend`

Get mood-based recommendations.

```bash
curl -X POST http://localhost:8000/api/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{"mood": "happy", "limit": 5}'
```

```json
{
  "tracks": [
    {
      "spotify_id": "abc123",
      "name": "Track Name",
      "artist": "Artist Name",
      "album": "Album Name",
      "image_url": "https://...",
      "preview_url": "https://...",
      "popularity": 85,
      "genres": ["pop", "dance"],
      "score": 0.92
    }
  ],
  "explanation": "Bu parcalar mutlu ve enerjik ruh halinize uygun...",
  "rag_used": true
}
```

### `GET /api/v1/search?q=<query>&limit=10`

Free-text track search via vector similarity.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rag_chain.py -v
```

## Supported Moods

| Mood | Description |
|------|-------------|
| `happy` | Mutlu, keyifli, pozitif |
| `sad` | Uzgun, huzunlu, melankolik |
| `angry` | Ofkeli, gergin, sert |
| `relaxed` | Rahat, sakin, huzurlu |
| `energetic` | Enerjik, hareketli, yuksek tempolu |
| `romantic` | Romantik, duygusal, sicak |
| `nostalgic` | Nostaljik, eski gunler, retro |
| `focused` | Odakli, minimal, konsantrasyon |
