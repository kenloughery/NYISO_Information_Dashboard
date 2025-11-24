# Frontend Specification: Interregional Price & Volume Comparison Module

**Date**: 2025-11-14  
**Feature**: Interregional Connection Point Analysis  
**Status**: Specification Ready for Implementation

---

## 1. Executive Summary

### 1.1 Feature Overview

Create a new frontend module that displays **comparative analysis** of import/export volumes and price differentials between NYISO locational prices and external RTO locational prices at each specific connection point (interface/node).

### 1.2 Key Objectives

1. **Volume Comparison**: Display import/export volumes at each connection point
2. **Price Differential Analysis**: Compare NYISO locational price vs external RTO locational price at each interface
3. **Connection Point Granularity**: Show data for each specific interface/node (e.g., PJM HTP, PJM NEPTUNE, PJM VFT separately)
4. **Trading Insights**: Highlight arbitrage opportunities based on price differentials and available capacity

### 1.3 User Value

- **Traders**: Identify arbitrage opportunities between NYISO and external markets
- **Analysts**: Understand locational price differences at each connection point
- **Operators**: Monitor import/export volumes and capacity utilization
- **Risk Managers**: Assess exposure to external market price movements

---

## 2. Current Frontend Architecture Analysis

### 2.1 ✅ Existing Infrastructure

#### A. Component Structure
- **Location**: `frontend/src/components/sections/`
- **Pattern**: Section-based components (Section1 through Section9)
- **Current Section 7**: `Section7_ExternalMarkets.tsx` - Basic external market data
- **Integration Point**: Add new section or enhance Section 7

#### B. Data Fetching Patterns
- **Hooks**: `useRealTimeData.ts` and `useHistoricalData.ts`
- **API Service**: `services/api.ts` with typed methods
- **State Management**: React Query (`@tanstack/react-query`)
- **Refresh Intervals**: 5-minute for real-time data

#### C. Styling & UI
- **Framework**: Tailwind CSS
- **Charts**: Recharts library
- **Visualization**: Custom SVG-based network/flow diagrams (no map libraries)
- **Theme**: Dark mode (slate-800, slate-700 colors)

#### D. Type System
- **Location**: `types/api.ts`
- **Pattern**: TypeScript interfaces matching API responses
- **Current Types**: `ExternalRTOPrice`, `InterfaceFlow`, `RealTimeLBMP`

### 2.2 ⚠️ Gaps for New Module

#### Missing API Integration
- ❌ No hook for `/api/interregional-flows` endpoint
- ❌ No TypeScript type for `InterregionalFlowResponse`
- ❌ No API service method for interregional flows

#### Missing Data Mapping
- ❌ No mapping between interfaces and NYISO zones
- ❌ No logic to match external RTO prices with interfaces
- ❌ No calculation for price differentials at connection points

#### Missing UI Components
- ❌ No component for connection point comparison
- ❌ No visualization for price differentials
- ❌ No volume comparison display

---

## 3. Data Requirements

### 3.1 API Endpoints Needed

#### A. Interregional Flows (NEW - Not Yet Integrated)
**Endpoint**: `GET /api/interregional-flows`

**Response Structure**:
```typescript
interface InterregionalFlow {
  timestamp: string;
  interface_name: string;      // e.g., "SCH - PJM_HTP"
  region: string;               // "PJM", "ISO-NE", "IESO", "HQ"
  node_name: string;            // "HTP", "NEPTUNE", "VFT", "NE - NY", etc.
  flow_mw: number;             // Positive = import, negative = export
  direction: "import" | "export" | "zero";
  positive_limit_mw: number;   // Import capacity
  negative_limit_mw: number;   // Export capacity
  utilization_percent: number | null;
}
```

**Usage**: Get latest data (no date filters) or historical with date range

#### B. External RTO Prices (EXISTING)
**Endpoint**: `GET /api/external-rto-prices`

**Response Structure**:
```typescript
interface ExternalRTOPrice {
  timestamp: string;
  rto_name: string;            // "PJM", "ISO-NE", "IESO"
  rtc_price?: number;          // NYISO RTC price
  cts_price?: number;          // External RTO CTS price
  price_difference?: number;   // rtc_price - cts_price
}
```

**Usage**: Get latest prices by RTO name

#### C. Real-Time LBMP (EXISTING)
**Endpoint**: `GET /api/realtime-lbmp`

**Response Structure**:
```typescript
interface RealTimeLBMP {
  timestamp: string;
  zone_name: string;           // NYISO zone (e.g., "WEST", "CENTRL", "LONGIL")
  lbmp: number;                // Locational price ($/MWh)
  marginal_cost_losses?: number;
  marginal_cost_congestion?: number;
}
```

**Usage**: Get prices for zones connected to interfaces

### 3.2 Data Mapping Requirements

#### Interface-to-Zone Mapping

