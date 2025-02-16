from fastapi import FastAPI, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.routers import triggers, events
from app.services.database import Database
from app.services.event_service import EventService
from app.utils.scheduler import setup_scheduler
from app.middleware.error_handler import error_handler, validation_error_handler
from app.middleware.logging import logging_middleware
from app.utils.logger import logger  # Import logger
from app.config import settings  # Import settings to verify MongoDB URL
import logging
from fastapi.responses import FileResponse

# Add this line to debug the MongoDB URL
logging.info(f"Using MongoDB URL: {settings.MONGODB_URL}")

app = FastAPI(
    title="Event Trigger Platform",
    description="Platform for managing event triggers and their executions",
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

# Add logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    try:
        # Connect to database
        await Database.connect_db()
        
        # Setup indexes
        await Database.setup_indexes()
        
        # Setup event change stream
        await EventService.setup_change_stream()
        
        # Initialize scheduler
        await setup_scheduler()
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

# Shutdown event
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
        # Print connection details (remove in production)
        logging.info(f"Attempting to connect to: {settings.MONGODB_URL}")
        
        db = Database.get_db()
        if not db:
            # Try to connect if not already connected
            await Database.connect_db()
            db = Database.get_db()
            
        await db.command("ping")
        return {
            "status": "healthy", 
            "database": "connected",
            "database_name": settings.DATABASE_NAME
        }
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/execute-triggers")
async def execute_triggers_page():
    return FileResponse("app/templates/execute-triggers.html")

@app.get("/update-triggers")
async def update_triggers_page():
    return FileResponse("app/templates/update-triggers.html") 