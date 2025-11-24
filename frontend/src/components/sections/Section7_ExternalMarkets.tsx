/**
 * Section 7: External Market & Inter-ISO Flows
 * Components:
 * 1. ATC/TTC Availability Tracker
 */

import { useMemo } from 'react';
import { useATCTTC } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { EnhancedCard } from '@/components/common/EnhancedCard';
import { formatLabel } from '@/utils/format';

export const Section7_ExternalMarkets = () => {
  const { data: atcData, isLoading: atcLoading, error: atcError } = useATCTTC({ forecast_type: 'short_term', limit: 50 });

  // ATC/TTC Tracker
  const atcTracker = useMemo(() => {
    if (!atcData || atcData.length === 0) return [];
    
    const latestTimestamp = atcData[0]?.timestamp;
    const latest = atcData.filter(d => d.timestamp === latestTimestamp);
    
    return latest.slice(0, 8).map(d => {
      const atc = d.atc_mw ?? 0;
      const ttc = d.ttc_mw ?? 0;
      
      // Utilization = (Used Capacity / Total Capacity) * 100
      // Used Capacity = TTC - ATC (what's being used vs what's available)
      // If TTC is 0 or invalid, can't calculate
      let utilization = 0;
      if (ttc > 0 && atc >= 0) {
        const used = ttc - atc;
        utilization = (used / ttc) * 100;
        // Clamp to 0-100% range
        utilization = Math.max(0, Math.min(100, utilization));
      }
      
      return {
        interface: d.interface_name,
        atc,
        ttc,
        utilization,
        direction: d.direction || null,
      };
    });
  }, [atcData]);

  return (
    <div className="space-y-6">
      <EnhancedCard>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">External Market & Inter-ISO Flows</h2>
        
        {/* ATC/TTC Tracker */}
        <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">ATC/TTC Availability</h3>
            {atcLoading ? (
              <LoadingSkeleton type="table" lines={5} />
            ) : atcError ? (
              <ErrorMessage 
                message={atcError instanceof Error ? atcError.message : 'Error loading ATC/TTC data. Please check API connection.'}
                onRetry={() => window.location.reload()}
              />
            ) : !atcData || atcData.length === 0 ? (
              <EmptyState 
                title="No ATC/TTC Data"
                message="No ATC/TTC data available. This data is updated hourly (30 minutes before the hour)."
                className="py-8"
              />
            ) : atcTracker.length === 0 ? (
              <EmptyState 
                title="No Recent ATC/TTC Data"
                message={`No ATC/TTC data found for the latest timestamp. Total records: ${atcData.length}`}
                className="py-8"
              />
            ) : (
              <div className="space-y-3">
                {atcTracker.map((atc) => {
                  const used = atc.ttc - atc.atc;
                  return (
                    <div key={atc.interface} className="bg-slate-700/50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{formatLabel(atc.interface)}</span>
                        <div className="flex items-center gap-2">
                          {atc.direction && (
                            <span className={`text-xs font-semibold px-2 py-1 rounded ${
                              atc.direction.toLowerCase() === 'import' 
                                ? 'bg-blue-500/20 text-blue-400' 
                                : atc.direction.toLowerCase() === 'export'
                                ? 'bg-orange-500/20 text-orange-400'
                                : 'bg-slate-500/20 text-slate-400'
                            }`}>
                              {atc.direction.toUpperCase()}
                            </span>
                          )}
                          <span className="text-xs text-slate-400">
                            {atc.ttc > 0 ? `${atc.utilization.toFixed(0)}% used` : 'N/A'}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-slate-400">ATC:</span>
                        <span className="font-semibold">{atc.atc.toLocaleString()} MW</span>
                        <span className="text-slate-400 ml-4">TTC:</span>
                        <span className="font-semibold">{atc.ttc.toLocaleString()} MW</span>
                      </div>
                      {atc.ttc > 0 && (
                        <>
                          <div className="text-xs text-slate-500 mt-1">
                            Used: {used.toLocaleString()} MW | Available: {atc.atc.toLocaleString()} MW
                          </div>
                          <div 
                            className="w-full h-2 bg-slate-600 rounded-full mt-2"
                            role="progressbar"
                            aria-valuenow={atc.utilization}
                            aria-valuemin={0}
                            aria-valuemax={100}
                            aria-label={`${formatLabel(atc.interface)} utilization: ${atc.utilization.toFixed(1)}%`}
                          >
                            <div
                              className={`h-full rounded-full ${
                                atc.utilization > 85 ? 'bg-red-500' : 
                                atc.utilization > 70 ? 'bg-yellow-500' : 
                                'bg-blue-500'
                              }`}
                              style={{ width: `${Math.min(atc.utilization, 100)}%` }}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
        </div>
      </EnhancedCard>
    </div>
  );
};

