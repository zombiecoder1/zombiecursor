# ZombieCursor Local AI

যেখানে কোড ও কথা বলে - Where Code Speaks

A local AI-powered coding assistant that provides Cursor AI-like functionality with complete privacy and offline operation.

## Product Information

- **Product**: ZombieCoder Local AI
- **Tagline**: যেখানে কোড ও কথা বলে
- **Owner**: Sahon Srabon
- **Company**: Developer Zone
- **Contact**: +880 1323-626282
- **Address**: 235 south pirarbag, Amtala Bazar, Mirpur -60 feet
- **Website**: https://zombiecoder.my.id/
- **Email**: infi@zombiecoder.my.id
- **GitHub Repository**: https://github.com/zombiecoder1/zombiecursor.git

## Features

- 🚀 **Local Operation**: Complete offline functionality with no external API calls
- 🤖 **Smart Agents**: Multiple specialized agents for different coding tasks
- 📝 **Code Comprehension**: Deep understanding of your codebase
- 🔧 **Error Identification**: Smart bug detection and fixing
- 📁 **File Management**: Safe file operations with project context
- 🌐 **WebSocket Support**: Real-time streaming responses
- 🔒 **Privacy First**: All data stays on your local machine

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Local LLM (Ollama or Llama.cpp)
- Git (optional, for version control features)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/zombiecoder1/zombiecursor.git
cd zombiecursor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start the server:
```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 5051 --reload
```

### VS Code Integration

Add this to your VS Code settings.json:

```json
{
  "cursor.ai.endpoint": "http://localhost:5051",
  "cursor.ai.agent": "coder"
}
```

## Architecture

```
zombiecursor/
├── server/          # FastAPI gateway
├── agents/          # AI agents
├── core/            # Core functionality
├── tools/           # Agent tools
├── vectorstores/    # Memory management
└── docs/           # Documentation
```

## Usage Examples

### Basic Query

```bash
curl -X POST "http://localhost:5051/agent/coder/run" \
  -H "Content-Type: application/json" \
  -d '{"query": "Fix the bug in payment_service.py"}'
```

### Streaming Response

```javascript
const ws = new WebSocket('ws://localhost:5051/ws');
ws.send(JSON.stringify({
  agent: 'coder',
  query: 'Explain this function',
  stream: true
}));
```

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Editor Integration](docs/EDITOR_INTEGRATION.md)
- [Agent Persona Guide](docs/AGENT_PERSONA_GUIDE.md)

## GitHub Repository

This project is hosted on GitHub at: [https://github.com/zombiecoder1/zombiecursor.git](https://github.com/zombiecoder1/zombiecursor.git)

You can contribute to the project, report issues, or fork it for your own use.

## License

© 2024 Developer Zone. All rights reserved.