"""
Script to generate NYISO zone boundaries from zone definitions.
Generates GeoJSON manually from available zone information.
"""

import json
import os
import sys
from pathlib import Path

# Import the generation function
SCRIPT_DIR = Path(__file__).parent
GENERATE_SCRIPT = SCRIPT_DIR / "generate_nyiso_zones.py"

# Output directory
PROJECT_ROOT = SCRIPT_DIR.parent
STATIC_DIR = PROJECT_ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = STATIC_DIR / "nyiso_zones.geojson"

# Zone name mapping: NYISO database names -> GeoJSON zone properties
# This mapping may need adjustment based on actual GeoJSON structure
ZONE_NAME_MAPPING = {
    'CAPITL': ['A', 'Capital', 'CAPITL'],
    'CENTRL': ['C', 'Central', 'CENTRL'],
    'DUNWOD': ['I', 'Dunwoodie', 'DUNWOD', 'DUNWOODIE'],
    'GENESE': ['B', 'Genese', 'GENESE', 'GENESEE'],
    'HUD VL': ['G', 'Hudson Valley', 'HUD VL', 'HUD_VL', 'HUDSON_VALLEY'],
    'LONGIL': ['K', 'Long Island', 'LONGIL', 'LONG_ISLAND'],
    'MILLWD': ['H', 'Millwood', 'MILLWD', 'MILLWOOD'],
    'N.Y.C.': ['J', 'NYC', 'New York City', 'N.Y.C.', 'NYC'],
    'NORTH': ['F', 'North', 'NORTH'],
    'WEST': ['A', 'West', 'WEST'],
    'MHK VL': ['E', 'Mohawk Valley', 'MHK VL', 'MHK_VL', 'MOHAWK_VALLEY'],
}


def process_geojson(geojson_data):
    """Process GeoJSON to ensure proper format and add zone name mappings."""
    print("Processing GeoJSON data...")
    
    # Ensure it's a FeatureCollection
    if geojson_data.get('type') != 'FeatureCollection':
        raise ValueError("Expected FeatureCollection type")
    
    features = geojson_data.get('features', [])
    print(f"Found {len(features)} zone features")
    
    # Process each feature to normalize zone names
    processed_features = []
    for feature in features:
        props = feature.get('properties', {})
        
        # Try to identify zone name from various possible property keys
        zone_name = None
        for key in ['Zone', 'ZONE', 'zone', 'name', 'NAME', 'Name']:
            if key in props:
                zone_name = props[key]
                break
        
        # If no zone name found, try to infer from other properties
        if not zone_name:
            # Check all properties for debugging
            print(f"Warning: No zone name found in feature. Properties: {list(props.keys())}")
            continue
        
        # Normalize zone name - try to map to NYISO database names
        normalized_zone = None
        for db_zone, possible_names in ZONE_NAME_MAPPING.items():
            if zone_name in possible_names or str(zone_name).upper() in [n.upper() for n in possible_names]:
                normalized_zone = db_zone
                break
        
        # If no mapping found, use original zone name
        if not normalized_zone:
            normalized_zone = str(zone_name).upper()
            print(f"Note: Zone '{zone_name}' not in mapping, using as-is")
        
        # Update feature properties with normalized zone name
        feature['properties']['zone_name'] = normalized_zone
        feature['properties']['original_zone'] = zone_name
        
        processed_features.append(feature)
    
    # Update GeoJSON with processed features
    geojson_data['features'] = processed_features
    
    print(f"✓ Processed {len(processed_features)} zone features")
    return geojson_data

def save_geojson(geojson_data, output_file):
    """Save processed GeoJSON to file."""
    print(f"Saving GeoJSON to {output_file}...")
    
    try:
        with open(output_file, 'w') as f:
            json.dump(geojson_data, f, indent=2)
        
        file_size = os.path.getsize(output_file)
        print(f"✓ Successfully saved GeoJSON ({file_size:,} bytes)")
        return True
    except Exception as e:
        print(f"✗ Error saving GeoJSON: {e}")
        raise

def generate_from_census():
    """Generate GeoJSON from Census county data (preferred method)."""
    print("Generating GeoJSON from Census county data...")
    
    # Try to use the Census-based generator
    CENSUS_SCRIPT = SCRIPT_DIR / "generate_nyiso_zones_from_census.py"
    
    if CENSUS_SCRIPT.exists():
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(CENSUS_SCRIPT)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"  ⚠ Census generation failed: {result.stderr}")
                return None
            
            # Read the generated file
            if OUTPUT_FILE.exists():
                with open(OUTPUT_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"  ⚠ Census generation error: {e}")
            return None
    
    return None

def generate_from_definitions():
    """Generate GeoJSON from zone definitions (fallback method)."""
    print("Generating GeoJSON from zone definitions (fallback)...")
    
    # Import and run the generation script
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        from generate_nyiso_zones import generate_geojson
        
        geojson_data = generate_geojson()
        return geojson_data
    except ImportError:
        # If import fails, run as subprocess
        import subprocess
        result = subprocess.run(
            [sys.executable, str(GENERATE_SCRIPT)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"Failed to generate GeoJSON: {result.stderr}")
        
        # Read the generated file
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, 'r') as f:
                return json.load(f)
        else:
            raise Exception("Generation script ran but file not found")

def main():
    """Main execution function."""
    print("=" * 60)
    print("NYISO Zone Boundaries Generator")
    print("=" * 60)
    print()
    
    try:
        # Try Census-based generation first (more accurate)
        print("Method 1: Generating from Census county data...")
        geojson_data = generate_from_census()
        
        if geojson_data:
            print("✓ Successfully generated GeoJSON from Census data")
            # Census data already has proper zone names, but process to ensure consistency
            processed_data = process_geojson(geojson_data)
            save_geojson(processed_data, OUTPUT_FILE)
            
            print()
            print("=" * 60)
            print("✓ Successfully completed!")
            print(f"Output file: {OUTPUT_FILE}")
            print("=" * 60)
            return
        
        # Fallback to simple definitions
        print()
        print("Method 2: Generating from zone definitions (fallback)...")
        geojson_data = generate_from_definitions()
        print("✓ Successfully generated GeoJSON from zone definitions")
        
        # Process to ensure zone name mapping
        processed_data = process_geojson(geojson_data)
        save_geojson(processed_data, OUTPUT_FILE)
        
        print()
        print("=" * 60)
        print("✓ Successfully completed!")
        print(f"Output file: {OUTPUT_FILE}")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Error: {e}")
        print("=" * 60)
        raise

if __name__ == "__main__":
    main()

