"""
Generate NYISO zone boundaries GeoJSON manually from available information.
Creates simplified polygons based on approximate zone centers and known geographic regions.
"""

import json
from pathlib import Path

# Zone center coordinates and approximate boundaries
# Based on NYISO zone definitions and approximate geographic coverage
ZONE_DATA = {
    'CAPITL': {
        'center': [42.65, -73.75],
        'name': 'Capital',
        'description': 'Albany area - Capital Region',
        # Approximate polygon: Albany, Schenectady, Troy area
        'bounds': [
            [42.4, -74.0],  # SW
            [42.9, -74.0],  # SE
            [42.9, -73.5],  # NE
            [42.4, -73.5],  # NW
            [42.4, -74.0],  # Close polygon
        ]
    },
    'CENTRL': {
        'center': [43.15, -76.15],
        'name': 'Central',
        'description': 'Syracuse area - Central NY',
        'bounds': [
            [42.9, -76.5],
            [43.4, -76.5],
            [43.4, -75.8],
            [42.9, -75.8],
            [42.9, -76.5],
        ]
    },
    'DUNWOD': {
        'center': [41.70, -73.92],
        'name': 'Dunwoodie',
        'description': 'Westchester County (southern portion)',
        'bounds': [
            [41.5, -74.1],
            [41.9, -74.1],
            [41.9, -73.7],
            [41.5, -73.7],
            [41.5, -74.1],
        ]
    },
    'GENESE': {
        'center': [43.00, -78.00],
        'name': 'Genese',
        'description': 'Rochester area - Western NY',
        'bounds': [
            [42.7, -78.3],
            [43.3, -78.3],
            [43.3, -77.7],
            [42.7, -77.7],
            [42.7, -78.3],
        ]
    },
    'HUD VL': {
        'center': [41.50, -74.00],
        'name': 'Hudson Valley',
        'description': 'Hudson Valley region',
        'bounds': [
            [41.2, -74.3],
            [41.8, -74.3],
            [41.8, -73.7],
            [41.2, -73.7],
            [41.2, -74.3],
        ]
    },
    'LONGIL': {
        'center': [40.80, -73.20],
        'name': 'Long Island',
        'description': 'Long Island - Nassau and Suffolk Counties',
        'bounds': [
            [40.6, -73.6],
            [41.0, -73.6],
            [41.0, -72.8],
            [40.6, -72.8],
            [40.6, -73.6],
        ]
    },
    'MILLWD': {
        'center': [41.30, -73.95],
        'name': 'Millwood',
        'description': 'Westchester County (northern portion)',
        'bounds': [
            [41.1, -74.2],
            [41.5, -74.2],
            [41.5, -73.7],
            [41.1, -73.7],
            [41.1, -74.2],
        ]
    },
    'N.Y.C.': {
        'center': [40.71, -74.01],
        'name': 'New York City',
        'description': 'New York City - 5 boroughs',
        'bounds': [
            [40.5, -74.3],
            [40.9, -74.3],
            [40.9, -73.7],
            [40.5, -73.7],
            [40.5, -74.3],
        ]
    },
    'NORTH': {
        'center': [44.70, -73.45],
        'name': 'North',
        'description': 'Plattsburgh area - Northern NY',
        'bounds': [
            [44.4, -73.8],
            [45.0, -73.8],
            [45.0, -73.1],
            [44.4, -73.1],
            [44.4, -73.8],
        ]
    },
    'WEST': {
        'center': [42.90, -78.85],
        'name': 'West',
        'description': 'Buffalo area - Western NY',
        'bounds': [
            [42.6, -79.2],
            [43.2, -79.2],
            [43.2, -78.5],
            [42.6, -78.5],
            [42.6, -79.2],
        ]
    },
    'MHK VL': {
        'center': [42.25, -73.80],
        'name': 'Mohawk Valley',
        'description': 'Mohawk Valley region',
        'bounds': [
            [42.0, -74.1],
            [42.5, -74.1],
            [42.5, -73.5],
            [42.0, -73.5],
            [42.0, -74.1],
        ]
    },
}

def create_polygon_feature(zone_code, zone_info):
    """Create a GeoJSON feature for a zone polygon.
    
    Note: GeoJSON uses [longitude, latitude] format, not [latitude, longitude].
    The bounds in ZONE_DATA are defined as [latitude, longitude], so we swap them.
    """
    # Convert bounds from [lat, lon] to [lon, lat] format for GeoJSON
    # Bounds are defined as [lat, lon] in ZONE_DATA
    bounds_lon_lat = []
    for coord in zone_info['bounds']:
        if len(coord) >= 2:
            # Swap: [lat, lon] -> [lon, lat]
            bounds_lon_lat.append([coord[1], coord[0]])
        else:
            bounds_lon_lat.append(coord)
    
    return {
        "type": "Feature",
        "properties": {
            "Zone": zone_code,
            "zone_name": zone_code,
            "name": zone_info['name'],
            "description": zone_info['description'],
            "center_lat": zone_info['center'][0],
            "center_lon": zone_info['center'][1],
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [bounds_lon_lat]
        }
    }

def generate_geojson():
    """Generate GeoJSON FeatureCollection from zone data."""
    features = []
    
    for zone_code, zone_info in ZONE_DATA.items():
        feature = create_polygon_feature(zone_code, zone_info)
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson

def main():
    """Main execution function."""
    print("=" * 60)
    print("NYISO Zone Boundaries Generator")
    print("=" * 60)
    print()
    print("Generating GeoJSON from zone definitions...")
    
    # Generate GeoJSON
    geojson_data = generate_geojson()
    
    # Determine output path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    static_dir = project_root / "static"
    static_dir.mkdir(exist_ok=True)
    
    output_file = static_dir / "nyiso_zones.geojson"
    
    # Save to file
    print(f"Saving GeoJSON to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(geojson_data, f, indent=2)
    
    file_size = output_file.stat().st_size
    print(f"✓ Successfully generated GeoJSON")
    print(f"  - Zones: {len(geojson_data['features'])}")
    print(f"  - File size: {file_size:,} bytes")
    print(f"  - Output: {output_file}")
    print()
    print("=" * 60)
    print("✓ Generation complete!")
    print()
    print("Note: These are simplified rectangular boundaries based on")
    print("approximate zone centers. For production use, consider:")
    print("  1. Obtaining official NYISO shapefiles")
    print("  2. Using more detailed county/census boundary data")
    print("  3. Refining polygons based on actual zone boundaries")
    print("=" * 60)

if __name__ == "__main__":
    main()

