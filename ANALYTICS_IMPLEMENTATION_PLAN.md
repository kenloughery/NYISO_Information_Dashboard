# Site Analytics Implementation Plan

**Date**: 2025-11-21  
**Feature**: Website Visitor Analytics  
**Status**: Planning Phase

---

## Executive Summary

This plan outlines the implementation of visitor analytics for the NYISO Power Trading Command Center dashboard. The solution will track page views, unique visitors, sessions, and user interactions while maintaining privacy compliance.

**Recommended Approach**: Hybrid solution with lightweight backend tracking + optional client-side analytics service integration.

---

## 1. Requirements Analysis

### 1.1 Core Metrics to Track

| Metric | Description | Priority |
|--------|-------------|----------|
| **Page Views** | Total number of page loads | High |
| **Unique Visitors** | Distinct users (by IP/session) | High |
| **Sessions** | User visits (30-min inactivity timeout) | High |
| **Page Paths** | Which pages are viewed | High |
| **Referrers** | Where visitors come from | Medium |
| **User Agents** | Browser/device information | Medium |
| **Geographic Data** | Country/region (from IP) | Medium |
| **Time on Page** | Duration of page views | Low |
| **Bounce Rate** | Single-page visits | Low |
| **Return Visitors** | Repeat visitors | Low |

### 1.2 Privacy & Compliance Requirements

- ✅ **GDPR Compliance**: No personal data collection without consent
- ✅ **Cookie Consent**: Optional cookie-based tracking
- ✅ **IP Anonymization**: Hash or truncate IP addresses
- ✅ **Data Retention**: Configurable retention period (default: 90 days)
- ✅ **Opt-out Support**: Allow users to opt out of tracking

### 1.3 Technical Requirements

- ✅ **Lightweight**: Minimal performance impact
- ✅ **Real-time**: Near real-time analytics updates
- ✅ **Scalable**: Handle high traffic volumes
- ✅ **Privacy-first**: No third-party cookies by default
- ✅ **Self-hosted Option**: Keep data in-house

---

## 2. Implementation Options

### Option A: Backend-Only Tracking (Recommended)

**Approach**: Track all analytics server-side via API middleware

**Pros**:
- ✅ Privacy-first (no client-side tracking)
- ✅ Works even with ad blockers
- ✅ Full control over data
- ✅ No third-party dependencies
- ✅ GDPR-friendly (server-side only)

**Cons**:
- ⚠️ Limited client-side insights (no scroll depth, clicks, etc.)
- ⚠️ Requires backend changes
- ⚠️ May miss some client-side events

**Implementation**:
- FastAPI middleware to log requests
- Store in database table
- API endpoint for analytics dashboard

**Estimated Effort**: 4-6 hours

---

### Option B: Client-Side + Backend Hybrid

**Approach**: Lightweight client-side tracking + backend storage

**Pros**:
- ✅ Rich client-side metrics (scroll, clicks, time on page)
- ✅ Better user experience insights
- ✅ Can track SPA navigation
- ✅ Privacy-controlled (opt-in)

**Cons**:
- ⚠️ Blocked by ad blockers
- ⚠️ Requires frontend changes
- ⚠️ More complex implementation

**Implementation**:
- React hook/component for tracking
- Backend API for receiving events
- Database storage

**Estimated Effort**: 6-8 hours

---

### Option C: Third-Party Service (Google Analytics, Plausible, etc.)

**Approach**: Integrate with external analytics service

**Pros**:
- ✅ Pre-built dashboards
- ✅ Advanced features (funnels, cohorts)
- ✅ Minimal development effort
- ✅ Professional analytics tools

**Cons**:
- ❌ Privacy concerns (third-party data)
- ❌ Cookie consent required
- ❌ External dependency
- ❌ May be blocked by ad blockers
- ❌ Data leaves your control

**Options**:
- **Google Analytics 4**: Free, powerful, privacy concerns
- **Plausible Analytics**: Privacy-focused, paid ($9/month)
- **Umami**: Open-source, self-hosted, free

**Estimated Effort**: 2-4 hours (integration only)

---

### Option D: Self-Hosted Analytics (Umami, Matomo)

**Approach**: Deploy open-source analytics platform

**Pros**:
- ✅ Full data control
- ✅ Privacy-compliant
- ✅ No third-party dependencies
- ✅ Open-source

**Cons**:
- ⚠️ Requires separate deployment
- ⚠️ Additional infrastructure
- ⚠️ More maintenance

**Estimated Effort**: 8-12 hours (including deployment)

---

## 3. Recommended Solution: Option A + Optional Option B

**Hybrid Approach**: Backend-only tracking (primary) + optional client-side events (enhanced)

