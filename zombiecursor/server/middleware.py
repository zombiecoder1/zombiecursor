"""
Enhanced CORS and security middleware for ZombieCursor.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import ipaddress
from typing import List, Optional, Dict, Any
from core.config import settings
from core.logging_config import log


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Use client host
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - self.period
        self.clients = {
            ip: times for ip, times in self.clients.items()
            if any(t > cutoff_time for t in times)
        }
        
        # Check current client
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        # Remove old calls for this client
        self.clients[client_ip] = [
            t for t in self.clients[client_ip] if t > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(self.clients[client_ip]) >= self.calls:
            return True
        
        # Add current call
        self.clients[client_ip].append(current_time)
        return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:;"
        )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        log.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        process_time = time.time() - start_time
        
        # Log response
        log.info(
            f"Response: {response.status_code} - "
            f"{request.method} {request.url} - "
            f"{process_time:.4f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist middleware for enhanced security."""
    
    def __init__(self, app: ASGIApp, allowed_ips: List[str] = None):
        super().__init__(app)
        self.allowed_ips = allowed_ips or []
        self.allowed_networks = []
        
        # Parse IP addresses and networks
        for ip in self.allowed_ips:
            try:
                if '/' in ip:
                    # Network CIDR notation
                    self.allowed_networks.append(ipaddress.ip_network(ip, strict=False))
                else:
                    # Single IP address
                    self.allowed_networks.append(ipaddress.ip_address(ip))
            except ValueError:
                log.warning(f"Invalid IP address/network: {ip}")
    
    async def dispatch(self, request: Request, call_next):
        if not self.allowed_networks:
            # No IP restrictions
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            
            # Check if IP is allowed
            is_allowed = any(
                client_ip_obj in network if isinstance(network, ipaddress.IPv4Network) or isinstance(network, ipaddress.IPv6Network)
                else client_ip_obj == network
                for network in self.allowed_networks
            )
            
            if not is_allowed:
                log.warning(f"Access denied for IP: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )
            
        except ValueError:
            log.warning(f"Invalid client IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


def setup_cors(app: FastAPI) -> None:
    """Setup CORS middleware."""
    # Parse CORS origins
    cors_origins = []
    for origin in settings.cors_origins:
        if origin == "*":
            cors_origins.append("*")
        else:
            cors_origins.append(origin)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"]
    )


def setup_security_middleware(app: FastAPI) -> None:
    """Setup security middleware."""
    # Trusted host middleware
    if settings.host != "0.0.0.0":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[settings.host, "localhost", "127.0.0.1"]
        )
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting (more permissive for development)
    if not settings.debug:
        app.add_middleware(RateLimitMiddleware, calls=100, period=60)


def setup_production_security(app: FastAPI, allowed_ips: List[str] = None) -> None:
    """Setup production security with IP whitelist."""
    if allowed_ips:
        app.add_middleware(IPWhitelistMiddleware, allowed_ips=allowed_ips)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API key authentication middleware."""
    
    def __init__(self, app: ASGIApp, api_keys: List[str] = None):
        super().__init__(app)
        self.api_keys = set(api_keys or [])
    
    async def dispatch(self, request: Request, call_next):
        # Skip API key check for certain endpoints
        skip_paths = ["/", "/health", "/docs", "/openapi.json", "/status/server"]
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Check API key
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            api_key = request.query_params.get("api_key")
        
        if not api_key or api_key not in self.api_keys:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"}
            )
        
        return await call_next(request)


def setup_api_key_auth(app: FastAPI, api_keys: List[str] = None) -> None:
    """Setup API key authentication."""
    if api_keys:
        app.add_middleware(APIKeyMiddleware, api_keys=api_keys)