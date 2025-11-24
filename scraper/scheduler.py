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
from database.schema import WeatherForecast, get_session

logger = logging.getLogger(__name__)


class NYISOScheduler:
    """Schedules scraping jobs based on update frequencies."""
    
    def __init__(self, scraper: Optional[NYISOScraper] = None):
        """Initialize scheduler."""
        self.scraper = scraper or NYISOScraper()
        self.config_loader = URLConfigLoader()
        self.running = False
        # Track last NYISO weather scrape attempt time (P-7A)
        self.last_nyiso_weather_attempt: Optional[datetime] = None
    
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
                # For weather data (P-7A), use conditional scheduling - only if Open Meteo unavailable
                # For other sources, use hourly
                if config.report_code == 'P-7A':
                    schedule.every().hour.do(
                        self._scrape_nyiso_weather_wrapper,
                        config.report_code
                    )
                    logger.info(f"Scheduled {config.report_code} hourly (conditional - only if Open Meteo unavailable)")
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
    
    def _has_recent_openmeteo_data(self, hours: int = 2) -> bool:
        """
        Check if Open Meteo data exists in the database within the last N hours.
        
        Args:
            hours: Number of hours to look back (default: 2 hours)
            
        Returns:
            True if recent Open Meteo data exists, False otherwise
        """
        try:
            db = get_session()
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                count = db.query(WeatherForecast).filter(
                    WeatherForecast.data_source == 'OpenMeteo',
                    WeatherForecast.timestamp >= cutoff_time
                ).count()
                
                has_data = count > 0
                if has_data:
                    logger.debug(f"Found {count} Open Meteo records in last {hours} hours")
                else:
                    logger.debug(f"No Open Meteo data found in last {hours} hours")
                
                return has_data
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Error checking for Open Meteo data: {e}")
            # If we can't check, assume no data (safer to scrape NYISO)
            return False
    
    def _scrape_nyiso_weather_wrapper(self, report_code: str):
        """
        Conditional wrapper for NYISO weather (P-7A) scraping.
        Only attempts if:
        1. Open Meteo data is not available, OR
        2. We haven't attempted in the current hour (max once per hour)
        """
        try:
            now = datetime.utcnow()
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            
            # Check if we've already attempted in this hour
            if self.last_nyiso_weather_attempt and self.last_nyiso_weather_attempt >= current_hour:
                logger.debug(f"Skipping {report_code} - already attempted in current hour")
                return
            
            # Check if Open Meteo data is available
            if self._has_recent_openmeteo_data(hours=2):
                logger.info(f"Skipping {report_code} - Open Meteo data is available (recent data found)")
                # Still mark as attempted to prevent retries within the hour
                self.last_nyiso_weather_attempt = now
                return
            
            # Open Meteo not available - proceed with NYISO scraping
            logger.info(f"Running scheduled scrape for {report_code} (Open Meteo unavailable)")
            self.last_nyiso_weather_attempt = now
            
            # Scrape current hour
            date = datetime.now().replace(minute=0, second=0, microsecond=0)
            job = self.scraper.scrape_date(date, report_code=report_code, force=True)
            
            if job and job.status == 'completed':
                logger.info(f"Successfully scraped {report_code} for {date.date()}")
            else:
                logger.warning(f"Scraping failed for {report_code}: {job.error_message if job else 'No job created'}")
                
        except Exception as e:
            logger.exception(f"Error in scheduled scrape for {report_code}: {str(e)}")
    
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

