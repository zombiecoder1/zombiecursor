# ZombieCursor Local AI - Installation Guide

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **Python**: 3.10 or higher
- **RAM**: 8GB (16GB recommended)
- **Storage**: 10GB free space
- **Network**: Optional (for model downloads)

### Recommended Requirements
- **OS**: Windows 11, Ubuntu 22.04+, macOS 13+
- **Python**: 3.11
- **RAM**: 16GB+ (32GB for large models)
- **Storage**: 50GB+ SSD
- **GPU**: NVIDIA RTX 3060+ (optional for acceleration)

## Installation Methods

### Method 1: Quick Start (Recommended)

#### Windows
```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Download and run installer
Invoke-WebRequest -Uri "https://github.com/zombiecursor/zombiecursor/releases/latest/download/install.ps1" -OutFile "install.ps1"
.\install.ps1
```

#### Linux/macOS
```bash
# Download and run installer
curl -fsSL https://github.com/zombiecursor/zombiecursor/releases/latest/download/install.sh | bash
```

### Method 2: Manual Installation

#### Step 1: Clone Repository
```bash
git clone https://github.com/zombiecursor/zombiecursor.git
cd zombiecursor
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or use your preferred editor
```

#### Step 5: Initialize Database
```bash
# If using database features
npm run db:push  # or python -m alembic upgrade head
```

## Local LLM Setup

### Option 1: Ollama (Recommended for Beginners)

#### Installation
```bash
# Windows (PowerShell)
iwr -useb https://ollama.ai/install.ps1 | iex

# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Download Models
```bash
# Start Ollama
ollama serve

# Download models (in another terminal)
ollama pull llama2
ollama pull codellama
ollama pull mistral
```

#### Configuration
```env
# In .env file
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
```

### Option 2: Llama.cpp (Advanced Users)

#### Download Llama.cpp
```bash
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Build
make  # Linux/macOS
# or use Visual Studio on Windows
```

#### Download Models
```bash
# Example: Download Llama 2 7B Chat
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
```

#### Run Server
```bash
./main -m llama-2-7b-chat.Q4_K_M.gguf --host 0.0.0.0 --port 8007 --ctx-size 2048 -ngl 32
```

#### Configuration
```env
# In .env file
LLM_HOST=http://localhost:8007
LLM_MODEL=llama-2-7b-chat.Q4_K_M.gguf
```

### Option 3: LocalAI (Docker)

#### Installation
```bash
docker run -d -p 8080:8080 --name localai -v $PWD/models:/models -e MODELS_PATH=/models localai/localai:latest
```

#### Download Models
```bash
# Download model configuration
curl -L https://raw.githubusercontent.com/go-skynet/model-gallery/main/llama-2-7b-chat.yaml -o models/llama-2-7b-chat.yaml
```

#### Configuration
```env
# In .env file
LLM_HOST=http://localhost:8080
LLM_MODEL=llama-2-7b-chat
```

## Configuration

### Environment Variables

Create `.env` file with following settings:

```env
# Server Configuration
HOST=0.0.0.0
PORT=5051
DEBUG=false

# LLM Configuration
LLM_HOST=http://localhost:11434  # Ollama default
LLM_MODEL=llama2
LLM_TIMEOUT=30
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# Alternative: Llama.cpp
# LLM_HOST=http://localhost:8007
# LLM_MODEL=llama-2-7b-chat.Q4_K_M.gguf

# Project Configuration
PROJECT_ROOT=.
MAX_CONTEXT_FILES=50
MAX_CONTEXT_SIZE=3000

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Agent Configuration
DEFAULT_AGENT=coder
ENABLE_STREAMING=true
ENABLE_MEMORY=true

