"""
Authentication utilities for the ZombieCursor server.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings
from core.logging_config import log


class AuthManager:
    """Manages authentication and authorization."""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.tokens = {}  # In-memory token storage (use Redis in production)
        self.api_keys = {}  # In-memory API key storage
        
    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate a JWT-like token."""
        expiry = datetime.now() + timedelta(seconds=expires_in)
        token_data = f"{user_id}:{expiry.timestamp()}:{secrets.token_hex(16)}"
        token = hashlib.sha256(f"{token_data}:{self.secret_key}".encode()).hexdigest()
        
        self.tokens[token] = {
            "user_id": user_id,
            "expires_at": expiry,
            "created_at": datetime.now()
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a token."""
        if token not in self.tokens:
            return None
        
        token_info = self.tokens[token]
        
        # Check if token has expired
        if datetime.now() > token_info["expires_at"]:
            del self.tokens[token]
            return None
        
        return token_info
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    def generate_api_key(self, name: str, permissions: list = None) -> str:
        """Generate an API key."""
        if permissions is None:
            permissions = ["read", "write"]
        
        api_key = f"zc_{secrets.token_urlsafe(32)}"
        
        self.api_keys[api_key] = {
            "name": name,
            "permissions": permissions,
            "created_at": datetime.now(),
            "last_used": None
        }
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify an API key."""
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key]
        key_info["last_used"] = datetime.now()
        
        return key_info
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens."""
        current_time = datetime.now()
        expired_tokens = [
            token for token, info in self.tokens.items()
            if current_time > info["expires_at"]
        ]
        
        for token in expired_tokens:
            del self.tokens[token]
        
        if expired_tokens:
            log.info(f"Cleaned up {len(expired_tokens)} expired tokens")


# Global auth manager
auth_manager = AuthManager()

# HTTP Bearer for token authentication
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get the current authenticated user."""
    # If no credentials provided, allow anonymous access (for development)
    if not credentials:
        return {
            "user_id": "anonymous",
            "permissions": ["read", "write"]
        }
    
    token = credentials.credentials
    token_info = auth_manager.verify_token(token)
    
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_info


async def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        # For now, all authenticated users have all permissions
        # In a real implementation, check user permissions
        return current_user
    
    return permission_checker


def create_test_token() -> str:
    """Create a test token for development."""
    return auth_manager.generate_token("test_user", expires_in=86400)  # 24 hours


def init_default_auth():
    """Initialize default authentication settings."""
    # Create a default API key for development
    if not auth_manager.api_keys:
        default_key = auth_manager.generate_api_key(
            "default",
            permissions=["read", "write", "admin"]
        )
        log.info(f"Created default API key: {default_key}")
    
    # Create a test token
    test_token = create_test_token()
    log.info(f"Created test token: {test_token}")
    
    return {
        "default_api_key": default_key,
        "test_token": test_token
    }