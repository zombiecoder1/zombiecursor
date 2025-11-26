"""
Core interfaces and type definitions for ZombieCursor.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Supported agent types."""
    CODER = "coder"
    WRITER = "writer"
    RETRIEVER = "retriever"
    EXPLAINER = "explainer"


class MessageRole(Enum):
    """Message roles in conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A message in the conversation."""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentRequest:
    """Request payload for agent execution."""
    query: str
    agent_type: AgentType
    context: Optional[str] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """Response from agent execution."""
    agent_type: AgentType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ProjectFile:
    """Represents a file in the project."""
    path: str
    content: str
    size: int
    last_modified: float


@dataclass
class ProjectContext:
    """Project context information."""
    files: List[ProjectFile]
    root_path: str
    total_files: int
    total_size: int


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def chat(self, messages: List[Message]) -> str:
        """Send chat messages and get response."""
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """Send chat messages and get streaming response."""
        pass


class Tool(ABC):
    """Abstract base class for agent tools."""
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Get tool description."""
        pass
    
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        pass


class MemoryStore(ABC):
    """Abstract base class for memory storage."""
    
    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store a value in memory."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory."""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory for relevant items."""
        pass


class Agent(ABC):
    """Abstract base class for AI agents."""
    
    @abstractmethod
    async def run(self, request: AgentRequest) -> AgentResponse:
        """Run the agent with given request."""
        pass
    
    @abstractmethod
    async def run_stream(self, request: AgentRequest) -> AsyncGenerator[str, None]:
        """Run the agent with streaming response."""
        pass
    
    @abstractmethod
    def get_persona(self) -> str:
        """Get the agent's persona description."""
        pass