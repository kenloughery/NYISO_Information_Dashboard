"""
Database schema for NYISO data pipeline.
Supports multiple data types with flexible time-series storage.
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    Boolean, Text, ForeignKey, Index, UniqueConstraint
)
import hashlib
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from pathlib import Path
import os

Base = declarative_base()


# ============================================================================
# METADATA TABLES
# ============================================================================

class DataSource(Base):
    """Metadata about available NYISO data sources."""
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True)
    data_type = Column(String(200), nullable=False)
    report_code = Column(String(20), nullable=False, unique=True)
    dataset_name = Column(String(100), nullable=False)
    filename_pattern = Column(String(200), nullable=False)
    direct_csv_url_template = Column(Text, nullable=False)
    archive_zip_url_template = Column(Text, nullable=False)
    category = Column(String(100))
    update_frequency = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    scraping_jobs = relationship("ScrapingJob", back_populates="data_source")


class ScrapingJob(Base):
    """Tracks scraping jobs and their status."""
    __tablename__ = 'scraping_jobs'
    
    id = Column(Integer, primary_key=True)
    data_source_id = Column(Integer, ForeignKey('data_sources.id'), nullable=False)
    target_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    rows_scraped = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    data_source = relationship("DataSource", back_populates="scraping_jobs")
    logs = relationship("ScrapingLog", back_populates="job")
    
    __table_args__ = (
        Index('idx_job_date_status', 'target_date', 'status'),
    )


class ScrapingLog(Base):
    """Detailed logs for scraping operations."""
    __tablename__ = 'scraping_logs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('scraping_jobs.id'), nullable=False)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("ScrapingJob", back_populates="logs")
    
    __table_args__ = (
        Index('idx_log_job_created', 'job_id', 'created_at'),
    )


# ============================================================================
# REFERENCE TABLES
# ============================================================================

class Zone(Base):
    """NYISO zones reference table."""
    __tablename__ = 'zones'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    ptid = Column(Integer, unique=True)
    display_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class Interface(Base):
    """Interface reference table for flows and limits."""
    __tablename__ = 'interfaces'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    point_id = Column(Integer, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# TIME-SERIES DATA TABLES
# ============================================================================

class RealTimeLBMP(Base):
    """Real-time zonal LBMP (5-minute intervals)."""
    __tablename__ = 'realtime_lbmp'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    ptid = Column(Integer)
    lbmp = Column(Float, nullable=False)
    marginal_cost_losses = Column(Float)
    marginal_cost_congestion = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zone = relationship("Zone")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'zone_id', name='uq_realtime_lbmp'),
        Index('idx_realtime_lbmp_timestamp', 'timestamp'),
        Index('idx_realtime_lbmp_zone', 'zone_id'),
    )


class DayAheadLBMP(Base):
    """Day-ahead zonal LBMP (hourly)."""
    __tablename__ = 'dayahead_lbmp'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    ptid = Column(Integer)
    lbmp = Column(Float, nullable=False)
    marginal_cost_losses = Column(Float)
    marginal_cost_congestion = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zone = relationship("Zone")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'zone_id', name='uq_dayahead_lbmp'),
        Index('idx_dayahead_lbmp_timestamp', 'timestamp'),
        Index('idx_dayahead_lbmp_zone', 'zone_id'),
    )


class TimeWeightedLBMP(Base):
    """Time-weighted/integrated real-time LBMP (hourly)."""
    __tablename__ = 'timeweighted_lbmp'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    ptid = Column(Integer)
    lbmp = Column(Float, nullable=False)
    marginal_cost_losses = Column(Float)
    marginal_cost_congestion = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zone = relationship("Zone")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'zone_id', name='uq_timeweighted_lbmp'),
        Index('idx_timeweighted_lbmp_timestamp', 'timestamp'),
    )


class RealTimeLoad(Base):
    """Real-time actual load (5-minute intervals)."""
    __tablename__ = 'realtime_load'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    ptid = Column(Integer)
    load = Column(Float, nullable=False)
    time_zone = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zone = relationship("Zone")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'zone_id', name='uq_realtime_load'),
        Index('idx_realtime_load_timestamp', 'timestamp'),
        Index('idx_realtime_load_zone', 'zone_id'),
    )


class LoadForecast(Base):
    """ISO load forecast (7-day, hourly)."""
    __tablename__ = 'load_forecast'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    forecast_load = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zone = relationship("Zone")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'zone_id', name='uq_load_forecast'),
        Index('idx_load_forecast_timestamp', 'timestamp'),
        Index('idx_load_forecast_zone', 'zone_id'),
    )


class InterfaceFlow(Base):
    """Interface limits and flows (5-minute intervals)."""
    __tablename__ = 'interface_flows'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    interface_id = Column(Integer, ForeignKey('interfaces.id'), nullable=False)
    point_id = Column(Integer)
    flow_mwh = Column(Float, nullable=False)
    positive_limit_mwh = Column(Float)
    negative_limit_mwh = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    interface = relationship("Interface")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'interface_id', name='uq_interface_flow'),
        Index('idx_interface_flow_timestamp', 'timestamp'),
        Index('idx_interface_flow_interface', 'interface_id'),
    )


class AncillaryService(Base):
    """Ancillary service prices (real-time and day-ahead)."""
    __tablename__ = 'ancillary_services'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    market_type = Column(String(20), nullable=False)  # 'realtime' or 'dayahead'
    service_type = Column(String(50))  # regulation, spinning_reserve, non_sync_reserve
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zone = relationship("Zone")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'zone_id', 'market_type', 'service_type', 
                        name='uq_ancillary_service'),
        Index('idx_ancillary_timestamp', 'timestamp'),
        Index('idx_ancillary_zone', 'zone_id'),
    )


# ============================================================================
# NEW DATA SOURCES - ADDITIONAL TABLES
# ============================================================================

class MarketAdvisory(Base):
    """Market advisory notifications and summaries."""
    __tablename__ = 'market_advisories'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    advisory_type = Column(String(100))
    title = Column(String(500))
    message = Column(Text)
    severity = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_advisory_timestamp', 'timestamp'),
    )


class Constraint(Base):
    """Transmission constraints (real-time and day-ahead)."""
    __tablename__ = 'constraints'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    constraint_name = Column(String(200), nullable=False)
    market_type = Column(String(20), nullable=False)  # 'realtime' or 'dayahead'
    shadow_price = Column(Float)
    binding_status = Column(String(50))
    limit_mw = Column(Float)
    flow_mw = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'constraint_name', 'market_type', 
                        name='uq_constraint'),
        Index('idx_constraint_timestamp', 'timestamp'),
        Index('idx_constraint_name', 'constraint_name'),
    )


class ExternalRTOPrice(Base):
    """External RTO CTS prices."""
    __tablename__ = 'external_rto_prices'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    rto_name = Column(String(50), nullable=False)  # IESO, PJM, ISO-NE
    rtc_price = Column(Float)
    cts_price = Column(Float)
    price_difference = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'rto_name', name='uq_external_rto_price'),
        Index('idx_external_rto_timestamp', 'timestamp'),
        Index('idx_external_rto_name', 'rto_name'),
    )


class ATC_TTC(Base):
    """Available Transfer Capability / Total Transfer Capability."""
    __tablename__ = 'atc_ttc'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    interface_id = Column(Integer, ForeignKey('interfaces.id'), nullable=False)
    forecast_type = Column(String(20))  # 'short_term' or 'long_term'
    atc_mw = Column(Float)
    ttc_mw = Column(Float)
    trm_mw = Column(Float)  # Transmission Reliability Margin
    direction = Column(String(20))  # 'import' or 'export'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    interface = relationship("Interface")
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'interface_id', 'forecast_type', 'direction',
                        name='uq_atc_ttc'),
        Index('idx_atc_ttc_timestamp', 'timestamp'),
        Index('idx_atc_ttc_interface', 'interface_id'),
    )


class Outage(Base):
    """Outage information (scheduled and actual)."""
    __tablename__ = 'outages'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    outage_type = Column(String(50), nullable=False)  # 'scheduled', 'actual', 'maintenance'
    market_type = Column(String(20))  # 'realtime' or 'dayahead'
    resource_name = Column(String(200))
    resource_type = Column(String(50))  # 'generator', 'transmission'
    mw_capacity = Column(Float)
    mw_outage = Column(Float)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_outage_timestamp', 'timestamp'),
        Index('idx_outage_resource', 'resource_name'),
        Index('idx_outage_type', 'outage_type'),
    )


class WeatherForecast(Base):
    """Weather forecast data."""
    __tablename__ = 'weather_forecast'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    forecast_time = Column(DateTime, nullable=False)  # Time being forecasted
    location = Column(String(100))
    vintage = Column(String(20))  # 'Actual' or 'Forecast' - Actual = current weather
    temperature_f = Column(Float)
    humidity_percent = Column(Float)
    wind_speed_mph = Column(Float)
    wind_direction = Column(String(20))
    cloud_cover_percent = Column(Float)
    zone_name = Column(String(50))  # NYISO zone name (e.g., 'WEST', 'N.Y.C.')
    irradiance_w_m2 = Column(Float)  # Solar irradiance in W/m²
    data_source = Column(String(20), default='NYISO')  # 'NYISO' or 'OpenMeteo'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'forecast_time', 'location', 'vintage', 'data_source', name='uq_weather_forecast'),
        Index('idx_weather_timestamp', 'timestamp'),
        Index('idx_weather_forecast_time', 'forecast_time'),
        Index('idx_weather_vintage', 'vintage'),
        Index('idx_weather_zone', 'zone_name'),
        Index('idx_weather_data_source', 'data_source'),
    )


class FuelMix(Base):
    """Real-time fuel mix / generation stack."""
    __tablename__ = 'fuel_mix'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    fuel_type = Column(String(50), nullable=False)  # gas, nuclear, hydro, wind, solar, other
    generation_mw = Column(Float, nullable=False)
    percentage = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'fuel_type', name='uq_fuel_mix'),
        Index('idx_fuel_mix_timestamp', 'timestamp'),
        Index('idx_fuel_mix_type', 'fuel_type'),
    )


# ============================================================================
# ANALYTICS TABLES
# ============================================================================

class PageView(Base):
    """Page view analytics."""
    __tablename__ = 'page_views'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    session_id = Column(String(64), nullable=False, index=True)  # Hashed session
    ip_hash = Column(String(64), nullable=False, index=True)  # Hashed IP (privacy)
    path = Column(String(500), nullable=False)  # Page path
    referrer = Column(String(500))  # Referrer URL
    user_agent = Column(String(500))  # Browser/device
    country = Column(String(2))  # ISO country code (from IP, optional)
    is_unique = Column(Boolean, default=True)  # First visit in session
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_pageview_timestamp', 'timestamp'),
        Index('idx_pageview_session', 'session_id'),
        Index('idx_pageview_path', 'path'),
    )


class VisitorSession(Base):
    """Visitor session tracking."""
    __tablename__ = 'visitor_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False, unique=True, index=True)
    ip_hash = Column(String(64), nullable=False, index=True)
    user_agent = Column(String(500))
    country = Column(String(2))
    first_visit = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_visit = Column(DateTime, nullable=False, default=datetime.utcnow)
    page_count = Column(Integer, default=1)
    is_returning = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_session_last_visit', 'last_visit'),
    )


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def get_database_url():
    """Get database URL from environment or use SQLite default."""
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Railway provides DATABASE_URL - use it directly
        # If it's PostgreSQL, it's already in the right format
        # If it's SQLite, it might need adjustment
        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            return db_url
        # Handle Railway's SQLite URL format if needed
        return db_url
    
    # Default to SQLite in current directory (works better for Railway)
    # Try multiple locations in order of preference
    possible_dirs = [
        Path.cwd() / 'data',  # Current working directory
        Path('/app/data'),     # Railway/Docker convention
        Path('/tmp'),          # Temporary directory (ephemeral)
        Path.cwd(),            # Current directory as fallback
    ]
    
    for data_dir in possible_dirs:
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / 'nyiso_data.db'
            db_path_str = str(db_path.absolute())
            return f'sqlite:///{db_path_str}'
        except (OSError, PermissionError):
            continue
    
    # Last resort: use current directory
    db_path = Path.cwd() / 'nyiso_data.db'
    return f'sqlite:///{str(db_path.absolute())}'


def create_engine_instance():
    """Create SQLAlchemy engine."""
    url = get_database_url()
    if url.startswith('sqlite'):
        # Increase timeout to 30s (default 5s) to handle concurrent access better
        return create_engine(url, echo=False, connect_args={'check_same_thread': False, 'timeout': 30})
    else:
        return create_engine(url, echo=False, pool_pre_ping=True)


def init_database():
    """Initialize database schema."""
    engine = create_engine_instance()
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get database session."""
    engine = create_engine_instance()
    Session = sessionmaker(bind=engine)
    return Session()