### Phase 1: Backend-Only Tracking (MVP)
- FastAPI middleware for request logging
- Database schema for analytics
- Basic metrics API endpoint
- Privacy-compliant (no cookies, IP anonymization)

### Phase 2: Enhanced Client-Side Tracking (Optional)
- React tracking hook
- Client-side event tracking (page views, clicks)
- Enhanced metrics (time on page, scroll depth)

---

## 4. Detailed Implementation Plan

### Phase 1: Backend Analytics (MVP)

#### Step 1.1: Database Schema

**File**: `database/schema.py`

```python
class PageView(Base):
    """Page view analytics."""
    __tablename__ = 'page_views'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    session_id = Column(String(64), nullable=False, index=True)  # Hashed session
    ip_hash = Column(String(64), nullable=False, index=True)  # Hashed IP (privacy)
    path = Column(String(500), nullable=False)  # Page path
    referrer = Column(String(500))  # Referrer URL
    user_agent = Column(String(500))  # Browser/device
    country = Column(String(2))  # ISO country code (from IP)
    is_unique = Column(Boolean, default=True)  # First visit in session
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_pageview_timestamp', 'timestamp'),
        Index('idx_pageview_session', 'session_id'),
        Index('idx_pageview_path', 'path'),
    )

class VisitorSession(Base):
    """Visitor session tracking."""
    __tablename__ = 'visitor_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False, unique=True, index=True)
    ip_hash = Column(String(64), nullable=False, index=True)
    user_agent = Column(String(500))
    country = Column(String(2))
    first_visit = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_visit = Column(DateTime, nullable=False, default=datetime.utcnow)
    page_count = Column(Integer, default=1)
    is_returning = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_session_last_visit', 'last_visit'),
    )
```

**Estimated Time**: 30 minutes

---

#### Step 1.2: Analytics Middleware

**File**: `api/middleware/analytics.py`

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import hmac
from datetime import datetime, timedelta
from database.schema import get_session, PageView, VisitorSession

class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to track page views and visitor analytics."""
    
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
        self.session_timeout = timedelta(minutes=30)
    
    def _hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy."""
        return hashlib.sha256(f"{ip}{self.secret_key}".encode()).hexdigest()[:32]
    
    def _get_session_id(self, request: Request) -> str:
        """Get or create session ID from cookie or generate new."""
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate new session ID
            session_id = hashlib.sha256(
                f"{request.client.host}{datetime.utcnow().isoformat()}{self.secret_key}".encode()
            ).hexdigest()[:32]
        return session_id
    
    def _get_country_from_ip(self, ip: str) -> str:
        """Get country code from IP (optional, can use geoip2 library)."""
        # Placeholder - implement with geoip2 or similar
        return None
    
    async def dispatch(self, request: Request, call_next):
        # Skip tracking for API endpoints and static files
        if request.url.path.startswith('/api/') or request.url.path.startswith('/static/'):
            response = await call_next(request)
            return response
        
        # Get client info
        ip = request.client.host if request.client else 'unknown'
        ip_hash = self._hash_ip(ip)
        session_id = self._get_session_id(request)
        user_agent = request.headers.get('user-agent', '')
        referrer = request.headers.get('referer', '')
        path = request.url.path
        
        # Track page view
        db = get_session()
        try:
            # Check if session exists
            session = db.query(VisitorSession).filter(
                VisitorSession.session_id == session_id
            ).first()
            
            now = datetime.utcnow()
            
            if session:
                # Update existing session
                time_since_last = now - session.last_visit
                if time_since_last > self.session_timeout:
                    # New session (timeout)
                    session = None
                else:
                    session.last_visit = now
                    session.page_count += 1
            else:
                # Check if returning visitor (same IP hash, different session)
                existing_visitor = db.query(VisitorSession).filter(
                    VisitorSession.ip_hash == ip_hash
                ).order_by(VisitorSession.last_visit.desc()).first()
                
                is_returning = existing_visitor is not None
                
                # Create new session
                session = VisitorSession(
                    session_id=session_id,
                    ip_hash=ip_hash,
                    user_agent=user_agent,
                    country=self._get_country_from_ip(ip),
                    first_visit=now,
                    last_visit=now,
                    page_count=1,
                    is_returning=is_returning
                )
                db.add(session)
            
            # Create page view
            page_view = PageView(
                session_id=session_id,
                ip_hash=ip_hash,
                path=path,
                referrer=referrer if referrer else None,
                user_agent=user_agent,
                country=session.country if session else None,
                is_unique=(session.page_count == 1) if session else True,
                timestamp=now
            )
            db.add(page_view)
            db.commit()
            
        except Exception as e:
            db.rollback()
            # Log error but don't break request
            print(f"Analytics error: {e}")
        finally:
            db.close()
        
        # Process request
        response = await call_next(request)
        
        # Set session cookie if new
        if not request.cookies.get('session_id'):
            response.set_cookie(
                key='session_id',
                value=session_id,
                max_age=86400 * 30,  # 30 days
                httponly=True,
                samesite='Lax'
            )
        
        return response
