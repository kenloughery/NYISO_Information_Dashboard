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
    # For SQLite absolute paths, use 4 slashes: sqlite:////absolute/path
    # For relative paths, use 3 slashes: sqlite:///relative/path
    if not os.getenv('DATABASE_URL'):
        db_path = str(data_dir / "nyiso_data.db")
        # Use 4 slashes for absolute path on Unix systems
        os.environ['DATABASE_URL'] = f'sqlite:////{db_path}'
        logger.info(f"Database URL set to: {os.environ['DATABASE_URL']}")
    
    # Initialize database before starting scheduler to catch any issues early
    # This ensures the database file and schema exist before the scheduler tries to use it
    try:
        from database.schema import init_database
        logger.info("Initializing database schema...")
        logger.info(f"Database will be created at: {os.getenv('DATABASE_URL', 'not set')}")
        init_database()
        logger.info("Database schema initialized successfully")
        
        # Verify database file was created
        db_file = data_dir / "nyiso_data.db"
        if db_file.exists():
            logger.info(f"Database file exists: {db_file} (size: {db_file.stat().st_size} bytes)")
        else:
            logger.warning(f"Database file not found at: {db_file}")
        
        # Small delay to ensure database is fully ready
        import time
        time.sleep(0.5)
        
    except Exception as e:
        logger.exception(f"Failed to initialize database: {e}")
        # Don't raise - let the app start and scheduler will retry
    
    # Start scheduler in background daemon thread
    # The scheduler will use the same database connection, so it should work now
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started (daemon mode)")
    
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
    
    # Import and run uvicorn
    import uvicorn
    from api.main import app
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

