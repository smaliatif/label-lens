import json
from pathlib import Path
from typing import Protocol

from app.config import Settings
from app.models import DietProfile, LabelAnalysis


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "label_analysis.txt"


class LabelAnalyzer(Protocol):
    def analyze(
        self, image_bytes: bytes, mime_type: str, profile: DietProfile
    ) -> LabelAnalysis:
        ...


class GeminiLabelAnalyzer:
    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    def analyze(
        self, image_bytes: bytes, mime_type: str, profile: DietProfile
    ) -> LabelAnalysis:
        from google.genai import errors, types

        prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
            profile=profile.model_dump_json()
        )
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LabelAnalysis,
                ),
            )
        except errors.APIError as exc:
            raise RuntimeError(
                f"Gemini request failed ({exc.code}): {exc.message}"
            ) from exc

        if not response.text:
            raise RuntimeError("Gemini returned an empty analysis")
        try:
            response_data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned malformed JSON") from exc
        try:
            return LabelAnalysis.model_validate(response_data)
        except ValueError as exc:
            raise RuntimeError(
                f"Gemini returned analysis that does not match the schema: {exc}"
            ) from exc