Each interface connects to a specific NYISO zone. We need to create a mapping:

```typescript
const INTERFACE_ZONE_MAPPING: Record<string, string> = {
  // PJM Interfaces
  'SCH - PJM_HTP': 'CENTRL',        // PJM HTP connects to Central zone
  'SCH - PJM_NEPTUNE': 'LONGIL',    // PJM NEPTUNE connects to Long Island
  'SCH - PJM_VFT': 'CENTRL',        // PJM VFT connects to Central zone
  'SCH - PJM_KEYSTONE': 'WEST',     // PJM KEYSTONE connects to West zone
  
  // ISO-NE Interfaces
  'SCH - NE - NY': 'LONGIL',        // ISO-NE connects to Long Island
  
  // IESO Interfaces
  'SCH - OH - NY': 'WEST',          // IESO (Ontario) connects to West zone
  
  // HQ Interfaces
  'SCH - HQ - NY': 'NORTH',         // Hydro Quebec connects to North zone
  'SCH - HQ_CEDARS': 'NORTH',       // HQ Cedars connects to North zone
};
```

**Note**: This mapping may need to be verified with actual NYISO data or documentation.

#### Region-to-RTO Mapping

Map interface regions to external RTO price data:

```typescript
const REGION_RTO_MAPPING: Record<string, string> = {
  'PJM': 'PJM',
  'ISO-NE': 'ISO-NE',
  'IESO': 'IESO',
  'HQ': 'IESO',  // Note: HQ may not have separate price data
};
```

---

## 4. Component Specification

### 4.1 Component Structure

**File**: `frontend/src/components/sections/Section10_InterregionalComparison.tsx`

**OR** (if replacing Section 7):
**File**: `frontend/src/components/sections/Section7_InterregionalComparison.tsx`

### 4.2 Component Architecture

```
Section10_InterregionalComparison
├── Header & Controls
│   ├── Title & Description
│   ├── Time Range Selector (Latest / 1H / 24H / Custom)
│   ├── Region Filter (All / PJM / ISO-NE / IESO / HQ)
│   └── Sort Options (Price Diff / Volume / Utilization)
│
├── Connection Point Comparison Table
│   ├── Table Header
│   ├── Connection Point Rows (one per interface)
│   │   ├── Interface Info (Region, Node, Zone)
│   │   ├── Volume Metrics (Flow MW, Direction, Utilization)
│   │   ├── Price Comparison (NYISO Price, External Price, Differential)
│   │   ├── Arbitrage Indicator
│   │   └── Actions (View Details, Export)
│   └── Table Footer (Totals, Averages)
│
├── Price Differential Visualization
│   ├── Bar Chart (Price Differential by Connection Point)
│   └── Color Coding (Green = NYISO cheaper, Red = External cheaper)
│
├── Network Flow Diagram (NEW - Replaces Map)
│   ├── NYISO Central Hub (center)
│   ├── Connection Point Nodes (arranged around hub)
│   ├── Flow Lines (connecting nodes to hub)
│   │   ├── Line thickness = flow volume
│   │   ├── Line color = price differential
│   │   └── Arrow direction = import/export
│   └── Interactive Tooltips (hover for details)
│
├── Volume Flow Visualization
│   ├── Flow Direction Indicators (Arrows)
│   ├── Volume Bars (Import vs Export)
│   └── Capacity Utilization Gauge
│
└── Summary Cards
    ├── Total Import Volume
    ├── Total Export Volume
    ├── Average Price Differential
    └── Active Arbitrage Opportunities
```

### 4.3 Data Flow

```
1. Component Mounts
   ↓
2. Fetch Data (Parallel)
   ├── useInterregionalFlows() → Latest flows
   ├── useExternalRTOPrices() → Latest prices by RTO
   └── useRealTimeLBMP() → Latest prices by zone
   ↓
3. Transform & Combine Data
   ├── Map interfaces to zones
   ├── Match external prices to interfaces
   ├── Calculate price differentials
   └── Calculate arbitrage opportunities
   ↓
4. Render Components
   ├── Table with sorted/filtered data
   ├── Charts with transformed data
   └── Summary cards with aggregated metrics
```

---

## 5. Detailed Component Specifications

### 5.1 Connection Point Comparison Table

#### Table Columns

| Column | Description | Data Source | Format |
|--------|-------------|-------------|--------|
| **Connection Point** | Region + Node name | `interregionalFlow.region` + `interregionalFlow.node_name` | "PJM - HTP" |
| **NYISO Zone** | Connected NYISO zone | `INTERFACE_ZONE_MAPPING[interface_name]` | "CENTRL" |
| **Flow (MW)** | Current flow volume | `interregionalFlow.flow_mw` | 1,250 MW |
| **Direction** | Import/Export | `interregionalFlow.direction` | Import/Export badge |
| **Utilization** | Capacity utilization | `interregionalFlow.utilization_percent` | 75% (gauge) |
| **NYISO Price** | Locational price at zone | `realTimeLBMP[zone].lbmp` | $45.23/MWh |
| **External Price** | External RTO CTS price | `externalRTOPrice[rto].cts_price` | $42.10/MWh |
| **Price Diff** | NYISO - External | Calculated | +$3.13/MWh |
| **Arbitrage** | Opportunity indicator | Calculated | 🟢/🟡/🔴 |

#### Row Styling

- **Import Flow** (positive): Blue accent
- **Export Flow** (negative): Orange accent
- **High Utilization** (>85%): Red border
- **Arbitrage Opportunity**: Green highlight

#### Sorting Options

1. **Price Differential** (descending) - Show best arbitrage first
2. **Volume** (descending) - Show highest flows first
3. **Utilization** (descending) - Show constrained interfaces first
4. **Region** (alphabetical) - Group by region

#### Filtering Options

1. **Region**: All / PJM / ISO-NE / IESO / HQ
2. **Direction**: All / Import / Export
3. **Arbitrage**: All / Opportunities Only (>$5/MWh differential)
4. **Utilization**: All / High (>80%) / Medium (50-80%) / Low (<50%)

### 5.2 Price Differential Visualization

#### Bar Chart Component

**Type**: Horizontal Bar Chart (Recharts)

**X-Axis**: Price Differential ($/MWh)
- Negative values: External cheaper (red bars, left)
- Positive values: NYISO cheaper (green bars, right)
- Zero: No differential (gray)

**Y-Axis**: Connection Points (sorted by differential)

**Data Structure**:
```typescript
interface PriceDifferentialData {
  connectionPoint: string;      // "PJM - HTP"
  nyisoPrice: number;
  externalPrice: number;
  differential: number;          // nyisoPrice - externalPrice
  flowMW: number;
  direction: string;
}
```

**Color Coding**:
- **Green** (positive): NYISO price higher → Export opportunity
- **Red** (negative): External price higher → Import opportunity
- **Intensity**: Based on absolute differential magnitude

**Tooltip**: Show NYISO price, External price, differential, and flow direction

### 5.3 Network Flow Diagram (Creative Alternative to Map)

#### Concept: Hub-and-Spoke Network Visualization

**Component**: Custom SVG-based network diagram (no map library needed)

**Layout**: 
- **NYISO Hub**: Large circle in center representing NYISO control area
- **Connection Nodes**: Smaller circles arranged around hub, one per interface
- **Flow Lines**: Curved lines connecting nodes to hub
- **Zone Indicators**: Color-coded sections of hub representing NYISO zones

#### Visual Elements

**NYISO Central Hub**:
- Large circle (200px diameter) in center
- Divided into colored sectors representing zones:
  - WEST: Blue sector
  - CENTRL: Green sector
  - LONGIL: Yellow sector
  - NORTH: Purple sector
- Hub label: "NYISO" in center
- Current system price displayed in center

**Connection Point Nodes**:
- Positioned around hub in circular arrangement
- Size: Proportional to flow volume (min 40px, max 80px)
- Color: Based on region
  - PJM: Orange (`#f97316`)
  - ISO-NE: Blue (`#3b82f6`)
  - IESO: Green (`#10b981`)
  - HQ: Purple (`#a855f7`)
- Border: Thickness indicates utilization (thick = high utilization)
- Badge: Arbitrage indicator (green dot if opportunity exists)

**Flow Lines**:
- Curved SVG paths connecting nodes to hub
- **Thickness**: Proportional to flow volume (2px to 10px)
- **Color Gradient**: 
  - Green → Yellow → Red based on price differential
  - Green: NYISO cheaper (export opportunity)
  - Red: External cheaper (import opportunity)
- **Direction**: Arrow at midpoint
  - Arrow pointing TO hub = Import
  - Arrow pointing FROM hub = Export
- **Animation**: Subtle pulse for active flows

**Interactive Features**:
- **Hover**: Highlight node, line, and connected zone sector
- **Click**: Show detailed tooltip with:
  - Connection point name
  - Flow volume and direction
  - NYISO price vs External price
  - Price differential
  - Utilization percentage
  - Arbitrage opportunity status
- **Filter**: Hide/show regions by clicking legend

#### Implementation Approach

**Option A: Pure SVG (Recommended)**
- Use React + SVG elements
- Calculate node positions using trigonometry
- Draw paths using SVG `<path>` with quadratic curves
- No external libraries needed
- Fully customizable and performant

**Option B: Recharts Custom Component**
- Use Recharts' custom shape components
- More limited but easier to integrate with existing charts

**Option C: D3.js (If needed for complex layouts)**
- Most flexible but adds dependency
- Overkill for this use case

**Recommended**: Option A (Pure SVG)

#### Alternative Visualization Options

