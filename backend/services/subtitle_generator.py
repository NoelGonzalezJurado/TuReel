"""
Genera archivos SRT de subtítulos.

Estrategia preferida: timestamps exactos de Edge TTS (WordBoundary).
Fallback: distribución proporcional por número de caracteres.
"""

import subprocess
import json
from pathlib import Path
from typing import List

_WORDS_PER_BLOCK = 7


def generate_srt(
    scenes,
    audio_path: Path,
    output_path: Path,
    word_boundaries: list[dict] | None = None,
) -> Path:
    if word_boundaries:
        print(f"[subtitle_generator] usando {len(word_boundaries)} word boundaries exactos")
        return _from_boundaries(word_boundaries, output_path)

    print("[subtitle_generator] sin word boundaries — usando timing proporcional")
    return _proportional(scenes, audio_path, output_path)


# ── Estrategia A: word boundaries exactos ─────────────────────────────────────

def _from_boundaries(word_boundaries: list[dict], output_path: Path) -> Path:
    blocks = [
        word_boundaries[i: i + _WORDS_PER_BLOCK]
        for i in range(0, len(word_boundaries), _WORDS_PER_BLOCK)
    ]
    lines: list[str] = []
    for idx, block in enumerate(blocks, 1):
        start = block[0]["start"]
        end = block[-1]["start"] + block[-1]["duration"]
        text = " ".join(w["word"] for w in block)
        lines += [str(idx), f"{_fmt(start)} --> {_fmt(end)}", text, ""]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


# ── Estrategia B: proporcional por caracteres ──────────────────────────────────

def _proportional(scenes, audio_path: Path, output_path: Path) -> Path:
    try:
        total_duration = _get_audio_duration(audio_path)
    except Exception:
        return output_path

    narrations = [s.narration for s in scenes]
    total_chars = sum(len(n) for n in narrations)
    if total_chars == 0:
        return output_path

    entries: list[dict] = []
    t = 0.0
    for narration in narrations:
        ratio = len(narration) / total_chars
        scene_dur = total_duration * ratio
        words = narration.split()
        blocks = [words[i: i + _WORDS_PER_BLOCK] for i in range(0, len(words), _WORDS_PER_BLOCK)]
        total_words = len(words)

        for block_words in blocks:
            block_ratio = len(block_words) / max(total_words, 1)
            block_dur = scene_dur * block_ratio
            entries.append({"start": t, "end": t + block_dur, "text": " ".join(block_words)})
            t += block_dur

    lines: list[str] = []
    for idx, entry in enumerate(entries, 1):
        lines += [str(idx), f"{_fmt(entry['start'])} --> {_fmt(entry['end'])}", entry["text"], ""]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(audio_path)],
        capture_output=True, text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def _fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
