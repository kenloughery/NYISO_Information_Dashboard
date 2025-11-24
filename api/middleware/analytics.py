"""
Analytics middleware for tracking page views and visitor sessions.
Privacy-first: IP addresses are hashed, no personal data collected.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
from datetime import datetime, timedelta
from database.schema import get_session, PageView, VisitorSession
import logging

logger = logging.getLogger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to track page views and visitor analytics."""
    
    def __init__(self, app, secret_key: str = "default-secret-key-change-in-production"):
        super().__init__(app)
        self.secret_key = secret_key
        self.session_timeout = timedelta(minutes=30)
    
    def _hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy."""
        if not ip or ip == 'unknown':
            return hashlib.sha256(b'unknown').hexdigest()[:32]
        return hashlib.sha256(f"{ip}{self.secret_key}".encode()).hexdigest()[:32]
    
    def _get_session_id(self, request: Request) -> str:
        """Get or create session ID from cookie or generate new."""
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate new session ID
            client_host = request.client.host if request.client else 'unknown'
            session_id = hashlib.sha256(
                f"{client_host}{datetime.utcnow().isoformat()}{self.secret_key}".encode()
            ).hexdigest()[:32]
        return session_id
    
    def _get_country_from_ip(self, ip: str) -> str:
        """Get country code from IP (optional, can use geoip2 library).
        
        For now, returns None. Can be enhanced with geoip2 or similar service.
        """
        # Placeholder - implement with geoip2 or similar if needed
        return None
    
    def _should_track(self, path: str) -> bool:
        """Determine if this path should be tracked."""
        # Skip API endpoints, static files, and health checks
        skip_paths = [
            '/api/',
            '/static/',
            '/health',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/favicon.ico',
        ]
        return not any(path.startswith(skip) for skip in skip_paths)
    
    async def dispatch(self, request: Request, call_next):
        # Skip tracking for API endpoints and static files
        if not self._should_track(request.url.path):
            response = await call_next(request)
            return response
        
        # Get client info
        ip = request.client.host if request.client else 'unknown'
        ip_hash = self._hash_ip(ip)
        session_id = self._get_session_id(request)
        user_agent = request.headers.get('user-agent', '')
        referrer = request.headers.get('referer', '')
        path = request.url.path
        
        # Limit referrer length
        if referrer and len(referrer) > 500:
            referrer = referrer[:500]
        
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
                    # Session expired - create new session
                    session = None
                else:
                    session.last_visit = now
                    session.page_count += 1
            
            if not session:
                # Check if returning visitor (same IP hash, different session)
                existing_visitor = db.query(VisitorSession).filter(
                    VisitorSession.ip_hash == ip_hash
                ).order_by(VisitorSession.last_visit.desc()).first()
                
                is_returning = existing_visitor is not None
                
                # Create new session
                session = VisitorSession(
                    session_id=session_id,
                    ip_hash=ip_hash,
                    user_agent=user_agent[:500] if user_agent else None,
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
                path=path[:500],
                referrer=referrer if referrer else None,
                user_agent=user_agent[:500] if user_agent else None,
                country=session.country,
                is_unique=(session.page_count == 1),
                timestamp=now
            )
            db.add(page_view)
            db.commit()
            
        except Exception as e:
            db.rollback()
            # Log error but don't break request
            logger.error(f"Analytics error: {e}", exc_info=True)
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
                samesite='Lax',
                secure=False  # Set to True in production with HTTPS
            )
        
        return response

