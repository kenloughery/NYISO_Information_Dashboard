/**
 * Section 9: Advanced Analytics & Context
 * Components:
 * 1. Outage Impact Analyzer
 * 2. Fuel Mix & Generation Stack
 */

import { useMemo } from 'react';
import { useOutages, useFuelMix } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { formatLabel } from '@/utils/format';

export const Section9_AdvancedAnalytics = () => {
  const { data: outagesData } = useOutages({ limit: 100 });
  const { data: fuelMixData } = useFuelMix({ limit: 100 });

  // Outage Impact
  const activeOutages = useMemo(() => {
    if (!outagesData) return [];
    return outagesData
      .filter(o => o.status === 'ACTIVE' || o.status === 'SCHEDULED')
      .slice(0, 10)
      .map(o => ({
        unit: o.unit_name,
        type: o.outage_type,
        capacity: o.mw_capacity || 0,
        start: o.start_time,
        end: o.end_time,
      }));
  }, [outagesData]);

  // Fuel Mix
  const fuelMixChart = useMemo(() => {
    if (!fuelMixData) return [];
    
    const latestTimestamp = fuelMixData[0]?.timestamp;
    const latest = fuelMixData.filter(d => d.timestamp === latestTimestamp);
    
    const grouped: { [key: string]: number } = {};
    latest.forEach(d => {
      grouped[d.fuel_type] = (grouped[d.fuel_type] || 0) + d.generation_mw;
    });
    
    return Object.entries(grouped).map(([fuel, mw]) => ({
      fuel,
      fuelDisplay: formatLabel(fuel),
      mw,
      percentage: (mw / Object.values(grouped).reduce((a, b) => a + b, 0)) * 100,
    }));
  }, [fuelMixData]);

  // Darker color palette optimized for dark theme with good variety
  const fuelColors = [
    '#4f46e5', // Indigo (nuclear, hydro)
    '#059669', // Dark emerald (renewables)
    '#d97706', // Dark amber (natural gas)
    '#dc2626', // Dark red (coal, oil)
    '#7c3aed', // Dark violet (other)
    '#0891b2', // Dark cyan (wind, solar)
    '#c026d3', // Dark magenta (biomass)
    '#64748b', // Slate gray (other fossil)
  ];

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Market Context</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 1. Outage Impact Analyzer */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Active Outages</h3>
            <div className="h-64 overflow-y-auto space-y-2">
              {activeOutages.length > 0 ? (
                activeOutages.map((outage, idx) => (
                  <div key={idx} className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">{outage.unit}</span>
                      <span className="text-xs text-slate-400">{outage.type}</span>
                    </div>
                    <div className="text-xs text-slate-400">
                      Capacity: {outage.capacity.toLocaleString()} MW
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-slate-400 text-sm text-center py-8" role="status" aria-label="No active reported outages">
                  No active reported outages
                </div>
              )}
            </div>
          </div>

          {/* 4. Fuel Mix & Generation Stack */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Fuel Mix & Generation Stack</h3>
            {fuelMixChart.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={fuelMixChart}
                      dataKey="mw"
                      nameKey="fuel"
                      cx="40%"
                      cy="50%"
                      outerRadius={100}
                    >
                      {fuelMixChart.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={fuelColors[index % fuelColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                      labelStyle={{ color: '#e2e8f0' }}
                      itemStyle={{ color: '#e2e8f0' }}
                      formatter={(value: number, name: string, props: any) => [
                        `${value.toLocaleString()} MW (${props.payload.percentage.toFixed(1)}%)`,
                        name
                      ]}
                    />
                    <Legend
                      verticalAlign="middle"
                      align="right"
                      layout="vertical"
                      formatter={(value) => {
                        const data = fuelMixChart.find(d => d.fuel === value);
                        return data ? `${formatLabel(value)} (${data.percentage.toFixed(1)}%)` : formatLabel(value);
                      }}
                      wrapperStyle={{ fontSize: '12px', color: '#e2e8f0' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <LoadingSkeleton type="card" lines={4} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

