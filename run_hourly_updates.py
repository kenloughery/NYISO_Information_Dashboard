"""
Hourly update script for NYISO data.
Scrapes all available data sources on an hourly basis.
Can be run as a cron job or service.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

from scraper.scraper import NYISOScraper

# Setup logging
log_file = Path(__file__).parent / 'nyiso_hourly.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_hourly_update():
    """Run hourly update for all data sources."""
    logger.info("=" * 80)
    logger.info("Starting hourly NYISO data update")
    logger.info("=" * 80)
    
    scraper = NYISOScraper()
    
    try:
        # Scrape today's data (will skip already-scraped dates)
        today = datetime.now()
        logger.info(f"Scraping data for {today.date()}")
        
        # Scrape all data sources for today
        jobs = scraper.scrape_recent(days=1)
        
        # Summary
        successful = sum(1 for j in jobs if j and j.status == 'completed')
        failed = sum(1 for j in jobs if j and j.status == 'failed')
        total_inserted = sum(j.rows_inserted for j in jobs if j)
        total_updated = sum(j.rows_updated for j in jobs if j)
        
        logger.info("=" * 80)
        logger.info("Hourly update summary:")
        logger.info(f"  Total jobs: {len(jobs)}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Total rows inserted: {total_inserted:,}")
        logger.info(f"  Total rows updated: {total_updated:,}")
        logger.info("=" * 80)
        
        # Exit with error code if any jobs failed
        if failed > 0:
            logger.warning(f"Some jobs failed. Check logs for details.")
            sys.exit(1)
        
        logger.info("Hourly update completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"Fatal error during hourly update: {str(e)}")
        sys.exit(1)
    finally:
        scraper.close()


if __name__ == "__main__":
    run_hourly_update()

