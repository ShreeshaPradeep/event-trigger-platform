from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.endpoints import triggers, events
from app.services.database import Database
from app.utils.scheduler import setup_scheduler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Event Trigger Platform",
    description="Platform for managing event triggers and their executions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(triggers.router, prefix="/api/v1/triggers", tags=["triggers"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await Database.connect_db()
        await Database.setup_indexes()
        await setup_scheduler()
        logging.info("Application started successfully")
    except Exception as e:
        logging.error(f"Startup error: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await Database.close_db()
        logging.info("Application shutdown complete")
    except Exception as e:
        logging.error(f"Shutdown error: {str(e)}")

@app.get("/health")
async def health_check():
    """Check application health"""
    try:
        db = Database.get_db()
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

