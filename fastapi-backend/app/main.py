from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import traceback

from app.database import connect_to_mongodb, close_mongodb_connection
from app.routes.train import router as train_router
from app.routes.route import router as route_router
from app.routes.alert import router as alert_router
from app.routes.log import router as log_router

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI app
app = FastAPI(
    title="Train Collision Avoidance System API",
    description="API for IoT-based Train Collision Avoidance System using GPS and RFID technology",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logging.info(f"Incoming request method={request.method} url={request.url}")
    response = await call_next(request)
    logging.info(f"Response status={response.status_code}")
    return response

# Add a global exception handler middleware
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """Global exception handler middleware"""
    try:
        return await call_next(request)
    except Exception as e:
        # Log the error with traceback
        logging.error(f"Unhandled exception: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Return a 500 response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."}
        )

# Database connection events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongodb()
    logging.info("Database connection established")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongodb_connection()
    logging.info("Database connection closed")


app.include_router(train_router, prefix="/api/trains", tags=["Trains"])
app.include_router(route_router, prefix="/api/routes", tags=["Routes"])
app.include_router(alert_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(log_router, prefix="/api/logs", tags=["Logs"])

@app.get("/", 
         summary="Health check endpoint", 
         description="Returns a welcome message to confirm the API is running")
async def root():
    return {"message": "Welcome to Train Collision Avoidance System API"}
