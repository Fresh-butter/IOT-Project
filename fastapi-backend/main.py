"""
Entry point for the FastAPI application.
"""
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# Import the app from the app package
try:
    from app.main import app
    logger.info("Application imported successfully")
except Exception as e:
    logger.error(f"Failed to import application: {e}")
    raise

if __name__ == "__main__":
    try:
        import uvicorn
        logger.info("Starting application server")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Failed to start application server: {e}")
        raise
