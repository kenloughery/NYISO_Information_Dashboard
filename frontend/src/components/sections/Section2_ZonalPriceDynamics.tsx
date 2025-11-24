/**
 * Section 2: Zonal Price Dynamics
 * Components:
 * 1. NYISO Zonal Pricing Heat Map
 * 2. Zone Price Ranking Table
 * 3. Top Intra-Zonal Spread
 */

import { useMemo, useState, useEffect } from 'react';
import { useRealTimeLBMP } from '@/hooks/useRealTimeData';
import { useZoneSpreads, useZoneBoundaries, useRTDASpreads, useDayAheadLBMP } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { MapContainer, TileLayer, GeoJSON, useMap, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { formatLabel } from '@/utils/format';
import type { GeoJsonObject } from 'geojson';
import { ArrowUpward, ArrowDownward, Remove } from '@mui/icons-material';

// Fix for default marker icon in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Component to fit map bounds to GeoJSON
function FitBounds({ geojson }: { geojson: GeoJsonObject | null }) {
  const map = useMap();
  
  useEffect(() => {
    if (geojson && geojson.type === 'FeatureCollection') {
      const geoJsonLayer = L.geoJSON(geojson as any);
      const bounds = geoJsonLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20] });
      }
    }
  }, [geojson, map]);
  
  return null;
}

// Approximate zone center coordinates (fallback)
const ZONE_COORDINATES: { [key: string]: [number, number] } = {
  'CAPITL': [42.65, -73.75], // Albany area
  'CENTRL': [43.15, -76.15], // Syracuse area
  'DUNWOD': [41.70, -73.92], // Poughkeepsie area
  'GENESE': [43.00, -78.00], // Rochester area
  'HUD VL': [41.50, -74.00], // Hudson Valley
  'LONGIL': [40.80, -73.20], // Long Island
  'MILLWD': [41.30, -73.95], // Millwood area
  'N.Y.C.': [40.71, -74.01], // New York City
  'NORTH': [44.70, -73.45], // Plattsburgh area
  'WEST': [42.90, -78.85], // Buffalo area
  'MHK VL': [42.25, -73.80], // Mohawk Valley
};

