"""
FastAPI application entry point.

Run locally with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Deployed to Render via render.yaml at the repo root of the backend folder.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.convert import router as convert_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Saree-to-Jacquard BMP Converter",
    description=(
        "Converts saree design images into weaving-ready jacquard shuttle "
        "BMPs. Each shuttle is exported as a 24-bit BMP where black pixels "
        "indicate the thread is active."
    ),
    version="1.0.0",
)


# ---- CORS ----
# Comma-separated list of allowed origins. In dev: http://localhost:5173 (Vite).
# In production: the Vercel frontend URL.
_default_origins = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
_origins_env = os.environ.get("ALLOWED_ORIGINS", _default_origins)
allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
logger.info("CORS allowed origins: %s", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # we don't use cookies/auth
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Palette-Metadata", "Content-Disposition"],
)


# ---- Routes ----
app.include_router(convert_router, prefix="/api", tags=["conversion"])


@app.get("/", tags=["health"])
async def root():
    """Simple liveness check."""
    return {"service": "saree-jacquard-converter", "status": "ok"}


@app.get("/api/health", tags=["health"])
async def health():
    """Readiness check for the deploy platform."""
    return {"status": "ok"}
