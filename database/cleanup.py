"""
Database cleanup module for removing old data.
Implements 14-day data retention policy.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from database.schema import (
    RealTimeLBMP, DayAheadLBMP, TimeWeightedLBMP,
    RealTimeLoad, LoadForecast, InterfaceFlow,
    AncillaryService, MarketAdvisory, Constraint,
    ExternalRTOPrice, ATC_TTC, Outage,
    WeatherForecast, FuelMix,
    ScrapingJob, ScrapingLog,
    PageView, VisitorSession
)

logger = logging.getLogger(__name__)


class DataCleanup:
    """Handles cleanup of old data based on retention policy."""
    
    def __init__(self, session: Session, retention_days: int = 14):
        """
        Initialize cleanup handler.
        
        Args:
            session: Database session
            retention_days: Number of days to retain data (default: 14)
        """
        self.session = session
        self.retention_days = retention_days
        self.cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    def cleanup_all(self) -> Dict[str, int]:
        """
        Clean up all old data from all tables.
        
        Returns:
            Dictionary with table names and number of records deleted
        """
        results = {}
        
        logger.info(f"Starting data cleanup - removing data older than {self.retention_days} days (before {self.cutoff_date})")
        
        # Time-series data tables (use timestamp column)
        results.update(self._cleanup_timeseries_table(RealTimeLBMP, 'realtime_lbmp'))
        results.update(self._cleanup_timeseries_table(DayAheadLBMP, 'dayahead_lbmp'))
        results.update(self._cleanup_timeseries_table(TimeWeightedLBMP, 'timeweighted_lbmp'))
        results.update(self._cleanup_timeseries_table(RealTimeLoad, 'realtime_load'))
        results.update(self._cleanup_timeseries_table(LoadForecast, 'load_forecast'))
        results.update(self._cleanup_timeseries_table(InterfaceFlow, 'interface_flows'))
        results.update(self._cleanup_timeseries_table(AncillaryService, 'ancillary_services'))
        results.update(self._cleanup_timeseries_table(MarketAdvisory, 'market_advisories'))
        results.update(self._cleanup_timeseries_table(Constraint, 'constraints'))
        results.update(self._cleanup_timeseries_table(ExternalRTOPrice, 'external_rto_prices'))
        results.update(self._cleanup_timeseries_table(ATC_TTC, 'atc_ttc'))
        results.update(self._cleanup_timeseries_table(Outage, 'outages'))
        results.update(self._cleanup_timeseries_table(FuelMix, 'fuel_mix'))
        
        # Weather forecast (use timestamp, but also check forecast_time for older forecasts)
        results.update(self._cleanup_weather_forecast())
        
        # Scraping jobs (use completed_at or created_at if completed_at is None)
        results.update(self._cleanup_scraping_jobs())
        
        # Scraping logs (use created_at)
        results.update(self._cleanup_scraping_logs())
        
        # Analytics data
        results.update(self._cleanup_analytics())
        
        total_deleted = sum(results.values())
        logger.info(f"Data cleanup completed - deleted {total_deleted} total records across {len(results)} tables")
        
        return results
    
    def _cleanup_timeseries_table(self, model_class, table_name: str) -> Dict[str, int]:
        """
        Clean up old records from a time-series table using timestamp column.
        
        Args:
            model_class: SQLAlchemy model class
            table_name: Name of the table (for logging)
            
        Returns:
            Dictionary with deletion count
        """
        try:
            # Count records to be deleted
            count_query = self.session.query(func.count(model_class.id)).filter(
                model_class.timestamp < self.cutoff_date
            )
            count = count_query.scalar() or 0
            
            if count > 0:
                # Delete old records
                deleted = self.session.query(model_class).filter(
                    model_class.timestamp < self.cutoff_date
                ).delete(synchronize_session=False)
                
                logger.info(f"Deleted {deleted} records from {table_name} (older than {self.retention_days} days)")
                return {table_name: deleted}
            else:
                return {table_name: 0}
                
        except Exception as e:
            logger.error(f"Error cleaning up {table_name}: {str(e)}")
            return {table_name: 0}
    
    def _cleanup_weather_forecast(self) -> Dict[str, int]:
        """
        Clean up old weather forecast data.
        Uses timestamp (weather observation time) for cleanup.
        
        Returns:
            Dictionary with deletion count
        """
        try:
            # Delete records where timestamp is older than cutoff
            deleted = self.session.query(WeatherForecast).filter(
                WeatherForecast.timestamp < self.cutoff_date
            ).delete(synchronize_session=False)
            
            logger.info(f"Deleted {deleted} records from weather_forecast (older than {self.retention_days} days)")
            return {'weather_forecast': deleted}
            
        except Exception as e:
            logger.error(f"Error cleaning up weather_forecast: {str(e)}")
            return {'weather_forecast': 0}
    
    def _cleanup_scraping_jobs(self) -> Dict[str, int]:
        """
        Clean up old scraping jobs.
        Uses completed_at if available, otherwise created_at.
        
        Returns:
            Dictionary with deletion count
        """
        try:
            # Delete jobs that are completed and older than cutoff
            # Use completed_at if available, otherwise use created_at
            deleted = self.session.query(ScrapingJob).filter(
                and_(
                    ScrapingJob.status.in_(['completed', 'failed']),
                    func.coalesce(ScrapingJob.completed_at, ScrapingJob.created_at) < self.cutoff_date
                )
            ).delete(synchronize_session=False)
            
            logger.info(f"Deleted {deleted} records from scraping_jobs (older than {self.retention_days} days)")
            return {'scraping_jobs': deleted}
            
        except Exception as e:
            logger.error(f"Error cleaning up scraping_jobs: {str(e)}")
            return {'scraping_jobs': 0}
    
    def _cleanup_scraping_logs(self) -> Dict[str, int]:
        """
        Clean up old scraping logs.
        Uses created_at for cleanup.
        
        Returns:
            Dictionary with deletion count
        """
        try:
            # Delete logs older than cutoff
            deleted = self.session.query(ScrapingLog).filter(
                ScrapingLog.created_at < self.cutoff_date
            ).delete(synchronize_session=False)
            
            logger.info(f"Deleted {deleted} records from scraping_logs (older than {self.retention_days} days)")
            return {'scraping_logs': deleted}
            
        except Exception as e:
            logger.error(f"Error cleaning up scraping_logs: {str(e)}")
            return {'scraping_logs': 0}
    
    def _cleanup_analytics(self) -> Dict[str, int]:
        """
        Clean up old analytics data (page views and visitor sessions).
        
        Returns:
            Dictionary with deletion counts
        """
        results = {}
        
        try:
            # Clean up page views
            page_views_deleted = self.session.query(PageView).filter(
                PageView.created_at < self.cutoff_date
            ).delete(synchronize_session=False)
            
            logger.info(f"Deleted {page_views_deleted} records from page_views (older than {self.retention_days} days)")
            results['page_views'] = page_views_deleted
            
            # Clean up visitor sessions (use last_visit)
            sessions_deleted = self.session.query(VisitorSession).filter(
                VisitorSession.last_visit < self.cutoff_date
            ).delete(synchronize_session=False)
            
            logger.info(f"Deleted {sessions_deleted} records from visitor_sessions (older than {self.retention_days} days)")
            results['visitor_sessions'] = sessions_deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up analytics data: {str(e)}")
            results['page_views'] = 0
            results['visitor_sessions'] = 0
        
        return results


def cleanup_old_data(session: Session, retention_days: int = 14) -> Dict[str, int]:
    """
    Convenience function to clean up old data.
    
    Args:
        session: Database session
        retention_days: Number of days to retain data (default: 14)
        
    Returns:
        Dictionary with table names and deletion counts
    """
    cleanup = DataCleanup(session, retention_days)
    return cleanup.cleanup_all()

