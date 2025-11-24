"""
Production API server startup.
Uses uvicorn with production settings.
"""
import uvicorn
import os

if __name__ == "__main__":
    # Production settings
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "127.0.0.1"),  # Only localhost (Nginx proxies)
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,  # No auto-reload in production
        log_level="info",
        workers=1,  # Single worker for SQLite (use more for PostgreSQL)
        access_log=True,
    )

