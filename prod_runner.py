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
    
    # Ensure data directory exists
    data_dir = Path("/app/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set database path if not already set
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///app/data/nyiso_data.db'
    
    # Start scheduler in background daemon thread
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

