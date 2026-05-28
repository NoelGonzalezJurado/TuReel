"""
Genera guiones de vídeo usando Claude API.

Devuelve 4 escenas con narración en español y keyword en inglés para Pexels.
"""

import json
import re
import anthropic
from models.schemas import Scene
from typing import List

# version: 1.0.0
_SYSTEM_PROMPT = """Eres un guionista de vídeos cortos.
Dado un tema, genera un guión dividido en exactamente 4 escenas.
Responde SOLO con JSON válido, sin texto adicional, sin markdown.

Formato exacto:
{
  "scenes": [
    {
      "narration": "texto de narración en español (1-2 frases)",
      "keyword": "1-3 palabras en inglés para buscar vídeo de stock"
    }
  ]
}

Reglas:
- La narración debe ser natural y fluida, como un narrador de documental
- El keyword debe describir una imagen visual concreta (evita abstractos como "concept" o "idea")
- Las 4 escenas deben tener coherencia narrativa entre sí"""


async def generate_script(idea: str, api_key: str) -> List[Scene]:
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Tema del vídeo: {idea}"}],
    )

    raw = message.content[0].text
    data = _parse_json(raw)

    scenes = data.get("scenes", [])
    if len(scenes) != 4:
        raise ValueError(f"Se esperaban 4 escenas, Claude devolvió {len(scenes)}")

    return [Scene(**scene) for scene in scenes]


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Claude no devolvió JSON válido: {text[:200]}")