export const Section2_ZonalPriceDynamics = () => {
  const [sortField, setSortField] = useState<'zone' | 'price' | 'daPrice' | 'congestion' | 'spread'>('price');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  
  const { data: lbmpData, isLoading: lbmpLoading, error: lbmpError } = useRealTimeLBMP();
  const { data: daLbmpData } = useDayAheadLBMP();
  const { data: zoneSpreadsData, isLoading: spreadsLoading } = useZoneSpreads({ limit: 100 });
  const { data: rtdaSpreadsData, isLoading: rtdaSpreadsLoading } = useRTDASpreads({ limit: 100 });
  const { data: zoneBoundaries, isLoading: boundariesLoading, error: boundariesError } = useZoneBoundaries();
  
  // Debug: Log zone boundaries when loaded
  useEffect(() => {
    if (zoneBoundaries && zoneBoundaries.features) {
      console.log('[Zone Boundaries] Loaded:', zoneBoundaries.features.length, 'zones');
      zoneBoundaries.features.forEach((feat: any, idx: number) => {
        const coords = feat.geometry?.coordinates?.[0];
        if (coords) {
          console.log(`[Zone ${idx + 1}] ${feat.properties?.zone_name}: ${coords.length} points`);
        }
      });
    }
  }, [zoneBoundaries]);

  // Get latest prices by zone and calculate price changes
  const zonePrices = useMemo(() => {
    if (!lbmpData || lbmpData.length === 0) return {};
    
    const latestTimestamp = lbmpData[0]?.timestamp;
    const latest = lbmpData.filter(d => d.timestamp === latestTimestamp);
    
    // Get previous timestamp (5 minutes ago typically)
    const timestamps = [...new Set(lbmpData.map(d => d.timestamp))].sort().reverse();
    const previousTimestamp = timestamps[1] || null;
    const previous = previousTimestamp ? lbmpData.filter(d => d.timestamp === previousTimestamp) : [];
    
    // Create a map of zone_name -> price data for quick lookup
    const priceMap: { [key: string]: { price: number; congestion: number; losses: number; priceChange?: number; priceChangePercent?: number } } = {};
    
    latest.forEach(d => {
      const prevData = previous.find(p => p.zone_name === d.zone_name);
      const priceChange = prevData ? d.lbmp - prevData.lbmp : undefined;
      const priceChangePercent = prevData && prevData.lbmp > 0 ? ((d.lbmp - prevData.lbmp) / prevData.lbmp) * 100 : undefined;
      
      priceMap[d.zone_name] = {
        price: d.lbmp,
        congestion: d.marginal_cost_congestion || 0,
        losses: d.marginal_cost_losses || 0,
        priceChange,
        priceChangePercent,
      };
    });
    
    return priceMap;
  }, [lbmpData]);

  // Get latest DA prices by zone
  const daZonePrices = useMemo(() => {
    if (!daLbmpData || daLbmpData.length === 0) return {};
    
    const latestTimestamp = daLbmpData[0]?.timestamp;
    const latest = daLbmpData.filter(d => d.timestamp === latestTimestamp);
    
    const priceMap: { [key: string]: number } = {};
    latest.forEach(d => {
      priceMap[d.zone_name] = d.lbmp;
    });
    
    return priceMap;
  }, [daLbmpData]);

  // Convert priceMap to array for table display
  const zonePricesArray = useMemo(() => {
    return Object.entries(zonePrices).map(([zone, data]) => ({
      zone,
      price: data.price,
      daPrice: daZonePrices[zone] || null,
      congestion: data.congestion,
      losses: data.losses,
      priceChange: data.priceChange,
      priceChangePercent: data.priceChangePercent,
    }));
  }, [zonePrices, daZonePrices]);

  // Get top intra-zonal spreads
  const topSpreads = useMemo(() => {
    if (!zoneSpreadsData || zoneSpreadsData.length === 0) return [];
    
    const latest = zoneSpreadsData[0];
    return [{
      maxZone: latest.max_zone,
      minZone: latest.min_zone,
      maxPrice: latest.max_price,
      minPrice: latest.min_price,
      spread: latest.spread,
    }];
  }, [zoneSpreadsData]);

  // Get top DA-RT spread
  const topDARTSpread = useMemo(() => {
    if (!rtdaSpreadsData || rtdaSpreadsData.length === 0) return null;
    
    // Find the spread with the largest absolute value
    const topSpread = rtdaSpreadsData.reduce((max, current) => {
      return Math.abs(current.spread) > Math.abs(max.spread) ? current : max;
    }, rtdaSpreadsData[0]);
    
    return {
      zone: topSpread.zone_name,
      rtPrice: topSpread.rt_lbmp,
      daPrice: topSpread.da_lbmp,
      spread: topSpread.spread,
      spreadPercent: topSpread.spread_percent,
    };
  }, [rtdaSpreadsData]);

  // Sort zone prices
  const sortedZonePrices = useMemo(() => {
    const sorted = [...zonePricesArray];
    sorted.sort((a, b) => {
      let aVal: number, bVal: number;
      switch (sortField) {
        case 'zone':
          return sortDirection === 'asc' 
            ? a.zone.localeCompare(b.zone)
            : b.zone.localeCompare(a.zone);
        case 'price':
          aVal = a.price;
          bVal = b.price;
          break;
        case 'daPrice':
          aVal = a.daPrice ?? 0;
          bVal = b.daPrice ?? 0;
          // Handle null values for sorting
          if (a.daPrice === null && b.daPrice === null) return 0;
          if (a.daPrice === null) return sortDirection === 'asc' ? 1 : -1;
          if (b.daPrice === null) return sortDirection === 'asc' ? -1 : 1;
          break;
        case 'congestion':
          aVal = a.congestion;
          bVal = b.congestion;
          break;
        case 'spread':
          aVal = a.price - Math.min(...zonePricesArray.map(z => z.price));
          bVal = b.price - Math.min(...zonePricesArray.map(z => z.price));
          break;
        default:
          return 0;
      }
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });
    return sorted;
  }, [zonePricesArray, sortField, sortDirection]);

  // Get price range for color coding
  const priceRange = useMemo(() => {
    if (zonePricesArray.length === 0) return { min: 0, max: 100 };
    const prices = zonePricesArray.map(z => z.price);
    return {
      min: Math.min(...prices),
      max: Math.max(...prices),
    };
  }, [zonePricesArray]);

  // Color function for heat map (choropleth) - using gradual color scale with 9 steps
  const getPriceColor = (price: number) => {
    const range = priceRange.max - priceRange.min;
    if (range === 0) return '#3b82f6'; // chart-primary
    
    const ratio = (price - priceRange.min) / range;
    
    // 9-step color scale for better granularity (prevents 5% differences from showing different colors)
    // Colors transition from green (low) -> yellow-green -> yellow -> orange -> red (high)
    if (ratio < 0.11) return '#10b981';      // Green (lowest)
    if (ratio < 0.22) return '#34d399';      // Emerald
    if (ratio < 0.33) return '#84cc16';      // Lime
    if (ratio < 0.44) return '#eab308';       // Yellow
    if (ratio < 0.55) return '#f59e0b';      // Amber
    if (ratio < 0.66) return '#f97316';     // Orange
    if (ratio < 0.77) return '#fb923c';      // Orange-red
    if (ratio < 0.88) return '#f87171';      // Light red
    return '#ef4444';                        // Red (highest)
  };

  // Style function for GeoJSON features
  const getZoneStyle = (feature: any) => {
    const zoneName = feature.properties?.zone_name || feature.properties?.Zone || feature.properties?.zone;
    const zoneData = zonePrices[zoneName];
    const price = zoneData?.price || 0;
    
    return {
      fillColor: getPriceColor(price),
      fillOpacity: 0.6,
      color: '#fff',
      weight: 2,
      opacity: 1,
    };
  };

  // Use GeoJSON directly - it's already in correct [lon, lat] format
  // No transformation needed as the file is generated correctly
  const transformedGeoJSON = useMemo(() => {
    if (!zoneBoundaries || !zoneBoundaries.features) {
      console.log('[GeoJSON] No zone boundaries data available');
      return zoneBoundaries;
    }
    
    // Verify we have detailed polygons (not simple rectangles)
    console.log('[GeoJSON] Loaded', zoneBoundaries.features.length, 'zones');
    zoneBoundaries.features.forEach((feat: any) => {
      const zoneName = feat.properties?.zone_name;
      const geomType = feat.geometry?.type;
      const coords = feat.geometry?.coordinates;
      
      if (geomType === 'Polygon') {
        const ring = coords[0];
        const pointCount = ring.length;
        console.log(`[GeoJSON] ${zoneName}: ${geomType}, ${pointCount} points`);
        if (pointCount < 10) {
          console.warn(`[GeoJSON] ⚠ ${zoneName} has only ${pointCount} points - might be simplified`);
        }
      } else if (geomType === 'MultiPolygon') {
        const totalPoints = coords.reduce((sum: number, poly: any[][]) => sum + poly[0].length, 0);
        const polyCount = coords.length;
        console.log(`[GeoJSON] ${zoneName}: ${geomType}, ${polyCount} polygons, ${totalPoints} total points`);
      } else {
        console.warn(`[GeoJSON] ⚠ ${zoneName}: Unexpected geometry type ${geomType}`);
      }
    });
    
    // Return the data as-is - coordinates are already in [lon, lat] format
    return zoneBoundaries;
  }, [zoneBoundaries]);

  // Handle feature click/popup and hover tooltip
  const onEachFeature = (feature: any, layer: L.Layer) => {
    const zoneName = feature.properties?.zone_name || feature.properties?.Zone || feature.properties?.zone;
    const zoneData = zonePrices[zoneName];
    
    // Store zone name in layer for later access in event handlers
    (layer as any)._zoneName = zoneName;
    
    // Create popup content
    if (zoneData) {
      const popupContent = `
        <div style="font-family: system-ui, -apple-system, sans-serif; color: #0f172a;">
          <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #1e293b;">
            ${formatLabel(zoneName)}
          </div>
          <div style="font-size: 13px; margin-bottom: 4px;">
            <span style="color: #0f172a;">Price:</span> 
            <span style="font-weight: 600; color: #1e293b;">$${zoneData.price.toFixed(2)}/MWh</span>
          </div>
          <div style="font-size: 13px;">
            <span style="color: #0f172a;">Congestion:</span> 
            <span style="font-weight: 600; color: ${zoneData.congestion > 0 ? '#fbbf24' : '#1e293b'};">$${zoneData.congestion.toFixed(2)}</span>
          </div>
        </div>
      `;
      layer.bindPopup(popupContent, {
        className: 'custom-popup',
      });
    } else {
      const popupContent = `
        <div style="font-family: system-ui, -apple-system, sans-serif; color: #0f172a;">
          <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #1e293b;">
            ${formatLabel(zoneName)}
          </div>
          <div style="font-size: 13px; color: #0f172a;">
            No price data available
          </div>
        </div>
      `;
      layer.bindPopup(popupContent, {
        className: 'custom-popup',
      });
    }
    
    // Add hover tooltip
    const tooltipContent = zoneData 
      ? `${formatLabel(zoneName)}: $${zoneData.price.toFixed(2)}/MWh`
      : formatLabel(zoneName);
    
    layer.bindTooltip(tooltipContent, {
      permanent: false,
      direction: 'center',
      className: 'custom-tooltip',
    });
    
    // Add hover effects
    layer.on({
      mouseover: (e: L.LeafletMouseEvent) => {
        const layer = e.target as L.Path;
        layer.setStyle({
          weight: 3,
          fillOpacity: 0.8,
        });
      },
      mouseout: (e: L.LeafletMouseEvent) => {
        const layer = e.target as L.Path;
        // Get zone name from stored property (set in onEachFeature)
        const storedZoneName = (layer as any)._zoneName || zoneName;
        const storedZoneData = zonePrices[storedZoneName];
        const storedPrice = storedZoneData?.price || 0;
        layer.setStyle({
          weight: 2,
          fillOpacity: 0.6,
          fillColor: getPriceColor(storedPrice),
        });
      },
    });
  };

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  if (lbmpLoading) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <LoadingSkeleton type="chart" height="400px" />
      </div>
    );
  }

  if (lbmpError) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <ErrorMessage 
          message={lbmpError instanceof Error ? lbmpError.message : "Failed to load zonal price data"}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Zonal Price Dynamics</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 1. Geographic Heat Map */}
          <div>
                  <h3 className="text-base sm:text-lg font-medium mb-3">NYISO Zonal Pricing Heat Map</h3>
            <div className="h-96 rounded-lg overflow-hidden border border-slate-700">
              {boundariesLoading ? (
                <LoadingSkeleton type="chart" height="100%" className="h-full" />
              ) : boundariesError ? (
                <div className="h-full flex items-center justify-center p-4">
                  <ErrorMessage 
                    message={boundariesError instanceof Error ? boundariesError.message : "Error loading zone boundaries"}
                    onRetry={() => window.location.reload()}
                    className="m-0"
                  />
                </div>
              ) : zoneBoundaries && !boundariesError ? (
                // Primary: Show GeoJSON polygons (choropleth map)
                <MapContainer
                  center={[42.65, -74.5] as [number, number]}
                  zoom={7}
                  style={{ height: '100%', width: '100%' }}
                  className="z-0"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <FitBounds geojson={transformedGeoJSON as GeoJsonObject} />
                  <GeoJSON
                    key="nyiso-zones" // Force re-render if data changes
                    data={transformedGeoJSON as GeoJsonObject}
                    style={getZoneStyle as any}
                    onEachFeature={onEachFeature as any}
                  />
                </MapContainer>
              ) : (
                // Fallback: Show point markers if GeoJSON unavailable
                <MapContainer
                  center={[42.65, -74.5] as [number, number]}
                  zoom={7}
                  style={{ height: '100%', width: '100%' }}
                  className="z-0"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {zonePricesArray.length > 0 ? (
                    zonePricesArray.map((zone) => (
                      <CircleMarker
                        key={zone.zone}
                        center={(ZONE_COORDINATES[zone.zone] || [42.65, -73.75]) as [number, number]}
                        radius={15}
                        pathOptions={{
                          fillColor: getPriceColor(zone.price),
                          fillOpacity: 0.7,
                          color: '#fff',
                          weight: 2,
                        }}
                      >
                        <Popup>
                          <div className="text-sm" style={{ color: '#0f172a' }}>
                            <div className="font-semibold" style={{ color: '#1e293b' }}>{formatLabel(zone.zone)}</div>
                            <div style={{ color: '#0f172a' }}>Price: <span style={{ fontWeight: 600, color: '#1e293b' }}>${zone.price.toFixed(2)}/MWh</span></div>
                            <div style={{ color: '#0f172a' }}>Congestion: <span style={{ fontWeight: 600, color: '#1e293b' }}>${zone.congestion.toFixed(2)}</span></div>
                          </div>
                        </Popup>
                      </CircleMarker>
                    ))
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <div className="text-sm text-slate-400">No zone data available</div>
                    </div>
                  )}
                </MapContainer>
              )}
            </div>
                  <p className="text-xs text-slate-400 mt-2 italic">
                    Note: Zone boundaries are approximations based on county-level data so do not reflect exact NYISO zone definitions.
                  </p>

            {/* 3. Top Intra-Zonal Spread and Top DA-RT Spread - Moved here to be directly below the map */}
            <div className="mt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Top Intra-Zonal Spread */}
                <div>
                  <h3 className="text-base sm:text-lg font-medium mb-3">Top Intra-Zonal Spread</h3>
                  {spreadsLoading ? (
                    <LoadingSkeleton type="table" lines={5} />
                  ) : topSpreads.length > 0 ? (
                    <div className="grid grid-cols-1 gap-6">
                      {topSpreads.map((spread, idx) => (
                        <div key={idx} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                          <div className="text-sm text-slate-400 mb-2">Current Spread</div>
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <div className="text-xs text-slate-400">{formatLabel(spread.maxZone)}</div>
                              <div className="text-lg font-bold text-red-400">${spread.maxPrice.toFixed(2)}</div>
                            </div>
                            <div className="text-2xl font-bold text-yellow-400">
                              ${spread.spread.toFixed(2)}
                            </div>
                            <div>
                              <div className="text-xs text-slate-400">{formatLabel(spread.minZone)}</div>
                              <div className="text-lg font-bold text-green-400">${spread.minPrice.toFixed(2)}</div>
                            </div>
                          </div>
                          <div className="text-xs text-slate-500 mt-2">
                            Spread: {spread.minPrice > 0 ? ((spread.spread / spread.minPrice) * 100).toFixed(1) : '0.0'}%
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState 
                      title="No Spreads Available"
                      message="Intra-zonal price spreads are not available at this time."
                      className="py-8"
                    />
                  )}
                </div>

                {/* Top DA-RT Spread */}
                <div>
                  <h3 className="text-base sm:text-lg font-medium mb-3">Top Day Ahead - Real Time Spread</h3>
                  {rtdaSpreadsLoading ? (
                    <LoadingSkeleton type="table" lines={5} />
                  ) : topDARTSpread ? (
                    <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                      <div className="text-sm text-slate-400 mb-2">Zone: <span className="font-semibold text-slate-200">{formatLabel(topDARTSpread.zone)}</span></div>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <div className="text-xs text-slate-400">Day Ahead Price</div>
                          <div className="text-2xl font-bold text-blue-400">${topDARTSpread.daPrice.toFixed(2)}</div>
                        </div>
                        <div className={`text-2xl font-bold ${topDARTSpread.spread > 0 ? 'text-yellow-400' : 'text-blue-400'}`}>
                          ${Math.abs(topDARTSpread.spread).toFixed(2)}
                        </div>
                        <div>
                          <div className="text-xs text-slate-400">Real Time Price</div>
                          <div className="text-lg font-bold text-red-400">${topDARTSpread.rtPrice.toFixed(2)}</div>
                        </div>
                      </div>
                      <div className="text-xs text-slate-500 mt-2 text-right">
                        Spread: {topDARTSpread.spreadPercent.toFixed(1)}%
                      </div>
                    </div>
                  ) : (
                    <EmptyState 
                      title="No Spread Available"
                      message="Day Ahead - Real Time price spreads are not available at this time."
                      className="py-8"
                    />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 2. Zone Price Ranking Table */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Zone Price Rankings</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th
                      className="text-left p-2 cursor-pointer hover:bg-slate-700/50 transition-colors select-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onClick={() => handleSort('zone')}
                      onKeyDown={(e: React.KeyboardEvent) => e.key === 'Enter' && handleSort('zone')}
                      tabIndex={0}
                      role="button"
                      aria-label={`Sort by zone ${sortField === 'zone' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : ''}`}
                    >
                      <div className="flex items-center gap-1">
                        Zone
                        {sortField === 'zone' && (
                          <span className="text-blue-400">
                            {sortDirection === 'asc' ? <ArrowUpward className="w-3 h-3" /> : <ArrowDownward className="w-3 h-3" />}
                          </span>
                        )}
                      </div>
                    </th>
                    <th
                      className="text-right p-2 cursor-pointer hover:bg-slate-700/50 transition-colors select-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onClick={() => handleSort('price')}
                      onKeyDown={(e: React.KeyboardEvent) => e.key === 'Enter' && handleSort('price')}
                      tabIndex={0}
                      role="button"
                      aria-label={`Sort by price ${sortField === 'price' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : ''}`}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Real Time Price
                        {sortField === 'price' && (
                          <span className="text-blue-400">
                            {sortDirection === 'asc' ? <ArrowUpward className="w-3 h-3" /> : <ArrowDownward className="w-3 h-3" />}
                          </span>
                        )}
                      </div>
                    </th>
                    <th
                      className="text-right p-2 cursor-pointer hover:bg-slate-700/50 transition-colors select-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onClick={() => handleSort('daPrice')}
                      onKeyDown={(e: React.KeyboardEvent) => e.key === 'Enter' && handleSort('daPrice')}
                      tabIndex={0}
                      role="button"
                      aria-label={`Sort by day ahead price ${sortField === 'daPrice' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : ''}`}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Day Ahead Price
                        {sortField === 'daPrice' && (
                          <span className="text-blue-400">
                            {sortDirection === 'asc' ? <ArrowUpward className="w-3 h-3" /> : <ArrowDownward className="w-3 h-3" />}
                          </span>
                        )}
                      </div>
                    </th>
                    <th
                      className="text-right p-2 cursor-pointer hover:bg-slate-700/50 transition-colors select-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onClick={() => handleSort('congestion')}
                      onKeyDown={(e: React.KeyboardEvent) => e.key === 'Enter' && handleSort('congestion')}
                      tabIndex={0}
                      role="button"
                      aria-label={`Sort by congestion ${sortField === 'congestion' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : ''}`}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Congestion
                        {sortField === 'congestion' && (
                          <span className="text-blue-400">
                            {sortDirection === 'asc' ? <ArrowUpward className="w-3 h-3" /> : <ArrowDownward className="w-3 h-3" />}
                          </span>
                        )}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedZonePrices.map((zone) => (
                    <tr key={zone.zone} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                      <td className="p-2 font-medium">{formatLabel(zone.zone)}</td>
                      <td className="p-2 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span>${zone.price.toFixed(2)}</span>
                          {zone.priceChange !== undefined && zone.priceChangePercent !== undefined && (
                            <span className={`text-xs font-semibold flex items-center gap-0.5 ${
                              zone.priceChange > 0 
                                ? 'text-status-danger' 
                                : zone.priceChange < 0 
                                ? 'text-status-success' 
                                : 'text-slate-400'
                            }`}>
                              {zone.priceChange > 0 ? (
                                <ArrowUpward className="w-3 h-3" />
                              ) : zone.priceChange < 0 ? (
                                <ArrowDownward className="w-3 h-3" />
                              ) : (
                                <Remove className="w-3 h-3" />
                              )}
                              {Math.abs(zone.priceChangePercent).toFixed(1)}%
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-2 text-right">
                        {zone.daPrice !== null ? (
                          <span className="text-slate-200">${zone.daPrice.toFixed(2)}</span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                      <td className="p-2 text-right">
                        <span className={zone.congestion > 0 ? 'text-status-warning' : 'text-slate-400'}>
                          ${zone.congestion.toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

