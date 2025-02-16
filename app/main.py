from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import triggers, events
from app.services.database import Database
from app.services.event_service import EventService
from app.utils.scheduler import setup_scheduler
from app.middleware.error_handler import error_handler, validation_error_handler
from app.middleware.logging import logging_middleware
from app.utils.logger import logger
from app.config import settings
import logging

app = FastAPI(
    title="Event Trigger Platform API",
    description="API for managing event triggers and their executions",
    version="1.0.0"
)

# Add middleware
app.middleware("http")(error_handler)
app.middleware("http")(logging_middleware)
app.add_exception_handler(RequestValidationError, validation_error_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    triggers.router,
    prefix="/api/v1/triggers",
    tags=["triggers"]
)
app.include_router(
    events.router,
    prefix="/api/v1/events",
    tags=["events"]
)

@app.on_event("startup")
async def startup_event():
    try:
        await Database.connect_db()
        await Database.setup_indexes()
        await EventService.setup_change_stream()
        await setup_scheduler()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await Database.close_db()
        logger.info("Application shutdown successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

@app.get("/health")
async def health_check():
    """Check application health"""
    try:
        db = Database.get_db()
        if not db:
            await Database.connect_db()
            db = Database.get_db()
        await db.command("ping")
        return {
            "status": "healthy", 
            "database": "connected",
            "database_name": settings.DATABASE_NAME
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "unhealthy", "error": str(e)} 