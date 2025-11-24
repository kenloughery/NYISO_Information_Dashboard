"""
Weather location configuration for NYISO zones.
Maps each NYISO price zone to multiple geographic locations for weather data collection.
"""

WEATHER_LOCATIONS = {
    # --- WESTERN NY ---
    'WEST': [
        {'name': 'Buffalo', 'lat': 42.8864, 'lon': -78.8784},      # Major Load Center
        {'name': 'Rochester', 'lat': 43.1566, 'lon': -77.6088},    # Major Load Center
        {'name': 'Jamestown', 'lat': 42.0970, 'lon': -79.2353},    # Southern Tier
    ],
    'GENESE': [
        {'name': 'Rochester Airport', 'lat': 43.1189, 'lon': -77.6724}, # Overlap w/ West boundary
        {'name': 'Hornell', 'lat': 42.3276, 'lon': -77.6611},           # Southern part of zone
        {'name': 'Geneseo', 'lat': 42.7959, 'lon': -77.8172},           # Central part of zone
    ],
    
    # --- CENTRAL NY ---
    'CENTRL': [
        {'name': 'Syracuse', 'lat': 43.0481, 'lon': -76.1474},     # Major Load Center
        {'name': 'Oswego', 'lat': 43.4553, 'lon': -76.5105},       # Lake Effect/Northern
        {'name': 'Cortland', 'lat': 42.6012, 'lon': -76.1816},     # Southern
    ],
    'MHK VL': [
        {'name': 'Utica', 'lat': 43.1009, 'lon': -75.2327},        # Major Hub
        {'name': 'Rome', 'lat': 43.2128, 'lon': -75.4557},         # Western Edge
        {'name': 'Amsterdam', 'lat': 42.9377, 'lon': -74.1903},    # Eastern Edge
    ],

    # --- NORTHERN NY ---
    'NORTH': [
        {'name': 'Watertown', 'lat': 43.9748, 'lon': -75.9108},    # Western/Lake Ontario
        {'name': 'Plattsburgh', 'lat': 44.6995, 'lon': -73.4529},  # Eastern/Lake Champlain
        {'name': 'Massena', 'lat': 44.9281, 'lon': -74.8919},      # Northern Border (Hydro)
    ],

    # --- CAPITAL REGION ---
    'CAPITL': [
        {'name': 'Albany', 'lat': 42.6526, 'lon': -73.7562},       # Major Load Center
        {'name': 'Schenectady', 'lat': 42.8142, 'lon': -73.9396}, # Industrial Hub
        {'name': 'Glens Falls', 'lat': 43.3095, 'lon': -73.6440},  # Northern Reach
    ],

    # --- HUDSON VALLEY ---
    'HUD VL': [
        {'name': 'Poughkeepsie', 'lat': 41.7004, 'lon': -73.9210}, # Mid-Valley
        {'name': 'Kingston', 'lat': 41.9270, 'lon': -74.0000},     # Northern Valley
        {'name': 'Middletown', 'lat': 41.4459, 'lon': -74.4229},   # Western/Orange County
    ],
    'MILLWD': [
        {'name': 'Yorktown Heights', 'lat': 41.2631, 'lon': -73.7739}, # Substation Hub
        {'name': 'Mount Kisco', 'lat': 41.2043, 'lon': -73.7271},      # Load Center
    ],
    'DUNWOD': [
        {'name': 'Yonkers', 'lat': 40.9312, 'lon': -73.8987},      # Major Load Center
        {'name': 'White Plains', 'lat': 41.0340, 'lon': -73.7629}, # Commercial Hub
    ],

    # --- NYC & LONG ISLAND ---
    'N.Y.C.': [
        {'name': 'Central Park', 'lat': 40.7829, 'lon': -73.9654}, # Manhattan
        {'name': 'JFK Airport', 'lat': 40.6413, 'lon': -73.7781},  # Queens/Coastal
        {'name': 'LaGuardia', 'lat': 40.7769, 'lon': -73.8740},    # Northern Queens
    ],
    'LONGIL': [
        {'name': 'Islip', 'lat': 40.7282, 'lon': -73.2141},        # Central LI (MacArthur)
        {'name': 'Montauk', 'lat': 41.0359, 'lon': -71.9545},      # Eastern Tip
        {'name': 'Garden City', 'lat': 40.7268, 'lon': -73.6343},  # Nassau County
    ],

    # --- EXTERNAL INTERFACES (Proxies) ---
    # Note: These are proxy locations for the external interface ties
    'H Q': [
        {'name': 'Montreal (Proxy)', 'lat': 45.5017, 'lon': -73.5673}, # HQ Import Source
    ],
    'O H': [
        {'name': 'Toronto (Proxy)', 'lat': 43.6532, 'lon': -79.3832},  # OH Import Source
    ],
    'PJM': [
        {'name': 'Allentown PA (Proxy)', 'lat': 40.6023, 'lon': -75.4714}, # PJM East Hub Proxy
    ],
    'NPX': [
        {'name': 'Bridgeport CT (Proxy)', 'lat': 41.1792, 'lon': -73.1894}, # ISO-NE Cross Sound Proxy
    ]
}


def get_locations_for_zone(zone_code: str):
    """Returns the list of weather monitoring locations for a given NYISO zone."""
    return WEATHER_LOCATIONS.get(zone_code, [])


def get_all_locations():
    """Returns all weather locations across all zones."""
    all_locations = []
    for zone_code, locations in WEATHER_LOCATIONS.items():
        for loc in locations:
            all_locations.append({
                'zone_code': zone_code,
                'name': loc['name'],
                'lat': loc['lat'],
                'lon': loc['lon']
            })
    return all_locations


def get_zone_for_location(location_name: str):
    """Returns the zone code for a given location name."""
    for zone_code, locations in WEATHER_LOCATIONS.items():
        for loc in locations:
            if loc['name'] == location_name:
                return zone_code
    return None

