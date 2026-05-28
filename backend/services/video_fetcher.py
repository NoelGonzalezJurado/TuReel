"""
Busca y descarga clips de vídeo desde la API de Pexels.
"""

import httpx
from pathlib import Path

# Mapeo orientación → parámetro Pexels
_PEXELS_ORIENTATION = {
    "horizontal": "landscape",
    "vertical": "portrait",
}


async def fetch_video(
    keyword: str,
    api_key: str,
    download_dir: Path,
    orientation: str = "horizontal",
) -> Path:
    """
    Busca un vídeo en Pexels por keyword y lo descarga.

    Args:
        keyword: Palabra(s) clave (ej: "mountain sunset")
        api_key: Pexels API key
        download_dir: Directorio donde guardar el archivo descargado
        orientation: "horizontal" (16:9) o "vertical" (9:16)

    Returns:
        Path al archivo MP4 descargado
    """
    pexels_orientation = _PEXELS_ORIENTATION.get(orientation, "landscape")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": api_key},
            params={"query": keyword, "per_page": 5, "orientation": pexels_orientation},
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("videos"):
            # Fallback sin filtro de orientación
            response = await client.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": api_key},
                params={"query": keyword, "per_page": 5},
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("videos"):
            raise ValueError(f"Sin resultados en Pexels para: '{keyword}'")

        video = data["videos"][0]
        video_file = _pick_best_file(video["video_files"], orientation)

        safe_keyword = keyword.replace(" ", "_").replace("/", "_")
        video_path = download_dir / f"{safe_keyword}_{video['id']}.mp4"

        async with client.stream("GET", video_file["link"]) as stream:
            stream.raise_for_status()
            with open(video_path, "wb") as f:
                async for chunk in stream.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

        return video_path


async def fetch_image_url(keyword: str, api_key: str) -> str | None:
    """
    Busca una foto en Pexels y devuelve la URL del thumbnail (medium).
    Usado para el preview antes de generar el vídeo.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": keyword, "per_page": 3, "orientation": "landscape"},
        )
        response.raise_for_status()
        data = response.json()
        photos = data.get("photos", [])
        if not photos:
            return None
        return photos[0]["src"]["medium"]


def _pick_best_file(video_files: list, orientation: str = "horizontal") -> dict:
    """Selecciona el archivo de vídeo más adecuado según orientación."""
    if orientation == "vertical":
        # Para vertical preferimos archivos con height > width
        portrait = [f for f in video_files if f.get("height", 0) > f.get("width", 0)]
        if portrait:
            return max(portrait, key=lambda f: f.get("height", 0))

    # Horizontal: prefiere HD 1280px
    hd = next(
        (f for f in video_files if f.get("quality") == "hd" and f.get("width") == 1280),
        None,
    )
    if hd:
        return hd
    return max(video_files, key=lambda f: f.get("width", 0))
