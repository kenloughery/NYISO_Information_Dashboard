/**
 * Main App component
 * New York Power Market (NYISO) Dashboard
 */

import { useMemo, useEffect } from 'react';
import { Layout } from '@/components/common/Layout';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { WeatherCarousel } from '@/components/common/WeatherCarousel';
import { useZones, useStats } from '@/hooks/useHistoricalData';
import { useRealTimeLBMP } from '@/hooks/useRealTimeData';
import { Section1_RealTimeOverview } from '@/components/sections/Section1_RealTimeOverview';
import { Section2_ZonalPriceDynamics } from '@/components/sections/Section2_ZonalPriceDynamics';
import { Section3_PriceEvolution } from '@/components/sections/Section3_PriceEvolution';
import { Section4_LoadForecast } from '@/components/sections/Section4_LoadForecast';
import { Section5_AncillaryServices } from '@/components/sections/Section5_AncillaryServices';
import { Section6_TransmissionConstraints } from '@/components/sections/Section6_TransmissionConstraints';
import { Section7_ExternalMarkets } from '@/components/sections/Section7_ExternalMarkets';
import { Section10_InterregionalComparison } from '@/components/sections/Section10_InterregionalComparison';
import { Section8_TradingSignals } from '@/components/sections/Section8_TradingSignals';
import { Section9_AdvancedAnalytics } from '@/components/sections/Section9_AdvancedAnalytics';