**Option 1: Hub-and-Spoke Network (Primary Recommendation)**
- NYISO as central hub
- Connection points as nodes around hub
- Flow lines show relationships
- Best for: Understanding connections and flows

**Option 2: Sankey Diagram**
- Flow from External RTOs → NYISO Zones
- Width of flow = volume
- Color = price differential
- Best for: Showing volume distribution

**Option 3: Radial Flow Chart**
- NYISO in center
- Connection points on concentric circles (by region)
- Flow lines radiate from center
- Best for: Grouping by region

**Option 4: Card-Based Grid with Flow Indicators**
- Each connection point as a card
- Visual flow indicators between cards
- Grouped by region
- Best for: Detailed comparison view

**Recommendation**: Use **Option 1 (Hub-and-Spoke)** as primary, with **Option 4 (Card Grid)** as alternative view toggle

#### SVG Structure

```tsx
<svg viewBox="0 0 800 800" className="w-full h-full">
  {/* NYISO Hub (center) */}
  <g transform="translate(400, 400)">
    {/* Zone sectors (pie chart style) */}
    <path d="M 0,0 L ..." fill="blue" /> {/* WEST zone */}
    <path d="M 0,0 L ..." fill="green" /> {/* CENTRL zone */}
    {/* ... other zones */}
    <circle r="80" fill="slate-800" stroke="slate-600" />
    <text>NYISO</text>
  </g>
  
  {/* Connection Nodes */}
  {connectionPoints.map((point, index) => {
    const angle = (index * 360) / connectionPoints.length;
    const radius = 250;
    const x = 400 + radius * Math.cos(angle * Math.PI / 180);
    const y = 400 + radius * Math.sin(angle * Math.PI / 180);
    
    return (
      <g key={point.id}>
        {/* Flow Line */}
        <path
          d={`M ${x},${y} Q ${(x+400)/2},${(y+400)/2} 400,400`}
          stroke={getLineColor(point.priceDifferential)}
          strokeWidth={point.flowMW / 100}
          fill="none"
          markerEnd={point.direction === 'import' ? 'url(#arrow-import)' : 'url(#arrow-export)'}
        />
        
        {/* Node Circle */}
        <circle
          cx={x}
          cy={y}
          r={getNodeSize(point.flowMW)}
          fill={getRegionColor(point.region)}
          stroke={getUtilizationColor(point.utilization)}
          strokeWidth={point.utilization > 80 ? 4 : 2}
          className="cursor-pointer hover:opacity-80"
          onClick={() => handleNodeClick(point)}
        />
        
        {/* Node Label */}
        <text
          x={x}
          y={y + getNodeSize(point.flowMW) + 15}
          textAnchor="middle"
          className="text-xs fill-slate-300"
        >
          {point.node_name}
        </text>
      </g>
    );
  })}
  
  {/* Arrow Markers */}
  <defs>
    <marker id="arrow-import" ... />
    <marker id="arrow-export" ... />
  </defs>
</svg>
```

#### Node Positioning Algorithm

```typescript
function calculateNodePositions(
  connectionPoints: ConnectionPointData[],
  centerX: number,
  centerY: number,
  radius: number
): Array<{ x: number; y: number; angle: number }> {
  // Group by region for better visual organization
  const grouped = groupBy(connectionPoints, 'region');
  const regions = Object.keys(grouped);
  
  const positions: Array<{ x: number; y: number; angle: number }> = [];
  let currentAngle = 0;
  const angleStep = 360 / connectionPoints.length;
  
  // Arrange nodes in circular pattern
  connectionPoints.forEach((point, index) => {
    const angle = (index * angleStep) * (Math.PI / 180);
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    
    positions.push({ x, y, angle: angle * (180 / Math.PI) });
  });
  
  return positions;
}
```

#### Line Color Calculation

```typescript
function getLineColor(priceDifferential: number, maxDifferential: number): string {
  // Normalize differential to 0-1 range
  const normalized = Math.abs(priceDifferential) / maxDifferential;
  
  if (priceDifferential > 0) {
    // NYISO higher (green gradient for export opportunity)
    const intensity = Math.min(normalized, 1);
    return `rgb(${Math.floor(16 + intensity * 239)}, ${Math.floor(185 + intensity * 70)}, ${Math.floor(129 - intensity * 129)})`;
  } else {
    // External higher (red gradient for import opportunity)
    const intensity = Math.min(normalized, 1);
    return `rgb(${Math.floor(239 - intensity * 223)}, ${Math.floor(68 + intensity * 187)}, ${Math.floor(68 + intensity * 187)})`;
  }
}
```

#### Interactive Tooltip Component

