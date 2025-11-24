"""
Production scraper with enhanced error handling and logging.
"""
import logging
import sys
from pathlib import Path
from scraper.scheduler import NYISOScheduler

# Production logging setup
SCRIPT_DIR = Path(__file__).parent
LOG_DIR = SCRIPT_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / 'scraper.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for production scraper."""
    logger.info("=" * 80)
    logger.info("Starting NYISO Scraper (Production Mode)")
    logger.info("=" * 80)
    
    scheduler = NYISOScheduler()
    
    try:
        scheduler.start(run_immediately=True)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        scheduler.stop()
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error in scraper: {e}")
        scheduler.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()

