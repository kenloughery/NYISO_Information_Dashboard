/**
 * Weather Carousel Component
 * Displays current weather information from P-7A data in a continuously scrolling bar
 */

import { useEffect, useMemo, useRef } from 'react';
import { useCurrentWeather } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from './LoadingSkeleton';

export const WeatherCarousel = () => {
  const { data: weatherData, isLoading, error, dataUpdatedAt } = useCurrentWeather();
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Group weather data by location
  const groupedData = useMemo(() => {
    if (!weatherData || weatherData.length === 0) return [];
    
    // Group by location
    const grouped: { [key: string]: typeof weatherData } = {};
    weatherData.forEach((item) => {
      const location = item.location || 'Unknown';
      if (!grouped[location]) {
        grouped[location] = [];
      }
      grouped[location].push(item);
    });

    // Convert to array format
    return Object.entries(grouped).map(([location, items]) => ({
      location,
      data: items[0], // Take the first item for each location
    }));
  }, [weatherData]);

  // Get the latest update timestamp (NYISO operates in Eastern Time)
  // Note: Timestamps from API are naive (no timezone) but represent Eastern Time
  // JavaScript interprets naive ISO strings as local time, so we need to treat them as ET
  const lastUpdateDate = useMemo(() => {
    if (!weatherData || weatherData.length === 0) return null;
    const timestamp = weatherData[0]?.timestamp;
    if (!timestamp) return null;
    
    // Parse timestamp and treat as Eastern Time
    let dateStr = typeof timestamp === 'string' ? timestamp : timestamp.toISOString();
    
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
              className="flex-shrink-0 bg-slate-700/50 rounded-lg p-2 min-w-[200px]"
            >
              <div className="flex items-center gap-2 text-xs">
                {/* Station ID */}
                <div>
                  <div className="text-slate-400 mb-1">Station ID</div>
                  <div className="text-sm font-semibold text-slate-200">
                    {formatLocation(group.location)}
                  </div>
                </div>
                
                {/* Temperature */}
                {group.data.temperature !== null && group.data.temperature !== undefined && (
                  <div>
                    <div className="text-slate-400 mb-1">Temp</div>
                    <div className="text-sm font-semibold text-slate-200">
                      {group.data.temperature.toFixed(1)}°F
                    </div>
                  </div>
                )}
                
                {/* Humidity */}
                {group.data.humidity !== null && group.data.humidity !== undefined && (
                  <div>
                    <div className="text-slate-400 mb-1">Humidity</div>
                    <div className="text-sm font-semibold text-slate-200">
                      {group.data.humidity.toFixed(0)}%
                    </div>
                  </div>
                )}
                
                {/* Wind */}
                {group.data.wind_speed !== null && group.data.wind_speed !== undefined && (
                  <div>
                    <div className="text-slate-400 mb-1">Wind</div>
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
                    <div className="text-slate-400 mb-1">Clouds</div>
                    <div className="text-sm font-semibold text-slate-200">
                      {group.data.cloud_cover_percent.toFixed(0)}%
                    </div>
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

