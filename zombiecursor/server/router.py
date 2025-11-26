"""
Router configuration for the ZombieCursor server.
"""
from fastapi import APIRouter
from typing import Dict, Any

# Create main router
router = APIRouter()

@router.get("/routes")
async def get_routes():
    """Get all available routes."""
    return {
        "routes": {
            "agent": "/agent",
            "status": "/status", 
            "websocket": "/ws",
            "docs": "/docs",
            "health": "/health"
        }
    }

@router.get("/info")
async def get_info():
    """Get server information."""
    return {
        "name": "ZombieCursor Local AI",
        "version": "1.0.0",
        "tagline": "যেখানে কোড ও কথা বলে",
        "description": "Local AI-powered coding assistant with Cursor AI features",
        "features": [
            "Local LLM integration",
            "Multiple specialized agents",
            "Real-time WebSocket communication",
            "Comprehensive tool integration",
            "Project context awareness",
            "Streaming responses"
        ]
    }