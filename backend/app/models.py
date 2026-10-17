from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


EU_ALLERGENS = (
    "cereals containing gluten",
    "crustaceans",
    "eggs",
    "fish",
    "peanuts",
    "soybeans",
    "milk",
    "tree nuts",
    "celery",
    "mustard",
    "sesame",
    "sulphur dioxide and sulphites",
    "lupin",
    "molluscs",
)
_ALLERGEN_ALIASES = {
    "gluten": "cereals containing gluten",
    "cereals containing gluten": "cereals containing gluten",
    "sesame seeds": "sesame",
    "sulphites": "sulphur dioxide and sulphites",
    "sulfites": "sulphur dioxide and sulphites",
    "tree nuts": "tree nuts",
}


def _canonicalize_allergens(values: list[str]) -> list[str]:
    canonical_names = {name.casefold(): name for name in EU_ALLERGENS}
    result = []
    for value in values:
        normalized = value.strip().casefold()
        result.append(
            _ALLERGEN_ALIASES.get(
                normalized, canonical_names.get(normalized, value.strip())
            )
        )
    return result


class DietProfile(BaseModel):
    dietary_choices: list[str] = Field(default_factory=list, max_length=20)
    allergens: list[str] = Field(default_factory=list, max_length=len(EU_ALLERGENS))
    goals: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("allergens")
    @classmethod
    def validate_allergens(cls, values: list[str]) -> list[str]:
        values = _canonicalize_allergens(values)
        invalid = sorted(set(values) - set(EU_ALLERGENS))
        if invalid:
            raise ValueError(
                f"allergens must be selected from the 14 EU allergens; invalid: {invalid}"
            )
        return values


class VocabularyItem(BaseModel):
    it: str
    en: str


class StaffPhrase(BaseModel):
    it: str
    en: str


class LabelAnalysis(BaseModel):
    readable: bool
    confidence: Literal["high", "medium", "low"]
    product_name: str
    ingredients_it: list[str]
    ingredients_en: list[str]
    allergens_detected: list[str]
    verdict: Literal["OK", "CHECK", "AVOID"]
    reasons: list[str]
    vocab: list[VocabularyItem] = Field(min_length=3, max_length=3)
    staff_phrase: StaffPhrase
    safety_notice: str = (
        "Check the physical package if you have an allergy; this is not medical advice."
    )
    retake_prompt: str | None = None

    @field_validator("safety_notice", mode="before")
    @classmethod
    def enforce_safety_notice(cls, _value: str | None) -> str:
        return "Check the physical package if you have an allergy; this is not medical advice."

    @field_validator("allergens_detected")
    @classmethod
    def validate_detected_allergens(cls, values: list[str]) -> list[str]:
        values = _canonicalize_allergens(values)
        invalid = sorted(set(values) - set(EU_ALLERGENS))
        if invalid:
            raise ValueError(f"allergens_detected contains unknown allergens: {invalid}")
        return values

    @model_validator(mode="after")
    def add_retake_prompt(self) -> "LabelAnalysis":
        if not self.readable and not self.retake_prompt:
            self.retake_prompt = (
                "The label is not readable. Please retake the photo with the full label in focus."
            )
        return self


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