# Vector Store Configuration
VECTOR_STORE_PATH=./vectorstores/data
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Tool Configuration
ENABLE_GIT_TOOL=true
ENABLE_PYTHON_TOOL=true
ENABLE_SYSTEM_TOOL=true
PYTHON_TIMEOUT=30
```

### Advanced Configuration

#### Production Settings
```env
DEBUG=false
LOG_LEVEL=INFO
ENABLE_RATE_LIMITING=true
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
```

#### Development Settings
```env
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_RATE_LIMITING=false
```

## Windows-Specific Setup

### Prerequisites
1. **Python 3.10+**: Download from python.org
2. **Git**: Download from git-scm.com
3. **Visual Studio Build Tools**: For compiling some packages

### Installation Steps

#### 1. Install Python
- Download Python 3.10+ from python.org
- Install with "Add to PATH" option
- Verify installation: `python --version`

#### 2. Install Git
- Download Git from git-scm.com
- Install with default options
- Verify installation: `git --version`

#### 3. Install ZombieCursor
```powershell
# Clone repository
git clone https://github.com/zombiecursor/zombiecursor.git
cd zombiecursor

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Configure Windows Firewall
- Allow Python through firewall for port 5051
- Allow LLM server through firewall (ports 11434 or 8007)

#### 5. Create Start Script
Create `start.bat`:
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python -m server.main
pause
```

## Linux-Specific Setup

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git build-essential

# CentOS/RHEL
sudo yum install python3 python3-pip git gcc make

# Arch Linux
sudo pacman -S python python-pip git base-devel
```

### Installation Steps
```bash
# Clone repository
git clone https://github.com/zombiecursor/zombiecursor.git
cd zombiecursor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service (optional)
sudo cp scripts/zombiecursor.service /etc/systemd/system/
sudo systemctl enable zombiecursor
sudo systemctl start zombiecursor
```

## macOS-Specific Setup

### Prerequisites
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python@3.11 git
```

### Installation Steps
```bash
# Clone repository
git clone https://github.com/zombiecursor/zombiecursor.git
cd zombiecursor

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Docker Installation

### Using Docker Compose

#### 1. Create docker-compose.yml
```yaml
version: '3.8'

services:
  zombiecursor:
    build: .
    ports:
      - "5051:5051"
    volumes:
      - ./data:/app/data
      - ./vectorstores:/app/vectorstores
    environment:
      - LLM_HOST=http://ollama:11434
      - LLM_MODEL=llama2
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0

volumes:
  ollama_data:
```

#### 2. Start Services
```bash
docker-compose up -d
```

#### 3. Download Models
```bash
docker-compose exec ollama ollama pull llama2
```

## Verification

### 1. Check Server Status
```bash
curl http://localhost:5051/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### 2. Check LLM Connection
```bash
curl http://localhost:5051/status/llm
```

### 3. Test Agent
```bash
curl -X POST http://localhost:5051/agent/coder/run \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, who are you?"}'
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
netstat -tulpn | grep :5051  # Linux
netstat -ano | findstr :5051  # Windows

# Kill process
kill -9 <PID>  # Linux
taskkill /PID <PID> /F  # Windows
```

#### 2. Python Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check virtual environment
which python  # Linux/macOS
where python  # Windows
```

#### 3. LLM Connection Failed
```bash
# Check LLM server
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8007/health     # Llama.cpp

# Check configuration
cat .env | grep LLM_HOST
```

#### 4. Memory Issues
```bash
# Reduce context size
echo "MAX_CONTEXT_SIZE=1500" >> .env

# Disable memory features
echo "ENABLE_MEMORY=false" >> .env
```

### Performance Optimization

#### 1. Reduce Memory Usage
```env
MAX_CONTEXT_FILES=20
MAX_CONTEXT_SIZE=1500
ENABLE_MEMORY=false
```

#### 2. Increase Speed
```env
LLM_MAX_TOKENS=1024
ENABLE_STREAMING=true
```

#### 3. GPU Acceleration
```env
# For Llama.cpp
LLM_HOST=http://localhost:8007
# Add -ngl 99 to command line for GPU layers
```

## Next Steps

After successful installation:

1. **Read the Architecture Guide**: Understand the system design
2. **Configure Editor Integration**: Set up VS Code or other editors
3. **Explore Agent Capabilities**: Learn about different agents
4. **Customize Configuration**: Adjust settings for your needs
5. **Join Community**: Get support and share experiences

## Support

- **Documentation**: [docs.zombiecoder.my.id](https://docs.zombiecoder.my.id)
- **Issues**: [GitHub Issues](https://github.com/zombiecursor/zombiecursor/issues)
- **Discord**: [Community Server](https://discord.gg/zombiecursor)
- **Email**: support@zombiecoder.my.id