```tsx
interface FlowTooltipProps {
  point: ConnectionPointData;
  x: number;
  y: number;
}

const FlowTooltip = ({ point, x, y }: FlowTooltipProps) => (
  <div
    className="absolute bg-slate-900 border border-slate-700 rounded-lg p-4 shadow-xl z-50"
    style={{ left: x, top: y }}
  >
    <h3 className="font-semibold text-white mb-2">
      {point.region} - {point.node_name}
    </h3>
    <div className="space-y-1 text-sm">
      <div className="flex justify-between">
        <span className="text-slate-400">Flow:</span>
        <span className="text-white">{Math.abs(point.flow_mw).toLocaleString()} MW</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">Direction:</span>
        <span className={point.direction === 'import' ? 'text-blue-400' : 'text-orange-400'}>
          {point.direction.toUpperCase()}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">NYISO Price:</span>
        <span className="text-white">${point.nyisoPrice.toFixed(2)}/MWh</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">External Price:</span>
        <span className="text-white">${point.externalPrice.toFixed(2)}/MWh</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">Differential:</span>
        <span className={point.priceDifferential > 0 ? 'text-green-400' : 'text-red-400'}>
          {point.priceDifferential > 0 ? '+' : ''}${point.priceDifferential.toFixed(2)}/MWh
        </span>
      </div>
      {point.arbitrageOpportunity && (
        <div className="mt-2 pt-2 border-t border-slate-700">
          <span className="text-green-400 font-semibold">🟢 Arbitrage Opportunity</span>
        </div>
      )}
    </div>
  </div>
);
```

#### Advantages Over Map

1. **No Geographic Accuracy Needed**: Focus on relationships, not geography
2. **Better for Trading Data**: Emphasizes price/flow relationships
3. **More Interactive**: Easier to highlight connections
4. **Performance**: Lighter weight than map libraries
5. **Customizable**: Full control over visual design
6. **Accessible**: Can add proper ARIA labels and keyboard navigation
7. **No External Dependencies**: Pure React + SVG, no map library overhead
8. **Mobile Friendly**: Scales better on small screens than maps
9. **Faster Rendering**: Lighter weight, better performance
10. **Trading-Focused**: Emphasizes price/flow relationships over geography

### 5.4 Volume Flow Visualization

#### Flow Direction Indicators

**Component**: Custom SVG arrows or icon-based indicators

**Display**:
- **Import** (positive flow): Arrow pointing INTO NYISO (→)
- **Export** (negative flow): Arrow pointing OUT of NYISO (←)
- **Size**: Proportional to flow volume
- **Color**: Based on utilization (green/yellow/red)

#### Volume Bars

**Type**: Grouped Bar Chart

**Groups**: One per connection point
- **Import Bar**: Positive flow values (blue)
- **Export Bar**: Negative flow values (orange, shown as positive)
- **Capacity Limit**: Dashed line showing limit

**Data Structure**:
```typescript
interface VolumeData {
  connectionPoint: string;
  importMW: number;             // Positive flow or 0
  exportMW: number;             // Absolute of negative flow or 0
  importLimit: number;          // positive_limit_mw
  exportLimit: number;          // Absolute of negative_limit_mw
}
```

### 5.4 Summary Cards

#### Card 1: Total Import Volume
- **Value**: Sum of all positive flows (MW)
- **Trend**: Arrow up/down vs previous period
- **Icon**: Import arrow (→)

#### Card 2: Total Export Volume
- **Value**: Sum of all negative flows (MW, absolute)
- **Trend**: Arrow up/down vs previous period
- **Icon**: Export arrow (←)

#### Card 3: Average Price Differential
- **Value**: Weighted average (by volume) of price differentials
- **Color**: Green if positive, Red if negative
- **Tooltip**: Shows which side is cheaper on average

#### Card 4: Active Arbitrage Opportunities
- **Value**: Count of interfaces with |differential| > $5/MWh
- **Details**: Click to filter table to opportunities only
- **Badge**: Red if > 3 opportunities

---

## 5.5 Additional Creative Visualization Options

### Option A: Connection Point Cards with Flow Indicators (Alternative View)

**Layout**: Grid of cards, one per connection point

**Card Structure**:
```
┌─────────────────────────────────┐
│  PJM - HTP              [🟢]    │  ← Arbitrage indicator
│  ─────────────────────────────  │
│  NYISO Zone: CENTRL              │
│                                  │
│  Flow: 1,250 MW → (Import)       │  ← Direction arrow
│  Utilization: ████████░░ 75%    │  ← Progress bar
│                                  │
│  NYISO: $45.23/MWh               │
│  External: $42.10/MWh            │
│  Diff: +$3.13/MWh                │  ← Color-coded
│                                  │
│  [View Details]                  │
└─────────────────────────────────┘
```

**Visual Flow Indicators**:
- **Between Cards**: Subtle lines connecting related interfaces
- **Color Coding**: Lines colored by price differential
- **Grouping**: Cards grouped by region with visual separators

