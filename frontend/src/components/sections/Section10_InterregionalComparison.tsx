/**
 * Section 10: Interregional Price & Volume Comparison
 * Components:
 * 1. Connection Point Comparison Table
 * 2. Price Differential Visualization
 * 3. Summary Cards
 */

import { useMemo, useState } from 'react';
import { useInterregionalFlows } from '@/hooks/useRealTimeData';
import { useExternalRTOPrices } from '@/hooks/useHistoricalData';
import { useRealTimeLBMP } from '@/hooks/useRealTimeData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { ResponsiveChart } from '@/components/common/ResponsiveChart';
import { EnhancedCard } from '@/components/common/EnhancedCard';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';
import type { ConnectionPointData } from '@/types/api';
import { formatLabel } from '@/utils/format';

// Interface-to-Zone Mapping
const INTERFACE_ZONE_MAPPING: Record<string, string> = {
  // PJM Interfaces
  'SCH - PJM_HTP': 'CENTRL',
  'SCH - PJM_NEPTUNE': 'LONGIL',
  'SCH - PJM_VFT': 'CENTRL',
  'SCH - PJM_KEYSTONE': 'WEST',
  
  // ISO-NE Interfaces
  'SCH - NE - NY': 'LONGIL',
  'SCH - N.E.': 'LONGIL',
  
  // IESO Interfaces
  'SCH - OH - NY': 'WEST',
  'SCH - ONTARIO': 'WEST',
  
  // HQ Interfaces
  'SCH - HQ - NY': 'NORTH',
  'SCH - HQ_CEDARS': 'NORTH',
};

// Region-to-RTO Mapping
const REGION_RTO_MAPPING: Record<string, string> = {
  'PJM': 'PJM',
  'ISO-NE': 'ISO-NE',
  'IESO': 'IESO',
  'HQ': 'IESO', // Note: HQ may not have separate price data
};

// Region Colors
const REGION_COLORS: Record<string, string> = {
  'PJM': '#f97316', // Orange
  'ISO-NE': '#3b82f6', // Blue
  'IESO': '#10b981', // Green
  'HQ': '#a855f7', // Purple
};

// Node Name Display Mapping
const NODE_DISPLAY_NAMES: Record<string, string> = {
  'HQ - NY': 'Chateauguay',
  'NE - NY': 'ISO-NE',
  'ISO-NE - NE - NY': 'ISO-NE',
};

// Helper function to get display name for node
const getNodeDisplayName = (region: string, nodeName: string): string => {
  // Check if nodeName itself is in the mapping (e.g., "HQ - NY")
  if (NODE_DISPLAY_NAMES[nodeName]) {
    return NODE_DISPLAY_NAMES[nodeName];
  }
  // Check if region + nodeName combination is in mapping
  const key = `${region} - ${nodeName}`;
  if (NODE_DISPLAY_NAMES[key]) {
    return NODE_DISPLAY_NAMES[key];
  }
  // Default to original nodeName
  return nodeName;
};

type RegionFilter = 'All' | 'PJM' | 'ISO-NE' | 'IESO' | 'HQ';
type DirectionFilter = 'All' | 'import' | 'export';