```

**Estimated Time**: 2-3 hours

---

#### Step 1.3: Add Middleware to FastAPI App

**File**: `api/main.py`

```python
from api.middleware.analytics import AnalyticsMiddleware
import os

# Add after app creation
app.add_middleware(
    AnalyticsMiddleware,
    secret_key=os.getenv('ANALYTICS_SECRET_KEY', 'your-secret-key-here')
)
```

**Estimated Time**: 15 minutes

---

#### Step 1.4: Analytics API Endpoint

**File**: `api/main.py`

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

class AnalyticsSummaryResponse(BaseModel):
    total_page_views: int
    unique_visitors: int
    sessions: int
    page_views_today: int
    unique_visitors_today: int
    top_pages: List[dict]
    referrers: List[dict]
    countries: List[dict]

@app.get("/api/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """Get analytics summary."""
    db = next(get_db())
    
    try:
        # Default to last N days
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=days)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Total page views
        total_views = db.query(func.count(PageView.id)).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date
        ).scalar()
        
        # Unique visitors (distinct IP hashes)
        unique_visitors = db.query(func.count(func.distinct(PageView.ip_hash))).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date
        ).scalar()
        
        # Sessions
        sessions = db.query(func.count(VisitorSession.id)).filter(
            VisitorSession.first_visit >= start_date,
            VisitorSession.first_visit <= end_date
        ).scalar()
        
        # Today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        views_today = db.query(func.count(PageView.id)).filter(
            PageView.timestamp >= today_start
        ).scalar()
        visitors_today = db.query(func.count(func.distinct(PageView.ip_hash))).filter(
            PageView.timestamp >= today_start
        ).scalar()
        
        # Top pages
        top_pages = db.query(
            PageView.path,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date
        ).group_by(PageView.path).order_by(desc('views')).limit(10).all()
        
        # Top referrers
        top_referrers = db.query(
            PageView.referrer,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date,
            PageView.referrer.isnot(None)
        ).group_by(PageView.referrer).order_by(desc('views')).limit(10).all()
        
        # Countries
        top_countries = db.query(
            PageView.country,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.timestamp >= start_date,
            PageView.timestamp <= end_date,
            PageView.country.isnot(None)
        ).group_by(PageView.country).order_by(desc('views')).limit(10).all()
        
        return {
            "total_page_views": total_views,
            "unique_visitors": unique_visitors,
            "sessions": sessions,
            "page_views_today": views_today,
            "unique_visitors_today": visitors_today,
            "top_pages": [{"path": p[0], "views": p[1]} for p in top_pages],
            "referrers": [{"referrer": r[0], "views": r[1]} for r in top_referrers],
            "countries": [{"country": c[0], "views": c[1]} for c in top_countries]
        }
    finally:
        db.close()
```

**Estimated Time**: 1-2 hours

---

#### Step 1.5: Database Migration

**File**: Create migration script or run manually

```python
# Run in Python shell or migration script
from database.schema import Base, engine
Base.metadata.create_all(engine)
```

**Estimated Time**: 15 minutes

---

### Phase 2: Enhanced Client-Side Tracking (Optional)

#### Step 2.1: React Analytics Hook

**File**: `frontend/src/hooks/useAnalytics.ts`

```typescript
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

export const useAnalytics = () => {
  const location = useLocation();
  const startTime = useRef<number>(Date.now());
  const hasTracked = useRef<boolean>(false);

  useEffect(() => {
    // Track page view
    if (!hasTracked.current) {
      trackPageView(location.pathname);
      hasTracked.current = true;
    }

    // Track time on page when leaving
    return () => {
      const timeOnPage = Math.round((Date.now() - startTime.current) / 1000);
      trackTimeOnPage(location.pathname, timeOnPage);
    };
  }, [location]);

  const trackPageView = async (path: string) => {
    try {
      await fetch('/api/analytics/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'pageview',
          path,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      // Silent fail - analytics shouldn't break the app
      console.error('Analytics error:', error);
    }
  };

  const trackTimeOnPage = async (path: string, seconds: number) => {
    try {
      await fetch('/api/analytics/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'time_on_page',
          path,
          seconds,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Analytics error:', error);
    }
  };

  return { trackPageView, trackTimeOnPage };
};
```

**Estimated Time**: 1-2 hours

