/**
 * Section 6: Transmission & Constraint Monitoring
 * Components:
 * 1. Active Constraint Impact Matrix
 * 2. Interface Flow vs Limit Gauges
 * 3. Constraint Persistence Heat Map
 * 4. Congestion Cost Waterfall
 */

import { useMemo } from 'react';
import { useConstraints, useInterregionalFlows } from '@/hooks/useRealTimeData';
import { useRealTimeLBMP } from '@/hooks/useRealTimeData';
import { ResponsiveChart } from '@/components/common/ResponsiveChart';
import { EnhancedCard } from '@/components/common/EnhancedCard';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export const Section6_TransmissionConstraints = () => {
  const { data: constraintsData } = useConstraints({ market_type: 'realtime', limit: 50 });
  const { data: interregionalFlows } = useInterregionalFlows({ limit: 100 });
  const { data: lbmpData } = useRealTimeLBMP();

  // Active Constraint Impact Matrix
  const constraintMatrix = useMemo(() => {
    if (!constraintsData) return [];
    
    return constraintsData
      .filter(c => c.binding_status === 'BINDING' || (c.shadow_price && c.shadow_price > 0))
      .slice(0, 10)
      .map(c => ({
        name: c.constraint_name,
        shadowPrice: c.shadow_price || 0,
        limit: c.limit_mw || 0,
        flow: c.flow_mw || 0,
      }))
      .sort((a, b) => b.shadowPrice - a.shadowPrice);
  }, [constraintsData]);

  // Interface Flow Gauges - Aggregate all connection points by region
  const interfaceGauges = useMemo(() => {
    // Always show all 4 critical regions, even if no data
    const critical = ['HQ', 'IESO', 'PJM', 'ISO-NE'];
    
    if (!interregionalFlows || interregionalFlows.length === 0) {
      // Return all regions with no data
      return critical.map(name => ({
        name,
        flow: 0,
        limit: 0,
        utilization: 0,
        hasData: false,
      }));
    }
    
    const latestTimestamp = interregionalFlows[0]?.timestamp;
    const latest = interregionalFlows.filter(d => d.timestamp === latestTimestamp);
    
    // Aggregate flows by region (sum all connection points for each region)
    const regionAggregates: { [key: string]: { flow: number; positiveLimit: number; negativeLimit: number } } = {};
    
    latest.forEach(flow => {
      const region = flow.region;
      if (!regionAggregates[region]) {
        regionAggregates[region] = { flow: 0, positiveLimit: 0, negativeLimit: 0 };
      }
      
      // Sum flows (positive = import, negative = export)
      regionAggregates[region].flow += flow.flow_mw || 0;
      
      // Sum limits (use maximum available capacity)
      regionAggregates[region].positiveLimit += Math.abs(flow.positive_limit_mw || 0);
      regionAggregates[region].negativeLimit += Math.abs(flow.negative_limit_mw || 0);
    });
    
    // Calculate utilization for each region - Always show all 4 critical regions
    return critical.map(name => {
      const aggregate = regionAggregates[name];
      
      // If no data for this region, show with 0 values
      if (!aggregate) {
        return {
          name,
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
      
      // Calculate utilization
      const utilization = limit > 0 ? (flow / limit) * 100 : 0;
      
      return {
        name,
        flow,
        limit,
        utilization: Math.min(utilization, 100),
        hasData: true,
      };
    });
  }, [interregionalFlows]);

  // Congestion Cost Waterfall
  const congestionData = useMemo(() => {
    if (!lbmpData) return [];
    
    const latestTimestamp = lbmpData[0]?.timestamp;
    const latest = lbmpData.filter(d => d.timestamp === latestTimestamp);
    
    return latest
      .map(d => ({
        zone: d.zone_name,
        energy: d.lbmp - (d.marginal_cost_congestion || 0) - (d.marginal_cost_losses || 0),
        congestion: d.marginal_cost_congestion || 0,
        losses: d.marginal_cost_losses || 0,
        total: d.lbmp,
      }))
      .sort((a, b) => b.congestion - a.congestion)
      .slice(0, 11);
  }, [lbmpData]);

  return (
    <div className="space-y-6">
      <EnhancedCard>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Transmission & Constraint Monitoring</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 1. Active Constraint Impact Matrix */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Active Constraint Impact Matrix</h3>
            <div className="bg-slate-700/30 rounded-lg border border-slate-700/50 overflow-x-auto">
              <table className="w-full text-sm" role="table" aria-label="Active Constraint Impact Matrix">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="text-left p-3 font-semibold text-slate-300" scope="col">Constraint</th>
                    <th className="text-right p-3 font-semibold text-slate-300" scope="col">Shadow Price</th>
                    <th className="text-right p-3 font-semibold text-slate-300" scope="col">Flow</th>
                    <th className="text-right p-3 font-semibold text-slate-300" scope="col">Limit</th>
                  </tr>
                </thead>
                <tbody>
                  {constraintMatrix.map((c) => (
                    <tr key={c.name} className="border-b border-slate-700/50 hover:bg-slate-700/50 transition-colors">
                      <td className="p-3 font-medium text-slate-200 truncate max-w-xs" title={c.name}>{c.name}</td>
                      <td className={`p-3 text-right font-semibold ${
                        c.shadowPrice > 50 ? 'text-red-400' : c.shadowPrice > 10 ? 'text-yellow-400' : 'text-slate-300'
                      }`}>
                        ${c.shadowPrice.toFixed(2)}
                      </td>
                      <td className="p-3 text-right text-slate-200">{c.flow.toLocaleString()} MW</td>
                      <td className="p-3 text-right text-slate-400">{c.limit.toLocaleString()} MW</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 2. Interface Flow Gauges */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Interface Flow Utilization</h3>
            <div className="space-y-6" role="list" aria-label="Interface flow utilization">
              {interfaceGauges.map((iface) => (
                <div key={iface.name} role="listitem">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{iface.name}</span>
                    {iface.hasData ? (
                      <span 
                        className={`text-sm font-semibold ${
                          iface.utilization > 90 ? 'text-status-danger' : iface.utilization > 75 ? 'text-status-warning' : 'text-status-success'
                        }`}
                        aria-label={`${iface.name} utilization: ${iface.utilization.toFixed(1)}%`}
                      >
                        {iface.utilization.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-sm text-slate-500" aria-label={`${iface.name}: No data available`}>
                        No data
                      </span>
                    )}
                  </div>
                  <div 
                    className="w-full h-3 bg-slate-700 rounded-full overflow-hidden relative"
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
                  {iface.hasData && (
                    <div 
                      className="text-xs text-slate-400 mt-1"
                      aria-label={`${iface.name} flow: ${iface.flow.toLocaleString()} MW, limit: ${iface.limit.toLocaleString()} MW`}
                    >
                      {iface.flow.toLocaleString()} / {iface.limit.toLocaleString()} MW
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 4. Congestion Cost Waterfall */}
        <div>
          <h3 className="text-base sm:text-lg font-medium mb-3">Congestion Cost by Zone</h3>
          <ResponsiveChart minHeight={320}>
              <BarChart data={congestionData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" tick={{ fill: '#9ca3af' }} />
                <YAxis dataKey="zone" type="category" stroke="#9ca3af" tick={{ fill: '#9ca3af' }} width={80} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  labelStyle={{ color: '#e2e8f0' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Bar dataKey="energy" stackId="a" fill="#3b82f6" name="Energy" />
                <Bar dataKey="congestion" stackId="a" fill="#f59e0b" name="Congestion" />
                <Bar dataKey="losses" stackId="a" fill="#8b5cf6" name="Losses" />
              </BarChart>
          </ResponsiveChart>
        </div>
      </EnhancedCard>
    </div>
  );
};