**Advantages**:
- More detailed information per connection point
- Better for mobile/tablet layouts
- Easier to scan and compare
- Can include more metrics

### Option B: Radial Price Differential Gauge

**Concept**: Circular gauge showing price differentials

**Layout**:
- Center: NYISO hub
- Rings: Connection points at different radii
- Sectors: Price differential shown as colored segments
- Arrows: Flow direction indicators

**Visual**:
```
        [PJM HTP]
           / \
          /   \
    [ISO-NE] [NYISO] [IESO]
          \   /
           \ /
        [HQ]
```

### Option C: Flow Comparison Matrix

**Concept**: Heatmap-style matrix comparing all connection points

**Layout**:
- Rows: Connection points
- Columns: Metrics (Flow, Price Diff, Utilization, etc.)
- Cells: Color-coded values
- Sorting: Click column headers to sort

**Advantages**:
- Compact view of all data
- Easy to spot patterns
- Good for comparing many points

### Option D: Interactive Flow Timeline

**Concept**: Horizontal timeline with connection points as lanes

**Layout**:
- Each connection point = horizontal lane
- Flow shown as colored bars (width = volume, color = price diff)
- Time on X-axis
- Can scroll/zoom through time

**Use Case**: Historical analysis view (toggle from real-time view)

---

## 6. Data Transformation Logic

### 6.1 Combine Interregional Flows with Prices

```typescript
function combineInterregionalData(
  flows: InterregionalFlow[],
  nyisoPrices: RealTimeLBMP[],
  externalPrices: ExternalRTOPrice[]
): ConnectionPointData[] {
  return flows.map(flow => {
    // Get NYISO zone for this interface
    const zone = INTERFACE_ZONE_MAPPING[flow.interface_name] || 'UNKNOWN';
    
    // Get NYISO price for this zone
    const latestTimestamp = nyisoPrices[0]?.timestamp;
    const zonePrice = nyisoPrices.find(
      p => p.timestamp === latestTimestamp && p.zone_name === zone
    )?.lbmp || 0;
    
    // Get external RTO price
    const rtoName = REGION_RTO_MAPPING[flow.region] || flow.region;
    const latestExternalTimestamp = externalPrices[0]?.timestamp;
    const externalPrice = externalPrices.find(
      p => p.timestamp === latestExternalTimestamp && 
           p.rto_name.toUpperCase() === rtoName.toUpperCase()
    )?.cts_price || 
    externalPrices.find(
      p => p.timestamp === latestExternalTimestamp && 
           p.rto_name.toUpperCase() === rtoName.toUpperCase()
    )?.rtc_price || 0;
    
    // Calculate price differential
    const priceDifferential = zonePrice - externalPrice;
    
    // Determine arbitrage opportunity
    const arbitrageOpportunity = Math.abs(priceDifferential) > 5 && 
                                 flow.utilization_percent !== null &&
                                 flow.utilization_percent < 85;
    
    return {
      ...flow,
      zone,
      nyisoPrice: zonePrice,
      externalPrice,
      priceDifferential,
      arbitrageOpportunity,
      // Additional calculated fields
      importMW: flow.direction === 'import' ? flow.flow_mw : 0,
      exportMW: flow.direction === 'export' ? Math.abs(flow.flow_mw) : 0,
    };
  });
}
```

### 6.2 Calculate Summary Metrics

```typescript
function calculateSummaryMetrics(data: ConnectionPointData[]) {
  const totalImport = data
    .filter(d => d.direction === 'import')
    .reduce((sum, d) => sum + d.flow_mw, 0);
  
  const totalExport = data
    .filter(d => d.direction === 'export')
    .reduce((sum, d) => sum + Math.abs(d.flow_mw), 0);
  
  // Weighted average price differential (by volume)
  const totalVolume = data.reduce((sum, d) => sum + Math.abs(d.flow_mw), 0);
  const weightedDifferential = totalVolume > 0
    ? data.reduce((sum, d) => 
        sum + (d.priceDifferential * Math.abs(d.flow_mw)), 0
      ) / totalVolume
    : 0;
  
  const arbitrageCount = data.filter(d => d.arbitrageOpportunity).length;
  
  return {
    totalImport,
    totalExport,
    averagePriceDifferential: weightedDifferential,
    arbitrageOpportunities: arbitrageCount,
  };
}
```

---

## 7. Implementation Checklist

### 7.1 Type Definitions

- [ ] Add `InterregionalFlow` interface to `types/api.ts`
- [ ] Add `ConnectionPointData` interface (extended InterregionalFlow)
- [ ] Add query parameter types for interregional flows

### 7.2 API Integration

- [ ] Add `fetchInterregionalFlows()` to `services/api.ts`
- [ ] Add `useInterregionalFlows()` hook to `hooks/useRealTimeData.ts`
- [ ] Test API integration with real data

### 7.3 Data Mapping

