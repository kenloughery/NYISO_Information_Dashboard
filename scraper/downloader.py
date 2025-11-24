"""
Robust downloader with retry logic, error handling, and archive fallback.
"""
import requests
import time
import zipfile
import io
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Custom exception for download errors."""
    pass


class NYISODownloader:
    """Downloads NYISO CSV files with retry and fallback logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 30,
        use_archive_fallback: bool = True
    ):
        """
        Initialize downloader.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Request timeout in seconds
            use_archive_fallback: Whether to try archive ZIP if direct CSV fails
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.use_archive_fallback = use_archive_fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NYISO Data Scraper)'
        })
    
    def download_csv(self, url: str) -> Optional[str]:
        """
        Download CSV content from URL.
        
        Args:
            url: URL to download
            
        Returns:
            CSV content as string, or None if download fails
            
        Raises:
            DownloadError: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Downloading {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Check if content is actually CSV
                content_type = response.headers.get('Content-Type', '').lower()
                if 'csv' in content_type or response.text.strip().startswith(','):
                    logger.info(f"Successfully downloaded {url}")
                    return response.text
                else:
                    logger.warning(f"Unexpected content type for {url}: {content_type}")
                    return response.text  # Try to parse anyway
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout downloading {url} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.debug(f"404 Not Found: {url}")
                    return None  # File doesn't exist, not a retryable error
                else:
                    logger.warning(f"HTTP {e.response.status_code} for {url} (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise DownloadError(f"HTTP {e.response.status_code}: {str(e)}")
                        
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for {url} (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise DownloadError(f"Request failed: {str(e)}")
        
        raise DownloadError(f"Failed to download {url} after {self.max_retries} attempts")
    
    def download_zip(self, url: str, filename_pattern: str) -> Optional[str]:
        """
        Download ZIP archive and extract CSV.
        
        Args:
            url: URL to ZIP archive
            filename_pattern: Expected filename pattern inside ZIP
            
        Returns:
            CSV content as string, or None if extraction fails
        """
        try:
            logger.debug(f"Downloading ZIP archive: {url}")
            response = self.session.get(url, timeout=self.timeout * 2)  # Longer timeout for ZIP
            response.raise_for_status()
            
            # Extract CSV from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                # Look for matching file
                for file_info in zip_file.namelist():
                    if filename_pattern in file_info or file_info.endswith('.csv'):
                        logger.info(f"Extracting {file_info} from ZIP")
                        csv_content = zip_file.read(file_info).decode('utf-8')
                        return csv_content
                
                # If no match, try first CSV file
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                if csv_files:
                    logger.info(f"Extracting {csv_files[0]} from ZIP")
                    csv_content = zip_file.read(csv_files[0]).decode('utf-8')
                    return csv_content
                
                logger.warning(f"No CSV file found in ZIP: {url}")
                return None
                
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {url}")
            return None
        except Exception as e:
            logger.error(f"Error extracting ZIP {url}: {str(e)}")
            return None
    
    def download_with_fallback(
        self,
        direct_url: str,
        archive_url: Optional[str] = None,
        filename_pattern: Optional[str] = None
    ) -> Optional[str]:
        """
        Download CSV with archive fallback.
        
        Args:
            direct_url: Direct CSV URL
            archive_url: Archive ZIP URL (optional)
            filename_pattern: Filename pattern for archive extraction
            
        Returns:
            CSV content as string, or None if both fail
        """
        # Try direct CSV first
        try:
            csv_content = self.download_csv(direct_url)
            if csv_content:
                return csv_content
        except DownloadError:
            logger.warning(f"Direct download failed: {direct_url}")
        
        # Fallback to archive if enabled
        if self.use_archive_fallback and archive_url:
            logger.info(f"Trying archive fallback: {archive_url}")
            csv_content = self.download_zip(archive_url, filename_pattern or '')
            if csv_content:
                return csv_content
        
        logger.error(f"Both direct and archive downloads failed for {direct_url}")
        return None
    
    def check_url_exists(self, url: str) -> bool:
        """
        Check if URL exists without downloading full content.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL exists and is accessible
        """
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

