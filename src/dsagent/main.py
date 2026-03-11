"""DSAgent Ralph - Main FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dsagent.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="2.0.0",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "2.0.0"}
    
    @app.get("/ready")
    async def readiness_check():
        return {"status": "ready"}
    
    return app


app = create_app()


@app.get("/")
async def root():
    return {
        "name": "DSAgent Ralph",
        "version": "2.0.0",
        "docs": "/docs"
    }
