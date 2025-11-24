"""
Open Meteo API downloader for weather data.
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
import pytz
import time

logger = logging.getLogger(__name__)


class OpenMeteoDownloadError(Exception):
    """Exception raised for Open Meteo download errors."""
    pass


class OpenMeteoDownloader:
    """
    Downloads weather data from Open Meteo API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Open Meteo downloader."""
        self.api_key = api_key or os.getenv('OPENMETEO_API_KEY')
        if not self.api_key:
            raise ValueError("Open Meteo API key not found. Set OPENMETEO_API_KEY environment variable.")
        
        self.base_url = 'https://customer-api.open-meteo.com/v1/forecast'
        self.timezone = 'America/New_York'  # NYISO uses Eastern Time
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def download_weather(
        self,
        lat: float,
        lon: float,
        location_name: str,
        start_date: datetime,
        end_date: datetime,
        retry_count: int = 0
    ) -> Dict:
        """
        Download weather data for a specific location and date range.
        
        Args:
            lat: Latitude
            lon: Longitude
            location_name: Name of the location (for logging)
            start_date: Start date for data
            end_date: End date for data
            retry_count: Current retry attempt
            
        Returns:
            Dict with hourly data from Open Meteo API
            
        Raises:
            OpenMeteoDownloadError: If download fails
        """
        # Format dates for API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Build API URL
        # Parameters: temperature_2m, relativehumidity_2m, direct_normal_irradiance, wind_speed_10m
        url = (
            f'{self.base_url}?'
            f'latitude={lat}&longitude={lon}'
            f'&hourly=temperature_2m,relativehumidity_2m,direct_normal_irradiance,wind_speed_10m'
            f'&apikey={self.api_key}'
            f'&timezone={self.timezone}'
            f'&start_date={start_str}&end_date={end_str}'
            f'&models=best_match'
        )
        
        try:
            logger.debug(f"Downloading weather for {location_name} ({lat}, {lon}) from {start_str} to {end_str}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if 'hourly' not in data:
                    raise OpenMeteoDownloadError(f"Invalid API response structure for {location_name}")
                
                logger.debug(f"Successfully downloaded weather data for {location_name}")
                return data
                
            elif response.status_code == 429:
                # Rate limit - wait and retry
                if retry_count < self.max_retries:
                    wait_time = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f"Rate limited for {location_name}. Waiting {wait_time}s before retry {retry_count + 1}/{self.max_retries}")
                    time.sleep(wait_time)
                    return self.download_weather(lat, lon, location_name, start_date, end_date, retry_count + 1)
                else:
                    raise OpenMeteoDownloadError(f"Rate limit exceeded for {location_name} after {self.max_retries} retries")
                    
            else:
                error_msg = f"API error for {location_name}: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                raise OpenMeteoDownloadError(error_msg)
                
        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"Request error for {location_name}: {str(e)}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self.download_weather(lat, lon, location_name, start_date, end_date, retry_count + 1)
            else:
                raise OpenMeteoDownloadError(f"Failed to download weather for {location_name} after {self.max_retries} retries: {str(e)}")
    
    def download_current_weather(
        self,
        lat: float,
        lon: float,
        location_name: str
    ) -> Dict:
        """
        Download current weather data (current hour + 24 hour forecast).
        
        Args:
            lat: Latitude
            lon: Longitude
            location_name: Name of the location
            
        Returns:
            Dict with hourly data from Open Meteo API
        """
        # Get data for current hour through next 24 hours
        # Start from current hour (rounded down)
        start_date = datetime.now().replace(minute=0, second=0, microsecond=0)
        # End 24 hours from now
        end_date = start_date + timedelta(hours=24)
        
        return self.download_weather(lat, lon, location_name, start_date, end_date)

