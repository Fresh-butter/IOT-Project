from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import connect_to_mongodb, close_mongodb_connection
from app.routes.train import router as train_router
from app.routes.route import router as route_router
from app.routes.user import router as user_router
from app.routes.alert import router as alert_router
from app.routes.log import router as log_router

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI app
app = FastAPI(
    title="Train Collision Avoidance System API",
    description="API for IoT-based Train Collision Avoidance System",
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

# Database connection events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongodb()
    logging.info("Database connection established")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongodb_connection()
    logging.info("Database connection closed")

# Include routers
app.include_router(user_router, prefix="/api/users", tags=["Users"])
app.include_router(train_router, prefix="/api/trains", tags=["Trains"])
app.include_router(route_router, prefix="/api/routes", tags=["Routes"])
app.include_router(alert_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(log_router, prefix="/api/logs", tags=["Logs"])

@app.get("/")
async def root():
    return {"message": "Welcome to Train Collision Avoidance System API"}
