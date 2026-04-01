"""
Main pipeline: Fetch tracks from Spotify → Embed → Store in Vector DB.

Usage:
    python -m src.pipeline --playlist <spotify_playlist_id>
    python -m src.pipeline --genre "turkish pop" --limit 50
"""

import argparse

from src.spotify.client import fetch_playlist_tracks, fetch_tracks_by_genre
from src.embedding.embedder import TrackEmbedder
from src.vectordb.store import VectorStore


def run_pipeline(tracks: list[dict]):
    print(f"Processing {len(tracks)} tracks...")

    # Embed
    embedder = TrackEmbedder()
    print("Generating embeddings...")
    embeddings = embedder.embed_tracks(tracks)
    print(f"Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    # Store
    store = VectorStore()
    store.create_collection()
    store.upsert_tracks(tracks, embeddings)
    print(f"Stored {len(tracks)} tracks in vector DB.")


def main():
    parser = argparse.ArgumentParser(description="Aria embedding pipeline")
    parser.add_argument("--playlist", type=str, help="Spotify playlist ID")
    parser.add_argument("--genre", type=str, help="Search by genre")
    parser.add_argument("--limit", type=int, default=50, help="Track limit for genre search")
    args = parser.parse_args()

    if args.playlist:
        tracks = fetch_playlist_tracks(args.playlist)
    elif args.genre:
        tracks = fetch_tracks_by_genre(args.genre, limit=args.limit)
    else:
        parser.error("Provide --playlist or --genre")

    run_pipeline(tracks)


if __name__ == "__main__":
    main()
