import json

from fastapi.testclient import TestClient

from app.main import app, get_analyzer
from app.models import LabelAnalysis


class FakeAnalyzer:
    def analyze(self, image_bytes: bytes, mime_type: str, profile):
        assert image_bytes == b"image"
        assert mime_type == "image/jpeg"
        assert profile.allergens == ["milk"]
        return LabelAnalysis(
            readable=True,
            confidence="high",
            product_name="Biscotti",
            ingredients_it=["farina di frumento", "latte"],
            ingredients_en=["wheat flour", "milk"],
            allergens_detected=["milk"],
            verdict="AVOID",
            reasons=["Milk is in the ingredient list."],
            vocab=[
                {"it": "latte", "en": "milk"},
                {"it": "farina", "en": "flour"},
                {"it": "contiene", "en": "contains"},
            ],
            staff_phrase={"it": "Contiene latte?", "en": "Does it contain milk?"},
        )


app.dependency_overrides[get_analyzer] = lambda: FakeAnalyzer()
client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_label_returns_structured_result() -> None:
    profile = {"dietary_choices": ["vegetarian"], "allergens": ["milk"], "goals": []}
    response = client.post(
        "/api/v1/analyze",
        files={
            "image": ("label.jpg", b"image", "image/jpeg"),
            "profile": (None, json.dumps(profile)),
        },
    )
    assert response.status_code == 200
    assert response.json()["verdict"] == "AVOID"
    assert response.json()["safety_notice"].startswith("Check the physical package")


def test_analyze_rejects_non_image() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={
            "image": ("label.txt", b"image", "text/plain"),
            "profile": (None, "{}"),
        },
    )
    assert response.status_code == 415


def test_safety_notice_is_fixed_and_unreadable_labels_prompt_retake() -> None:
    result = LabelAnalysis(
        readable=False,
        confidence="low",
        product_name="",
        ingredients_it=[],
        ingredients_en=[],
        allergens_detected=[],
        verdict="CHECK",
        reasons=["Text is not visible."],
        vocab=[
            {"it": "etichetta", "en": "label"},
            {"it": "sfocato", "en": "blurry"},
            {"it": "leggibile", "en": "readable"},
        ],
        staff_phrase={"it": "Può ripetere?", "en": "Can you repeat that?"},
        safety_notice="safe to eat",
    )
    assert result.safety_notice == (
        "Check the physical package if you have an allergy; this is not medical advice."
    )
    assert result.retake_prompt is not None


def test_common_allergen_aliases_are_canonicalized() -> None:
    result = LabelAnalysis(
        readable=True,
        confidence="high",
        product_name="Crackers",
        ingredients_it=["semi di sesamo"],
        ingredients_en=["sesame seeds"],
        allergens_detected=["sesame seeds"],
        verdict="AVOID",
        reasons=["Sesame is visible on the label."],
        vocab=[
            {"it": "sesamo", "en": "sesame"},
            {"it": "semi", "en": "seeds"},
            {"it": "contiene", "en": "contains"},
        ],
        staff_phrase={"it": "Contiene sesamo?", "en": "Does it contain sesame?"},
    )
    assert result.allergens_detected == ["sesame"]
