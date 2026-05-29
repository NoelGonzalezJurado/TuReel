"""
Convierte texto de narración en audio MP3 usando Edge TTS (Microsoft, gratuito).
Captura los eventos WordBoundary para sincronización exacta de subtítulos.
"""

import edge_tts
from pathlib import Path

_DEFAULT_VOICE = "es-ES-AlvaroNeural"
_MAX_CHARS = 5000


async def generate_audio(
    narration: str,
    output_dir: Path,
    voice: str = _DEFAULT_VOICE,
) -> tuple[Path, list[dict]]:
    """
    Genera audio MP3 con Edge TTS y devuelve (audio_path, word_boundaries).
    word_boundaries: lista de {"word", "start", "duration"} en segundos.
    Si no se obtienen boundaries, la lista estará vacía (fallback proporcional).
    """
    if len(narration) > _MAX_CHARS:
        narration = narration[:_MAX_CHARS]

    audio_path = output_dir / "narration.mp3"
    word_boundaries: list[dict] = []

    try:
        communicate = edge_tts.Communicate(narration, voice=voice)
        with open(audio_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "wordboundary"):
                    word_boundaries.append({
                        "word": chunk["text"],
                        "start": chunk["offset"] / 1e7,        # ticks → segundos
                        "duration": chunk["duration"] / 1e7,
                    })
        print(f"[audio_generator] {len(word_boundaries)} word boundaries capturados")
    except Exception as e:
        print(f"[audio_generator] stream() falló ({e}), usando save() sin boundaries")
        word_boundaries = []
        communicate2 = edge_tts.Communicate(narration, voice=voice)
        await communicate2.save(str(audio_path))

    return audio_path, word_boundaries