function App() {
  const { data: zones, isLoading: zonesLoading, error: zonesError } = useZones();
  const { data: stats, isLoading: statsLoading, error: statsError } = useStats();
  const { data: lbmpData } = useRealTimeLBMP();

  // Get latest update timestamp (NYISO operates in Eastern Time)
  // Note: Timestamps from API are naive (no timezone) but represent Eastern Time
  // The timestamp comes as "2025-12-15T15:45:23" which represents 15:45:23 ET
  // We need to display it as-is without timezone conversion
  const lastUpdated = useMemo(() => {
    if (!lbmpData || lbmpData.length === 0) return null;
    const timestamp = lbmpData[0]?.timestamp;
    if (!timestamp) return null;
    
    // Parse timestamp string (format: "2025-12-15T15:45:23" or "2025-12-15T15:45:23.123456")
    let dateStr: string = typeof timestamp === 'string' ? timestamp : String(timestamp);
    
    // Remove microseconds if present
    dateStr = dateStr.split('.')[0];
    
    // Check if it already has timezone info
    const hasTimezone = dateStr.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(dateStr);
    
    if (!hasTimezone) {
      // Timestamp is naive but represents Eastern Time
      // Parse components and format directly as ET (no conversion needed)
      const [datePart, timePart] = dateStr.split('T');
      const [, month] = datePart.split('-').map(Number);
      const timeComponents = (timePart || '00:00:00').split(':').map(Number);
      
      // Create a date object by appending ET timezone offset
      // We need to determine if DST is in effect
      // Simple heuristic: check if the date falls in typical DST period (March-November)
      const monthNum = month;
      const isLikelyDST = monthNum >= 3 && monthNum <= 11;
      const offset = isLikelyDST ? '-04:00' : '-05:00';
      
      // Create date with ET offset - this ensures JavaScript parses it as ET
      const dateWithOffset = new Date(`${dateStr}${offset}`);
      
      // Format using ET timezone - this will display the correct time
      return dateWithOffset.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'America/New_York',
        timeZoneName: 'short',
      });
    } else {
      // Has timezone, parse normally
      const date = new Date(dateStr);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'America/New_York',
        timeZoneName: 'short',
      });
    }
  }, [lbmpData]);

  // Scroll to top on initial page load
  useEffect(() => {
    // Always scroll to top on mount, regardless of hash
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    // Also set scroll position directly
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, []);

  return (
    <Layout>
      <div className="p-6">
        <div className="mb-6" id="overview">
          <div className="text-slate-400 text-base leading-relaxed w-full">
            <p>
              This dashboard provides a centralized view of real-time data from the New York Independent System Operator (NYISO), the entity managing New York's electric grid and wholesale markets. Designed for comprehensive market visibility, the platform tracks live electricity prices across all eleven pricing zones, monitors interregional power flows, and analyzes load forecasts against actual demand. It also offers deep insights into ancillary services and fuel mix composition. By automatically aggregating NYISO's public data feeds, this tool enables users to assess grid reliability, identify price differentials, and make data-driven decisions regarding trading and system operations.
            </p>
          </div>
        </div>

        {/* Section 1: Real-Time Market Overview (Top Banner) */}
        <div className="mb-10">
          <Section1_RealTimeOverview lastUpdated={lastUpdated} />
        </div>

        {/* Section 2: Zonal Price Dynamics */}
        <div id="zonal" className="scroll-mt-6 mb-10">
          <Section2_ZonalPriceDynamics />
        </div>

        {/* Section 3: Multi-Timeframe Price Evolution */}
        <div id="price-evolution" className="scroll-mt-6 mb-10">
          <Section3_PriceEvolution />
        </div>

        {/* Section 9: Market Context */}
        <div id="analytics" className="scroll-mt-6 mb-10">
          <Section9_AdvancedAnalytics />
        </div>

        {/* Weather Carousel */}
        <div className="mb-10">
          <WeatherCarousel />
        </div>

        {/* Section 4: Load & Forecast Analytics */}
        <div id="load" className="scroll-mt-6 mb-10">
          <Section4_LoadForecast />
        </div>

        {/* Section 5: Ancillary Services Market */}
        <div id="ancillary" className="scroll-mt-6 mb-10">
          <Section5_AncillaryServices />
        </div>

        {/* Section 6: Transmission & Constraint Monitoring */}
        <div id="transmission" className="scroll-mt-6 mb-10">
          <Section6_TransmissionConstraints />
        </div>

        {/* Section 10: Interregional Price & Volume Comparison */}
        <div id="interregional" className="scroll-mt-6 mb-10">
          <Section10_InterregionalComparison />
        </div>

        {/* Section 7: External Market & Inter-ISO Flows */}
        <div id="external" className="scroll-mt-6 mb-10">
          <Section7_ExternalMarkets />
        </div>

        {/* Section 8: Trading Signals & Portfolio Monitor */}
        <div id="signals" className="scroll-mt-6 mb-10">
          <Section8_TradingSignals />
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 className="text-sm text-slate-400 mb-1">Zones</h3>
            {zonesLoading ? (
              <LoadingSpinner size="sm" />
            ) : zonesError ? (
              <p className="text-red-400 text-sm">Error loading zones</p>
            ) : (
              <p className="text-2xl font-bold">{zones?.length || 0}</p>
            )}
          </div>

          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 className="text-sm text-slate-400 mb-1">Total Records</h3>
            {statsLoading ? (
              <LoadingSpinner size="sm" />
            ) : statsError ? (
              <p className="text-red-400 text-sm">Error loading stats</p>
            ) : (
              <p className="text-2xl font-bold">
                {stats?.total_records?.toLocaleString() || '0'}
              </p>
            )}
      </div>

          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 className="text-sm text-slate-400 mb-1">Data Range</h3>
            {statsLoading ? (
              <LoadingSpinner size="sm" />
            ) : statsError ? (
              <p className="text-red-400 text-sm">Error loading stats</p>
            ) : (
              <p className="text-sm">
                {stats?.date_range?.start
                  ? new Date(stats.date_range.start).toLocaleDateString()
                  : 'N/A'}{' '}
                -{' '}
                {stats?.date_range?.end
                  ? new Date(stats.date_range.end).toLocaleDateString()
                  : 'N/A'}
              </p>
            )}
          </div>
        </div>

        {/* API Connection Status */}
        <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
          <h3 className="text-lg font-semibold mb-2">API Status</h3>
          {zonesError || statsError ? (
            <ErrorMessage
              message="Unable to connect to API. Please ensure the backend server is running on http://localhost:8000"
              onRetry={() => window.location.reload()}
            />
          ) : (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-slate-300">Connected to NYISO API</span>
            </div>
          )}
        </div>

      </div>
    </Layout>
  );
}

export default App;
