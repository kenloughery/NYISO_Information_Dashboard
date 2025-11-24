"""
Generate NYISO zone boundaries GeoJSON from US Census county data.
Uses official Census TIGER/Line shapefiles and maps counties to NYISO zones.
"""

import geopandas as gpd
import requests
import zipfile
import io
import json
import os
from pathlib import Path

# Zone code to NYISO database name mapping
# Census mapping uses single letters (A, B, C, etc.) but database uses full names
# Based on NYISO Gold Book and zone definitions
ZONE_CODE_TO_NAME = {
    'A': 'WEST',      # Western NY (Zone A)
    'B': 'GENESE',    # Genese (Zone B)
    'C': 'CENTRL',    # Central (Zone C)
    'D': 'NORTH',     # North (Zone D) - St. Lawrence and northern counties
    'E': 'MHK VL',    # Mohawk Valley (Zone E)
    'F': 'NORTH',     # North (Zone F) - northern counties
    'G': 'HUD VL',    # Hudson Valley (Zone G)
    'H': 'MILLWD',    # Millwood (Zone H - Westchester northern, merged with I at county level)
    'I': 'DUNWOD',    # Dunwoodie (Zone I - Westchester southern)
    'J': 'N.Y.C.',    # New York City (Zone J)
    'K': 'LONGIL',    # Long Island (Zone K)
    'CAPITL': 'CAPITL',  # Capital - Albany, Schenectady, Rensselaer, Saratoga area
}

