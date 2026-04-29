RECOMMENDATION_PROMPT = """Kullanici su an "{mood}" hissediyor.
Kisa aciklama: {mood_detail}
Dil: Turkce.

Asagidaki muzik listesini inceleyerek bu ruh haline en uygun {top_k} sarkiyi sec ve neden bu sarkilari sectigini dogal, samimi bir dille acikla.

Mevcut Sarkilar:
{tracks_context}

Yanitini asagidaki JSON formatinda ver:
{{
    "selected_indices": [1, 3, 5],
    "explanation": "Sinyaller: genre + enerji. Neden: ..."
}}

Kurallar:
- selected_indices listesinde sarki numaralarini (koseli parantez icindeki sayilar) kullan
- Tam olarak {top_k} sarki sec
- Aciklamayi su formatta yaz: "Sinyaller: <en az 2 ipucu>. Neden: <2-3 cumle>"
- Sinyaller listesinde en az 2 farkli ipucu olsun (genre, audio_features, yil/donem, tempo/enerji)
- Ayni sanatcidan en fazla {max_per_artist} sarki sec (mecbur kalmadikca)
- Aciklamayi Turkce yaz, 2-3 cumle yeterli
"""

MOOD_DESCRIPTIONS = {
    "happy": "mutlu, keyifli, pozitif",
    "sad": "uzgun, hüzünlü, melankolik",
    "angry": "ofkeli, gergin, sert",
    "relaxed": "rahat, sakin, huzurlu",
    "energetic": "enerjik, hareketli, yuksek tempolu",
    "romantic": "romantik, duygusal, sicak",
    "nostalgic": "nostaljik, eski gunler, retro",
    "focused": "odakli, minimal, konsantrasyon",
}

MOOD_EMBEDDING_HINTS = {
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


def build_recommendation_prompt(
    mood: str,
    mood_detail: str,
    tracks: list[dict],
    top_k: int,
    max_per_artist: int,
) -> str:
    return RECOMMENDATION_PROMPT.format(
        mood=mood,
        mood_detail=mood_detail,
        tracks_context=format_tracks_context(tracks),
        top_k=top_k,
        max_per_artist=max_per_artist,
    )
