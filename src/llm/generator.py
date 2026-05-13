import json
import re
import logging

from pydantic import BaseModel, ValidationError

from config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationPayload(BaseModel):
    selected_indices: list[int]
    explanation: str
    reasons: dict[str, str] = {}


class QwenGenerator:
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._backend = None  # "llama_cpp" or "transformers"
        self._load_model()

    def _load_model(self):
        # Try llama_cpp first (GGUF, faster)
        if self._try_llama_cpp():
            return
        # Fallback to transformers (normal HF model)
        if self._try_transformers():
            return
        logger.warning("No LLM backend available. Generator will be disabled.")

    def _try_llama_cpp(self) -> bool:
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
            self._backend = "llama_cpp"
            logger.info("Qwen model loaded via llama_cpp")
            return True
        except Exception as e:
            logger.warning(f"llama_cpp failed: {e}")
            return False

    def _try_transformers(self) -> bool:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            model_id = settings.llm.transformers_model_id
            logger.info(f"Loading {model_id} via transformers...")

            self._tokenizer = AutoTokenizer.from_pretrained(
                model_id, trust_remote_code=True
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True,
            )
            self._backend = "transformers"
            logger.info(f"Qwen model loaded via transformers: {model_id}")
            return True
        except Exception as e:
            logger.warning(f"transformers failed: {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def generate(self, prompt: str) -> str:
        if not self.is_available:
            raise RuntimeError("Qwen model is not loaded")

        if self._backend == "llama_cpp":
            return self._generate_llama_cpp(prompt)
        return self._generate_transformers(prompt)

    def _generate_llama_cpp(self, prompt: str) -> str:
        response = self._model.create_chat_completion(
            messages=[
                {"role": "system", "content": "Sen Aria adinda bir muzik oneri asistanisin. Yanitlarini her zaman JSON formatinda ver."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.llm.max_tokens,
            temperature=settings.llm.temperature,
        )
        return response["choices"][0]["message"]["content"]

    def _generate_transformers(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": "Sen Aria adinda bir muzik oneri asistanisin. Yanitlarini her zaman JSON formatinda ver."},
            {"role": "user", "content": prompt},
        ]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt").to(self._model.device)

        import torch
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=settings.llm.max_tokens,
                temperature=settings.llm.temperature,
                do_sample=True,
                top_p=0.9,
            )
        # Decode only the new tokens
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        return self._tokenizer.decode(new_tokens, skip_special_tokens=True)

    def generate_json(self, prompt: str) -> dict | None:
        attempts = 0
        max_retries = settings.llm.reprompt_max_retries if settings.llm.reprompt_on_fail else 0
        last_error = None
        current_prompt = prompt

        while attempts <= max_retries:
            raw = self.generate(current_prompt)
            parsed = self._parse_json(raw)
            if parsed:
                try:
                    validated = RecommendationPayload.model_validate(parsed)
                    return validated.model_dump()
                except ValidationError as e:
                    last_error = e
                    logger.warning(f"Invalid LLM JSON schema: {e}")
            else:
                last_error = "parse_failed"

            if attempts >= max_retries:
                break

            current_prompt = (
                f"{prompt}\n\n"
                "Yanit JSON formatinda degil. Sadece gecerli JSON dondur. "
                "Ek aciklama, kod blogu ya da metin yazma."
            )
            attempts += 1

        logger.warning(f"LLM JSON reprompt failed: {last_error}")
        return None

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
