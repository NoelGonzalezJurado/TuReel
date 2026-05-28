"""
Convierte texto de narración en audio MP3 usando Edge TTS (Microsoft, gratuito).
"""

import edge_tts
from pathlib import Path

_DEFAULT_VOICE = "es-ES-AlvaroNeural"
_MAX_CHARS = 5000


async def generate_audio(
    narration: str,
    output_dir: Path,
    voice: str = _DEFAULT_VOICE,
) -> Path:
    """Genera audio MP3 con Edge TTS (gratuito, sin API key) y retorna audio_path."""
    if len(narration) > _MAX_CHARS:
        narration = narration[:_MAX_CHARS]

    audio_path = output_dir / "narration.mp3"
    communicate = edge_tts.Communicate(narration, voice=voice)
    await communicate.save(str(audio_path))
    return audio_path
