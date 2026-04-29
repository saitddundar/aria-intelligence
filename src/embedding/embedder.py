from sentence_transformers import SentenceTransformer

from config.settings import settings


class TrackEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding.model_name)
        model_name = settings.embedding.model_name.lower()
        if "bge-m3" in model_name:
            self.doc_prefix = "passage: "
            self.query_prefix = "query: "
        else:
            self.doc_prefix = ""
            self.query_prefix = ""

    def _track_to_text(self, track: dict) -> str:
        """Convert track metadata to a text representation for embedding."""
        parts = [
            f"{track['name']} by {track['artist']}",
            f"Album: {track['album']}",
        ]

        if features := track.get("audio_features"):
            mood_words = []
            if features.get("valence", 0) > 0.6:
                mood_words.append("happy upbeat positive")
            elif features.get("valence", 0) < 0.3:
                mood_words.append("sad melancholic somber")

            if features.get("energy", 0) > 0.7:
                mood_words.append("energetic intense powerful")
            elif features.get("energy", 0) < 0.3:
                mood_words.append("calm relaxed gentle")

            if features.get("danceability", 0) > 0.7:
                mood_words.append("danceable groovy rhythmic")

            if features.get("acousticness", 0) > 0.7:
                mood_words.append("acoustic organic natural")

            # major key = brighter, minor key = darker
            if features.get("mode") == 1:
                mood_words.append("bright major")
            elif features.get("mode") == 0:
                mood_words.append("dark minor")

            if features.get("liveness", 0) > 0.8:
                mood_words.append("live concert")

            if mood_words:
                parts.append(f"Mood: {' '.join(mood_words)}")

        if genres := track.get("genres"):
            parts.append(f"Genre: {', '.join(genres)}")

        if release_date := track.get("release_date", ""):
            year = release_date[:4]
            parts.append(f"Year: {year}")

        return ". ".join(parts)

    def track_to_text(self, track: dict) -> str:
        return self._track_to_text(track)

    @staticmethod
    def _apply_prefix(prefix: str, text: str) -> str:
        return f"{prefix}{text}" if prefix else text

    def embed_tracks(self, tracks: list[dict]) -> list[list[float]]:
        """Embed a list of tracks. Returns list of vectors."""
        texts = [self._apply_prefix(self.doc_prefix, self._track_to_text(t)) for t in tracks]
        embeddings = self.model.encode(
            texts,
            batch_size=settings.embedding.batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string (e.g. mood description)."""
        query_text = self._apply_prefix(self.query_prefix, query)
        embedding = self.model.encode(query_text, normalize_embeddings=True)
        return embedding.tolist()
