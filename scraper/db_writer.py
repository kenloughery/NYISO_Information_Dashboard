"""
Database writer with upsert logic and transaction management.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from database.schema import (
    DataSource, ScrapingJob, ScrapingLog, Zone, Interface,
    RealTimeLBMP, DayAheadLBMP, TimeWeightedLBMP, RealTimeLoad,
    LoadForecast, InterfaceFlow, AncillaryService,
    MarketAdvisory, Constraint, ExternalRTOPrice, ATC_TTC,
    Outage, WeatherForecast, FuelMix
)

logger = logging.getLogger(__name__)


class DatabaseWriter:
    """Writes parsed data to database with upsert logic."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
    
    def get_or_create_zone(self, name: str, ptid: Optional[int] = None) -> Zone:
        """Get or create zone."""
        zone = self.session.query(Zone).filter(Zone.name == name.upper()).first()
        if not zone:
            zone = Zone(name=name.upper(), ptid=ptid)
            self.session.add(zone)
            self.session.flush()
        elif ptid and not zone.ptid:
            zone.ptid = ptid
        return zone
    
    def get_or_create_interface(self, name: str, point_id: Optional[int] = None) -> Interface:
        """Get or create interface."""
        interface = self.session.query(Interface).filter(Interface.name == name).first()
        if not interface:
            interface = Interface(name=name, point_id=point_id)
            self.session.add(interface)
            self.session.flush()
        elif point_id and not interface.point_id:
            interface.point_id = point_id
        return interface
    
    def upsert_realtime_lbmp(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert real-time LBMP records."""
        inserted = 0
        updated = 0
        
        for record in records:
            zone = self.get_or_create_zone(record['zone_name'], record.get('ptid'))
            
            existing = self.session.query(RealTimeLBMP).filter(
                and_(
                    RealTimeLBMP.timestamp == record['timestamp'],
                    RealTimeLBMP.zone_id == zone.id
                )
            ).first()
            
            if existing:
                existing.lbmp = record.get('lbmp')
                existing.marginal_cost_losses = record.get('marginal_cost_losses')
                existing.marginal_cost_congestion = record.get('marginal_cost_congestion')
                updated += 1
            else:
                new_record = RealTimeLBMP(
                    timestamp=record['timestamp'],
                    zone_id=zone.id,
                    ptid=record.get('ptid'),
                    lbmp=record.get('lbmp'),
                    marginal_cost_losses=record.get('marginal_cost_losses'),
                    marginal_cost_congestion=record.get('marginal_cost_congestion')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_dayahead_lbmp(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert day-ahead LBMP records."""
        inserted = 0
        updated = 0
        
        for record in records:
            zone = self.get_or_create_zone(record['zone_name'], record.get('ptid'))
            
            existing = self.session.query(DayAheadLBMP).filter(
                and_(
                    DayAheadLBMP.timestamp == record['timestamp'],
                    DayAheadLBMP.zone_id == zone.id
                )
            ).first()
            
            if existing:
                existing.lbmp = record.get('lbmp')
                existing.marginal_cost_losses = record.get('marginal_cost_losses')
                existing.marginal_cost_congestion = record.get('marginal_cost_congestion')
                updated += 1
            else:
                new_record = DayAheadLBMP(
                    timestamp=record['timestamp'],
                    zone_id=zone.id,
                    ptid=record.get('ptid'),
                    lbmp=record.get('lbmp'),
                    marginal_cost_losses=record.get('marginal_cost_losses'),
                    marginal_cost_congestion=record.get('marginal_cost_congestion')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_timeweighted_lbmp(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert time-weighted LBMP records."""
        inserted = 0
        updated = 0
        
        for record in records:
            zone = self.get_or_create_zone(record['zone_name'], record.get('ptid'))
            
            existing = self.session.query(TimeWeightedLBMP).filter(
                and_(
                    TimeWeightedLBMP.timestamp == record['timestamp'],
                    TimeWeightedLBMP.zone_id == zone.id
                )
            ).first()
            
            if existing:
                existing.lbmp = record.get('lbmp')
                existing.marginal_cost_losses = record.get('marginal_cost_losses')
                existing.marginal_cost_congestion = record.get('marginal_cost_congestion')
                updated += 1
            else:
                new_record = TimeWeightedLBMP(
                    timestamp=record['timestamp'],
                    zone_id=zone.id,
                    ptid=record.get('ptid'),
                    lbmp=record.get('lbmp'),
                    marginal_cost_losses=record.get('marginal_cost_losses'),
                    marginal_cost_congestion=record.get('marginal_cost_congestion')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_realtime_load(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert real-time load records."""
        inserted = 0
        updated = 0
        
        for record in records:
            zone = self.get_or_create_zone(record['zone_name'], record.get('ptid'))
            
            existing = self.session.query(RealTimeLoad).filter(
                and_(
                    RealTimeLoad.timestamp == record['timestamp'],
                    RealTimeLoad.zone_id == zone.id
                )
            ).first()
            
            if existing:
                existing.load = record.get('load')
                existing.time_zone = record.get('time_zone')
                updated += 1
            else:
                new_record = RealTimeLoad(
                    timestamp=record['timestamp'],
                    zone_id=zone.id,
                    ptid=record.get('ptid'),
                    load=record.get('load'),
                    time_zone=record.get('time_zone')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_load_forecast(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert load forecast records."""
        inserted = 0
        updated = 0
        
        for record in records:
            zone = self.get_or_create_zone(record['zone_name'])
            
            existing = self.session.query(LoadForecast).filter(
                and_(
                    LoadForecast.timestamp == record['timestamp'],
                    LoadForecast.zone_id == zone.id
                )
            ).first()
            
            if existing:
                existing.forecast_load = record.get('forecast_load')
                updated += 1
            else:
                new_record = LoadForecast(
                    timestamp=record['timestamp'],
                    zone_id=zone.id,
                    forecast_load=record.get('forecast_load')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_interface_flows(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert interface flow records."""
        inserted = 0
        updated = 0
        
        for record in records:
            interface = self.get_or_create_interface(
                record['interface_name'],
                record.get('point_id')
            )
            
            existing = self.session.query(InterfaceFlow).filter(
                and_(
                    InterfaceFlow.timestamp == record['timestamp'],
                    InterfaceFlow.interface_id == interface.id
                )
            ).first()
            
            if existing:
                existing.flow_mwh = record.get('flow_mwh')
                existing.positive_limit_mwh = record.get('positive_limit_mwh')
                existing.negative_limit_mwh = record.get('negative_limit_mwh')
                updated += 1
            else:
                new_record = InterfaceFlow(
                    timestamp=record['timestamp'],
                    interface_id=interface.id,
                    point_id=record.get('point_id'),
                    flow_mwh=record.get('flow_mwh'),
                    positive_limit_mwh=record.get('positive_limit_mwh'),
                    negative_limit_mwh=record.get('negative_limit_mwh')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_ancillary_services(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert ancillary service records."""
        inserted = 0
        updated = 0
        
        for record in records:
            zone = self.get_or_create_zone(record['zone_name'])
            
            existing = self.session.query(AncillaryService).filter(
                and_(
                    AncillaryService.timestamp == record['timestamp'],
                    AncillaryService.zone_id == zone.id,
                    AncillaryService.market_type == record['market_type'],
                    AncillaryService.service_type == record.get('service_type', 'regulation')
                )
            ).first()
            
            if existing:
                existing.price = record.get('price')
                updated += 1
            else:
                new_record = AncillaryService(
                    timestamp=record['timestamp'],
                    zone_id=zone.id,
                    market_type=record['market_type'],
                    service_type=record.get('service_type', 'regulation'),
                    price=record.get('price')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_market_advisory(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert market advisory records."""
        inserted = 0
        updated = 0
        
        for record in records:
            existing = self.session.query(MarketAdvisory).filter(
                and_(
                    MarketAdvisory.timestamp == record['timestamp'],
                    MarketAdvisory.title == record.get('title', '')
                )
            ).first()
            
            if existing:
                existing.advisory_type = record.get('advisory_type')
                existing.message = record.get('message')
                existing.severity = record.get('severity')
                updated += 1
            else:
                new_record = MarketAdvisory(
                    timestamp=record['timestamp'],
                    advisory_type=record.get('advisory_type'),
                    title=record.get('title', ''),
                    message=record.get('message'),
                    severity=record.get('severity')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_constraints(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert constraint records."""
        inserted = 0
        updated = 0
        
        for record in records:
            existing = self.session.query(Constraint).filter(
                and_(
                    Constraint.timestamp == record['timestamp'],
                    Constraint.constraint_name == record['constraint_name'],
                    Constraint.market_type == record['market_type']
                )
            ).first()
            
            if existing:
                existing.shadow_price = record.get('shadow_price')
                existing.binding_status = record.get('binding_status')
                existing.limit_mw = record.get('limit_mw')
                existing.flow_mw = record.get('flow_mw')
                updated += 1
            else:
                new_record = Constraint(
                    timestamp=record['timestamp'],
                    constraint_name=record['constraint_name'],
                    market_type=record['market_type'],
                    shadow_price=record.get('shadow_price'),
                    binding_status=record.get('binding_status'),
                    limit_mw=record.get('limit_mw'),
                    flow_mw=record.get('flow_mw')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_external_rto_prices(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert external RTO price records."""
        inserted = 0
        updated = 0
        
        for record in records:
            existing = self.session.query(ExternalRTOPrice).filter(
                and_(
                    ExternalRTOPrice.timestamp == record['timestamp'],
                    ExternalRTOPrice.rto_name == record['rto_name']
                )
            ).first()
            
            if existing:
                existing.rtc_price = record.get('rtc_price')
                existing.cts_price = record.get('cts_price')
                existing.price_difference = record.get('price_difference')
                updated += 1
            else:
                new_record = ExternalRTOPrice(
                    timestamp=record['timestamp'],
                    rto_name=record['rto_name'],
                    rtc_price=record.get('rtc_price'),
                    cts_price=record.get('cts_price'),
                    price_difference=record.get('price_difference')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_atc_ttc(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert ATC/TTC records."""
        inserted = 0
        updated = 0
        
        for record in records:
            interface = self.get_or_create_interface(record['interface_name'])
            
            existing = self.session.query(ATC_TTC).filter(
                and_(
                    ATC_TTC.timestamp == record['timestamp'],
                    ATC_TTC.interface_id == interface.id,
                    ATC_TTC.forecast_type == record['forecast_type'],
                    ATC_TTC.direction == record.get('direction', '')
                )
            ).first()
            
            if existing:
                existing.atc_mw = record.get('atc_mw')
                existing.ttc_mw = record.get('ttc_mw')
                existing.trm_mw = record.get('trm_mw')
                updated += 1
            else:
                new_record = ATC_TTC(
                    timestamp=record['timestamp'],
                    interface_id=interface.id,
                    forecast_type=record['forecast_type'],
                    atc_mw=record.get('atc_mw'),
                    ttc_mw=record.get('ttc_mw'),
                    trm_mw=record.get('trm_mw'),
                    direction=record.get('direction', '')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_outages(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert outage records."""
        inserted = 0
        updated = 0
        
        for record in records:
            # Use resource_name + timestamp + outage_type as unique key
            existing = self.session.query(Outage).filter(
                and_(
                    Outage.timestamp == record['timestamp'],
                    Outage.resource_name == record.get('resource_name', ''),
                    Outage.outage_type == record['outage_type']
                )
            ).first()
            
            if existing:
                existing.market_type = record.get('market_type')
                existing.resource_type = record.get('resource_type')
                existing.mw_capacity = record.get('mw_capacity')
                existing.mw_outage = record.get('mw_outage')
                existing.start_time = record.get('start_time')
                existing.end_time = record.get('end_time')
                existing.status = record.get('status')
                updated += 1
            else:
                new_record = Outage(
                    timestamp=record['timestamp'],
                    outage_type=record['outage_type'],
                    market_type=record.get('market_type'),
                    resource_name=record.get('resource_name', ''),
                    resource_type=record.get('resource_type'),
                    mw_capacity=record.get('mw_capacity'),
                    mw_outage=record.get('mw_outage'),
                    start_time=record.get('start_time'),
                    end_time=record.get('end_time'),
                    status=record.get('status')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_weather_forecast(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert weather forecast records."""
        inserted = 0
        updated = 0
        
        for record in records:
            # Unique constraint includes: timestamp, forecast_time, location, vintage, data_source
            data_source = record.get('data_source', 'NYISO')  # Default to NYISO for backward compatibility
            
            existing = self.session.query(WeatherForecast).filter(
                and_(
                    WeatherForecast.timestamp == record['timestamp'],
                    WeatherForecast.forecast_time == record['forecast_time'],
                    WeatherForecast.location == record.get('location', ''),
                    WeatherForecast.vintage == record.get('vintage'),
                    WeatherForecast.data_source == data_source
                )
            ).first()
            
            if existing:
                existing.temperature_f = record.get('temperature_f')
                existing.humidity_percent = record.get('humidity_percent')
                existing.wind_speed_mph = record.get('wind_speed_mph')
                existing.wind_direction = record.get('wind_direction')
                existing.cloud_cover_percent = record.get('cloud_cover_percent')
                # Update new fields if provided
                if 'zone_name' in record:
                    existing.zone_name = record.get('zone_name')
                if 'irradiance_w_m2' in record:
                    existing.irradiance_w_m2 = record.get('irradiance_w_m2')
                if 'data_source' in record:
                    existing.data_source = record.get('data_source')
                updated += 1
            else:
                new_record = WeatherForecast(
                    timestamp=record['timestamp'],
                    forecast_time=record['forecast_time'],
                    location=record.get('location', ''),
                    vintage=record.get('vintage'),
                    temperature_f=record.get('temperature_f'),
                    humidity_percent=record.get('humidity_percent'),
                    wind_speed_mph=record.get('wind_speed_mph'),
                    wind_direction=record.get('wind_direction'),
                    cloud_cover_percent=record.get('cloud_cover_percent'),
                    zone_name=record.get('zone_name'),
                    irradiance_w_m2=record.get('irradiance_w_m2'),
                    data_source=data_source
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def upsert_fuel_mix(self, records: List[Dict]) -> Tuple[int, int]:
        """Upsert fuel mix records."""
        inserted = 0
        updated = 0
        
        for record in records:
            existing = self.session.query(FuelMix).filter(
                and_(
                    FuelMix.timestamp == record['timestamp'],
                    FuelMix.fuel_type == record['fuel_type']
                )
            ).first()
            
            if existing:
                existing.generation_mw = record.get('generation_mw')
                existing.percentage = record.get('percentage')
                updated += 1
            else:
                new_record = FuelMix(
                    timestamp=record['timestamp'],
                    fuel_type=record['fuel_type'],
                    generation_mw=record.get('generation_mw'),
                    percentage=record.get('percentage')
                )
                self.session.add(new_record)
                inserted += 1
        
        return inserted, updated
    
    def write_records(
        self,
        records: List[Dict],
        report_code: str,
        job: ScrapingJob
    ) -> Tuple[int, int]:
        """
        Write records to appropriate table based on report code.
        
        Returns:
            Tuple of (inserted_count, updated_count)
        """
        try:
            if report_code == 'P-24A':
                inserted, updated = self.upsert_realtime_lbmp(records)
            elif report_code == 'P-2A':
                inserted, updated = self.upsert_dayahead_lbmp(records)
            elif report_code == 'P-4A':
                inserted, updated = self.upsert_timeweighted_lbmp(records)
            elif report_code == 'P-58B':
                inserted, updated = self.upsert_realtime_load(records)
            elif report_code == 'P-7':
                inserted, updated = self.upsert_load_forecast(records)
            elif report_code in ['P-32', 'P-32-CURRENT']:
                inserted, updated = self.upsert_interface_flows(records)
            elif report_code in ['P-6B', 'P-5']:
                inserted, updated = self.upsert_ancillary_services(records)
            elif report_code == 'P-31':
                inserted, updated = self.upsert_market_advisory(records)
            elif report_code in ['P-33', 'P-511A']:
                inserted, updated = self.upsert_constraints(records)
            elif report_code == 'P-42':
                inserted, updated = self.upsert_external_rto_prices(records)
            elif report_code in ['P-8', 'P-8A']:
                inserted, updated = self.upsert_atc_ttc(records)
            elif report_code in ['P-54A', 'P-54B', 'P-54C', 'P-14B', 'P-15']:
                inserted, updated = self.upsert_outages(records)
            elif report_code == 'P-7A':
                inserted, updated = self.upsert_weather_forecast(records)
            elif report_code == 'P-63':
                inserted, updated = self.upsert_fuel_mix(records)
            else:
                logger.warning(f"Unknown report code: {report_code}, skipping write")
                return 0, 0
            
            self.session.commit()
            logger.info(f"Wrote {inserted} new, {updated} updated records for {report_code}")
            return inserted, updated
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error writing records: {str(e)}")
            raise

