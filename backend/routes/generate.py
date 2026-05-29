import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from config import settings
from models.schemas import GenerateResponse, PreviewRequest, PreviewResponse, PreviewScene
from services import audio_generator, script_parser, subtitle_generator, video_assembler, video_fetcher

router = APIRouter()

OUTPUT_DIR = Path(__file__).parent.parent / "output"
_MAX_DURATION = 600  # 10 minutos

# ── Job store en memoria ──────────────────────────────────────────────────────
# { job_id: { status, step, step_index, total_steps, result, error } }
_jobs: dict[str, dict] = {}

_STEPS = [
    "Procesando guion...",
    "Descargando vídeos...",
    "Generando voz...",
    "Generando subtítulos...",
    "Ensamblando vídeo...",
    "¡Listo!",
]


def _set_step(job_id: str, index: int):
    _jobs[job_id]["step"] = _STEPS[index]
    _jobs[job_id]["step_index"] = index


# ── Voice preview ────────────────────────────────────────────────────────────

class VoicePreviewRequest(BaseModel):
    voice: str

_VOICE_PREVIEW_TEXT = {
    "es": "Hola, esta es una muestra de mi voz para tus vídeos.",
    "en": "Hello, this is a sample of my voice for your videos.",
    "fr": "Bonjour, voici un exemple de ma voix pour vos vidéos.",
    "de": "Hallo, das ist eine Probe meiner Stimme für Ihre Videos.",
    "pt": "Olá, esta é uma amostra da minha voz para os seus vídeos.",
}

@router.post("/preview-voice")
async def preview_voice(request: VoicePreviewRequest):
    import edge_tts, tempfile, io
    lang = request.voice[:2].lower()
    text = _VOICE_PREVIEW_TEXT.get(lang, _VOICE_PREVIEW_TEXT["es"])
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        communicate = edge_tts.Communicate(text, voice=request.voice)
        await communicate.save(str(tmp_path))
        audio_bytes = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")


# ── Preview ───────────────────────────────────────────────────────────────────

@router.post("/preview", response_model=PreviewResponse)
async def preview_script(request: PreviewRequest):
    try:
        scenes = script_parser.parse_script(request.script)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    image_urls = await asyncio.gather(*[
        video_fetcher.fetch_image_url(scene.keyword, settings.pexels_api_key)
        for scene in scenes
    ], return_exceptions=True)

    return PreviewResponse(scenes=[
        PreviewScene(
            narration=scene.narration,
            keyword=scene.keyword,
            image_url=img if isinstance(img, str) else None,
        )
        for scene, img in zip(scenes, image_urls)
    ])


# ── Generate: inicia job y devuelve job_id inmediatamente ────────────────────

@router.post("/generate")
async def generate_video(
    script: str = Form(...),
    keywords: str = Form(""),
    duration_seconds: int = Form(60),
    orientation: str = Form("horizontal"),
    voice: str = Form("es-ES-AlvaroNeural"),
    subtitles_enabled: str = Form("1"),
    subtitle_color: str = Form("&H00FFFFFF"),
    subtitle_size: int = Form(22),
    music: Optional[UploadFile] = File(None),
):
    job_id = str(uuid.uuid4())[:8]
    job_dir = OUTPUT_DIR / "temp" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    duration = max(5, min(duration_seconds, _MAX_DURATION))
    use_subtitles = subtitles_enabled.strip() not in ("0", "false", "")

    music_path: Optional[Path] = None
    if music and music.filename:
        music_path = job_dir / "background_music.mp3"
        music_path.write_bytes(await music.read())

    _jobs[job_id] = {
        "status": "running",
        "step": _STEPS[0],
        "step_index": 0,
        "total_steps": len(_STEPS),
        "result": None,
        "error": None,
    }

    asyncio.create_task(_run_job(
        job_id, script, keywords, duration, orientation, job_dir, music_path,
        voice=voice,
        use_subtitles=use_subtitles,
        subtitle_color=subtitle_color,
        subtitle_size=subtitle_size,
    ))

    return {"job_id": job_id}


async def _run_job(
    job_id: str,
    script: str,
    keywords: str,
    duration: int,
    orientation: str,
    job_dir: Path,
    music_path: Optional[Path],
    voice: str = "es-ES-AlvaroNeural",
    use_subtitles: bool = True,
    subtitle_color: str = "&H00FFFFFF",
    subtitle_size: int = 22,
):
    try:
        import re as _re

        # 1. Parsear guion (solo para narración y subtítulos)
        _set_step(job_id, 0)
        scenes = script_parser.parse_script(script)

        # Keywords para imágenes: los del usuario si los hay, si no auto-extraídos
        if keywords.strip():
            kw_list = [k.strip() for k in _re.split(r"[\n,]+", keywords) if k.strip()]
        else:
            kw_list = [s.keyword for s in scenes]

        print(f"[generate] {len(kw_list)} keywords: {kw_list}")

        # 2. Descargar un clip por keyword
        _set_step(job_id, 1)
        video_paths = await asyncio.gather(*[
            video_fetcher.fetch_video(
                kw, settings.pexels_api_key, job_dir,
                orientation=orientation,
            )
            for kw in kw_list
        ])

        # 3. Generar voz
        _set_step(job_id, 2)
        full_narration = " ".join(scene.narration for scene in scenes)
        audio_path, word_boundaries = await audio_generator.generate_audio(full_narration, job_dir, voice=voice)

        # 4. Subtítulos
        _set_step(job_id, 3)
        srt_path = job_dir / f"{job_id}.srt"
        if use_subtitles:
            subtitle_generator.generate_srt(scenes, audio_path, srt_path, word_boundaries=word_boundaries)

        # 5. Ensamblar
        _set_step(job_id, 4)
        output_path = OUTPUT_DIR / f"{job_id}.mp4"
        await video_assembler.assemble_video(
            list(video_paths), audio_path, job_dir, output_path,
            srt_path=srt_path if (use_subtitles and srt_path.exists()) else None,
            max_duration=duration,
            orientation=orientation,
            music_path=music_path,
            subtitle_color=subtitle_color,
            subtitle_size=subtitle_size,
        )

        srt_output = OUTPUT_DIR / f"{job_id}.srt"
        if srt_path.exists():
            shutil.copy2(str(srt_path), str(srt_output))

        # 6. Listo
        _set_step(job_id, 5)
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["result"] = {
            "video_path": str(output_path),
            "video_url": f"http://localhost:8000/api/video/{job_id}.mp4",
            "subtitle_url": f"http://localhost:8000/api/video/{job_id}.srt" if srt_output.exists() else None,
            "scenes": [{"narration": s.narration, "keyword": s.keyword} for s in scenes],
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(e)


# ── Status polling ────────────────────────────────────────────────────────────

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


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
