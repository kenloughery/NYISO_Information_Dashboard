# Interregional Data Panel - Requirements Analysis & Implementation Plan

**Date**: 2025-11-14  
**Feature**: NYISO Real-Time Dashboard - Interregional Data Panel  
**Status**: Analysis Complete - Backend Enhancement Required

---

## 1. Requirements Summary

### 1.1 Feature Description
Recreate the **Interregional Data** panel from the NYISO Real-Time Dashboard, which displays real-time power flows between NYISO and four external regions:
- **PJM** (Pennsylvania-New Jersey-Maryland Interconnection)
- **New England** (ISO-NE)
- **Ontario** (IESO - Ontario Hydro)
- **Hydro Quebec** (HQ)

### 1.2 Data Source Requirements

| Requirement | Specification |
|------------|---------------|
| **Dataset** | External Interface Limits and Flows (5-minute) |
| **Endpoint** | `http://mis.nyiso.com/public/csv/ExternalLimitsFlows/currentExternalLimitsFlows.csv` |
| **Update Frequency** | Every 5 minutes |
| **File Format** | CSV with headers |
| **Key Columns** | `Interface Name`, `Flow (MWH)`, `Positive Limit (MWH)`, `Negative Limit (MWH)` |

### 1.3 Interface Filtering Requirements

The dashboard must filter and display only these four interfaces:

| Dashboard Label | CSV Interface Name Filter | Notes |
|----------------|---------------------------|-------|
| **PJM** | Contains `SCH - PJM - NY` | Primary scheduled interface |
| **New England** | Contains `SCH - NE - NY` | Primary scheduled interface |
| **Ontario** | Contains `SCH - OH - NY` | "OH" = Ontario Hydro (IESO) |
| **Hydro Quebec** | Contains `SCH - HQ - NY` | Primary scheduled interface |

**Fallback Logic**: If "SCH" (Scheduled) rows are unavailable, fallback to `ACTUAL` rows if present.

### 1.4 Data Transformations Required

#### A. Sign Convention
- **Positive (+) Flow** = **Import** (Flow INTO NYISO Control Area)
- **Negative (-) Flow** = **Export** (Flow OUT of NYISO Control Area)

#### B. Unit Handling
- Column header says `Flow (MWH)` but represents **MW** in 5-minute context
- **No conversion needed** - use value directly as MW
- Store/display as `flow_mw` for clarity

#### C. Utilization Percentage (Optional but Recommended)
Calculate utilization percentage for visual "thermometer" style indicators:

- **If Import (positive flow):**
  ```
  Utilization % = (Flow MW / Positive Limit) * 100
  ```

- **If Export (negative flow):**
  ```
  Utilization % = (abs(Flow MW) / abs(Negative Limit)) * 100
  ```

---

## 2. Current Backend State Analysis

### 2.1 ✅ What We Already Have

#### A. Data Source Configuration
- **Report Code**: P-32 (Interface Limits & Flows)
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Current URL Pattern**: `{YYYYMMDD}ExternalLimitsFlows.csv` (date-based)
- **Update Frequency**: 5-minute intervals (scheduled)
- **Database Table**: `interface_flows`
- **API Endpoint**: `/api/interface-flows`

#### B. Database Schema
```sql
interface_flows:
  - timestamp (DateTime, indexed)
  - interface_id (FK to interfaces table)
  - point_id (Integer)
  - flow_mwh (Float)  -- Note: stored as MWH but represents MW
  - positive_limit_mwh (Float)
  - negative_limit_mwh (Float)
```

#### C. Data Parsing
- ✅ CSV parser implemented (`_transform_interface_flows()`)
- ✅ Extracts all required columns
- ✅ Stores interface names in `interfaces` reference table
- ✅ Upsert logic with unique constraint on (timestamp, interface_id)

#### D. API Endpoint
- ✅ `/api/interface-flows` exists
- ✅ Supports filtering by:
  - Date range (`start_date`, `end_date`)
  - Interface names (`interfaces` parameter - comma-separated)
  - Result limiting

