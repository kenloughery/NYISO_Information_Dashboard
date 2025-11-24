/**
 * Section 1: Real-Time Market Overview (Top Banner)
 * Components:
 * 1. System Status Indicator
 * 2. NYISO-Wide RT Price
 * 3. Total Load Ticker
 * 4. Critical Interface Utilization
 * 5. Active Constraints Ticker
 */

import { useMemo } from 'react';
import { useRealTimeLBMP, useRealTimeLoad, useInterregionalFlows, useConstraints, useMarketAdvisories } from '@/hooks/useRealTimeData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { Sparklines, SparklinesLine } from 'react-sparklines';
import { Bolt, Power, SwapHoriz, Warning, AttachMoney } from '@mui/icons-material';

interface Section1_RealTimeOverviewProps {
  lastUpdated?: string | null;
}

export const Section1_RealTimeOverview = ({ lastUpdated }: Section1_RealTimeOverviewProps) => {
  const { data: lbmpData, isLoading: lbmpLoading, error: lbmpError } = useRealTimeLBMP();
  const { data: loadData, isLoading: loadLoading, error: loadError } = useRealTimeLoad();
  const { data: interregionalFlows, isLoading: interfaceLoading } = useInterregionalFlows({ limit: 100 });
  const { data: constraintsData, isLoading: constraintsLoading } = useConstraints({ market_type: 'realtime' });
  const { data: advisoriesData } = useMarketAdvisories({ limit: 10 });

  // Calculate NYISO-wide RT price (weighted average)
  const nyisoWidePrice = useMemo(() => {
    if (!lbmpData || lbmpData.length === 0) return null;
    
    // Get latest timestamp
    const latestTimestamp = lbmpData[0]?.timestamp;
    const latestData = lbmpData.filter(d => d.timestamp === latestTimestamp);
    
    if (latestData.length === 0) return null;
    
    // Simple average (could be weighted by load if available)
    const avg = latestData.reduce((sum, d) => sum + d.lbmp, 0) / latestData.length;
    return avg;
  }, [lbmpData]);

  // Get 24-hour price history for sparkline
  const priceHistory = useMemo(() => {
    if (!lbmpData) return [];
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    // Group by hour and average
    const hourly: { [key: string]: number[] } = {};
    lbmpData.forEach(d => {
      const date = new Date(d.timestamp);
      if (date >= yesterday) {
        const hour = date.toISOString().slice(0, 13);
        if (!hourly[hour]) hourly[hour] = [];
        hourly[hour].push(d.lbmp);
      }
    });
    
    return Object.keys(hourly)
      .sort()
      .map(hour => hourly[hour].reduce((a, b) => a + b, 0) / hourly[hour].length);
  }, [lbmpData]);

  // Calculate total load
  const totalLoad = useMemo(() => {
    if (!loadData || loadData.length === 0) return null;
    const latestTimestamp = loadData[0]?.timestamp;
    const latestLoads = loadData.filter(d => d.timestamp === latestTimestamp);
    return latestLoads.reduce((sum, d) => sum + d.load, 0);
  }, [loadData]);

  // Get critical interfaces (HQ, IESO, PJM, ISO-NE) - Aggregate all connection points by region
  const criticalInterfaces = useMemo(() => {
    // Always show all 4 critical regions, even if no data
    const critical = ['HQ', 'IESO', 'PJM', 'ISO-NE'];
    
    // Map internal names to display names
    const displayNames: { [key: string]: string } = {
      'HQ': 'HQ (Hydro-Québec)',
      'IESO': 'IESO (Ontario)',
      'PJM': 'PJM - Interconnection',
      'ISO-NE': 'ISO-NE (New England)',
    };
    
    if (!interregionalFlows || interregionalFlows.length === 0) {
      // Return all regions with no data
      return critical.map(name => ({
        name: displayNames[name] || name,
        flow: 0,
        limit: 0,
        utilization: 0,
        hasData: false,
      }));
    }
    
    const latestTimestamp = interregionalFlows[0]?.timestamp;
    const latest = interregionalFlows.filter(d => d.timestamp === latestTimestamp);
    
    // Debug: Check what regions we have in the data
    const uniqueRegions = [...new Set(latest.map(f => f.region))];
    console.log('Available regions in data:', uniqueRegions);
    console.log('Latest flows sample:', latest.slice(0, 3));
    
    // Aggregate flows by region (sum all connection points for each region)
    const regionAggregates: { [key: string]: { flow: number; positiveLimit: number; negativeLimit: number } } = {};
    
    latest.forEach(flow => {
      const region = flow.region;
      if (!regionAggregates[region]) {
        regionAggregates[region] = { flow: 0, positiveLimit: 0, negativeLimit: 0 };
      }
      
      // Sum flows (positive = import, negative = export)
      const flowValue = flow.flow_mw ?? 0;
      regionAggregates[region].flow += flowValue;
      
      // Sum limits (use maximum available capacity)
      const posLimit = flow.positive_limit_mw ?? 0;
      const negLimit = flow.negative_limit_mw ?? 0;
      regionAggregates[region].positiveLimit += Math.abs(posLimit);
      regionAggregates[region].negativeLimit += Math.abs(negLimit);
    });
    
    // Debug logging
    console.log('Region Aggregates:', regionAggregates);
    
    // Calculate utilization for each region - Always show all 4 critical regions
    return critical.map(name => {
      const aggregate = regionAggregates[name];
      const displayName = displayNames[name] || name;
      
      // If no data for this region, show with 0 values
      if (!aggregate) {
        console.log(`Interface ${name}: No aggregate data found`);
        return {
          name: displayName,
          flow: 0,
          limit: 0,
          utilization: 0,
          hasData: false,
        };
      }
      
      // Determine direction and use appropriate limit
      const isImport = aggregate.flow > 0;
      const limit = isImport ? aggregate.positiveLimit : aggregate.negativeLimit;
      const flow = Math.abs(aggregate.flow);
      
      // Calculate utilization - if limit is 0 but flow exists, show flow but no utilization bar
      const utilization = limit > 0 ? (flow / limit) * 100 : 0;
      
      const result = {
        name: displayName,
        flow,
        limit,
        utilization: Math.min(utilization, 100),
        hasData: aggregate.positiveLimit > 0 || aggregate.negativeLimit > 0 || flow > 0, // Has data if any limit or flow exists
      };
      
      // Debug logging
      console.log(`Interface ${name}:`, {
        ...result,
        rawAggregate: aggregate,
        isImport,
        calculatedLimit: limit,
      });
      
      return result;
    });
  }, [interregionalFlows]);

  // Get active constraints
  const activeConstraints = useMemo(() => {
    if (!constraintsData) return [];
    return constraintsData
      .filter(c => c.binding_status === 'BINDING' || c.shadow_price && c.shadow_price > 0)
      .slice(0, 10)
      .map(c => ({
        name: c.constraint_name,
        shadowPrice: c.shadow_price || 0,
      }));
  }, [constraintsData]);

  // System status from advisories
  const systemStatus = useMemo(() => {
    if (!advisoriesData || advisoriesData.length === 0) return 'normal';
    const latest = advisoriesData[0];
    const severity = latest.severity?.toLowerCase() || 'info';
    if (severity.includes('emergency') || severity.includes('critical')) return 'emergency';
    if (severity.includes('warning')) return 'warning';
    return 'normal';
  }, [advisoriesData]);

  const statusColors = {
    normal: 'bg-status-success',
    warning: 'bg-status-warning',
    emergency: 'bg-status-danger',
  };
  
  const statusGradients = {
    normal: 'bg-gradient-to-br from-green-600/20 to-emerald-600/20 border-green-500/30',
    warning: 'bg-gradient-to-br from-yellow-600/20 to-orange-600/20 border-yellow-500/30',
    emergency: 'bg-gradient-to-br from-red-600/20 to-rose-600/20 border-red-500/30',
  };

  // Calculate price trend for sparkline
  const priceTrend = useMemo(() => {
    if (priceHistory.length < 2) return 'neutral';
    const recent = priceHistory.slice(-5);
    const older = priceHistory.slice(-10, -5);
    if (older.length === 0) return 'neutral';
    const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
    if (recentAvg > olderAvg * 1.02) return 'up';
    if (recentAvg < olderAvg * 0.98) return 'down';
    return 'neutral';
  }, [priceHistory]);

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold">Real-Time Market Overview</h2>
        {lastUpdated && (
          <span className="text-sm text-slate-500">Most Recent Data: {lastUpdated}</span>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {/* 1. System Status Indicator - Enhanced */}
          <div 
            className={`${statusGradients[systemStatus]} rounded-xl p-4 border shadow-lg`}
            role="status"
            aria-live="polite"
            aria-label={`System status: ${systemStatus}`}
          >
            <div className="text-xs text-slate-400 font-medium mb-2 flex items-center gap-1">
              <Bolt className="w-3 h-3" aria-hidden="true" />
              System Status
            </div>
            <div className="flex items-center gap-2">
              <div 
                className={`w-3 h-3 rounded-full ${statusColors[systemStatus]} ${systemStatus === 'emergency' ? 'animate-pulse' : ''}`}
                aria-hidden="true"
              />
              <div className="text-lg sm:text-xl font-bold text-white capitalize">{systemStatus}</div>
            </div>
          </div>

          {/* 2. NYISO-Wide RT Price - Enhanced with MetricCard styling */}
          <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-xl p-4 border border-blue-500/30 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs text-slate-400 font-medium flex items-center gap-1">
                <AttachMoney className="w-3 h-3" />
                NYISO-Wide Real Time Price
              </div>
              {priceHistory.length > 0 && (
                <div className="w-20 h-8">
                  <Sparklines data={priceHistory} width={80} height={32}>
                    <SparklinesLine color="#3b82f6" style={{ strokeWidth: 2 }} />
                  </Sparklines>
                </div>
              )}
            </div>
            {lbmpLoading ? (
              <LoadingSkeleton type="text" lines={2} className="h-12" />
            ) : lbmpError ? (
              <ErrorMessage 
                message={lbmpError instanceof Error ? lbmpError.message : 'Failed to load price data'} 
                onRetry={() => window.location.reload()}
                className="m-0"
              />
            ) : nyisoWidePrice !== null ? (
              <div className="flex items-baseline gap-2">
                <div className="text-2xl sm:text-3xl font-bold text-white">${nyisoWidePrice.toFixed(2)}</div>
                <div className="text-sm text-slate-400">/MWh</div>
                {priceTrend !== 'neutral' && (
                  <div className={`text-sm font-semibold ${priceTrend === 'up' ? 'text-status-danger' : 'text-status-success'}`}>
                    {priceTrend === 'up' ? '↑' : '↓'}
                  </div>
                )}
              </div>
            ) : (
              <EmptyState 
                title="No Price Data"
                message="Real-time price data is not available."
                className="py-4"
              />
            )}
          </div>

          {/* 3. Total Load - Enhanced */}
          <div className="bg-gradient-to-br from-pink-400/20 to-fuchsia-400/20 rounded-xl p-4 border border-pink-400/30 shadow-lg">
            <div className="text-xs text-slate-400 font-medium mb-2 flex items-center gap-1">
              <Power className="w-3 h-3" />
              Total Load
            </div>
            {loadLoading ? (
              <LoadingSkeleton type="text" lines={2} className="h-12" />
            ) : loadError ? (
              <ErrorMessage 
                message={loadError instanceof Error ? loadError.message : 'Failed to load load data'} 
                onRetry={() => window.location.reload()}
                className="m-0"
              />
            ) : totalLoad !== null ? (
              <>
                <div className="text-2xl sm:text-3xl font-bold text-white mb-2">{totalLoad.toLocaleString()} <span className="text-lg text-slate-400">MW</span></div>
                <div 
                  className="w-full h-2 bg-slate-700 rounded-full"
                  role="progressbar"
                  aria-valuenow={totalLoad}
                  aria-valuemin={0}
                  aria-valuemax={30000}
                  aria-label={`Total load: ${totalLoad.toLocaleString()} MW, ${((totalLoad / 30000) * 100).toFixed(0)}% of typical peak`}
                >
                  <div
                    className="h-full bg-gradient-to-r from-pink-400 to-fuchsia-400 rounded-full transition-all"
                    style={{ width: `${Math.min((totalLoad / 30000) * 100, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {((totalLoad / 30000) * 100).toFixed(0)}% of typical peak
                </div>
              </>
            ) : (
              <EmptyState 
                title="No Load Data"
                message="Real-time load data is not available."
                className="py-4"
              />
            )}
          </div>

          {/* 4. Critical Interface Utilization - Enhanced */}
          <div className="bg-gradient-to-br from-blue-600/20 to-indigo-600/20 rounded-xl p-4 border border-blue-500/30 shadow-lg">
            <div className="text-xs text-slate-400 mb-3 font-medium flex items-center gap-1">
              <SwapHoriz className="w-3 h-3" />
              Interface Utilization
            </div>
            <div className="space-y-2">
              {interfaceLoading ? (
                <LoadingSkeleton type="text" lines={4} className="h-24" />
              ) : (
                criticalInterfaces.map((iface, idx) => {
                  // Debug: Log each interface being rendered
                  if (idx === 0) {
                    console.log('Rendering interfaces:', criticalInterfaces);
                  }
                  
                  return (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-slate-300">{iface.name}</span>
                        {iface.hasData ? (
                          <span className={`text-xs font-semibold ${
                            iface.utilization > 90
                              ? 'text-status-danger'
                              : iface.utilization > 75
                              ? 'text-status-warning'
                              : 'text-status-success'
                          }`}>
                            {iface.utilization.toFixed(0)}%
                          </span>
                        ) : (
                          <span className="text-xs text-slate-500">No data</span>
                        )}
                      </div>
                      <div 
                        className="w-full h-2 bg-slate-700 rounded-full overflow-hidden relative"
                        role="progressbar"
                        aria-valuenow={iface.hasData ? iface.utilization : 0}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-label={`${iface.name} utilization: ${iface.hasData ? iface.utilization.toFixed(1) : 0}%`}
                      >
                        {iface.hasData && iface.limit > 0 && (
                          <div
                            className="h-full rounded-full transition-all"
                            style={{ 
                              width: `${Math.max(iface.utilization, 0)}%`,
                              minWidth: iface.utilization > 0 ? '2px' : '0px',
                              height: '100%',
                              backgroundColor: iface.utilization > 90
                                ? '#ef4444'  // status-danger
                                : iface.utilization > 75
                                ? '#f59e0b'  // status-warning
                                : '#10b981', // status-success
                              display: 'block',
                              position: 'relative'
                            }}
                          />
                        )}
                        {iface.hasData && iface.limit === 0 && iface.flow > 0 && (
                          <div 
                            className="h-full w-full rounded-full opacity-50" 
                            title="Flow data available but no limit data"
                            style={{ 
                              height: '100%', 
                              backgroundColor: '#475569', // slate-600
                              display: 'block',
                              position: 'relative'
                            }}
                          />
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* 5. Active Constraints Ticker - Enhanced */}
          <div className="bg-gradient-to-br from-orange-500/10 to-red-500/10 rounded-xl p-4 border border-orange-500/20 shadow-lg">
            <div className="text-xs text-slate-400 mb-3 font-medium flex items-center gap-1">
              <Warning className="w-3 h-3" />
              Active Constraints
            </div>
            <div className="h-20 overflow-y-auto space-y-2">
              {constraintsLoading ? (
                <LoadingSkeleton type="text" lines={3} className="h-16" />
              ) : activeConstraints.length > 0 ? (
                activeConstraints.map((c, idx) => (
                  <div key={idx} className="text-xs flex justify-between items-center bg-slate-600/30 rounded px-2 py-1">
                    <span className="truncate flex-1 text-slate-300">{c.name}</span>
                    <span className="text-status-warning ml-2 font-semibold">${c.shadowPrice.toFixed(0)}</span>
                  </div>
                ))
              ) : (
                <div className="text-slate-400 text-xs">No active constraints</div>
              )}
            </div>
          </div>
        </div>
    </div>
  );
};

