from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db.client import prisma
from src.ehrbase.client import ehrbase_client
from src.encounters.router import router as encounters_router
from src.observations.router import router as observations_router
from src.patients.router import router as patients_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await prisma.connect()
    yield
    # Shutdown
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
    return {"status": "healthy"}
