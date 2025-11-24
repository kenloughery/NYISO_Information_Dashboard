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
        from scraper.scheduler import NYISOScheduler
        
        logger.info("Starting NYISO scheduler in background thread...")
        scheduler = NYISOScheduler()
        scheduler.start(run_immediately=True)
    except Exception as e:
        logger.exception(f"Error in scheduler thread: {e}")


def main():
    """Main entry point - starts scheduler and FastAPI app."""
    logger.info("=" * 80)
    logger.info("Starting NYISO Dashboard (Production Mode)")
    logger.info("=" * 80)
    
    # Ensure data directory exists and is writable
    data_dir = Path("/app/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify directory is writable
    try:
        test_file = data_dir / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        logger.info(f"Data directory is writable: {data_dir}")
    except Exception as e:
        logger.error(f"Data directory is not writable: {e}")
        raise
    
    # Set database path if not already set
    # For SQLite, we'll use the absolute path directly
    if not os.getenv('DATABASE_URL'):
        db_path = data_dir / "nyiso_data.db"
        # SQLAlchemy SQLite format: sqlite:////absolute/path (4 slashes for absolute)
        # But we need to ensure the path is properly formatted
        # Alternative: use sqlite:/// with absolute path (3 slashes also works for absolute)
        db_path_str = str(db_path.absolute())
        # Try 3 slashes first - SQLAlchemy handles absolute paths with 3 slashes too
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path_str}'
        logger.info(f"Database URL set to: {os.environ['DATABASE_URL']}")
        logger.info(f"Database file path: {db_path_str}")
        logger.info(f"Database file exists: {db_path.exists()}")
        logger.info(f"Database directory exists: {data_dir.exists()}")
        logger.info(f"Database directory permissions: {oct(data_dir.stat().st_mode)}")
    
    # Initialize database before starting scheduler to catch any issues early
    # This ensures the database file and schema exist before the scheduler tries to use it
    try:
        from database.schema import init_database, get_database_url
        logger.info("Initializing database schema...")
        db_url = get_database_url()
        logger.info(f"Database URL: {db_url}")
        
        # Try to create an empty database file first to ensure we can write
        db_file = data_dir / "nyiso_data.db"
        try:
            # Touch the file to ensure it exists and is writable
            db_file.touch(exist_ok=True)
            logger.info(f"Database file created/touched: {db_file}")
        except Exception as touch_error:
            logger.error(f"Failed to create database file: {touch_error}")
            raise
        
        # Now initialize the schema
        init_database()
        logger.info("Database schema initialized successfully")
        
        # Verify database file was created and has content
        if db_file.exists():
            file_size = db_file.stat().st_size
            logger.info(f"Database file exists: {db_file} (size: {file_size} bytes)")
            if file_size == 0:
                logger.warning("Database file is empty - schema creation may have failed")
        else:
            logger.error(f"Database file not found at: {db_file}")
            raise FileNotFoundError(f"Database file was not created at {db_file}")
        
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
    
    # Import and run uvicorn
    # Wrap in try-except to catch any import errors
    try:
        import uvicorn
        from api.main import app
        
        logger.info("FastAPI app imported successfully")
        logger.info("Starting uvicorn server...")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Failed to import required modules. Check dependencies.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

