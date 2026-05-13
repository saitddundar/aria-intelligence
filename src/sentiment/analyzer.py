import json
import logging
import re
import time

from src.llm.generator import QwenGenerator
from src.llm.prompts import MOOD_DESCRIPTIONS

logger = logging.getLogger(__name__)

SENTIMENT_PROMPT = """Kullanicinin asagidaki metnini analiz et ve ruh halini belirle.

Metin: "{text}"

Yanitini asagidaki JSON formatinda ver:
{{
    "mood": "happy|sad|angry|relaxed|energetic|romantic|nostalgic|focused",
    "sentiment_label": "positive|negative|neutral|mixed|bittersweet",
    "dominant_emotion": "joy|sadness|anger|calm|excitement|love|nostalgia|focus",
    "valence": 0.0,
    "arousal": 0.0,
    "energy": 0.0,
    "emotion_scores": {{"joy": 0.0, "sadness": 0.0, "anger": 0.0, "calm": 0.0, "excitement": 0.0, "love": 0.0, "nostalgia": 0.0, "focus": 0.0}},
    "language": "tr"
}}

Kurallar:
- mood alaninda su seceneklerden birini yaz: happy, sad, angry, relaxed, energetic, romantic, nostalgic, focused
- valence: [-1.0, +1.0] araliginda, -1 negatif, +1 pozitif
- arousal: [-1.0, +1.0] araliginda, -1 sakin, +1 heyecanli
- energy: [0.0, 1.0] araliginda
- emotion_scores: her duygu icin 0.0-1.0 araliginda skor ver
- Sadece JSON dondur, ek aciklama yazma
"""

_MOOD_TO_EMOTION = {
    "happy": "joy",
    "sad": "sadness",
    "angry": "anger",
    "relaxed": "calm",
    "energetic": "excitement",
    "romantic": "love",
    "nostalgic": "nostalgia",
    "focused": "focus",
}

_MOOD_DEFAULTS = {
    "happy":     {"sentiment_label": "positive",    "valence": 0.8,  "arousal": 0.5,  "energy": 0.7},
    "sad":       {"sentiment_label": "negative",    "valence": -0.6, "arousal": -0.4, "energy": 0.2},
    "angry":     {"sentiment_label": "negative",    "valence": -0.5, "arousal": 0.8,  "energy": 0.9},
    "relaxed":   {"sentiment_label": "positive",    "valence": 0.4,  "arousal": -0.6, "energy": 0.2},
    "energetic": {"sentiment_label": "positive",    "valence": 0.7,  "arousal": 0.9,  "energy": 0.95},
    "romantic":  {"sentiment_label": "positive",    "valence": 0.6,  "arousal": 0.1,  "energy": 0.4},
    "nostalgic": {"sentiment_label": "mixed",       "valence": 0.1,  "arousal": -0.2, "energy": 0.3},
    "focused":   {"sentiment_label": "neutral",     "valence": 0.2,  "arousal": 0.3,  "energy": 0.5},
}

_KEYWORD_MAP = {
    "mutlu": "happy", "keyifli": "happy", "pozitif": "happy", "sevinc": "happy",
    "uzgun": "sad", "huzunlu": "sad", "melankolik": "sad", "uzuntu": "sad",
    "ofkeli": "angry", "kizgin": "angry", "sinirli": "angry", "gergin": "angry",
    "sakin": "relaxed", "rahat": "relaxed", "huzurlu": "relaxed",
    "enerjik": "energetic", "hareketli": "energetic", "dinamik": "energetic",
    "romantik": "romantic", "duygusal": "romantic", "ask": "romantic",
    "nostaljik": "nostalgic", "eski": "nostalgic", "retro": "nostalgic",
    "odakli": "focused", "konsantre": "focused",
    "happy": "happy", "sad": "sad", "angry": "angry", "relaxed": "relaxed",
    "energetic": "energetic", "romantic": "romantic", "nostalgic": "nostalgic", "focused": "focused",
}


class SentimentAnalyzer:
    def __init__(self, generator: QwenGenerator):
        self.generator = generator

    def analyze(self, text: str, language_hint: str = "") -> dict:
        start = time.time()
        result = self._analyze_with_llm(text)
        if result is None:
            result = self._fallback_keyword(text)
        elapsed_ms = int((time.time() - start) * 1000)
        result["processing_ms"] = elapsed_ms
        result["model_version"] = "aria-sentiment-v1.0.0"
        if language_hint:
            result["language"] = language_hint
        return result

    def _analyze_with_llm(self, text: str) -> dict | None:
        if not self.generator or not self.generator.is_available:
            return None

        prompt = SENTIMENT_PROMPT.format(text=text)
        try:
            raw = self.generator.generate(prompt)
        except Exception as e:
            logger.warning(f"Sentiment LLM generation failed: {e}")
            return None

        parsed = self._parse_json(raw)
        if not parsed:
            return None

        mood = parsed.get("mood", "").strip().lower()
        if mood not in MOOD_DESCRIPTIONS:
            return None

        defaults = _MOOD_DEFAULTS[mood]
        return {
            "sentiment_label": parsed.get("sentiment_label", defaults["sentiment_label"]),
            "dominant_emotion": parsed.get("dominant_emotion", _MOOD_TO_EMOTION[mood]),
            "valence": float(parsed.get("valence", defaults["valence"])),
            "arousal": float(parsed.get("arousal", defaults["arousal"])),
            "energy": float(parsed.get("energy", defaults["energy"])),
            "emotion_scores": parsed.get("emotion_scores", {}),
            "language": parsed.get("language", "tr"),
        }

    def _fallback_keyword(self, text: str) -> dict:
        text_lower = text.lower()
        mood = "relaxed"  # default
        for keyword, mood_key in _KEYWORD_MAP.items():
            if keyword in text_lower:
                mood = mood_key
                break

        defaults = _MOOD_DEFAULTS[mood]
        return {
            "sentiment_label": defaults["sentiment_label"],
            "dominant_emotion": _MOOD_TO_EMOTION[mood],
            "valence": defaults["valence"],
            "arousal": defaults["arousal"],
            "energy": defaults["energy"],
            "emotion_scores": {_MOOD_TO_EMOTION[mood]: 0.8},
            "language": "tr",
        }

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r"```(?:json)?\s*(\{.*?})\s*```", text, re.DOTALL)
        if not match:
            match = re.search(r"\{.*}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if match.lastindex else match.group())
            except json.JSONDecodeError:
                pass
        return None
