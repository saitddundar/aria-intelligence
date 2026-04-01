# Aria Intelligence

RAG and embedding pipeline for the Aria music recommendation system.

## What is Aria?

Aria is an emotion-driven music recommendation system. Users select their current mood, and Aria suggests music that matches — powered by RAG (Retrieval-Augmented Generation) over a Spotify-sourced music catalog.

## This Repository

This repo contains the **ML/RAG pipeline** layer of the Aria project:

- **Music Embedding Pipeline** — Fetches track data from Spotify, generates embeddings using a lightweight model (e.g. bge-m3, nomic-embed), and stores them in a vector database.
- **RAG Engine** — Takes a user's mood, converts it to a query embedding, retrieves relevant tracks via similarity search, and uses Qwen (local LLM) to generate personalized recommendations.
- **API Service** — Exposes endpoints for the Go backend to consume (emotion analysis, music recommendation).

## Full System Architecture

```
React UI  →  Go Backend API  →  Python ML Service (this repo)
                                      ├── Embedding Pipeline
                                      ├── RAG Engine (Qwen)
                                      └── Vector DB (Qdrant/ChromaDB)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Embedding Model | bge-m3 / nomic-embed (TBD) |
| Generation Model | Qwen (local) |
| Vector Database | Qdrant / ChromaDB (TBD) |
| Music Data | Spotify API |
| Language | Python |

## Status

Early development — pipeline design phase.
