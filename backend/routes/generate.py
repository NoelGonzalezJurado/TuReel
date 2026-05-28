import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from config import settings
from models.schemas import GenerateResponse, PreviewRequest, PreviewResponse, PreviewScene
from services import audio_generator, script_parser, subtitle_generator, video_assembler, video_fetcher

router = APIRouter()

OUTPUT_DIR = Path(__file__).parent.parent / "output"
_MAX_DURATION = 180


# ── Preview ───────────────────────────────────────────────────────────────────

@router.post("/preview", response_model=PreviewResponse)
async def preview_script(request: PreviewRequest):
    """Parsea el guion y devuelve thumbnails de Pexels por escena (rápido, sin generar vídeo)."""
    try:
        scenes = script_parser.parse_script(request.script)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    image_urls = await asyncio.gather(*[
        video_fetcher.fetch_image_url(scene.keyword, settings.pexels_api_key)
        for scene in scenes
    ], return_exceptions=True)

    preview_scenes = [
        PreviewScene(
            narration=scene.narration,
            keyword=scene.keyword,
            image_url=img if isinstance(img, str) else None,
        )
        for scene, img in zip(scenes, image_urls)
    ]
    return PreviewResponse(scenes=preview_scenes)


# ── Generate (multipart) ──────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_video(
    script: str = Form(...),
    duration_seconds: int = Form(60),
    orientation: str = Form("horizontal"),
    music: Optional[UploadFile] = File(None),
):
    job_id = str(uuid.uuid4())[:8]
    job_dir = OUTPUT_DIR / "temp" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    duration = max(5, min(duration_seconds, _MAX_DURATION))

    # Guardar música si se subió
    music_path: Optional[Path] = None
    if music and music.filename:
        music_path = job_dir / "background_music.mp3"
        with open(music_path, "wb") as f:
            content = await music.read()
            f.write(content)

    try:
        # 1. Parsear guion
        scenes = script_parser.parse_script(script)

        # 2. Descargar vídeos en paralelo
        video_paths = await asyncio.gather(*[
            video_fetcher.fetch_video(
                scene.keyword, settings.pexels_api_key, job_dir,
                orientation=orientation,
            )
            for scene in scenes
        ])

        # 3. Audio con Edge TTS
        full_narration = " ".join(scene.narration for scene in scenes)
        audio_path = await audio_generator.generate_audio(full_narration, job_dir)

        # 4. Subtítulos
        srt_path = job_dir / f"{job_id}.srt"
        subtitle_generator.generate_srt(scenes, audio_path, srt_path)

        # 5. Montaje FFmpeg
        output_path = OUTPUT_DIR / f"{job_id}.mp4"
        await video_assembler.assemble_video(
            list(video_paths), audio_path, job_dir, output_path,
            srt_path=srt_path if srt_path.exists() else None,
            max_duration=duration,
            orientation=orientation,
            music_path=music_path,
        )

        srt_output = OUTPUT_DIR / f"{job_id}.srt"
        if srt_path.exists():
            shutil.copy2(str(srt_path), str(srt_output))

        video_url = f"http://localhost:8000/api/video/{job_id}.mp4"
        subtitle_url = f"http://localhost:8000/api/video/{job_id}.srt" if srt_output.exists() else None
        return GenerateResponse(
            video_path=str(output_path),
            video_url=video_url,
            subtitle_url=subtitle_url,
            scenes=scenes,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error en Pexels API: HTTP {e.response.status_code}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Servir archivos ───────────────────────────────────────────────────────────

@router.get("/video/{filename}")
async def serve_video(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    if filename.endswith(".mp4"):
        return FileResponse(str(file_path), media_type="video/mp4", filename=filename)
    if filename.endswith(".srt"):
        return FileResponse(str(file_path), media_type="text/plain", filename=filename)
    raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
