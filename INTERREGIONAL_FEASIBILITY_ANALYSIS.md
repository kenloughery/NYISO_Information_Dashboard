# Interregional Data Integration - Feasibility Analysis & Execution Plan

**Date**: 2025-11-21  
**Feature**: Interregional Data Panel  
**Status**: ✅ **FEASIBLE - Ready for Implementation**

---

## Executive Summary

**Feasibility Score: 9.5/10** ✅ **EXCELLENT**

The interregional data feature is **highly feasible** and integrates seamlessly with the existing architecture. All core infrastructure is in place, and only minor enhancements are needed.

### Key Findings:
- ✅ **Current file accessible**: Verified `currentExternalLimitsFlows.csv` exists and has correct structure
- ✅ **Architecture compatible**: All components (scraper, parser, database, API) support this feature
- ✅ **Proven patterns**: Non-date files (P-14B, P-15) already work in production
- ✅ **Zero schema changes**: Database schema is fully compatible
- ⚠️ **Minor gaps**: Need specialized API endpoint and utilization calculation

**Estimated Implementation Time**: 3-6 hours (backend only) - **Simplified** since no aggregation logic needed

---

## 1. Requirements Verification

### 1.1 Data Source Requirements ✅

| Requirement | Status | Details |
|------------|--------|---------|
| **Current File URL** | ✅ **VERIFIED** | `http://mis.nyiso.com/public/csv/ExternalLimitsFlows/currentExternalLimitsFlows.csv` |
| **File Format** | ✅ **VERIFIED** | CSV with headers - matches expected structure |
| **Update Frequency** | ✅ **SUPPORTED** | 5-minute scheduler already configured |
| **Required Columns** | ✅ **PRESENT** | All columns exist: `Timestamp`, `Interface Name`, `Flow (MWH)`, `Positive Limit (MWH)`, `Negative Limit (MWH)` |
| **Target Interfaces** | ✅ **VERIFIED** | All external interfaces found, including multiple PJM nodes |

**Note**: Each region has one or more interface connections:
- **PJM**: 3 interfaces - `SCH - PJM_HTP`, `SCH - PJM_NEPTUNE`, `SCH - PJM_VFT` (each connects to different NYISO nodes)
- **ISO-NE**: 1 interface - `SCH - NE - NY`
- **IESO**: 1 interface - `SCH - OH - NY`
- **HQ**: 1 interface - `SCH - HQ - NY` (plus additional: `SCH - HQ_CEDARS`, `SCH - HQ_IMPORT_EXPORT`)

**Action Required**: Return all interfaces separately (no aggregation) to show individual locational price deltas for each connection point.

### 1.2 Interface Filtering Requirements ✅

**Required Interfaces** (all returned separately):
- ✅ `SCH - NE - NY` (New England) - **FOUND**
- ✅ `SCH - PJM_HTP`, `SCH - PJM_NEPTUNE`, `SCH - PJM_VFT` (PJM) - **FOUND** (3 separate interfaces)
- ✅ `SCH - OH - NY` (Ontario/IESO) - **FOUND**
- ✅ `SCH - HQ - NY` (Hydro Quebec) - **FOUND**
- ✅ Additional HQ interfaces: `SCH - HQ_CEDARS`, `SCH - HQ_IMPORT_EXPORT` (if needed)

**Fallback Logic**: If `SCH` (Scheduled) rows unavailable, fallback to `ACTUAL` rows.

**Current State**: Parser stores all interfaces. Filtering can be done at API level.

### 1.3 Data Transformations ✅

| Transformation | Status | Implementation |
|---------------|--------|----------------|
| **Sign Convention** | ✅ **SUPPORTED** | Data preserved as-is (positive = import, negative = export) |
| **Unit Handling** | ✅ **SUPPORTED** | Stored as `flow_mwh` (represents MW in 5-min context) |
| **Utilization %** | ❌ **MISSING** | Need to add calculation in API endpoint |

---

## 2. Architecture Compatibility Analysis

### 2.1 URL Configuration System ✅ **PERFECT**

**Current State**:
- System uses `DataSourceConfig.build_url(date)` which replaces `{YYYYMMDD}` placeholders
- **Proven Precedent**: P-14B (`outage-schedule.csv`) and P-15 (`gen_maint_report.csv`) are non-date-based files that work perfectly

**How It Works**:
```python
# config/url_config.py
def build_url(self, date: datetime, use_archive: bool = False) -> str:
    date_str = date.strftime('%Y%m%d')
    url = self.direct_csv_url_template.replace('{YYYYMMDD}', date_str)
    return url
```

**For Static URLs**: If URL template doesn't contain `{YYYYMMDD}`, `.replace()` does nothing, leaving the static URL intact.

**Integration Risk**: 🟢 **NONE** - Proven pattern already in use

**Required Change**: Add entry to `URL_Instructions.txt` with static URL (no `{YYYYMMDD}` placeholder)

### 2.2 Scraper Architecture ✅ **PERFECT**

**Current State**:
- Scraper always passes `date` parameter to `build_url()`
- For non-date files, date is still passed but URL template ignores it
- Job tracking uses `target_date` field (can use current date for "current" file)

**Integration Risk**: 🟢 **NONE** - No code changes needed

**Required Change**: None - existing scraper handles this automatically

### 2.3 Database Schema ✅ **PERFECT**

**Current Schema**:
```sql
interface_flows:
  ✅ timestamp (DateTime, indexed) - Can store current file timestamps
  ✅ interface_id (FK to interfaces table) - Stores interface names
  ✅ point_id (Integer) - Point identifier
  ✅ flow_mwh (Float) - Stores flow values (MW, despite name)
  ✅ positive_limit_mwh (Float) - Import limit
  ✅ negative_limit_mwh (Float) - Export limit
  ✅ Unique constraint: (timestamp, interface_id)
```

**Integration Risk**: 🟢 **NONE** - Zero schema changes needed

**Required Change**: None - Schema is already compatible

### 2.4 CSV Parser ✅ **PERFECT**

**Current Implementation**:
```python
def _transform_interface_flows(self, df: pd.DataFrame, timestamp_col: str) -> List[Dict]:
    records = []
    for _, row in df.iterrows():
        records.append({
            'timestamp': row[timestamp_col],
            'interface_name': row.get('Interface Name', ''),
            'point_id': row.get('Point ID'),
            'flow_mwh': row.get('Flow (MWH)'),
            'positive_limit_mwh': row.get('Positive Limit (MWH)'),
            'negative_limit_mwh': row.get('Negative Limit (MWH)'),
        })
    return records
```

**Integration Risk**: 🟢 **NONE** - Parser already handles the exact CSV format needed

**Required Change**: None - Parser is ready

**Note**: Current file has `Timestamp` column (verified), so timestamp extraction will work.

### 2.5 Database Writer ✅ **PERFECT**

**Current State**:
- `upsert_interface_flows()` method exists
- Handles interface reference table creation
- Upsert logic with unique constraint on `(timestamp, interface_id)`
- Transaction management with rollback on errors

**Integration Risk**: 🟢 **NONE** - Writer is ready

**Required Change**: None - Writer already handles interface flows correctly

### 2.6 Scheduler Integration ✅ **EXCELLENT**

**Current State**:
- Scheduler runs every 5 minutes for real-time sources
- P-32 is already scheduled every 5 minutes
- Uses `scraper.scrape_date(datetime.now())` for real-time sources

**Integration Risk**: 🟡 **LOW** - Minor configuration change only

**Required Change**: Add P-32-CURRENT entry to scheduler (or reuse P-32 with updated URL)

### 2.7 API Endpoint ⚠️ **NEEDS ENHANCEMENT**

**Current State**:
- `/api/interface-flows` endpoint exists
- Supports filtering by interface names
- Returns data in compatible format
- Follows established FastAPI patterns

**Gaps**:
- ❌ No pre-filtering for external interfaces (PJM, ISO-NE, IESO, HQ)
- ❌ No utilization percentage calculation
- ❌ No specialized response model for dashboard
- ❌ No region mapping (identify which region each interface belongs to)

**Integration Risk**: 🟢 **NONE** - Standard endpoint addition

**Required Change**: Create new endpoint `/api/interregional-flows` with:
- Pre-filtering for external interfaces (all interfaces matching PJM, ISO-NE, IESO, HQ patterns)
- Return all interfaces separately (no aggregation) to show individual locational price deltas
- Utilization percentage calculation per interface
- Region mapping (identify region for each interface)
- Specialized response model

---

## 3. Compatibility Matrix

| Component | Current State | Integration | Risk | Changes Needed |
|-----------|--------------|-------------|------|---------------|
| **URL Config** | ✅ Handles static URLs | ✅ Perfect | 🟢 None | Add config entry (5 min) |
| **Scraper** | ✅ Works with any URL | ✅ Perfect | 🟢 None | None |
| **Parser** | ✅ Handles interface flows | ✅ Perfect | 🟢 None | None |
| **Database Schema** | ✅ All columns exist | ✅ Perfect | 🟢 None | None |
| **Database Writer** | ✅ Upsert logic ready | ✅ Perfect | 🟢 None | None |
| **Scheduler** | ✅ 5-min scheduling exists | ✅ Excellent | 🟡 Low | Config only |
| **API Endpoint** | ✅ Pattern established | ⚠️ Needs enhancement | 🟢 None | New endpoint (2-4 hrs) |

**Overall Integration Score**: ✅ **9.5/10** (Excellent)

---

## 4. Implementation Strategy

### Recommended Approach: Option C (Hybrid) ✅

**Approach**: Keep P-32 for historical, add P-32-CURRENT for real-time

**Rationale**:
- ✅ Historical data scraping continues unchanged
- ✅ Real-time dashboard gets fresh "current" file
- ✅ Maximum flexibility
- ✅ No breaking changes
- ✅ Clear separation of concerns

**Changes Required**:
1. Add P-32-CURRENT entry to `URL_Instructions.txt`
2. Add metadata to `URL_Lookup.txt`
3. Create `/api/interregional-flows` endpoint
4. Test end-to-end

---

## 5. Execution Plan

### Phase 1: Configuration & Data Source Setup (30 minutes)

#### Step 1.1: Add P-32-CURRENT Data Source
- **File**: `URL_Instructions.txt`
- **Action**: Add new entry:
  ```
  Interface Limits & Flows (Current),P-32-CURRENT,ExternalLimitsFlows,currentExternalLimitsFlows.csv,http://mis.nyiso.com/public/csv/ExternalLimitsFlows/currentExternalLimitsFlows.csv,http://mis.nyiso.com/public/csv/ExternalLimitsFlows/{YYYYMM01}ExternalLimitsFlows_csv.zip,http://mis.nyiso.com/public/csv/ExternalLimitsFlows/currentExternalLimitsFlows.csv,"dataset_name = ""ExternalLimitsFlows"", filename = ""currentExternalLimitsFlows"""
  ```
- **File**: `URL_Lookup.txt`
- **Action**: Add metadata entry
- **Estimate**: 10 minutes

#### Step 1.2: Verify Parser Handles Current File
- **Action**: Test parser with sample "current" file
- **Verify**: 
  - Timestamp extraction works (`Timestamp` column)
  - All columns parse correctly
  - Interface names stored properly
- **Estimate**: 15 minutes

#### Step 1.3: Test Scraper with Current File
- **Action**: Run manual scrape of P-32-CURRENT
- **Verify**: 
  - URL builds correctly (no date replacement)
  - Data downloads successfully
  - Data stores in database
- **Estimate**: 5 minutes

**Phase 1 Total**: 30 minutes

---

### Phase 2: API Endpoint Development (2-4 hours) - **Simplified** (no aggregation logic)

#### Step 2.1: Create Response Model
- **File**: `api/main.py`
- **Action**: Add `InterregionalFlowResponse` Pydantic model
- **Fields**:
  ```python
  class InterregionalFlowResponse(BaseModel):
      timestamp: datetime
      interface_name: str  # Full interface name (e.g., "SCH - PJM_HTP")
      region: str  # "PJM", "ISO-NE", "IESO", "HQ"
      node_name: str  # Specific node/connection (e.g., "HTP", "NEPTUNE", "VFT" for PJM)
      flow_mw: float  # Clarified as MW (not MWH)
      direction: str  # "import" or "export"
      positive_limit_mw: float
      negative_limit_mw: float
      utilization_percent: Optional[float]  # Calculated
  ```
- **Estimate**: 30 minutes

#### Step 2.2: Implement Endpoint
- **File**: `api/main.py`
- **Action**: Add `GET /api/interregional-flows` endpoint
- **Features**:
  - Pre-filter for external interfaces (match patterns for PJM, ISO-NE, IESO, HQ):
    - **PJM**: `SCH - PJM_*` or `ACTUAL - PJM_*` (returns all separately: HTP, NEPTUNE, VFT)
    - **ISO-NE**: `SCH - NE - NY` or `ACTUAL - NE - NY`
    - **IESO**: `SCH - OH - NY` or `ACTUAL - OH - NY`
    - **HQ**: `SCH - HQ*` or `ACTUAL - HQ*` (returns all separately: HQ - NY, HQ_CEDARS, etc.)
  - Return all interfaces separately (no aggregation) to preserve individual locational price deltas
  - Calculate utilization percentage per interface:
    - Import: `(flow_mw / positive_limit_mw) * 100`
    - Export: `(abs(flow_mw) / abs(negative_limit_mw)) * 100`
  - Determine direction: `"import"` if flow > 0, `"export"` if flow < 0
  - Map interface name to region and extract node name:
    - `"SCH - PJM_HTP"` → region: `"PJM"`, node: `"HTP"`
    - `"SCH - NE - NY"` → region: `"ISO-NE"`, node: `"NE - NY"`
    - `"SCH - OH - NY"` → region: `"IESO"`, node: `"OH - NY"`
    - `"SCH - HQ - NY"` → region: `"HQ"`, node: `"HQ - NY"`
  - Return latest data by default (or accept timestamp parameter)
- **Estimate**: 2-3 hours

#### Step 2.3: Add Error Handling
- **Action**: Handle edge cases:
  - Missing interfaces (return empty list or 404)
  - Zero limits (skip utilization calculation)
  - Null values (handle gracefully)
- **Estimate**: 30 minutes

#### Step 2.4: Add Unit Tests
- **File**: Create test file or add to existing test suite
- **Action**: Test endpoint with mock data
- **Verify**:
  - Correct interface filtering
  - Utilization calculation accuracy
  - Sign convention (import/export)
  - Latest data retrieval
- **Estimate**: 1 hour

**Phase 2 Total**: 3-5 hours

---

### Phase 3: Testing & Verification (1-2 hours)

#### Step 3.1: End-to-End Testing
- **Action**: Test complete flow:
  1. Scraper downloads current file
  2. Parser extracts data
  3. Database stores records
  4. API endpoint returns filtered data
  5. Verify utilization calculations
- **Estimate**: 1 hour

#### Step 3.2: Verify Scheduler Integration
- **Action**: Verify scheduler picks up P-32-CURRENT
- **Verify**: 
  - Scheduler runs every 5 minutes
  - Data updates in database
  - API returns fresh data
- **Estimate**: 30 minutes

#### Step 3.3: Verify Interface Filtering
- **Action**: Check that all 4 interfaces are found
- **Verify**: 
  - PJM interface exists (may need to check naming)
  - All interfaces return data
  - Fallback logic works if `SCH` not available
- **Estimate**: 30 minutes

**Phase 3 Total**: 1-2 hours

---

### Phase 4: Documentation (30 minutes)

#### Step 4.1: Update API Documentation
- **File**: `API_ENDPOINTS_REFERENCE.md`
- **Action**: Add `/api/interregional-flows` endpoint documentation
- **Estimate**: 15 minutes

#### Step 4.2: Update Status Documents
- **Files**: `PHASE1_STATUS.md`, `DATA_SOURCES_STATUS.md`
- **Action**: Mark P-32-CURRENT as implemented
- **Estimate**: 15 minutes

**Phase 4 Total**: 30 minutes

---

## 6. Total Implementation Estimate

| Phase | Tasks | Time Estimate |
|-------|-------|---------------|
| **Phase 1** | Configuration & Setup | 30 minutes |
| **Phase 2** | API Endpoint Development | 2-4 hours (simplified - no aggregation) |
| **Phase 3** | Testing & Verification | 1-2 hours |
| **Phase 4** | Documentation | 30 minutes |
| **Total** | | **4-7 hours** |

**Recommended Buffer**: Add 1 hour for unexpected issues

**Total with Buffer**: **5-8 hours** (1 day)

**Note**: Implementation is simplified since we don't need aggregation logic - just filter and return all external interfaces separately.

---

## 7. Questions for Developer/Clarification

### 7.1 Interface Naming Convention

**Question 1**: How should we handle multiple PJM interfaces? ✅ **ANSWERED**
- **Context**: PJM has 3 interfaces: `SCH - PJM_HTP`, `SCH - PJM_NEPTUNE`, `SCH - PJM_VFT`
- **Each interface connects to a different NYISO node, creating different locational price deltas**
- **Decision**: Return all interfaces separately (no aggregation)
- **Rationale**: Each interface represents a different physical connection point with unique price characteristics

**Implementation**:
- Return all 3 PJM interfaces as separate entries in the response
- Each entry includes full interface name, region (`"PJM"`), and node name (`"HTP"`, `"NEPTUNE"`, `"VFT"`)
- Frontend can display all interfaces separately to show individual locational price deltas
- Same approach for other regions with multiple interfaces (e.g., HQ)

**Action**: Filter and return all external interfaces separately (no aggregation logic needed)

---

### 7.2 Fallback Logic Implementation

**Question 2**: How should fallback logic work?
- **Context**: Requirements say "If SCH rows unavailable, fallback to ACTUAL rows"
- **Options**:
  - **Option A**: Prefer `SCH - *` interfaces, only use `ACTUAL - *` if `SCH - *` not found
  - **Option B**: Use whichever is available (SCH or ACTUAL)
  - **Option C**: Always prefer SCH, but include ACTUAL if SCH missing for that region

**Recommendation**: **Option A** - Prefer scheduled, fallback to actual if scheduled not available

---

### 7.3 Utilization Calculation Edge Cases

**Question 3**: How should we handle edge cases in utilization calculation?
- **Zero Limits**: What if `positive_limit_mw` or `negative_limit_mw` is 0?
  - **Recommendation**: Return `None` or `0` for utilization, log warning
- **Null Limits**: What if limits are missing?
  - **Recommendation**: Return `None` for utilization
- **Negative Limits**: What if `negative_limit_mw` is positive (should be negative)?
  - **Recommendation**: Use absolute value for calculation

**Action**: Implement robust error handling for all edge cases

---

### 7.4 Data Freshness

**Question 4**: How should we handle data freshness?
- **Context**: "Current" file updates every 5 minutes
- **Options**:
  - **Option A**: API always returns latest data (default behavior)
  - **Option B**: API accepts `timestamp` parameter for historical queries
  - **Option C**: Both - latest by default, historical if timestamp provided

**Recommendation**: **Option C** - Latest by default, historical if timestamp provided

---

### 7.5 Response Format

**Question 5**: What response format does the frontend expect? ✅ **ANSWERED**
- **Context**: Dashboard needs to display all interfaces separately to show individual locational price deltas
- **Decision**: Return flat list of all external interfaces (one entry per interface)
- **Format**: Each entry includes interface name, region, node name, flow, limits, utilization
- **Rationale**: Each interface connects to a different NYISO node, creating different locational price deltas that traders need to see separately

**Response Format**: 
- Flat list of interfaces (not grouped)
- Latest timestamp by default
- Each interface shown separately (e.g., 3 separate PJM entries for HTP, Neptune, VFT)

**Action**: Implement flat list response with all interfaces separately

---

## 8. Risk Assessment

### 8.1 Low Risks ✅

| Risk | Impact | Probability | Mitigation |
|------|--------|--------------|------------|
| **URL Template Handling** | Low | Very Low | Proven pattern (P-14B, P-15) |
| **Parser Compatibility** | Low | Very Low | Parser already handles format |
| **Database Schema** | Low | Very Low | Schema already compatible |
| **Scheduler Integration** | Low | Low | Standard configuration |

### 8.2 Medium Risks ⚠️

| Risk | Impact | Probability | Mitigation |
|------|--------|--------------|------------|
| **Interface Filtering** | Low | Low | Filter for external interfaces (PJM, ISO-NE, IESO, HQ) and return all separately |
| **Timestamp Format** | Medium | Low | Parser handles various formats, test with actual file |
| **Data Duplication** | Low | Low | Unique constraint prevents duplicates |

### 8.3 Mitigation Strategies

1. **Interface Filtering**: Filter for external interfaces matching PJM, ISO-NE, IESO, HQ patterns and return all separately (no aggregation)
2. **Timestamp**: Test parser with actual current file before deployment
3. **Data Duplication**: Unique constraint on `(timestamp, interface_id)` handles this automatically

---

## 9. Success Criteria

### 9.1 Backend Success Criteria ✅

- [ ] P-32-CURRENT data source configured and working
- [ ] Scraper successfully downloads current file every 5 minutes
- [ ] Parser correctly extracts all 4 interface flows
- [ ] Database stores data with correct timestamps
- [ ] `/api/interregional-flows` endpoint returns filtered data
- [ ] Utilization percentage calculated correctly
- [ ] Direction (import/export) determined correctly
- [ ] All external interfaces (PJM nodes, ISO-NE, IESO, HQ) return data separately
- [ ] API handles edge cases gracefully
- [ ] Unit tests pass
- [ ] End-to-end test successful

### 9.2 Integration Success Criteria ✅

- [ ] No breaking changes to existing endpoints
- [ ] Existing P-32 scraping continues unchanged
- [ ] Scheduler handles both P-32 and P-32-CURRENT
- [ ] Database schema unchanged (backward compatible)
- [ ] API follows established patterns

---

## 10. Conclusion

### Feasibility Assessment

**Overall Score**: ✅ **9.5/10 (Excellent)**

The interregional data feature is **highly feasible** and integrates seamlessly with the existing architecture. All core infrastructure is in place:

1. ✅ **Data Source**: Current file exists and is accessible
2. ✅ **Architecture**: All components support this feature
3. ✅ **Proven Patterns**: Non-date files already work in production
4. ✅ **Zero Schema Changes**: Database is ready
5. ⚠️ **Minor Gaps**: Need specialized API endpoint (standard addition)

### Recommendation

✅ **PROCEED WITH IMPLEMENTATION**

The integration is straightforward and low-risk. The system is well-architected to handle this feature with minimal changes.

### Next Steps

1. **Clarify Questions**: Answer questions in Section 7 (especially PJM interface naming)
2. **Execute Plan**: Follow Phase 1-4 execution plan (5-8 hours)
3. **Test Thoroughly**: Verify all 4 interfaces return data
4. **Document**: Update API documentation

### Estimated Timeline

- **Backend Implementation**: 4-7 hours (1 day) - **Simplified** (no aggregation)
- **Testing & Verification**: 1-2 hours
- **Total**: 5-8 hours (1 day)

**Note**: Implementation is simpler than originally estimated since we're returning all interfaces separately rather than aggregating them.

---

**Document Status**: ✅ Complete - Ready for Implementation

**Last Updated**: 2025-11-21

