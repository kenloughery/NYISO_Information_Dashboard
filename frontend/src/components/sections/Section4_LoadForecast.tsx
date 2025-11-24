/**
 * Section 4: Load & Forecast Analytics
 * Components:
 * 1. Actual vs Forecast Load Gauge
 * 2. Peak Load Warning Indicator
 * 3. Zonal Load Contribution
 */

import { useMemo } from 'react';
import { useRealTimeLoad } from '@/hooks/useRealTimeData';
import { useLoadForecast } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { ResponsiveChart } from '@/components/common/ResponsiveChart';
import { EnhancedCard } from '@/components/common/EnhancedCard';
import { CircularGauge } from '@/components/common/CircularGauge';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import type { LoadForecast } from '@/types/api';
import { formatLabel } from '@/utils/format';
import { CheckCircle, Warning } from '@mui/icons-material';

export const Section4_LoadForecast = () => {
  const { data: loadData } = useRealTimeLoad();
  const { data: forecastData, isLoading: forecastLoading, error: forecastError } = useLoadForecast();

  // Actual vs Forecast Gauge
  const loadComparison = useMemo(() => {
    if (!loadData || loadData.length === 0 || !forecastData || forecastData.length === 0) return null;
    
    // Get latest load data (aggregate across all zones)
    const latestLoadTimestamp = loadData[0]?.timestamp;
    const latestLoads = loadData.filter(d => d.timestamp === latestLoadTimestamp);
    const totalActualLoad = latestLoads.reduce((sum, d) => sum + d.load, 0);
    
    // Round real-time load timestamp to the hour (forecasts are hourly)
    const loadDate = new Date(latestLoadTimestamp);
    const roundedHour = new Date(loadDate);
    roundedHour.setMinutes(0);
    roundedHour.setSeconds(0);
    roundedHour.setMilliseconds(0);
    
    const targetHour = roundedHour.getTime();
    
    // Find forecast that matches the exact hour (forecasts are on the hour)
    // Also check the hour before in case we're early in the hour
    let matchingForecast: LoadForecast | null = null;
    let minDiff = Infinity;
    
    forecastData.forEach(f => {
      const forecastDate = new Date(f.timestamp);
      const forecastHour = new Date(forecastDate);
      forecastHour.setMinutes(0);
      forecastHour.setSeconds(0);
      forecastHour.setMilliseconds(0);
      const forecastHourTime = forecastHour.getTime();
      
      // Check if forecast is for the same hour or the hour before
      const diff1 = Math.abs(forecastHourTime - targetHour);
      const diff2 = Math.abs(forecastHourTime - (targetHour - 60 * 60 * 1000));
      
      const minDiffForThis = Math.min(diff1, diff2);
      
      // Prefer exact hour match, but accept hour before if within tolerance
      if (minDiffForThis < minDiff && minDiffForThis < 60 * 60 * 1000) {
        minDiff = minDiffForThis;
        matchingForecast = f;
      }
    });
    
    // If still no match, use the most recent forecast as fallback
    if (!matchingForecast && forecastData.length > 0) {
      matchingForecast = forecastData[0];
    }
    
    if (!matchingForecast) {
      return null;
    }
    
    // Aggregate forecast across all zones for the same timestamp
    const forecastTimestamp = matchingForecast.timestamp;
    const forecasts = forecastData.filter(f => f.timestamp === forecastTimestamp);
    const totalForecastLoad = forecasts.reduce((sum, f) => sum + f.forecast_load, 0);
    
    if (totalForecastLoad === 0) return null;
    
    const error = totalActualLoad - totalForecastLoad;
    const errorPercent = (error / totalForecastLoad) * 100;
    const accuracy = 100 - Math.abs(errorPercent);
    
    return {
      actual: totalActualLoad,
      forecast: totalForecastLoad,
      error,
      errorPercent,
      accuracy: Math.max(0, accuracy), // Ensure non-negative
    };
  }, [loadData, forecastData]);
  
  // Calculate forecast accuracy metrics (historical)
  const forecastAccuracy = useMemo(() => {
    if (!loadData || !forecastData || loadData.length === 0 || forecastData.length === 0) return null;
    
    // Get last 24 hours of data
    const now = new Date();
    const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const accuracyData: number[] = [];
    
    // Group forecasts by hour
    const forecastsByHour: { [key: string]: LoadForecast[] } = {};
    forecastData.forEach(f => {
      const forecastDate = new Date(f.timestamp);
      const hourKey = new Date(forecastDate.getFullYear(), forecastDate.getMonth(), forecastDate.getDate(), forecastDate.getHours()).toISOString();
      if (!forecastsByHour[hourKey]) {
        forecastsByHour[hourKey] = [];
      }
      forecastsByHour[hourKey].push(f);
    });
    
    // For each hour with both actual and forecast, calculate accuracy
    Object.entries(forecastsByHour).forEach(([hourKey, forecasts]) => {
      const hourDate = new Date(hourKey);
      if (hourDate < twentyFourHoursAgo) return;
      
      // Find actual load for this hour (within 5 minutes of the hour)
      const hourStart = new Date(hourDate);
      hourStart.setMinutes(0, 0, 0);
      const hourEnd = new Date(hourStart);
      hourEnd.setMinutes(59, 59, 999);
      
      const actualLoads = loadData.filter(d => {
        const loadDate = new Date(d.timestamp);
        return loadDate >= hourStart && loadDate <= hourEnd;
      });
      
      if (actualLoads.length === 0) return;
      
      // Average actual load for the hour
      const avgActual = actualLoads.reduce((sum, d) => sum + d.load, 0) / actualLoads.length;
      
      // Sum forecast for this hour
      const totalForecast = forecasts.reduce((sum, f) => sum + f.forecast_load, 0);
      
      if (totalForecast > 0) {
        const error = Math.abs(avgActual - totalForecast);
        const errorPercent = (error / totalForecast) * 100;
        const accuracy = 100 - errorPercent;
        accuracyData.push(Math.max(0, accuracy));
      }
    });
    
    if (accuracyData.length === 0) return null;
    
    const avgAccuracy = accuracyData.reduce((a, b) => a + b, 0) / accuracyData.length;
    const minAccuracy = Math.min(...accuracyData);
    const maxAccuracy = Math.max(...accuracyData);
    
    return {
      average: avgAccuracy,
      min: minAccuracy,
      max: maxAccuracy,
      sampleSize: accuracyData.length,
    };
  }, [loadData, forecastData]);

  // Peak Load Warning
  const peakLoadInfo = useMemo(() => {
    if (!loadData || loadData.length === 0) return null;
    
    // Get the latest timestamp
    const latestTimestamp = loadData[0]?.timestamp;
    
    // Sum all zones for the latest timestamp to get total system load
    const currentLoad = loadData
      .filter(d => d.timestamp === latestTimestamp)
      .reduce((sum, d) => sum + (d.load || 0), 0);
    
    // Calculate max load across all timestamps (sum all zones per timestamp)
    const loadsByTimestamp: { [key: string]: number } = {};
    loadData.forEach(d => {
      if (!loadsByTimestamp[d.timestamp]) {
        loadsByTimestamp[d.timestamp] = 0;
      }
      loadsByTimestamp[d.timestamp] += d.load || 0;
    });
    const maxLoad = Math.max(...Object.values(loadsByTimestamp));
    
    const peakLoad = 35000; // Approximate NYISO peak capacity (~35 GW)
    
    return {
      current: currentLoad,
      max: maxLoad,
      peak: peakLoad,
      percentOfPeak: (currentLoad / peakLoad) * 100,
    };
  }, [loadData]);

  // Zonal Load Contribution
  const zonalLoadData = useMemo(() => {
    if (!loadData) return [];
    
    const latestTimestamp = loadData[0]?.timestamp;
    const latest = loadData.filter(d => d.timestamp === latestTimestamp);
    
    return latest.map(d => ({
      zone: formatLabel(d.zone_name),
      load: d.load,
    })).sort((a, b) => b.load - a.load);
  }, [loadData]);


  return (
    <div className="space-y-6">
      <EnhancedCard>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Load & Forecast Analytics</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 1. Actual vs Forecast Load Gauge - Enhanced with Circular Gauge */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Actual vs Forecast Load</h3>
            {forecastLoading ? (
              <LoadingSkeleton type="card" lines={4} />
            ) : forecastError ? (
              <ErrorMessage 
                message={forecastError instanceof Error ? forecastError.message : 'Error loading forecast data. Please check API connection.'}
                onRetry={() => window.location.reload()}
              />
            ) : !loadData || !forecastData ? (
              <EmptyState 
                title="No Data Available"
                message="Ensure both real-time load and forecast data are available."
                className="py-8"
              />
            ) : loadComparison ? (
              <div className="bg-slate-700/30 rounded-lg p-6 border border-slate-700/50">
                <div className="flex flex-col sm:flex-row items-center justify-around gap-8">
                  {/* Deviation Bullet Chart */}
                  <div className="w-full sm:w-96" role="img" aria-label={`Forecast deviation: ${loadComparison.errorPercent.toFixed(2)}%`}>
                    <div className="mb-3">
                      <div className="text-sm font-medium text-slate-300 mb-1">Forecast Deviation</div>
                      <div className="text-xs text-slate-400">
                        {loadComparison.errorPercent > 0 ? 'Under-forecast' : loadComparison.errorPercent < 0 ? 'Over-forecast' : 'Perfect match'}: {loadComparison.errorPercent > 0 ? '+' : ''}{loadComparison.errorPercent.toFixed(2)}%
                      </div>
                    </div>
                    <div className="relative" style={{ height: '60px' }}>
                      {/* Background gray bar (battery meter style) */}
                      <div 
                        className="absolute bg-slate-600 rounded-full"
                        style={{ 
                          height: '32px', 
                          top: '14px',
                          left: '0',
                          right: '0',
                        }}
                      />
                      
                      {/* Safe Zone shading (±2%) - centered */}
                      <div 
                        className="absolute bg-green-500/30 rounded-full"
                        style={{ 
                          height: '32px', 
                          top: '14px',
                          left: 'calc(50% - 2%)',
                          width: '4%',
                        }}
                      />
                      
                      {/* Center marker (0% error) - vertical line */}
                      <div 
                        className="absolute bg-slate-200 z-10"
                        style={{ 
                          width: '2px', 
                          height: '32px', 
                          left: '50%', 
                          top: '14px',
                          transform: 'translateX(-50%)',
                        }}
                      />
                      
                      {/* Deviation bar - extends from center */}
                      {Math.abs(loadComparison.errorPercent) > 0 && (() => {
                        const maxDeviation = 10; // Maximum deviation to show (±10%)
                        const deviationPercent = Math.min(Math.abs(loadComparison.errorPercent), maxDeviation);
                        const barWidth = (deviationPercent / maxDeviation) * 50; // 50% of total width (half on each side)
                        const isOverForecast = loadComparison.errorPercent < 0;
                        const isOutsideSafeZone = Math.abs(loadComparison.errorPercent) > 2;
                        
                        return (
                          <div
                            className={`absolute rounded-full z-20 ${
                              isOutsideSafeZone ? 'bg-red-500' : 'bg-blue-500'
                            }`}
                            style={{
                              height: '32px',
                              top: '14px',
                              width: `${barWidth}%`,
                              left: isOverForecast 
                                ? `calc(50% - ${barWidth}%)` 
                                : '50%',
                              transition: 'all 0.3s ease',
                            }}
                          />
                        );
                      })()}
                      
                      {/* Scale markers */}
                      <div className="absolute inset-0 flex justify-between items-end" style={{ top: '46px', paddingLeft: '4px', paddingRight: '4px' }}>
                        <div className="text-xs text-slate-400">-10%</div>
                        <div className="text-xs text-slate-400 font-medium">0%</div>
                        <div className="text-xs text-slate-400">+10%</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Comparison Details */}
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Actual Load</span>
                      <span className="text-lg font-bold">{loadComparison.actual.toLocaleString()} MW</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Forecast Load</span>
                      <span className="text-lg font-bold text-blue-400">{loadComparison.forecast.toLocaleString()} MW</span>
                    </div>
                    <div className="pt-2 border-t border-slate-600">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-400">Forecast Error</span>
                        <span className={`text-lg font-bold flex items-center gap-1 ${
                          loadComparison.accuracy >= 99
                            ? 'text-green-400'
                            : loadComparison.accuracy >= 95
                            ? 'text-yellow-400'
                            : 'text-red-400'
                        }`}>
                          {loadComparison.accuracy >= 99 ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : (
                            <Warning className="w-4 h-4" />
                          )}
                          {loadComparison.error > 0 ? '+' : ''}{loadComparison.error.toLocaleString()} MW
                          <span className="text-sm">
                            ({loadComparison.errorPercent > 0 ? '+' : ''}{loadComparison.errorPercent.toFixed(1)}%)
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState 
                title="Unable to Calculate Load Comparison"
                message="Unable to match real-time load data with forecast data. Please ensure both data sources are available and synchronized."
                className="py-8"
              />
            )}
          </div>

          {/* 2. Forecast Accuracy Metrics */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Forecast Accuracy (24h)</h3>
            {forecastAccuracy ? (
              <div className="bg-slate-700/30 rounded-lg p-6 border border-slate-700/50">
                <div className="space-y-6">
                  <div className="flex items-center justify-center mb-4">
                    <div role="img" aria-label={`Average forecast accuracy: ${forecastAccuracy.average.toFixed(1)}%`}>
                      <CircularGauge
                        value={forecastAccuracy.average}
                        max={100}
                        label="Average Accuracy"
                        unit="%"
                        size={120}
                        strokeWidth={12}
                        showPercentage={false}
                        thresholds={{ low: 95, medium: 98, high: 99 }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-600">
                    <div className="text-center">
                      <div className="text-xs text-slate-500 mb-1">Min</div>
                      <div className="text-sm font-semibold text-red-400">{forecastAccuracy.min.toFixed(1)}%</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-slate-500 mb-1">Average</div>
                      <div className="text-sm font-semibold text-blue-400">{forecastAccuracy.average.toFixed(1)}%</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-slate-500 mb-1">Max</div>
                      <div className="text-sm font-semibold text-green-400">{forecastAccuracy.max.toFixed(1)}%</div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 text-center pt-2 border-t border-slate-600">
                    Based on {forecastAccuracy.sampleSize} hourly comparisons
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-700/50">
                <div className="text-sm text-slate-400 text-center">
                  Insufficient data for accuracy calculation. Need at least 1 hour of matching actual and forecast data.
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* 3. Peak Load Warning Indicator */}
        <div className="mb-8">
          <h3 className="text-base sm:text-lg font-medium mb-3">Peak Load Warning</h3>
          {peakLoadInfo ? (
            <div className="bg-slate-700/30 rounded-lg p-6 border border-slate-700/50">
              <div className="flex flex-col sm:flex-row items-center justify-around gap-6">
                <div role="img" aria-label={`Current load: ${Math.round(peakLoadInfo.current).toLocaleString()} MW, ${peakLoadInfo.percentOfPeak.toFixed(1)}% of peak capacity`}>
                  <CircularGauge
                    value={Math.round(peakLoadInfo.current)}
                    max={peakLoadInfo.peak}
                    label="Current Load"
                    unit="MW"
                    size={140}
                    strokeWidth={14}
                    thresholds={{ low: 70, medium: 85, high: 95 }}
                  />
                </div>
                <div className="flex-1 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Current Load</span>
                    <span className="text-lg font-semibold">{Math.round(peakLoadInfo.current).toLocaleString()} MW</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Peak Capacity</span>
                    <span className="text-lg font-semibold">{peakLoadInfo.peak.toLocaleString()} MW</span>
                  </div>
                  <div className="pt-2 border-t border-slate-600">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-400">Utilization</span>
                      <span className={`text-lg font-bold flex items-center gap-1 ${
                        peakLoadInfo.percentOfPeak > 95
                          ? 'text-red-400 animate-pulse'
                          : peakLoadInfo.percentOfPeak > 85
                          ? 'text-yellow-400'
                          : 'text-green-400'
                      }`}>
                        {peakLoadInfo.percentOfPeak > 95 && <Warning className="w-4 h-4" />}
                        {peakLoadInfo.percentOfPeak.toFixed(1)}%
                      </span>
                    </div>
                    <div 
                      className="w-full h-3 bg-slate-600 rounded-full overflow-hidden"
                      role="progressbar"
                      aria-valuenow={peakLoadInfo.percentOfPeak}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`Peak load utilization: ${peakLoadInfo.percentOfPeak.toFixed(1)}%`}
                    >
                      <div
                        className={`h-full rounded-full transition-all ${
                          peakLoadInfo.percentOfPeak > 95
                            ? 'bg-red-500'
                            : peakLoadInfo.percentOfPeak > 85
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${peakLoadInfo.percentOfPeak}%` }}
                      />
                    </div>
                    {peakLoadInfo.percentOfPeak > 95 && (
                      <div className="text-xs text-red-400 mt-2 flex items-center gap-1">
                        <Warning className="w-3 h-3" />
                        Approaching peak capacity
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <LoadingSkeleton type="card" lines={4} />
          )}
        </div>

        {/* 4. Zonal Load Contribution */}
        <div>
          <h3 className="text-base sm:text-lg font-medium mb-3">Zonal Load Contribution</h3>
          <ResponsiveChart minHeight={256}>
              <AreaChart data={zonalLoadData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="zone"
                  stroke="#9ca3af"
                  tick={{ fill: '#9ca3af' }}
                />
                <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  labelStyle={{ color: '#e2e8f0' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Area
                  type="monotone"
                  dataKey="load"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                  name="Load (MW)"
                />
              </AreaChart>
          </ResponsiveChart>
        </div>
      </EnhancedCard>
    </div>
  );
};

