"""
WebSocket routes for real-time communication.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import json
import asyncio
from datetime import datetime
from core.interfaces import AgentType
from agents.coder.agent import CoderAgent
from core.logging_config import log


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        self.connection_info[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.now().isoformat(),
            "message_count": 0
        }
        
        log.info(f"WebSocket connection established: {self.connection_info[websocket]['client_id']}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.connection_info:
            client_id = self.connection_info[websocket]["client_id"]
            del self.connection_info[websocket]
            log.info(f"WebSocket connection closed: {client_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
            
            # Update message count
            if websocket in self.connection_info:
                self.connection_info[websocket]["message_count"] += 1
                
        except Exception as e:
            log.error(f"Error sending personal message: {str(e)}")
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                log.error(f"Error broadcasting to client: {str(e)}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about all connections."""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "client_id": info["client_id"],
                    "connected_at": info["connected_at"],
                    "message_count": info["message_count"]
                }
                for info in self.connection_info.values()
            ]
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication."""
    client_id = None
    
    try:
        # Extract client ID from query parameters
        query_params = dict(websocket.query_params)
        client_id = query_params.get("client_id")
        
        # Accept connection
        await manager.connect(websocket, client_id)
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Connected to ZombieCursor Local AI",
            "client_id": manager.connection_info[websocket]["client_id"],
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(welcome_message), websocket)
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                response = await process_message(message, websocket)
                
                if response:
                    await manager.send_personal_message(json.dumps(response), websocket)
                    
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
                
            except Exception as e:
                error_response = {
                    "type": "error",
                    "message": f"Error processing message: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        log.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


async def process_message(message: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Process incoming WebSocket message."""
    message_type = message.get("type")
    
    if message_type == "ping":
        return {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }
    
    elif message_type == "agent_request":
        return await handle_agent_request(message, websocket)
    
    elif message_type == "tool_request":
        return await handle_tool_request(message, websocket)
    
    elif message_type == "status_request":
        return await handle_status_request(message, websocket)
    
    elif message_type == "stream_request":
        return await handle_stream_request(message, websocket)
    
    else:
        return {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.now().isoformat()
        }


async def handle_agent_request(message: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Handle agent execution request."""
    try:
        agent_name = message.get("agent", "coder")
        query = message.get("query")
        context = message.get("context")
        metadata = message.get("metadata")
        
        if not query:
            return {
                "type": "error",
                "message": "Query is required for agent request",
                "timestamp": datetime.now().isoformat()
            }
        
        # Initialize agent
        if agent_name == "coder":
            agent = CoderAgent()
        else:
            return {
                "type": "error",
                "message": f"Unknown agent: {agent_name}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Create agent request
        from core.interfaces import AgentRequest
        agent_request = AgentRequest(
            query=query,
            agent_type=AgentType.CODER,
            context=context,
            stream=False,
            metadata=metadata
        )
        
        # Run agent
        response = await agent.run(agent_request)
        
        return {
            "type": "agent_response",
            "agent": agent_name,
            "query": query,
            "content": response.content,
            "metadata": response.metadata,
            "error": response.error,
            "success": response.error is None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log.error(f"Error handling agent request: {str(e)}")
        return {
            "type": "error",
            "message": f"Agent request failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


async def handle_tool_request(message: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Handle tool execution request."""
    try:
        tool_name = message.get("tool_name")
        operation = message.get("operation")
        params = message.get("params", {})
        
        if not tool_name or not operation:
            return {
                "type": "error",
                "message": "Tool name and operation are required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Initialize agent to access tools
        agent = CoderAgent()
        
        # Execute tool
        result = await agent.execute_tool(tool_name, operation, **params)
        
        return {
            "type": "tool_response",
            "tool_name": tool_name,
            "operation": operation,
            "result": result,
            "success": result.get("success", True) and "error" not in result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log.error(f"Error handling tool request: {str(e)}")
        return {
            "type": "error",
            "message": f"Tool request failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


async def handle_status_request(message: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Handle status request."""
    try:
        status_type = message.get("status_type", "general")
        
        if status_type == "connections":
            return {
                "type": "status_response",
                "status_type": "connections",
                "connections": manager.get_connection_info(),
                "timestamp": datetime.now().isoformat()
            }
        
        elif status_type == "agent":
            agent = CoderAgent()
            health = await agent.health_check()
            capabilities = await agent.get_capabilities()
            
            return {
                "type": "status_response",
                "status_type": "agent",
                "health": health,
                "capabilities": capabilities,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            # General status
            return {
                "type": "status_response",
                "status_type": "general",
                "message": "ZombieCursor Local AI is running",
                "connections": manager.get_connection_info(),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        log.error(f"Error handling status request: {str(e)}")
        return {
            "type": "error",
            "message": f"Status request failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


async def handle_stream_request(message: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Handle streaming request."""
    try:
        agent_name = message.get("agent", "coder")
        query = message.get("query")
        context = message.get("context")
        metadata = message.get("metadata")
        
        if not query:
            return {
                "type": "error",
                "message": "Query is required for stream request",
                "timestamp": datetime.now().isoformat()
            }
        
        # Initialize agent
        if agent_name == "coder":
            agent = CoderAgent()
        else:
            return {
                "type": "error",
                "message": f"Unknown agent: {agent_name}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Create agent request
        from core.interfaces import AgentRequest
        agent_request = AgentRequest(
            query=query,
            agent_type=AgentType.CODER,
            context=context,
            stream=True,
            metadata=metadata
        )
        
        # Send start message
        start_message = {
            "type": "stream_start",
            "agent": agent_name,
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(start_message), websocket)
        
        # Stream response
        async for chunk in agent.run_stream(agent_request):
            chunk_message = {
                "type": "stream_chunk",
                "content": chunk,
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(chunk_message), websocket)
        
        # Send end message
        end_message = {
            "type": "stream_end",
            "agent": agent_name,
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(end_message), websocket)
        
        # Return acknowledgment
        return {
            "type": "stream_acknowledgment",
            "message": "Streaming completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log.error(f"Error handling stream request: {str(e)}")
        error_message = {
            "type": "stream_error",
            "message": f"Stream request failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_message), websocket)
        
        return {
            "type": "error",
            "message": f"Stream request failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@router.get("/connections")
async def get_websocket_connections():
    """Get information about WebSocket connections."""
    return manager.get_connection_info()


@router.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast a message to all connected clients."""
    try:
        message["timestamp"] = datetime.now().isoformat()
        await manager.broadcast(json.dumps(message))
        
        return {
            "message": "Message broadcasted successfully",
            "connections": len(manager.active_connections)
        }
        
    except Exception as e:
        log.error(f"Error broadcasting message: {str(e)}")
        return {"error": str(e)}