### 2.2 ❌ What's Missing

#### A. Current File Endpoint
**Gap**: We're scraping **date-based** files (`{YYYYMMDD}ExternalLimitsFlows.csv`), but the requirement needs the **current** file (`currentExternalLimitsFlows.csv`).

**Impact**: 
- Current system scrapes historical/archived data by date
- Dashboard needs real-time "current" data that updates every 5 minutes
- The "current" file always contains the latest snapshot

**Solution Required**: 
- Add support for scraping the "current" file endpoint
- This may require a separate data source configuration or a special scraping mode

#### B. Interface Filtering
**Gap**: Current system stores **all** interfaces, but dashboard needs only the 4 external interfaces.

**Current State**: 
- All interface flows are stored (internal + external)
- No filtering applied during ingestion

**Solution Required**: 
- Filter during parsing OR filter at API level
- Recommended: Filter at API level to preserve all data for other use cases

#### C. Utilization Percentage
**Gap**: Utilization percentage calculation is not implemented.

**Current State**: 
- Raw flow and limit values are stored
- No calculated utilization field

**Solution Required**: 
- Add calculated field in API response (not stored in DB)
- Calculate on-the-fly based on flow direction and limits

#### D. Specialized Endpoint
**Gap**: Current `/api/interface-flows` endpoint is generic and requires client-side filtering.

**Solution Required**: 
- Create new endpoint: `/api/interregional-flows` or enhance existing endpoint
- Pre-filter for the 4 external interfaces
- Include utilization percentage in response
- Optimize for dashboard consumption

---

## 3. Backend vs Requirements Comparison

| Requirement | Current State | Gap | Priority |
|------------|---------------|-----|----------|
| **Data Source** | ✅ P-32 configured | ⚠️ Date-based vs current file | **HIGH** |
| **Update Frequency** | ✅ 5-minute scheduled | ✅ Matches | - |
| **Data Schema** | ✅ All columns present | ✅ Matches | - |
| **Interface Filtering** | ❌ Stores all interfaces | ⚠️ Need 4 specific ones | **MEDIUM** |
| **Sign Convention** | ✅ Data preserved | ✅ Matches | - |
| **Unit Handling** | ⚠️ Stored as `flow_mwh` | ⚠️ Should clarify as MW | **LOW** |
| **Utilization %** | ❌ Not calculated | ⚠️ Need calculation | **MEDIUM** |
| **API Endpoint** | ✅ Generic endpoint exists | ⚠️ Need specialized endpoint | **MEDIUM** |

---

## 4. Implementation Options

### Option A: Enhance Existing System (Recommended)

**Approach**: Add support for "current" file scraping while maintaining date-based scraping.

**Changes Required**:

1. **Add "Current" File Support**
   - Add new data source configuration entry for P-32-CURRENT
   - OR: Add special scraping mode that uses `currentExternalLimitsFlows.csv`
   - URL: `http://mis.nyiso.com/public/csv/ExternalLimitsFlows/currentExternalLimitsFlows.csv`
   - Update frequency: Every 5 minutes (same as existing)

2. **Create Specialized API Endpoint**
   - New endpoint: `GET /api/interregional-flows`
   - Pre-filters for 4 external interfaces:
     - `SCH - PJM - NY`
     - `SCH - NE - NY`
     - `SCH - OH - NY`
     - `SCH - HQ - NY`
   - Includes utilization percentage calculation
   - Returns latest data by default (or accepts timestamp parameter)

3. **Response Model Enhancement**
   ```typescript
   {
     timestamp: datetime,
     interface_name: string,  // e.g., "SCH - PJM - NY"
     region: string,           // "PJM", "ISO-NE", "IESO", "HQ"
     flow_mw: float,           // Clarified as MW (not MWH)
     direction: "import" | "export",
     positive_limit_mw: float,
     negative_limit_mw: float,
     utilization_percent: float  // Calculated
   }
   ```

**Pros**:
- Maintains backward compatibility
- Preserves all historical data
- Clear separation of concerns
- Easy to test and maintain

