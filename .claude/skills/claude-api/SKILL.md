# Skill: claude-api

## Propósito
Guía para integrar la Anthropic API (Claude) en TuReel desde Python: configuración del cliente, generación de guiones y manejo de errores.

## Cuándo usar esta skill
- Implementar o modificar `services/script_generator.py`
- Añadir un nuevo tipo de llamada a Claude
- Optimizar el uso de tokens en la generación de guiones

## Setup del cliente (Python)

```bash
pip install anthropic
```

```python
# services/script_generator.py
import anthropic

client = anthropic.Anthropic(api_key=api_key)
```

## Llamada básica para generación de guión

```python
import anthropic
import json

def call_claude(api_key: str, system: str, user_message: str, max_tokens: int = 1024) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}]
    )

    return message.content[0].text
```

## Modelos disponibles y cuándo usar cada uno

| Modelo | Cuándo usar |
|---|---|
| `claude-haiku-4-5-20251001` | Generación rápida, guiones simples (menor coste) |
| `claude-sonnet-4-6` | Generación de guiones — balance calidad/coste (default) |
| `claude-opus-4-7` | Solo si Sonnet produce guiones de mala calidad |

## Estimación de tokens para TuReel

```
- System prompt: ~150 tokens
- User message (idea del vídeo): ~20 tokens
- Respuesta JSON con 4 escenas: ~200 tokens
- Total por generación: ~370 tokens
- Coste aproximado con claude-sonnet-4-6: < $0.002 por vídeo
```

## Manejo de errores

| Status | Causa | Acción |
|---|---|---|
| `401` | API key inválida | Propagar como HTTPException 401 |
| `429` | Rate limit | Reintentar con backoff exponencial (máx 3) |
| `500/529` | Servidor Anthropic | Reintentar máx. 2 veces con espera de 5s |

```python
import anthropic

try:
    response = call_claude(...)
except anthropic.AuthenticationError:
    raise ValueError("Anthropic API key inválida")
except anthropic.RateLimitError:
    # reintentar con backoff
    ...
except anthropic.APIError as e:
    raise RuntimeError(f"Error de Claude API: {e.message}")
```

## Reglas de uso
1. La API key llega siempre como parámetro — nunca hardcodeada.
2. Incluir siempre `max_tokens` — 1024 es suficiente para un guión de 4 escenas.
3. La respuesta JSON debe parsearse con try/catch — usar fallback regex si falla.
4. Usar `claude-sonnet-4-6` por defecto — no usar Opus para esta tarea.
