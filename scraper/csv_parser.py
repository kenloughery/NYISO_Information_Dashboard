"""
CSV parser with dynamic schema detection and validation.
Handles different NYISO data formats.
"""
import io
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class CSVParseError(Exception):
    """Custom exception for CSV parsing errors."""
    pass


class NYISOCSVParser:
    """Parses NYISO CSV files with schema detection."""
    
    # Date format patterns to try
    DATE_FORMATS = [
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',  # Date only (for weather data)
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',  # Date only
    ]
    
    def __init__(self):
        """Initialize parser."""
        pass
    
    def parse(self, csv_content: str, data_type: str) -> pd.DataFrame:
        """
        Parse CSV content into DataFrame.
        
        Args:
            csv_content: CSV content as string
            data_type: Type of data (for schema-specific handling)
            
        Returns:
            Parsed DataFrame
            
        Raises:
            CSVParseError: If parsing fails
        """
        try:
            # Read CSV
            df = pd.read_csv(
                io.StringIO(csv_content),
                skipinitialspace=True,
                low_memory=False
            )
            
            if df.empty:
                raise CSVParseError("CSV file is empty")
            
            # Normalize column names
            df.columns = df.columns.str.strip()
            
            # Parse timestamps
            df = self._parse_timestamps(df)
            
            # Validate and clean data
            df = self._clean_data(df, data_type)
            
            logger.info(f"Parsed {len(df)} rows from {data_type}")
            return df
            
        except Exception as e:
            raise CSVParseError(f"Failed to parse CSV: {str(e)}")
    
    def _parse_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse timestamp columns."""
        timestamp_cols = [col for col in df.columns 
                         if any(kw in col.lower() for kw in ['time', 'date', 'timestamp'])]
        
        main_timestamp_col = None
        for col in timestamp_cols:
            if col in df.columns:
                # Skip 'Vintage Date' - it will be handled separately for weather data
                if col == 'Vintage Date':
                    # Parse Vintage Date but don't rename it
                    parsed = None
                    for fmt in self.DATE_FORMATS:
                        try:
                            parsed = pd.to_datetime(df[col], format=fmt, errors='coerce')
                            if parsed.notna().sum() > 0:
                                break
                        except:
                            continue
                    
                    # Fallback to pandas auto-detection
                    if parsed is None or parsed.isna().all():
                        parsed = pd.to_datetime(df[col], errors='coerce')
                    
                    df[col] = parsed
                    continue
                
                # Try different date formats
                parsed = None
                for fmt in self.DATE_FORMATS:
                    try:
                        parsed = pd.to_datetime(df[col], format=fmt, errors='coerce')
                        if parsed.notna().sum() > 0:
                            break
                    except:
                        continue
                
                # Fallback to pandas auto-detection
                if parsed is None or parsed.isna().all():
                    parsed = pd.to_datetime(df[col], errors='coerce')
                
                df[col] = parsed
                
                # Identify main timestamp column (prefer 'timestamp' or 'time stamp' or 'Forecast Date')
                if main_timestamp_col is None:
                    if 'timestamp' in col.lower() or (col.lower() == 'time stamp'):
                        main_timestamp_col = col
                    elif col == 'Forecast Date':
                        # For weather data, use Forecast Date as main timestamp
                        main_timestamp_col = col
        
        # Rename main timestamp column to standard 'timestamp'
        if main_timestamp_col and main_timestamp_col != 'timestamp':
            df = df.rename(columns={main_timestamp_col: 'timestamp'})
        
        return df
    
    def _clean_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Clean and validate data based on type."""
        # Remove rows with null timestamps
        timestamp_col = next((col for col in df.columns 
                            if 'timestamp' in col.lower()), None)
        if timestamp_col:
            initial_count = len(df)
            df = df[df[timestamp_col].notna()].copy()
            if len(df) < initial_count:
                logger.warning(f"Removed {initial_count - len(df)} rows with null timestamps")
        
        # Convert numeric columns
        numeric_keywords = ['lbmp', 'price', 'load', 'flow', 'limit', 'cost', 'mwh']
        for col in df.columns:
            if any(kw in col.lower() for kw in numeric_keywords):
                if df[col].dtype == 'object':
                    # Remove currency symbols and convert
                    df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def transform_for_database(
        self,
        df: pd.DataFrame,
        data_type: str,
        report_code: str
    ) -> List[Dict[str, Any]]:
        """
        Transform DataFrame to database-ready format.
        
        Args:
            df: Parsed DataFrame
            data_type: Type of data
            report_code: Report code for routing
            
        Returns:
            List of dictionaries ready for database insertion
        """
        records = []
        
        # Get timestamp column - check for 'timestamp' first, then 'time stamp', then any time-related column
        timestamp_col = None
        if 'timestamp' in df.columns:
            timestamp_col = 'timestamp'
        elif 'Time Stamp' in df.columns:
            timestamp_col = 'Time Stamp'
        else:
            timestamp_col = next((col for col in df.columns 
                                if any(kw in col.lower() for kw in ['time', 'timestamp', 'date'])), None)
        
        if not timestamp_col:
            raise CSVParseError(f"No timestamp column found. Available columns: {list(df.columns)}")
        
        # Route to appropriate transformer based on report code
        if report_code == 'P-24A':  # Real-Time Zonal LBMP
            records = self._transform_realtime_lbmp(df, timestamp_col)
        elif report_code == 'P-2A':  # Day-Ahead Zonal LBMP
            records = self._transform_dayahead_lbmp(df, timestamp_col)
        elif report_code == 'P-4A':  # Time-Weighted RT LBMP
            records = self._transform_timeweighted_lbmp(df, timestamp_col)
        elif report_code == 'P-58B':  # Real-Time Actual Load
            records = self._transform_realtime_load(df, timestamp_col)
        elif report_code == 'P-7':  # ISO Load Forecast
            records = self._transform_load_forecast(df, timestamp_col)
        elif report_code in ['P-32', 'P-32-CURRENT']:  # Interface Limits & Flows
            records = self._transform_interface_flows(df, timestamp_col)
        elif report_code in ['P-6B', 'P-5']:  # Ancillary Services
            records = self._transform_ancillary_services(df, timestamp_col, report_code)
        elif report_code == 'P-31':  # Market Advisory
            records = self._transform_market_advisory(df, timestamp_col)
        elif report_code == 'P-33':  # Real-Time Constraints
            records = self._transform_constraints(df, timestamp_col, 'realtime')
        elif report_code == 'P-511A':  # Day-Ahead Constraints
            records = self._transform_constraints(df, timestamp_col, 'dayahead')
        elif report_code == 'P-42':  # External RTO Prices
            records = self._transform_external_rto_prices(df, timestamp_col)
        elif report_code == 'P-8':  # Short-term ATC/TTC
            records = self._transform_atc_ttc(df, timestamp_col, 'short_term')
        elif report_code == 'P-8A':  # Long-term ATC/TTC
            records = self._transform_atc_ttc(df, timestamp_col, 'long_term')
        elif report_code == 'P-54A':  # Real-Time Scheduled Outages
            records = self._transform_outages(df, timestamp_col, 'scheduled', 'realtime')
        elif report_code == 'P-54B':  # Real-Time Actual Outages
            records = self._transform_outages(df, timestamp_col, 'actual', 'realtime')
        elif report_code == 'P-54C':  # Day-Ahead Scheduled Outages
            records = self._transform_outages(df, timestamp_col, 'scheduled', 'dayahead')
        elif report_code == 'P-14B':  # Outage Schedules
            records = self._transform_outages(df, timestamp_col, 'scheduled', None)
        elif report_code == 'P-15':  # Generation Maintenance
            records = self._transform_outages(df, timestamp_col, 'maintenance', None)
        elif report_code == 'P-7A':  # Weather Forecast
            records = self._transform_weather_forecast(df, timestamp_col)
        elif report_code == 'P-63':  # Real-Time Fuel Mix
            records = self._transform_fuel_mix(df, timestamp_col)
        else:
            # Generic transformation
            records = self._transform_generic(df, timestamp_col)
        
        return records
    
    def _transform_realtime_lbmp(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform real-time LBMP data."""
        records = []
        for _, row in df.iterrows():
            records.append({
                'timestamp': row[timestamp_col],
                'zone_name': row.get('Name', ''),
                'ptid': row.get('PTID'),
                'lbmp': row.get('LBMP ($/MWHr)'),
                'marginal_cost_losses': row.get('Marginal Cost Losses ($/MWHr)'),
                'marginal_cost_congestion': row.get('Marginal Cost Congestion ($/MWHr)'),
            })
        return records
    
    def _transform_dayahead_lbmp(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform day-ahead LBMP data."""
        return self._transform_realtime_lbmp(df, timestamp_col)  # Same structure
    
    def _transform_timeweighted_lbmp(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform time-weighted LBMP data."""
        return self._transform_realtime_lbmp(df, timestamp_col)  # Same structure
    
    def _transform_realtime_load(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform real-time load data."""
        records = []
        for _, row in df.iterrows():
            time_zone = row.get('Time Zone', '')
            # Handle pandas NaT/NaN values
            if pd.isna(time_zone):
                time_zone = None
            elif isinstance(time_zone, str):
                time_zone = time_zone.strip() if time_zone else None
            else:
                time_zone = str(time_zone) if time_zone else None
            
            records.append({
                'timestamp': row[timestamp_col],
                'zone_name': row.get('Name', ''),
                'ptid': row.get('PTID'),
                'load': row.get('Load'),
                'time_zone': time_zone,
            })
        return records
    
    def _transform_load_forecast(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform load forecast data (wide format)."""
        records = []
        zone_columns = [col for col in df.columns 
                       if col != timestamp_col and col != 'NYISO']
        
        for _, row in df.iterrows():
            for zone_col in zone_columns:
                records.append({
                    'timestamp': row[timestamp_col],
                    'zone_name': zone_col.upper(),
                    'forecast_load': row.get(zone_col),
                })
        return records
    
    def _transform_interface_flows(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform interface flows data."""
        records = []
        for _, row in df.iterrows():
            records.append({
                'timestamp': row[timestamp_col],
                'interface_name': row.get('Interface Name', ''),
                'point_id': row.get('Point ID'),
                'flow_mwh': row.get('Flow (MWH)'),
                'positive_limit_mwh': row.get('Positive Limit (MWH)'),
                'negative_limit_mwh': row.get('Negative Limit (MWH)'),
            })
        return records
    
    def _transform_ancillary_services(self, df: pd.DataFrame, timestamp_col: str, report_code: str) -> List[Dict]:
        """Transform ancillary services data.
        
        CSV has multiple service type columns:
        - 10 Min Spinning Reserve ($/MWHr)
        - 10 Min Non-Synchronous Reserve ($/MWHr)
        - 30 Min Operating Reserve ($/MWHr)
        - NYCA Regulation Capacity ($/MWHr)
        - NYCA Regulation Movement ($/MW)
        """
        records = []
        market_type = 'realtime' if report_code == 'P-6B' else 'dayahead'
        
        # Map column names to service types
        service_columns = {
            '10 Min Spinning Reserve ($/MWHr)': 'spinning_reserve',
            '10 Min Non-Synchronous Reserve ($/MWHr)': 'non_sync_reserve',
            '30 Min Operating Reserve ($/MWHr)': 'operating_reserve',
            'NYCA Regulation Capacity ($/MWHr)': 'regulation_capacity',
            'NYCA Regulation Movement ($/MW)': 'regulation_movement',
        }
        
        for _, row in df.iterrows():
            zone_name = row.get('Name', '')
            timestamp = row[timestamp_col]
            
            # Create a record for each service type that has a price
            for col_name, service_type in service_columns.items():
                if col_name in df.columns:
                    price = row.get(col_name)
                    # Only create record if price is not null/zero
                    if price is not None and not pd.isna(price) and price != 0:
                        records.append({
                            'timestamp': timestamp,
                            'zone_name': zone_name,
                            'market_type': market_type,
                            'service_type': service_type,
                            'price': float(price) if price else None,
                        })
        
        return records
    
    def _transform_market_advisory(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform market advisory data.
        
        Note: P-31 (HAM_energy_rep.csv) is actually hourly energy data, not advisory notifications.
        This transformation handles both formats.
        """
        records = []
        
        # Check if this is the HAM energy report format (has Start Time/End Time)
        if 'Start Time' in df.columns:
            # This is hourly energy data, not advisory notifications
            # Store as advisory with energy report type
            for _, row in df.iterrows():
                start_time = row.get('Start Time', '')
                end_time = row.get('End Time', '')
                
                # Skip Total rows
                if pd.isna(start_time) or str(start_time).strip().lower() == 'total':
                    continue
                
                # Use Start Time as timestamp
                try:
                    timestamp = pd.to_datetime(start_time)
                except:
                    continue
                
                # Create a summary message with key metrics
                gen_scheduled = row.get('Generation Scheduled', 0)
                net_imports = row.get('Net Imports', 0)
                
                records.append({
                    'timestamp': timestamp,
                    'advisory_type': 'HAM_Energy_Report',
                    'title': f'Hour-Ahead Market Energy Report: {start_time} - {end_time}',
                    'message': f'Generation Scheduled: {gen_scheduled:.1f} MW, Net Imports: {net_imports:.1f} MW',
                    'severity': 'info',
                })
        else:
            # Standard advisory format
            for _, row in df.iterrows():
                timestamp = row.get(timestamp_col)
                
                # Skip rows with invalid timestamps
                if pd.isna(timestamp):
                    continue
                
                records.append({
                    'timestamp': timestamp,
                    'advisory_type': row.get('Advisory Type', '') or None,
                    'title': row.get('Title', '') or None,
                    'message': row.get('Message', '') or None,
                    'severity': row.get('Severity', '') or None,
                })
        
        return records
    
    def _transform_constraints(self, df: pd.DataFrame, timestamp_col: str, market_type: str) -> List[Dict]:
        """Transform constraints data."""
        records = []
        for _, row in df.iterrows():
            records.append({
                'timestamp': row[timestamp_col],
                'constraint_name': row.get('Constraint Name', '') or row.get('Name', ''),
                'market_type': market_type,
                'shadow_price': row.get('Shadow Price', None) or row.get('Price', None),
                'binding_status': row.get('Binding Status', '') or row.get('Status', ''),
                'limit_mw': row.get('Limit (MW)', None) or row.get('Limit', None),
                'flow_mw': row.get('Flow (MW)', None) or row.get('Flow', None),
            })
        return records
    
    def _transform_external_rto_prices(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform external RTO prices data.
        
        CSV structure:
        - RTC Execution Time: Start timestamp
        - RTC End Time Stamp: End timestamp (use this as primary timestamp)
        - Gen Name: Generator name with embedded RTO (e.g., "N.E._GEN_SANDY PD" = ISO-NE)
        - Gen LBMP: NYISO RTC price
        - External RTO CTS Price: External RTO CTS price
        """
        records = []
        
        # Determine timestamp column (prefer RTC End Time Stamp, fallback to RTC Execution Time)
        end_timestamp_col = 'RTC End Time Stamp' if 'RTC End Time Stamp' in df.columns else timestamp_col
        
        # RTO name mapping from Gen Name patterns
        def extract_rto_name(gen_name: str) -> str:
            """Extract RTO name from generator name."""
            if pd.isna(gen_name):
                return ''
            gen_name_upper = str(gen_name).upper()
            
            # Check for RTO patterns in order of specificity
            if 'ISO-NE' in gen_name_upper or 'N.E.' in gen_name_upper or 'NE_' in gen_name_upper:
                return 'ISO-NE'
            elif 'PJM' in gen_name_upper:
                return 'PJM'
            elif 'IESO' in gen_name_upper:
                return 'IESO'
            else:
                # Try to extract from common patterns
                if gen_name_upper.startswith('N.E.') or gen_name_upper.startswith('NE_'):
                    return 'ISO-NE'
                elif gen_name_upper.startswith('PJM'):
                    return 'PJM'
                elif gen_name_upper.startswith('IESO'):
                    return 'IESO'
            
            return ''
        
        for _, row in df.iterrows():
            gen_name = row.get('Gen Name', '') or row.get('Generator Name', '')
            rto_name = extract_rto_name(gen_name)
            
            # Skip if we can't identify the RTO
            if not rto_name:
                continue
            
            # Get prices
            rtc_price = row.get('Gen LBMP', None) or row.get('RTC Price', None) or row.get('RTC', None)
            cts_price = row.get('External RTO CTS Price', None) or row.get('CTS Price', None) or row.get('CTS', None)
            
            # Convert to float, handling NaN
            try:
                rtc_price = float(rtc_price) if rtc_price is not None and not pd.isna(rtc_price) else None
                cts_price = float(cts_price) if cts_price is not None and not pd.isna(cts_price) else None
            except (ValueError, TypeError):
                rtc_price = None
                cts_price = None
            
            # Calculate price difference
            price_difference = None
            if rtc_price is not None and cts_price is not None:
                price_difference = rtc_price - cts_price
            
            # Use RTC End Time Stamp as the primary timestamp
            timestamp = row[end_timestamp_col] if end_timestamp_col in df.columns else row[timestamp_col]
            
            records.append({
                'timestamp': timestamp,
                'rto_name': rto_name,
                'rtc_price': rtc_price,
                'cts_price': cts_price,
                'price_difference': price_difference,
            })
        
        return records
    
    def _transform_atc_ttc(self, df: pd.DataFrame, timestamp_col: str, forecast_type: str) -> List[Dict]:
        """Transform ATC/TTC data.
        
        For short_term (P-8), the CSV has a wide format with multiple time-based columns:
        - TTC (DAM), ATC (DAM) - Day-Ahead Market
        - TTC (HAM) xx:00, ATC (HAM) xx:00 - Hour-Ahead Market :00
        - TTC (HAM) xx:15, ATC (HAM) xx:15 - Hour-Ahead Market :15
        - TTC (HAM) xx:30, ATC (HAM) xx:30 - Hour-Ahead Market :30
        - TTC (HAM) xx:45, ATC (HAM) xx:45 - Hour-Ahead Market :45
        
        We create separate records for each forecast time.
        """
        records = []
        
        if forecast_type == 'short_term':
            # P-8 has wide format with multiple time columns
            # We'll store the HAM :00 forecast (most recent/relevant) as the primary value
            # HAM (Hour-Ahead Market) forecasts are more current than DAM (Day-Ahead Market)
            for _, row in df.iterrows():
                interface_name = row.get('Interface Name', '') or row.get('Interface', '')
                base_timestamp = row[timestamp_col]
                
                # Prefer HAM :00 (most recent forecast), fallback to DAM if HAM not available
                ttc_value = None
                atc_value = None
                
                # Try HAM :00 first (most current)
                if 'TTC (HAM) xx:00' in df.columns and 'ATC (HAM) xx:00' in df.columns:
                    ttc_ham = row.get('TTC (HAM) xx:00', None)
                    atc_ham = row.get('ATC (HAM) xx:00', None)
                    # Handle both NaN and valid numeric values (including 0)
                    if pd.notna(ttc_ham):
                        ttc_value = float(ttc_ham)
                    if pd.notna(atc_ham):
                        atc_value = float(atc_ham)
                
                # Fallback to DAM if HAM values are still None
                if ttc_value is None and atc_value is None:
                    if 'TTC (DAM)' in df.columns and 'ATC (DAM)' in df.columns:
                        ttc_dam = row.get('TTC (DAM)', None)
                        atc_dam = row.get('ATC (DAM)', None)
                        if pd.notna(ttc_dam):
                            ttc_value = float(ttc_dam)
                        if pd.notna(atc_dam):
                            atc_value = float(atc_dam)
                
                # Create record if we have at least one value (including 0, which is valid)
                # Only skip if both are None (truly missing)
                if ttc_value is not None or atc_value is not None:
                    records.append({
                        'timestamp': base_timestamp,
                        'interface_name': interface_name,
                        'forecast_type': forecast_type,
                        'atc_mw': atc_value,
                        'ttc_mw': ttc_value,
                        'trm_mw': None,  # TRM not in short-term data
                        'direction': '',  # Direction not in short-term data
                    })
        else:
            # P-8A (long_term) has simple format
            for _, row in df.iterrows():
                records.append({
                    'timestamp': row[timestamp_col],
                    'interface_name': row.get('Interface Name', '') or row.get('Interface', ''),
                    'forecast_type': forecast_type,
                    'atc_mw': row.get('ATC (MW)', None) or row.get('ATC', None),
                    'ttc_mw': row.get('TTC (MW)', None) or row.get('TTC', None),
                    'trm_mw': row.get('TRM (MW)', None) or row.get('TRM', None),
                    'direction': row.get('Direction', '') or row.get('Flow Direction', ''),
                })
        
        return records
    
    def _transform_outages(self, df: pd.DataFrame, timestamp_col: str, outage_type: str, market_type: Optional[str]) -> List[Dict]:
        """Transform outages data."""
        records = []
        for _, row in df.iterrows():
            records.append({
                'timestamp': row[timestamp_col],
                'outage_type': outage_type,
                'market_type': market_type,
                'resource_name': row.get('Resource Name', '') or row.get('Name', '') or row.get('Unit', ''),
                'resource_type': row.get('Resource Type', '') or row.get('Type', ''),
                'mw_capacity': row.get('Capacity (MW)', None) or row.get('Capacity', None),
                'mw_outage': row.get('Outage (MW)', None) or row.get('Outage', None),
                'start_time': row.get('Start Time', None) or row.get('Start', None),
                'end_time': row.get('End Time', None) or row.get('End', None),
                'status': row.get('Status', ''),
            })
        return records
    
    def _transform_weather_forecast(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform weather forecast data.
        
        Actual CSV structure:
        - Forecast Date: Forecast date
        - Vintage Date: When the forecast was created
        - Vintage: 'Actual' or 'Forecast'
        - Station ID: Weather station identifier (e.g., 'ALB', 'ART', 'BGM')
        - Max Temp: Maximum temperature (F)
        - Min Temp: Minimum temperature (F)
        - Max Wet Bulb: Maximum wet bulb temperature (F)
        - Min Wet Bulb: Minimum wet bulb temperature (F)
        """
        records = []
        for _, row in df.iterrows():
            # Use Forecast Date as timestamp, Vintage Date as forecast_time
            timestamp = row[timestamp_col]
            forecast_time = row.get('Vintage Date', timestamp) if 'Vintage Date' in df.columns else timestamp
            
            # Get station ID (location)
            location = row.get('Station ID', '') or row.get('Location', '') or row.get('Station', '')
            
            # Calculate average temperature from max and min
            max_temp = row.get('Max Temp', None)
            min_temp = row.get('Min Temp', None)
            avg_temp = None
            if pd.notna(max_temp) and pd.notna(min_temp):
                try:
                    avg_temp = (float(max_temp) + float(min_temp)) / 2.0
                except (ValueError, TypeError):
                    pass
            elif pd.notna(max_temp):
                try:
                    avg_temp = float(max_temp)
                except (ValueError, TypeError):
                    pass
            elif pd.notna(min_temp):
                try:
                    avg_temp = float(min_temp)
                except (ValueError, TypeError):
                    pass
            
            # Calculate average wet bulb (proxy for humidity)
            max_wet_bulb = row.get('Max Wet Bulb', None)
            min_wet_bulb = row.get('Min Wet Bulb', None)
            avg_wet_bulb = None
            if pd.notna(max_wet_bulb) and pd.notna(min_wet_bulb):
                try:
                    avg_wet_bulb = (float(max_wet_bulb) + float(min_wet_bulb)) / 2.0
                except (ValueError, TypeError):
                    pass
            
            # Estimate humidity from wet bulb temperature (rough approximation)
            # Humidity is not directly available, but wet bulb temp correlates with humidity
            # For now, we'll leave humidity as None or use a placeholder calculation
            humidity_percent = None
            if avg_temp is not None and avg_wet_bulb is not None:
                # Rough approximation: higher wet bulb relative to temp = higher humidity
                # This is a simplified calculation
                try:
                    temp_diff = avg_temp - avg_wet_bulb
                    if temp_diff > 0:
                        # Rough estimate: smaller temp-wetbulb diff = higher humidity
                        humidity_percent = max(0, min(100, 100 - (temp_diff * 10)))
                except:
                    pass
            
            # Get vintage (Actual or Forecast)
            vintage = row.get('Vintage', '') if 'Vintage' in df.columns else None
            
            records.append({
                'timestamp': timestamp,
                'forecast_time': forecast_time,
                'location': location,
                'vintage': vintage,  # 'Actual' or 'Forecast'
                'temperature_f': avg_temp,
                'humidity_percent': humidity_percent,
                'wind_speed_mph': None,  # Not available in CSV
                'wind_direction': '',  # Not available in CSV
                'cloud_cover_percent': None,  # Not available in CSV
            })
        return records
    
    def _transform_fuel_mix(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Transform fuel mix data."""
        records = []
        
        # Check if it's long format (Fuel Category column) or wide format (columns for each fuel)
        if 'Fuel Category' in df.columns or 'fuel_category' in [c.lower() for c in df.columns]:
            # Long format: Time Stamp, Fuel Category, Gen MW
            fuel_category_col = next((c for c in df.columns if 'fuel' in c.lower() and 'category' in c.lower()), 'Fuel Category')
            gen_mw_col = next((c for c in df.columns if 'gen' in c.lower() and 'mw' in c.lower()), 'Gen MW')
            
            for _, row in df.iterrows():
                fuel_category = row.get(fuel_category_col, '')
                gen_mw = row.get(gen_mw_col)
                
                if pd.notna(gen_mw) and fuel_category:
                    # Normalize fuel type name
                    fuel_type = str(fuel_category).lower().replace(' ', '_').replace('-', '_')
                    records.append({
                        'timestamp': row[timestamp_col],
                        'fuel_type': fuel_type,
                        'generation_mw': float(gen_mw) if pd.notna(gen_mw) else 0.0,
                        'percentage': None,  # Calculate if total available
                    })
        else:
            # Wide format: columns for each fuel type
            fuel_columns = [col for col in df.columns 
                           if col != timestamp_col and col.lower() not in ['total', 'timestamp', 'time', 'time zone']]
            
            for _, row in df.iterrows():
                for fuel_col in fuel_columns:
                    fuel_value = row.get(fuel_col)
                    if pd.notna(fuel_value):
                        try:
                            gen_mw = float(fuel_value)
                            if gen_mw != 0:
                                records.append({
                                    'timestamp': row[timestamp_col],
                                    'fuel_type': fuel_col.lower().replace(' ', '_').replace('-', '_'),
                                    'generation_mw': gen_mw,
                                    'percentage': None,
                                })
                        except (ValueError, TypeError):
                            # Skip non-numeric values
                            continue
        
        return records
    
    def _transform_generic(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
        """Generic transformation for unknown formats."""
        return df.to_dict('records')