- [ ] Create `INTERFACE_ZONE_MAPPING` constant
- [ ] Create `REGION_RTO_MAPPING` constant
- [ ] Verify mappings with actual NYISO data
- [ ] Add fallback logic for unmapped interfaces

### 7.4 Component Development

- [ ] Create `Section10_InterregionalComparison.tsx` component
- [ ] Implement data fetching and transformation
- [ ] Build connection point comparison table
- [ ] Build price differential chart
- [ ] Build network flow diagram (SVG-based, replaces map)
- [ ] Build volume flow visualization
- [ ] Build summary cards
- [ ] Add filtering and sorting
- [ ] Add loading and error states

### 7.5 Integration

- [ ] Add component to `App.tsx`
- [ ] Add navigation link
- [ ] Test with real data
- [ ] Add responsive design
- [ ] Add accessibility features

### 7.6 Testing

- [ ] Unit tests for data transformation
- [ ] Component tests for rendering
- [ ] Integration tests for data flow
- [ ] Visual regression tests

---

## 8. UI/UX Design Guidelines

### 8.1 Color Scheme

- **Import Flow**: Blue (`#3b82f6`)
- **Export Flow**: Orange (`#f97316`)
- **Positive Differential** (NYISO higher): Green (`#10b981`)
- **Negative Differential** (External higher): Red (`#ef4444`)
- **High Utilization**: Red (`#ef4444`)
- **Medium Utilization**: Yellow (`#f59e0b`)
- **Low Utilization**: Green (`#10b981`)

### 8.2 Typography

- **Table Headers**: `text-sm font-semibold text-slate-300`
- **Table Data**: `text-sm text-slate-200`
- **Card Titles**: `text-lg font-semibold`
- **Card Values**: `text-2xl font-bold`

### 8.3 Spacing & Layout

- **Section Padding**: `p-6`
- **Card Gap**: `gap-4`
- **Table Row Height**: `h-12`
- **Chart Height**: `h-64` (256px)

### 8.4 Responsive Design

- **Mobile**: Single column, stacked cards, scrollable table
- **Tablet**: 2-column grid for cards, full-width table
- **Desktop**: 4-column grid for cards, full-width table with all columns

---

## 9. Performance Considerations

### 9.1 Data Fetching

- **Parallel Queries**: Fetch all three data sources in parallel
- **Caching**: Use React Query caching (5-minute stale time)
- **Refetch Interval**: 5 minutes for real-time data
- **Limit Results**: Use `limit` parameter to avoid large payloads

### 9.2 Rendering Optimization

- **Memoization**: Use `useMemo` for transformed data
- **Virtual Scrolling**: For large tables (>50 rows)
- **Lazy Loading**: Load charts only when visible
- **Debouncing**: For filter/sort changes

### 9.3 Data Transformation

- **Efficient Algorithms**: O(n) complexity for transformations
- **Indexed Lookups**: Use Maps for zone/RTO lookups
- **Batch Calculations**: Calculate all metrics in single pass

---

## 10. Error Handling

### 10.1 Data Fetching Errors

- **API Errors**: Show error message with retry button
- **Missing Data**: Show placeholder with "No data available"
- **Partial Data**: Show available data with warnings for missing fields

### 10.2 Data Validation

- **Missing Mappings**: Log warning, show "Unknown" zone/RTO
- **Invalid Prices**: Skip calculation, show "N/A"
- **Zero Limits**: Handle division by zero in utilization

### 10.3 User Feedback

- **Loading States**: Show spinners during data fetch
- **Empty States**: Show helpful message when no data
- **Error States**: Show error message with actionable steps

---

## 11. Future Enhancements

### 11.1 Historical Analysis

- **Time Series Charts**: Show price differential trends over time
- **Volume Trends**: Show import/export volume history
- **Correlation Analysis**: Compare price movements

### 11.2 Advanced Features

- **Arbitrage Calculator**: Calculate potential profit from trades
- **Alert System**: Notify when arbitrage opportunities appear
- **Export Functionality**: Export data to CSV/Excel
- **Comparison Mode**: Compare current vs historical periods

### 11.3 Integration

- **Trading Signals**: Link to Section 8 (Trading Signals)
- **Constraint Impact**: Show how constraints affect flows
- **Forecast Integration**: Show day-ahead vs real-time comparisons

---

## 12. Acceptance Criteria

### 12.1 Functional Requirements

- ✅ Display all connection points with current flow data
- ✅ Show NYISO and external prices for each connection point
- ✅ Calculate and display price differentials
- ✅ Filter and sort by various criteria
- ✅ Visualize price differentials in chart
- ✅ Visualize connection points in network flow diagram (no map)
- ✅ Visualize volume flows with direction indicators
- ✅ Display summary metrics in cards
- ✅ Auto-refresh every 5 minutes

### 12.2 Non-Functional Requirements

