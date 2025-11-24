"""
Test script to verify the scraping pipeline works end-to-end.
"""
import logging
from datetime import datetime, timedelta
from scraper.scraper import NYISOScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_scrape():
    """Test scraping a single data source for today."""
    logger.info("Testing single data source scrape...")
    
    scraper = NYISOScraper()
    try:
        # Test with a known working data source (P-24A: Real-Time Zonal LBMP)
        yesterday = datetime.now() - timedelta(days=1)
        job = scraper.scrape_date(yesterday, report_code='P-24A', force=False)
        
        if job:
            logger.info(f"✓ Scrape completed: {job.status}")
            logger.info(f"  Rows scraped: {job.rows_scraped}")
            logger.info(f"  Rows inserted: {job.rows_inserted}")
            logger.info(f"  Rows updated: {job.rows_updated}")
            if job.error_message:
                logger.warning(f"  Error: {job.error_message}")
            return job.status == 'completed'
        else:
            logger.error("✗ Scrape failed: No job created")
            return False
    except Exception as e:
        logger.exception(f"✗ Test failed with exception: {str(e)}")
        return False
    finally:
        scraper.close()


def test_config_loading():
    """Test configuration loading."""
    logger.info("Testing configuration loading...")
    
    from config.url_config import URLConfigLoader
    
    loader = URLConfigLoader()
    configs = loader.get_all_configs()
    
    logger.info(f"✓ Loaded {len(configs)} configurations")
    for config in configs:
        logger.info(f"  - {config.report_code}: {config.data_type}")
    
    return len(configs) > 0


def test_database_init():
    """Test database initialization."""
    logger.info("Testing database initialization...")
    
    from database.schema import init_database, get_session, DataSource
    
    try:
        engine = init_database()
        session = get_session()
        
        # Check if data sources are synced
        count = session.query(DataSource).count()
        logger.info(f"✓ Database initialized with {count} data sources")
        
        session.close()
        return True
    except Exception as e:
        logger.exception(f"✗ Database initialization failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("NYISO Pipeline Test Suite")
    logger.info("=" * 80)
    
    results = []
    
    # Test 1: Configuration loading
    results.append(("Configuration Loading", test_config_loading()))
    
    # Test 2: Database initialization
    results.append(("Database Initialization", test_database_init()))
    
    # Test 3: Single scrape
    results.append(("Single Data Source Scrape", test_single_scrape()))
    
    # Summary
    logger.info("=" * 80)
    logger.info("Test Results Summary")
    logger.info("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    logger.info("=" * 80)
    if all_passed:
        logger.info("✓ All tests passed!")
    else:
        logger.warning("✗ Some tests failed")
    logger.info("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

