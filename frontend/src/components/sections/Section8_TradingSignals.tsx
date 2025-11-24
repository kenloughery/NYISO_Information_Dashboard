/**
 * Section 8: Trading Signals & Portfolio Monitor
 * Components:
 * 1. Trade Signal Alert Feed
 * 2. Spread Trade Monitor
 * 3. Historical Pattern Matcher
 * 4. Risk Dashboard
 */

import { useMemo } from 'react';
import { useTradingSignals } from '@/hooks/useRealTimeData';
import { useRTDASpreads, usePriceVolatility } from '@/hooks/useHistoricalData';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { EnhancedCard } from '@/components/common/EnhancedCard';
import { useDashboardStore } from '@/store/dashboardStore';
import { formatLabel } from '@/utils/format';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

export const Section8_TradingSignals = () => {
  const { data: signalsData } = useTradingSignals({ limit: 50 });
  const { data: spreadsData } = useRTDASpreads({ limit: 100 });
  const { data: volatilityData } = usePriceVolatility({ limit: 24 });
  const portfolioPositions = useDashboardStore((state) => state.portfolioPositions);

  // Trade Signal Alert Feed
  const sortedSignals = useMemo(() => {
    if (!signalsData) return [];
    
    const severityOrder = { critical: 3, warning: 2, info: 1 };
    return [...signalsData].sort((a, b) => {
      const aSev = severityOrder[a.severity] || 0;
      const bSev = severityOrder[b.severity] || 0;
      return bSev - aSev;
    }).slice(0, 20);
  }, [signalsData]);

  // Spread Trade Monitor
  const spreadTrades = useMemo(() => {
    if (!spreadsData) return [];
    
    return spreadsData
      .filter(s => Math.abs(s.spread) > 15)
      .slice(0, 10)
      .map(s => ({
        zone: s.zone_name,
        spread: s.spread,
        rtPrice: s.rt_lbmp,
        daPrice: s.da_lbmp,
        timestamp: s.timestamp,
      }));
  }, [spreadsData]);

  // Risk Metrics
  const riskMetrics = useMemo(() => {
    if (!volatilityData || volatilityData.length === 0) return null;
    
    const volatilities = volatilityData.map(d => d.volatility);
    const avgVolatility = volatilities.reduce((a, b) => a + b, 0) / volatilities.length;
    const maxVolatility = Math.max(...volatilities);
    
    return {
      avgVolatility,
      maxVolatility,
      riskLevel: maxVolatility > 20 ? 'high' : maxVolatility > 10 ? 'medium' : 'low',
    };
  }, [volatilityData]);

  // Market Regime Indicator
  const marketRegime = useMemo(() => {
    if (!volatilityData || volatilityData.length === 0) return 'normal';
    
    const avgVolatility = volatilityData.reduce((sum, d) => sum + d.volatility, 0) / volatilityData.length;
    
    if (avgVolatility > 20) return 'high_volatility';
    if (avgVolatility > 10) return 'moderate_volatility';
    return 'normal';
  }, [volatilityData]);

  const regimeColors = {
    normal: 'bg-green-500/20 text-green-400 border-green-500/50',
    moderate_volatility: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    high_volatility: 'bg-red-500/20 text-red-400 border-red-500/50',
  };

  const severityColors = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/50',
    warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    info: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
  };

  return (
    <div className="space-y-6">
      <EnhancedCard>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-4">Trading Signals & Portfolio Monitor</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 1. Trade Signal Alert Feed */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Trade Signal Alert Feed</h3>
            <div className="h-96 overflow-y-auto space-y-2" role="log" aria-label="Trade signal alert feed" aria-live="polite">
              {sortedSignals.length > 0 ? (
                sortedSignals.map((signal, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border ${severityColors[signal.severity]}`}
                    role="alert"
                    aria-label={`${signal.severity} signal: ${signal.signal_type} - ${signal.message}`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className="text-xs font-semibold uppercase">{signal.signal_type}</span>
                      <span className="text-xs text-slate-400">
                        {new Date(signal.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-sm mb-1">{signal.message}</div>
                    {signal.zone_name && (
                      <div className="text-xs text-slate-400">Zone: {signal.zone_name}</div>
                    )}
                    {signal.value !== undefined && signal.threshold !== undefined && (
                      <div className="text-xs mt-1">
                        Value: {signal.value.toFixed(2)} | Threshold: {signal.threshold.toFixed(2)}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <EmptyState 
                  title="No Signals Available"
                  message="No trading signals are currently available."
                  className="py-8"
                />
              )}
            </div>
          </div>

          {/* 2. Spread Trade Monitor */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Spread Trade Monitor</h3>
            <div className="h-96 overflow-y-auto" role="list" aria-label="Spread trade monitor">
              {spreadTrades.length > 0 ? (
                <div className="space-y-2">
                  {spreadTrades.map((trade, idx) => (
                    <div key={idx} className="bg-slate-700/30 rounded-lg p-3 border border-slate-700/50 hover:bg-slate-700/50 transition-colors" role="listitem">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-slate-200">{formatLabel(trade.zone)}</span>
                        <span className={`text-lg font-bold flex items-center gap-1 ${
                          trade.spread > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {trade.spread > 0 ? (
                            <TrendingUp className="w-4 h-4" />
                          ) : (
                            <TrendingDown className="w-4 h-4" />
                          )}
                          ${trade.spread > 0 ? '+' : ''}{trade.spread.toFixed(2)}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-slate-400">RT:</span>
                          <span className="ml-1 font-semibold text-slate-200">${trade.rtPrice.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-slate-400">DA:</span>
                          <span className="ml-1 font-semibold text-slate-200">${trade.daPrice.toFixed(2)}</span>
                        </div>
                      </div>
                      {Math.abs(trade.spread) > 15 && (
                        <div className="text-xs text-yellow-400 mt-2">
                          ⚠️ High spread opportunity
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState 
                  title="No Significant Spreads"
                  message="No significant spreads detected at this time."
                  className="py-8"
                />
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 3. Historical Pattern Matcher */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Pattern Analysis</h3>
            <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-700/50">
              <div className="text-sm text-slate-400 mb-4">
                Historical pattern matching will be available once sufficient data is collected.
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Data Points</span>
                  <span className="font-semibold">{volatilityData?.length || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Analysis Period</span>
                  <span className="font-semibold">24 hours</span>
                </div>
              </div>
            </div>
          </div>

          {/* 4. Risk Dashboard */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Risk Dashboard</h3>
            {riskMetrics ? (
              <div className="bg-slate-700/50 rounded-lg p-4 space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-400">Avg Volatility</span>
                    <span className="font-semibold">{riskMetrics.avgVolatility.toFixed(2)}%</span>
                  </div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-400">Max Volatility</span>
                    <span className="font-semibold">{riskMetrics.maxVolatility.toFixed(2)}%</span>
                  </div>
                  <div className="pt-3 border-t border-slate-600">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Risk Level</span>
                      <span className={`font-bold text-lg ${
                        riskMetrics.riskLevel === 'high'
                          ? 'text-red-400'
                          : riskMetrics.riskLevel === 'medium'
                          ? 'text-yellow-400'
                          : 'text-green-400'
                      }`}>
                        {riskMetrics.riskLevel.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-2">Portfolio Positions</div>
                  <div className="text-lg font-bold">{portfolioPositions.length}</div>
                </div>
              </div>
            ) : (
              <LoadingSkeleton type="card" lines={4} />
            )}
          </div>

          {/* 5. Market Regime Indicator */}
          <div>
            <h3 className="text-base sm:text-lg font-medium mb-3">Market Regime Indicator</h3>
            <div className={`p-4 rounded-lg border ${regimeColors[marketRegime]} shadow-lg`}>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Current Regime</span>
                <span className="font-bold text-lg capitalize">
                  {formatLabel(marketRegime)}
                </span>
              </div>
              <div className="text-xs text-slate-500 mt-2">
                Based on 24-hour volatility analysis
              </div>
            </div>
          </div>
        </div>
      </EnhancedCard>
    </div>
  );
};

