# ZombieCursor Local AI - Architecture Guide

## Overview

ZombieCursor Local AI is a comprehensive, locally-operated AI coding assistant that provides Cursor AI-like functionality with complete privacy and offline operation. The system is built with a modular architecture that supports multiple agents, tools, and integration points.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ZombieCursor Local AI                    │
├─────────────────────────────────────────────────────────────┤
│                      API Gateway                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Agent     │ │   Status    │ │    WebSocket           │ │
│  │   Routes    │ │   Routes    │ │    Routes              │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Core Components                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │    LLM      │ │   Memory    │ │    Context             │ │
│  │  Adapter    │ │   Store     │ │   Loader               │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Agent Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Coder     │ │   Writer    │ │    Retriever            │ │
│  │   Agent     │ │   Agent     │ │    Agent                │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Tool Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Filesystem  │ │   Python    │ │    Search               │ │
│  │    Tool     │ │    Tool     │ │    Tool                 │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │     Git     │ │   System    │ │                         │ │
│  │    Tool     │ │    Tool     │ │                         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Vector    │ │   Config    │ │    Logging              │ │
│  │   Store     │ │  Manager    │ │    System               │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Gateway (FastAPI Server)
- **Port**: 5051 (default)
- **Routes**: Agent execution, status monitoring, WebSocket communication
- **Middleware**: CORS, security headers, rate limiting, authentication
- **Documentation**: Auto-generated OpenAPI/Swagger docs

### 2. Local LLM Adapter
- **Supported Backends**: Llama.cpp (port 8007), Ollama (port 11434)
- **Features**: Streaming and non-streaming responses, health checks
- **Compatibility**: OpenAI-compatible `/v1/chat/completions` endpoint

### 3. Agent System
- **Coder Agent**: Bengali coding partner with persona-driven responses
- **Future Agents**: Writer, Retriever, Explainer (extensible architecture)
- **Capabilities**: Code generation, debugging, explanation, refactoring

### 4. Tool Integration
- **Filesystem Tool**: Safe file operations with project context
- **Python Tool**: Code execution, syntax checking, formatting, linting
- **Search Tool**: Text search, function/class finding, reference location
- **Git Tool**: Version control operations and history analysis
- **System Tool**: System monitoring and resource management

### 5. Memory Management
- **Vector Store**: FAISS-based semantic search with sentence transformers
- **Simple Memory**: File-based key-value storage for session data
- **Features**: Semantic search, hybrid search, caching, persistence

### 6. Project Context
- **Dynamic Loading**: Real-time project structure analysis
- **File Awareness**: Git-aware file discovery and exclusion
- **Language Detection**: Automatic language statistics and categorization

## Data Flow

### Request Processing
1. **Client Request** → API Gateway
2. **Authentication** → Security Middleware
3. **Route Resolution** → Agent/Status/WebSocket Handlers
4. **Agent Execution** → LLM Adapter + Tools
5. **Response Generation** → Streaming/Non-streaming
6. **Memory Storage** → Vector Store + Simple Memory
7. **Client Response** → Formatted JSON/WebSocket

### Tool Execution Flow
1. **Agent Request** → Tool Manager
2. **Tool Selection** → Based on request analysis
3. **Parameter Validation** → Tool-specific schema
4. **Execution** → Async tool operation
5. **Result Processing** → Error handling and formatting
6. **Response** → Agent integration

### Memory Storage Flow
1. **Content Generation** → Agent/Tool output
2. **Embedding Creation** → Sentence transformer
3. **Vector Storage** → FAISS index
4. **Metadata Storage** → File-based persistence
5. **Index Update** → Real-time vector addition

## Security Architecture

### Authentication Layers
1. **API Key Authentication** (Optional)
2. **Token-based Authentication** (JWT-like)
3. **IP Whitelisting** (Production)
4. **Rate Limiting** (Per-client)

### Security Features
- **CORS Configuration**: Configurable origin restrictions
- **Security Headers**: XSS protection, content type options
- **Input Validation**: Pydantic schemas for all inputs
- **Path Traversal Protection**: Safe file operations
- **Command Injection Prevention**: Sanitized system calls

## Performance Considerations

### Caching Strategy
- **Project Context**: 5-minute cache with invalidation
- **LLM Responses**: Optional response caching
- **Vector Search**: FAISS-optimized similarity search
- **File Operations**: Lazy loading with size limits

### Resource Management
- **Memory Limits**: Configurable context and file size limits
- **Timeout Handling**: LLM and tool execution timeouts
- **Connection Pooling**: Efficient resource utilization
- **Background Tasks**: Async operations for non-blocking I/O

## Scalability Architecture

### Horizontal Scaling
- **Stateless Design**: Easy horizontal scaling
- **Load Balancing**: Multiple server instances support
- **Database Scaling**: External vector stores (Pinecone, Weaviate)
- **Cache Distribution**: Redis for distributed caching

### Vertical Scaling
- **Resource Allocation**: Configurable memory and CPU limits
- **Model Optimization**: Quantized models for efficiency
- **Batch Processing**: Bulk operations support
- **Parallel Execution**: Concurrent tool operations

## Integration Points

### Editor Integration
- **VS Code**: Extension support with Language Server Protocol
- **Cursor AI**: Compatible API endpoints
- **Generic Editors**: REST API + WebSocket support

### LLM Integration
- **Local Models**: Llama.cpp, Ollama, LocalAI
- **Model Formats**: GGUF, SafeTensors, ONNX
- **Hardware Support**: CPU, GPU, Metal acceleration

### Tool Extensions
- **Custom Tools**: Plugin architecture for new tools
- **External APIs**: Webhook and API integration support
- **Database Connectors**: SQL and NoSQL database tools

## Monitoring and Observability

### Logging System
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: Configurable verbosity (DEBUG, INFO, WARNING, ERROR)
- **Log Rotation**: Automatic file management
- **Performance Metrics**: Request timing and resource usage

### Health Monitoring
- **Component Health**: LLM, agents, tools, memory systems
- **System Metrics**: CPU, memory, disk usage
- **Error Tracking**: Comprehensive error reporting
- **Performance Analytics**: Response time and throughput

## Configuration Management

### Environment Variables
- **Server Configuration**: Host, port, debug mode
- **LLM Settings**: Model, temperature, max tokens
- **Security Options**: CORS origins, API keys, rate limits
- **Resource Limits**: File sizes, context lengths, timeouts

### Dynamic Configuration
- **Runtime Updates**: Hot configuration reloading
- **Feature Flags**: Enable/disable features dynamically
- **A/B Testing**: Experimental feature support
- **Environment Profiles**: Development, staging, production configs

## Deployment Architecture

### Development Environment
- **Local Development**: Single-machine deployment
- **Docker Support**: Containerized deployment options
- **Hot Reloading**: Development server with auto-restart
- **Debug Tools**: Integrated debugging and profiling

### Production Environment
- **Container Orchestration**: Kubernetes, Docker Compose
- **Load Balancing**: Nginx, HAProxy, cloud load balancers
- **Monitoring Stack**: Prometheus, Grafana, ELK stack
- **Backup Systems**: Automated data backup and recovery

## Future Architecture Plans

### Multi-Modal Support
- **Vision Models**: Image understanding and generation
- **Audio Processing**: Speech-to-text and text-to-speech
- **Document Analysis**: PDF, Word, Excel integration

### Advanced Features
- **Code Execution Sandboxes**: Secure isolated environments
- **Collaborative Coding**: Multi-user real-time collaboration
- **Knowledge Graphs**: Advanced code relationship mapping
- **Auto-completion**: Intelligent code suggestions

### Cloud Integration
- **Hybrid Deployment**: Local + cloud model support
- **Model Marketplace**: Community model sharing
- **Enterprise Features**: SSO, audit logs, compliance
- **API Economy**: Monetization and licensing options