import json
import re
import logging

from pydantic import BaseModel, ValidationError

from config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationPayload(BaseModel):
    selected_indices: list[int]
    explanation: str


class QwenGenerator:
    def __init__(self):
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from llama_cpp import Llama
            from huggingface_hub import hf_hub_download

            model_path = hf_hub_download(
                repo_id=settings.llm.model_path,
                filename=settings.llm.model_file,
            )
            self._model = Llama(
                model_path=model_path,
                n_ctx=settings.llm.n_ctx,
                n_gpu_layers=settings.llm.n_gpu_layers,
                verbose=False,
            )
            logger.info("Qwen model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load Qwen model: {e}")
            self._model = None

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def generate(self, prompt: str) -> str:
        if not self.is_available:
            raise RuntimeError("Qwen model is not loaded")

        response = self._model.create_chat_completion(
            messages=[
                {"role": "system", "content": "Sen Aria adında bir müzik öneri asistanısın. Yanıtlarını her zaman JSON formatında ver."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.llm.max_tokens,
            temperature=settings.llm.temperature,
        )
        return response["choices"][0]["message"]["content"]

    def generate_json(self, prompt: str) -> dict | None:
        raw = self.generate(prompt)
        parsed = self._parse_json(raw)
        if not parsed:
            return None
        try:
            validated = RecommendationPayload.model_validate(parsed)
        except ValidationError as e:
            logger.warning(f"Invalid LLM JSON schema: {e}")
            return None
        return validated.model_dump()

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Extract JSON block from markdown code fence or raw braces
        match = re.search(r"```(?:json)?\s*(\{.*?})\s*```", text, re.DOTALL)
        if not match:
            match = re.search(r"\{.*}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if match.lastindex else match.group())
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse LLM JSON output: {text[:200]}")
        return None
