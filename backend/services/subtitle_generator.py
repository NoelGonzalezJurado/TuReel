"""
Genera archivos SRT de subtítulos a partir de las escenas y la duración total del audio.

Estrategia:
  - Usa ffprobe para obtener la duración total del audio.
  - Distribuye el tiempo proporcionalmente al número de caracteres de cada escena.
  - Divide frases largas en bloques de N palabras con timing proporcional.
"""

import subprocess
import json
from pathlib import Path
from typing import List

_WORDS_PER_BLOCK = 7


def generate_srt(scenes, audio_path: Path, output_path: Path) -> Path:
    """
    Genera un SRT sincronizado con el audio.

    Args:
        scenes: Lista de Scene (con atributo .narration)
        audio_path: Ruta al MP3 generado
        output_path: Ruta donde guardar el .srt

    Returns:
        output_path (si pudo generarse) o output_path sin escribir (si falla)
    """
    try:
        total_duration = _get_audio_duration(audio_path)
    except Exception:
        return output_path   # sin subtítulos si ffprobe falla

    narrations = [s.narration for s in scenes]
    total_chars = sum(len(n) for n in narrations)
    if total_chars == 0:
        return output_path

    # Calcular duración de cada escena proporcional a su longitud
    entries: List[dict] = []
    t = 0.0
    for narration in narrations:
        ratio = len(narration) / total_chars
        scene_dur = total_duration * ratio
        words = narration.split()
        blocks = _split_words(words, _WORDS_PER_BLOCK)
        total_words = len(words)

        for block_words in blocks:
            block_ratio = len(block_words) / max(total_words, 1)
            block_dur = scene_dur * block_ratio
            entries.append({
                "start": t,
                "end": t + block_dur,
                "text": " ".join(block_words),
            })
            t += block_dur

    lines: List[str] = []
    for idx, entry in enumerate(entries, 1):
        lines.append(str(idx))
        lines.append(f"{_fmt(entry['start'])} --> {_fmt(entry['end'])}")
        lines.append(entry["text"])
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_audio_duration(audio_path: Path) -> float:
    """Usa ffprobe para obtener la duración en segundos."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def _split_words(words: List[str], n: int) -> List[List[str]]:
    return [words[i : i + n] for i in range(0, len(words), n)]


def _fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
