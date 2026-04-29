from src.llm.prompts import format_tracks_context, build_recommendation_prompt, MOOD_DESCRIPTIONS


def test_format_tracks_context_basic():
    tracks = [
        {"name": "Song A", "artist": "Artist 1", "genres": ["pop", "rock"]},
        {"name": "Song B", "artist": "Artist 2", "genres": []},
    ]
    result = format_tracks_context(tracks)
    assert "[1] Song A - Artist 1 | pop, rock" in result
    assert "[2] Song B - Artist 2" in result
    assert "| " not in result.split("\n")[1]  # no trailing pipe for empty genres


def test_format_tracks_context_with_audio_features():
    tracks = [
        {
            "name": "Happy Song",
            "artist": "Artist",
            "genres": [],
            "audio_features": {"valence": 0.8, "energy": 0.9},
        },
    ]
    result = format_tracks_context(tracks)
    assert "pozitif" in result
    assert "enerjik" in result


def test_build_recommendation_prompt():
    tracks = [{"name": "Test", "artist": "A", "genres": ["jazz"]}]
    prompt = build_recommendation_prompt("happy", "mutlu", tracks, 5, 2)
    assert "happy" in prompt
    assert "[1] Test - A" in prompt
    assert "5" in prompt


def test_mood_descriptions_has_all_moods():
    expected = {"happy", "sad", "angry", "relaxed", "energetic", "romantic", "nostalgic", "focused"}
    assert set(MOOD_DESCRIPTIONS.keys()) == expected
