"""
Open Meteo API response parser.
Transforms Open Meteo API responses into database-ready format.
"""
import logging
from datetime import datetime
from typing import Dict, List
import pytz

logger = logging.getLogger(__name__)


class OpenMeteoParser:
    """
    Parses Open Meteo API responses into database records.
    """
    
    def __init__(self):
        """Initialize parser."""
        self.eastern_tz = pytz.timezone('America/New_York')
    
    def parse_weather_response(
        self,
        api_response: Dict,
        location_name: str,
        zone_name: str,
        lat: float,
        lon: float,
        fetch_time: datetime
    ) -> List[Dict]:
        """
        Parse API response into list of database records.
        
        Each record represents one hour of data.
        
        Args:
            api_response: Open Meteo API response dict
            location_name: Name of the location
            zone_name: NYISO zone name
            lat: Latitude
            lon: Longitude
            fetch_time: When the data was fetched (used as forecast_time)
            
        Returns:
            List of dicts ready for database insertion
        """
        records = []
        
        if 'hourly' not in api_response:
            logger.warning(f"No hourly data in API response for {location_name}")
            return records
        
        hourly_data = api_response['hourly']
        
        # Extract time series
        times = hourly_data.get('time', [])
        temperatures = hourly_data.get('temperature_2m', [])
        humidities = hourly_data.get('relativehumidity_2m', [])
        irradiances = hourly_data.get('direct_normal_irradiance', [])
        wind_speeds = hourly_data.get('wind_speed_10m', [])
        
        if not times:
            logger.warning(f"No time data in API response for {location_name}")
            return records
        
        # Convert fetch_time to Eastern Time (naive)
        if fetch_time.tzinfo:
            fetch_time_et = fetch_time.astimezone(self.eastern_tz).replace(tzinfo=None)
        else:
            # Assume it's already in Eastern Time
            fetch_time_et = fetch_time
        
        # Process each hour
        for i, time_str in enumerate(times):
            try:
                # Parse timestamp (Open Meteo returns ISO format strings)
                # The API returns times in the requested timezone (Eastern Time)
                timestamp = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                
                # Convert to Eastern Time if needed
                if timestamp.tzinfo:
                    timestamp_et = timestamp.astimezone(self.eastern_tz).replace(tzinfo=None)
                else:
                    timestamp_et = timestamp
                
                # Get values for this hour
                temp_c = temperatures[i] if i < len(temperatures) else None
                humidity = humidities[i] if i < len(humidities) else None
                irradiance = irradiances[i] if i < len(irradiances) else None
                wind_speed_ms = wind_speeds[i] if i < len(wind_speeds) else None
                
                # Convert units
                temp_f = self._celsius_to_fahrenheit(temp_c) if temp_c is not None else None
                wind_speed_mph = self._ms_to_mph(wind_speed_ms) if wind_speed_ms is not None else None
                
                # Only create record if we have at least temperature data
                if temp_f is not None:
                    record = {
                        'timestamp': timestamp_et,  # Weather observation time
                        'forecast_time': fetch_time_et,  # When data was fetched
                        'location': location_name,
                        'zone_name': zone_name,
                        'vintage': 'Actual',  # Open Meteo provides actual/current data
                        'temperature_f': temp_f,
                        'humidity_percent': humidity,
                        'wind_speed_mph': wind_speed_mph,
                        'wind_direction': '',  # Not requested in API call
                        'cloud_cover_percent': None,  # Not requested in API call
                        'irradiance_w_m2': irradiance,
                        'data_source': 'OpenMeteo'
                    }
                    records.append(record)
                    
            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"Error parsing hour {i} for {location_name}: {str(e)}")
                continue
        
        logger.info(f"Parsed {len(records)} weather records for {location_name}")
        return records
    
    @staticmethod
    def _celsius_to_fahrenheit(celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        if celsius is None:
            return None
        return (celsius * 9/5) + 32
    
    @staticmethod
    def _ms_to_mph(meters_per_second: float) -> float:
        """Convert meters per second to miles per hour."""
        if meters_per_second is None:
            return None
        return meters_per_second * 2.237

