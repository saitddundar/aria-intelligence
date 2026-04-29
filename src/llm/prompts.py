RECOMMENDATION_PROMPT = """Kullanıcı şu an "{mood}" hissediyor.

Aşağıdaki müzik listesini inceleyerek bu ruh haline en uygun {top_k} şarkıyı seç ve neden bu şarkıları seçtiğini doğal, samimi bir dille açıkla.

Mevcut Şarkılar:
{tracks_context}

Yanıtını aşağıdaki JSON formatında ver:
{{
  "selected_indices": [1, 3, 5],
  "explanation": "Bu şarkıları seçtim çünkü..."
}}

Kurallar:
- selected_indices listesinde şarkı numaralarını (köşeli parantez içindeki sayılar) kullan
- Tam olarak {top_k} şarkı seç
- Açıklamayı Türkçe yaz, 2-3 cümle yeterli
"""

MOOD_DESCRIPTIONS = {
    "happy": "happy joyful upbeat positive cheerful bright major energetic",
    "sad": "sad melancholic somber depressed heartbroken dark minor slow",
    "angry": "angry aggressive intense powerful loud heavy distorted",
    "relaxed": "relaxed calm peaceful gentle soft acoustic soothing",
    "energetic": "energetic hype powerful fast intense danceable groovy",
    "romantic": "romantic love tender warm intimate soft emotional",
    "nostalgic": "nostalgic memories retro classic old school vintage",
    "focused": "focused ambient minimal instrumental concentration study",
}


def format_tracks_context(tracks: list[dict]) -> str:
    lines = []
    for i, t in enumerate(tracks, 1):
        genres = ", ".join(t.get("genres", []))
        line = f"[{i}] {t.get('name', '')} - {t.get('artist', '')}"
        if genres:
            line += f" | {genres}"
        if af := t.get("audio_features"):
            descriptors = []
            if af.get("valence", 0) > 0.6:
                descriptors.append("pozitif")
            elif af.get("valence", 0) < 0.3:
                descriptors.append("hüzünlü")
            if af.get("energy", 0) > 0.7:
                descriptors.append("enerjik")
            elif af.get("energy", 0) < 0.3:
                descriptors.append("sakin")
            if descriptors:
                line += f" | {', '.join(descriptors)}"
        lines.append(line)
    return "\n".join(lines)


def build_recommendation_prompt(mood: str, tracks: list[dict], top_k: int) -> str:
    return RECOMMENDATION_PROMPT.format(
        mood=mood,
        tracks_context=format_tracks_context(tracks),
        top_k=top_k,
    )
