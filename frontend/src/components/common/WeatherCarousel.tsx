/**
 * Weather Carousel Component
 * Displays current weather information from NYISO and Open Meteo data in a continuously scrolling bar
 */

import { useEffect, useMemo, useRef } from 'react';
import { useCurrentWeather } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from './LoadingSkeleton';

export const WeatherCarousel = () => {
  const { data: weatherData, isLoading, error, dataUpdatedAt } = useCurrentWeather();
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Group weather data by location and data source
  // If same location has both NYISO and Open Meteo, prefer Open Meteo (more complete data)
  const groupedData = useMemo(() => {
    if (!weatherData || weatherData.length === 0) return [];
    
    // Group by location, preferring Open Meteo over NYISO when both exist
    const grouped: { [key: string]: typeof weatherData } = {};
    weatherData.forEach((item) => {
      const location = item.location || 'Unknown';
      if (!grouped[location]) {
        grouped[location] = [];
      }
      grouped[location].push(item);
    });

    // Convert to array format, preferring Open Meteo data when available
    return Object.entries(grouped).map(([location, items]) => {
      // Prefer Open Meteo if available, otherwise use first item
      const openMeteoItem = items.find(item => item.data_source === 'OpenMeteo');
      const selectedItem = openMeteoItem || items[0];
      
      return {
        location,
        data: selectedItem,
      };
    });
  }, [weatherData]);

  // Get the latest update timestamp (NYISO operates in Eastern Time)
  // Note: Timestamps from API are naive (no timezone) but represent Eastern Time
  // JavaScript interprets naive ISO strings as local time, so we need to treat them as ET
  // Use forecast_time (Vintage Date) which represents when the data was last updated
  // Fallback to timestamp (Forecast Date) if forecast_time is not available
  const lastUpdateDate = useMemo(() => {
    if (!weatherData || weatherData.length === 0) return null;
    // Use forecast_time (Vintage Date) for "Most Recent Data" - this is when data was last updated
    const timestamp = weatherData[0]?.forecast_time || weatherData[0]?.timestamp;
    if (!timestamp) return null;
    
    // Parse timestamp and treat as Eastern Time
    let dateStr: string = typeof timestamp === 'string' ? timestamp : String(timestamp);
    
    // Check if it already has timezone info (look for timezone pattern at the end: +HH:MM, -HH:MM, or Z)
    const hasTimezone = dateStr.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(dateStr);
    
    if (!hasTimezone) {
      // Append Eastern Time offset (EST = -05:00, EDT = -04:00)
      const month = parseInt(dateStr.substring(5, 7) || '1');
      const isDST = month >= 3 && month <= 11;
      const offset = isDST ? '-04:00' : '-05:00';
      dateStr = dateStr + offset;
    }
    
    const date = new Date(dateStr);
    
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZone: 'America/New_York',
      timeZoneName: 'short',
    });
  }, [weatherData]);

  // Reset scroll position when data updates
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollLeft = 0;
    }
  }, [dataUpdatedAt]);

  const formatLocation = (location?: string) => {
    if (!location) return 'Unknown';
    return location.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <LoadingSkeleton type="text" lines={1} className="h-12" />
      </div>
    );
  }

  if (error || !weatherData || weatherData.length === 0 || groupedData.length === 0) {
    return null;
  }

  // Duplicate the content for seamless infinite scroll
  const duplicatedData = [...groupedData, ...groupedData];

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-300">Current Weather Conditions</h3>
        {lastUpdateDate && (
          <div className="text-xs text-slate-400">
            Most Recent Data: {lastUpdateDate}
          </div>
        )}
      </div>

      {/* Scrolling container with infinite animation */}
      <div className="relative overflow-hidden weather-scroll-container">
        <div
          ref={scrollContainerRef}
          className="flex gap-4 weather-scroll-content"
          style={{
            width: 'max-content',
            animation: `weather-scroll ${Math.max(groupedData.length * 4, 30)}s linear infinite`,
          }}
        >
          {/* Duplicate content for seamless loop */}
          {duplicatedData.map((group, index) => (
            <div
              key={`${group.location}-${index}`}
              className="flex-shrink-0 bg-slate-700/50 rounded-lg p-2 min-w-[280px]"
            >
              <div className="flex flex-col gap-1.5">
                {/* Header: Location and Zone */}
                <div className="flex items-center justify-between mb-1">
                  <div className="text-sm font-semibold text-slate-200">
                    {formatLocation(group.location)}
                  </div>
                  {group.data.zone_name && (
                    <div className="text-xs px-1.5 py-0.5 bg-blue-600/30 text-blue-300 rounded">
                      {group.data.zone_name}
                    </div>
                  )}
                </div>
                
                {/* Weather Metrics Grid */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {/* Temperature */}
                  {group.data.temperature !== null && group.data.temperature !== undefined && (
                    <div>
                      <div className="text-slate-400 mb-0.5">Temp</div>
                      <div className="text-sm font-semibold text-slate-200">
                        {group.data.temperature.toFixed(1)}°F
                      </div>
                    </div>
                  )}
                  
                  {/* Humidity */}
                  {group.data.humidity !== null && group.data.humidity !== undefined && (
                    <div>
                      <div className="text-slate-400 mb-0.5">Humidity</div>
                      <div className="text-sm font-semibold text-slate-200">
                        {group.data.humidity.toFixed(0)}%
                      </div>
                    </div>
                  )}
                  
                  {/* Wind */}
                  {group.data.wind_speed !== null && group.data.wind_speed !== undefined && (
                    <div>
                      <div className="text-slate-400 mb-0.5">Wind</div>
                      <div className="text-sm font-semibold text-slate-200">
                        {group.data.wind_speed.toFixed(1)} mph
                        {group.data.wind_direction && (
                          <span className="text-slate-400 ml-1 text-[10px]">
                            {group.data.wind_direction}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Cloud Cover */}
                  {group.data.cloud_cover_percent !== null && group.data.cloud_cover_percent !== undefined && (
                    <div>
                      <div className="text-slate-400 mb-0.5">Clouds</div>
                      <div className="text-sm font-semibold text-slate-200">
                        {group.data.cloud_cover_percent.toFixed(0)}%
                      </div>
                    </div>
                  )}
                  
                  {/* Irradiance (Open Meteo only) */}
                  {group.data.irradiance_w_m2 !== null && group.data.irradiance_w_m2 !== undefined && (
                    <div>
                      <div className="text-slate-400 mb-0.5">Irradiance</div>
                      <div className="text-sm font-semibold text-slate-200">
                        {group.data.irradiance_w_m2.toFixed(0)} W/m²
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Data Source Badge */}
                {group.data.data_source && (
                  <div className="text-[10px] text-slate-500 mt-1">
                    Source: {group.data.data_source}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CSS for infinite scroll animation - pause on hover */}
      <style>{`
        .weather-scroll-container:hover .weather-scroll-content {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

