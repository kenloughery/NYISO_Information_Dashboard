"""
FastAPI REST API for NYISO data access.
Provides endpoints for dashboard consumption.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import statistics
import json
import os
from pathlib import Path
import pytz

from database.schema import (
    get_session, RealTimeLBMP, DayAheadLBMP, TimeWeightedLBMP,
    RealTimeLoad, LoadForecast, InterfaceFlow, Zone, Interface,
    MarketAdvisory, Constraint, ExternalRTOPrice, ATC_TTC,
    Outage, WeatherForecast, FuelMix, AncillaryService,
    PageView, VisitorSession
)

app = FastAPI(
    title="NYISO Data API",
    description="REST API for accessing NYISO market data",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Log startup information for debugging."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("NYISO API Starting Up")
    logger.info("=" * 80)
    logger.info(f"PORT environment variable: {os.getenv('PORT', 'not set')}")
    logger.info(f"HOST environment variable: {os.getenv('HOST', 'not set')}")
    logger.info(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'not set')[:50]}...")  # Truncate for security
    logger.info("FastAPI app initialized successfully")
    logger.info("=" * 80)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Analytics middleware (must be after CORS)
# Make it optional to prevent startup failures
try:
    from api.middleware.analytics import AnalyticsMiddleware
    app.add_middleware(
        AnalyticsMiddleware,
        secret_key=os.getenv('ANALYTICS_SECRET_KEY', 'nyiso-analytics-secret-key-change-in-production')
    )
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Analytics middleware not available: {e}. Continuing without analytics.")


# Pydantic models for responses
class ZoneResponse(BaseModel):
    id: int
    name: str
    ptid: Optional[int]
    display_name: Optional[str]

    class Config:
        from_attributes = True


class RealTimeLBMPResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    lbmp: float
    marginal_cost_losses: Optional[float]
    marginal_cost_congestion: Optional[float]

    class Config:
        from_attributes = True


class DayAheadLBMPResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    lbmp: float
    marginal_cost_losses: Optional[float]
    marginal_cost_congestion: Optional[float]

    class Config:
        from_attributes = True


class TimeWeightedLBMPResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    lbmp: float
    marginal_cost_losses: Optional[float]
    marginal_cost_congestion: Optional[float]

    class Config:
        from_attributes = True


class AncillaryServiceResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    market_type: str
    service_type: Optional[str]
    price: Optional[float]

    class Config:
        from_attributes = True


class RealTimeLoadResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    load: float
    time_zone: Optional[str]

    class Config:
        from_attributes = True


class LoadForecastResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    forecast_load: float

    class Config:
        from_attributes = True


class InterfaceFlowResponse(BaseModel):
    timestamp: datetime
    interface_name: str
    flow_mwh: float
    positive_limit_mwh: Optional[float]
    negative_limit_mwh: Optional[float]

    class Config:
        from_attributes = True


class InterregionalFlowResponse(BaseModel):
    timestamp: datetime
    interface_name: str
    region: str  # "PJM", "ISO-NE", "IESO", "HQ"
    node_name: str  # Specific node/connection (e.g., "HTP", "NEPTUNE", "VFT" for PJM)
    flow_mw: float  # Clarified as MW (not MWH)
    direction: str  # "import" or "export"
    positive_limit_mw: float
    negative_limit_mw: float
    utilization_percent: Optional[float]  # Calculated

    class Config:
        from_attributes = True


class MarketAdvisoryResponse(BaseModel):
    timestamp: datetime
    advisory_type: Optional[str]
    title: Optional[str]
    message: Optional[str]
    severity: Optional[str]

    class Config:
        from_attributes = True


class ConstraintResponse(BaseModel):
    timestamp: datetime
    constraint_name: str
    market_type: str
    shadow_price: Optional[float]
    binding_status: Optional[str]
    limit_mw: Optional[float]
    flow_mw: Optional[float]

    class Config:
        from_attributes = True


class ExternalRTOPriceResponse(BaseModel):
    timestamp: datetime
    rto_name: str
    rtc_price: Optional[float]
    cts_price: Optional[float]
    price_difference: Optional[float]

    class Config:
        from_attributes = True


class ATC_TTCResponse(BaseModel):
    timestamp: datetime
    interface_name: str
    forecast_type: Optional[str]
    atc_mw: Optional[float]
    ttc_mw: Optional[float]
    trm_mw: Optional[float]
    direction: Optional[str]

    class Config:
        from_attributes = True


class OutageResponse(BaseModel):
    timestamp: datetime
    outage_type: str
    market_type: Optional[str]
    resource_name: Optional[str]
    resource_type: Optional[str]
    mw_capacity: Optional[float]
    mw_outage: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: Optional[str]

    class Config:
        from_attributes = True


class WeatherForecastResponse(BaseModel):
    timestamp: datetime
    forecast_time: Optional[datetime] = None
    location: Optional[str] = None
    vintage: Optional[str] = None  # 'Actual' or 'Forecast'
    temperature: Optional[float] = None  # Mapped from temperature_f
    humidity: Optional[float] = None  # Mapped from humidity_percent
    wind_speed: Optional[float] = None  # Mapped from wind_speed_mph
    wind_direction: Optional[str] = None
    cloud_cover_percent: Optional[float] = None
    zone_name: Optional[str] = None  # NYISO zone name
    irradiance_w_m2: Optional[float] = None  # Solar irradiance in W/m²
    data_source: Optional[str] = None  # 'NYISO' or 'OpenMeteo'
    forecast_horizon: Optional[float] = None  # Hours until forecast time

    class Config:
        from_attributes = True


class FuelMixResponse(BaseModel):
    timestamp: datetime
    fuel_type: str
    generation_mw: float
    percentage: Optional[float]

    class Config:
        from_attributes = True


# Calculated Metrics Response Models
class RTDASpreadResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    rt_lbmp: float
    da_lbmp: float
    spread: float
    spread_percent: Optional[float]

    class Config:
        from_attributes = True


class ZoneSpreadResponse(BaseModel):
    timestamp: datetime
    max_zone: str
    min_zone: str
    max_price: float
    min_price: float
    spread: float
    all_zones: Optional[dict]  # zone_name -> price mapping

    class Config:
        from_attributes = True


class LoadForecastErrorResponse(BaseModel):
    timestamp: datetime
    zone_name: str
    actual_load: float
    forecast_load: float
    error_mw: float
    error_percent: float

    class Config:
        from_attributes = True


class ReserveMarginResponse(BaseModel):
    timestamp: datetime
    total_load: float
    total_generation: Optional[float]
    reserve_margin_mw: Optional[float]
    reserve_margin_percent: Optional[float]
    zones: Optional[dict]  # zone_name -> reserve_margin

    class Config:
        from_attributes = True


class PriceVolatilityResponse(BaseModel):
    timestamp: datetime
    zone_name: Optional[str]
    volatility: float
    window_hours: int
    mean_price: float
    std_dev: float

    class Config:
        from_attributes = True


class CorrelationResponse(BaseModel):
    zone1: str
    zone2: str
    correlation: float
    sample_count: int
    period_start: datetime
    period_end: datetime

    class Config:
        from_attributes = True


class TradingSignalResponse(BaseModel):
    timestamp: datetime
    signal_type: str
    severity: str
    zone_name: Optional[str]
    message: str
    value: Optional[float]
    threshold: Optional[float]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_records: int
    date_range: dict
    zones: List[str]


# Helper function to get database session
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    """API root endpoint or frontend index (in production)."""
    # Check if frontend is available (production mode)
    static_dir = Path(__file__).parent.parent / "static"
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    
    frontend_root = static_dir if static_dir.exists() else (frontend_dist if frontend_dist.exists() else None)
    
    if frontend_root:
        # Production: serve frontend index.html
        index_file = frontend_root / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    
    # Development: return API info
    return {
        "message": "NYISO Data API",
        "version": "1.0.0",
        "endpoints": {
            "zones": "/api/zones",
            "interfaces": "/api/interfaces",
            "realtime_lbmp": "/api/realtime-lbmp",
            "dayahead_lbmp": "/api/dayahead-lbmp",
            "timeweighted_lbmp": "/api/timeweighted-lbmp",
            "ancillary_services": "/api/ancillary-services",
            "realtime_load": "/api/realtime-load",
            "load_forecast": "/api/load-forecast",
            "interface_flows": "/api/interface-flows",
            "interregional_flows": "/api/interregional-flows",
            "analytics": "/api/analytics/summary",
            "weather_current": "/api/weather-current",
            "market_advisories": "/api/market-advisories",
            "constraints": "/api/constraints",
            "external_rto_prices": "/api/external-rto-prices",
            "atc_ttc": "/api/atc-ttc",
            "outages": "/api/outages",
            "weather_forecast": "/api/weather-forecast",
            "fuel_mix": "/api/fuel-mix",
            "rt_da_spreads": "/api/rt-da-spreads",
            "zone_spreads": "/api/zone-spreads",
            "load_forecast_errors": "/api/load-forecast-errors",
            "reserve_margins": "/api/reserve-margins",
            "price_volatility": "/api/price-volatility",
            "correlations": "/api/correlations",
            "trading_signals": "/api/trading-signals",
            "stats": "/api/stats"
        }
    }


@app.get("/api/zones", response_model=List[ZoneResponse])
async def get_zones():
    """Get all zones."""
    db = next(get_db())
    try:
        zones = db.query(Zone).order_by(Zone.name).all()
        return zones
    finally:
        db.close()


@app.get("/api/interfaces", response_model=List[dict])
async def get_interfaces():
    """Get all interfaces."""
    db = next(get_db())
    try:
        interfaces = db.query(Interface).order_by(Interface.name).all()
        return [{"id": i.id, "name": i.name, "point_id": i.point_id} for i in interfaces]
    finally:
        db.close()


@app.get("/api/realtime-lbmp", response_model=List[RealTimeLBMPResponse])
async def get_realtime_lbmp(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get real-time LBMP data.
    
    Note: NYISO publishes some forward-looking intervals in their real-time data.
    By default, timestamps more than 30 minutes in the future are filtered out
    to show only current/actual data. Use date filters to see all data including forecasts.
    """
    db = next(get_db())
    
    query = db.query(RealTimeLBMP).join(Zone)
    
    # Apply filters
    if start_date:
        query = query.filter(RealTimeLBMP.timestamp >= start_date)
    if end_date:
        query = query.filter(RealTimeLBMP.timestamp <= end_date)
    else:
        # If no end_date specified, filter out future timestamps (NYISO includes forecasts)
        # Allow 30 minutes buffer for publication delays
        eastern = pytz.timezone('US/Eastern')
        now_et = datetime.now(eastern).replace(tzinfo=None)
        future_cutoff = now_et + timedelta(minutes=30)
        query = query.filter(RealTimeLBMP.timestamp <= future_cutoff)
    
    if zones:
        zone_list = [z.strip().upper() for z in zones.split(',')]
        query = query.filter(Zone.name.in_(zone_list))
    
    # Order and limit
    query = query.order_by(desc(RealTimeLBMP.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "zone_name": r.zone.name,
                "lbmp": r.lbmp,
                "marginal_cost_losses": r.marginal_cost_losses,
                "marginal_cost_congestion": r.marginal_cost_congestion
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/dayahead-lbmp", response_model=List[DayAheadLBMPResponse])
async def get_dayahead_lbmp(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get day-ahead LBMP data."""
    db = next(get_db())
    
    query = db.query(DayAheadLBMP).join(Zone)
    
    if start_date:
        query = query.filter(DayAheadLBMP.timestamp >= start_date)
    if end_date:
        query = query.filter(DayAheadLBMP.timestamp <= end_date)
    if zones:
        zone_list = [z.strip().upper() for z in zones.split(',')]
        query = query.filter(Zone.name.in_(zone_list))
    
    query = query.order_by(desc(DayAheadLBMP.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "zone_name": r.zone.name,
                "lbmp": r.lbmp,
                "marginal_cost_losses": r.marginal_cost_losses,
                "marginal_cost_congestion": r.marginal_cost_congestion
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/timeweighted-lbmp", response_model=List[TimeWeightedLBMPResponse])
async def get_timeweighted_lbmp(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get time-weighted/integrated real-time LBMP data (hourly)."""
    db = next(get_db())
    
    query = db.query(TimeWeightedLBMP).join(Zone)
    
    if start_date:
        query = query.filter(TimeWeightedLBMP.timestamp >= start_date)
    if end_date:
        query = query.filter(TimeWeightedLBMP.timestamp <= end_date)
    if zones:
        zone_list = [z.strip().upper() for z in zones.split(',')]
        query = query.filter(Zone.name.in_(zone_list))
    
    query = query.order_by(desc(TimeWeightedLBMP.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "zone_name": r.zone.name,
                "lbmp": r.lbmp,
                "marginal_cost_losses": r.marginal_cost_losses,
                "marginal_cost_congestion": r.marginal_cost_congestion
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/ancillary-services", response_model=List[AncillaryServiceResponse])
async def get_ancillary_services(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    market_type: Optional[str] = Query(None, description="Filter by market type: 'realtime' or 'dayahead'"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get ancillary service prices (real-time and day-ahead)."""
    db = next(get_db())
    
    query = db.query(AncillaryService).join(Zone)
    
    if start_date:
        query = query.filter(AncillaryService.timestamp >= start_date)
    if end_date:
        query = query.filter(AncillaryService.timestamp <= end_date)
    if market_type:
        query = query.filter(AncillaryService.market_type == market_type.lower())
    if zones:
        zone_list = [z.strip().upper() for z in zones.split(',')]
        query = query.filter(Zone.name.in_(zone_list))
    if service_type:
        query = query.filter(AncillaryService.service_type == service_type.lower())
    
    query = query.order_by(desc(AncillaryService.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "zone_name": r.zone.name,
                "market_type": r.market_type,
                "service_type": r.service_type,
                "price": r.price
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/realtime-load", response_model=List[RealTimeLoadResponse])
async def get_realtime_load(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get real-time load data."""
    db = next(get_db())
    
    query = db.query(RealTimeLoad).join(Zone)
    
    if start_date:
        query = query.filter(RealTimeLoad.timestamp >= start_date)
    if end_date:
        query = query.filter(RealTimeLoad.timestamp <= end_date)
    if zones:
        zone_list = [z.strip().upper() for z in zones.split(',')]
        query = query.filter(Zone.name.in_(zone_list))
    
    query = query.order_by(desc(RealTimeLoad.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "zone_name": r.zone.name,
                "load": r.load,
                "time_zone": r.time_zone
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/load-forecast", response_model=List[LoadForecastResponse])
async def get_load_forecast(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get load forecast data."""
    db = next(get_db())
    
    query = db.query(LoadForecast).join(Zone)
    
    if start_date:
        query = query.filter(LoadForecast.timestamp >= start_date)
    if end_date:
        query = query.filter(LoadForecast.timestamp <= end_date)
    if zones:
        zone_list = [z.strip().upper() for z in zones.split(',')]
        query = query.filter(Zone.name.in_(zone_list))
    
    query = query.order_by(desc(LoadForecast.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "zone_name": r.zone.name,
                "forecast_load": r.forecast_load
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/interface-flows", response_model=List[InterfaceFlowResponse])
async def get_interface_flows(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    interfaces: Optional[str] = Query(None, description="Comma-separated interface names"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get interface flow data."""
    db = next(get_db())
    
    query = db.query(InterfaceFlow).join(Interface)
    
    if start_date:
        query = query.filter(InterfaceFlow.timestamp >= start_date)
    if end_date:
        query = query.filter(InterfaceFlow.timestamp <= end_date)
    if interfaces:
        interface_list = [i.strip() for i in interfaces.split(',')]
        query = query.filter(Interface.name.in_(interface_list))
    
    query = query.order_by(desc(InterfaceFlow.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "interface_name": r.interface.name,
                "flow_mwh": r.flow_mwh,
                "positive_limit_mwh": r.positive_limit_mwh,
                "negative_limit_mwh": r.negative_limit_mwh
            }
            for r in results
        ]
    finally:
        db.close()


def _identify_region_and_node(interface_name: str) -> tuple[str, str]:
    """
    Identify region and node name from interface name.
    
    Returns:
        (region, node_name) tuple
    """
    interface_upper = interface_name.upper()
    
    # PJM interfaces
    if 'PJM' in interface_upper or ('PJ - NY' in interface_upper and 'PJM' not in interface_upper):
        if 'HTP' in interface_upper:
            return ('PJM', 'HTP')
        elif 'NEPTUNE' in interface_upper:
            return ('PJM', 'NEPTUNE')
        elif 'VFT' in interface_upper:
            return ('PJM', 'VFT')
        elif 'KEYSTONE' in interface_upper:
            return ('PJM', 'KEYSTONE')
        elif 'PJ - NY' in interface_upper:
            return ('PJM', 'PJ - NY')
        else:
            # Generic PJM
            return ('PJM', 'PJM')
    
    # ISO-NE (New England)
    elif 'NE - NY' in interface_upper or 'NE_NY' in interface_upper:
        return ('ISO-NE', 'NE - NY')
    elif 'N.E.' in interface_upper or 'N.E' in interface_upper:
        return ('ISO-NE', 'NE')
    
    # IESO (Ontario)
    elif 'OH - NY' in interface_upper or 'OH_NY' in interface_upper:
        return ('IESO', 'OH - NY')
    elif 'ONTARIO' in interface_upper or 'IESO' in interface_upper:
        return ('IESO', 'ONTARIO')
    
    # Hydro Quebec
    elif 'HQ - NY' in interface_upper or 'HQ_NY' in interface_upper:
        return ('HQ', 'HQ - NY')
    elif 'HQ_CEDARS' in interface_upper:
        return ('HQ', 'CEDARS')
    elif 'HQ_IMPORT_EXPORT' in interface_upper or 'HQ_IMPORT' in interface_upper:
        return ('HQ', 'IMPORT_EXPORT')
    elif 'HQ' in interface_upper:
        return ('HQ', 'HQ')
    
    # Default: unknown
    return ('UNKNOWN', interface_name)


def _calculate_utilization(flow_mw: float, positive_limit: Optional[float], negative_limit: Optional[float]) -> Optional[float]:
    """
    Calculate utilization percentage based on flow direction.
    
    Args:
        flow_mw: Flow in MW (positive = import, negative = export)
        positive_limit: Import limit (positive)
        negative_limit: Export limit (negative)
    
    Returns:
        Utilization percentage (0-100) or None if cannot calculate
    """
    if flow_mw is None:
        return None
    
    # Import (positive flow)
    if flow_mw > 0:
        if positive_limit is None or positive_limit == 0:
            return None
        return (flow_mw / positive_limit) * 100
    
    # Export (negative flow)
    elif flow_mw < 0:
        if negative_limit is None or negative_limit == 0:
            return None
        # Use absolute value for calculation
        return (abs(flow_mw) / abs(negative_limit)) * 100
    
    # Zero flow
    return 0.0


@app.get("/api/interregional-flows", response_model=List[InterregionalFlowResponse])
async def get_interregional_flows(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    """
    Get interregional flow data for external interfaces (PJM, ISO-NE, IESO, HQ).
    
    Returns all external interfaces separately to show individual locational price deltas.
    Each interface represents a different physical connection point.
    """
    db = next(get_db())
    
    try:
        # Query interface flows with interface names
        query = db.query(InterfaceFlow).join(Interface)
        
        # Filter for external interfaces (PJM, ISO-NE, IESO, HQ)
        # Use case-insensitive matching with LIKE
        external_patterns = [
            '%PJM%',
            '%NE - NY%',
            '%N.E.%',
            '%OH - NY%',
            '%ONTARIO%',
            '%IESO%',
            '%HQ%'
        ]
        
        from sqlalchemy import or_
        interface_filters = or_(*[Interface.name.ilike(pattern) for pattern in external_patterns])
        query = query.filter(interface_filters)
        
        # Apply date filters
        if start_date:
            query = query.filter(InterfaceFlow.timestamp >= start_date)
        if end_date:
            query = query.filter(InterfaceFlow.timestamp <= end_date)
        
        # Get latest data by default (if no date filters)
        if not start_date and not end_date:
            # Get the latest timestamp
            latest_timestamp = db.query(func.max(InterfaceFlow.timestamp)).scalar()
            if latest_timestamp:
                query = query.filter(InterfaceFlow.timestamp == latest_timestamp)
        
        query = query.order_by(desc(InterfaceFlow.timestamp), Interface.name).limit(limit)
        
        results = query.all()
        
        # Transform results
        response_data = []
        for r in results:
            interface_name = r.interface.name
            region, node_name = _identify_region_and_node(interface_name)
            
            # Skip if not a recognized external region
            if region == 'UNKNOWN':
                continue
            
            # Get flow (stored as MWH but represents MW in 5-min context)
            flow_mw = r.flow_mwh if r.flow_mwh is not None else 0.0
            
            # Determine direction
            direction = "import" if flow_mw > 0 else "export" if flow_mw < 0 else "zero"
            
            # Calculate utilization
            utilization_percent = _calculate_utilization(
                flow_mw,
                r.positive_limit_mwh,
                r.negative_limit_mwh
            )
            
            response_data.append({
                "timestamp": r.timestamp,
                "interface_name": interface_name,
                "region": region,
                "node_name": node_name,
                "flow_mw": flow_mw,
                "direction": direction,
                "positive_limit_mw": r.positive_limit_mwh if r.positive_limit_mwh is not None else 0.0,
                "negative_limit_mw": r.negative_limit_mwh if r.negative_limit_mwh is not None else 0.0,
                "utilization_percent": utilization_percent
            })
        
        return response_data
    
    finally:
        db.close()


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

class AnalyticsSummaryResponse(BaseModel):
    total_page_views: int
    unique_visitors: int
    sessions: int
    page_views_today: int
    unique_visitors_today: int
    top_pages: List[Dict[str, Any]]
    referrers: List[Dict[str, Any]]
    countries: List[Dict[str, Any]]


@app.get("/api/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    days: int = Query(30, ge=1, le=365, description="Number of days (if dates not provided)")
):
    """Get analytics summary."""
    db = next(get_db())
    
    try:
        # Default to last N days
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=days)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Total page views
        total_views = db.query(func.count(PageView.id)).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date
        ).scalar() or 0
        
        # Unique visitors (distinct IP hashes)
        unique_visitors = db.query(func.count(func.distinct(PageView.ip_hash))).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date
        ).scalar() or 0
        
        # Sessions
        sessions = db.query(func.count(VisitorSession.id)).filter(
            VisitorSession.first_visit >= start_date,
            VisitorSession.first_visit <= end_date
        ).scalar() or 0
        
        # Today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        views_today = db.query(func.count(PageView.id)).filter(
            PageView.timestamp >= today_start
        ).scalar() or 0
        visitors_today = db.query(func.count(func.distinct(PageView.ip_hash))).filter(
            PageView.timestamp >= today_start
        ).scalar() or 0
        
        # Top pages
        top_pages = db.query(
            PageView.path,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date
        ).group_by(PageView.path).order_by(desc('views')).limit(10).all()
        
        # Top referrers
        top_referrers = db.query(
            PageView.referrer,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date,
            PageView.referrer.isnot(None)
        ).group_by(PageView.referrer).order_by(desc('views')).limit(10).all()
        
        # Countries
        top_countries = db.query(
            PageView.country,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date,
            PageView.country.isnot(None)
        ).group_by(PageView.country).order_by(desc('views')).limit(10).all()
        
        return {
            "total_page_views": total_views,
            "unique_visitors": unique_visitors,
            "sessions": sessions,
            "page_views_today": views_today,
            "unique_visitors_today": visitors_today,
            "top_pages": [{"path": p[0], "views": p[1]} for p in top_pages],
            "referrers": [{"referrer": r[0], "views": r[1]} for r in top_referrers],
            "countries": [{"country": c[0], "views": c[1]} for c in top_countries]
        }
    finally:
        db.close()


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics."""
    db = next(get_db())
    
    # Count records
    rt_lbmp_count = db.query(func.count(RealTimeLBMP.id)).scalar()
    da_lbmp_count = db.query(func.count(DayAheadLBMP.id)).scalar()
    rt_load_count = db.query(func.count(RealTimeLoad.id)).scalar()
    load_fcst_count = db.query(func.count(LoadForecast.id)).scalar()
    if_flow_count = db.query(func.count(InterfaceFlow.id)).scalar()
    advisory_count = db.query(func.count(MarketAdvisory.id)).scalar()
    constraint_count = db.query(func.count(Constraint.id)).scalar()
    external_rto_count = db.query(func.count(ExternalRTOPrice.id)).scalar()
    atc_ttc_count = db.query(func.count(ATC_TTC.id)).scalar()
    outage_count = db.query(func.count(Outage.id)).scalar()
    weather_count = db.query(func.count(WeatherForecast.id)).scalar()
    fuel_mix_count = db.query(func.count(FuelMix.id)).scalar()
    
    total = (rt_lbmp_count + da_lbmp_count + rt_load_count + load_fcst_count + 
             if_flow_count + advisory_count + constraint_count + external_rto_count +
             atc_ttc_count + outage_count + weather_count + fuel_mix_count)
    
    # Date ranges
    rt_lbmp_min = db.query(func.min(RealTimeLBMP.timestamp)).scalar()
    rt_lbmp_max = db.query(func.max(RealTimeLBMP.timestamp)).scalar()
    
    # Zones
    zones = db.query(Zone.name).order_by(Zone.name).all()
    zone_names = [z[0] for z in zones]
    
    try:
        return {
            "total_records": total,
            "date_range": {
                "start": rt_lbmp_min.isoformat() if rt_lbmp_min else None,
                "end": rt_lbmp_max.isoformat() if rt_lbmp_max else None
            },
            "zones": zone_names,
            "record_counts": {
                "realtime_lbmp": rt_lbmp_count,
                "dayahead_lbmp": da_lbmp_count,
                "realtime_load": rt_load_count,
                "load_forecast": load_fcst_count,
                "interface_flows": if_flow_count,
                "market_advisories": advisory_count,
                "constraints": constraint_count,
                "external_rto_prices": external_rto_count,
                "atc_ttc": atc_ttc_count,
                "outages": outage_count,
                "weather_forecast": weather_count,
                "fuel_mix": fuel_mix_count
            }
        }
    finally:
        db.close()


@app.get("/api/market-advisories", response_model=List[MarketAdvisoryResponse])
async def get_market_advisories(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    """Get market advisory notifications."""
    db = next(get_db())
    
    query = db.query(MarketAdvisory)
    
    if start_date:
        query = query.filter(MarketAdvisory.timestamp >= start_date)
    if end_date:
        query = query.filter(MarketAdvisory.timestamp <= end_date)
    
    query = query.order_by(desc(MarketAdvisory.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "advisory_type": r.advisory_type,
                "title": r.title,
                "message": r.message,
                "severity": r.severity
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/constraints", response_model=List[ConstraintResponse])
async def get_constraints(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    market_type: Optional[str] = Query(None, description="Filter by market type: 'realtime' or 'dayahead'"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get transmission constraints."""
    db = next(get_db())
    
    query = db.query(Constraint)
    
    if start_date:
        query = query.filter(Constraint.timestamp >= start_date)
    if end_date:
        query = query.filter(Constraint.timestamp <= end_date)
    if market_type:
        query = query.filter(Constraint.market_type == market_type.lower())
    
    query = query.order_by(desc(Constraint.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "constraint_name": r.constraint_name,
                "market_type": r.market_type,
                "shadow_price": r.shadow_price,
                "binding_status": r.binding_status,
                "limit_mw": r.limit_mw,
                "flow_mw": r.flow_mw
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/external-rto-prices", response_model=List[ExternalRTOPriceResponse])
async def get_external_rto_prices(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    rto_name: Optional[str] = Query(None, description="Filter by RTO name (IESO, PJM, ISO-NE)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get external RTO CTS prices."""
    db = next(get_db())
    
    query = db.query(ExternalRTOPrice)
    
    if start_date:
        query = query.filter(ExternalRTOPrice.timestamp >= start_date)
    if end_date:
        query = query.filter(ExternalRTOPrice.timestamp <= end_date)
    if rto_name:
        query = query.filter(ExternalRTOPrice.rto_name == rto_name.upper())
    
    query = query.order_by(desc(ExternalRTOPrice.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "rto_name": r.rto_name,
                "rtc_price": r.rtc_price,
                "cts_price": r.cts_price,
                "price_difference": r.price_difference
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/atc-ttc", response_model=List[ATC_TTCResponse])
async def get_atc_ttc(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    interfaces: Optional[str] = Query(None, description="Comma-separated interface names"),
    forecast_type: Optional[str] = Query(None, description="Filter by forecast type: 'short_term' or 'long_term'"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get ATC/TTC data."""
    db = next(get_db())
    
    query = db.query(ATC_TTC).join(Interface)
    
    if start_date:
        query = query.filter(ATC_TTC.timestamp >= start_date)
    if end_date:
        query = query.filter(ATC_TTC.timestamp <= end_date)
    if interfaces:
        interface_list = [i.strip() for i in interfaces.split(',')]
        query = query.filter(Interface.name.in_(interface_list))
    if forecast_type:
        query = query.filter(ATC_TTC.forecast_type == forecast_type)
    
    query = query.order_by(desc(ATC_TTC.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "interface_name": r.interface.name,
                "forecast_type": r.forecast_type,
                "atc_mw": r.atc_mw,
                "ttc_mw": r.ttc_mw,
                "trm_mw": r.trm_mw,
                "direction": r.direction
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/outages", response_model=List[OutageResponse])
async def get_outages(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    outage_type: Optional[str] = Query(None, description="Filter by outage type: 'scheduled', 'actual', 'maintenance'"),
    market_type: Optional[str] = Query(None, description="Filter by market type: 'realtime' or 'dayahead'"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type: 'generator' or 'transmission'"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get outage information."""
    db = next(get_db())
    
    query = db.query(Outage)
    
    if start_date:
        query = query.filter(Outage.timestamp >= start_date)
    if end_date:
        query = query.filter(Outage.timestamp <= end_date)
    if outage_type:
        query = query.filter(Outage.outage_type == outage_type.lower())
    if market_type:
        query = query.filter(Outage.market_type == market_type.lower())
    if resource_type:
        query = query.filter(Outage.resource_type == resource_type.lower())
    
    query = query.order_by(desc(Outage.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "outage_type": r.outage_type,
                "market_type": r.market_type,
                "resource_name": r.resource_name,
                "resource_type": r.resource_type,
                "mw_capacity": r.mw_capacity,
                "mw_outage": r.mw_outage,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "status": r.status
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/weather-forecast", response_model=List[WeatherForecastResponse])
async def get_weather_forecast(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    location: Optional[str] = Query(None, description="Filter by location"),
    vintage: Optional[str] = Query(None, description="Filter by vintage: 'Actual' or 'Forecast'"),
    zone_name: Optional[str] = Query(None, description="Filter by NYISO zone name"),
    data_source: Optional[str] = Query(None, description="Filter by data source: 'NYISO' or 'OpenMeteo'"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get weather forecast data."""
    db = next(get_db())
    
    query = db.query(WeatherForecast)
    
    if start_date:
        query = query.filter(WeatherForecast.timestamp >= start_date)
    if end_date:
        query = query.filter(WeatherForecast.timestamp <= end_date)
    if location:
        query = query.filter(WeatherForecast.location == location)
    if vintage:
        query = query.filter(WeatherForecast.vintage == vintage)
    if zone_name:
        query = query.filter(WeatherForecast.zone_name == zone_name)
    if data_source:
        query = query.filter(WeatherForecast.data_source == data_source)
    
    query = query.order_by(desc(WeatherForecast.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "forecast_time": r.forecast_time.isoformat() if r.forecast_time else None,
                "location": r.location,
                "vintage": r.vintage,  # 'Actual' or 'Forecast'
                "temperature": r.temperature_f,  # Map to frontend-friendly name
                "humidity": r.humidity_percent,  # Map to frontend-friendly name
                "wind_speed": r.wind_speed_mph,  # Map to frontend-friendly name
                "wind_direction": r.wind_direction,
                "cloud_cover_percent": r.cloud_cover_percent,
                "zone_name": r.zone_name,
                "irradiance_w_m2": r.irradiance_w_m2,
                "data_source": r.data_source or 'NYISO',
                "forecast_horizon": (r.forecast_time - r.timestamp).total_seconds() / 3600 if r.forecast_time and r.timestamp else None
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/weather-current", response_model=List[WeatherForecastResponse])
async def get_current_weather(
    location: Optional[str] = Query(None, description="Filter by location (station ID)"),
    zone_name: Optional[str] = Query(None, description="Filter by NYISO zone name"),
    data_source: Optional[str] = Query(None, description="Filter by data source: 'NYISO' or 'OpenMeteo'")
):
    """Get current weather data (Actual vintage, most recent per station).
    
    Returns the most recent actual weather observations. The 'forecast_time' field
    represents when the data was last updated (Vintage Date), while 'timestamp' 
    represents the date the weather is for (Forecast Date).
    """
    db = next(get_db())
    
    try:
        # Get most recent actual weather data
        # Use forecast_time (Vintage Date) to find the most recently updated data
        latest_vintage_date = db.query(func.max(WeatherForecast.forecast_time)).filter(
            WeatherForecast.vintage == 'Actual'
        ).scalar()
        
        if not latest_vintage_date:
            return []
        
        # Get the most recent timestamp (Forecast Date) for this vintage date
        latest_timestamp = db.query(func.max(WeatherForecast.timestamp)).filter(
            WeatherForecast.vintage == 'Actual',
            WeatherForecast.forecast_time == latest_vintage_date
        ).scalar()
        
        if not latest_timestamp:
            return []
        
        # Get one record per location for the latest data
        # Use a subquery to get the most recent record per location
        subquery = db.query(
            WeatherForecast.location,
            func.max(WeatherForecast.forecast_time).label('max_forecast_time')
        ).filter(
            WeatherForecast.vintage == 'Actual',
            WeatherForecast.timestamp == latest_timestamp,
            WeatherForecast.forecast_time == latest_vintage_date
        )
        
        if location:
            subquery = subquery.filter(WeatherForecast.location == location)
        if zone_name:
            subquery = subquery.filter(WeatherForecast.zone_name == zone_name)
        if data_source:
            subquery = subquery.filter(WeatherForecast.data_source == data_source)
        
        subquery = subquery.group_by(WeatherForecast.location).subquery()
        
        # Join to get full records
        query = db.query(WeatherForecast).join(
            subquery,
            and_(
                WeatherForecast.location == subquery.c.location,
                WeatherForecast.forecast_time == subquery.c.max_forecast_time,
                WeatherForecast.vintage == 'Actual',
                WeatherForecast.timestamp == latest_timestamp
            )
        )
        
        if location:
            query = query.filter(WeatherForecast.location == location)
        if zone_name:
            query = query.filter(WeatherForecast.zone_name == zone_name)
        if data_source:
            query = query.filter(WeatherForecast.data_source == data_source)
        
        query = query.order_by(WeatherForecast.location)
        
        results = query.all()
        return [
            {
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "forecast_time": r.forecast_time.isoformat() if r.forecast_time else None,  # This is the "last updated" time
                "location": r.location,
                "vintage": r.vintage,
                "temperature": r.temperature_f,
                "humidity": r.humidity_percent,
                "wind_speed": r.wind_speed_mph,
                "wind_direction": r.wind_direction,
                "cloud_cover_percent": r.cloud_cover_percent,
                "zone_name": r.zone_name,
                "irradiance_w_m2": r.irradiance_w_m2,
                "data_source": r.data_source or 'NYISO',
                "forecast_horizon": None  # Current weather, not a forecast
            }
            for r in results
        ]
    finally:
        db.close()


@app.get("/api/fuel-mix", response_model=List[FuelMixResponse])
async def get_fuel_mix(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Get real-time fuel mix / generation stack."""
    db = next(get_db())
    
    query = db.query(FuelMix)
    
    if start_date:
        query = query.filter(FuelMix.timestamp >= start_date)
    if end_date:
        query = query.filter(FuelMix.timestamp <= end_date)
    if fuel_type:
        query = query.filter(FuelMix.fuel_type == fuel_type.lower())
    
    query = query.order_by(desc(FuelMix.timestamp)).limit(limit)
    
    try:
        results = query.all()
        return [
            {
                "timestamp": r.timestamp,
                "fuel_type": r.fuel_type,
                "generation_mw": r.generation_mw,
                "percentage": r.percentage
            }
            for r in results
        ]
    finally:
        db.close()


# ============================================================================
# CALCULATED METRICS ENDPOINTS
# ============================================================================

@app.get("/api/rt-da-spreads", response_model=List[RTDASpreadResponse])
async def get_rt_da_spreads(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    min_spread: Optional[float] = Query(None, description="Minimum spread threshold ($/MWh)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Calculate RT-DA price spreads by zone.
    
    Compares real-time LBMP with day-ahead LBMP for the same timestamp and zone.
    Positive spread means RT > DA (real-time is more expensive).
    """
    db = next(get_db())
    
    try:
        # Get RT and DA LBMP data, matching by timestamp and zone
        rt_query = db.query(
            RealTimeLBMP.timestamp,
            Zone.name.label('zone_name'),
            RealTimeLBMP.lbmp.label('rt_lbmp')
        ).join(Zone).filter(RealTimeLBMP.zone_id == Zone.id)
        
        da_query = db.query(
            DayAheadLBMP.timestamp,
            Zone.name.label('zone_name'),
            DayAheadLBMP.lbmp.label('da_lbmp')
        ).join(Zone).filter(DayAheadLBMP.zone_id == Zone.id)
        
        if start_date:
            rt_query = rt_query.filter(RealTimeLBMP.timestamp >= start_date)
            da_query = da_query.filter(DayAheadLBMP.timestamp >= start_date)
        if end_date:
            rt_query = rt_query.filter(RealTimeLBMP.timestamp <= end_date)
            da_query = da_query.filter(DayAheadLBMP.timestamp <= end_date)
        if zones:
            zone_list = [z.strip().upper() for z in zones.split(',')]
            rt_query = rt_query.filter(Zone.name.in_(zone_list))
            da_query = da_query.filter(Zone.name.in_(zone_list))
        
        # Get data - use tuple keys for matching
        rt_data = {(r.timestamp, r.zone_name): r.rt_lbmp for r in rt_query.all()}
        da_data = {(r.timestamp, r.zone_name): r.da_lbmp for r in da_query.all()}
        
        # Calculate spreads for matching timestamps and zones
        spreads = []
        for (ts, zone), rt_lbmp in rt_data.items():
            if (ts, zone) in da_data:
                da_lbmp = da_data[(ts, zone)]
                spread = rt_lbmp - da_lbmp
                spread_pct = (spread / da_lbmp * 100) if da_lbmp != 0 else None
                
                if min_spread is None or abs(spread) >= min_spread:
                    spreads.append({
                        "timestamp": ts,
                        "zone_name": zone,
                        "rt_lbmp": rt_lbmp,
                        "da_lbmp": da_lbmp,
                        "spread": spread,
                        "spread_percent": spread_pct
                    })
        
        # Sort by timestamp desc and limit
        spreads.sort(key=lambda x: x["timestamp"], reverse=True)
        return spreads[:limit]
    finally:
        db.close()


@app.get("/api/zone-spreads", response_model=List[ZoneSpreadResponse])
async def get_zone_spreads(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    include_all_zones: bool = Query(False, description="Include all zone prices in response"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Calculate intra-zonal price differentials.
    
    For each timestamp, finds the maximum and minimum zone prices,
    and calculates the spread between them.
    """
    db = next(get_db())
    
    try:
        # Get all RT LBMP data grouped by timestamp
        query = db.query(
            RealTimeLBMP.timestamp,
            Zone.name.label('zone_name'),
            RealTimeLBMP.lbmp
        ).join(Zone).filter(RealTimeLBMP.zone_id == Zone.id)
        
        if start_date:
            query = query.filter(RealTimeLBMP.timestamp >= start_date)
        if end_date:
            query = query.filter(RealTimeLBMP.timestamp <= end_date)
        
        results = query.order_by(desc(RealTimeLBMP.timestamp)).limit(limit * 20).all()
        
        # Group by timestamp
        by_timestamp = {}
        for r in results:
            ts = r.timestamp
            if ts not in by_timestamp:
                by_timestamp[ts] = {}
            by_timestamp[ts][r.zone_name] = r.lbmp
        
        # Calculate spreads
        spreads = []
        for ts, zone_prices in sorted(by_timestamp.items(), reverse=True)[:limit]:
            if len(zone_prices) < 2:
                continue
            
            max_zone = max(zone_prices.items(), key=lambda x: x[1])
            min_zone = min(zone_prices.items(), key=lambda x: x[1])
            
            spreads.append({
                "timestamp": ts,
                "max_zone": max_zone[0],
                "min_zone": min_zone[0],
                "max_price": max_zone[1],
                "min_price": min_zone[1],
                "spread": max_zone[1] - min_zone[1],
                "all_zones": zone_prices if include_all_zones else None
            })
        
        return spreads
    finally:
        db.close()


@app.get("/api/load-forecast-errors", response_model=List[LoadForecastErrorResponse])
async def get_load_forecast_errors(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    max_error_percent: Optional[float] = Query(None, description="Maximum error percentage threshold"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Calculate load forecast errors (forecast vs actual deviations).
    
    Compares load forecast with actual real-time load for the same timestamp and zone.
    """
    db = next(get_db())
    
    try:
        # Get forecast and actual load data
        forecast_query = db.query(
            LoadForecast.timestamp,
            Zone.name.label('zone_name'),
            LoadForecast.forecast_load
        ).join(Zone).filter(LoadForecast.zone_id == Zone.id)
        
        actual_query = db.query(
            RealTimeLoad.timestamp,
            Zone.name.label('zone_name'),
            RealTimeLoad.load.label('actual_load')
        ).join(Zone).filter(RealTimeLoad.zone_id == Zone.id)
        
        if start_date:
            forecast_query = forecast_query.filter(LoadForecast.timestamp >= start_date)
            actual_query = actual_query.filter(RealTimeLoad.timestamp >= start_date)
        if end_date:
            forecast_query = forecast_query.filter(LoadForecast.timestamp <= end_date)
            actual_query = actual_query.filter(RealTimeLoad.timestamp <= end_date)
        if zones:
            zone_list = [z.strip().upper() for z in zones.split(',')]
            forecast_query = forecast_query.filter(Zone.name.in_(zone_list))
            actual_query = actual_query.filter(Zone.name.in_(zone_list))
        
        forecast_data = {(r.timestamp, r.zone_name): r.forecast_load for r in forecast_query.all()}
        actual_data = {(r.timestamp, r.zone_name): r.actual_load for r in actual_query.all()}
        
        # Calculate errors
        errors = []
        for (ts, zone), forecast_load in forecast_data.items():
            if (ts, zone) in actual_data:
                actual_load = actual_data[(ts, zone)]
                error_mw = actual_load - forecast_load
                error_pct = (error_mw / forecast_load * 100) if forecast_load != 0 else 0
                
                if max_error_percent is None or abs(error_pct) <= max_error_percent:
                    errors.append({
                        "timestamp": ts,
                        "zone_name": zone,
                        "actual_load": actual_load,
                        "forecast_load": forecast_load,
                        "error_mw": error_mw,
                        "error_percent": error_pct
                    })
        
        errors.sort(key=lambda x: x["timestamp"], reverse=True)
        return errors[:limit]
    finally:
        db.close()


@app.get("/api/reserve-margins", response_model=List[ReserveMarginResponse])
async def get_reserve_margins(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Calculate reserve margins.
    
    Reserve margin = (Total Generation Capacity - Total Load) / Total Load * 100
    Uses fuel mix data for generation and real-time load for demand.
    """
    db = next(get_db())
    
    try:
        # Get total load by timestamp
        load_query = db.query(
            RealTimeLoad.timestamp,
            func.sum(RealTimeLoad.load).label('total_load')
        ).group_by(RealTimeLoad.timestamp)
        
        # Get total generation by timestamp (from fuel mix)
        gen_query = db.query(
            FuelMix.timestamp,
            func.sum(FuelMix.generation_mw).label('total_generation')
        ).group_by(FuelMix.timestamp)
        
        if start_date:
            load_query = load_query.filter(RealTimeLoad.timestamp >= start_date)
            gen_query = gen_query.filter(FuelMix.timestamp >= start_date)
        if end_date:
            load_query = load_query.filter(RealTimeLoad.timestamp <= end_date)
            gen_query = gen_query.filter(FuelMix.timestamp <= end_date)
        
        load_data = {r.timestamp: r.total_load for r in load_query.all()}
        gen_data = {r.timestamp: r.total_generation for r in gen_query.all()}
        
        # Calculate reserve margins
        margins = []
        for ts in sorted(set(load_data.keys()) & set(gen_data.keys()), reverse=True)[:limit]:
            total_load = load_data[ts]
            total_gen = gen_data[ts]
            reserve_mw = total_gen - total_load if total_gen else None
            reserve_pct = (reserve_mw / total_load * 100) if total_load and reserve_mw else None
            
            margins.append({
                "timestamp": ts,
                "total_load": total_load,
                "total_generation": total_gen,
                "reserve_margin_mw": reserve_mw,
                "reserve_margin_percent": reserve_pct,
                "zones": None  # Could be enhanced to calculate per-zone
            })
        
        return margins
    finally:
        db.close()


@app.get("/api/price-volatility", response_model=List[PriceVolatilityResponse])
async def get_price_volatility(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names"),
    window_hours: int = Query(24, ge=1, le=168, description="Rolling window size in hours"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return")
):
    """Calculate rolling price volatility metrics.
    
    Computes standard deviation of prices over a rolling window.
    """
    db = next(get_db())
    
    try:
        query = db.query(
            RealTimeLBMP.timestamp,
            Zone.name.label('zone_name'),
            RealTimeLBMP.lbmp
        ).join(Zone).filter(RealTimeLBMP.zone_id == Zone.id)
        
        if start_date:
            query = query.filter(RealTimeLBMP.timestamp >= start_date)
        if end_date:
            query = query.filter(RealTimeLBMP.timestamp <= end_date)
        if zones:
            zone_list = [z.strip().upper() for z in zones.split(',')]
            query = query.filter(Zone.name.in_(zone_list))
        
        results = query.order_by(RealTimeLBMP.timestamp).all()
        
        # Group by zone
        by_zone = {}
        for r in results:
            if r.zone_name not in by_zone:
                by_zone[r.zone_name] = []
            by_zone[r.zone_name].append((r.timestamp, r.lbmp))
        
        # Calculate rolling volatility
        volatilities = []
        window_delta = timedelta(hours=window_hours)
        
        for zone_name, prices in by_zone.items():
            for i, (ts, price) in enumerate(prices):
                window_start = ts - window_delta
                window_prices = [p for t, p in prices if window_start <= t <= ts]
                
                if len(window_prices) >= 2:
                    mean_price = statistics.mean(window_prices)
                    std_dev = statistics.stdev(window_prices)
                    volatility = (std_dev / mean_price * 100) if mean_price != 0 else 0
                    
                    volatilities.append({
                        "timestamp": ts,
                        "zone_name": zone_name,
                        "volatility": volatility,
                        "window_hours": window_hours,
                        "mean_price": mean_price,
                        "std_dev": std_dev
                    })
        
        volatilities.sort(key=lambda x: x["timestamp"], reverse=True)
        return volatilities[:limit]
    finally:
        db.close()


@app.get("/api/correlations", response_model=List[CorrelationResponse])
async def get_correlations(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    zones: Optional[str] = Query(None, description="Comma-separated zone names (default: all)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum zone pairs to return")
):
    """Calculate zone-to-zone price correlations.
    
    Computes Pearson correlation coefficient between zone prices over the time period.
    """
    db = next(get_db())
    
    try:
        query = db.query(
            RealTimeLBMP.timestamp,
            Zone.name.label('zone_name'),
            RealTimeLBMP.lbmp
        ).join(Zone).filter(RealTimeLBMP.zone_id == Zone.id)
        
        if start_date:
            query = query.filter(RealTimeLBMP.timestamp >= start_date)
        if end_date:
            query = query.filter(RealTimeLBMP.timestamp <= end_date)
        if zones:
            zone_list = [z.strip().upper() for z in zones.split(',')]
            query = query.filter(Zone.name.in_(zone_list))
        
        results = query.order_by(RealTimeLBMP.timestamp).all()
        
        # Group by timestamp, then by zone
        by_timestamp = {}
        zones_set = set()
        for r in results:
            if r.timestamp not in by_timestamp:
                by_timestamp[r.timestamp] = {}
            by_timestamp[r.timestamp][r.zone_name] = r.lbmp
            zones_set.add(r.zone_name)
        
        # Calculate correlations for all zone pairs
        correlations = []
        zones_list = sorted(zones_set)
        
        for i, zone1 in enumerate(zones_list):
            for zone2 in zones_list[i+1:]:
                prices1 = []
                prices2 = []
                
                for ts in sorted(by_timestamp.keys()):
                    if zone1 in by_timestamp[ts] and zone2 in by_timestamp[ts]:
                        prices1.append(by_timestamp[ts][zone1])
                        prices2.append(by_timestamp[ts][zone2])
                
                if len(prices1) >= 2:
                    try:
                        # Calculate Pearson correlation coefficient
                        mean1 = statistics.mean(prices1)
                        mean2 = statistics.mean(prices2)
                        std1 = statistics.stdev(prices1) if len(prices1) > 1 else 0
                        std2 = statistics.stdev(prices2) if len(prices2) > 1 else 0
                        
                        if std1 == 0 or std2 == 0:
                            correlation = 0.0
                        else:
                            covariance = sum((p1 - mean1) * (p2 - mean2) for p1, p2 in zip(prices1, prices2)) / len(prices1)
                            correlation = covariance / (std1 * std2)
                    except:
                        correlation = 0.0
                    
                    if start_date and end_date:
                        period_start = start_date
                        period_end = end_date
                    else:
                        timestamps = sorted(by_timestamp.keys())
                        period_start = timestamps[0] if timestamps else datetime.utcnow()
                        period_end = timestamps[-1] if timestamps else datetime.utcnow()
                    
                    correlations.append({
                        "zone1": zone1,
                        "zone2": zone2,
                        "correlation": correlation,
                        "sample_count": len(prices1),
                        "period_start": period_start,
                        "period_end": period_end
                    })
        
        # Sort by absolute correlation (descending)
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return correlations[:limit]
    finally:
        db.close()


@app.get("/api/trading-signals", response_model=List[TradingSignalResponse])
async def get_trading_signals(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum signals to return")
):
    """Generate trading signals based on market conditions.
    
    Rule-based signal generation from various market metrics.
    """
    db = next(get_db())
    
    try:
        signals = []
        now = datetime.utcnow()
        lookback = start_date if start_date else now - timedelta(hours=24)
        lookforward = end_date if end_date else now
        
        # Signal 1: High RT-DA Spreads
        rt_da_query = db.query(
            RealTimeLBMP.timestamp,
            Zone.name.label('zone_name'),
            RealTimeLBMP.lbmp.label('rt_lbmp')
        ).join(Zone).filter(
            RealTimeLBMP.timestamp >= lookback,
            RealTimeLBMP.timestamp <= lookforward
        )
        
        da_query = db.query(
            DayAheadLBMP.timestamp,
            Zone.name.label('zone_name'),
            DayAheadLBMP.lbmp.label('da_lbmp')
        ).join(Zone).filter(
            DayAheadLBMP.timestamp >= lookback,
            DayAheadLBMP.timestamp <= lookforward
        )
        
        rt_data = {(r.timestamp, r.zone_name): r.rt_lbmp for r in rt_da_query.all()}
        da_data = {(r.timestamp, r.zone_name): r.da_lbmp for r in da_query.all()}
        
        for (ts, zone), rt_lbmp in rt_data.items():
            if (ts, zone) in da_data:
                spread = rt_lbmp - da_data[(ts, zone)]
                if abs(spread) >= 15.0:  # $15/MWh threshold
                    signals.append({
                        "timestamp": ts,
                        "signal_type": "rt_da_spread",
                        "severity": "high" if abs(spread) >= 25.0 else "medium",
                        "zone_name": zone,
                        "message": f"RT-DA spread of ${spread:.2f}/MWh in {zone}",
                        "value": spread,
                        "threshold": 15.0
                    })
        
        # Signal 2: High Load Forecast Errors
        forecast_query = db.query(
            LoadForecast.timestamp,
            Zone.name.label('zone_name'),
            LoadForecast.forecast_load
        ).join(Zone).filter(
            LoadForecast.timestamp >= lookback,
            LoadForecast.timestamp <= lookforward
        )
        
        actual_query = db.query(
            RealTimeLoad.timestamp,
            Zone.name.label('zone_name'),
            RealTimeLoad.load.label('actual_load')
        ).join(Zone).filter(
            RealTimeLoad.timestamp >= lookback,
            RealTimeLoad.timestamp <= lookforward
        )
        
        forecast_data = {(r.timestamp, r.zone_name): r.forecast_load for r in forecast_query.all()}
        actual_data = {(r.timestamp, r.zone_name): r.actual_load for r in actual_query.all()}
        
        for (ts, zone), forecast_load in forecast_data.items():
            if (ts, zone) in actual_data:
                error_pct = abs((actual_data[(ts, zone)] - forecast_load) / forecast_load * 100) if forecast_load != 0 else 0
                if error_pct >= 5.0:  # 5% threshold
                    signals.append({
                        "timestamp": ts,
                        "signal_type": "load_forecast_error",
                        "severity": "high" if error_pct >= 10.0 else "medium",
                        "zone_name": zone,
                        "message": f"Load forecast error of {error_pct:.1f}% in {zone}",
                        "value": error_pct,
                        "threshold": 5.0
                    })
        
        # Signal 3: Low Reserve Margins
        load_query = db.query(
            RealTimeLoad.timestamp,
            func.sum(RealTimeLoad.load).label('total_load')
        ).filter(
            RealTimeLoad.timestamp >= lookback,
            RealTimeLoad.timestamp <= lookforward
        ).group_by(RealTimeLoad.timestamp)
        
        gen_query = db.query(
            FuelMix.timestamp,
            func.sum(FuelMix.generation_mw).label('total_generation')
        ).filter(
            FuelMix.timestamp >= lookback,
            FuelMix.timestamp <= lookforward
        ).group_by(FuelMix.timestamp)
        
        load_data = {r.timestamp: r.total_load for r in load_query.all()}
        gen_data = {r.timestamp: r.total_generation for r in gen_query.all()}
        
        for ts in set(load_data.keys()) & set(gen_data.keys()):
            total_load = load_data[ts]
            total_gen = gen_data[ts]
            if total_load and total_gen:
                reserve_pct = (total_gen - total_load) / total_load * 100
                if reserve_pct < 10.0:  # 10% threshold
                    signals.append({
                        "timestamp": ts,
                        "signal_type": "low_reserve_margin",
                        "severity": "high" if reserve_pct < 5.0 else "medium",
                        "zone_name": None,
                        "message": f"Low reserve margin of {reserve_pct:.1f}%",
                        "value": reserve_pct,
                        "threshold": 10.0
                    })
        
        # Filter and sort
        if signal_type:
            signals = [s for s in signals if s["signal_type"] == signal_type]
        if severity:
            signals = [s for s in signals if s["severity"] == severity.lower()]
        
        signals.sort(key=lambda x: x["timestamp"], reverse=True)
        return signals[:limit]
    finally:
        db.close()


@app.get("/api/maps/nyiso-zones")
async def get_nyiso_zones():
    """
    Get NYISO zone boundaries as GeoJSON.
    Returns zone polygons generated from zone definitions.
    """
    try:
        # Path to static GeoJSON file
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        geojson_file = project_root / "static" / "nyiso_zones.geojson"
        
        # If file doesn't exist, return helpful error
        if not geojson_file.exists():
            raise HTTPException(
                status_code=404,
                detail="GeoJSON file not found. Please run 'python3 scripts/generate_nyiso_zones.py' or 'python3 scripts/fetch_nyiso_zones.py' to generate the zone boundaries file."
            )
        
        # Read and return the cached file
        with open(geojson_file, 'r') as f:
            geojson_data = json.load(f)
        
        return JSONResponse(
            content=geojson_data,
            headers={
                "Content-Type": "application/geo+json",
                "Cache-Control": "no-cache, no-store, must-revalidate",  # Disable caching to ensure fresh polygons
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="NYISO zones GeoJSON file not found. Please run scripts/fetch_nyiso_zones.py first."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading NYISO zones: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway/deployment monitoring."""
    try:
        db = next(get_db())
        # Simple query to test database connection
        db.query(Zone).limit(1).all()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        # Return 200 with degraded status instead of 503
        # This allows Railway to see the app as running even if DB isn't ready
        # The app can still serve static files and respond to requests
        return {
            "status": "degraded", 
            "database": "disconnected",
            "error": str(e),
            "message": "API is running but database connection failed"
        }


# Serve static frontend files (for production deployment)
# This allows the API to serve the React frontend
# Check for static directory (production) or frontend/dist (development)
static_dir = Path(__file__).parent.parent / "static"
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"

# Determine which directory to use
if static_dir.exists():
    # Production: static directory contains built frontend
    frontend_root = static_dir
elif frontend_dist.exists():
    # Development: frontend/dist exists
    frontend_root = frontend_dist
else:
    frontend_root = None

if frontend_root:
    # Mount static assets (JS, CSS, images, etc.) from assets subdirectory
    assets_dir = frontend_root / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    # Serve index.html for all non-API routes (SPA routing)
    # This catch-all route must be defined AFTER all API routes
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React frontend for all non-API routes (SPA catch-all)."""
        # Don't serve frontend for API routes, docs, or static assets
        if (full_path.startswith("api/") or 
            full_path.startswith("docs") or 
            full_path.startswith("redoc") or
            full_path.startswith("openapi.json") or
            full_path.startswith("assets/")):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Serve index.html for SPA routing (React Router)
        index_file = frontend_root / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            raise HTTPException(
                status_code=404, 
                detail="Frontend not built. Run 'npm run build' in frontend directory."
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