export const Section10_InterregionalComparison = () => {
  const { data: flowsData, isLoading: flowsLoading, error: flowsError } = useInterregionalFlows({ limit: 100 });
  const { data: externalPrices } = useExternalRTOPrices({ limit: 100 });
  const { data: nyisoPrices } = useRealTimeLBMP();
  
  const [regionFilter, setRegionFilter] = useState<RegionFilter>('All');
  const [directionFilter, setDirectionFilter] = useState<DirectionFilter>('All');

  // Combine interregional flows with prices
  const connectionPointData = useMemo((): ConnectionPointData[] => {
    if (!flowsData || !nyisoPrices || !externalPrices || flowsData.length === 0) return [];
    
    const latestNYISOTimestamp = nyisoPrices[0]?.timestamp;
    const latestExternalTimestamp = externalPrices[0]?.timestamp;
    
    // Group external prices by RTO
    const rtoPriceMap: { [key: string]: typeof externalPrices[0] } = {};
    externalPrices.forEach(ep => {
      const rtoName = ep.rto_name.toUpperCase();
      if (!rtoPriceMap[rtoName] || new Date(ep.timestamp) > new Date(rtoPriceMap[rtoName].timestamp)) {
        rtoPriceMap[rtoName] = ep;
      }
    });
    
    return flowsData
      .filter(flow => {
        // Filter out HQ - IMPORT_EXPORT as it's missing required data
        return !(flow.region === 'HQ' && flow.node_name === 'IMPORT_EXPORT');
      })
      .map(flow => {
        // Get NYISO zone for this interface
        const zone = INTERFACE_ZONE_MAPPING[flow.interface_name] || 'UNKNOWN';
        
        // Get NYISO price for this zone
        const zonePrice = nyisoPrices.find(
          p => p.timestamp === latestNYISOTimestamp && p.zone_name === zone
        )?.lbmp || 0;
      
      // Get external RTO price
      const rtoName = REGION_RTO_MAPPING[flow.region] || flow.region;
      const rtoPriceRecord = rtoPriceMap[rtoName.toUpperCase()];
      const externalPrice = rtoPriceRecord?.cts_price ?? rtoPriceRecord?.rtc_price ?? null;
      
      // Calculate price differential (null if external price not available)
      const priceDifferential = externalPrice !== null ? zonePrice - externalPrice : null;
      
      // Determine arbitrage opportunity (|differential| > $5/MWh && utilization < 85%)
      const arbitrageOpportunity = priceDifferential !== null &&
                                   Math.abs(priceDifferential) > 5 && 
                                   flow.utilization_percent !== null &&
                                   flow.utilization_percent < 85;
      
      return {
        ...flow,
        zone,
        nyisoPrice: zonePrice,
        externalPrice,
        priceDifferential,
        arbitrageOpportunity,
        importMW: flow.direction === 'import' ? flow.flow_mw : 0,
        exportMW: flow.direction === 'export' ? Math.abs(flow.flow_mw) : 0,
      };
    });
  }, [flowsData, nyisoPrices, externalPrices]);

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let filtered = [...connectionPointData];
    
    // Apply region filter
    if (regionFilter !== 'All') {
      filtered = filtered.filter(d => d.region === regionFilter);
    }
    
    // Apply direction filter
    if (directionFilter !== 'All') {
      filtered = filtered.filter(d => d.direction === directionFilter);
    }
    
    return filtered;
  }, [connectionPointData, regionFilter, directionFilter]);

  // Summary metrics
  const summaryMetrics = useMemo(() => {
    const totalImport = connectionPointData
      .filter(d => d.direction === 'import')
      .reduce((sum, d) => sum + d.flow_mw, 0);
    
    const totalExport = connectionPointData
      .filter(d => d.direction === 'export')
      .reduce((sum, d) => sum + Math.abs(d.flow_mw), 0);
    
    const totalVolume = connectionPointData.reduce((sum, d) => sum + Math.abs(d.flow_mw), 0);
    const weightedDifferential = totalVolume > 0
      ? connectionPointData
          .filter(d => d.priceDifferential !== null)
          .reduce((sum, d) => 
            sum + ((d.priceDifferential ?? 0) * Math.abs(d.flow_mw)), 0
          ) / connectionPointData.filter(d => d.priceDifferential !== null).reduce((sum, d) => sum + Math.abs(d.flow_mw), 0) || 0
      : 0;
    
    const arbitrageCount = connectionPointData.filter(d => d.arbitrageOpportunity).length;
    
    return {
      totalImport,
      totalExport,
      averagePriceDifferential: weightedDifferential,
      arbitrageOpportunities: arbitrageCount,
    };
  }, [connectionPointData]);

  // Price differential chart data (filter out null values)
  const priceDifferentialChart = useMemo(() => {
    return filteredAndSortedData
      .filter(d => d.priceDifferential !== null)
      .map(d => ({
        connectionPoint: `${d.region} - ${getNodeDisplayName(d.region, d.node_name)}`,
        differential: d.priceDifferential!,
        nyisoPrice: d.nyisoPrice,
        externalPrice: d.externalPrice!,
      }));
  }, [filteredAndSortedData]);

  if (flowsLoading) {
    return (
      <EnhancedCard>
        <LoadingSkeleton type="chart" height="400px" />
      </EnhancedCard>
    );
  }

  if (flowsError) {
    return (
      <EnhancedCard>
        <ErrorMessage 
          message={flowsError instanceof Error ? flowsError.message : "Failed to load interregional flow data"}
          onRetry={() => window.location.reload()}
        />
      </EnhancedCard>
    );
  }

  if (!connectionPointData || connectionPointData.length === 0) {
    return (
      <EnhancedCard>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Interregional Price & Volume Comparison</h2>
        <p className="text-slate-400">No interregional flow data available</p>
      </EnhancedCard>
    );
  }

  return (
    <div className="space-y-6">
      <EnhancedCard>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Interregional Price & Volume Comparison</h2>
        <p className="text-slate-400 mb-6">Comparative analysis of import/export volumes and price differentials at each connection point</p>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">Total Import</div>
            <div className="text-2xl font-bold text-blue-400">
              {summaryMetrics.totalImport.toLocaleString()} MW
            </div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">Total Export</div>
            <div className="text-2xl font-bold text-orange-400">
              {summaryMetrics.totalExport.toLocaleString()} MW
            </div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">Avg Price Diff</div>
            <div className={`text-2xl font-bold ${
              summaryMetrics.averagePriceDifferential > 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {summaryMetrics.averagePriceDifferential > 0 ? '+' : ''}
              ${summaryMetrics.averagePriceDifferential.toFixed(2)}/MWh
            </div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">Arbitrage Opportunities</div>
            <div className={`text-2xl font-bold ${
              summaryMetrics.arbitrageOpportunities > 3 ? 'text-red-400' : 'text-green-400'
            }`}>
              {summaryMetrics.arbitrageOpportunities}
            </div>
          </div>
        </div>

        {/* Filters and Controls */}
        <div className="flex flex-wrap gap-6 mb-8">
          <div>
            <label htmlFor="region-filter" className="text-sm text-slate-400 mr-2">Region:</label>
            <select
              id="region-filter"
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value as RegionFilter)}
              className="bg-slate-700 text-slate-200 rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Filter by region"
            >
              <option value="All">All</option>
              <option value="PJM">PJM</option>
              <option value="ISO-NE">ISO-NE</option>
              <option value="IESO">IESO</option>
              <option value="HQ">HQ</option>
            </select>
          </div>
          <div>
            <label htmlFor="direction-filter" className="text-sm text-slate-400 mr-2">Direction:</label>
            <select
              id="direction-filter"
              value={directionFilter}
              onChange={(e) => setDirectionFilter(e.target.value as DirectionFilter)}
              className="bg-slate-700 text-slate-200 rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Filter by flow direction"
            >
              <option value="All">All</option>
              <option value="import">Import</option>
              <option value="export">Export</option>
            </select>
          </div>
        </div>

        {/* Price Differential Chart */}
        <div className="mb-6">
          <h3 className="text-base sm:text-lg font-medium mb-3">Price Differential by Connection Point</h3>
          <ResponsiveChart minHeight={256}>
              <BarChart data={priceDifferentialChart} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" tick={{ fill: '#9ca3af' }} />
                <YAxis 
                  type="category" 
                  dataKey="connectionPoint" 
                  stroke="#9ca3af" 
                  tick={{ fill: '#9ca3af' }}
                  width={180}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  labelStyle={{ color: '#e2e8f0' }}
                  itemStyle={{ color: '#e2e8f0' }}
                  formatter={(value: number) => [`$${value.toFixed(2)}/MWh`, 'Differential']}
                />
                <Bar dataKey="differential" name="Price Differential ($/MWh)">
                  {priceDifferentialChart.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.differential > 0 ? '#10b981' : '#ef4444'} 
                    />
                  ))}
                </Bar>
              </BarChart>
          </ResponsiveChart>
        </div>

        {/* Connection Point Comparison Table */}
        <div>
          <h3 className="text-base sm:text-lg font-medium mb-3">Connection Point Comparison</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" role="table" aria-label="Connection Point Comparison">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left p-3 text-slate-300" scope="col">Connection Point</th>
                  <th className="text-left p-3 text-slate-300" scope="col">NYISO Zone</th>
                  <th className="text-right p-3 text-slate-300" scope="col">Flow (MW)</th>
                  <th className="text-center p-3 text-slate-300" scope="col">Direction</th>
                  <th className="text-right p-3 text-slate-300" scope="col">Utilization</th>
                  <th className="text-right p-3 text-slate-300" scope="col">NYISO Price</th>
                  <th className="text-right p-3 text-slate-300" scope="col">External Price</th>
                  <th className="text-right p-3 text-slate-300" scope="col">Price Diff</th>
                  <th className="text-center p-3 text-slate-300" scope="col">Arbitrage</th>
                </tr>
              </thead>
              <tbody>
                {filteredAndSortedData.map((point, idx) => (
                  <tr
                    key={`${point.interface_name}-${idx}`}
                    className={`border-b border-slate-700/50 hover:bg-slate-700/30 ${
                      point.direction === 'import' ? 'bg-blue-500/5' : 'bg-orange-500/5'
                    } ${point.utilization_percent && point.utilization_percent > 85 ? 'border-l-4 border-l-red-500' : ''} ${
                      point.arbitrageOpportunity ? 'bg-green-500/10' : ''
                    }`}
                  >
                    <td className="p-3 font-medium">{point.region} - {getNodeDisplayName(point.region, point.node_name)}</td>
                    <td className="p-3">{formatLabel(point.zone)}</td>
                    <td className="p-3 text-right">{Math.abs(point.flow_mw).toLocaleString()}</td>
                    <td className="p-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        point.direction === 'import' 
                          ? 'bg-blue-500/20 text-blue-400' 
                          : point.direction === 'export'
                          ? 'bg-orange-500/20 text-orange-400'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {point.direction.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      {point.utilization_percent !== null ? (
                        <div className="flex items-center justify-end gap-2">
                          <div className="w-16 h-2 bg-slate-600 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all"
                              style={{ 
                                width: `${Math.max(point.utilization_percent, 0)}%`,
                                minWidth: point.utilization_percent > 0 ? '2px' : '0px',
                                height: '100%',
                                backgroundColor: point.utilization_percent > 85
                                  ? '#ef4444'  // status-danger - red
                                  : point.utilization_percent > 50
                                  ? '#f59e0b'  // status-warning - orange
                                  : '#10b981', // status-success - green
                                display: 'block',
                                position: 'relative'
                              }}
                            />
                          </div>
                          <span>{point.utilization_percent.toFixed(0)}%</span>
                        </div>
                      ) : (
                        <span className="text-slate-500">N/A</span>
                      )}
                    </td>
                    <td className="p-3 text-right">${point.nyisoPrice.toFixed(2)}</td>
                    <td className="p-3 text-right">
                      {point.externalPrice !== null ? `$${point.externalPrice.toFixed(2)}` : '—'}
                    </td>
                    <td className={`p-3 text-right font-semibold ${
                      point.priceDifferential !== null
                        ? (point.priceDifferential > 0 ? 'text-status-success' : 'text-status-danger')
                        : 'text-slate-500'
                    }`}>
                      {point.priceDifferential !== null
                        ? `${point.priceDifferential > 0 ? '+' : ''}$${point.priceDifferential.toFixed(2)}`
                        : '—'}
                    </td>
                    <td className="p-3 text-center">
                      {point.arbitrageOpportunity ? (
                        <span className="text-status-success text-lg">🟢</span>
                      ) : (
                        <span className="text-slate-500">⚪</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </EnhancedCard>
    </div>
  );
};


