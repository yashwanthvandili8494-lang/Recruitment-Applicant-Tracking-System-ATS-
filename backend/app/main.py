"""
RecruitFlow ATS — FastAPI Application Entry Point.

Configures CORS, includes API routers, and provides health checks.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 RecruitFlow ATS starting up...")
    logger.info(f"   Environment: {settings.APP_ENV}")
    logger.info(f"   Debug: {settings.DEBUG}")

    # Ensure upload directory exists
    import os
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

    yield

    logger.info("🛑 RecruitFlow ATS shutting down...")


app = FastAPI(
    title="RecruitFlow ATS API",
    description="Recruitment & Applicant Tracking System — REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ───────────────────── CORS ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────── API Routes ─────────────────────
from app.api.v1.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api/v1")


# ───────────────────── Health Checks ─────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic liveness check."""
    return {"status": "healthy", "service": "RecruitFlow ATS"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check — verifies database connectivity."""
    from sqlalchemy import text
    from app.core.database import async_session_factory

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "database": "disconnected"}
