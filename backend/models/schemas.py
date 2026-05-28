from pydantic import BaseModel
from typing import List, Literal


class Scene(BaseModel):
    narration: str
    keyword: str


class GenerateRequest(BaseModel):
    script: str
    duration_seconds: int = 60  # máximo 180 (3 min)
    orientation: Literal["horizontal", "vertical"] = "horizontal"


class GenerateResponse(BaseModel):
    video_path: str
    video_url: str
    subtitle_url: str | None = None
    scenes: List[Scene]


class PreviewRequest(BaseModel):
    script: str


class PreviewScene(BaseModel):
    narration: str
    keyword: str
    image_url: str | None = None


class PreviewResponse(BaseModel):
    scenes: List[PreviewScene]
