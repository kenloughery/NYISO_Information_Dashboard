# Zonal Map Setup Notes

## GeoJSON Generation

The implementation generates GeoJSON manually from zone definitions. The system:

1. **Generation script**: Creates GeoJSON from zone definitions
2. **Local file**: Saves to `static/nyiso_zones.geojson`
3. **Graceful degradation**: Frontend falls back to point markers if GeoJSON unavailable

## Current Status

The implementation is complete and working. The code:
- Generates GeoJSON from zone definitions automatically
- Creates simplified rectangular polygons for each zone
- Falls back gracefully if GeoJSON is unavailable

## Zone Boundaries

The generated boundaries are simplified rectangular polygons based on approximate zone centers. For production use with accurate boundaries, consider:
- Obtaining official NYISO shapefiles
- Using detailed county/census boundary data
- Refining polygons based on actual utility territories

## Next Steps

1. **Test the map**: Verify zones render correctly in the frontend
2. **Refine boundaries**: If needed, adjust polygon coordinates for better accuracy
3. **Production**: Consider obtaining official shapefiles for production deployment

The frontend will work with the generated GeoJSON, with point markers as fallback.

