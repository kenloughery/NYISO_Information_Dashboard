"""
Test script to explore NYISO data structure before building full pipeline.
Downloads sample CSVs and analyzes their structure.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Any

# Sample URLs from URL_Instructions.txt
SAMPLE_URLS = [
    "http://mis.nyiso.com/public/csv/realtime/20251113realtime_zone.csv",
    "http://mis.nyiso.com/public/csv/damlbmp/20251113damlbmp_zone.csv",
    "http://mis.nyiso.com/public/csv/pal/20251113pal.csv",
    "http://mis.nyiso.com/public/csv/isolf/20251113isolf.csv",
    "http://mis.nyiso.com/public/csv/ExternalLimitsFlows/20251113ExternalLimitsFlows.csv",
    "http://mis.nyiso.com/public/csv/realtime/20251113int_lbmp_zone.csv",
    "http://mis.nyiso.com/public/csv/rt_ancillaryservices/20251113rt_ancillaryservices.csv",
    "http://mis.nyiso.com/public/csv/damlbmp/20251113damlbmp_ancillaryservices.csv",
]

def download_and_analyze(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Download CSV and analyze its structure."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {url}")
    print(f"{'='*80}")
    
    result = {
        "url": url,
        "success": False,
        "error": None,
        "rows": 0,
        "columns": [],
        "sample_data": None,
        "dtypes": {},
        "null_counts": {},
        "date_columns": [],
        "numeric_columns": []
    }
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Try to read CSV
        df = pd.read_csv(url)
        
        result["success"] = True
        result["rows"] = len(df)
        result["columns"] = list(df.columns)
        result["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
        result["null_counts"] = df.isnull().sum().to_dict()
        
        # Identify date columns
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'timestamp']):
                result["date_columns"].append(col)
        
        # Identify numeric columns
        result["numeric_columns"] = df.select_dtypes(include=['number']).columns.tolist()
        
        # Get sample data (first 3 rows)
        result["sample_data"] = df.head(3).to_dict('records')
        
        print(f"✓ Successfully downloaded")
        print(f"  Rows: {result['rows']}")
        print(f"  Columns: {len(result['columns'])}")
        print(f"  Column names: {result['columns']}")
        print(f"\n  Sample data (first row):")
        if result['sample_data']:
            for key, value in result['sample_data'][0].items():
                print(f"    {key}: {value}")
        
    except requests.exceptions.RequestException as e:
        result["error"] = f"HTTP Error: {str(e)}"
        print(f"✗ Failed to download: {result['error']}")
    except Exception as e:
        result["error"] = f"Parse Error: {str(e)}"
        print(f"✗ Failed to parse: {result['error']}")
    
    return result

def main():
    """Run exploration tests."""
    print("NYISO Data Structure Exploration")
    print("=" * 80)
    
    results = []
    for url in SAMPLE_URLS:
        result = download_and_analyze(url)
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    successful = sum(1 for r in results if r["success"])
    print(f"Successful downloads: {successful}/{len(SAMPLE_URLS)}")
    
    # Save results to JSON for analysis
    output_file = Path("data_exploration_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")
    
    # Print column analysis
    print("\nColumn Analysis:")
    all_columns = set()
    for result in results:
        if result["success"]:
            all_columns.update(result["columns"])
    
    print(f"Total unique columns across all datasets: {len(all_columns)}")
    print("\nCommon patterns:")
    print("  - Date/Time columns:", [c for c in all_columns if any(k in c.lower() for k in ['date', 'time'])])
    print("  - Zone columns:", [c for c in all_columns if 'zone' in c.lower()])
    print("  - Price columns:", [c for c in all_columns if 'price' in c.lower() or 'lbmp' in c.lower()])

if __name__ == "__main__":
    main()

