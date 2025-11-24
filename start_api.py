"""
Start the API server.
Usage: python start_api.py
"""
import uvicorn
import os

if __name__ == "__main__":
    # Railway sets PORT environment variable
    port = int(os.getenv('PORT', 8000))
    # Disable reload in production (Railway)
    reload = os.getenv('ENVIRONMENT', 'production').lower() == 'development'
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info"
    )

