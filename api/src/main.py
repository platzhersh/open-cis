import importlib.metadata
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.auth.router import router as auth_router
from src.cave.router import router as cave_router
from src.config import settings
from src.db.client import prisma
from src.ehrbase.client import ehrbase_client
from src.ehrbase.templates import ensure_templates_registered, warm_web_template_cache
from src.encounters.router import router as encounters_router
from src.errors import (
    CompositionNotFoundError,
    EHRBaseUnavailableError,
    EHRBaseValidationError,
    PatientNotFoundError,
)
from src.observations.router import router as observations_router
from src.patients.router import router as patients_router
from src.system.router import router as system_router
from src.terminology.client import terminology_client
from src.terminology.router import fhir_router as fhir_terminology_router
from src.terminology.router import router as terminology_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:\t%(name)s - %(message)s"
)

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

    # Ensure openEHR templates are registered in EHRBase
    try:
        template_results = await ensure_templates_registered()
        if template_results:
            for template_id, success in template_results.items():
                status = "registered" if success else "FAILED"
                logger.info(f"Template {template_id}: {status}")
    except Exception as e:
        logger.warning(f"Could not ensure templates are registered: {e}")

    # Warm web template cache for FLAT path verification (ADR-0009)
    try:
        await warm_web_template_cache()
    except Exception as e:
        logger.warning(f"Could not warm web template cache: {e}")

    yield
    # Shutdown
    if prisma.is_connected():
        await prisma.disconnect()
    await ehrbase_client.close()
    await terminology_client.close()


try:
    _version = importlib.metadata.version("cis-api")
except importlib.metadata.PackageNotFoundError:
    _version = "0.6.1"

app = FastAPI(
    title="CIS API",
    description="Clinical Information System on openEHR",
    version=_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(patients_router, prefix="/api/patients", tags=["patients"])
app.include_router(encounters_router, prefix="/api/encounters", tags=["encounters"])
app.include_router(observations_router, prefix="/api/observations", tags=["observations"])
app.include_router(cave_router, prefix="/api/cave", tags=["cave"])
app.include_router(system_router, prefix="/api/system", tags=["system"])
app.include_router(terminology_router, prefix="/api/terminology", tags=["terminology"])
app.include_router(fhir_terminology_router, prefix="/api/fhir", tags=["fhir-terminology"])


@app.exception_handler(EHRBaseValidationError)
async def ehrbase_validation_handler(request: Request, exc: EHRBaseValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={
        "error": "validation_error",
        "message": exc.message,
        "details": exc.details,
    })


@app.exception_handler(EHRBaseUnavailableError)
async def ehrbase_unavailable_handler(
    request: Request, exc: EHRBaseUnavailableError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={
        "error": "service_unavailable",
        "message": exc.message,
    })


@app.exception_handler(PatientNotFoundError)
async def patient_not_found_handler(request: Request, exc: PatientNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={
        "error": "not_found",
        "message": exc.message,
    })


@app.exception_handler(CompositionNotFoundError)
async def composition_not_found_handler(
    request: Request, exc: CompositionNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={
        "error": "not_found",
        "message": exc.message,
    })


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={
        "error": "internal_server_error",
        "message": "An unexpected error occurred.",
    })


@app.get("/api/version")
async def get_version() -> dict[str, str]:
    return {"version": app.version}


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