def generate_nyiso_geojson():
    """Generate NYISO zones from Census county data."""
    print("=" * 60)
    print("NYISO Zone Boundaries Generator (Census-Based)")
    print("=" * 60)
    print()
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    static_dir = project_root / "static"
    static_dir.mkdir(exist_ok=True)
    temp_dir = script_dir / "temp_census_shp"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        print("1. Downloading US Counties (Census TIGER/Line 2022)...")
        # Official US Census Bureau Shapefile URL (Stable)
        url = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_county_20m.zip"
        
        print(f"   Fetching from: {url}")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall(temp_dir)
        
        print("   ✓ Download complete")
        
        # Load and filter for NY State (FIPS 36)
        print("2. Loading and filtering for NY State...")
        shp_file = temp_dir / "cb_2022_us_county_20m.shp"
        gdf = gpd.read_file(str(shp_file))
        ny_gdf = gdf[gdf['STATEFP'] == '36'].copy()
        print(f"   ✓ Found {len(ny_gdf)} NY counties")
        
        print("3. Mapping Counties to NYISO Zones...")
        # Official Mapping (Source: NYISO Gold Book and zone definitions)
        # Note: 'Westchester' is split into Zones H & I in reality, but defined here as Zone I 
        # for visualization purposes as county-level data cannot distinguish the substation split.
        # Zone D = NORTH (St. Lawrence and northern counties)
        # Zone I = DUNWOD (Westchester County southern portion)
        # CAPITL = Capital region (Albany, Schenectady, Rensselaer, Saratoga)
        county_to_zone = {
            '001': 'CAPITL',  # Albany -> CAPITL (Capital region)
            '003': 'C',       # Allegany -> C (CENTRL) - between WEST and CENTRL
            '005': 'J',       # Bronx -> J (N.Y.C.)
            '007': 'C',       # Broome -> C (CENTRL)
            '009': 'A',       # Cattaraugus -> A (WEST)
            '011': 'C',       # Cayuga -> C (CENTRL)
            '013': 'A',       # Chautauqua -> A (WEST)
            '015': 'C',       # Chemung -> C (CENTRL)
            '017': 'C',       # Chenango -> C (CENTRL)
            '019': 'F',       # Clinton -> F (NORTH) - northern border county
            '021': 'CAPITL',  # Columbia -> CAPITL (Capital region) - extends CAPITL north
            '023': 'C',       # Cortland -> C (CENTRL)
            '025': 'E',       # Delaware -> E (MHK VL) - between HUD VL and MHK VL
            '027': 'G',       # Dutchess -> G (HUD VL) - Hudson Valley region
            '029': 'A',       # Erie -> A (WEST)
            '031': 'F',       # Essex -> F (NORTH) - Adirondacks, northern region
            '033': 'F',       # Franklin -> F (NORTH) - northern border county
            '035': 'E',       # Fulton -> E (MHK VL) - Mohawk Valley
            '037': 'B',       # Genesee -> B (GENESE)
            '039': 'CAPITL',  # Greene -> CAPITL (Capital region) - extends CAPITL north
            '041': 'E',       # Hamilton -> E (MHK VL) - Adirondacks, but part of Mohawk Valley zone
            '043': 'E',       # Herkimer -> E (MHK VL) - core Mohawk Valley
            '045': 'E',       # Jefferson -> E (MHK VL) - northeast of MHK VL, extends zone northeast
            '047': 'J',       # Kings -> J (N.Y.C.)
            '049': 'E',       # Lewis -> E (MHK VL) - northeast of MHK VL, extends zone northeast
            '051': 'B',       # Livingston -> B (GENESE)
            '053': 'E',       # Madison -> E (MHK VL) - near Oneida, part of Mohawk Valley
            '055': 'B',       # Monroe -> B (GENESE)
            '057': 'E',       # Montgomery -> E (MHK VL)
            '059': 'K',       # Nassau -> K (LONGIL)
            '061': 'J',       # New York -> J (N.Y.C.)
            '063': 'A',       # Niagara -> A (WEST)
            '065': 'E',       # Oneida -> E (MHK VL) - core Mohawk Valley county
            '067': 'C',       # Onondaga -> C (CENTRL)
            '069': 'B',       # Ontario -> B (GENESE)
            '071': 'G',       # Orange -> G (HUD VL)
            '073': 'B',       # Orleans -> B (GENESE)
            '075': 'C',       # Oswego -> C (CENTRL)
            '077': 'E',       # Otsego -> E (MHK VL) - between HUD VL and MHK VL, part of Mohawk Valley
            '079': 'G',       # Putnam -> G (HUD VL)
            '081': 'J',       # Queens -> J (N.Y.C.)
            '083': 'CAPITL',  # Rensselaer -> CAPITL (Capital region)
            '085': 'J',       # Richmond -> J (N.Y.C.)
            '087': 'G',       # Rockland -> G (HUD VL)
            '089': 'E',       # St. Lawrence -> E (MHK VL) - furthest northwest area, contains Black Lake
            '091': 'CAPITL',  # Saratoga -> CAPITL (Capital region)
            '093': 'CAPITL',  # Schenectady -> CAPITL (Capital region)
            '095': 'E',       # Schoharie -> E (MHK VL) - Mohawk Valley area, between CAPITL and MHK VL
            '097': 'C',       # Schuyler -> C (CENTRL)
            '099': 'C',       # Seneca -> C (CENTRL)
            '101': 'C',       # Steuben -> C (CENTRL) - between WEST and CENTRL
            '103': 'K',       # Suffolk -> K (LONGIL)
            '105': 'G',       # Sullivan -> G (HUD VL) - Hudson Valley region, south of HUD VL
            '107': 'C',       # Tioga -> C (CENTRL)
            '109': 'C',       # Tompkins -> C (CENTRL)
            '111': 'G',       # Ulster -> G (HUD VL) - Hudson Valley region, connects HUD VL to MHK VL area
            '113': 'CAPITL',  # Warren -> CAPITL (Capital region) - extends CAPITL north
            '115': 'CAPITL',  # Washington -> CAPITL (Capital region) - extends CAPITL north
            '117': 'B',       # Wayne -> B (GENESE)
            '119': 'I',       # Westchester -> I (DUNWOD) - southern portion
            '121': 'B',       # Wyoming -> B (GENESE)
            '123': 'B'        # Yates -> B (GENESE)
        }
        
        ny_gdf['Zone'] = ny_gdf['COUNTYFP'].map(county_to_zone)
        
        # Fill any unmapped counties (safety check)
        unmapped = ny_gdf[ny_gdf['Zone'].isnull()]
        if len(unmapped) > 0:
            print(f"   ⚠ Warning: {len(unmapped)} counties were not mapped:")
            for idx, row in unmapped.iterrows():
                print(f"      County FIPS {row['COUNTYFP']}: {row.get('NAME', 'Unknown')}")
            # Assign unmapped counties to a default zone (or skip them)
            ny_gdf = ny_gdf[ny_gdf['Zone'].notna()].copy()
        
        print(f"   ✓ Mapped {len(ny_gdf)} counties to zones")
        
        print("4. Dissolving boundaries by zone...")
        # Merge counties into single Zone polygons
        # Note: Zones H (MILLWD) and I (DUNWOD) both map to Westchester County (FIPS 119),
        # so they'll be merged into a single polygon. This is a limitation of county-level data.
        # Also note: Zone D and Zone F both map to NORTH, so they'll be merged.
        zones_gdf = ny_gdf.dissolve(by='Zone').reset_index()
        print(f"   ✓ Created {len(zones_gdf)} zone polygons")
        print(f"   Zone codes: {sorted(zones_gdf['Zone'].unique().tolist())}")
        
        # Verify CAPITL was created
        if 'CAPITL' in zones_gdf['Zone'].values:
            print(f"   ✓ CAPITL zone created successfully")
        else:
            print(f"   ⚠ Warning: CAPITL zone not found after dissolve")
        
        # Handle CAPITL - it's typically part of the Capital region (Albany area)
        # Some counties in Zone F (North) are actually in the Capital region
        # For now, we'll note that CAPITL is represented within Zone F
        # If needed, we can split Zone F into F (North) and CAPITL (Capital) later
        
        # Project to WGS84 (Lat/Lon) for Leaflet if not already
        if zones_gdf.crs != 'EPSG:4326':
            print("5. Projecting to WGS84 (EPSG:4326)...")
            zones_gdf = zones_gdf.to_crs(epsg=4326)
        else:
            print("5. Already in WGS84, skipping projection")
        
        # Simplify geometry to reduce file size for web (optional but recommended)
        print("6. Simplifying geometry...")
        zones_gdf['geometry'] = zones_gdf.geometry.simplify(tolerance=0.01, preserve_topology=True)
        print("   ✓ Geometry simplified")
        
        print("7. Converting to GeoJSON format...")
        # Convert to GeoJSON and map zone codes to database names
        # Use __geo_interface__ to get GeoJSON-compatible geometry
        features = []
        created_zones = set()
        
        for idx, row in zones_gdf.iterrows():
            zone_code = row['Zone']
            zone_name = ZONE_CODE_TO_NAME.get(zone_code, zone_code)
            
            # Get geometry as GeoJSON using __geo_interface__
            geom = row.geometry
            
            # Validate geometry before converting
            if geom.is_empty:
                print(f"   ⚠ Warning: Zone {zone_name} ({zone_code}) has empty geometry, skipping")
                continue
            
            if not geom.is_valid:
                print(f"   ⚠ Warning: Zone {zone_name} ({zone_code}) has invalid geometry, attempting to fix...")
                geom = geom.buffer(0)  # Fix invalid geometries
            
            if geom.is_empty:
                print(f"   ⚠ Warning: Zone {zone_name} ({zone_code}) still empty after fix, skipping")
                continue
            
            # Check if geometry has sufficient points
            if hasattr(geom, 'exterior'):
                # Polygon
                coords_count = len(geom.exterior.coords) if hasattr(geom.exterior, 'coords') else 0
            elif hasattr(geom, 'geoms'):
                # MultiPolygon - check each polygon
                coords_count = 0
                for g in geom.geoms:
                    if hasattr(g, 'exterior') and hasattr(g.exterior, 'coords'):
                        coords_count += len(g.exterior.coords)
            else:
                coords_count = 0
            
            if coords_count < 3:
                print(f"   ⚠ Warning: Zone {zone_name} ({zone_code}) has only {coords_count} coordinate points")
                print(f"      This may be due to dissolve issues or missing county data")
                print(f"      Attempting to use buffer to fix...")
                # Try buffering to fix invalid geometries
                geom = geom.buffer(0.0001).buffer(-0.0001)
                if geom.is_empty:
                    print(f"   ⚠ Zone {zone_name} ({zone_code}) still invalid after buffer, skipping")
                    continue
            
            geom_dict = geom.__geo_interface__
            
            feature = {
                "type": "Feature",
                "properties": {
                    "Zone": zone_code,
                    "zone_name": zone_name,
                    "name": zone_name,
                },
                "geometry": geom_dict
            }
            features.append(feature)
            created_zones.add(zone_name)
        
        # Check for missing zones
        # Note: 
        # - MILLWD (Zone H) is merged with DUNWOD (Zone I) because both are in Westchester County
        #   and county-level data cannot distinguish the substation-level split
        # - Zone D and Zone F both map to NORTH (they are merged in the county mapping)
        all_required_zones = {'CAPITL', 'CENTRL', 'DUNWOD', 'GENESE', 'HUD VL', 'LONGIL', 
                              'MILLWD', 'N.Y.C.', 'NORTH', 'WEST', 'MHK VL'}
        missing_zones = all_required_zones - created_zones
        
        if missing_zones:
            print(f"   ⚠ Note: Some zones not in Census mapping: {missing_zones}")
            if 'MILLWD' in missing_zones:
                print(f"      - MILLWD is merged with DUNWOD (both in Westchester County)")
            print(f"   These limitations are due to county-level data granularity")
        
        # Verify DUNWOD appears only once (should be in Westchester area)
        dunwod_features = [f for f in features if f['properties']['zone_name'] == 'DUNWOD']
        if len(dunwod_features) > 1:
            print(f"   ⚠ Warning: DUNWOD appears {len(dunwod_features)} times (should be 1)")
        elif len(dunwod_features) == 1:
            print(f"   ✓ DUNWOD appears once (correct)")
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        output_file = static_dir / "nyiso_zones.geojson"
        print(f"8. Saving to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        file_size = output_file.stat().st_size
        print(f"   ✓ Successfully saved GeoJSON")
        print(f"   - Zones: {len(features)}")
        print(f"   - File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        print(f"   - Output: {output_file}")
        print()
        print("=" * 60)
        print("✓ Generation complete!")
        print("=" * 60)
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error downloading Census data: {e}")
        raise
    except Exception as e:
        print(f"✗ Error: {e}")
        raise
    finally:
        # Clean up temporary files
        if temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(temp_dir)
                print(f"\n✓ Cleaned up temporary files")
            except:
                pass

if __name__ == "__main__":
    generate_nyiso_geojson()