---

#### Step 2.2: Client-Side Event Tracking Endpoint

**File**: `api/main.py`

```python
class AnalyticsEvent(BaseModel):
    type: str  # 'pageview', 'click', 'scroll', etc.
    path: str
    data: Optional[dict] = None
    timestamp: datetime

@app.post("/api/analytics/track")
async def track_event(event: AnalyticsEvent):
    """Track client-side analytics event."""
    # Store in database or process
    # Can extend PageView table or create separate events table
    pass
```

**Estimated Time**: 1 hour

---

## 5. Implementation Timeline

### Phase 1: Backend Analytics (MVP)
- **Step 1.1**: Database Schema (30 min)
- **Step 1.2**: Analytics Middleware (2-3 hours)
- **Step 1.3**: Add Middleware to App (15 min)
- **Step 1.4**: Analytics API Endpoint (1-2 hours)
- **Step 1.5**: Database Migration (15 min)
- **Testing**: 1 hour

**Total Phase 1**: 5-7 hours

### Phase 2: Enhanced Client-Side (Optional)
- **Step 2.1**: React Analytics Hook (1-2 hours)
- **Step 2.2**: Event Tracking Endpoint (1 hour)
- **Testing**: 1 hour

**Total Phase 2**: 3-4 hours

**Grand Total**: 8-11 hours (1-1.5 days)

---

## 6. Privacy & Compliance

### 6.1 Data Minimization
- ✅ Hash IP addresses (not stored in plain text)
- ✅ No personal information collected
- ✅ Session IDs are random (not tied to user identity)
- ✅ Optional: Add cookie consent banner

### 6.2 Data Retention
- ✅ Configurable retention period (default: 90 days)
- ✅ Automatic cleanup of old records
- ✅ User can request data deletion

### 6.3 Cookie Consent (Optional)
If implementing client-side tracking, add cookie consent:

```typescript
// Cookie consent component
const CookieConsent = () => {
  const [accepted, setAccepted] = useState(
    localStorage.getItem('analytics_consent') === 'true'
  );

  const acceptCookies = () => {
    localStorage.setItem('analytics_consent', 'true');
    setAccepted(true);
  };

  if (accepted) return null;

  return (
    <div className="cookie-consent-banner">
      <p>We use cookies for analytics. Do you consent?</p>
      <button onClick={acceptCookies}>Accept</button>
      <button onClick={() => setAccepted(true)}>Decline</button>
    </div>
  );
};
```

---

## 7. Testing Plan

### 7.1 Unit Tests
- Test IP hashing function
- Test session creation/update logic
- Test analytics API endpoints

### 7.2 Integration Tests
- Test middleware with various request types
- Test analytics data collection
- Test API response accuracy

### 7.3 Manual Testing
- Verify page views are tracked
- Verify unique visitor counting
- Verify session management
- Test with different browsers/devices

---

## 8. Monitoring & Maintenance

### 8.1 Performance Monitoring
- Monitor middleware performance impact
- Track database query performance
- Set up alerts for high error rates

### 8.2 Data Cleanup
- Implement scheduled job to delete old records
- Monitor database size
- Archive old analytics data if needed

### 8.3 Analytics Dashboard (Future)
- Create admin dashboard for viewing analytics
- Add charts/graphs for visualization
- Export functionality for reports

---

## 9. Alternative: Quick Integration with Umami

If you want a faster solution with a pre-built dashboard:

### Option: Self-Hosted Umami
- Open-source, privacy-focused analytics
- Pre-built dashboard
- Easy React integration
- Self-hosted (full control)

**Steps**:
1. Deploy Umami (Docker or standalone)
2. Add Umami script to React app
3. Configure tracking

**Estimated Time**: 2-3 hours (deployment + integration)

---

## 10. Recommendation

**For MVP**: Implement **Phase 1 (Backend-Only Tracking)**
- Privacy-compliant
- Works with ad blockers
- Full control
- 5-7 hours implementation

**For Enhanced Analytics**: Add **Phase 2 (Client-Side Tracking)**
- Richer metrics
- Better user insights
- 3-4 additional hours

**For Quick Solution**: Consider **Umami** (self-hosted)
- Pre-built dashboard
- Privacy-focused
- 2-3 hours integration

---

## 11. Next Steps

1. **Review and approve plan**
2. **Choose implementation approach** (Backend-only vs Hybrid vs Umami)
3. **Set up environment variables** (ANALYTICS_SECRET_KEY)
4. **Implement Phase 1** (Backend analytics)
5. **Test and verify** analytics collection
6. **Deploy and monitor**

---

**Document Status**: ✅ Ready for Implementation

**Last Updated**: 2025-11-21

