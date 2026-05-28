# Skill: rest-api

## Propósito
Convenciones para implementar y consumir APIs REST en TuReel: el endpoint FastAPI del backend y las llamadas desde el frontend Next.js.

## Cuándo usar esta skill
- Añadir un nuevo endpoint en FastAPI
- Implementar una llamada fetch desde Next.js al backend
- Gestionar errores HTTP entre frontend y backend

## Backend — FastAPI

### Estructura de un endpoint

```python
# routes/generate.py
from fastapi import APIRouter, HTTPException
from models.schemas import GenerateRequest, GenerateResponse

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_video(request: GenerateRequest):
    try:
        # lógica del pipeline
        ...
        return GenerateResponse(...)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Schemas Pydantic

```python
# models/schemas.py
from pydantic import BaseModel
from typing import List

class Scene(BaseModel):
    narration: str
    keyword: str

class GenerateRequest(BaseModel):
    idea: str

class GenerateResponse(BaseModel):
    video_path: str
    scenes: List[Scene]
```

### CORS (para Next.js en localhost:3000)

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

## Frontend — fetch desde Next.js

```ts
// Llamada al backend con manejo de errores
async function generateVideo(idea: string) {
  const res = await fetch('http://localhost:8000/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idea }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'Error desconocido');
  }

  return res.json(); // { video_path: string, scenes: Scene[] }
}
```

## Reintentos con backoff (para servicios externos desde Python)

```python
import asyncio

async def with_retry(coro_fn, max_attempts=3, base_delay=1.0):
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_fn()
        except Exception as e:
            if attempt == max_attempts:
                raise
            await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
```

## Checklist antes de añadir un endpoint
- [ ] Response model tipado con Pydantic
- [ ] HTTPException con mensaje descriptivo en cada `except`
- [ ] CORS configurado para el origen del frontend
- [ ] Las API keys no aparecen en ninguna respuesta ni log