- ✅ Page load time < 2 seconds
- ✅ Smooth interactions (no lag on filter/sort)
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Accessible (WCAG 2.1 AA)
- ✅ Error handling for all edge cases

### 12.3 Data Accuracy

- ✅ Correct zone mapping for all interfaces
- ✅ Accurate price differential calculations
- ✅ Correct volume aggregations
- ✅ Proper arbitrage opportunity detection

---

## 13. Dependencies

### 13.1 New Dependencies

- **None** - all required libraries already in use
- **No map libraries needed** - using pure SVG for network visualization

### 13.2 Existing Dependencies

- `@tanstack/react-query`: Data fetching
- `recharts`: Chart visualization (for bar charts, not network diagram)
- `tailwindcss`: Styling
- `typescript`: Type safety
- **React + SVG**: Network flow diagram (native, no library needed)

---

## 14. Estimated Implementation Time

| Task | Estimate |
|------|----------|
| Type definitions & API integration | 2-3 hours |
| Data mapping & transformation logic | 3-4 hours |
| Connection point table component | 4-6 hours |
| Price differential chart | 2-3 hours |
| Network flow diagram (SVG) | 4-6 hours |
| Volume flow visualization | 3-4 hours |
| Summary cards | 2-3 hours |
| Filtering & sorting | 2-3 hours |
| Integration & testing | 3-4 hours |
| **Total** | **25-34 hours** |

---

## 15. Appendix: Example Data Structure

### 15.1 Combined Connection Point Data

```typescript
interface ConnectionPointData {
  // From InterregionalFlow
  timestamp: string;
  interface_name: string;
  region: string;
  node_name: string;
  flow_mw: number;
  direction: "import" | "export" | "zero";
  positive_limit_mw: number;
  negative_limit_mw: number;
  utilization_percent: number | null;
  
  // Added by transformation
  zone: string;                    // NYISO zone
  nyisoPrice: number;              // NYISO locational price
  externalPrice: number;           // External RTO price
  priceDifferential: number;       // nyisoPrice - externalPrice
  arbitrageOpportunity: boolean;   // |differential| > $5 && utilization < 85%
  importMW: number;                // Positive flow or 0
  exportMW: number;                // Absolute of negative flow or 0
}
```

### 15.2 Example Rendered Data

```
Connection Point    Zone    Flow      Direction  NYISO Price  External Price  Diff      Arbitrage
─────────────────────────────────────────────────────────────────────────────────────────────────
PJM - HTP          CENTRL   1,250 MW  Import     $45.23/MWh   $42.10/MWh     +$3.13    🟢
PJM - NEPTUNE      LONGIL   850 MW    Export     $48.50/MWh   $50.20/MWh     -$1.70    ⚪
PJM - VFT          CENTRL   2,100 MW  Import     $45.23/MWh   $40.00/MWh     +$5.23    🟢
ISO-NE - NE - NY   LONGIL   1,500 MW  Import     $48.50/MWh   $46.80/MWh     +$1.70    ⚪
IESO - OH - NY     WEST     2,200 MW  Import     $42.10/MWh   $38.50/MWh     +$3.60    ⚪
HQ - HQ - NY       NORTH    800 MW    Export     $40.00/MWh   $42.00/MWh     -$2.00    ⚪
```

---

---

## 16. Network Diagram Implementation Details

### 16.1 SVG Coordinate System

**Viewport**: 800x800px viewBox
**Center**: (400, 400)
**Hub Radius**: 80px
**Node Circle Radius**: 250px from center
**Node Size Range**: 20px (min) to 60px (max) based on flow volume

### 16.2 Responsive Behavior

**Desktop (>1024px)**:
- Full network diagram visible
- All nodes and labels shown
- Interactive tooltips on hover

**Tablet (768px-1024px)**:
- Slightly smaller diagram
- Abbreviated labels
- Touch-friendly interactions

**Mobile (<768px)**:
- Switch to card-based layout (Option A from 5.5)
- Network diagram hidden or simplified
- Vertical scrolling for cards

### 16.3 Animation & Transitions

**On Data Update**:
- Smooth transitions for node sizes (flow changes)
- Color transitions for line colors (price changes)
- Fade-in for new connection points

**On Interaction**:
- Node hover: Scale up (1.1x) with shadow
- Line hover: Brighten and thicken
- Zone sector hover: Highlight entire sector

### 16.4 Accessibility Features

- **ARIA Labels**: Each node has descriptive label
- **Keyboard Navigation**: Tab through nodes, Enter to select
- **Screen Reader**: Announce flow direction and prices
- **Color Contrast**: WCAG AA compliant colors
- **Focus Indicators**: Clear focus rings for keyboard users

---

**Document Status**: ✅ Complete - Ready for Implementation  
**Last Updated**: 2025-11-14  
**Leaflet Removed**: ✅ Replaced with SVG-based network flow diagram

