# Skill: prompt-engineering

## Propósito
Técnicas para diseñar, iterar y versionar los prompts que TuReel envía a Claude para generar guiones de vídeo estructurados.

## Cuándo usar esta skill
- Diseñar o modificar el prompt en `ia-guion`
- Mejorar la calidad o consistencia de los guiones generados
- Reducir tokens sin perder calidad narrativa

## Principios generales

### 1. System prompt con rol y restricciones claras

```
Eres un guionista de vídeos cortos.
Dado un tema, genera un guión dividido en exactamente 4 escenas.
Responde SOLO con JSON válido, sin texto adicional, sin markdown.
```

### 2. Schema de output explícito en el prompt

```
Formato exacto:
{
  "scenes": [
    {
      "narration": "texto en español (1-2 frases, ~20 palabras)",
      "keyword": "1-3 palabras en inglés para buscar vídeo de stock"
    }
  ]
}
```

### 3. Reglas explícitas para reducir errores

```
Reglas:
- La narración: fluida, estilo documental, en español
- El keyword: imagen visual concreta (evita "concept", "idea", "beauty")
- Las 4 escenas deben tener coherencia narrativa entre sí
- Exactamente 4 escenas, ni más ni menos
```

## Prompt actual del proyecto (v1.0)

```python
# services/script_generator.py — version: 1.0.0
SYSTEM_PROMPT = """Eres un guionista de vídeos cortos.
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
```

## Evaluación de calidad del prompt

| Criterio | Qué verificar |
|---|---|
| **Parseable** | El JSON devuelto es válido en ≥95% de los casos |
| **Correcto** | Siempre devuelve exactamente 4 escenas |
| **Visual** | Los keywords producen resultados útiles en Pexels |
| **Natural** | La narración suena fluida al pasarla por ElevenLabs |

## Optimización de tokens

```python
# El guión es corto — no necesita reducción agresiva
# Estima: ~150 tokens de input + ~200 tokens de output = ~350 tokens por generación
# Coste con claude-sonnet-4-6: ~$0.001 por generación — no optimizar prematuramente
```

## Fallback para JSON mal formado

```python
import re, json

def parse_script_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Claude no devolvió JSON válido: {text[:200]}")
```

## Iteración de versiones

Al modificar el prompt, incrementa la versión en el comentario:
```python
# version: 1.1.0 — Añadida regla de coherencia narrativa entre escenas
# version: 1.2.0 — Cambiado keyword a inglés para mejor cobertura en Pexels
```
