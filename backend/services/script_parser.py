"""
Convierte el guion aportado por el usuario en escenas para TuReel.

Estrategia:
  - Divide el guion en párrafos (líneas en blanco como separador).
  - Cada párrafo → una escena con su narración completa.
  - El keyword para Pexels se extrae automáticamente: toma las primeras
    palabras sustantivas del párrafo filtrando stopwords en español.
  - Si el guion tiene un solo bloque (sin párrafos), se divide en trozos
    de N palabras para tener al menos 2 escenas.
"""

import re
from typing import List
from models.schemas import Scene

# Máx. palabras por escena cuando no hay párrafos
_WORDS_PER_CHUNK = 40

# Stopwords básicas en español para extraer keywords
_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "a", "en", "con", "por", "para", "que",
    "es", "son", "está", "están", "fue", "ser", "se", "su", "sus",
    "y", "o", "pero", "como", "más", "muy", "ya", "no", "si",
    "lo", "le", "les", "me", "te", "nos", "yo", "tú", "él", "ella",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "también", "así", "tanto", "cada", "todo", "toda", "todos", "todas",
    "donde", "cuando", "porque", "aunque", "sino", "ni", "e", "u",
    "hay", "han", "has", "he", "hemos", "había", "tienen", "tiene",
    "pueden", "puede", "deben", "debe", "hace", "hacen",
}


def parse_script(script: str) -> List[Scene]:
    """
    Convierte el texto del guion en una lista de Scene.

    Args:
        script: Texto libre del usuario. Párrafos separados por líneas en blanco.

    Returns:
        Lista de Scene con narración y keyword para Pexels.

    Raises:
        ValueError: si el guion está vacío.
    """
    script = script.strip()
    if not script:
        raise ValueError("El guion no puede estar vacío.")

    paragraphs = _split_paragraphs(script)

    scenes: List[Scene] = []
    for para in paragraphs:
        keyword = _extract_keyword(para)
        scenes.append(Scene(narration=para, keyword=keyword))

    return scenes


# ── helpers ──────────────────────────────────────────────────────────────────

def _split_paragraphs(text: str) -> List[str]:
    """Divide por líneas en blanco; si no hay, trocea por palabras."""
    # Normalizar saltos de línea
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Dividir por una o más líneas en blanco
    parts = re.split(r"\n{2,}", text)
    # Limpiar y filtrar vacíos
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) >= 2:
        return parts

    # Sin párrafos: trocea por palabras
    words = text.split()
    if len(words) <= _WORDS_PER_CHUNK:
        return [text]

    chunks = []
    for i in range(0, len(words), _WORDS_PER_CHUNK):
        chunk = " ".join(words[i : i + _WORDS_PER_CHUNK])
        chunks.append(chunk)
    return chunks


def _extract_keyword(text: str) -> str:
    """
    Extrae hasta 3 palabras clave en inglés-friendly del párrafo.
    Como el texto está en español, toma los sustantivos más representativos
    (palabras largas, no stopwords) y los devuelve en minúsculas para Pexels.
    """
    # Tokenizar: solo letras
    tokens = re.findall(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{3,}", text)
    # Filtrar stopwords, quedarse con palabras ≥ 4 letras
    candidates = [
        t.lower() for t in tokens
        if t.lower() not in _STOPWORDS and len(t) >= 4
    ]
    # Eliminar duplicados preservando orden
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    # Tomar las 2 primeras palabras candidatas
    keyword_words = unique[:2] if unique else tokens[:2]
    return " ".join(keyword_words) if keyword_words else "nature landscape"
