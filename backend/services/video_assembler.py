"""
Ensambla clips de vídeo con audio usando FFmpeg.

Pipeline:
  1. Normaliza cada clip a la resolución target (16:9 o 9:16), 30fps, sin audio
  2. Concatena todos los clips normalizados
  3. Muxea narración (+ mezcla música de fondo si se proporcionó)
  4. (Opcional) Quema subtítulos y/o recorta a max_duration
"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional

_RESOLUTIONS = {
    "horizontal": (1280, 720),
    "vertical":   (720, 1280),
}

# Volumen de la música de fondo relativo a la narración
_MUSIC_VOLUME = 0.12  # 12% — audible pero sin tapar la voz


async def assemble_video(
    video_paths: List[Path],
    audio_path: Path,
    temp_dir: Path,
    output_path: Path,
    srt_path: Optional[Path] = None,
    max_duration: Optional[int] = None,
    orientation: str = "horizontal",
    music_path: Optional[Path] = None,
    subtitle_color: str = "&H00FFFFFF",
    subtitle_size: int = 22,
) -> Path:
    w, h = _RESOLUTIONS.get(orientation, (1280, 720))

    # Paso 1: normalizar clips
    normalized = []
    for i, vp in enumerate(video_paths):
        out = temp_dir / f"norm_{i:02d}.mp4"
        await _run_ffmpeg([
            "ffmpeg", "-y", "-i", str(vp),
            "-vf", (
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black"
            ),
            "-r", "30",
            "-c:v", "libx264", "-preset", "fast",
            "-an", str(out),
        ])
        normalized.append(out)

    # Paso 2: concatenar
    concat_file = temp_dir / "filelist.txt"
    concat_file.write_text(
        "\n".join(f"file '{p.absolute()}'" for p in normalized),
        encoding="utf-8",
    )
    merged = temp_dir / "merged.mp4"
    await _run_ffmpeg([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy", str(merged),
    ])

    # Paso 3: muxear audio (narración ± música de fondo)
    # -stream_loop -1 en el vídeo: si los clips son más cortos que el audio, se loopean
    muxed = temp_dir / "muxed.mp4"
    if music_path and music_path.exists():
        await _run_ffmpeg([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(merged),
            "-i", str(audio_path),
            "-i", str(music_path),
            "-filter_complex",
            f"[2:a]volume={_MUSIC_VOLUME},aloop=loop=-1:size=2e+09[music];"
            "[1:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(muxed),
        ])
    else:
        await _run_ffmpeg([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(merged),
            "-i", str(audio_path),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest", str(muxed),
        ])

    # Paso 4: subtítulos + duración
    duration_args = ["-t", str(max_duration)] if max_duration else []

    if srt_path and srt_path.exists():
        srt_escaped = str(srt_path.absolute()).replace("\\", "/").replace(":", "\\:")
        style = (
            f"Fontsize={subtitle_size},PrimaryColour={subtitle_color},"
            "OutlineColour=&H00000000,Outline=2,Shadow=1,Bold=1,"
            "Alignment=2,MarginV=30"
        )
        await _run_ffmpeg([
            "ffmpeg", "-y", "-i", str(muxed),
            *duration_args,
            "-vf", f"subtitles='{srt_escaped}':force_style='{style}'",
            "-c:a", "copy", str(output_path),
        ])
    elif max_duration:
        await _run_ffmpeg([
            "ffmpeg", "-y", "-i", str(muxed),
            *duration_args, "-c", "copy", str(output_path),
        ])
    else:
        import shutil
        shutil.copy2(str(muxed), str(output_path))

    return output_path


async def _run_ffmpeg(cmd: List[str]) -> None:
    await asyncio.to_thread(_run_ffmpeg_sync, cmd)


def _run_ffmpeg_sync(cmd: List[str]) -> None:
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise FileNotFoundError("FFmpeg no encontrado. Instálalo y añádelo al PATH del sistema.")
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg falló (código {result.returncode}):\n{result.stderr.decode()}")
