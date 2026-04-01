import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config.settings import settings


def get_spotify_client() -> spotipy.Spotify:
    auth_manager = SpotifyClientCredentials(
        client_id=settings.spotify.client_id,
        client_secret=settings.spotify.client_secret,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def fetch_playlist_tracks(playlist_id: str) -> list[dict]:
    """Fetch all tracks from a Spotify playlist with audio features."""
    sp = get_spotify_client()
    results = sp.playlist_tracks(playlist_id)

    tracks = []
    artist_ids = set()

    for item in results["items"]:
        track = item.get("track")
        if not track:
            continue

        artist_list = track["artists"]
        for a in artist_list:
            artist_ids.add(a["id"])

        image_url = ""
        if track["album"].get("images"):
            image_url = track["album"]["images"][0]["url"]

        tracks.append({
            "id": track["id"],
            "name": track["name"],
            "artist": ", ".join(a["name"] for a in artist_list),
            "artist_ids": [a["id"] for a in artist_list],
            "album": track["album"]["name"],
            "image_url": image_url,
            "preview_url": track.get("preview_url", ""),
            "popularity": track.get("popularity", 0),
            "duration_ms": track.get("duration_ms", 0),
            "release_date": track["album"].get("release_date", ""),
            "genres": [],
        })

    # Fetch artist genres in batch (max 50 per request)
    artist_id_list = list(artist_ids)
    artist_genres = {}
    for i in range(0, len(artist_id_list), 50):
        batch = artist_id_list[i:i + 50]
        artists_data = sp.artists(batch)
        for artist in artists_data["artists"]:
            artist_genres[artist["id"]] = artist.get("genres", [])

    for track in tracks:
        genres = set()
        for aid in track["artist_ids"]:
            genres.update(artist_genres.get(aid, []))
        track["genres"] = list(genres)

    # Fetch audio features in batch
    track_ids = [t["id"] for t in tracks]
    audio_features = sp.audio_features(track_ids)

    for track, features in zip(tracks, audio_features):
        if features:
            track["audio_features"] = {
                "danceability": features["danceability"],
                "energy": features["energy"],
                "valence": features["valence"],
                "tempo": features["tempo"],
                "acousticness": features["acousticness"],
                "instrumentalness": features["instrumentalness"],
                "loudness": features["loudness"],
                "mode": features["mode"],  # 1=major, 0=minor
                "key": features["key"],
                "speechiness": features["speechiness"],
                "liveness": features["liveness"],
            }

    return tracks


def fetch_tracks_by_genre(genre: str, limit: int = 50) -> list[dict]:
    """Search tracks by genre."""
    sp = get_spotify_client()
    results = sp.search(q=f"genre:{genre}", type="track", limit=limit)

    tracks = []
    for track in results["tracks"]["items"]:
        image_url = ""
        if track["album"].get("images"):
            image_url = track["album"]["images"][0]["url"]

        tracks.append({
            "id": track["id"],
            "name": track["name"],
            "artist": ", ".join(a["name"] for a in track["artists"]),
            "album": track["album"]["name"],
            "image_url": image_url,
            "preview_url": track.get("preview_url", ""),
            "popularity": track.get("popularity", 0),
            "duration_ms": track.get("duration_ms", 0),
            "release_date": track["album"].get("release_date", ""),
        })

    return tracks
