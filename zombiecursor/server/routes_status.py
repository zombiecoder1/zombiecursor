"""
Status routes for the ZombieCursor server.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import psutil
import platform
from datetime import datetime
from core.config import settings
from core.logging_config import log
from core.llm import LocalLLM


router = APIRouter()


@router.get("/server")
async def get_server_status():
    """Get server status information."""
    try:
        # System information
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.architecture(),
            "hostname": platform.node(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
        
        # Resource usage
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resource_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
        
        # Process information
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
            "cpu_percent": process.cpu_percent(),
            "memory_info": process.memory_info()._asdict(),
            "memory_percent": process.memory_percent(),
            "num_threads": process.num_threads
        }
        
        return {
            "server": {
                "name": "ZombieCursor Local AI",
                "version": "1.0.0",
                "tagline": "যেখানে কোড ও কথা বলে",
                "uptime": datetime.now().isoformat(),
                "debug": settings.debug
            },
            "system": system_info,
            "resources": resource_info,
            "process": process_info,
            "configuration": {
                "host": settings.host,
                "port": settings.port,
                "llm_host": settings.llm_host,
                "llm_model": settings.llm_model,
                "project_root": settings.project_root,
                "max_context_files": settings.max_context_files,
                "enable_streaming": settings.enable_streaming,
                "enable_memory": settings.enable_memory
            }
        }
        
    except Exception as e:
        log.error(f"Error getting server status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm")
async def get_llm_status():
    """Get LLM status information."""
    try:
        llm = LocalLLM()
        
        # Health check
        is_healthy = await llm.health_check()
        
        # List available models
        models = await llm.list_models()
        
        # Configuration
        config = {
            "host": settings.llm_host,
            "model": settings.llm_model,
            "timeout": settings.llm_timeout,
            "max_tokens": settings.llm_max_tokens,
            "temperature": settings.llm_temperature,
            "use_ollama": settings.ollama_host is not None
        }
        
        # If using Ollama, include Ollama-specific config
        if settings.ollama_host:
            config.update({
                "ollama_host": settings.ollama_host,
                "ollama_model": settings.ollama_model
            })
        
        return {
            "healthy": is_healthy,
            "models": models,
            "configuration": config,
            "current_model": settings.llm_model,
            "model_count": len(models)
        }
        
    except Exception as e:
        log.error(f"Error getting LLM status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agents_status():
    """Get status of all agents."""
    try:
        from agents.coder.agent import CoderAgent
        
        agents_status = {}
        
        # Check coder agent
        try:
            coder_agent = CoderAgent()
            coder_health = await coder_agent.health_check()
            coder_capabilities = await coder_agent.get_capabilities()
            
            agents_status["coder"] = {
                "healthy": coder_health.get("healthy", False),
                "capabilities": coder_capabilities,
                "health_details": coder_health
            }
        except Exception as e:
            agents_status["coder"] = {
                "healthy": False,
                "error": str(e)
            }
        
        return {
            "agents": agents_status,
            "total_agents": len(agents_status),
            "healthy_agents": sum(1 for agent in agents_status.values() if agent.get("healthy", False))
        }
        
    except Exception as e:
        log.error(f"Error getting agents status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_tools_status():
    """Get status of all tools."""
    try:
        from tools.fs_tool import FilesystemTool
        from tools.python_tool import PythonTool
        from tools.search_tool import SearchTool
        from tools.git_tool import GitTool
        from tools.system_tool import SystemTool
        
        tools_status = {}
        
        # Check each tool
        tools = {
            "filesystem": FilesystemTool(),
            "python": PythonTool(),
            "search": SearchTool(),
            "git": GitTool(),
            "system": SystemTool()
        }
        
        for name, tool in tools.items():
            try:
                # Basic tool health check
                description = tool.description()
                parameters = tool.parameters()
                
                tools_status[name] = {
                    "healthy": True,
                    "description": description,
                    "parameters": parameters
                }
            except Exception as e:
                tools_status[name] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return {
            "tools": tools_status,
            "total_tools": len(tools_status),
            "healthy_tools": sum(1 for tool in tools_status.values() if tool.get("healthy", False))
        }
        
    except Exception as e:
        log.error(f"Error getting tools status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def get_memory_status():
    """Get memory system status."""
    try:
        from core.memory import memory_store
        
        if not settings.enable_memory:
            return {
                "enabled": False,
                "message": "Memory system is disabled"
            }
        
        # Get memory statistics
        stats = await memory_store.get_stats()
        
        return {
            "enabled": True,
            "statistics": stats,
            "configuration": {
                "vector_store_path": settings.vector_store_path,
                "embedding_model": settings.embedding_model
            }
        }
        
    except Exception as e:
        log.error(f"Error getting memory status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project")
async def get_project_status():
    """Get project context status."""
    try:
        from pathlib import Path
        from core.utils import get_project_languages, is_git_repository
        
        project_path = Path(settings.project_root).resolve()
        
        # Basic project info
        project_info = {
            "path": str(project_path),
            "exists": project_path.exists(),
            "is_directory": project_path.is_dir() if project_path.exists() else False
        }
        
        if project_info["exists"] and project_info["is_directory"]:
            # Get language statistics
            languages = get_project_languages(project_path)
            
            # Check if it's a git repository
            is_git = is_git_repository(project_path)
            
            project_info.update({
                "languages": languages,
                "language_count": len(languages),
                "is_git_repository": is_git,
                "total_files": sum(languages.values()) if languages else 0
            })
        
        return {
            "project": project_info,
            "configuration": {
                "max_context_files": settings.max_context_files,
                "max_context_size": settings.max_context_size
            }
        }
        
    except Exception as e:
        log.error(f"Error getting project status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Comprehensive health check."""
    try:
        health_status = {
            "overall": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check server
        try:
            server_status = await get_server_status()
            health_status["checks"]["server"] = {
                "status": "healthy",
                "details": server_status
            }
        except Exception as e:
            health_status["checks"]["server"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "unhealthy"
        
        # Check LLM
        try:
            llm_status = await get_llm_status()
            health_status["checks"]["llm"] = {
                "status": "healthy" if llm_status["healthy"] else "unhealthy",
                "details": llm_status
            }
            if not llm_status["healthy"]:
                health_status["overall"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["llm"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "unhealthy"
        
        # Check agents
        try:
            agents_status = await get_agents_status()
            all_healthy = all(agent.get("healthy", False) for agent in agents_status["agents"].values())
            health_status["checks"]["agents"] = {
                "status": "healthy" if all_healthy else "unhealthy",
                "details": agents_status
            }
            if not all_healthy:
                health_status["overall"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["agents"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "unhealthy"
        
        # Check tools
        try:
            tools_status = await get_tools_status()
            all_healthy = all(tool.get("healthy", False) for tool in tools_status["tools"].values())
            health_status["checks"]["tools"] = {
                "status": "healthy" if all_healthy else "unhealthy",
                "details": tools_status
            }
            if not all_healthy:
                health_status["overall"] = "degraded"
        except Exception as e:
            health_status["checks"]["tools"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        log.error(f"Error in comprehensive health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def is_git_repository(path: Path) -> bool:
    """Check if a path is a git repository."""
    return (path / '.git').exists()