**Cons**:
- Requires code changes
- Two data sources for same logical dataset

### Option B: Modify Existing Scraper

**Approach**: Modify P-32 scraper to also scrape the "current" file.

**Changes Required**:
- Update scraper to check both date-based and current file
- Store with special timestamp or flag to indicate "current" data
- More complex logic in scraper

**Pros**:
- Single data source
- Automatic updates

**Cons**:
- Mixes historical and current data concepts
- More complex scraper logic
- Harder to maintain

### Option C: Frontend-Only Filtering

**Approach**: Use existing `/api/interface-flows` endpoint and filter on frontend.

**Changes Required**:
- Frontend filters for 4 interfaces
- Frontend calculates utilization percentage
- No backend changes

**Pros**:
- No backend changes needed
- Fast to implement

**Cons**:
- Less efficient (transfers all interface data)
- Frontend does business logic
- No specialized endpoint for dashboard
- Still need to handle "current" file issue

---

## 5. Recommended Implementation Plan

### Phase 1: Backend Enhancements (Required Before Frontend)

#### Step 1.1: Add "Current" File Data Source
- **File**: `config/url_config.py` or `URL_Instructions.txt`
- **Action**: Add new entry for P-32-CURRENT with `currentExternalLimitsFlows.csv` URL
- **Alternative**: Modify scraper to support "current" file mode for P-32
- **Estimate**: 2-4 hours

#### Step 1.2: Create Specialized API Endpoint
- **File**: `api/main.py`
- **Action**: Add `GET /api/interregional-flows` endpoint
- **Features**:
  - Pre-filters for 4 external interfaces
  - Calculates utilization percentage
  - Returns latest data by default
  - Optional timestamp parameter for historical queries
- **Estimate**: 4-6 hours

#### Step 1.3: Add Response Model
- **File**: `api/main.py`
- **Action**: Create `InterregionalFlowResponse` Pydantic model
- **Fields**: timestamp, region, interface_name, flow_mw, direction, limits, utilization_percent
- **Estimate**: 1-2 hours

#### Step 1.4: Testing
- **Action**: Test endpoint with real data
- **Verify**: 
  - Correct interface filtering
  - Utilization calculation accuracy
  - Sign convention (import/export)
  - Latest data retrieval
- **Estimate**: 2-3 hours

**Total Backend Estimate**: 9-15 hours

### Phase 2: Frontend Implementation (After Backend Complete)

#### Step 2.1: API Integration
- **File**: `frontend/src/services/api.ts`
- **Action**: Add function to fetch interregional flows
- **Estimate**: 1-2 hours

#### Step 2.2: Component Development
- **File**: `frontend/src/components/sections/SectionX_InterregionalData.tsx` (or similar)
- **Action**: Create dashboard panel component
- **Features**:
  - Display 4 regions with flow arrows
  - Show flow direction (import/export)
  - Display utilization percentage
  - Auto-refresh every 5 minutes
- **Estimate**: 8-12 hours

#### Step 2.3: Visualization
- **Action**: Implement arrow indicators with direction
- **Features**:
  - Color coding (green=import, red=export, or similar)
  - Utilization "thermometer" style fill
  - Flow values and limits display
- **Estimate**: 4-6 hours

**Total Frontend Estimate**: 13-20 hours

---

## 6. Decision Matrix: Can We Go to Frontend?

### ✅ YES - If We Implement Phase 1 First

**Prerequisites**:
1. ✅ Backend endpoint `/api/interregional-flows` created
2. ✅ Endpoint returns filtered data for 4 external interfaces
3. ✅ Utilization percentage calculated
4. ✅ "Current" file data available (or latest timestamp data)

**Frontend Can Then**:
- Call specialized endpoint
- Display data immediately
- Focus on visualization and UX

### ❌ NO - If We Skip Backend Enhancements

**Issues**:
1. ❌ No way to get "current" file data (only date-based historical)
2. ❌ Frontend must filter all interfaces (inefficient)
3. ❌ Frontend must calculate utilization (business logic in wrong layer)
4. ❌ No optimized endpoint for dashboard use case

**Result**: Frontend will be harder to build, less performant, and violate separation of concerns.

---

## 7. Recommended Next Steps

### Immediate Actions (Before Frontend)

1. **✅ Analysis Complete** (This document)

2. **Backend Development**:
   - [ ] Add "current" file support to scraper OR create P-32-CURRENT data source
   - [ ] Create `/api/interregional-flows` endpoint
   - [ ] Implement interface filtering (4 external interfaces)
   - [ ] Add utilization percentage calculation
   - [ ] Create response model with all required fields
   - [ ] Write unit tests for endpoint
   - [ ] Test with real NYISO data

3. **Documentation**:
   - [ ] Update API documentation
   - [ ] Document endpoint usage for frontend team
   - [ ] Create example response payload

### After Backend Complete

4. **Frontend Development**:
   - [ ] Integrate API endpoint
   - [ ] Build dashboard panel component
   - [ ] Implement visualization (arrows, utilization indicators)
   - [ ] Add auto-refresh functionality
   - [ ] Test with real data

---

## 8. Technical Considerations

### 8.1 Data Freshness
- **Current File**: Always contains latest 5-minute snapshot
- **Date-Based Files**: May have delay in availability
- **Recommendation**: Use "current" file for real-time dashboard, date-based for historical analysis

### 8.2 Interface Name Matching
- **Exact Match**: Use `contains` or `startswith` for interface name matching
- **Case Sensitivity**: Interface names may vary in case - normalize to uppercase
- **Fallback Logic**: Implement fallback to `ACTUAL` if `SCH` not available

### 8.3 Utilization Calculation Edge Cases
- **Zero Limits**: Handle division by zero
- **Null Values**: Handle missing limit data
- **Negative Limits**: Ensure absolute value used for export calculations

### 8.4 Performance
- **Database Query**: Index on `interface_name` for fast filtering
- **Caching**: Consider caching latest interregional data (5-minute TTL)
- **Response Size**: Pre-filtering reduces payload size significantly

---

## 9. Conclusion

### Summary
- ✅ **Data Available**: We have P-32 data source implemented
- ⚠️ **Gap Identified**: Need "current" file support and specialized endpoint
- ✅ **Architecture Sound**: Existing system can be extended cleanly

### Recommendation
**Implement Phase 1 (Backend Enhancements) before proceeding to frontend development.**

This ensures:
1. Clean separation of concerns
2. Optimized API for dashboard use case
3. Proper business logic in backend
4. Better performance and maintainability

### Estimated Timeline
- **Backend**: 9-15 hours (1-2 days)
- **Frontend**: 13-20 hours (2-3 days)
- **Total**: 22-35 hours (3-5 days)

---

## 10. Appendix: Example API Response

```json
{
  "timestamp": "2025-11-14T18:30:00Z",
  "flows": [
    {
      "interface_name": "SCH - PJM - NY",
      "region": "PJM",
      "flow_mw": 1250.5,
      "direction": "import",
      "positive_limit_mw": 2000.0,
      "negative_limit_mw": -1500.0,
      "utilization_percent": 62.5
    },
    {
      "interface_name": "SCH - NE - NY",
      "region": "ISO-NE",
      "flow_mw": -450.2,
      "direction": "export",
      "positive_limit_mw": 1800.0,
      "negative_limit_mw": -1200.0,
      "utilization_percent": 37.5
    },
    {
      "interface_name": "SCH - OH - NY",
      "region": "IESO",
      "flow_mw": 800.0,
      "direction": "import",
      "positive_limit_mw": 1000.0,
      "negative_limit_mw": -800.0,
      "utilization_percent": 80.0
    },
    {
      "interface_name": "SCH - HQ - NY",
      "region": "HQ",
      "flow_mw": -200.5,
      "direction": "export",
      "positive_limit_mw": 1500.0,
      "negative_limit_mw": -1000.0,
      "utilization_percent": 20.05
    }
  ]
}
```

---

**Document Status**: ✅ Complete - Ready for Implementation Planning

