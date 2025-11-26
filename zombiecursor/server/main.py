"""
Main FastAPI server for ZombieCursor Local AI.
"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from core.config import settings
from core.logging_config import log
from server.routes_agent import router as agent_router
from server.routes_status import router as status_router
from server.ws import router as ws_router
from server.middleware import setup_cors, setup_security_middleware
from server.auth import init_default_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    log.info("Starting ZombieCursor Local AI Server...")
    log.info(f"Server running on {settings.host}:{settings.port}")
    log.info(f"LLM endpoint: {settings.llm_host}")
    log.info(f"Project root: {settings.project_root}")
    
    # Initialize authentication
    auth_info = init_default_auth()
    log.info(f"Authentication initialized - API Key: {auth_info['default_api_key'][:8]}...")
    
    yield
    
    # Shutdown
    log.info("Shutting down ZombieCursor Local AI Server...")


# Create FastAPI app
app = FastAPI(
    title="ZombieCursor Local AI",
    description="যেখানে কোড ও কথা বলে - Local AI-powered coding assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Setup security and CORS middleware
setup_cors(app)
setup_security_middleware(app)

# Include routers
app.include_router(agent_router, prefix="/agent", tags=["agents"])
app.include_router(status_router, prefix="/status", tags=["status"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ZombieCursor Local AI",
        "tagline": "যেখানে কোড ও কথা বলে",
        "version": "1.0.0",
        "endpoints": {
            "agents": "/agent",
            "status": "/status",
            "websocket": "/ws",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": log._core.start_time if hasattr(log._core, 'start_time') else None,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )