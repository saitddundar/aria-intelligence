# Aria Intelligence - Project Context

## Overview
RAG-based music recommendation system that analyzes user emotions and suggests music accordingly.

## Architecture
- **Frontend:** React (separate repo or directory)
- **Backend API:** Go (orchestration, auth, API endpoints)
- **ML/RAG Pipeline:** Python (this repo) — embedding, RAG, emotion-to-query mapping

Go backend communicates with Python ML service via HTTP/gRPC.

## Key Decisions
- **Music data source:** Spotify API
- **Emotion input:** Selection-based UI (user picks from predefined emotions/moods)
- **Embedding model:** Lightweight model (e.g. bge-m3, nomic-embed) — NOT Qwen
- **Generation model:** Qwen (local) — used for RAG generation/reasoning
- **Vector DB:** TBD (Qdrant, Milvus, or ChromaDB)

## Pipeline Flow
1. Fetch music data + features from Spotify API
2. Embed music using lightweight embedding model → store in vector DB
3. User selects mood → map to query embedding
4. Vector similarity search → retrieve relevant tracks
5. Qwen generates personalized recommendation with retrieved context

## Tech Notes
- Keep embedding and generation models separate for performance
- Batch embed music catalog offline, serve queries online
- Python service exposes REST/gRPC endpoints for Go backend
