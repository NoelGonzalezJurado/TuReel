from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.generate import router

app = FastAPI(title="TuReel API")  # v4: music upload + preview button

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Asegurar que existen los directorios de salida
Path("output").mkdir(exist_ok=True)
Path("output/temp").mkdir(exist_ok=True)

app.include_router(router, prefix="/api")
