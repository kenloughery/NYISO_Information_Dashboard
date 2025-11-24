"""
Main scraper orchestrator that coordinates downloading, parsing, and writing.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from config.url_config import URLConfigLoader, DataSourceConfig
from scraper.downloader import NYISODownloader, DownloadError
from scraper.csv_parser import NYISOCSVParser, CSVParseError
from scraper.db_writer import DatabaseWriter
from scraper.openmeteo_downloader import OpenMeteoDownloader, OpenMeteoDownloadError
from scraper.openmeteo_parser import OpenMeteoParser
from config.weather_locations import get_all_locations
from database.schema import (
    DataSource, ScrapingJob, ScrapingLog, init_database, get_session
)

logger = logging.getLogger(__name__)


class NYISOScraper:
    """Main scraper for NYISO data."""
    
    def __init__(
        self,
        config_loader: Optional[URLConfigLoader] = None,
        downloader: Optional[NYISODownloader] = None,
        parser: Optional[NYISOCSVParser] = None
    ):
        """Initialize scraper components."""
        self.config_loader = config_loader or URLConfigLoader()
        self.downloader = downloader or NYISODownloader()
        self.parser = parser or NYISOCSVParser()
        self.session = get_session()
        
        # Initialize database if needed
        init_database()
        
        # Sync data sources to database
        self._sync_data_sources()
    
    def _sync_data_sources(self):
        """Sync data source configurations to database."""
        configs = self.config_loader.get_all_configs()
        
        for config in configs:
            existing = self.session.query(DataSource).filter(
                DataSource.report_code == config.report_code
            ).first()
            
            if not existing:
                data_source = DataSource(
                    data_type=config.data_type,
                    report_code=config.report_code,
                    dataset_name=config.dataset_name,
                    filename_pattern=config.filename_pattern,
                    direct_csv_url_template=config.direct_csv_url_template,
                    archive_zip_url_template=config.archive_zip_url_template,
                    category=config.category,
                    update_frequency=config.update_frequency,
                    description=config.description
                )
                self.session.add(data_source)
                logger.info(f"Added new data source: {config.report_code}")
            else:
                # Update if changed
                existing.data_type = config.data_type
                existing.dataset_name = config.dataset_name
                existing.filename_pattern = config.filename_pattern
                existing.direct_csv_url_template = config.direct_csv_url_template
                existing.archive_zip_url_template = config.archive_zip_url_template
                existing.category = config.category
                existing.update_frequency = config.update_frequency
                existing.description = config.description
                existing.updated_at = datetime.utcnow()
        
        self.session.commit()
    
    def scrape_date(
        self,
        date: datetime,
        report_code: Optional[str] = None,
        force: bool = False
    ) -> Optional[ScrapingJob]:
        """
        Scrape data for a specific date.
        
        Args:
            date: Date to scrape
            report_code: Specific report code to scrape (None for all)
            force: Force re-scrape even if already exists
            
        Returns:
            ScrapingJob object or None if failed
        """
        configs = [self.config_loader.get_config(report_code)] if report_code else \
                  self.config_loader.get_all_configs()
        
        configs = [c for c in configs if c is not None]
        
        jobs = []
        for config in configs:
            job = self._scrape_single_source(config, date, force)
            if job:
                jobs.append(job)
        
        return jobs[0] if jobs else None
    
    def _scrape_single_source(
        self,
        config: DataSourceConfig,
        date: datetime,
        force: bool = False
    ) -> Optional[ScrapingJob]:
        """Scrape a single data source for a date."""
        # Check if already scraped
        if not force:
            existing_job = self.session.query(ScrapingJob).join(DataSource).filter(
                DataSource.report_code == config.report_code,
                ScrapingJob.target_date == date.replace(hour=0, minute=0, second=0, microsecond=0),
                ScrapingJob.status == 'completed'
            ).first()
            
            if existing_job:
                logger.info(f"Already scraped {config.report_code} for {date.date()}")
                return existing_job
        
        # Get data source from DB
        data_source = self.session.query(DataSource).filter(
            DataSource.report_code == config.report_code
        ).first()
        
        if not data_source:
            logger.error(f"Data source not found in DB: {config.report_code}")
            return None
        
        # Create job
        job = ScrapingJob(
            data_source_id=data_source.id,
            target_date=date.replace(hour=0, minute=0, second=0, microsecond=0),
            status='running',
            started_at=datetime.utcnow()
        )
        self.session.add(job)
        self.session.commit()
        
        try:
            # Build URLs
            direct_url = config.build_url(date, use_archive=False)
            archive_url = config.build_url(date, use_archive=True)
            filename_pattern = config.get_filename_pattern(date)
            
            self._log(job, 'INFO', f"Starting scrape: {direct_url}")
            
            # Download
            csv_content = self.downloader.download_with_fallback(
                direct_url,
                archive_url,
                filename_pattern,
                target_date=date,
                url_template=config.direct_csv_url_template
            )
            
            if not csv_content:
                raise DownloadError(f"Failed to download data for {config.report_code}")
            
            job.rows_scraped = len(csv_content.split('\n')) - 1  # Approximate
            self._log(job, 'INFO', f"Downloaded {job.rows_scraped} rows")
            
            # Parse
            df = self.parser.parse(csv_content, config.data_type)
            records = self.parser.transform_for_database(df, config.data_type, config.report_code)
            
            self._log(job, 'INFO', f"Parsed {len(records)} records")
            
            # Write to database
            writer = DatabaseWriter(self.session)
            inserted, updated = writer.write_records(records, config.report_code, job)
            
            job.rows_inserted = inserted
            job.rows_updated = updated
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            
            self._log(job, 'INFO', f"Completed: {inserted} inserted, {updated} updated")
            
        except DownloadError as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self._log(job, 'ERROR', f"Download failed: {str(e)}")
            logger.error(f"Download failed for {config.report_code}: {str(e)}")
            
        except CSVParseError as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self._log(job, 'ERROR', f"Parse failed: {str(e)}")
            logger.error(f"Parse failed for {config.report_code}: {str(e)}")
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self._log(job, 'ERROR', f"Unexpected error: {str(e)}")
            logger.exception(f"Unexpected error for {config.report_code}")
        
        self.session.commit()
        return job
    
    def _log(self, job: ScrapingJob, level: str, message: str):
        """Add log entry for job."""
        log_entry = ScrapingLog(
            job_id=job.id,
            log_level=level,
            message=message
        )
        self.session.add(log_entry)
        self.session.flush()
        logger.log(getattr(logging, level), f"[Job {job.id}] {message}")
    
    def scrape_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        report_code: Optional[str] = None,
        force: bool = False
    ) -> List[ScrapingJob]:
        """
        Scrape data for a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            report_code: Specific report code to scrape (None for all)
            force: Force re-scrape even if already exists
            
        Returns:
            List of ScrapingJob objects
        """
        jobs = []
        current_date = start_date
        
        while current_date <= end_date:
            job = self.scrape_date(current_date, report_code, force)
            if job:
                jobs.append(job)
            current_date += timedelta(days=1)
        
        return jobs
    
    def scrape_recent(self, days: int = 7, report_code: Optional[str] = None) -> List[ScrapingJob]:
        """
        Scrape recent data.
        
        Args:
            days: Number of recent days to scrape
            report_code: Specific report code to scrape (None for all)
            
        Returns:
            List of ScrapingJob objects
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.scrape_date_range(start_date, end_date, report_code, force=False)
    
    def scrape_openmeteo_weather(
        self,
        date: datetime,
        force: bool = False
    ) -> Optional[ScrapingJob]:
        """
        Scrape weather data from Open Meteo API for all configured locations.
        
        This creates a single ScrapingJob that processes all locations.
        
        Args:
            date: Date to scrape (used for job tracking)
            force: Force re-scrape even if already exists
            
        Returns:
            ScrapingJob object or None if failed
        """
        # Check if OpenMeteo API key is configured
        import os
        if not os.getenv('OPENMETEO_API_KEY'):
            logger.warning("OPENMETEO_API_KEY not set, cannot scrape Open Meteo weather data")
            return None
        # Check if already scraped today
        if not force:
            today = date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Check for existing Open Meteo job today
            existing_job = self.session.query(ScrapingJob).join(DataSource).filter(
                DataSource.report_code == 'OPENMETEO-WEATHER',
                ScrapingJob.target_date == today,
                ScrapingJob.status == 'completed'
            ).first()
            
            if existing_job:
                logger.info(f"Already scraped Open Meteo weather for {date.date()}")
                return existing_job
        
        # Get or create data source
        data_source = self.session.query(DataSource).filter(
            DataSource.report_code == 'OPENMETEO-WEATHER'
        ).first()
        
        if not data_source:
            # Create data source if it doesn't exist
            data_source = DataSource(
                data_type='weather',
                report_code='OPENMETEO-WEATHER',
                dataset_name='openmeteo_weather',
                filename_pattern='openmeteo_weather',
                direct_csv_url_template='https://customer-api.open-meteo.com/v1/forecast',
                archive_zip_url_template='',
                category='Weather',
                update_frequency='hourly',
                description='Open Meteo API weather data (temperature, humidity, irradiance, wind speed)'
            )
            self.session.add(data_source)
            self.session.commit()
        
        # Create job
        job = ScrapingJob(
            data_source_id=data_source.id,
            target_date=date.replace(hour=0, minute=0, second=0, microsecond=0),
            status='running',
            started_at=datetime.utcnow()
        )
        self.session.add(job)
        self.session.commit()
        
        try:
            self._log(job, 'INFO', "Starting Open Meteo weather scrape")
            
            # Initialize Open Meteo components
            downloader = OpenMeteoDownloader()
            parser = OpenMeteoParser()
            writer = DatabaseWriter(self.session)
            
            # Get all locations
            all_locations = get_all_locations()
            total_locations = len(all_locations)
            
            self._log(job, 'INFO', f"Processing {total_locations} locations across all zones")
            
            all_records = []
            successful_locations = 0
            failed_locations = 0
            
            fetch_time = datetime.now()
            
            # Process each location
            for i, loc in enumerate(all_locations, 1):
                zone_code = loc['zone_code']
                location_name = loc['name']
                lat = loc['lat']
                lon = loc['lon']
                
                try:
                    self._log(job, 'INFO', f"Processing location {i}/{total_locations}: {location_name} ({zone_code})")
                    
                    # Download weather data
                    api_response = downloader.download_current_weather(lat, lon, location_name)
                    
                    # Parse response
                    records = parser.parse_weather_response(
                        api_response,
                        location_name,
                        zone_code,
                        lat,
                        lon,
                        fetch_time
                    )
                    
                    all_records.extend(records)
                    successful_locations += 1
                    
                    self._log(job, 'INFO', f"Successfully processed {location_name}: {len(records)} records")
                    
                except OpenMeteoDownloadError as e:
                    failed_locations += 1
                    self._log(job, 'ERROR', f"Failed to download weather for {location_name}: {str(e)}")
                    logger.error(f"Open Meteo download error for {location_name}: {str(e)}")
                    continue
                    
                except Exception as e:
                    failed_locations += 1
                    self._log(job, 'ERROR', f"Error processing {location_name}: {str(e)}")
                    logger.exception(f"Error processing {location_name}")
                    continue
            
            # Write all records to database
            if all_records:
                self._log(job, 'INFO', f"Writing {len(all_records)} records to database")
                inserted, updated = writer.upsert_weather_forecast(all_records)
                
                job.rows_scraped = len(all_records)
                job.rows_inserted = inserted
                job.rows_updated = updated
                
                self._log(job, 'INFO', f"Inserted {inserted} records, updated {updated} records")
            else:
                job.rows_scraped = 0
                job.rows_inserted = 0
                job.rows_updated = 0
                self._log(job, 'WARNING', "No records to write")
            
            # Update job status
            if failed_locations == 0:
                job.status = 'completed'
                self._log(job, 'INFO', f"Successfully scraped {successful_locations} locations")
            elif successful_locations > 0:
                job.status = 'completed'
                self._log(job, 'WARNING', f"Completed with {successful_locations} successful, {failed_locations} failed")
            else:
                job.status = 'failed'
                job.error_message = f"All {failed_locations} locations failed"
                self._log(job, 'ERROR', f"All locations failed")
            
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self._log(job, 'ERROR', f"Unexpected error: {str(e)}")
            logger.exception("Unexpected error in Open Meteo scrape")
        
        self.session.commit()
        return job
    
    def close(self):
        """Close database session."""
        self.session.close()

