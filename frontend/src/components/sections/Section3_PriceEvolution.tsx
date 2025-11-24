/**
 * Section 3: Multi-Timeframe Price Evolution
 * Components:
 * 1. Intraday Price Curves (RT vs DA)
 * 2. Rolling 7-Day Price Distribution
 * 3. Real Time - Day Ahead Spread Waterfall
 */

import { useMemo, useState, Fragment } from 'react';
import { useRealTimeLBMP } from '@/hooks/useRealTimeData';
import { useDayAheadLBMP, useTimeWeightedLBMP, useRTDASpreads } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { ResponsiveChart } from '@/components/common/ResponsiveChart';
import { EnhancedCard } from '@/components/common/EnhancedCard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar, Cell, ReferenceLine } from 'recharts';
import { subHours, format } from 'date-fns';
import { AccessTime, BarChart as BarChartIcon } from '@mui/icons-material';

export const Section3_PriceEvolution = () => {
  const [selectedZones] = useState<string[]>(['WEST', 'N.Y.C.', 'CENTRL']);
  const [timeRange, setTimeRange] = useState<'24h' | '48h' | '72h'>('24h');

  const { data: rtData } = useRealTimeLBMP();
  const { data: daData } = useDayAheadLBMP();
  const { data: twData, isLoading: twLoading, error: twError } = useTimeWeightedLBMP();
  const { data: spreadsData } = useRTDASpreads({ limit: 500 });

  // Prepare price curves data
  const priceCurvesData = useMemo(() => {
    if (!rtData || !daData) return [];
    
    const now = new Date();
    const cutoff = subHours(now, timeRange === '24h' ? 24 : timeRange === '48h' ? 48 : 72);
    
    // Group RT data by timestamp (keep 5-minute resolution)
    const rtByTimestamp: { [key: string]: { [key: string]: number | string; displayTime: string } } = {};
    rtData
      .filter(d => {
        const date = new Date(d.timestamp);
        return date >= cutoff && selectedZones.includes(d.zone_name);
      })
      .forEach(d => {
        const ts = d.timestamp;
        if (!rtByTimestamp[ts]) {
          rtByTimestamp[ts] = { displayTime: format(new Date(ts), 'MM/dd HH:mm') };
        }
        rtByTimestamp[ts][d.zone_name] = d.lbmp;
      });

    // Group DA data by hour (round to nearest hour for alignment)
    const daByHour: { [key: string]: { [zone: string]: number } } = {};
    daData
      .filter(d => {
        const date = new Date(d.timestamp);
        return date >= cutoff && selectedZones.includes(d.zone_name);
      })
      .forEach(d => {
        const date = new Date(d.timestamp);
        // Round to hour
        date.setMinutes(0, 0, 0);
        const hourKey = date.toISOString();
        if (!daByHour[hourKey]) daByHour[hourKey] = {};
        daByHour[hourKey][d.zone_name] = d.lbmp;
      });

    // Create chart data: for each RT timestamp, find matching DA (by hour)
    const chartDataMap: { [key: string]: any } = {};
    
    // Add RT data points
    Object.entries(rtByTimestamp).forEach(([ts, data]) => {
      const date = new Date(ts);
      const hourKey = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), 0, 0).toISOString();
      
      const chartPoint: any = {
        timestamp: ts,
        time: data.displayTime,
      };
      
      selectedZones.forEach(zone => {
        chartPoint[`${zone}_RT`] = data[zone] ?? null;
        // Find DA value for this hour
        chartPoint[`${zone}_DA`] = daByHour[hourKey]?.[zone] ?? null;
      });
      
      chartDataMap[ts] = chartPoint;
    });
    
    // Add DA-only data points (if any)
    Object.entries(daByHour).forEach(([hourKey, zoneData]) => {
      // Check if we already have this hour covered by RT data
      const hourDate = new Date(hourKey);
      const hasRTData = Object.keys(rtByTimestamp).some(ts => {
        const rtDate = new Date(ts);
        return rtDate.getTime() >= hourDate.getTime() && rtDate.getTime() < hourDate.getTime() + 3600000;
      });
      
      if (!hasRTData) {
        const chartPoint: any = {
          timestamp: hourKey,
          time: format(hourDate, 'MM/dd HH:mm'),
        };
        
        selectedZones.forEach(zone => {
          chartPoint[`${zone}_RT`] = null;
          chartPoint[`${zone}_DA`] = zoneData[zone] ?? null;
        });
        
        chartDataMap[hourKey] = chartPoint;
      }
    });
    
    // Convert to array and sort by timestamp
    return Object.values(chartDataMap).sort((a: any, b: any) => {
      return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
    });
  }, [rtData, daData, selectedZones, timeRange]);

  // Prepare 7-day price distribution with statistical annotations
  const priceDistribution = useMemo(() => {
    if (!twData || twData.length === 0) return null;
    
    const sevenDaysAgo = subHours(new Date(), 168);
    const prices = twData
      .filter(d => {
        const date = new Date(d.timestamp);
        return date >= sevenDaysAgo && d.lbmp != null && !isNaN(d.lbmp);
      })
      .map(d => d.lbmp)
      .sort((a, b) => a - b);
    
    if (prices.length === 0) return null;
    
    // Calculate quartiles
    const q1 = prices[Math.floor(prices.length * 0.25)];
    const median = prices[Math.floor(prices.length * 0.5)];
    const q3 = prices[Math.floor(prices.length * 0.75)];
    const min = prices[0];
    const max = prices[prices.length - 1];
    
    // Calculate mean and standard deviation
    const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
    const variance = prices.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / prices.length;
    const stdDev = Math.sqrt(variance);
    
    // Get current price (most recent)
    const current = twData[0]?.lbmp || median;
    
    return { min, q1, median, q3, max, mean, stdDev, current, sampleSize: prices.length };
  }, [twData]);
  
  // Calculate statistical annotations for price curves
  const priceStats = useMemo(() => {
    if (!priceCurvesData || priceCurvesData.length === 0) return null;
    
    const allPrices: number[] = [];
    selectedZones.forEach(zone => {
      priceCurvesData.forEach((point: any) => {
        const rtPrice = point[`${zone}_RT`];
        const daPrice = point[`${zone}_DA`];
        if (rtPrice != null && !isNaN(rtPrice)) allPrices.push(rtPrice);
        if (daPrice != null && !isNaN(daPrice)) allPrices.push(daPrice);
      });
    });
    
    if (allPrices.length === 0) return null;
    
    const mean = allPrices.reduce((a, b) => a + b, 0) / allPrices.length;
    const variance = allPrices.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / allPrices.length;
    const stdDev = Math.sqrt(variance);
    const sorted = [...allPrices].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    
    return { mean, stdDev, median, min: sorted[0], max: sorted[sorted.length - 1] };
  }, [priceCurvesData, selectedZones]);

  // Prepare Real Time - Day Ahead spread waterfall - Aggregate by timestamp (average across zones)
  const spreadWaterfall = useMemo(() => {
    if (!spreadsData || spreadsData.length === 0) return [];
    
    // Group by timestamp and calculate average spread across zones
    const byTimestamp: { [key: string]: { spreads: number[], rtPrices: number[], daPrices: number[] } } = {};
    spreadsData.forEach(d => {
      const timestamp = d.timestamp;
      if (!byTimestamp[timestamp]) {
        byTimestamp[timestamp] = { spreads: [], rtPrices: [], daPrices: [] };
      }
      byTimestamp[timestamp].spreads.push(d.spread);
      byTimestamp[timestamp].rtPrices.push(d.rt_lbmp);
      byTimestamp[timestamp].daPrices.push(d.da_lbmp);
    });
    
    // Convert to array, average per timestamp, and sort by timestamp
    const chartData = Object.entries(byTimestamp)
      .map(([timestamp, values]) => ({
        timestamp,
        time: format(new Date(timestamp), 'MM/dd HH:mm'),
        spread: values.spreads.reduce((a, b) => a + b, 0) / values.spreads.length,
        avgRtPrice: values.rtPrices.reduce((a, b) => a + b, 0) / values.rtPrices.length,
        avgDaPrice: values.daPrices.reduce((a, b) => a + b, 0) / values.daPrices.length,
      }))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    
    // Filter to selected time range
    const now = new Date();
    const hoursAgo = timeRange === '24h' ? 24 : timeRange === '48h' ? 48 : 72;
    const cutoffTime = new Date(now.getTime() - hoursAgo * 60 * 60 * 1000);
    const filteredData = chartData.filter(d => new Date(d.timestamp) >= cutoffTime);
    
    // If we have hourly data, show all. If we have 5-minute data, sample to avoid overcrowding
    // Show more points for longer time ranges
    const maxPoints = timeRange === '24h' ? 48 : timeRange === '48h' ? 96 : 144;
    if (filteredData.length > maxPoints) {
      // Sample to get approximately maxPoints evenly spaced points
      const step = Math.ceil(filteredData.length / maxPoints);
      return filteredData.filter((_, idx) => idx % step === 0 || idx === filteredData.length - 1);
    }
    
    return filteredData;
  }, [spreadsData, timeRange]);

  const zoneColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      <EnhancedCard>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
          <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold">Multi-Timeframe Price Evolution</h2>
          <div className="flex items-center gap-2">
            <AccessTime className="w-4 h-4 text-slate-400" />
            <div className="flex gap-2 bg-slate-700/50 p-1 rounded-lg" role="tablist" aria-label="Time range selector">
              {(['24h', '48h', '72h'] as const).map(range => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  onKeyDown={(e: React.KeyboardEvent) => e.key === 'Enter' && setTimeRange(range)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    timeRange === range
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-300 hover:bg-slate-600 hover:text-white'
                  }`}
                  role="tab"
                  aria-selected={timeRange === range}
                  aria-label={`Select ${range} time range`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {/* Statistical Summary */}
        {priceStats && (
          <div className="mb-4 p-3 bg-slate-700/30 rounded-lg border border-slate-700/50">
            <div className="flex items-center gap-2 mb-2">
              <BarChartIcon className="w-4 h-4 text-slate-400" />
              <span className="text-xs font-medium text-slate-400">Statistical Summary ({timeRange})</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
              <div>
                <div className="text-slate-500">Average Price</div>
                <div className="font-semibold text-slate-200">${priceStats.mean.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-slate-500">Median Price</div>
                <div className="font-semibold text-blue-400">${priceStats.median.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-slate-500">Standard Deviation</div>
                <div className="font-semibold text-slate-200">${priceStats.stdDev.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-slate-500">Minimum Price</div>
                <div className="font-semibold text-green-400">${priceStats.min.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-slate-500">Maximum Price</div>
                <div className="font-semibold text-red-400">${priceStats.max.toFixed(2)}</div>
              </div>
            </div>
          </div>
        )}

        {/* 1. Intraday Price Curves */}
        <div className="mb-6">
          <h3 className="text-base sm:text-lg font-medium mb-3">Real Time vs Day Ahead Price Curves</h3>
          <ResponsiveChart minHeight={400}>
              <LineChart data={priceCurvesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="time"
                  stroke="#9ca3af"
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  stroke="#9ca3af" 
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  label={{ value: 'Price ($/MWh)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
                  itemStyle={{ color: '#e2e8f0' }}
                  formatter={(value: number, name: string) => [`$${value.toFixed(2)}`, name]}
                />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }}
                  iconType="line"
                  content={({ payload }) => (
                    <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '16px', paddingTop: '20px' }}>
                      {payload?.map((entry, index) => {
                        const isDashed = entry.value?.includes('Day Ahead');
                        return (
                          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <svg width="20" height="12" style={{ display: 'inline-block' }}>
                              <line
                                x1="0"
                                y1="6"
                                x2="20"
                                y2="6"
                                stroke={entry.color}
                                strokeWidth={isDashed ? 2 : 2.5}
                                strokeDasharray={isDashed ? "8 4" : "0"}
                              />
                            </svg>
                            <span style={{ color: '#e2e8f0', fontSize: '12px' }}>{entry.value}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                />
                {selectedZones.map((zone, idx) => (
                  <Fragment key={zone}>
                    <Line
                      type="monotone"
                      dataKey={`${zone}_RT`}
                      stroke={zoneColors[idx % zoneColors.length]}
                      strokeWidth={2.5}
                      dot={false}
                      name={`${zone} (Real Time)`}
                      connectNulls={false}
                    />
                    <Line
                      type="monotone"
                      dataKey={`${zone}_DA`}
                      stroke={zoneColors[idx % zoneColors.length]}
                      strokeWidth={2}
                      strokeDasharray="8 4"
                      dot={false}
                      name={`${zone} (Day Ahead)`}
                      connectNulls={false}
                    />
                  </Fragment>
                ))}
              </LineChart>
          </ResponsiveChart>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 2. Rolling 7-Day Price Distribution */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">7-Day Price Distribution</h3>
            {twLoading ? (
              <LoadingSkeleton type="card" lines={8} />
            ) : twError ? (
              <ErrorMessage 
                message={twError instanceof Error ? twError.message : 'Error loading price distribution data. Please check API connection.'}
                onRetry={() => window.location.reload()}
              />
            ) : priceDistribution ? (
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="space-y-3">
                  {/* Statistical Summary */}
                  <div className="grid grid-cols-2 gap-3 pb-3 border-b border-slate-600">
                    <div>
                      <div className="text-xs text-slate-500">Average Price</div>
                      <div className="font-semibold text-slate-200">${priceDistribution.mean.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Standard Deviation</div>
                      <div className="font-semibold text-slate-200">${priceDistribution.stdDev.toFixed(2)}</div>
                    </div>
                  </div>
                  
                  {/* Quartiles */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">Minimum Price</span>
                      <span className="font-semibold text-green-400">${priceDistribution.min.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">First Quartile (25th Percentile)</span>
                      <span className="font-semibold">${priceDistribution.q1.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">Median (50th Percentile)</span>
                      <span className="font-semibold text-blue-400">${priceDistribution.median.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">Third Quartile (75th Percentile)</span>
                      <span className="font-semibold">${priceDistribution.q3.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">Maximum Price</span>
                      <span className="font-semibold text-red-400">${priceDistribution.max.toFixed(2)}</span>
                    </div>
                  </div>
                  
                  {/* Current Price */}
                  <div className="pt-3 border-t border-slate-600">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-300">Current Price</span>
                      <span className={`font-bold text-lg ${
                        priceDistribution.current > priceDistribution.q3
                          ? 'text-red-400'
                          : priceDistribution.current < priceDistribution.q1
                          ? 'text-green-400'
                          : 'text-blue-400'
                      }`}>
                        ${priceDistribution.current.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {priceDistribution.current > priceDistribution.q3 
                        ? 'Above 75th percentile'
                        : priceDistribution.current < priceDistribution.q1
                        ? 'Below 25th percentile'
                        : 'Within interquartile range'}
                    </div>
                  </div>
                  
                  {/* Sample Size */}
                  <div className="text-xs text-slate-500 pt-2 border-t border-slate-600">
                    Sample Size: {priceDistribution.sampleSize.toLocaleString()} data points
                  </div>
                </div>
              </div>
            ) : twData && twData.length > 0 ? (
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">
                  Insufficient data for 7-day distribution. Found {twData.length} records. Need more historical data.
                </div>
              </div>
            ) : (
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">
                  No time-weighted LBMP data available. Ensure the scraper has collected P-4A data.
                </div>
              </div>
            )}
          </div>

          {/* 3. Real Time - Day Ahead Spread Waterfall */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Real Time - Day Ahead Spread Waterfall</h3>
            <ResponsiveChart minHeight={256}>
              <BarChart data={spreadWaterfall}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="time"
                    stroke="#9ca3af"
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis 
                    stroke="#9ca3af" 
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    label={{ value: 'Spread ($/MWh)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
                    itemStyle={{ color: '#e2e8f0' }}
                    formatter={(value: number) => [`$${value.toFixed(2)}/MWh`, 'Spread']}
                  />
                  <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" />
                  <Bar
                    dataKey="spread"
                    name="Spread ($/MWh)"
                  >
                    {spreadWaterfall.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.spread > 0 ? '#10b981' : entry.spread < 0 ? '#ef4444' : '#6b7280'} 
                      />
                    ))}
                  </Bar>
                </BarChart>
            </ResponsiveChart>
          </div>
        </div>
      </EnhancedCard>
    </div>
  );
};

