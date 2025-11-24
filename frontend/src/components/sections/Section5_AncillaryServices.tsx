/**
 * Section 5: Ancillary Services Market
 * Components:
 * 1. Ancillary Services Price Table
 * 2. Reserve Margin Gauge
 * 3. AS Price Volatility Index
 */

import { useMemo } from 'react';
import { useAncillaryServices, useReserveMargins, usePriceVolatility } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { ResponsiveChart } from '@/components/common/ResponsiveChart';
import { EnhancedCard } from '@/components/common/EnhancedCard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Warning } from '@mui/icons-material';
import { formatLabel } from '@/utils/format';

export const Section5_AncillaryServices = () => {
  const { data: asData, isLoading: asLoading, error: asError } = useAncillaryServices({ market_type: 'realtime', limit: 100 });
  const { data: reserveData, isLoading: reserveLoading, error: reserveError } = useReserveMargins({ limit: 24 });
  const { data: volatilityData } = usePriceVolatility({ limit: 168 });

  // AS Price Table
  const asPriceTable = useMemo(() => {
    if (!asData) return [];
    
    const latestTimestamp = asData[0]?.timestamp;
    const latest = asData.filter(d => d.timestamp === latestTimestamp);
    
    // Group by service type and zone
    const grouped: { [key: string]: { [zone: string]: number } } = {};
    latest.forEach(d => {
      const key = d.service_type || 'unknown';
      if (!grouped[key]) grouped[key] = {};
      grouped[key][d.zone_name] = d.price || 0;
    });
    
    return Object.entries(grouped).map(([service, zones]) => ({
      service,
      zones,
      avgPrice: Object.values(zones).reduce((a, b) => a + b, 0) / Object.values(zones).length,
    }));
  }, [asData]);

  // Reserve Margin
  const latestReserve = useMemo(() => {
    if (!reserveData || reserveData.length === 0) return null;
    return reserveData[0];
  }, [reserveData]);

  // Volatility Index - Aggregate by timestamp (average across zones)
  const volatilityChart = useMemo(() => {
    if (!volatilityData || volatilityData.length === 0) return [];
    
    // Group by timestamp and average volatility across zones
    const byTimestamp: { [key: string]: number[] } = {};
    volatilityData.forEach(d => {
      const timestamp = d.timestamp;
      if (!byTimestamp[timestamp]) {
        byTimestamp[timestamp] = [];
      }
      byTimestamp[timestamp].push(d.volatility);
    });
    
    // Convert to array, average per timestamp, and sort by timestamp
    const chartData = Object.entries(byTimestamp)
      .map(([timestamp, volatilities]) => ({
        timestamp,
        time: new Date(timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        volatility: volatilities.reduce((a, b) => a + b, 0) / volatilities.length,
      }))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .slice(-24); // Get last 24 unique timestamps
    
    return chartData;
  }, [volatilityData]);

  // Calculate deficit/surplus percentage
  // Reserve margin % = (Generation - Load) / Load * 100
  // Positive = surplus, Negative = deficit
  const reserveMarginPercent = latestReserve?.reserve_margin_percent ?? 0;
  const reserveMarginMW = latestReserve?.reserve_margin_mw ?? 0;
  const totalLoad = latestReserve?.total_load ?? 0;
  
  // Calculate deficit/surplus as percentage of load
  const deficitSurplusPercent = totalLoad > 0 
    ? (reserveMarginMW / totalLoad) * 100 
    : 0;

  return (
    <div className="space-y-6">
      <EnhancedCard>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Ancillary Services Market</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 1. AS Price Table */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Ancillary Services Prices (RT)</h3>
            {asLoading ? (
              <LoadingSkeleton type="table" lines={5} />
            ) : asError ? (
              <ErrorMessage 
                message={asError instanceof Error ? asError.message : 'Error loading ancillary services data. Please check API connection.'}
                onRetry={() => window.location.reload()}
              />
            ) : asPriceTable.length > 0 ? (
              <div className="bg-slate-700/30 rounded-lg border border-slate-700/50 overflow-x-auto">
                <table className="w-full text-sm" role="table" aria-label="Ancillary Services Prices">
                  <thead>
                    <tr className="border-b border-slate-600">
                      <th className="text-left p-3 font-semibold text-slate-300" scope="col">Service Type</th>
                      <th className="text-right p-3 font-semibold text-slate-300" scope="col">Avg Price</th>
                      <th className="text-right p-3 font-semibold text-slate-300" scope="col">Zones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {asPriceTable
                      .sort((a, b) => b.avgPrice - a.avgPrice)
                      .map((row) => {
                        // Capitalize each word in the service type
                        const capitalizedService = formatLabel(row.service)
                          .split(' ')
                          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                          .join(' ');
                        return (
                          <tr key={row.service} className="border-b border-slate-700/50 hover:bg-slate-700/50 transition-colors">
                            <td className="p-3 font-medium text-slate-200">{capitalizedService}</td>
                            <td className="p-3 text-right font-semibold">${row.avgPrice.toFixed(2)}</td>
                            <td className="p-3 text-right text-slate-400">{Object.keys(row.zones).length}</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState 
                title="No Ancillary Services Data"
                message={asData && asData.length === 0 ? "Ensure the scraper has collected P-6B (RT Ancillary Services) data." : "No ancillary services data available."}
                className="py-8"
              />
            )}
          </div>

          {/* 2. Reserve Margin Gauge */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Reserve Margin</h3>
            {reserveLoading ? (
              <LoadingSkeleton type="card" lines={4} />
            ) : reserveError ? (
              <ErrorMessage 
                message={reserveError instanceof Error ? reserveError.message : 'Error loading reserve margin data. Please check API connection.'}
                onRetry={() => window.location.reload()}
              />
            ) : latestReserve ? (
              <div className="bg-slate-700/30 rounded-lg p-6 border border-slate-700/50">
                <div className="flex flex-col sm:flex-row items-center justify-around gap-8">
                  {/* Deficit/Surplus Display - Show Percentage */}
                  <div className="flex flex-col items-center">
                    <div className={`text-4xl font-bold mb-2 ${
                      deficitSurplusPercent > 5
                        ? 'text-green-400'
                        : deficitSurplusPercent > 0
                        ? 'text-yellow-400'
                        : deficitSurplusPercent > -2
                        ? 'text-orange-400'
                        : 'text-red-400'
                    }`}>
                      {deficitSurplusPercent > 0 ? '+' : ''}{deficitSurplusPercent.toFixed(1)}%
                    </div>
                    <div className="text-sm font-medium text-slate-300 mb-1">
                      {deficitSurplusPercent > 0 ? 'System Surplus' : 'System Deficit'}
                    </div>
                  </div>
                  
                  {/* Details */}
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Total Load</span>
                      <span className="text-lg font-semibold">{latestReserve.total_load.toLocaleString()} MW</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Total Generation</span>
                      <span className="text-lg font-semibold">{latestReserve.total_generation.toLocaleString()} MW</span>
                    </div>
                    <div className="pt-2 border-t border-slate-600">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-slate-400">Reserve Margin</span>
                        <span className={`text-lg font-bold flex items-center gap-1 ${
                          reserveMarginMW > 0
                            ? reserveMarginPercent > 15
                              ? 'text-green-400'
                              : reserveMarginPercent > 10
                              ? 'text-yellow-400'
                              : 'text-orange-400'
                            : 'text-red-400'
                        }`}>
                          {reserveMarginMW < 0 && <Warning className="w-4 h-4" />}
                          {reserveMarginMW > 0 ? '+' : ''}{reserveMarginMW.toLocaleString()} MW
                        </span>
                      </div>
                      <div className="w-full h-3 bg-slate-600 rounded-full overflow-hidden">
                        {reserveMarginPercent > 0 ? (
                          <div
                            className={`h-full rounded-full transition-all ${
                              reserveMarginPercent > 15
                                ? 'bg-green-500'
                                : reserveMarginPercent > 10
                                ? 'bg-yellow-500'
                                : 'bg-orange-500'
                            }`}
                            style={{ width: `${Math.min((reserveMarginPercent / 30) * 100, 100)}%` }}
                          />
                        ) : (
                          <div className="h-full w-full bg-red-500/50 rounded-full" />
                        )}
                      </div>
                      {reserveMarginMW < 0 && (
                        <div className="text-xs text-red-400 mt-2 flex items-center gap-1">
                          <Warning className="w-3 h-3" />
                          Generation below load - system deficit
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState 
                title="No Reserve Margin Data"
                message="No reserve margin data available. This is a calculated metric that requires load and generation data."
                className="py-8"
              />
            )}
          </div>
        </div>

        {/* 3. AS Price Volatility Index */}
        <div>
          <h3 className="text-base sm:text-lg font-medium mb-3">AS Price Volatility Index (24h)</h3>
          <ResponsiveChart minHeight={300}>
              <LineChart data={volatilityChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="time"
                  stroke="#9ca3af"
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                />
                <YAxis 
                  stroke="#9ca3af" 
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  label={{ value: 'Volatility Index', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
                  itemStyle={{ color: '#e2e8f0' }}
                  formatter={(value: number) => [value.toFixed(2), 'Volatility']}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Line
                  type="monotone"
                  dataKey="volatility"
                  stroke="#f59e0b"
                  strokeWidth={2.5}
                  dot={false}
                  name="AS Price Volatility"
                />
              </LineChart>
          </ResponsiveChart>
        </div>
      </EnhancedCard>
    </div>
  );
};

