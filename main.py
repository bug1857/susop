from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.routers import auth, organizations, workspaces, projects, audit, ingestion, process, conformance, esg, copilot, brsr, recommendation, green_rerouting, process_optimization, ocel, object_conformance, object_carbon, object_interaction, object_simulation, ocel_interoperability, carbon_fitness, sustainability_conformance, sustainability_digital_twin, benchmarking
from app.routers import settings as settings_router
from app.routers import reports
from app.services.audit_retention_service import run_retention_cleanup

logger = logging.getLogger(__name__)

# Initialize database tables locally on startup for speed
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context.
    On startup: run the 90-day audit log retention sweep (non-blocking).
    """
    db = SessionLocal()
    try:
        result = run_retention_cleanup(db)
        logger.info(f"[Startup] Audit retention sweep complete: {result}")
    except Exception as exc:
        logger.warning(f"[Startup] Audit retention sweep failed (non-critical): {exc}")
    finally:
        db.close()
    yield  # Application runs here


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(workspaces.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(conformance.router, prefix="/api")
app.include_router(esg.router, prefix="/api/v1")
app.include_router(copilot.router, prefix="/api/v1")
app.include_router(brsr.router, prefix="/api/v1")
app.include_router(recommendation.router, prefix="/api/v1")
app.include_router(green_rerouting.router, prefix="/api/v1")
app.include_router(process_optimization.router, prefix="/api/v1")
app.include_router(ocel.router, prefix="/api/v1")
app.include_router(object_conformance.router, prefix="/api/v1")
app.include_router(object_carbon.router, prefix="/api/v1")
app.include_router(object_interaction.router, prefix="/api/v1")
app.include_router(object_simulation.router, prefix="/api/v1")
app.include_router(ocel_interoperability.router, prefix="/api/v1")
app.include_router(carbon_fitness.router, prefix="/api/v1")
app.include_router(sustainability_conformance.router, prefix="/api/v1")
app.include_router(sustainability_digital_twin.router, prefix="/api/v1")
app.include_router(benchmarking.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "SustainOCPM API Online"}
