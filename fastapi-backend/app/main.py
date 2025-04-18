"""
Main application module.
Initializes FastAPI application with routes and middleware.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import traceback
import asyncio
from typing import Optional

# Import configuration first to ensure environment variables are loaded
from app.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION, ALLOW_ORIGINS,
    configure_logging, MONITORING_ENABLED, MONITOR_INTERVAL_SECONDS,
    monitor_stop_event
)

# Configure logging before any other operations
configure_logging()
logger = logging.getLogger("app.main")

# Database connections
from app.database import connect_to_mongodb, close_mongodb_connection, safe_db_operation

# Now import routers
from app.routes.train import router as train_router
from app.routes.route import router as route_router
from app.routes.alert import router as alert_router
from app.routes.log import router as log_router
from app.api.analytics import router as analytics_router


# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log incoming requests and responses"""
    try:
        logger.info(f"Incoming request method={request.method} url={request.url}")
        
        # Process the request
        response = await call_next(request)
        
        # Log the response
        logger.info(f"Response status={response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error in logging middleware: {str(e)}")
        # Pass through to the main exception handler
        raise

# Add a global exception handler middleware
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """Global exception handler middleware"""
    try:
        return await call_next(request)
    except Exception as e:
        # Log the error with traceback
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a 500 response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."}
        )

# Background tasks
monitoring_task: Optional[asyncio.Task] = None

# Database connection events
@app.on_event("startup")
async def startup_db_client():
    """Connect to MongoDB on application startup"""
    try:
        # First establish database connection
        await connect_to_mongodb()
        logger.info("Database connection established")
        
        # Create database indexes
        from app.database import create_indexes
        await create_indexes()
        logger.info("Database indexes created or verified")
        
        # Start background monitoring tasks if enabled
        global monitoring_task
        if MONITORING_ENABLED:
            # Import here to avoid circular imports
            from app.tasks.monitor import start_monitoring
            
            # Delay monitoring startup to ensure DB connection is ready
            await asyncio.sleep(2)
            
            monitoring_task = asyncio.create_task(
                start_monitoring(interval_seconds=MONITOR_INTERVAL_SECONDS, stop_event=monitor_stop_event)
            )
            logger.info(f"Background monitoring tasks started with interval {MONITOR_INTERVAL_SECONDS}s")
        else:
            logger.info("Background monitoring is disabled by configuration")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Log full traceback for debugging
        logger.error(traceback.format_exc())
        # Allow the app to continue starting up, but in a degraded state
        # This way the API endpoints that don't need DB/monitoring can still work

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on application shutdown"""
    try:
        # Stop monitoring tasks gracefully
        global monitoring_task
        if monitoring_task:
            logger.info("Stopping background monitoring tasks...")
            monitor_stop_event.set()
            try:
                # Wait for a short time for tasks to complete
                await asyncio.wait_for(monitoring_task, timeout=5.0)
                logger.info("Background monitoring tasks stopped successfully")
            except asyncio.TimeoutError:
                logger.warning("Background monitoring tasks did not stop gracefully (timeout)")
            except Exception as e:
                logger.error(f"Error stopping monitoring tasks: {str(e)}")
        
        # Close database connection
        await close_mongodb_connection()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Include routers
app.include_router(train_router, prefix="/api/trains", tags=["Trains"])
app.include_router(route_router, prefix="/api/routes", tags=["Routes"])
app.include_router(alert_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(log_router, prefix="/api/logs", tags=["Logs"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

# Root endpoint
@app.get("/", 
         summary="Health check endpoint", 
         description="Returns a welcome message to confirm the API is running")
async def root():
    """Health check endpoint"""
    return {
        "message": "Welcome to Train Collision Avoidance System API",
        "version": API_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "monitoring_enabled": MONITORING_ENABLED
    }

# Version endpoint
@app.get("/version", 
         summary="API version endpoint", 
         description="Returns the current API version information")
async def version():
    """Return API version information"""
    return {
        "api_version": API_VERSION,
        "title": API_TITLE,
        "monitoring_enabled": MONITORING_ENABLED
    }

# System status endpoint
@app.get("/status", 
         summary="System status endpoint", 
         description="Returns the current system status")
async def status():
    """Get system status"""
    try:
        # Import here to avoid circular imports
        from app.tasks.monitor import generate_system_status_report
        
        status_report = await generate_system_status_report()
        return status_report
    except Exception as e:
        logger.error(f"Error generating status report: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to generate status report",
            "error": str(e)
        }
