import json

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status

from app.config import Settings, get_settings
from app.models import DietProfile, HealthResponse, LabelAnalysis
from app.services.analyzer import GeminiLabelAnalyzer, LabelAnalyzer

app = FastAPI(title="Label Lens API", version="0.1.0")


def get_analyzer(settings: Settings = Depends(get_settings)) -> LabelAnalyzer:
    try:
        return GeminiLabelAnalyzer(settings)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/api/v1/analyze", response_model=LabelAnalysis)
async def analyze_label(
    image: UploadFile = File(...),
    profile: str = Form(...),
    analyzer: LabelAnalyzer = Depends(get_analyzer),
    settings: Settings = Depends(get_settings),
) -> LabelAnalysis:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="image must be an image/* upload")

    try:
        diet_profile = DietProfile.model_validate(json.loads(profile))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="profile must be valid diet-profile JSON") from exc

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="image must not be empty")
    if len(image_bytes) > settings.max_image_bytes:
        raise HTTPException(status_code=413, detail="image exceeds the 10 MB limit")

    try:
        return analyzer.analyze(image_bytes, image.content_type, diet_profile)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

