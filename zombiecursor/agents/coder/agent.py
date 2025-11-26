"""
Main agent implementation for the ZombieCoder Coder Agent.
"""
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from pathlib import Path
from core.interfaces import Agent, AgentRequest, AgentResponse, Message, MessageRole
from core.llm import LocalLLM
from core.context import ProjectContext
from core.memory import memory_store
from core.config import settings
from core.logging_config import log
from tools.fs_tool import FilesystemTool
from tools.python_tool import PythonTool
from tools.search_tool import SearchTool
from tools.git_tool import GitTool
from tools.system_tool import SystemTool


class CoderAgent(Agent):
    """ZombieCoder Coder Agent - A Bengali coding partner for Shawon."""
    
    def __init__(self):
        self.llm = LocalLLM()
        self.persona_path = Path(__file__).parent / "persona.md"
        self.persona = self._load_persona()
        
        # Initialize tools
        self.tools = {
            "filesystem": FilesystemTool(),
            "python": PythonTool(),
            "search": SearchTool(),
            "git": GitTool(),
            "system": SystemTool()
        }
        
        # Tool descriptions for LLM
        self.tool_descriptions = self._get_tool_descriptions()
        
        log.info("ZombieCoder Coder Agent initialized")
    
    def _load_persona(self) -> str:
        """Load agent persona from file."""
        try:
            with open(self.persona_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            log.error(f"Failed to load persona: {str(e)}")
            return "You are a helpful coding assistant."
    
    def _get_tool_descriptions(self) -> str:
        """Get descriptions of available tools for the LLM."""
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool.description()}")
        return "\n".join(descriptions)
    
    async def run(self, request: AgentRequest) -> AgentResponse:
        """Run the agent with given request."""
        try:
            # Build conversation messages
            messages = [
                Message(role=MessageRole.SYSTEM, content=self.persona),
                Message(role=MessageRole.USER, content=self._build_user_message(request))
            ]
            
            # Get response from LLM
            response = await self.llm.chat(messages)
            
            # Store in memory
            if settings.enable_memory:
                await memory_store.store(
                    f"agent_request_{hash(request.query)}",
                    {
                        "query": request.query,
                        "response": response,
                        "timestamp": asyncio.get_event_loop().time()
                    }
                )
            
            return AgentResponse(
                agent_type=request.agent_type,
                content=response,
                metadata={
                    "tools_used": self._extract_tools_used(response),
                    "context_size": len(request.context) if request.context else 0
                }
            )
            
        except Exception as e:
            log.error(f"Agent execution error: {str(e)}")
            return AgentResponse(
                agent_type=request.agent_type,
                content=f"Arrey Shawon, kichu problem hoyeche! Error: {str(e)}",
                error=str(e)
            )
    
    async def run_stream(self, request: AgentRequest) -> AsyncGenerator[str, None]:
        """Run the agent with streaming response."""
        try:
            # Build conversation messages
            messages = [
                Message(role=MessageRole.SYSTEM, content=self.persona),
                Message(role=MessageRole.USER, content=self._build_user_message(request))
            ]
            
            # Stream response from LLM
            async for chunk in self.llm.chat_stream(messages):
                yield chunk
            
            # Store in memory (collect full response)
            if settings.enable_memory:
                full_response = ""
                async for chunk in self.llm.chat_stream(messages):
                    full_response += chunk
                
                await memory_store.store(
                    f"agent_request_{hash(request.query)}",
                    {
                        "query": request.query,
                        "response": full_response,
                        "timestamp": asyncio.get_event_loop().time()
                    }
                )
            
        except Exception as e:
            log.error(f"Agent streaming error: {str(e)}")
            yield f"Arrey Shawon, kichu problem hoyeche! Error: {str(e)}"
    
    def _build_user_message(self, request: AgentRequest) -> str:
        """Build user message with context and tools."""
        message_parts = []
        
        # Add context if available
        if request.context:
            message_parts.append(f"Project Context:\n{request.context[:3000]}")
        
        # Add tool information
        message_parts.append(f"\nAvailable Tools:\n{self.tool_descriptions}")
        
        # Add the main query
        message_parts.append(f"\nUser Query:\n{request.query}")
        
        # Add instructions for tool usage
        message_parts.append("""
        
Tool Usage Instructions:
- When you need to read files, use the filesystem tool
- When you need to run Python code, use the python tool
- When you need to search for code, use the search tool
- When you need Git operations, use the git tool
- When you need system information, use the system tool

Always provide the complete solution with explanations. Remember to communicate as Shawon's friend!
        """)
        
        return "\n".join(message_parts)
    
    def _extract_tools_used(self, response: str) -> list:
        """Extract tool usage information from response."""
        # Simple heuristic to detect tool mentions
        tools_used = []
        for tool_name in self.tools.keys():
            if tool_name.lower() in response.lower():
                tools_used.append(tool_name)
        return tools_used
    
    async def execute_tool(self, tool_name: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific tool operation."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        tool = self.tools[tool_name]
        return await tool.execute(operation, **kwargs)
    
    def get_persona(self) -> str:
        """Get the agent's persona description."""
        return self.persona
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": "ZombieCoder Coder Agent",
            "description": "A humorous, sharp, energetic Bengali coding partner",
            "tools": list(self.tools.keys()),
            "capabilities": [
                "Code comprehension",
                "Error identification and fixing",
                "New code generation",
                "Full file generation",
                "Directory scanning",
                "File modification suggestions",
                "Step-by-step explanations",
                "Conversational interactions",
                "Python code execution",
                "Git operations",
                "System monitoring",
                "Project search and analysis"
            ],
            "languages": [
                "Python", "JavaScript", "TypeScript", "Java", "C++", "C#",
                "HTML", "CSS", "SQL", "Shell scripting"
            ],
            "frameworks": [
                "React", "Node.js", "Django", "Flask", "FastAPI", "Spring",
                "Express.js", "Next.js", "Vue.js", "Angular"
            ]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health."""
        try:
            # Check LLM
            llm_healthy = await self.llm.health_check()
            
            # Check tools
            tools_healthy = {}
            for name, tool in self.tools.items():
                try:
                    # Try a simple operation
                    if hasattr(tool, 'description'):
                        tools_healthy[name] = True
                    else:
                        tools_healthy[name] = False
                except Exception:
                    tools_healthy[name] = False
            
            # Check memory
            memory_healthy = True
            if settings.enable_memory:
                try:
                    await memory_store.store("health_check", {"test": True})
                    await memory_store.retrieve("health_check")
                except Exception:
                    memory_healthy = False
            
            return {
                "healthy": llm_healthy and all(tools_healthy.values()) and memory_healthy,
                "llm": llm_healthy,
                "tools": tools_healthy,
                "memory": memory_healthy,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }