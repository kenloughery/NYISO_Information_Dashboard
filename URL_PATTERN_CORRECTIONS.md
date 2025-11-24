# URL Pattern Corrections

**Date**: 2025-11-14  
**Status**: ✅ **All URL patterns corrected**

## Summary

Found and corrected 5 incorrect URL patterns by inspecting NYISO index pages. These were not date-limited issues, but incorrect URL patterns.

## Corrections Made

### 1. P-5 - Day-Ahead Ancillary Services ✅

**Incorrect Pattern:**
- URL: `csv/damlbmp/{YYYYMMDD}damlbmp_ancillaryservices.csv`
- Dataset: `damlbmp`
- Filename: `damlbmp_ancillaryservices`

**Correct Pattern:**
- URL: `csv/damasp/{YYYYMMDD}damasp.csv`
- Dataset: `damasp`
- Filename: `damasp`

**Verification:**
- ✅ `http://mis.nyiso.com/public/csv/damasp/20251113damasp.csv` - Works

### 2. P-8A - Long-Term ATC/TTC ✅

**Incorrect Pattern:**
- URL: `csv/ltatc/{YYYYMMDD}ltatc.csv`
- Dataset: `ltatc`
- Filename: `ltatc`

**Correct Pattern:**
- URL: `csv/preSchedAtcTtc/{YYYYMMDD}presched_atc_ttc.csv`
- Dataset: `preSchedAtcTtc`
- Filename: `presched_atc_ttc`

**Verification:**
- ✅ `http://mis.nyiso.com/public/csv/preSchedAtcTtc/20251113presched_atc_ttc.csv` - Works

### 3. P-54B - Real-Time Actual Outages ✅

**Incorrect Pattern:**
- URL: `csv/rtactualoutages/{YYYYMMDD}rtactualoutages.csv`
- Dataset: `rtactualoutages`
- Filename: `rtactualoutages`

**Correct Pattern:**
- URL: `csv/realtimelineoutages/{YYYYMMDD}RTLineOutages.csv`
- Dataset: `realtimelineoutages`
- Filename: `RTLineOutages`

**Verification:**
- ✅ `http://mis.nyiso.com/public/csv/realtimelineoutages/20251113RTLineOutages.csv` - Works

### 4. P-54C - Day-Ahead Scheduled Outages ✅

**Incorrect Pattern:**
- URL: `csv/dascheduledoutages/{YYYYMMDD}dascheduledoutages.csv`
- Dataset: `dascheduledoutages`
- Filename: `dascheduledoutages`

**Correct Pattern:**
- URL: `csv/outSched/{YYYYMMDD}outSched.csv`
- Dataset: `outSched`
- Filename: `outSched`

**Verification:**
- ✅ `http://mis.nyiso.com/public/csv/outSched/20251113outSched.csv` - Works

### 5. P-14B - Outage Schedules CSV ✅

**Incorrect Pattern:**
- URL: `csv/outageschedules/{YYYYMMDD}outageschedules.csv` (date-based)
- Dataset: `outageschedules`
- Filename: `outageschedules`

**Correct Pattern:**
- URL: `csv/os/outage-schedule.csv` (single file, no date pattern)
- Dataset: `os`
- Filename: `outage-schedule`

**Note**: This is a single file that gets updated, not a date-based pattern. The scraper will need special handling for this.

**Verification:**
- ✅ `http://mis.nyiso.com/public/csv/os/outage-schedule.csv` - Works

## Impact

All 5 sources can now be scraped successfully with the corrected URL patterns. These were not date-limited issues - the URL patterns were simply incorrect.

## Next Steps

1. ✅ URL patterns updated in `URL_Instructions.txt`
2. ⚠️ P-14B requires special handling (single file, not date-based)
3. ✅ Re-scrape these sources to collect data

