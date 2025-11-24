"""
Configuration parser for NYISO URL patterns.
Reads from URL_Instructions.txt and URL_Lookup.txt.
"""
import csv
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DataSourceConfig:
    """Configuration for a single data source."""
    data_type: str
    report_code: str
    dataset_name: str
    filename_pattern: str
    direct_csv_url_template: str
    archive_zip_url_template: str
    category: Optional[str] = None
    update_frequency: Optional[str] = None
    description: Optional[str] = None
    
    def build_url(self, date: datetime, use_archive: bool = False) -> str:
        """Build URL for a specific date."""
        date_str = date.strftime('%Y%m%d')
        month_str = date.strftime('%Y%m01')  # First day of month for archives
        
        if use_archive:
            url = self.archive_zip_url_template.replace('{YYYYMM01}', month_str)
        else:
            url = self.direct_csv_url_template.replace('{YYYYMMDD}', date_str)
        
        return url
    
    def get_filename_pattern(self, date: datetime) -> str:
        """Get expected filename pattern for a date."""
        date_str = date.strftime('%Y%m%d')
        return self.filename_pattern.replace('{YYYYMMDD}', date_str)


class URLConfigLoader:
    """Loads and manages data source configurations."""
    
    def __init__(self, instructions_file: str = None, lookup_file: str = None):
        """Initialize with file paths."""
        base_path = Path(__file__).parent.parent
        self.instructions_file = instructions_file or (base_path / 'URL_Instructions.txt')
        self.lookup_file = lookup_file or (base_path / 'URL_Lookup.txt')
        self.configs: Dict[str, DataSourceConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load configurations from both files."""
        # Load from URL_Instructions.txt (primary source with URL patterns)
        with open(self.instructions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                config = DataSourceConfig(
                    data_type=row['Data Type'],
                    report_code=row['Report Code'],
                    dataset_name=row['Dataset Name'],
                    filename_pattern=row['Filename Pattern'],
                    direct_csv_url_template=row['Direct CSV URL'],
                    archive_zip_url_template=row['Archive ZIP URL']
                )
                self.configs[config.report_code] = config
        
        # Enrich with metadata from URL_Lookup.txt
        with open(self.lookup_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                report_code = row['Report Code']
                if report_code in self.configs:
                    self.configs[report_code].category = row.get('Category', '')
                    self.configs[report_code].update_frequency = row.get('Update Frequency', '')
                    self.configs[report_code].description = row.get('Description', '')
    
    def get_config(self, report_code: str) -> Optional[DataSourceConfig]:
        """Get configuration for a report code."""
        return self.configs.get(report_code)
    
    def get_all_configs(self) -> List[DataSourceConfig]:
        """Get all configurations."""
        return list(self.configs.values())
    
    def get_configs_by_category(self, category: str) -> List[DataSourceConfig]:
        """Get configurations filtered by category."""
        return [c for c in self.configs.values() if c.category == category]
    
    def get_active_configs(self) -> List[DataSourceConfig]:
        """Get all active configurations."""
        return [c for c in self.configs.values()]

