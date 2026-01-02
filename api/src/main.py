import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.db.client import prisma
from src.ehrbase.client import ehrbase_client
from src.encounters.router import router as encounters_router
from src.observations.router import router as observations_router
from src.patients.router import router as patients_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - attempt database connection but don't fail if unavailable
    logger.info(f"CORS allowed origins: {settings.cors_origins}")
    try:
        await prisma.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
    yield
    # Shutdown
    if prisma.is_connected():
        await prisma.disconnect()
    await ehrbase_client.close()


app = FastAPI(
    title="CIS API",
    description="Clinical Information System on openEHR",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients_router, prefix="/api/patients", tags=["patients"])
app.include_router(encounters_router, prefix="/api/encounters", tags=["encounters"])
app.include_router(observations_router, prefix="/api/observations", tags=["observations"])


@app.get("/health")
async def health_check():
    db_connected = prisma.is_connected()
    status = "healthy" if db_connected else "degraded"
    response_data = {
        "status": status,
        "database": "connected" if db_connected else "disconnected",
    }
    if not db_connected:
        return JSONResponse(status_code=503, content=response_data)
    return response_data
