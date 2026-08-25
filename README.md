# TuReel

Generador automático de vídeos cortos para YouTube, TikTok y Shorts. Escribes un guion, eliges el formato y TuReel monta el vídeo final: clips de stock, narración por voz, subtítulos quemados y música de fondo opcional.

Sin suscripciones ni APIs de IA de pago: la voz se sintetiza con Edge TTS y los clips vienen del banco gratuito de Pexels.

## Cómo funciona

El guion se divide en escenas. Para cada una, el sistema busca un clip que encaje, genera la narración, calcula los tiempos de los subtítulos y compone el resultado con FFmpeg en un único MP4 listo para publicar.

**1. Parseo del guion** en escenas independientes.

**2. Clips de stock** — búsqueda y descarga vía Pexels API.

**3. Narración** — síntesis de voz con selector de voces (Edge TTS).

**4. Subtítulos** — generación y sincronización con el audio.

**5. Ensamblaje** — composición final con FFmpeg: orientación vertical u horizontal, música de fondo opcional, hasta 10 minutos de duración.

## Stack

**Backend** · Python · FastAPI · FFmpeg · Edge TTS · Pexels API

**Frontend** · Next.js

## Puesta en marcha

Requisitos: Python 3.10 o superior, FFmpeg instalado en el sistema y una API key gratuita de Pexels.

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

La API queda disponible en `http://localhost:8000`, con las rutas bajo `/api`.

## Estado

Proyecto personal. Este repositorio publica el backend; el frontend se mantiene aparte.
