# Skill: error-handling

## Propósito
Estrategia para capturar y comunicar errores en TuReel: errores de las APIs externas (Claude, Pexels, ElevenLabs), errores de FFmpeg y errores de red entre frontend y backend.

## Cuándo usar esta skill
- Añadir manejo de errores a un servicio del backend
- Implementar mensajes de error claros en el frontend
- Depurar fallos del pipeline de generación

## Errores esperados por servicio

| Servicio | Error | Causa | Acción |
|---|---|---|---|
| Claude API | `401` | API key inválida | Mostrar "Anthropic API key incorrecta" |
| Claude API | `429` | Rate limit | Reintentar con backoff exponencial (máx 3) |
| Claude API | JSONDecodeError | Respuesta no parseable | Reintentar con fallback regex |
| Pexels API | `401` | API key inválida | Mostrar "Pexels API key incorrecta" |
| Pexels API | Sin resultados | Keyword sin vídeos | Log warning + usar keyword alternativo |
| ElevenLabs API | `401` | API key inválida | Mostrar "ElevenLabs API key incorrecta" |
| ElevenLabs API | `422` | Texto > 5000 chars | Truncar narración antes de enviar |
| FFmpeg | returncode != 0 | FFmpeg no instalado o fallo | Incluir stderr en el mensaje de error |

## Backend — excepciones en FastAPI

```python
# En routes/generate.py
@router.post("/generate")
async def generate_video(request: GenerateRequest):
    try:
        ...
    except httpx.HTTPStatusError as e:
        service = _identify_service(str(e.request.url))
        raise HTTPException(
            status_code=502,
            detail=f"Error en {service}: HTTP {e.response.status_code}"
        )
    except RuntimeError as e:
        # FFmpeg falló
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

def _identify_service(url: str) -> str:
    if "anthropic" in url: return "Claude API"
    if "pexels" in url: return "Pexels API"
    if "elevenlabs" in url: return "ElevenLabs API"
    return "servicio externo"
```

## Backend — reintentos para APIs externas

```python
async def with_retry(fn, max_attempts=3, base_delay=1.0):
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_attempts:
                await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
                continue
            raise
```

## Frontend — mostrar errores al usuario

```tsx
// En page.tsx
const [error, setError] = useState<string | null>(null);

async function handleGenerate(idea: string) {
  setError(null);
  try {
    const data = await generateVideo(idea);
    setResult(data);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Error desconocido');
  }
}

// En el JSX
{error && (
  <div className="bg-red-950 border border-red-800 rounded-lg p-4">
    <p className="text-red-400 text-sm">{error}</p>
  </div>
)}
```

## Reglas
1. Nunca mostrar stack traces ni variables internas al usuario.
2. Identificar siempre qué servicio falló (Claude, Pexels, ElevenLabs, FFmpeg).
3. Los errores de FFmpeg deben incluir el stderr para facilitar la depuración local.
4. Las API keys nunca aparecen en logs ni en mensajes de error.
