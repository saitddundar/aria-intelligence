import logging

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config.settings import settings

logger = logging.getLogger(__name__)

_client: spotipy.Spotify | None = None


def get_spotify_client() -> spotipy.Spotify:
    global _client
    if _client is None:
        auth_manager = SpotifyClientCredentials(
            client_id=settings.spotify.client_id,
            client_secret=settings.spotify.client_secret,
        )
        _client = spotipy.Spotify(auth_manager=auth_manager)
    return _client


def _enrich_with_genres(sp: spotipy.Spotify, tracks: list[dict]):
    """Fetch artist genres in batch and attach to tracks."""
    artist_ids = set()
    for t in tracks:
        for aid in t.get("artist_ids", []):
            artist_ids.add(aid)

    if not artist_ids:
        return

    artist_genres = {}
    artist_id_list = list(artist_ids)
    for i in range(0, len(artist_id_list), 50):
        batch = artist_id_list[i:i + 50]
        try:
            artists_data = sp.artists(batch)
            for artist in artists_data["artists"]:
                artist_genres[artist["id"]] = artist.get("genres", [])
        except Exception as e:
            logger.warning(f"Failed to fetch artist genres for batch: {e}")

    for track in tracks:
        genres = set()
        for aid in track.get("artist_ids", []):
            genres.update(artist_genres.get(aid, []))
        track["genres"] = list(genres)


def _enrich_with_audio_features(sp: spotipy.Spotify, tracks: list[dict]):
    """Fetch audio features in batch and attach to tracks."""
    track_ids = [t["id"] for t in tracks]

    for i in range(0, len(track_ids), 100):
        batch_ids = track_ids[i:i + 100]
        batch_tracks = tracks[i:i + 100]
        try:
            features_list = sp.audio_features(batch_ids)
        except Exception as e:
            logger.warning(f"Failed to fetch audio features: {e}")
            continue

        for track, features in zip(batch_tracks, features_list):
            if features:
                track["audio_features"] = {
                    "danceability": features["danceability"],
                    "energy": features["energy"],
                    "valence": features["valence"],
                    "tempo": features["tempo"],
                    "acousticness": features["acousticness"],
                    "instrumentalness": features["instrumentalness"],
                    "loudness": features["loudness"],
                    "mode": features["mode"],
                    "key": features["key"],
                    "speechiness": features["speechiness"],
                    "liveness": features["liveness"],
                }


def _parse_track_item(track: dict) -> dict:
    """Parse a single Spotify track object into our internal format."""
    artist_list = track["artists"]
    image_url = ""
    if track["album"].get("images"):
        image_url = track["album"]["images"][0]["url"]

    return {
        "id": track["id"],
        "name": track["name"],
        "artist": ", ".join(a["name"] for a in artist_list),
        "artist_ids": [a["id"] for a in artist_list],
        "album": track["album"]["name"],
        "image_url": image_url,
        "preview_url": track.get("preview_url") or "",
        "popularity": track.get("popularity", 0),
        "duration_ms": track.get("duration_ms", 0),
        "release_date": track["album"].get("release_date", ""),
        "genres": [],
    }


def fetch_playlist_tracks(playlist_id: str) -> list[dict]:
    """Fetch all tracks from a Spotify playlist with full metadata."""
    sp = get_spotify_client()
    results = sp.playlist_tracks(playlist_id)

    tracks = []
    while results:
        for item in results["items"]:
            track = item.get("track")
            if not track or not track.get("id"):
                continue
            tracks.append(_parse_track_item(track))

        # paginate
        if results.get("next"):
            results = sp.next(results)
        else:
            break

    logger.info(f"Fetched {len(tracks)} tracks from playlist {playlist_id}")

    _enrich_with_genres(sp, tracks)
    _enrich_with_audio_features(sp, tracks)

    return tracks


def fetch_tracks_by_genre(genre: str, limit: int = 50) -> list[dict]:
    """Search tracks by genre with full metadata enrichment."""
    sp = get_spotify_client()
    limit = min(limit, 50)  # Spotify search API max
    results = sp.search(q=f"genre:{genre}", type="track", limit=limit)

    tracks = []
    for track in results["tracks"]["items"]:
        if not track.get("id"):
            continue
        tracks.append(_parse_track_item(track))

    _enrich_with_genres(sp, tracks)
    _enrich_with_audio_features(sp, tracks)

    return tracks
