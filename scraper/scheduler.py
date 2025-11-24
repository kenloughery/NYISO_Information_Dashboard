"""
Scheduler for automated scraping based on update frequencies.
"""
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from scraper.scraper import NYISOScraper
from config.url_config import URLConfigLoader

logger = logging.getLogger(__name__)


class NYISOScheduler:
    """Schedules scraping jobs based on update frequencies."""
    
    def __init__(self, scraper: Optional[NYISOScraper] = None):
        """Initialize scheduler."""
        self.scraper = scraper or NYISOScraper()
        self.config_loader = URLConfigLoader()
        self.running = False
    
    def _schedule_by_frequency(self):
        """Schedule jobs based on update frequencies."""
        configs = self.config_loader.get_all_configs()
        
        for config in configs:
            frequency = config.update_frequency or ''
            frequency_lower = frequency.lower()
            
            # Real-time (5-minute intervals)
            if '5-minute' in frequency_lower or 'real-time' in frequency_lower:
                schedule.every(5).minutes.do(
                    self._scrape_wrapper,
                    config.report_code,
                    'realtime'
                )
                logger.info(f"Scheduled {config.report_code} every 5 minutes")
            
            # Multiple times daily (check BEFORE daily to avoid false matches)
            elif 'multiple times daily' in frequency_lower:
                # For weather data (P-7A), check hourly since it updates multiple times daily
                # For other sources, use 6 hours
                if config.report_code == 'P-7A':
                    schedule.every().hour.do(
                        self._scrape_wrapper,
                        config.report_code,
                        'hourly'
                    )
                    logger.info(f"Scheduled {config.report_code} hourly (weather data)")
                else:
                    # Schedule hourly for other "multiple times daily" sources (user requirement: all data at least hourly)
                    schedule.every().hour.do(
                        self._scrape_wrapper,
                        config.report_code,
                        'hourly'
                    )
                    logger.info(f"Scheduled {config.report_code} hourly (multiple times daily, now hourly per requirement)")
            
            # Hourly
            elif 'hourly' in frequency_lower:
                schedule.every().hour.do(
                    self._scrape_wrapper,
                    config.report_code,
                    'hourly'
                )
                logger.info(f"Scheduled {config.report_code} hourly")
            
            # Daily - schedule hourly to ensure fresh data (user requirement: all data at least hourly)
            elif 'daily' in frequency_lower:
                # Schedule hourly instead of daily to meet requirement
                # Day-ahead market sources still update once per day, but we check hourly
                schedule.every().hour.do(
                    self._scrape_wrapper,
                    config.report_code,
                    'hourly'
                )
                logger.info(f"Scheduled {config.report_code} hourly (was daily, now hourly per requirement)")
        
        # Schedule Open Meteo weather data scraping (hourly)
        schedule.every().hour.do(self._scrape_openmeteo_wrapper)
        logger.info("Scheduled Open Meteo weather data hourly")
    
    def _scrape_wrapper(self, report_code: str, frequency_type: str):
        """Wrapper for scheduled scraping."""
        try:
            logger.info(f"Running scheduled scrape for {report_code} ({frequency_type})")
            
            # Determine date(s) to scrape
            if frequency_type == 'realtime':
                # Scrape today
                date = datetime.now()
                # Force re-scrape for real-time data (updates multiple times per day)
                force = True
            elif frequency_type == 'hourly':
                # Scrape current hour
                date = datetime.now().replace(minute=0, second=0, microsecond=0)
                # Force re-scrape for hourly data (updates multiple times per day)
                force = True
            elif frequency_type == 'multiple_daily':
                # Scrape today
                date = datetime.now()
                # Force re-scrape for sources that update multiple times daily
                force = True
            else:
                # Scrape today (for any other frequency type)
                date = datetime.now()
                # Force re-scrape to ensure fresh data
                force = True
            
            job = self.scraper.scrape_date(date, report_code=report_code, force=force)
            
            if job and job.status == 'completed':
                logger.info(f"Successfully scraped {report_code} for {date.date()}")
            else:
                logger.warning(f"Scraping failed for {report_code}: {job.error_message if job else 'No job created'}")
                
        except Exception as e:
            logger.exception(f"Error in scheduled scrape for {report_code}: {str(e)}")
    
    def _scrape_openmeteo_wrapper(self):
        """Wrapper for Open Meteo weather scraping."""
        try:
            # Check if OpenMeteo API key is configured
            import os
            if not os.getenv('OPENMETEO_API_KEY'):
                logger.warning("OPENMETEO_API_KEY not set, skipping Open Meteo weather scrape")
                return
            
            logger.info("Running scheduled Open Meteo weather scrape")
            date = datetime.now()
            job = self.scraper.scrape_openmeteo_weather(date, force=True)
            
            if job and job.status == 'completed':
                logger.info(f"Successfully scraped Open Meteo weather: {job.rows_inserted} inserted, {job.rows_updated} updated")
            else:
                logger.warning(f"Open Meteo scraping failed: {job.error_message if job else 'No job created'}")
                
        except Exception as e:
            logger.exception(f"Error in Open Meteo scrape: {str(e)}")
    
    def start(self, run_immediately: bool = True):
        """Start the scheduler."""
        self._schedule_by_frequency()
        self.running = True
        
        if run_immediately:
            # Run initial scrape for today
            logger.info("Running initial scrape for today")
            self.scraper.scrape_recent(days=1)
        
        logger.info("Scheduler started")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        self.scraper.close()
        logger.info("Scheduler stopped")
    
    def run_once(self):
        """Run scheduled jobs once (for testing)."""
        schedule.run_all()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run scheduler
    scheduler = NYISOScheduler()
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()

