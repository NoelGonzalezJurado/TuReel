# Skill: documentation

## Propósito
Estándares para documentar el código y las decisiones de arquitectura de TuReel.

## Cuándo usar esta skill
- Documentar un servicio o utilidad nueva
- Escribir o actualizar el README del proyecto
- Registrar una decisión de arquitectura

## Docstrings en servicios Python

```python
async def generate_script(idea: str, api_key: str) -> List[Scene]:
    """
    Genera un guión de 4 escenas usando Claude API.

    Args:
        idea: Tema del vídeo en español (ej: "los volcanes de Islandia")
        api_key: Anthropic API key del usuario

    Returns:
        Lista de 4 Scene con narration (español) y keyword (inglés para Pexels)

    Raises:
        ValueError: Si Claude no devuelve JSON válido tras el fallback
        anthropic.APIError: Si la API key es inválida o hay rate limit
    """
```

## Comentarios inline: solo el POR QUÉ

```python
# ✅ Explica la razón no obvia
# Descargamos en paralelo porque Pexels puede tardar 2-5s por clip
video_paths = await asyncio.gather(*[...])

# ❌ No comenta lo evidente
# Creamos el directorio si no existe
job_dir.mkdir(parents=True, exist_ok=True)
```

## Estructura del README

```markdown
# TuReel

Genera vídeos automáticos con IA: escribe una idea y obtén un MP4 con narración,
clips de stock y montaje automático.

## Stack
- Backend: Python + FastAPI
- Frontend: Next.js 14
- IA: Claude (guión) + ElevenLabs (voz)
- Vídeo: Pexels API + FFmpeg

## Requisitos
- Python 3.11+, Node 18+
- FFmpeg instalado y en PATH
- API keys: Anthropic, Pexels, ElevenLabs

## Instalación
\`\`\`bash
# Backend
cd backend && pip install -r requirements.txt
cp .env.example .env  # Añade tus API keys
uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
\`\`\`

## Variables de entorno (backend/.env)
| Variable | Descripción |
|---|---|
| ANTHROPIC_API_KEY | Claude API key |
| PEXELS_API_KEY | Pexels API key |
| ELEVENLABS_API_KEY | ElevenLabs API key |
| ELEVENLABS_VOICE_ID | ID de voz (default: Rachel) |
```

## ADR (Architecture Decision Records)

Cuando se tome una decisión importante, crear `docs/adr/NNN-titulo.md`:

```markdown
# ADR-001: Backend en Python en lugar de Next.js API routes

## Estado: Aceptado

## Contexto
FFmpeg requiere llamadas a subprocesos del sistema y descarga de archivos binarios.

## Decisión
Backend separado en Python + FastAPI.

## Consecuencias
- ✅ FFmpeg y descarga de vídeos son nativos en Python
- ✅ Separación clara frontend/backend
- ❌ Dos procesos que arrancar en local
```
