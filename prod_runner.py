"""
Production entrypoint script for Railway deployment.
Starts the scheduler in a background thread and runs the FastAPI app.
"""
import os
import sys
import threading
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_scheduler():
    """Run the scheduler in a background thread."""
    try:
        import time
        # Delay scheduler start to allow API to bind to port and pass health checks
        # This prevents resource contention during startup (CPU/SQLite locks)
        logger.info("Waiting 30s before starting scheduler to allow API startup...")
        time.sleep(30)
        
        from scraper.scheduler import NYISOScheduler
        
        logger.info("Starting NYISO scheduler in background thread...")
        scheduler = NYISOScheduler()
        # Run immediately=True scrapes recent data, which is heavy
        # We've delayed start, so API should be up now.
        scheduler.start(run_immediately=True)
    except Exception as e:
        logger.exception(f"Error in scheduler thread: {e}")


def validate_environment():
    """Validate required environment variables and log warnings if missing."""
    import os
    warnings = []
    errors = []
    
    # Check for Open Meteo API key (required for weather data)
    openmeteo_key = os.getenv('OPENMETEO_API_KEY')
    if not openmeteo_key:
        warnings.append(
            "⚠️  OPENMETEO_API_KEY not set - Open Meteo weather data will not be collected.\n"
            "   To fix: Set OPENMETEO_API_KEY in Railway dashboard → Variables\n"
            "   API Key: MZHzyrTuNWt9Bsh5"
        )
    else:
        logger.info(f"✅ OPENMETEO_API_KEY is set (length: {len(openmeteo_key)})")
    
    # Log warnings
    if warnings:
        logger.warning("=" * 80)
        logger.warning("ENVIRONMENT VARIABLE WARNINGS:")
        logger.warning("=" * 80)
        for warning in warnings:
            logger.warning(warning)
        logger.warning("=" * 80)
    
    # Log errors (currently none, but structure for future)
    if errors:
        logger.error("=" * 80)
        logger.error("ENVIRONMENT VARIABLE ERRORS:")
        logger.error("=" * 80)
        for error in errors:
            logger.error(error)
        logger.error("=" * 80)
    
    return len(errors) == 0


def main():
    """Main entry point - starts scheduler and FastAPI app."""
    logger.info("=" * 80)
    logger.info("Starting NYISO Dashboard (Production Mode)")
    logger.info("=" * 80)
    
    # Validate environment variables
    validate_environment()
    
    # Database URL will be handled by get_database_url() in schema.py
    # It will try multiple paths and use Railway's DATABASE_URL if set
    # No need to manually set it here - let the schema module handle it
    logger.info("Database configuration will be handled by database.schema.get_database_url()")
    
    # Initialize database before starting scheduler to catch any issues early
    # This ensures the database file and schema exist before the scheduler tries to use it
    try:
        from database.schema import init_database, get_database_url
        logger.info("Initializing database schema...")
        db_url = get_database_url()
        logger.info(f"Database URL: {db_url}")
        
        # Initialize the schema (get_database_url() handles path selection)
        init_database()
        logger.info("Database schema initialized successfully")
        
        # Verify database connection works
        from database.schema import get_session
        try:
            test_session = get_session()
            test_session.close()
            logger.info("Database connection verified successfully")
        except Exception as conn_error:
            logger.warning(f"Database connection test failed: {conn_error}")
            # Don't raise - let it continue, might be a temporary issue
        
        # Small delay to ensure database is fully ready
        import time
        time.sleep(0.5)
        
    except Exception as e:
        logger.exception(f"Failed to initialize database: {e}")
        logger.warning("Database initialization failed, but continuing...")
        logger.warning("The API may not work correctly until database is initialized")
        # Don't raise - let the app start and scheduler will retry
        # This allows the health check endpoint to still respond
    
    # Start scheduler in background daemon thread
    # The scheduler will use the same database connection, so it should work now
    # Don't let scheduler failures prevent the API from starting
    try:
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Scheduler thread started (daemon mode)")
    except Exception as e:
        logger.error(f"Failed to start scheduler thread: {e}")
        logger.warning("Continuing without scheduler - API will still work")
    
    # Get port from environment (Railway sets PORT env var)
    # Railway provides PORT as a string, ensure it's converted to int
    port_str = os.getenv('PORT', '8000')
    try:
        port = int(port_str)
    except (ValueError, TypeError):
        logger.warning(f"Invalid PORT value '{port_str}', defaulting to 8000")
        port = 8000
    
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    logger.info(f"PORT environment variable: {os.getenv('PORT', 'not set')}")
    logger.info(f"HOST environment variable: {os.getenv('HOST', 'not set')}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Import and run uvicorn
    # Wrap in try-except to catch any import errors
    try:
        logger.info("Importing FastAPI app...")
        import uvicorn
        logger.info(f"Uvicorn version: {uvicorn.__version__}")
        
        from api.main import app
        logger.info("FastAPI app imported successfully")
        
        logger.info("Starting uvicorn server...")
        logger.info(f"Server will listen on {host}:{port}")
        logger.info("If you see 'Uvicorn running' below, the server started successfully")
        
        # Use uvicorn.run with minimal settings for Railway
        logger.info("=" * 80)
        logger.info("Starting Uvicorn Server")
        logger.info(f"Host: {host}, Port: {port}")
        logger.info("=" * 80)
        
        # Start uvicorn - use only well-known parameters
        # Note: uvicorn.run() is blocking, so this will run until the server stops
        logger.info("Calling uvicorn.run() - this will block until server stops")
        try:
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=False  # Railway handles access logs
            )
        except Exception as uvicorn_error:
            logger.exception(f"Uvicorn crashed: {uvicorn_error}")
            raise
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Failed to import required modules. Check dependencies.")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error starting server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

