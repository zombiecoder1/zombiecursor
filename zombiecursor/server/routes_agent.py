"""
Agent routes for the ZombieCursor server.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from core.interfaces import AgentType
from agents.coder.agent import CoderAgent
from core.config import settings
from core.logging_config import log


router = APIRouter()


class AgentRequest(BaseModel):
    """Request model for agent operations."""
    query: str
    agent_type: Optional[str] = "coder"
    context: Optional[str] = None
    stream: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Response model for agent operations."""
    agent_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    success: bool = True


class ToolRequest(BaseModel):
    """Request model for tool operations."""
    tool_name: str
    operation: str
    params: Optional[Dict[str, Any]] = None


class ToolResponse(BaseModel):
    """Response model for tool operations."""
    tool_name: str
    operation: str
    result: Dict[str, Any]
    success: bool = True


# Initialize agents
agents = {
    "coder": CoderAgent()
}


@router.post("/{agent_name}/run", response_model=AgentResponse)
async def run_agent(agent_name: str, request: AgentRequest):
    """Run an agent with the given request."""
    try:
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agents[agent_name]
        
        # Convert string agent_type to enum
        try:
            agent_type = AgentType(agent_name)
        except ValueError:
            agent_type = AgentType.CODER  # Default to CODER
        
        # Create agent request
        agent_request = agent.__class__.__bases__[0].__module__.split('.')[0]  # Get the base class
        from core.interfaces import AgentRequest as CoreAgentRequest
        
        core_request = CoreAgentRequest(
            query=request.query,
            agent_type=agent_type,
            context=request.context,
            stream=request.stream,
            metadata=request.metadata
        )
        
        # Run agent
        response = await agent.run(core_request)
        
        return AgentResponse(
            agent_type=agent_name,
            content=response.content,
            metadata=response.metadata,
            error=response.error,
            success=response.error is None
        )
        
    except Exception as e:
        log.error(f"Error running agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_name}/stream")
async def stream_agent(agent_name: str, request: AgentRequest):
    """Stream agent response (placeholder for future implementation)."""
    try:
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # For now, return non-streaming response
        # In a full implementation, this would use Server-Sent Events
        return await run_agent(agent_name, request)
        
    except Exception as e:
        log.error(f"Error streaming agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/info")
async def get_agent_info(agent_name: str):
    """Get information about an agent."""
    try:
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agents[agent_name]
        capabilities = await agent.get_capabilities()
        
        return {
            "agent_name": agent_name,
            "persona": agent.get_persona(),
            "capabilities": capabilities,
            "health": await agent.health_check()
        }
        
    except Exception as e:
        log.error(f"Error getting agent info {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_name}/tools/execute", response_model=ToolResponse)
async def execute_tool(agent_name: str, tool_request: ToolRequest):
    """Execute a tool operation through an agent."""
    try:
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agents[agent_name]
        
        # Execute tool
        result = await agent.execute_tool(
            tool_request.tool_name,
            tool_request.operation,
            **(tool_request.params or {})
        )
        
        return ToolResponse(
            tool_name=tool_request.tool_name,
            operation=tool_request.operation,
            result=result,
            success=result.get("success", True) and "error" not in result
        )
        
    except Exception as e:
        log.error(f"Error executing tool {tool_request.tool_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/tools")
async def list_agent_tools(agent_name: str):
    """List available tools for an agent."""
    try:
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agents[agent_name]
        
        if hasattr(agent, 'tools'):
            tools_info = {}
            for name, tool in agent.tools.items():
                tools_info[name] = {
                    "name": name,
                    "description": tool.description(),
                    "parameters": tool.parameters()
                }
            return {"tools": tools_info}
        else:
            return {"tools": []}
        
    except Exception as e:
        log.error(f"Error listing tools for agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/health")
async def check_agent_health(agent_name: str):
    """Check the health of an agent."""
    try:
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agents[agent_name]
        health = await agent.health_check()
        
        return health
        
    except Exception as e:
        log.error(f"Error checking health for agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_agents():
    """List all available agents."""
    agents_info = {}
    
    for name, agent in agents.items():
        try:
            capabilities = await agent.get_capabilities()
            agents_info[name] = {
                "name": name,
                "description": capabilities.get("description", ""),
                "capabilities": capabilities.get("capabilities", []),
                "tools": capabilities.get("tools", [])
            }
        except Exception as e:
            log.error(f"Error getting info for agent {name}: {str(e)}")
            agents_info[name] = {
                "name": name,
                "error": str(e)
            }
    
    return {"agents": agents_info}


@router.post("/{agent_name}/batch")
async def batch_operations(agent_name: str, requests: List[AgentRequest]):
    """Execute multiple agent requests in batch."""
    try:
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agents[agent_name]
        results = []
        
        for request in requests:
            try:
                # Convert string agent_type to enum
                agent_type = AgentType(agent_name)
                
                # Create agent request
                from core.interfaces import AgentRequest as CoreAgentRequest
                core_request = CoreAgentRequest(
                    query=request.query,
                    agent_type=agent_type,
                    context=request.context,
                    stream=request.stream,
                    metadata=request.metadata
                )
                
                # Run agent
                response = await agent.run(core_request)
                
                results.append(AgentResponse(
                    agent_type=agent_name,
                    content=response.content,
                    metadata=response.metadata,
                    error=response.error,
                    success=response.error is None
                ))
                
            except Exception as e:
                results.append(AgentResponse(
                    agent_type=agent_name,
                    content="",
                    error=str(e),
                    success=False
                ))
        
        return {"results": results, "total": len(results)}
        
    except Exception as e:
        log.error(f"Error in batch operations for agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))